"""Custom exceptions for FGO auto enhancement tool"""


class FGOAutoEnhanceError(Exception):
    """Base exception for FGO auto enhancement tool"""
    pass


class ADBError(FGOAutoEnhanceError):
    """ADB-related errors"""
    pass


class DeviceNotFoundError(ADBError):
    """Raised when no ADB device is found or connected"""
    pass


class DeviceConnectionError(ADBError):
    """Raised when ADB device connection fails"""
    pass


class ScreenCaptureError(ADBError):
    """Raised when screen capture fails"""
    pass


class TouchOperationError(ADBError):
    """Raised when touch operation fails"""
    pass


class ImageAnalysisError(FGOAutoEnhanceError):
    """Image analysis and template matching errors"""
    pass


class TemplateNotFoundError(ImageAnalysisError):
    """Raised when required template is not found"""
    pass


class GameStateError(ImageAnalysisError):
    """Raised when game state cannot be determined or is unexpected"""
    pass


class TemplateMatchError(ImageAnalysisError):
    """Raised when template matching fails"""
    pass


class EnhancementError(FGOAutoEnhanceError):
    """Enhancement process errors"""
    pass


class NavigationError(EnhancementError):
    """Raised when navigation to required screen fails"""
    pass


class MaterialSelectionError(EnhancementError):
    """Raised when material selection fails"""
    pass


class EnhancementExecutionError(EnhancementError):
    """Raised when enhancement execution fails"""
    pass


class TargetNotReachedError(EnhancementError):
    """Raised when target level/condition is not reached within max attempts"""
    pass


class SafetyError(FGOAutoEnhanceError):
    """Safety-related errors"""
    pass


class EmergencyStopError(SafetyError):
    """Raised when emergency stop is triggered"""
    pass


class AnomalyDetectedError(SafetyError):
    """Raised when anomalous behavior is detected"""
    pass


class OperationTimeoutError(SafetyError):
    """Raised when operation times out"""
    pass


class ConfigurationError(FGOAutoEnhanceError):
    """Configuration-related errors"""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid"""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing"""
    pass


class ConfigLoadError(ConfigurationError):
    """Raised when configuration loading fails"""
    pass


class ValidationError(FGOAutoEnhanceError):
    """Validation errors"""
    pass


class InvalidInputError(ValidationError):
    """Raised when input validation fails"""
    pass


class ResourceError(FGOAutoEnhanceError):
    """Resource-related errors"""
    pass


class TemplateDirectoryError(ResourceError):
    """Raised when template directory is missing or inaccessible"""
    pass


class LogDirectoryError(ResourceError):
    """Raised when log directory cannot be created or accessed"""
    pass


class RetryableError(FGOAutoEnhanceError):
    """Base class for errors that can be retried"""
    
    def __init__(self, message: str, retry_count: int = 0, max_retries: int = 3):
        super().__init__(message)
        self.retry_count = retry_count
        self.max_retries = max_retries
    
    def can_retry(self) -> bool:
        """Check if error can be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1


class TemporaryError(RetryableError):
    """Temporary error that should be retried"""
    pass


class NetworkError(TemporaryError):
    """Network-related temporary error"""
    pass


class DeviceTemporaryError(TemporaryError):
    """Temporary device error"""
    pass


class GameTemporaryError(TemporaryError):
    """Temporary game state error"""
    pass


def handle_adb_error(func):
    """Decorator for handling ADB-related errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "device not found" in str(e).lower():
                raise DeviceNotFoundError(f"ADB device not found: {e}")
            elif "device offline" in str(e).lower():
                raise DeviceConnectionError(f"ADB device offline: {e}")
            elif "timeout" in str(e).lower():
                raise OperationTimeoutError(f"ADB operation timeout: {e}")
            else:
                raise ADBError(f"ADB operation failed: {e}")
    return wrapper


def handle_image_error(func):
    """Decorator for handling image analysis errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "template" in str(e).lower():
                raise TemplateMatchError(f"Template matching failed: {e}")
            elif "state" in str(e).lower():
                raise GameStateError(f"Game state detection failed: {e}")
            else:
                raise ImageAnalysisError(f"Image analysis failed: {e}")
    return wrapper


def handle_safety_error(func):
    """Decorator for handling safety-related errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            raise EmergencyStopError("Emergency stop triggered by user")
        except Exception as e:
            if "anomaly" in str(e).lower():
                raise AnomalyDetectedError(f"Anomaly detected: {e}")
            elif "timeout" in str(e).lower():
                raise OperationTimeoutError(f"Safety timeout: {e}")
            else:
                raise SafetyError(f"Safety check failed: {e}")
    return wrapper


class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self, logger):
        self.logger = logger
        self.error_counts = {}
        self.recovery_strategies = {
            DeviceConnectionError: self._recover_device_connection,
            GameStateError: self._recover_game_state,
            TemplateMatchError: self._recover_template_match,
            NavigationError: self._recover_navigation
        }
    
    def handle_error(self, error: Exception, context: str = "") -> bool:
        """Handle error and attempt recovery"""
        error_type = type(error)
        
        # Log error
        self.logger.error(f"Error in {context}: {error}", exc_info=True)
        
        # Track error count
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Check if error can be retried
        if isinstance(error, RetryableError) and error.can_retry():
            error.increment_retry()
            self.logger.info(f"Retrying operation (attempt {error.retry_count}/{error.max_retries})")
            return True
        
        # Try recovery strategy
        if error_type in self.recovery_strategies:
            try:
                recovery_result = self.recovery_strategies[error_type](error)
                if recovery_result:
                    self.logger.info(f"Successfully recovered from {error_type.__name__}")
                    return True
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")
        
        # No recovery possible
        return False
    
    def _recover_device_connection(self, error: DeviceConnectionError) -> bool:
        """Attempt to recover from device connection error"""
        # Implementation would attempt device reconnection
        return False
    
    def _recover_game_state(self, error: GameStateError) -> bool:
        """Attempt to recover from game state error"""
        # Implementation would attempt to navigate back to known state
        return False
    
    def _recover_template_match(self, error: TemplateMatchError) -> bool:
        """Attempt to recover from template match error"""
        # Implementation would try alternative templates or lower thresholds
        return False
    
    def _recover_navigation(self, error: NavigationError) -> bool:
        """Attempt to recover from navigation error"""
        # Implementation would attempt to navigate back and retry
        return False
    
    def get_error_statistics(self) -> dict:
        """Get error statistics"""
        return {
            'error_counts': self.error_counts.copy(),
            'total_errors': sum(self.error_counts.values()),
            'error_types': list(self.error_counts.keys())
        }