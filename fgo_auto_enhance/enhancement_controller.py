"""Enhancement controller for managing the complete enhancement process"""

import time
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .adb_manager import ADBManager
from .image_analyzer import ImageAnalyzer, GameState
from .touch_controller import TouchController
from .safety_manager import SafetyManager


@dataclass
class EnhancementConfig:
    """Enhancement configuration settings"""
    target_craft_essence: str
    target_level: int
    max_attempts: int
    material_priority: List[str]
    device_id: Optional[str]
    screen_resolution: Tuple[int, int]
    enhancement_timeout: float = 30.0  # seconds per enhancement attempt
    state_change_timeout: float = 10.0  # seconds to wait for state changes


@dataclass
class EnhancementResult:
    """Enhancement operation result"""
    success: bool
    current_level: int
    exp_gained: int
    materials_used: List[str]
    error_message: Optional[str]
    timestamp: datetime
    attempts_made: int


class EnhancementController:
    """Main controller for craft essence enhancement process"""
    
    def __init__(self, config: EnhancementConfig, adb_manager: ADBManager,
                 image_analyzer: ImageAnalyzer, touch_controller: TouchController,
                 safety_manager: SafetyManager):
        self.config = config
        self.adb_manager = adb_manager
        self.image_analyzer = image_analyzer
        self.touch_controller = touch_controller
        self.safety_manager = safety_manager
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self.current_state = GameState.UNKNOWN
        self.last_state_change = time.time()
        self.enhancement_attempts = 0
        self.total_exp_gained = 0
        self.materials_used = []
        
        # Process control
        self.is_running = False
        self.should_stop = False
    
    def start_enhancement(self, target_level: int = None, max_attempts: int = None) -> EnhancementResult:
        """Start the enhancement process"""
        if target_level is not None:
            self.config.target_level = target_level
        if max_attempts is not None:
            self.config.max_attempts = max_attempts
        
        self.is_running = True
        self.should_stop = False
        self.enhancement_attempts = 0
        self.total_exp_gained = 0
        self.materials_used = []
        
        self.logger.info(f"Starting enhancement process - Target level: {self.config.target_level}, "
                        f"Max attempts: {self.config.max_attempts}")
        
        try:
            # Initial state detection
            if not self._detect_initial_state():
                return self._create_error_result("Failed to detect initial game state")
            
            # Main enhancement loop
            while (self.is_running and 
                   self.enhancement_attempts < self.config.max_attempts and
                   not self.should_stop):
                
                # Safety check
                if not self.safety_manager.is_safe_to_continue():
                    self.logger.warning("Safety manager requested stop")
                    break
                
                # Perform enhancement cycle
                result = self._perform_enhancement_cycle()
                
                if result.success:
                    self.enhancement_attempts += 1
                    self.total_exp_gained += result.exp_gained
                    self.materials_used.extend(result.materials_used)
                    
                    self.logger.info(f"Enhancement #{self.enhancement_attempts} completed. "
                                   f"Current level: {result.current_level}")
                    
                    # Check if target level reached
                    if result.current_level >= self.config.target_level:
                        self.logger.info(f"Target level {self.config.target_level} reached!")
                        break
                else:
                    self.logger.error(f"Enhancement cycle failed: {result.error_message}")
                    # Try to recover from error state
                    if not self._recover_from_error():
                        return self._create_error_result("Failed to recover from error state")
            
            # Create final result
            return EnhancementResult(
                success=True,
                current_level=0,  # Would need OCR to determine actual level
                exp_gained=self.total_exp_gained,
                materials_used=self.materials_used,
                error_message=None,
                timestamp=datetime.now(),
                attempts_made=self.enhancement_attempts
            )
            
        except Exception as e:
            self.logger.error(f"Enhancement process failed with exception: {e}")
            return self._create_error_result(f"Enhancement process exception: {e}")
        finally:
            self.is_running = False
    
    def stop_enhancement(self):
        """Stop the enhancement process"""
        self.should_stop = True
        self.logger.info("Enhancement stop requested")
    
    def _perform_enhancement_cycle(self) -> EnhancementResult:
        """Perform a single enhancement cycle"""
        try:
            # 1. Navigate to enhancement screen
            if not self._navigate_to_enhancement_screen():
                return self._create_error_result("Failed to navigate to enhancement screen")
            
            # 2. Select materials
            materials = self._select_materials()
            if not materials:
                return self._create_error_result("Failed to select enhancement materials")
            
            # 3. Execute enhancement
            if not self._execute_enhancement():
                return self._create_error_result("Failed to execute enhancement")
            
            # 4. Process result
            exp_gained = self._process_enhancement_result()
            
            return EnhancementResult(
                success=True,
                current_level=0,  # Would need OCR
                exp_gained=exp_gained,
                materials_used=materials,
                error_message=None,
                timestamp=datetime.now(),
                attempts_made=1
            )
            
        except Exception as e:
            return self._create_error_result(f"Enhancement cycle exception: {e}")
    
    def _detect_initial_state(self) -> bool:
        """Detect and verify initial game state"""
        for attempt in range(3):
            screen = self.adb_manager.capture_screen()
            if screen is None:
                self.logger.error("Failed to capture screen")
                continue
            
            self.current_state = self.image_analyzer.detect_game_state(screen)
            self.logger.info(f"Detected initial state: {self.current_state}")
            
            if self.current_state != GameState.UNKNOWN:
                return True
            
            self.touch_controller.wait_random(1.0, 2.0)
        
        return False
    
    def _navigate_to_enhancement_screen(self) -> bool:
        """Navigate to the enhancement screen based on current state"""
        max_navigation_attempts = 10
        
        for attempt in range(max_navigation_attempts):
            screen = self.adb_manager.capture_screen()
            if screen is None:
                continue
            
            current_state = self.image_analyzer.detect_game_state(screen)
            self.logger.debug(f"Current state: {current_state}")
            
            if current_state == GameState.CE_ENHANCEMENT_SCREEN:
                return True
            elif current_state == GameState.CE_LIST_SCREEN:
                # Find target craft essence and tap it
                if self._select_target_craft_essence(screen):
                    self._wait_for_state_change()
                    continue
                else:
                    self.logger.error("Failed to find target craft essence")
                    return False
            elif current_state == GameState.ENHANCEMENT_MENU:
                # Navigate to CE enhancement from enhancement menu
                if self._navigate_to_ce_enhancement(screen):
                    self._wait_for_state_change()
                    continue
                else:
                    self.logger.error("Failed to navigate to CE enhancement")
                    return False
            elif current_state == GameState.MAIN_MENU:
                # Navigate to enhancement menu
                if self._navigate_to_enhancement_menu(screen):
                    self._wait_for_state_change()
                    continue
                else:
                    self.logger.error("Failed to navigate to enhancement menu")
                    return False
            elif current_state == GameState.ERROR_STATE:
                self.logger.error("Detected error state during navigation")
                return False
            else:
                # Try to go back or navigate
                self._perform_back_navigation(screen)
                self._wait_for_state_change()
        
        self.logger.error("Failed to navigate to enhancement screen after maximum attempts")
        return False
    
    def _select_target_craft_essence(self, screen) -> bool:
        """Select the target craft essence from the list"""
        ces = self.image_analyzer.find_craft_essences(screen)
        
        if not ces:
            self.logger.warning("No craft essences found on screen")
            return False
        
        # For now, select the first available craft essence
        # In a real implementation, this would match against the target
        target_ce = ces[0]
        
        return self.touch_controller.tap_at(target_ce[0], target_ce[1])
    
    def _navigate_to_enhancement_menu(self, screen) -> bool:
        """Navigate from main menu to enhancement menu"""
        # Look for enhancement menu button
        enhancement_menu_button = self.image_analyzer.find_template(screen, "enhancement_menu_button")
        
        if enhancement_menu_button:
            return self.touch_controller.tap_at(enhancement_menu_button[0], enhancement_menu_button[1])
        
        self.logger.warning("Enhancement menu button not found")
        return False
    
    def _navigate_to_ce_enhancement(self, screen) -> bool:
        """Navigate from enhancement menu to CE enhancement screen"""
        # Look for CE enhancement button
        ce_enhancement_button = self.image_analyzer.find_template(screen, "ce_enhancement_button")
        
        if ce_enhancement_button:
            return self.touch_controller.tap_at(ce_enhancement_button[0], ce_enhancement_button[1])
        
        self.logger.warning("CE enhancement button not found")
        return False
    
    def _perform_back_navigation(self, screen):
        """Perform back navigation or menu button tap"""
        # Look for back button
        back_button = self.image_analyzer.find_template(screen, "back_button")
        if back_button:
            self.touch_controller.tap_at(back_button[0], back_button[1])
            return
        
        # Look for menu button
        menu_button = self.image_analyzer.find_template(screen, "menu_button")
        if menu_button:
            self.touch_controller.tap_at(menu_button[0], menu_button[1])
            return
        
        # Try Android back button as fallback
        self.adb_manager.execute_command("input keyevent 4")
    
    def _select_materials(self) -> List[str]:
        """Select enhancement materials"""
        screen = self.adb_manager.capture_screen()
        if screen is None:
            return []
        
        # Check if we need to open CE selection or can directly enhance
        current_state = self.image_analyzer.detect_game_state(screen)
        
        if current_state == GameState.CE_ENHANCEMENT_SCREEN:
            # Check if target CE slot needs to be selected
            target_ce_slot = self.image_analyzer.find_template(screen, "target_ce_slot")
            if target_ce_slot:
                # Need to select CE first
                self.touch_controller.tap_at(target_ce_slot[0], target_ce_slot[1])
                if self._wait_for_state(GameState.CE_LIST_SCREEN):
                    # Select target CE
                    screen = self.adb_manager.capture_screen()
                    if not self._select_target_craft_essence(screen):
                        return []
                    # Wait to return to CE enhancement screen
                    if not self._wait_for_state(GameState.CE_ENHANCEMENT_SCREEN):
                        return []
                    screen = self.adb_manager.capture_screen()
            
            # Now try to start enhancement
            enhance_button = self.image_analyzer.find_template(screen, "enhance_button")
            if enhance_button:
                self.touch_controller.tap_at(enhance_button[0], enhance_button[1])
                if not self._wait_for_state(GameState.MATERIAL_SELECTION):
                    return []
            else:
                self.logger.error("Enhance button not found")
                return []
        elif not self._wait_for_state(GameState.MATERIAL_SELECTION):
            return []
        
        # Find available materials
        materials = self.image_analyzer.find_enhancement_materials(screen)
        selected_materials = []
        
        # Select materials based on priority
        for material_pos in materials[:5]:  # Select up to 5 materials
            if self.touch_controller.tap_at(material_pos[0], material_pos[1]):
                selected_materials.append("material")  # Would need OCR to identify actual material
                self.touch_controller.wait_random(0.3, 0.8)
        
        self.logger.info(f"Selected {len(selected_materials)} materials")
        return selected_materials
    
    def _execute_enhancement(self) -> bool:
        """Execute the enhancement process"""
        screen = self.adb_manager.capture_screen()
        if screen is None:
            return False
        
        # Look for enhancement execute button
        execute_button = self.image_analyzer.find_template(screen, "execute_enhancement_button")
        
        if not execute_button:
            self.logger.error("Enhancement execute button not found")
            return False
        
        # Tap execute button
        if not self.touch_controller.tap_at(execute_button[0], execute_button[1]):
            return False
        
        # Wait for confirmation screen
        if not self._wait_for_state(GameState.ENHANCEMENT_CONFIRM):
            return False
        
        # Confirm enhancement
        screen = self.adb_manager.capture_screen()
        confirm_button = self.image_analyzer.find_template(screen, "confirm_button")
        
        if not confirm_button:
            self.logger.error("Confirmation button not found")
            return False
        
        return self.touch_controller.tap_at(confirm_button[0], confirm_button[1])
    
    def _process_enhancement_result(self) -> int:
        """Process enhancement result and extract exp gained"""
        if not self._wait_for_state(GameState.ENHANCEMENT_RESULT):
            return 0
        
        # Wait for animation to complete
        self.touch_controller.wait_random(2.0, 4.0)
        
        # Extract exp gained (would need OCR implementation)
        exp_gained = 100  # Placeholder value
        
        # Tap to continue
        screen = self.adb_manager.capture_screen()
        continue_button = self.image_analyzer.find_template(screen, "continue_button")
        
        if continue_button:
            self.touch_controller.tap_at(continue_button[0], continue_button[1])
        else:
            # Tap center of screen as fallback
            resolution = self.adb_manager.get_screen_resolution()
            if resolution:
                center_x, center_y = resolution[0] // 2, resolution[1] // 2
                self.touch_controller.tap_at(center_x, center_y)
        
        return exp_gained
    
    def _wait_for_state(self, target_state: GameState, timeout: float = None) -> bool:
        """Wait for specific game state"""
        if timeout is None:
            timeout = self.config.state_change_timeout
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            screen = self.adb_manager.capture_screen()
            if screen is None:
                continue
            
            current_state = self.image_analyzer.detect_game_state(screen)
            if current_state == target_state:
                return True
            
            time.sleep(0.5)
        
        self.logger.warning(f"Timeout waiting for state {target_state}")
        return False
    
    def _wait_for_state_change(self):
        """Wait for any state change"""
        self.touch_controller.wait_random(1.0, 2.0)
    
    def _recover_from_error(self) -> bool:
        """Attempt to recover from error state"""
        self.logger.info("Attempting error recovery")
        
        # Try pressing back button multiple times
        for _ in range(3):
            self.adb_manager.execute_command("input keyevent 4")
            self.touch_controller.wait_random(1.0, 2.0)
            
            screen = self.adb_manager.capture_screen()
            if screen is not None:
                state = self.image_analyzer.detect_game_state(screen)
                if state != GameState.ERROR_STATE:
                    self.logger.info("Successfully recovered from error state")
                    return True
        
        return False
    
    def _create_error_result(self, error_message: str) -> EnhancementResult:
        """Create an error result"""
        return EnhancementResult(
            success=False,
            current_level=0,
            exp_gained=0,
            materials_used=[],
            error_message=error_message,
            timestamp=datetime.now(),
            attempts_made=self.enhancement_attempts
        )
    
    def check_completion_conditions(self) -> bool:
        """Check if enhancement should be completed"""
        if self.should_stop:
            return True
        
        if self.enhancement_attempts >= self.config.max_attempts:
            return True
        
        # Would check current level vs target level with OCR
        
        return False
    
    def get_progress_report(self) -> dict:
        """Get current progress report"""
        return {
            'is_running': self.is_running,
            'attempts_made': self.enhancement_attempts,
            'max_attempts': self.config.max_attempts,
            'target_level': self.config.target_level,
            'total_exp_gained': self.total_exp_gained,
            'materials_used_count': len(self.materials_used),
            'current_state': self.current_state.value
        }