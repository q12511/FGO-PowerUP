"""Safety manager for human-like operation patterns and anomaly detection"""

import random
import time
import logging
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from pynput import keyboard
import threading


@dataclass
class SafetyConfig:
    """Safety configuration settings"""
    min_wait_time: float = 0.5
    max_wait_time: float = 2.0
    tap_offset_range: int = 10
    operation_variance: float = 0.3
    anomaly_detection: bool = True
    emergency_stop_key: str = "f12"
    swipe_duration_range: Tuple[int, int] = (200, 500)
    max_consecutive_operations: int = 50
    break_interval: float = 30.0  # seconds
    break_duration: float = 5.0  # seconds


class SafetyManager:
    """Manages safe operation patterns and detects anomalies"""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Operation tracking
        self.operation_count = 0
        self.last_break_time = time.time()
        self.emergency_stop_triggered = False
        
        # Pattern analysis
        self.operation_history = []
        self.last_operation_time = 0
        
        # Keyboard listener for emergency stop
        self.keyboard_listener = None
        self.start_keyboard_listener()
    
    def start_keyboard_listener(self):
        """Start keyboard listener for emergency stop"""
        def on_key_press(key):
            try:
                if hasattr(key, 'name') and key.name.lower() == self.config.emergency_stop_key.lower():
                    self.emergency_stop_triggered = True
                    self.logger.warning("Emergency stop triggered!")
                elif hasattr(key, 'char') and key.char and key.char.lower() == self.config.emergency_stop_key.lower():
                    self.emergency_stop_triggered = True
                    self.logger.warning("Emergency stop triggered!")
            except AttributeError:
                pass
        
        try:
            self.keyboard_listener = keyboard.Listener(on_press=on_key_press)
            self.keyboard_listener.start()
            self.logger.info(f"Emergency stop key listener started (key: {self.config.emergency_stop_key})")
        except Exception as e:
            self.logger.error(f"Failed to start keyboard listener: {e}")
    
    def stop_keyboard_listener(self):
        """Stop keyboard listener"""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def get_random_offset(self, max_offset: int = None) -> Tuple[int, int]:
        """Generate random offset for touch coordinates"""
        if max_offset is None:
            max_offset = self.config.tap_offset_range
        
        # Use normal distribution for more natural variation
        offset_x = int(random.gauss(0, max_offset / 3))
        offset_y = int(random.gauss(0, max_offset / 3))
        
        # Clamp to max offset
        offset_x = max(-max_offset, min(max_offset, offset_x))
        offset_y = max(-max_offset, min(max_offset, offset_y))
        
        return (offset_x, offset_y)
    
    def get_random_wait_time(self, base_time: float, variance: float = None) -> float:
        """Generate random wait time with variance"""
        if variance is None:
            variance = self.config.operation_variance
        
        # Use normal distribution for more human-like timing
        wait_time = random.gauss(base_time, base_time * variance)
        
        # Ensure minimum and maximum bounds
        wait_time = max(self.config.min_wait_time, 
                       min(self.config.max_wait_time, wait_time))
        
        return wait_time
    
    def is_safe_to_continue(self) -> bool:
        """Check if it's safe to continue operations"""
        # Check emergency stop
        if self.emergency_stop_triggered:
            self.logger.warning("Emergency stop active - stopping operations")
            return False
        
        # Check if break is needed
        if self._should_take_break():
            self._take_scheduled_break()
            return True
        
        # Check operation patterns for anomalies
        if self.config.anomaly_detection and self._detect_pattern_anomaly():
            self.logger.warning("Anomalous operation pattern detected - taking precautionary break")
            self._take_scheduled_break()
            return True
        
        return True
    
    def detect_anomaly(self, screen: np.ndarray) -> bool:
        """Detect visual anomalies in screen content"""
        if not self.config.anomaly_detection:
            return False
        
        try:
            # Simple anomaly detection based on screen properties
            
            # Check for completely black or white screens
            mean_brightness = np.mean(screen)
            if mean_brightness < 10 or mean_brightness > 245:
                self.logger.warning(f"Anomalous screen brightness detected: {mean_brightness}")
                return True
            
            # Check for extremely low variance (frozen screen)
            variance = np.var(screen)
            if variance < 100:
                self.logger.warning(f"Extremely low screen variance detected: {variance}")
                return True
            
            # Check screen dimensions consistency
            expected_channels = 3  # BGR
            if len(screen.shape) != 3 or screen.shape[2] != expected_channels:
                self.logger.warning(f"Unexpected screen format: {screen.shape}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            return True  # Err on the side of caution
    
    def record_operation(self, operation_type: str, success: bool):
        """Record operation for pattern analysis"""
        current_time = time.time()
        
        operation_record = {
            'type': operation_type,
            'success': success,
            'timestamp': current_time,
            'interval': current_time - self.last_operation_time if self.last_operation_time > 0 else 0
        }
        
        self.operation_history.append(operation_record)
        self.last_operation_time = current_time
        self.operation_count += 1
        
        # Keep only recent history
        max_history = 100
        if len(self.operation_history) > max_history:
            self.operation_history = self.operation_history[-max_history:]
        
        self.logger.debug(f"Recorded operation: {operation_type}, success: {success}")
    
    def _should_take_break(self) -> bool:
        """Check if a scheduled break is needed"""
        current_time = time.time()
        
        # Check operation count threshold
        if self.operation_count >= self.config.max_consecutive_operations:
            return True
        
        # Check time-based break interval
        if current_time - self.last_break_time >= self.config.break_interval:
            return True
        
        return False
    
    def _take_scheduled_break(self):
        """Take a scheduled break with random duration"""
        base_duration = self.config.break_duration
        actual_duration = self.get_random_wait_time(base_duration, 0.5)
        
        self.logger.info(f"Taking scheduled break for {actual_duration:.1f} seconds")
        time.sleep(actual_duration)
        
        # Reset counters
        self.operation_count = 0
        self.last_break_time = time.time()
    
    def _detect_pattern_anomaly(self) -> bool:
        """Detect anomalous patterns in operation history"""
        if len(self.operation_history) < 10:
            return False
        
        recent_operations = self.operation_history[-10:]
        
        # Check for too many failures
        failure_rate = sum(1 for op in recent_operations if not op['success']) / len(recent_operations)
        if failure_rate > 0.5:
            self.logger.warning(f"High failure rate detected: {failure_rate:.1%}")
            return True
        
        # Check for too regular timing (bot-like behavior)
        intervals = [op['interval'] for op in recent_operations if op['interval'] > 0]
        if len(intervals) >= 5:
            interval_variance = np.var(intervals)
            if interval_variance < 0.1:  # Very regular timing
                self.logger.warning(f"Suspiciously regular timing detected: variance={interval_variance:.3f}")
                return True
        
        # Check for same operation repeated too many times
        recent_types = [op['type'] for op in recent_operations]
        if len(set(recent_types)) == 1 and len(recent_types) >= 8:
            self.logger.warning(f"Same operation repeated too many times: {recent_types[0]}")
            return True
        
        return False
    
    def get_humanized_swipe_duration(self) -> int:
        """Get humanized swipe duration"""
        min_duration, max_duration = self.config.swipe_duration_range
        base_duration = (min_duration + max_duration) / 2
        
        # Add some randomness
        variance = (max_duration - min_duration) * 0.3
        duration = random.gauss(base_duration, variance)
        
        # Clamp to valid range
        duration = max(min_duration, min(max_duration, int(duration)))
        
        return duration
    
    def reset_emergency_stop(self):
        """Reset emergency stop flag"""
        self.emergency_stop_triggered = False
        self.logger.info("Emergency stop flag reset")
    
    def get_status_report(self) -> dict:
        """Get current safety manager status"""
        return {
            'operation_count': self.operation_count,
            'emergency_stop_active': self.emergency_stop_triggered,
            'time_since_last_break': time.time() - self.last_break_time,
            'recent_operation_count': len(self.operation_history),
            'keyboard_listener_active': self.keyboard_listener is not None and self.keyboard_listener.running
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_keyboard_listener()