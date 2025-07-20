"""Tests for ADB Manager"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from fgo_auto_enhance.adb_manager import ADBManager
from fgo_auto_enhance.exceptions import DeviceNotFoundError, DeviceConnectionError


class TestADBManager(unittest.TestCase):
    """Test cases for ADB Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.adb_manager = ADBManager()
    
    @patch('subprocess.run')
    def test_get_connected_devices_success(self, mock_run):
        """Test successful device detection"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="List of devices attached\ndevice123\tdevice\n"
        )
        
        devices = self.adb_manager.get_connected_devices()
        
        self.assertEqual(devices, ['device123'])
        mock_run.assert_called_once_with(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_get_connected_devices_no_devices(self, mock_run):
        """Test when no devices are connected"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="List of devices attached\n"
        )
        
        devices = self.adb_manager.get_connected_devices()
        
        self.assertEqual(devices, [])
    
    @patch('subprocess.run')
    def test_get_connected_devices_adb_not_found(self, mock_run):
        """Test when ADB is not installed"""
        mock_run.side_effect = FileNotFoundError()
        
        devices = self.adb_manager.get_connected_devices()
        
        self.assertEqual(devices, [])
    
    @patch.object(ADBManager, 'get_connected_devices')
    @patch.object(ADBManager, 'execute_command')
    def test_connect_device_success(self, mock_execute, mock_get_devices):
        """Test successful device connection"""
        mock_get_devices.return_value = ['device123']
        mock_execute.return_value = 'test'
        
        result = self.adb_manager.connect_device()
        
        self.assertTrue(result)
        self.assertEqual(self.adb_manager.device_id, 'device123')
    
    @patch.object(ADBManager, 'get_connected_devices')
    def test_connect_device_no_devices(self, mock_get_devices):
        """Test connection when no devices available"""
        mock_get_devices.return_value = []
        
        result = self.adb_manager.connect_device()
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution"""
        self.adb_manager.device_id = 'device123'
        mock_run.return_value = Mock(
            returncode=0,
            stdout='command output'
        )
        
        result = self.adb_manager.execute_command('echo test')
        
        self.assertEqual(result, 'command output')
        mock_run.assert_called_once_with(
            ['adb', '-s', 'device123', 'shell', 'echo test'],
            capture_output=True,
            text=True,
            timeout=30
        )
    
    @patch('subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """Test command execution failure"""
        self.adb_manager.device_id = 'device123'
        mock_run.return_value = Mock(
            returncode=1,
            stderr='command failed'
        )
        
        result = self.adb_manager.execute_command('invalid command')
        
        self.assertIsNone(result)
    
    @patch('subprocess.run')
    @patch('cv2.imdecode')
    def test_capture_screen_success(self, mock_imdecode, mock_run):
        """Test successful screen capture"""
        self.adb_manager.device_id = 'device123'
        self.adb_manager._connected = True
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=b'fake_image_data'
        )
        
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image
        
        result = self.adb_manager.capture_screen()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, (1080, 1920, 3))
    
    @patch('subprocess.run')
    def test_capture_screen_failure(self, mock_run):
        """Test screen capture failure"""
        self.adb_manager.device_id = 'device123'
        self.adb_manager._connected = True
        
        mock_run.return_value = Mock(
            returncode=1,
            stderr='screencap failed'
        )
        
        result = self.adb_manager.capture_screen()
        
        self.assertIsNone(result)
    
    @patch.object(ADBManager, 'execute_command')
    def test_get_screen_resolution_success(self, mock_execute):
        """Test successful screen resolution detection"""
        mock_execute.return_value = 'Physical size: 1080x1920'
        
        result = self.adb_manager.get_screen_resolution()
        
        self.assertEqual(result, (1080, 1920))
    
    @patch.object(ADBManager, 'execute_command')
    def test_get_screen_resolution_failure(self, mock_execute):
        """Test screen resolution detection failure"""
        mock_execute.return_value = None
        
        result = self.adb_manager.get_screen_resolution()
        
        self.assertIsNone(result)
    
    @patch.object(ADBManager, 'execute_command')
    def test_tap_success(self, mock_execute):
        """Test successful tap operation"""
        mock_execute.return_value = 'input tap executed'
        
        result = self.adb_manager.tap(100, 200)
        
        self.assertTrue(result)
        mock_execute.assert_called_once_with('input tap 100 200')
    
    @patch.object(ADBManager, 'execute_command')
    def test_swipe_success(self, mock_execute):
        """Test successful swipe operation"""
        mock_execute.return_value = 'input swipe executed'
        
        result = self.adb_manager.swipe(100, 200, 300, 400, 500)
        
        self.assertTrue(result)
        mock_execute.assert_called_once_with('input swipe 100 200 300 400 500')


if __name__ == '__main__':
    unittest.main()