"""Logging setup and configuration for FGO auto enhancement tool"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .config_manager import LoggingConfig


class LoggerSetup:
    """Setup and configure logging for the application"""
    
    @staticmethod
    def setup_logging(config: LoggingConfig, logger_name: Optional[str] = None) -> logging.Logger:
        """Setup logging with the specified configuration"""
        
        # Get logger
        logger = logging.getLogger(logger_name)
        
        # Clear existing handlers to avoid duplication
        logger.handlers.clear()
        
        # Set log level
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if config.file_output:
            log_file_path = Path(config.log_file)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file_path),
                maxBytes=config.max_log_size,
                backupCount=config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    @staticmethod
    def setup_module_loggers(config: LoggingConfig) -> dict:
        """Setup loggers for all modules"""
        loggers = {}
        
        # Main application modules
        module_names = [
            'fgo_auto_enhance.main_app',
            'fgo_auto_enhance.adb_manager',
            'fgo_auto_enhance.image_analyzer',
            'fgo_auto_enhance.touch_controller',
            'fgo_auto_enhance.safety_manager',
            'fgo_auto_enhance.enhancement_controller',
            'fgo_auto_enhance.config_manager'
        ]
        
        for module_name in module_names:
            loggers[module_name] = LoggerSetup.setup_logging(config, module_name)
        
        return loggers


class CustomLogRecord(logging.LogRecord):
    """Custom log record with additional fields"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom fields
        self.operation_id = getattr(self, 'operation_id', None)
        self.device_id = getattr(self, 'device_id', None)
        self.game_state = getattr(self, 'game_state', None)


class OperationLogger:
    """Specialized logger for operation tracking"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.operation_counter = 0
        self.current_operation_id = None
    
    def start_operation(self, operation_name: str, **kwargs) -> str:
        """Start logging for a new operation"""
        self.operation_counter += 1
        self.current_operation_id = f"op_{self.operation_counter:04d}"
        
        extra = {
            'operation_id': self.current_operation_id,
            **kwargs
        }
        
        self.logger.info(f"Starting operation: {operation_name}", extra=extra)
        return self.current_operation_id
    
    def log_operation_step(self, step_name: str, success: bool = True, **kwargs):
        """Log an operation step"""
        extra = {
            'operation_id': self.current_operation_id,
            **kwargs
        }
        
        level = logging.INFO if success else logging.WARNING
        status = "SUCCESS" if success else "FAILED"
        
        self.logger.log(level, f"Operation step {step_name}: {status}", extra=extra)
    
    def end_operation(self, success: bool = True, **kwargs):
        """End the current operation"""
        extra = {
            'operation_id': self.current_operation_id,
            **kwargs
        }
        
        level = logging.INFO if success else logging.ERROR
        status = "COMPLETED" if success else "FAILED"
        
        self.logger.log(level, f"Operation {status}", extra=extra)
        self.current_operation_id = None
    
    def log_error(self, error_message: str, exception: Exception = None, **kwargs):
        """Log an error with optional exception details"""
        extra = {
            'operation_id': self.current_operation_id,
            **kwargs
        }
        
        if exception:
            self.logger.error(f"Error: {error_message} - {type(exception).__name__}: {exception}", 
                            extra=extra, exc_info=True)
        else:
            self.logger.error(f"Error: {error_message}", extra=extra)


class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers = {}
    
    def start_timer(self, timer_name: str):
        """Start a performance timer"""
        import time
        self.timers[timer_name] = time.time()
    
    def end_timer(self, timer_name: str, log_level: int = logging.DEBUG):
        """End a performance timer and log the duration"""
        import time
        
        if timer_name not in self.timers:
            self.logger.warning(f"Timer '{timer_name}' was not started")
            return
        
        duration = time.time() - self.timers[timer_name]
        del self.timers[timer_name]
        
        self.logger.log(log_level, f"Performance: {timer_name} took {duration:.3f} seconds")
    
    def log_metric(self, metric_name: str, value: float, unit: str = ""):
        """Log a performance metric"""
        self.logger.debug(f"Metric: {metric_name} = {value} {unit}")


def setup_exception_logging(logger: logging.Logger):
    """Setup global exception logging"""
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception


def create_structured_logger(config: LoggingConfig, module_name: str) -> tuple:
    """Create a structured logger with operation and performance loggers"""
    
    # Setup main logger
    main_logger = LoggerSetup.setup_logging(config, module_name)
    
    # Create specialized loggers
    operation_logger = OperationLogger(main_logger)
    performance_logger = PerformanceLogger(main_logger)
    
    return main_logger, operation_logger, performance_logger


class LogContext:
    """Context manager for structured logging"""
    
    def __init__(self, operation_logger: OperationLogger, operation_name: str, **kwargs):
        self.operation_logger = operation_logger
        self.operation_name = operation_name
        self.kwargs = kwargs
        self.operation_id = None
        self.success = True
    
    def __enter__(self):
        self.operation_id = self.operation_logger.start_operation(
            self.operation_name, **self.kwargs
        )
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.success = False
            self.operation_logger.log_error(
                f"Exception in {self.operation_name}",
                exc_value,
                **self.kwargs
            )
        
        self.operation_logger.end_operation(self.success, **self.kwargs)
        return False  # Don't suppress exceptions
    
    def log_step(self, step_name: str, success: bool = True, **kwargs):
        """Log a step within the operation"""
        self.operation_logger.log_operation_step(
            step_name, success, **{**self.kwargs, **kwargs}
        )
    
    def mark_failed(self):
        """Mark the operation as failed"""
        self.success = False