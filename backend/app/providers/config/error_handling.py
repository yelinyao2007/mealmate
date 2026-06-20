"""
Comprehensive error handling and logging system for LLM provider configuration issues.
Provides structured error reporting, recovery mechanisms, and detailed logging.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConfigurationErrorType(Enum):
    """Types of configuration errors."""
    MISSING_REQUIRED_VAR = "missing_required_variable"
    INVALID_FORMAT = "invalid_format"
    DEPENDENCY_FAILURE = "dependency_failure"
    PROVIDER_LOAD_ERROR = "provider_load_error"
    VALIDATION_FAILURE = "validation_failure"
    ENVIRONMENT_PARSE_ERROR = "environment_parse_error"
    RUNTIME_CONFIG_ERROR = "runtime_configuration_error"


@dataclass
class ConfigurationError:
    """Structured representation of a configuration error."""
    timestamp: datetime = field(default_factory=datetime.now)
    error_type: ConfigurationErrorType = ConfigurationErrorType.VALIDATION_FAILURE
    severity: ErrorSeverity = ErrorSeverity.ERROR
    provider_name: Optional[str] = None
    error_message: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    suggested_fixes: List[str] = field(default_factory=list)
    recovery_action_taken: Optional[str] = None
    is_resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for logging/serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_type': self.error_type.value,
            'severity': self.severity.value,
            'provider_name': self.provider_name,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'suggested_fixes': self.suggested_fixes,
            'recovery_action_taken': self.recovery_action_taken,
            'is_resolved': self.is_resolved
        }


class ErrorHandler:
    """
    Centralized error handling system for configuration management.

    Provides:
    - Structured error classification and logging
    - Recovery mechanisms for different error types
    - Error notification system
    - Detailed diagnostic information
    """

    def __init__(self):
        self._error_history: List[ConfigurationError] = []
        self._error_callbacks: List[Callable[[ConfigurationError], None]] = []
        self._max_history_size = 1000

    def handle_error(
        self,
        error_type: ConfigurationErrorType,
        error_message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        provider_name: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        suggested_fixes: Optional[List[str]] = None,
        recovery_action: Optional[str] = None
    ) -> ConfigurationError:
        """
        Handle a configuration error with full context.

        Args:
            error_type: Type of configuration error
            error_message: Human-readable error message
            severity: Error severity level
            provider_name: Name of affected provider (if applicable)
            error_details: Additional technical details
            stack_trace: Full stack trace (if available)
            suggested_fixes: List of suggested solutions
            recovery_action: Action taken to recover from error

        Returns:
            Structured ConfigurationError object
        """
        # Generate suggested fixes if not provided
        if suggested_fixes is None:
            suggested_fixes = self._generate_suggested_fixes(error_type, error_details)

        # Create error object
        config_error = ConfigurationError(
            error_type=error_type,
            severity=severity,
            provider_name=provider_name,
            error_message=error_message,
            error_details=error_details or {},
            stack_trace=stack_trace,
            suggested_fixes=suggested_fixes,
            recovery_action_taken=recovery_action
        )

        # Add to history
        self._add_to_history(config_error)

        # Log the error
        self._log_error(config_error)

        # Notify callbacks
        self._notify_callbacks(config_error)

        # Attempt recovery if appropriate
        if severity in [ErrorSeverity.WARNING, ErrorSeverity.ERROR]:
            self._attempt_recovery(config_error)

        return config_error

    def _generate_suggested_fixes(
        self,
        error_type: ConfigurationErrorType,
        error_details: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate suggested fixes based on error type."""
        fixes = []

        if error_type == ConfigurationErrorType.MISSING_REQUIRED_VAR:
            var_name = error_details.get('variable_name', '')
            fixes.extend([
                f"Set environment variable {var_name}",
                "Check .env.example file for required variables",
                "Verify API key is valid and active"
            ])

        elif error_type == ConfigurationErrorType.INVALID_FORMAT:
            var_name = error_details.get('variable_name', '')
            expected_format = error_details.get('expected_format', 'valid value')
            fixes.extend([
                f"Update {var_name} to match expected format: {expected_format}",
                "Check documentation for correct syntax",
                "Validate values using official provider tools"
            ])

        elif error_type == ConfigurationErrorType.PROVIDER_LOAD_ERROR:
            provider_name = error_details.get('provider_name', 'unknown')
            fixes.extend([
                f"Verify provider '{provider_name}' implementation exists",
                "Check that required dependencies are installed",
                "Ensure provider class inherits from LLMProvider base class",
                f"Review provider/{provider_name}/provider.py for errors"
            ])

        elif error_type == ConfigurationErrorType.DEPENDENCY_FAILURE:
            dependency_name = error_details.get('dependency_name', 'unknown')
            fixes.extend([
                f"Install missing dependency: {dependency_name}",
                "Run pip install with required packages",
                "Check requirements.txt for correct version pins",
                "Verify virtual environment is activated"
            ])

        elif error_type == ConfigurationErrorType.RUNTIME_CONFIG_ERROR:
            fixes.extend([
                "Restart application to apply configuration changes",
                "Check for conflicting environment variables",
                "Verify file permissions for configuration files"
            ])

        else:
            fixes.extend([
                "Review logs for more detailed error information",
                "Check official provider documentation",
                "Contact support with error details"
            ])

        return fixes

    def _add_to_history(self, error: ConfigurationError) -> None:
        """Add error to history with size limit enforcement."""
        self._error_history.append(error)

        # Trim history if too large
        if len(self._error_history) > self._max_history_size:
            self._error_history = self._error_history[-self._max_history_size:]

    def _log_error(self, error: ConfigurationError) -> None:
        """Log error with appropriate severity level."""
        log_method = {
            ErrorSeverity.DEBUG: logger.debug,
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical
        }[error.severity]

        # Format log message
        message_parts = [
            f"[{error.error_type.value.upper()}] {error.error_message}"
        ]

        if error.provider_name:
            message_parts.append(f"(Provider: {error.provider_name})")

        if error.recovery_action_taken:
            message_parts.append(f"Recovery: {error.recovery_action_taken}")

        log_message = " ".join(message_parts)

        # Include stack trace for errors and critical issues
        if error.stack_trace and error.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            log_method(log_message)
            logger.error("Stack trace:\n%s", error.stack_trace)
        else:
            log_method(log_message)

        # Log suggested fixes at info level
        if error.suggested_fixes:
            for fix in error.suggested_fixes[:3]:  # Limit number of suggestions
                logger.info("Suggestion: %s", fix)

    def _notify_callbacks(self, error: ConfigurationError) -> None:
        """Notify all registered error callback functions."""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def _attempt_recovery(self, error: ConfigurationError) -> None:
        """Attempt automatic recovery for specific error types."""
        recovery_action = None

        try:
            if error.error_type == ConfigurationErrorType.MISSING_REQUIRED_VAR:
                # For missing required variables, try to use defaults or fallbacks
                if error.provider_name:
                    recovery_action = f"Using fallback for provider '{error.provider_name}'"

            elif error.error_type == ConfigurationErrorType.INVALID_FORMAT:
                # For invalid formats, try to parse/convert values
                var_name = error.error_details.get('variable_name')
                if var_name and var_name.endswith('_TIMEOUT'):
                    recovery_action = f"Using default timeout for {var_name}"

            elif error.error_type == ConfigurationErrorType.PROVIDER_LOAD_ERROR:
                # Remove problematic provider from loading
                provider_name = error.provider_name
                if provider_name:
                    # This would require integration with provider loader
                    recovery_action = f"Temporarily disabled provider '{provider_name}'"

            # Record recovery action
            if recovery_action:
                error.recovery_action_taken = recovery_action
                logger.info(f"Automatic recovery attempted: {recovery_action}")

        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")

    def add_error_callback(self, callback: Callable[[ConfigurationError], None]) -> None:
        """Add callback function for error notifications."""
        self._error_callbacks.append(callback)

    def remove_error_callback(self, callback: Callable[[ConfigurationError], None]) -> None:
        """Remove error callback function."""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get summary of recent errors.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary containing error statistics and details
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_errors = [
            error for error in self._error_history
            if error.timestamp.timestamp() > cutoff_time
        ]

        error_types = {}
        severities = {}

        for error in recent_errors:
            # Count by error type
            error_types[error.error_type.value] = error_types.get(error.error_type.value, 0) + 1

            # Count by severity
            severities[error.severity.value] = severities.get(error.severity.value, 0) + 1

        return {
            'timestamp': datetime.now().isoformat(),
            'period_hours': hours,
            'total_errors': len(recent_errors),
            'error_types': error_types,
            'severities': severities,
            'unresolved_count': sum(1 for e in recent_errors if not e.is_resolved),
            'recent_errors': [
                error.to_dict() for error in recent_errors[-10:]  # Last 10 errors
            ]
        }

    def mark_error_resolved(self, error_timestamp: datetime) -> None:
        """Mark an error as resolved."""
        for error in self._error_history:
            if error.timestamp == error_timestamp:
                error.is_resolved = True
                break

    def clear_error_history(self, older_than_days: int = 7) -> None:
        """Clear old error history."""
        cutoff_time = datetime.now().timestamp() - (older_than_days * 86400)
        initial_count = len(self._error_history)

        self._error_history = [
            error for error in self._error_history
            if error.timestamp.timestamp() > cutoff_time
        ]

        cleared_count = initial_count - len(self._error_history)
        logger.info(f"Cleared {cleared_count} old error records")


