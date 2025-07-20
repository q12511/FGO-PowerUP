"""Touch controller for automated touch operations"""

import time
import random
import logging
from typing import Tuple, Optional
from .adb_manager import ADBManager


class TouchController:
    """Touch operations controller with safety and randomization"""
    
    def __init__(self, adb_manager: ADBManager, safety_manager=None):
        self.adb_manager = adb_manager
        self.safety_manager = safety_manager
        self.logger = logging.getLogger(__name__)
        
        # Default timing parameters
        self.default_tap_delay = (0.5, 2.0)  # min, max seconds
        self.default_swipe_duration = (200, 500)  # min, max milliseconds
        self.default_offset_range = 10  # pixels
        
    def tap_at(self, x: int, y: int, randomize: bool = True) -> bool:
        """Tap at specified coordinates with optional randomization"""
        try:
            # Apply random offset if randomization is enabled
            if randomize:
                offset_x, offset_y = self._get_random_offset()
                x += offset_x
                y += offset_y
                
            self.logger.debug(f"Tapping at ({x}, {y})")
            
            # Execute tap
            success = self.adb_manager.tap(x, y)
            
            if success:
                self.logger.info(f"Successfully tapped at ({x}, {y})")
                
                # Add random wait time after tap
                if randomize:
                    self.wait_random()
            else:
                self.logger.error(f"Failed to tap at ({x}, {y})")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error during tap operation: {e}")
            return False
    
    def swipe(self, start: Tuple[int, int], end: Tuple[int, int], 
              duration: Optional[int] = None, randomize: bool = True) -> bool:
        """Swipe from start to end coordinates"""
        try:
            start_x, start_y = start
            end_x, end_y = end
            
            # Apply random offset if randomization is enabled
            if randomize:
                offset_x, offset_y = self._get_random_offset()
                start_x += offset_x
                start_y += offset_y
                end_x += offset_x
                end_y += offset_y
            
            # Set random duration if not specified
            if duration is None:
                duration = random.randint(*self.default_swipe_duration)
            
            self.logger.debug(f"Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y}) "
                            f"in {duration}ms")
            
            # Execute swipe
            success = self.adb_manager.swipe(start_x, start_y, end_x, end_y, duration)
            
            if success:
                self.logger.info(f"Successfully swiped from ({start_x}, {start_y}) "
                               f"to ({end_x}, {end_y})")
                
                # Add random wait time after swipe
                if randomize:
                    self.wait_random()
            else:
                self.logger.error(f"Failed to swipe from ({start_x}, {start_y}) "
                                f"to ({end_x}, {end_y})")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error during swipe operation: {e}")
            return False
    
    def long_press(self, x: int, y: int, duration: int = 1000, randomize: bool = True) -> bool:
        """Long press at specified coordinates"""
        try:
            # Apply random offset if randomization is enabled
            if randomize:
                offset_x, offset_y = self._get_random_offset()
                x += offset_x
                y += offset_y
                
                # Add some randomness to duration
                duration += random.randint(-100, 100)
                duration = max(500, duration)  # Ensure minimum duration
            
            self.logger.debug(f"Long pressing at ({x}, {y}) for {duration}ms")
            
            # Execute long press
            success = self.adb_manager.long_press(x, y, duration)
            
            if success:
                self.logger.info(f"Successfully long pressed at ({x}, {y}) for {duration}ms")
                
                # Add random wait time after long press
                if randomize:
                    self.wait_random()
            else:
                self.logger.error(f"Failed to long press at ({x}, {y})")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error during long press operation: {e}")
            return False
    
    def wait_random(self, min_sec: float = None, max_sec: float = None) -> None:
        """Wait for random time between min_sec and max_sec"""
        if min_sec is None or max_sec is None:
            min_sec, max_sec = self.default_tap_delay
            
        wait_time = random.uniform(min_sec, max_sec)
        
        # Apply safety manager adjustments if available
        if self.safety_manager:
            wait_time = self.safety_manager.get_random_wait_time(wait_time)
        
        self.logger.debug(f"Waiting for {wait_time:.2f} seconds")
        time.sleep(wait_time)
    
    def _get_random_offset(self) -> Tuple[int, int]:
        """Get random offset for touch coordinates"""
        if self.safety_manager:
            return self.safety_manager.get_random_offset()
        else:
            # Default random offset
            offset_x = random.randint(-self.default_offset_range, self.default_offset_range)
            offset_y = random.randint(-self.default_offset_range, self.default_offset_range)
            return (offset_x, offset_y)
    
    def tap_with_retry(self, x: int, y: int, max_retries: int = 3, 
                      retry_delay: float = 1.0) -> bool:
        """Tap with retry mechanism"""
        for attempt in range(max_retries):
            if self.tap_at(x, y):
                return True
            
            if attempt < max_retries - 1:
                self.logger.warning(f"Tap failed, retrying in {retry_delay}s "
                                  f"(attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
        
        self.logger.error(f"All {max_retries} tap attempts failed")
        return False
    
    def multi_tap(self, coordinates: list, delay_between: float = 0.5) -> bool:
        """Execute multiple taps in sequence"""
        success_count = 0
        
        for i, (x, y) in enumerate(coordinates):
            if self.tap_at(x, y):
                success_count += 1
            
            # Add delay between taps (except for last tap)
            if i < len(coordinates) - 1:
                time.sleep(delay_between)
        
        success_rate = success_count / len(coordinates)
        self.logger.info(f"Multi-tap completed: {success_count}/{len(coordinates)} "
                        f"successful ({success_rate:.1%})")
        
        return success_rate >= 0.8  # Consider success if 80% or more taps succeeded
    
    def scroll_down(self, start_y: int = None, end_y: int = None, 
                   center_x: int = None) -> bool:
        """Scroll down on screen"""
        # Get screen resolution if coordinates not provided
        if start_y is None or end_y is None or center_x is None:
            resolution = self.adb_manager.get_screen_resolution()
            if resolution is None:
                self.logger.error("Cannot get screen resolution for scroll")
                return False
            
            width, height = resolution
            center_x = center_x or width // 2
            start_y = start_y or int(height * 0.7)
            end_y = end_y or int(height * 0.3)
        
        return self.swipe((center_x, start_y), (center_x, end_y))
    
    def scroll_up(self, start_y: int = None, end_y: int = None, 
                 center_x: int = None) -> bool:
        """Scroll up on screen"""
        # Get screen resolution if coordinates not provided
        if start_y is None or end_y is None or center_x is None:
            resolution = self.adb_manager.get_screen_resolution()
            if resolution is None:
                self.logger.error("Cannot get screen resolution for scroll")
                return False
            
            width, height = resolution
            center_x = center_x or width // 2
            start_y = start_y or int(height * 0.3)
            end_y = end_y or int(height * 0.7)
        
        return self.swipe((center_x, start_y), (center_x, end_y))
    
    def emergency_stop_check(self) -> bool:
        """Check for emergency stop condition"""
        if self.safety_manager:
            return not self.safety_manager.is_safe_to_continue()
        return False