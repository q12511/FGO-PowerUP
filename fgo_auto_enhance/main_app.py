"""Main application for FGO craft essence auto enhancement"""

import sys
import argparse
import time
from pathlib import Path
from typing import Optional

from .config_manager import ConfigManager, AppConfig, DeviceConfig, TemplateConfig
from .adb_manager import ADBManager
from .image_analyzer import ImageAnalyzer
from .touch_controller import TouchController
from .safety_manager import SafetyManager, SafetyConfig
from .enhancement_controller import EnhancementController, EnhancementConfig
from .logger_setup import LoggerSetup, create_structured_logger, setup_exception_logging, LogContext
from .exceptions import *


class MainApp:
    """Main application class for FGO auto enhancement"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_manager = ConfigManager(config_file)
        self.config = None
        self.logger = None
        self.operation_logger = None
        self.performance_logger = None
        
        # Core components
        self.adb_manager = None
        self.image_analyzer = None
        self.touch_controller = None
        self.safety_manager = None
        self.enhancement_controller = None
        
        # State
        self.is_initialized = False
        self.is_running = False
    
    def initialize(self) -> bool:
        """Initialize the application"""
        try:
            # Load configuration
            self.config = self.config_manager.load_config()
            
            # Setup logging
            self.logger, self.operation_logger, self.performance_logger = create_structured_logger(
                self.config.logging, 'fgo_auto_enhance.main_app'
            )
            
            # Setup global exception logging
            setup_exception_logging(self.logger)
            
            self.logger.info("FGO Auto Enhancement Tool starting...")
            
            # Validate configuration
            config_issues = self.config_manager.validate_config(self.config)
            if config_issues:
                for issue in config_issues:
                    self.logger.warning(f"Configuration issue: {issue}")
            
            # Initialize core components
            with LogContext(self.operation_logger, "initialize_components"):
                if not self._initialize_components():
                    return False
            
            self.is_initialized = True
            self.logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize application: {e}", exc_info=True)
            else:
                print(f"Failed to initialize application: {e}")
            return False
    
    def _initialize_components(self) -> bool:
        """Initialize core components"""
        try:
            # Initialize ADB manager
            self.adb_manager = ADBManager(self.config.device.device_id)
            
            if not self.adb_manager.connect_device():
                raise DeviceConnectionError("Failed to connect to ADB device")
            
            self.logger.info(f"Connected to device: {self.adb_manager.device_id}")
            
            # Initialize image analyzer
            template_dir = Path(self.config.template.template_dir)
            if not template_dir.exists():
                self.logger.warning(f"Template directory not found: {template_dir}")
                template_dir.mkdir(parents=True, exist_ok=True)
            
            self.image_analyzer = ImageAnalyzer(str(template_dir))
            
            # Initialize safety manager
            self.safety_manager = SafetyManager(self.config.safety)
            
            # Initialize touch controller
            self.touch_controller = TouchController(self.adb_manager, self.safety_manager)
            
            self.logger.info("Core components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def start_enhancement(self, enhancement_config: EnhancementConfig) -> bool:
        """Start the enhancement process"""
        if not self.is_initialized:
            self.logger.error("Application not initialized")
            return False
        
        try:
            with LogContext(self.operation_logger, "start_enhancement",
                          target_level=enhancement_config.target_level,
                          max_attempts=enhancement_config.max_attempts) as ctx:
                
                # Create enhancement controller
                self.enhancement_controller = EnhancementController(
                    enhancement_config,
                    self.adb_manager,
                    self.image_analyzer,
                    self.touch_controller,
                    self.safety_manager
                )
                
                ctx.log_step("controller_created")
                
                # Start enhancement process
                self.is_running = True
                self.performance_logger.start_timer("total_enhancement")
                
                result = self.enhancement_controller.start_enhancement()
                
                self.performance_logger.end_timer("total_enhancement", logging.INFO)
                self.is_running = False
                
                # Log results
                if result.success:
                    self.logger.info(f"Enhancement completed successfully. "
                                   f"Attempts: {result.attempts_made}, "
                                   f"EXP gained: {result.exp_gained}")
                    ctx.log_step("enhancement_completed", True)
                else:
                    self.logger.error(f"Enhancement failed: {result.error_message}")
                    ctx.log_step("enhancement_failed", False)
                
                return result.success
                
        except EmergencyStopError:
            self.logger.warning("Enhancement stopped by emergency stop")
            return False
        except Exception as e:
            self.logger.error(f"Enhancement process failed: {e}", exc_info=True)
            return False
        finally:
            self.is_running = False
    
    def stop_enhancement(self):
        """Stop the enhancement process"""
        if self.enhancement_controller:
            self.enhancement_controller.stop_enhancement()
        self.is_running = False
        self.logger.info("Enhancement stop requested")
    
    def test_device_connection(self) -> bool:
        """Test ADB device connection"""
        try:
            if not self.adb_manager:
                self.adb_manager = ADBManager(self.config.device.device_id)
            
            devices = self.adb_manager.get_connected_devices()
            self.logger.info(f"Connected devices: {devices}")
            
            if not devices:
                self.logger.error("No ADB devices found")
                return False
            
            if self.adb_manager.connect_device():
                self.logger.info("Device connection test successful")
                
                # Test screen capture
                screen = self.adb_manager.capture_screen()
                if screen is not None:
                    self.logger.info(f"Screen capture test successful: {screen.shape}")
                    return True
                else:
                    self.logger.error("Screen capture test failed")
                    return False
            else:
                self.logger.error("Device connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Device connection test error: {e}")
            return False
    
    def test_image_analysis(self) -> bool:
        """Test image analysis functionality"""
        try:
            if not self.image_analyzer:
                template_dir = Path(self.config.template.template_dir)
                self.image_analyzer = ImageAnalyzer(str(template_dir))
            
            # Test template loading
            templates = self.image_analyzer.load_templates()
            self.logger.info(f"Loaded {len(templates)} templates")
            
            if not templates:
                self.logger.warning("No templates found - image analysis may not work properly")
                return False
            
            # Test with current screen if device is connected
            if self.adb_manager and self.adb_manager.is_device_connected():
                screen = self.adb_manager.capture_screen()
                if screen is not None:
                    game_state = self.image_analyzer.detect_game_state(screen)
                    self.logger.info(f"Current game state: {game_state}")
                    return True
            
            self.logger.info("Image analysis test completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Image analysis test error: {e}")
            return False
    
    def run_diagnostics(self) -> dict:
        """Run comprehensive diagnostics"""
        results = {
            'config_valid': False,
            'device_connected': False,
            'templates_loaded': False,
            'safety_manager_active': False
        }
        
        try:
            # Check configuration
            config_issues = self.config_manager.validate_config(self.config)
            results['config_valid'] = len(config_issues) == 0
            if config_issues:
                self.logger.warning(f"Configuration issues: {config_issues}")
            
            # Test device connection
            results['device_connected'] = self.test_device_connection()
            
            # Test image analysis
            results['templates_loaded'] = self.test_image_analysis()
            
            # Test safety manager
            if self.safety_manager:
                status = self.safety_manager.get_status_report()
                results['safety_manager_active'] = status['keyboard_listener_active']
            
            self.logger.info(f"Diagnostics completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Diagnostics failed: {e}")
            return results
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up application resources...")
        
        if self.safety_manager:
            self.safety_manager.stop_keyboard_listener()
        
        if self.enhancement_controller:
            self.enhancement_controller.stop_enhancement()
        
        self.is_running = False
        self.logger.info("Cleanup completed")


def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line interface parser"""
    parser = argparse.ArgumentParser(
        description="FGO Craft Essence Auto Enhancement Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--device-id', '-d',
        help='ADB device ID to use'
    )
    
    parser.add_argument(
        '--target-level', '-l',
        type=int,
        default=100,
        help='Target level for enhancement (default: 100)'
    )
    
    parser.add_argument(
        '--max-attempts', '-a',
        type=int,
        default=50,
        help='Maximum enhancement attempts (default: 50)'
    )
    
    parser.add_argument(
        '--target-ce',
        default='',
        help='Target craft essence name'
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test device connection and exit'
    )
    
    parser.add_argument(
        '--test-templates',
        action='store_true',
        help='Test template loading and exit'
    )
    
    parser.add_argument(
        '--diagnostics',
        action='store_true',
        help='Run diagnostics and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='FGO Auto Enhancement Tool 1.0.0'
    )
    
    return parser


