"""ADB Manager for Android device control"""

import subprocess
import time
import logging
from typing import List, Optional, Tuple
import numpy as np
import cv2
from pathlib import Path


class ADBManager:
    """ADB device connection and management"""
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.logger = logging.getLogger(__name__)
        self._connected = False
        
    def get_connected_devices(self) -> List[str]:
        """Get list of connected ADB devices"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.error(f"ADB devices command failed: {result.stderr}")
                return []
                
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
                    
            return devices
            
        except subprocess.TimeoutExpired:
            self.logger.error("ADB devices command timed out")
            return []
        except FileNotFoundError:
            self.logger.error("ADB not found. Please install Android SDK Platform Tools")
            return []
        except Exception as e:
            self.logger.error(f"Failed to get connected devices: {e}")
            return []
    
    def connect_device(self) -> bool:
        """Connect to ADB device"""
        devices = self.get_connected_devices()
        
        if not devices:
            self.logger.error("No devices connected")
            return False
            
        if self.device_id is None:
            if len(devices) == 1:
                self.device_id = devices[0]
                self.logger.info(f"Auto-selected device: {self.device_id}")
            else:
                self.logger.error(f"Multiple devices found: {devices}. Please specify device_id")
                return False
        elif self.device_id not in devices:
            self.logger.error(f"Device {self.device_id} not found in connected devices: {devices}")
            return False
            
        # Test connection with a simple command
        if self.execute_command("echo test") is not None:
            self._connected = True
            self.logger.info(f"Successfully connected to device: {self.device_id}")
            return True
        else:
            self.logger.error(f"Failed to connect to device: {self.device_id}")
            return False
    
    def is_device_connected(self) -> bool:
        """Check if device is connected"""
        if not self._connected or not self.device_id:
            return False
            
        # Test with a simple command
        result = self.execute_command("echo test")
        return result is not None
    
    def execute_command(self, command: str) -> Optional[str]:
        """Execute ADB command on connected device"""
        if not self.device_id:
            self.logger.error("No device connected")
            return None
            
        full_command = ['adb', '-s', self.device_id, 'shell', command]
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.error(f"ADB command failed: {result.stderr}")
                return None
                
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"ADB command timed out: {command}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to execute ADB command: {e}")
            return None
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """Capture device screen using ADB screencap"""
        if not self.is_device_connected():
            self.logger.error("Device not connected")
            return None
            
        try:
            # Use ADB screencap command to capture screen
            result = subprocess.run(
                ['adb', '-s', self.device_id, 'exec-out', 'screencap', '-p'],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.error("Screen capture failed")
                return None
                
            # Convert bytes to numpy array
            nparr = np.frombuffer(result.stdout, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                self.logger.error("Failed to decode captured image")
                return None
                
            return img
            
        except subprocess.TimeoutExpired:
            self.logger.error("Screen capture timed out")
            return None
        except Exception as e:
            self.logger.error(f"Failed to capture screen: {e}")
            return None
    
    def get_screen_resolution(self) -> Optional[Tuple[int, int]]:
        """Get device screen resolution"""
        result = self.execute_command("wm size")
        if result is None:
            return None
            
        try:
            # Parse output like "Physical size: 1080x2340"
            size_str = result.split(': ')[1]
            width, height = map(int, size_str.split('x'))
            return (width, height)
        except (IndexError, ValueError) as e:
            self.logger.error(f"Failed to parse screen resolution: {e}")
            return None
    
    def tap(self, x: int, y: int) -> bool:
        """Tap at specified coordinates"""
        command = f"input tap {x} {y}"
        result = self.execute_command(command)
        return result is not None
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 300) -> bool:
        """Swipe from start to end coordinates"""
        command = f"input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
        result = self.execute_command(command)
        return result is not None
    
    def long_press(self, x: int, y: int, duration: int = 1000) -> bool:
        """Long press at specified coordinates"""
        # Simulate long press by tap down, wait, tap up
        command_down = f"input touchscreen down {x} {y}"
        command_up = f"input touchscreen up {x} {y}"
        
        if self.execute_command(command_down) is None:
            return False
            
        time.sleep(duration / 1000.0)
        
        return self.execute_command(command_up) is not None