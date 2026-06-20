"""
Multi-provider LLM system for MealMate.

This package provides a flexible, extensible framework for connecting to multiple
LLM providers with intelligent fallback, health monitoring, and configuration management.
"""

# Core abstraction
from .base.llm_provider import (
    LLMProvider, LLMProviderError, AuthError, RateLimitError,
    ModelNotFoundError, TimeoutError, ResourceLimitError
)

# Provider implementations - import optionally to handle missing dependencies
try:
    from .openai.provider import OpenAILLMProvider
except ImportError:
    OpenAILLMProvider = None

try:
    from .anthropic.provider import AnthropicLLMProvider
except ImportError:
    AnthropicLLMProvider = None

try:
    from .gemini.provider import GeminiLLMProvider
except ImportError:
    GeminiLLMProvider = None

try:
    from .local.provider import LocalLLMProvider
except ImportError:
    LocalLLMProvider = None

try:
    from .longcat.provider import LongcatLLMProvider
except ImportError:
    LongcatLLMProvider = None

# Fallback and circuit breaking
from .fallback.circuit_breaker import (
    CircuitBreaker, get_circuit_breaker, get_all_circuit_breaker_states,
    reset_all_circuit_breakers
)
from .fallback.fallback_strategy import (
    FallbackStrategy, get_fallback_strategy, initialize_fallback_strategy,
    start_global_health_monitoring, stop_global_health_monitoring
)

# Health monitoring
from .health_monitor import (
    HealthMonitor, get_health_monitor, initialize_health_monitor,
    stop_health_monitor, get_health_report
)

# Configuration management
from .config.provider_config import (
    EnvironmentConfigParser, get_config_parser, initialize_configuration_parser,
    get_enabled_provider_names, get_provider_config, get_global_settings
)
from .config.runtime_config import (
    RuntimeConfigurationManager, get_runtime_manager,
    start_global_configuration_watcher, stop_global_configuration_watcher,
    reload_configuration_from_environment, get_runtime_configuration_status
)
from .config.error_handling import (
    ErrorHandler, get_error_handler, handle_configuration_error,
    add_error_notification_callback, get_configuration_error_summary,
    clear_old_error_records, ConfigurationErrorType, ErrorSeverity
)

# Provider loading and factory
from .provider_loader import (
    ProviderLoader, get_provider_loader, initialize_provider_loader,
    load_provider_with_config, get_loading_summary, validate_all_enabled_providers
)

# Multi-provider client (main interface)
from .multi_provider_client import (
    MultiProviderLLMClient, get_multi_provider_client, initialize_multi_provider_client,
    shutdown_multi_provider_client
)

# Exponential backoff for retries
from .exponential_backoff import (
    ExponentialBackoff, BackoffStrategy, RetryableTask,
    create_retryable_task, get_default_backoff_config, get_retryable_function
)

__version__ = "1.0.0"
__all__ = [
    # Core
    'LLMProvider', 'LLMProviderError', 'AuthError', 'RateLimitError',
    'ModelNotFoundError', 'TimeoutError', 'ResourceLimitError',

    # Providers
    'OpenAILLMProvider', 'AnthropicLLMProvider', 'GeminiLLMProvider', 'LocalLLMProvider', 'LongcatLLMProvider',

    # Fallback and circuit breaking
    'CircuitBreaker', 'get_circuit_breaker', 'get_all_circuit_breaker_states',
    'reset_all_circuit_breakers', 'FallbackStrategy', 'get_fallback_strategy',
    'initialize_fallback_strategy', 'start_global_health_monitoring',
    'stop_global_health_monitoring',

    # Health monitoring
    'HealthMonitor', 'get_health_monitor', 'initialize_health_monitor',
    'stop_health_monitor', 'get_health_report',

    # Configuration
    'EnvironmentConfigParser', 'get_config_parser', 'initialize_configuration_parser',
    'get_enabled_provider_names', 'get_provider_config', 'get_global_settings',
    'RuntimeConfigurationManager', 'get_runtime_manager',
    'start_global_configuration_watcher', 'stop_global_configuration_watcher',
    'reload_configuration_from_environment', 'get_runtime_configuration_status',
    'ErrorHandler', 'get_error_handler', 'handle_configuration_error',
    'add_error_notification_callback', 'get_configuration_error_summary',
    'clear_old_error_records', 'ConfigurationErrorType', 'ErrorSeverity',

    # Loading and factory
    'ProviderLoader', 'get_provider_loader', 'initialize_provider_loader',
    'load_provider_with_config', 'get_loading_summary', 'validate_all_enabled_providers',

    # Main client
    'MultiProviderLLMClient', 'get_multi_provider_client', 'initialize_multi_provider_client',
    'shutdown_multi_provider_client',

    # Retry/backoff
    'ExponentialBackoff', 'BackoffStrategy', 'RetryableTask',
    'create_retryable_task', 'get_default_backoff_config', 'get_retryable_function'
]