def main():
    """Main entry point"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Initialize application
    app = MainApp(args.config)
    
    if not app.initialize():
        print("Failed to initialize application")
        sys.exit(1)
    
    try:
        # Handle test modes
        if args.test_connection:
            success = app.test_device_connection()
            sys.exit(0 if success else 1)
        
        if args.test_templates:
            success = app.test_image_analysis()
            sys.exit(0 if success else 1)
        
        if args.diagnostics:
            results = app.run_diagnostics()
            all_passed = all(results.values())
            print(f"Diagnostics results: {results}")
            sys.exit(0 if all_passed else 1)
        
        # Create enhancement configuration
        device_config = app.config.device
        if args.device_id:
            device_config.device_id = args.device_id
        
        enhancement_config = EnhancementConfig(
            target_craft_essence=args.target_ce,
            target_level=args.target_level,
            max_attempts=args.max_attempts,
            material_priority=[],
            device_id=device_config.device_id,
            screen_resolution=device_config.screen_resolution
        )
        
        # Start enhancement
        app.logger.info("Starting enhancement process...")
        success = app.start_enhancement(enhancement_config)
        
        if success:
            app.logger.info("Enhancement completed successfully")
        else:
            app.logger.error("Enhancement failed")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        app.logger.info("Interrupted by user")
        app.stop_enhancement()
        sys.exit(0)
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()