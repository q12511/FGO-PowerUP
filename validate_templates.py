#!/usr/bin/env python3
"""Template validation helper for FGO automation"""

import sys
import cv2
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fgo_auto_enhance.template_manager import TemplateManager, TemplatePriority


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}")


def print_section(text: str):
    """Print formatted section"""
    print(f"\n{'-'*40}")
    print(f"{text}")
    print(f"{'-'*40}")


def validate_all_templates():
    """Comprehensive template validation"""
    print_header("FGO Template Validation Tool")
    
    # Initialize template manager
    try:
        template_manager = TemplateManager("templates")
    except Exception as e:
        print(f"❌ Failed to initialize template manager: {e}")
        return False
    
    # Validate templates
    print_section("1. Template Registry Validation")
    validation_results = template_manager.validate_templates()
    status_summary = template_manager.get_template_status_summary()
    
    print(f"📊 Template Summary:")
    print(f"   Total templates: {status_summary['total']}")
    print(f"   Existing: {status_summary['existing']}")
    print(f"   Missing: {status_summary['missing']}")
    print(f"   Missing required: {status_summary['required_missing']}")
    print(f"   Missing high priority: {status_summary['high_priority_missing']}")
    
    # Show missing templates by priority
    print_section("2. Missing Templates by Priority")
    missing_templates = template_manager.get_missing_templates()
    
    all_missing = []
    for priority, templates in missing_templates.items():
        if templates:
            print(f"\n{priority.value} Priority Missing:")
            for template in templates:
                info = template_manager.get_template_info(template)
                print(f"   ❌ {info.filename} - {info.description}")
                all_missing.append(template)
            
    if not all_missing:
        print("✅ No missing templates!")
    
    # Show existing templates
    print_section("3. Existing Templates")
    existing_templates = template_manager.list_templates(exists_only=True)
    
    if existing_templates:
        for template in existing_templates:
            info = template_manager.get_template_info(template)
            size_info = f" ({info.size[0]}x{info.size[1]})" if info.size else ""
            print(f"   ✅ {info.filename}{size_info} - {info.description}")
    else:
        print("❌ No templates found!")
    
    # Check template quality
    print_section("4. Template Quality Analysis")
    
    template_dir = Path("templates")
    if template_dir.exists():
        for template_file in template_dir.glob("*.png"):
            template_name = template_file.stem
            
            # Load template
            template = cv2.imread(str(template_file))
            if template is None:
                print(f"   ❌ {template_file.name}: Failed to load")
                continue
                
            h, w = template.shape[:2]
            
            # Size analysis
            size_status = "✅"
            size_notes = []
            
            if w < 50 or h < 50:
                size_status = "⚠️"
                size_notes.append("Very small")
            elif w > 500 or h > 500:
                size_status = "⚠️"
                size_notes.append("Very large")
            
            # Color analysis
            color_status = "✅"
            gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            mean_brightness = gray.mean()
            
            if mean_brightness < 50:
                color_status = "⚠️"
                size_notes.append("Very dark")
            elif mean_brightness > 200:
                color_status = "⚠️"
                size_notes.append("Very bright")
            
            # Contrast analysis
            contrast = gray.std()
            if contrast < 20:
                color_status = "⚠️"
                size_notes.append("Low contrast")
            
            notes_str = f" ({', '.join(size_notes)})" if size_notes else ""
            print(f"   {size_status} {template_file.name}: {w}x{h}, brightness={mean_brightness:.1f}, contrast={contrast:.1f}{notes_str}")
    
    # Priority recommendations
    print_section("5. Priority Recommendations")
    
    required_missing = [t for t in all_missing 
                       if template_manager.get_template_info(t).priority == TemplatePriority.REQUIRED]
    high_missing = [t for t in all_missing 
                   if template_manager.get_template_info(t).priority == TemplatePriority.HIGH]
    
    if required_missing:
        print("🚨 CRITICAL: Create these templates first:")
        for template in required_missing:
            info = template_manager.get_template_info(template)
            print(f"   1. {info.filename} - {info.description}")
    
    if high_missing:
        print("\n⚠️  HIGH PRIORITY: Create these templates next:")
        for template in high_missing:
            info = template_manager.get_template_info(template)
            print(f"   2. {info.filename} - {info.description}")
    
    medium_missing = [t for t in all_missing 
                     if template_manager.get_template_info(t).priority == TemplatePriority.MEDIUM]
    if medium_missing:
        print(f"\n📝 MEDIUM PRIORITY: {len(medium_missing)} templates for enhanced functionality")
    
    # Creation order recommendation
    print_section("6. Recommended Creation Order")
    
    creation_order = [
        "main_menu",
        "enhancement_menu_button", 
        "enhancement_menu",
        "ce_enhancement_button",
        "ce_enhancement_screen",
        "target_ce_slot",
        "enhance_button",
        "material_selection",
        "ce_material",
        "execute_enhancement_button",
        "enhancement_confirm",
        "confirm_button",
        "enhancement_result",
        "continue_button"
    ]
    
    print("Follow this order for optimal testing:")
    for i, template_name in enumerate(creation_order, 1):
        info = template_manager.get_template_info(template_name)
        if info:
            status = "✅" if info.exists else "❌"
            print(f"   {i:2d}. {status} {info.filename} - {info.description}")
    
    # Next steps
    print_section("7. Next Steps")
    
    if status_summary['required_missing'] > 0:
        print("🚨 IMMEDIATE ACTION NEEDED:")
        print("   1. Create missing required templates")
        print("   2. Run: python debug_screen.py")
        print("   3. Follow TEMPLATE_CREATION_GUIDE.md")
    elif status_summary['missing'] > 0:
        print("📋 RECOMMENDED ACTIONS:")
        print("   1. Create missing high-priority templates")
        print("   2. Test existing templates with: python debug_template.py [name]")
        print("   3. Run: python main.py --test-templates")
    else:
        print("✅ ALL TEMPLATES READY!")
        print("   1. Run: python main.py --test-templates")
        print("   2. Run: python main.py --test-connection")
        print("   3. Begin real device testing")
    
    # Save validation report
    print_section("8. Saving Validation Report")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"validation_report_{timestamp}.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"FGO Template Validation Report\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            f.write(f"Summary: {status_summary}\n\n")
            
            f.write("Missing Templates:\n")
            for priority, templates in missing_templates.items():
                if templates:
                    f.write(f"  {priority.value}: {templates}\n")
            
            f.write(f"\nExisting Templates: {existing_templates}\n")
        
        print(f"📄 Validation report saved: {report_file}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")
    
    # Return success status
    success = status_summary['required_missing'] == 0
    
    print_header("Validation Complete")
    if success:
        print("✅ Ready for testing - all required templates exist")
    else:
        print("❌ Not ready - missing required templates")
    
    return success


