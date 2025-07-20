"""Image analysis and template matching for FGO game state detection"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


class GameState(Enum):
    """Game state enumeration"""
    UNKNOWN = "unknown"
    MAIN_MENU = "main_menu"
    ENHANCEMENT_MENU = "enhancement_menu"
    CE_ENHANCEMENT_SCREEN = "ce_enhancement_screen"
    CE_LIST_SCREEN = "ce_list_screen"
    MATERIAL_SELECTION = "material_selection"
    ENHANCEMENT_CONFIRM = "enhancement_confirm"
    ENHANCEMENT_RESULT = "enhancement_result"
    ERROR_STATE = "error_state"


class ImageAnalyzer:
    """Image analysis and template matching for game state detection"""
    
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self.templates: Dict[str, np.ndarray] = {}
        self.logger = logging.getLogger(__name__)
        
        # Template matching parameters
        self.default_threshold = 0.8
        self.match_method = cv2.TM_CCOEFF_NORMED
        
        # Load templates on initialization
        self.load_templates()
    
    def load_templates(self) -> Dict[str, np.ndarray]:
        """Load template images from directory"""
        if not self.template_dir.exists():
            self.logger.warning(f"Template directory not found: {self.template_dir}")
            return {}
        
        template_files = list(self.template_dir.glob("*.png")) + list(self.template_dir.glob("*.jpg"))
        
        for template_file in template_files:
            try:
                template = cv2.imread(str(template_file), cv2.IMREAD_COLOR)
                if template is not None:
                    template_name = template_file.stem
                    self.templates[template_name] = template
                    self.logger.info(f"Loaded template: {template_name}")
                else:
                    self.logger.warning(f"Failed to load template: {template_file}")
                    
            except Exception as e:
                self.logger.error(f"Error loading template {template_file}: {e}")
        
        self.logger.info(f"Loaded {len(self.templates)} templates")
        return self.templates
    
    def find_template(self, screen: np.ndarray, template_name: str, 
                     threshold: float = None) -> Optional[Tuple[int, int]]:
        """Find template in screen image using template matching"""
        if threshold is None:
            threshold = self.default_threshold
            
        if template_name not in self.templates:
            self.logger.error(f"Template not found: {template_name}")
            return None
        
        template = self.templates[template_name]
        
        try:
            # Perform template matching
            result = cv2.matchTemplate(screen, template, self.match_method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Use max_loc for TM_CCOEFF_NORMED
            if max_val >= threshold:
                # Return center coordinates of matched template
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                self.logger.debug(f"Template {template_name} found at ({center_x}, {center_y}) "
                                f"with confidence {max_val:.3f}")
                return (center_x, center_y)
            else:
                self.logger.debug(f"Template {template_name} not found "
                                f"(confidence {max_val:.3f} < {threshold})")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in template matching for {template_name}: {e}")
            return None
    
    def find_template_all_matches(self, screen: np.ndarray, template_name: str, 
                                 threshold: float = None) -> List[Tuple[int, int]]:
        """Find all matches of template in screen image"""
        if threshold is None:
            threshold = self.default_threshold
            
        if template_name not in self.templates:
            self.logger.error(f"Template not found: {template_name}")
            return []
        
        template = self.templates[template_name]
        matches = []
        
        try:
            result = cv2.matchTemplate(screen, template, self.match_method)
            h, w = template.shape[:2]
            
            # Find all locations where match value is above threshold
            locations = np.where(result >= threshold)
            
            for pt in zip(*locations[::-1]):  # Switch x and y
                center_x = pt[0] + w // 2
                center_y = pt[1] + h // 2
                matches.append((center_x, center_y))
            
            self.logger.debug(f"Found {len(matches)} matches for template {template_name}")
            return matches
            
        except Exception as e:
            self.logger.error(f"Error finding all matches for {template_name}: {e}")
            return []
    
    def detect_game_state(self, screen: np.ndarray) -> GameState:
        """Detect current game state based on screen content"""
        try:
            # Check for each game state in priority order
            
            # Enhancement result screen (check first as it's most specific)
            if self.find_template(screen, "enhancement_result", 0.7):
                return GameState.ENHANCEMENT_RESULT
            
            # Enhancement confirmation screen
            if self.find_template(screen, "enhancement_confirm", 0.7):
                return GameState.ENHANCEMENT_CONFIRM
            
            # Material selection screen
            if self.find_template(screen, "material_selection", 0.7):
                return GameState.MATERIAL_SELECTION
            
            # CE list screen (specific CE selection screen)
            if self.find_template(screen, "ce_list_screen", 0.7):
                return GameState.CE_LIST_SCREEN
            
            # CE enhancement screen (specific CE enhancement interface)
            if self.find_template(screen, "ce_enhancement_screen", 0.7):
                return GameState.CE_ENHANCEMENT_SCREEN
            
            # Enhancement menu (general enhancement menu)
            if self.find_template(screen, "enhancement_menu", 0.7):
                return GameState.ENHANCEMENT_MENU
            
            # Main menu
            if self.find_template(screen, "main_menu", 0.7):
                return GameState.MAIN_MENU
            
            # Check for error indicators
            if (self.find_template(screen, "error_dialog", 0.6) or 
                self.find_template(screen, "connection_error", 0.6)):
                return GameState.ERROR_STATE
            
            return GameState.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Error detecting game state: {e}")
            return GameState.ERROR_STATE
    
    def find_enhancement_materials(self, screen: np.ndarray) -> List[Tuple[int, int]]:
        """Find available craft essence materials for enhancement (max 20 selectable)"""
        materials = []
        
        # Primary material templates (expandable for multiple types)
        material_templates = [
            "material_item",
            # Future: add more material types
            # "material_item_gold",
            # "material_item_silver", 
            # "material_item_bronze"
        ]
        
        # Find unselected materials
        for template_name in material_templates:
            unselected = self.find_template_all_matches(screen, template_name, 0.7)
            materials.extend(unselected)
        
        # Find selected materials (green highlighted) to avoid duplicate selection
        selected_materials = self.find_template_all_matches(screen, "material_item_selected", 0.7)
        
        # Remove duplicates and filter out already selected materials
        unique_materials = list(set(materials))
        
        # Filter out positions that are too close to selected materials (to avoid reselecting)
        filtered_materials = []
        for material in unique_materials:
            too_close = False
            for selected in selected_materials:
                distance = ((material[0] - selected[0]) ** 2 + (material[1] - selected[1]) ** 2) ** 0.5
                if distance < 50:  # If within 50 pixels, consider it the same item
                    too_close = True
                    break
            if not too_close:
                filtered_materials.append(material)
        
        # Sort by position for consistent selection order
        filtered_materials.sort(key=lambda x: (x[1], x[0]))  # Sort by y then x
        
        self.logger.debug(f"Found {len(filtered_materials)} available materials, {len(selected_materials)} already selected")
        
        return filtered_materials
    
    def find_craft_essences(self, screen: np.ndarray) -> List[Tuple[int, int]]:
        """Find craft essence slots in craft essence list"""
        ces = []
        
        # Look for craft essence slots
        ce_templates = [
            "ce_item"
            # Temporarily disabled until templates are created:
            # "ce_equipped",
            # "ce_unequipped",
            # "ce_locked",
            # "ce_unlocked"
        ]
        
        for template_name in ce_templates:
            matches = self.find_template_all_matches(screen, template_name, 0.7)
            ces.extend(matches)
        
        # Remove duplicates and sort by position
        unique_ces = list(set(ces))
        unique_ces.sort(key=lambda x: (x[1], x[0]))  # Sort by y then x
        
        self.logger.debug(f"Found {len(unique_ces)} craft essences")
        return unique_ces
    
    def is_enhancement_available(self, screen: np.ndarray) -> bool:
        """Check if enhancement button is available/clickable"""
        enhance_button = self.find_template(screen, "enhance_button_active", 0.8)
        return enhance_button is not None
    
    def get_current_level(self, screen: np.ndarray) -> Optional[int]:
        """Extract current level from enhancement screen (OCR would be needed)"""
        # This would require OCR implementation
        # For now, return None to indicate OCR not implemented
        self.logger.debug("Level extraction requires OCR implementation")
        return None
    
    def save_debug_image(self, screen: np.ndarray, filename: str):
        """Save screen image for debugging purposes"""
        try:
            debug_dir = Path("debug_images")
            debug_dir.mkdir(exist_ok=True)
            cv2.imwrite(str(debug_dir / filename), screen)
            self.logger.debug(f"Saved debug image: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save debug image: {e}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better template matching"""
        try:
            # Convert to grayscale for some operations if needed
            # For now, return original image
            return image
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            return image