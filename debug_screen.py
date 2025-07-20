#!/usr/bin/env python3
"""Debug script for real device screen analysis"""

import sys
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fgo_auto_enhance.adb_manager import ADBManager
from fgo_auto_enhance.image_analyzer import ImageAnalyzer, GameState
from fgo_auto_enhance.config_manager import ConfigManager


def save_debug_image(image: np.ndarray, filename: str):
    """Save debug image with timestamp"""
    debug_dir = Path("debug_images")
    debug_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{timestamp}_{filename}"
    
    cv2.imwrite(str(debug_dir / full_filename), image)
    print(f"Saved debug image: debug_images/{full_filename}")


def analyze_current_screen():
    """Analyze current screen state and save debug information"""
    print("=== FGO Screen Debug Tool ===")
    
    # Initialize components
    try:
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()
        
        adb_manager = ADBManager(config.device.device_id)
        image_analyzer = ImageAnalyzer(config.template.template_dir)
        
    except Exception as e:
        print(f"Error initializing components: {e}")
        return False
    
    # Test device connection
    print("\n1. Testing device connection...")
    if not adb_manager.connect_device():
        print("❌ Failed to connect to device")
        print("Make sure:")
        print("  - Android device is connected")
        print("  - USB debugging is enabled")
        print("  - ADB drivers are installed")
        return False
    
    print(f"✅ Connected to device: {adb_manager.device_id}")
    
    # Get device info
    print("\n2. Device information:")
    try:
        resolution = adb_manager.get_screen_resolution()
        print(f"   Screen resolution: {resolution}")
        
        devices = adb_manager.get_connected_devices()
        print(f"   Available devices: {devices}")
    except Exception as e:
        print(f"   Warning: Could not get device info: {e}")
    
    # Capture screen
    print("\n3. Capturing screen...")
    screen = adb_manager.capture_screen()
    if screen is None:
        print("❌ Failed to capture screen")
        print("Make sure FGO is running and visible")
        return False
    
    print(f"✅ Screen captured: {screen.shape}")
    save_debug_image(screen, "current_screen.png")
    
    # Analyze game state
    print("\n4. Analyzing game state...")
    game_state = image_analyzer.detect_game_state(screen)
    print(f"   Detected state: {game_state}")
    
    # Test template loading
    print("\n5. Template status:")
    templates = image_analyzer.load_templates()
    print(f"   Loaded templates: {len(templates)}")
    
    if templates:
        print("   Available templates:")
        for template_name in sorted(templates.keys()):
            print(f"     - {template_name}")
    else:
        print("   ⚠️  No templates found in templates/ directory")
        print("   Please create template images following TEMPLATE_CREATION_GUIDE.md")
    
    # Test template matching for current state
    print("\n6. Template matching results:")
    
    # Test common templates
    common_templates = [
        "main_menu",
        "enhancement_menu",
        "ce_enhancement_screen",
        "material_selection",
        "enhancement_confirm",
        "enhancement_result"
    ]
    
    matches = {}
    for template_name in common_templates:
        if template_name in templates:
            match = image_analyzer.find_template(screen, template_name)
            matches[template_name] = match
            if match:
                print(f"   ✅ {template_name}: Found at ({match[0]}, {match[1]})")
            else:
                print(f"   ❌ {template_name}: Not found")
        else:
            print(f"   ⚠️  {template_name}: Template file missing")
    
    # Look for UI elements
    print("\n7. UI element detection:")
    
    # Test navigation buttons
    nav_templates = [
        "enhancement_menu_button",
        "ce_enhancement_button",
        "enhance_button",
        "execute_enhancement_button",
        "confirm_button",
        "continue_button"
    ]
    
    for template_name in nav_templates:
        if template_name in templates:
            match = image_analyzer.find_template(screen, template_name, 0.7)
            if match:
                print(f"   🔘 {template_name}: Found at ({match[0]}, {match[1]})")
        else:
            print(f"   ⚠️  {template_name}: Template missing")
    
    # Test material detection if in material selection
    if game_state == GameState.MATERIAL_SELECTION:
        print("\n8. Material detection:")
        materials = image_analyzer.find_enhancement_materials(screen)
        print(f"   Found {len(materials)} materials")
        
        for i, (x, y) in enumerate(materials[:5]):  # Show first 5
            print(f"     Material {i+1}: ({x}, {y})")
    
    # Test CE detection if in CE list
    if game_state == GameState.CE_LIST_SCREEN:
        print("\n8. Craft Essence detection:")
        ces = image_analyzer.find_craft_essences(screen)
        print(f"   Found {len(ces)} craft essences")
        
        for i, (x, y) in enumerate(ces[:5]):  # Show first 5
            print(f"     CE {i+1}: ({x}, {y})")
    
    # Save analysis results
    print("\n9. Saving analysis results...")
    
    # Create annotated image
    annotated = screen.copy()
    
    # Draw detected elements
    for template_name, match in matches.items():
        if match:
            cv2.circle(annotated, match, 20, (0, 255, 0), 3)
            cv2.putText(annotated, template_name, (match[0] + 25, match[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    save_debug_image(annotated, "annotated_screen.png")
    
    print("\n=== Debug Complete ===")
    print("Check debug_images/ folder for saved screenshots")
    print("Next steps:")
    print("1. Review detected game state")
    print("2. Create missing template images")
    print("3. Run: python main.py --test-templates")
    
    return True


if __name__ == "__main__":
    try:
        success = analyze_current_screen()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nDebug interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)