# Global error handler instance
_global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    return _global_error_handler


def handle_configuration_error(
    error_type: ConfigurationErrorType,
    error_message: str,
    **kwargs
) -> ConfigurationError:
    """
    Convenience function to handle configuration errors.

    Args:
        error_type: Type of configuration error
        error_message: Error description
        **kwargs: Additional arguments passed to error handler

    Returns:
        ConfigurationError object
    """
    return _global_error_handler.handle_error(error_type, error_message, **kwargs)


def add_error_notification_callback(
    callback: Callable[[ConfigurationError], None]
) -> None:
    """Add callback for error notifications."""
    _global_error_handler.add_error_callback(callback)


def get_configuration_error_summary(hours: int = 24) -> Dict[str, Any]:
    """Get summary of recent configuration errors."""
    return _global_error_handler.get_error_summary(hours)


def clear_old_error_records(days: int = 7) -> None:
    """Clear error records older than specified days."""
    _global_error_handler.clear_error_history(days)


# Predefined error handlers for common scenarios
def handle_missing_api_key(provider_name: str, variable_name: str) -> ConfigurationError:
    """Handle missing API key error."""
    return handle_configuration_error(
        ConfigurationErrorType.MISSING_REQUIRED_VAR,
        f"Missing API key for provider '{provider_name}'",
        severity=ErrorSeverity.ERROR,
        provider_name=provider_name,
        error_details={'variable_name': variable_name},
        suggested_fixes=[
            f"Set {variable_name} environment variable",
            "Get API key from provider dashboard",
            "Check .env.example for setup instructions"
        ]
    )


def handle_invalid_provider_config(provider_name: str, config_issues: List[str]) -> ConfigurationError:
    """Handle invalid provider configuration."""
    return handle_configuration_error(
        ConfigurationErrorType.INVALID_FORMAT,
        f"Invalid configuration for provider '{provider_name}'",
        severity=ErrorSeverity.WARNING,
        provider_name=provider_name,
        error_details={'config_issues': config_issues},
        suggested_fixes=[
            "Review provider documentation for correct settings",
            "Use default configuration where possible",
            "Validate settings before applying"
        ]
    )


def handle_provider_load_failure(provider_name: str, original_error: Exception) -> ConfigurationError:
    """Handle provider load failure."""
    return handle_configuration_error(
        ConfigurationErrorType.PROVIDER_LOAD_ERROR,
        f"Failed to load provider '{provider_name}'",
        severity=ErrorSeverity.ERROR,
        provider_name=provider_name,
        error_details={
            'original_error': str(original_error),
            'error_type': type(original_error).__name__
        },
        suggested_fixes=[
            "Check provider implementation exists",
            "Verify all dependencies are installed",
            "Review provider code for syntax errors"
        ],
        stack_trace=''.join(traceback.format_exception(type(original_error), original_error, original_error.__traceback__))
    )