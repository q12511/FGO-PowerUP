"""Configuration management for FGO auto enhancement tool"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field

from .safety_manager import SafetyConfig
from .enhancement_controller import EnhancementConfig


@dataclass
class DeviceConfig:
    """Device-specific configuration"""
    device_id: Optional[str] = None
    screen_resolution: Tuple[int, int] = (1080, 2340)
    adb_timeout: float = 30.0
    screencap_format: str = "png"


@dataclass
class TemplateConfig:
    """Template matching configuration"""
    template_dir: str = "templates"
    default_threshold: float = 0.8
    match_method: str = "TM_CCOEFF_NORMED"
    save_debug_images: bool = False
    debug_image_dir: str = "debug_images"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_file: str = "fgo_enhancement.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    file_output: bool = True


@dataclass
class AppConfig:
    """Main application configuration"""
    device: DeviceConfig = field(default_factory=DeviceConfig)
    template: TemplateConfig = field(default_factory=TemplateConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    enhancement: Optional[EnhancementConfig] = None


class ConfigManager:
    """Configuration file management"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self._config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """Load configuration from file"""
        if self._config is not None:
            return self._config
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                self._config = self._parse_config_data(config_data)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                self.logger.error(f"Failed to load config from {self.config_file}: {e}")
                self._config = AppConfig()
                
        else:
            self.logger.info(f"Config file {self.config_file} not found, using defaults")
            self._config = AppConfig()
            self.save_config()  # Save default config
        
        return self._config
    
    def save_config(self, config: AppConfig = None) -> bool:
        """Save configuration to file"""
        if config is not None:
            self._config = config
        
        if self._config is None:
            self.logger.error("No configuration to save")
            return False
        
        try:
            config_data = self._serialize_config(self._config)
            
            # Create directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config to {self.config_file}: {e}")
            return False
    
    def get_config(self) -> AppConfig:
        """Get current configuration"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            config = self.get_config()
            
            # Apply updates using dot notation
            for key, value in updates.items():
                self._set_nested_value(config, key, value)
            
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False
    
    def _parse_config_data(self, data: Dict[str, Any]) -> AppConfig:
        """Parse configuration data from dictionary"""
        config = AppConfig()
        
        # Parse device config
        if 'device' in data:
            device_data = data['device']
            config.device = DeviceConfig(
                device_id=device_data.get('device_id'),
                screen_resolution=tuple(device_data.get('screen_resolution', [1080, 2340])),
                adb_timeout=device_data.get('adb_timeout', 30.0),
                screencap_format=device_data.get('screencap_format', 'png')
            )
        
        # Parse template config
        if 'template' in data:
            template_data = data['template']
            config.template = TemplateConfig(
                template_dir=template_data.get('template_dir', 'templates'),
                default_threshold=template_data.get('default_threshold', 0.8),
                match_method=template_data.get('match_method', 'TM_CCOEFF_NORMED'),
                save_debug_images=template_data.get('save_debug_images', False),
                debug_image_dir=template_data.get('debug_image_dir', 'debug_images')
            )
        
        # Parse safety config
        if 'safety' in data:
            safety_data = data['safety']
            config.safety = SafetyConfig(
                min_wait_time=safety_data.get('min_wait_time', 0.5),
                max_wait_time=safety_data.get('max_wait_time', 2.0),
                tap_offset_range=safety_data.get('tap_offset_range', 10),
                operation_variance=safety_data.get('operation_variance', 0.3),
                anomaly_detection=safety_data.get('anomaly_detection', True),
                emergency_stop_key=safety_data.get('emergency_stop_key', 'f12'),
                swipe_duration_range=tuple(safety_data.get('swipe_duration_range', [200, 500])),
                max_consecutive_operations=safety_data.get('max_consecutive_operations', 50),
                break_interval=safety_data.get('break_interval', 30.0),
                break_duration=safety_data.get('break_duration', 5.0)
            )
        
        # Parse logging config
        if 'logging' in data:
            logging_data = data['logging']
            config.logging = LoggingConfig(
                log_level=logging_data.get('log_level', 'INFO'),
                log_file=logging_data.get('log_file', 'fgo_enhancement.log'),
                max_log_size=logging_data.get('max_log_size', 10 * 1024 * 1024),
                backup_count=logging_data.get('backup_count', 5),
                console_output=logging_data.get('console_output', True),
                file_output=logging_data.get('file_output', True)
            )
        
        # Parse enhancement config if present
        if 'enhancement' in data:
            enhancement_data = data['enhancement']
            config.enhancement = EnhancementConfig(
                target_craft_essence=enhancement_data.get('target_craft_essence', ''),
                target_level=enhancement_data.get('target_level', 100),
                max_attempts=enhancement_data.get('max_attempts', 50),
                material_priority=enhancement_data.get('material_priority', []),
                device_id=enhancement_data.get('device_id'),
                screen_resolution=tuple(enhancement_data.get('screen_resolution', [1080, 2340])),
                enhancement_timeout=enhancement_data.get('enhancement_timeout', 30.0),
                state_change_timeout=enhancement_data.get('state_change_timeout', 10.0)
            )
        
        return config
    
    def _serialize_config(self, config: AppConfig) -> Dict[str, Any]:
        """Serialize configuration to dictionary"""
        result = {}
        
        # Serialize device config
        result['device'] = asdict(config.device)
        
        # Serialize template config
        result['template'] = asdict(config.template)
        
        # Serialize safety config
        result['safety'] = asdict(config.safety)
        
        # Serialize logging config
        result['logging'] = asdict(config.logging)
        
        # Serialize enhancement config if present
        if config.enhancement is not None:
            result['enhancement'] = asdict(config.enhancement)
        
        return result
    
    def _set_nested_value(self, obj: Any, key: str, value: Any):
        """Set nested value using dot notation (e.g., 'device.screen_resolution')"""
        keys = key.split('.')
        current = obj
        
        for k in keys[:-1]:
            if hasattr(current, k):
                current = getattr(current, k)
            else:
                raise ValueError(f"Invalid config key: {key}")
        
        final_key = keys[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
        else:
            raise ValueError(f"Invalid config key: {key}")
    
    def create_default_config(self) -> AppConfig:
        """Create default configuration with sensible defaults"""
        return AppConfig(
            device=DeviceConfig(
                device_id=None,
                screen_resolution=(1080, 2340),
                adb_timeout=30.0,
                screencap_format="png"
            ),
            template=TemplateConfig(
                template_dir="templates",
                default_threshold=0.8,
                match_method="TM_CCOEFF_NORMED",
                save_debug_images=False,
                debug_image_dir="debug_images"
            ),
            safety=SafetyConfig(
                min_wait_time=0.5,
                max_wait_time=2.0,
                tap_offset_range=10,
                operation_variance=0.3,
                anomaly_detection=True,
                emergency_stop_key="f12",
                swipe_duration_range=(200, 500),
                max_consecutive_operations=50,
                break_interval=30.0,
                break_duration=5.0
            ),
            logging=LoggingConfig(
                log_level="INFO",
                log_file="fgo_enhancement.log",
                max_log_size=10 * 1024 * 1024,
                backup_count=5,
                console_output=True,
                file_output=True
            )
        )
    
    def validate_config(self, config: AppConfig = None) -> List[str]:
        """Validate configuration and return list of issues"""
        if config is None:
            config = self.get_config()
        
        issues = []
        
        # Validate device config
        if config.device.screen_resolution[0] <= 0 or config.device.screen_resolution[1] <= 0:
            issues.append("Invalid screen resolution")
        
        if config.device.adb_timeout <= 0:
            issues.append("ADB timeout must be positive")
        
        # Validate template config
        if not Path(config.template.template_dir).exists():
            issues.append(f"Template directory does not exist: {config.template.template_dir}")
        
        if not (0.0 <= config.template.default_threshold <= 1.0):
            issues.append("Template threshold must be between 0.0 and 1.0")
        
        # Validate safety config
        if config.safety.min_wait_time < 0 or config.safety.max_wait_time < config.safety.min_wait_time:
            issues.append("Invalid wait time configuration")
        
        if config.safety.tap_offset_range < 0:
            issues.append("Tap offset range must be non-negative")
        
        # Validate logging config
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.logging.log_level not in valid_log_levels:
            issues.append(f"Invalid log level: {config.logging.log_level}")
        
        return issues