def validate_specific_template(template_name: str):
    """Validate a specific template"""
    print_header(f"Validating Template: {template_name}")
    
    template_manager = TemplateManager("templates")
    info = template_manager.get_template_info(template_name)
    
    if not info:
        print(f"❌ Template '{template_name}' not found in registry")
        print("\nAvailable templates:")
        for name in template_manager.list_templates():
            print(f"   - {name}")
        return False
    
    print(f"📝 Template Information:")
    print(f"   File: {info.filename}")
    print(f"   Description: {info.description}")
    print(f"   Purpose: {info.purpose}")
    print(f"   Priority: {info.priority.value}")
    print(f"   Threshold: {info.threshold}")
    print(f"   Exists: {'✅' if info.exists else '❌'}")
    
    if info.size:
        print(f"   Size: {info.size[0]}x{info.size[1]}")
    
    if info.exists:
        template_path = Path("templates") / info.filename
        
        # Load and analyze template
        template = cv2.imread(str(template_path))
        if template is not None:
            h, w = template.shape[:2]
            gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            print(f"\n📊 Quality Analysis:")
            print(f"   Dimensions: {w}x{h}")
            print(f"   Brightness: {gray.mean():.1f}")
            print(f"   Contrast: {gray.std():.1f}")
            
            # Recommendations
            print(f"\n💡 Recommendations:")
            if w < 50 or h < 50:
                print("   ⚠️  Template is very small - consider larger area")
            if gray.std() < 20:
                print("   ⚠️  Low contrast - may cause matching issues")
            if gray.mean() < 50:
                print("   ⚠️  Very dark - ensure good visibility")
            if gray.mean() > 200:
                print("   ⚠️  Very bright - ensure good contrast")
            
            print(f"\n🧪 Testing:")
            print(f"   Run: python debug_template.py {template_name}")
            print(f"   Expected threshold: {info.threshold}")
        else:
            print(f"❌ Failed to load template file: {template_path}")
            return False
    else:
        print(f"\n📋 Creation Steps:")
        print(f"   1. Navigate to appropriate game screen")
        print(f"   2. Run: python debug_screen.py")
        print(f"   3. Cut out relevant area from screenshot")
        print(f"   4. Save as templates/{info.filename}")
        print(f"   5. Test with: python debug_template.py {template_name}")
    
    return info.exists


def main():
    parser = argparse.ArgumentParser(description="Validate FGO template images")
    parser.add_argument("template_name", nargs="?", help="Specific template to validate")
    parser.add_argument("--all", action="store_true", help="Validate all templates")
    
    args = parser.parse_args()
    
    try:
        if args.template_name:
            success = validate_specific_template(args.template_name)
        else:
            success = validate_all_templates()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()