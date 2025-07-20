#!/usr/bin/env python3
"""Debug script for specific template matching"""

import sys
import cv2
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fgo_auto_enhance.adb_manager import ADBManager
from fgo_auto_enhance.image_analyzer import ImageAnalyzer
from fgo_auto_enhance.config_manager import ConfigManager


def save_debug_image(image: np.ndarray, filename: str):
    """Save debug image with timestamp"""
    debug_dir = Path("debug_images")
    debug_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{timestamp}_{filename}"
    
    cv2.imwrite(str(debug_dir / full_filename), image)
    print(f"Saved: debug_images/{full_filename}")


def test_template_matching(template_name: str, threshold: float = 0.7):
    """Test specific template matching with detailed analysis"""
    print(f"=== Template Matching Debug: {template_name} ===")
    
    # Initialize components
    try:
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()
        
        adb_manager = ADBManager(config.device.device_id)
        image_analyzer = ImageAnalyzer(config.template.template_dir)
        
    except Exception as e:
        print(f"Error initializing: {e}")
        return False
    
    # Connect to device
    if not adb_manager.connect_device():
        print("❌ Failed to connect to device")
        return False
    
    print(f"✅ Connected to device: {adb_manager.device_id}")
    
    # Check template exists
    template_path = Path(config.template.template_dir) / f"{template_name}.png"
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        print("Available templates:")
        template_dir = Path(config.template.template_dir)
        if template_dir.exists():
            for template_file in template_dir.glob("*.png"):
                print(f"   - {template_file.stem}")
        return False
    
    # Load template
    template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if template is None:
        print(f"❌ Failed to load template: {template_path}")
        return False
    
    print(f"✅ Template loaded: {template.shape}")
    save_debug_image(template, f"template_{template_name}.png")
    
    # Capture current screen
    screen = adb_manager.capture_screen()
    if screen is None:
        print("❌ Failed to capture screen")
        return False
    
    print(f"✅ Screen captured: {screen.shape}")
    save_debug_image(screen, "current_screen_for_template.png")
    
    # Perform template matching with detailed analysis
    print(f"\n=== Template Matching Analysis ===")
    print(f"Template: {template_name}")
    print(f"Threshold: {threshold}")
    print(f"Method: TM_CCOEFF_NORMED")
    
    # Basic template matching
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"\nMatching Results:")
    print(f"   Max confidence: {max_val:.4f}")
    print(f"   Min confidence: {min_val:.4f}")
    print(f"   Best match location: {max_loc}")
    print(f"   Threshold: {threshold}")
    print(f"   Match status: {'✅ MATCH' if max_val >= threshold else '❌ NO MATCH'}")
    
    # Create visualization
    h, w = template.shape[:2]
    
    # Draw best match location
    visualized = screen.copy()
    
    if max_val >= threshold:
        # Draw green rectangle for successful match
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv2.rectangle(visualized, top_left, bottom_right, (0, 255, 0), 3)
        
        # Draw center point
        center_x = top_left[0] + w // 2
        center_y = top_left[1] + h // 2
        cv2.circle(visualized, (center_x, center_y), 10, (0, 255, 0), -1)
        
        # Add confidence text
        text = f"{template_name}: {max_val:.3f}"
        cv2.putText(visualized, text, (top_left[0], top_left[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        print(f"\n✅ Template found at center: ({center_x}, {center_y})")
        
    else:
        # Draw red rectangle for failed match (best attempt)
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv2.rectangle(visualized, top_left, bottom_right, (0, 0, 255), 3)
        
        # Add confidence text
        text = f"{template_name}: {max_val:.3f} (FAIL)"
        cv2.putText(visualized, text, (top_left[0], top_left[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        print(f"\n❌ Template not found (best match: {max_val:.3f})")
    
    save_debug_image(visualized, f"match_result_{template_name}.png")
    
    # Test multiple thresholds
    print(f"\n=== Multi-Threshold Analysis ===")
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    for test_threshold in thresholds:
        match_status = "✅" if max_val >= test_threshold else "❌"
        print(f"   Threshold {test_threshold}: {match_status} ({max_val:.3f})")
    
    # Find all matches above threshold
    print(f"\n=== All Matches Above Threshold ===")
    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))
    
    if matches:
        print(f"Found {len(matches)} matches:")
        for i, (x, y) in enumerate(matches[:10]):  # Show first 10
            confidence = result[y, x]
            center_x = x + w // 2
            center_y = y + h // 2
            print(f"   Match {i+1}: center({center_x}, {center_y}) confidence={confidence:.3f}")
            
            # Draw additional matches in blue
            if i > 0:  # Skip first one (already drawn in green/red)
                cv2.rectangle(visualized, (x, y), (x + w, y + h), (255, 0, 0), 2)
    else:
        print("No matches found above threshold")
    
    # Save final visualization
    save_debug_image(visualized, f"final_analysis_{template_name}.png")
    
    # Recommendations
    print(f"\n=== Recommendations ===")
    
    if max_val >= threshold:
        print("✅ Template matching is working correctly")
        if len(matches) > 1:
            print("⚠️  Multiple matches found - consider making template more specific")
    else:
        print("❌ Template matching failed. Possible solutions:")
        print("   1. Recreate template with more distinctive features")
        print("   2. Include more background context")
        print("   3. Check if UI has changed since template creation")
        print(f"   4. Lower threshold (current: {threshold}, max confidence: {max_val:.3f})")
        print("   5. Ensure correct game screen is displayed")
    
    if max_val < 0.3:
        print("⚠️  Very low confidence - template may be completely wrong")
    elif max_val < 0.5:
        print("⚠️  Low confidence - template needs significant improvement")
    elif max_val < 0.7:
        print("⚠️  Moderate confidence - template could be improved")
    
    print(f"\n=== Debug Complete ===")
    print("Check debug_images/ folder for detailed analysis images")
    
    return max_val >= threshold


def main():
    parser = argparse.ArgumentParser(description="Debug template matching for FGO automation")
    parser.add_argument("template_name", help="Template name (without .png extension)")
    parser.add_argument("--threshold", "-t", type=float, default=0.7, 
                       help="Matching threshold (default: 0.7)")
    
    args = parser.parse_args()
    
    try:
        success = test_template_matching(args.template_name, args.threshold)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nDebug interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()