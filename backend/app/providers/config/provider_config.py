"""
Provider configuration management system.
Parses environment variables and provides structured access to provider settings.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ProviderConfiguration:
    """Complete configuration for a single provider."""
    name: str
    enabled: bool = True
    priority: int = 0
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class EnvironmentConfigParser:
    """
    Parser for LLM provider environment variables.

    Supports the following environment variable patterns:
    - PRIMARY_PROVIDER=openai
    - OPENAI_API_KEY=sk-...
    - SECONDARY_PROVIDER=anthropic
    - ANTHROPIC_API_KEY=sk-ant-...

    Configuration is organized by provider type with optional priority ordering.
    """

    # Environment variable prefixes for each provider type
    PROVIDER_PREFIXES = {
        'openai': 'OPENAI_',
        'anthropic': 'ANTHROPIC_',
        'gemini': 'GOOGLE_',
        'local': 'LOCAL_',
        'longcat': 'LONGCAT_',
        'moonshot': 'MOONSHOT_',
        'stepfun': 'STEPFUN_'
    }

    # Required environment variables for each provider type
    REQUIRED_VARS = {
        'openai': ['API_KEY'],
        'anthropic': ['API_KEY'],
        'gemini': ['API_KEY'],
        'local': []  # Local providers have different requirements
        , 'longcat': ['API_KEY']
        , 'moonshot': ['API_KEY']
        , 'stepfun': ['API_KEY']
    }

    def __init__(self):
        self.providers: Dict[str, ProviderConfiguration] = {}
        self._parsed = False

    def parse_environment(self) -> None:
        """
        Parse all environment variables related to LLM providers.

        This method should be called once during application initialization.
        It reads all relevant environment variables and builds a structured
        configuration object.
        """
        if self._parsed:
            return

        logger.info("Parsing LLM provider environment variables...")

        # First pass: identify primary, secondary, tertiary providers
        provider_order = ['primary', 'secondary', 'tertiary']
        provider_configs = {}

        for order in provider_order:
            provider_key = f"{order.upper()}_PROVIDER"
            provider_name = os.getenv(provider_key)

            if provider_name:
                provider_name = provider_name.lower().strip()
                if provider_name in self.PROVIDER_PREFIXES:
                    provider_configs[order] = provider_name
                else:
                    logger.warning(
                        f"Unknown provider '{provider_name}' specified in {provider_key}. "
                        f"Valid options: {list(self.PROVIDER_PREFIXES.keys())}"
                    )

        # Second pass: collect all provider-specific configuration
        selected_providers = set(provider_configs.values())

        for provider_type, prefix in self.PROVIDER_PREFIXES.items():
            provider_config = self._collect_provider_settings(
                provider_type,
                prefix,
                is_selected=provider_type in selected_providers,
            )
            if provider_config:
                # Assign priority based on order in environment
                priority = provider_order.index(
                    next((k for k, v in provider_configs.items() if v == provider_type), 'tertiary')
                )

                self.providers[provider_type] = ProviderConfiguration(
                    name=provider_type,
                    enabled=True,
                    priority=priority,
                    config=provider_config
                )

        # Validate configurations
        self._validate_configurations()

        self._parsed = True
        logger.info(f"Parsed {len(self.providers)} provider configurations")

    def _collect_provider_settings(self, provider_type: str, prefix: str, is_selected: bool = False) -> Dict[str, Any]:
        """
        Collect all environment variables for a specific provider type.

        Args:
            provider_type: Type of provider (openai, anthropic, etc.)
            prefix: Environment variable prefix for this provider

        Returns:
            Dictionary of provider-specific configuration
        """
        config = {}

        # Get all environment variables that start with the prefix
        for env_var, value in os.environ.items():
            if env_var.startswith(prefix):
                # Remove prefix to get the actual setting name
                setting_name = env_var[len(prefix):].lower()

                # Convert snake_case to camelCase for some providers
                if provider_type in ('openai', 'moonshot', 'stepfun') and setting_name == 'base_url':
                    setting_name = 'baseUrl'
                elif provider_type in ('openai', 'moonshot', 'stepfun') and setting_name == 'timeout':
                    setting_name = 'timeout'
                elif provider_type == 'anthropic' and setting_name == 'base_url':
                    setting_name = 'baseUrl'

                config[setting_name] = value

        if not config and not is_selected:
            return {}

        # Add default values for common settings
        defaults = {
            'timeout': '30.0',
            'max_retries': '2',
            'circuit_breaker_timeout': '300.0',
            'failure_threshold': '3',
            'health_check_interval': '60.0',
            'model': 'LongCat-Flash-Chat'
        }

        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value

        # Convert numeric values where appropriate
        for key in ['timeout', 'max_retries', 'circuit_breaker_timeout', 'failure_threshold', 'health_check_interval']:
            if key in config:
                try:
                    config[key] = float(config[key])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid numeric value for {key}: {config[key]}, using default")
                    # Fall back to the configured default for this key
                    default_str = defaults.get(key, '30.0')
                    try:
                        config[key] = float(default_str)
                    except (ValueError, TypeError):
                        config[key] = 30.0

        return config

    def _validate_configurations(self) -> None:
        """
        Validate all provider configurations and log warnings for issues.

        Checks for:
        - Missing required API keys
        - Invalid configuration values
        - Conflicting settings
        """
        for provider_type, config in self.providers.items():
            self._validate_single_provider(config.name, config.config)

    def _validate_single_provider(self, provider_type: str, config: Dict[str, Any]) -> None:
        """
        Validate configuration for a single provider.

        Args:
            provider_type: Type of provider being validated
            config: Provider configuration dictionary
        """
        # Check for required API keys
        required_vars = self.REQUIRED_VARS.get(provider_type, [])

        for var_name in required_vars:
            env_var_name = f"{self.PROVIDER_PREFIXES[provider_type]}{var_name}"
            api_key = os.getenv(env_var_name)

            if not api_key:
                logger.warning(
                    f"Missing required API key for {provider_type}: {env_var_name}"
                )
            elif len(api_key) < 10:  # Basic validation
                logger.error(
                    f"Invalid API key format for {provider_type}: {env_var_name} "
                    "(too short or placeholder)"
                )

        # Provider-specific validations
        if provider_type == 'local':
            self._validate_local_provider(config)
        elif provider_type == 'openai':
            self._validate_openai_provider(config)
        elif provider_type == 'anthropic':
            self._validate_anthropic_provider(config)
        elif provider_type == 'gemini':
            self._validate_gemini_provider(config)

    def _validate_local_provider(self, config: Dict[str, Any]) -> None:
        """Validate local provider configuration."""
        backend = config.get('backend', 'ollama')

        if backend == 'ollama':
            host = config.get('host', 'http://localhost:11434')
            if not host.startswith(('http://', 'https://')):
                logger.warning(f"Invalid Ollama host format: {host}")
        elif backend == 'huggingface':
            model_path = config.get('model_path')
            if not model_path:
                logger.warning("HuggingFace backend requires 'model_path' configuration")

    def _validate_openai_provider(self, config: Dict[str, Any]) -> None:
        """Validate OpenAI provider configuration."""
        base_url = config.get('baseUrl') or config.get('base_url')
        if base_url and not base_url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid OpenAI base URL format: {base_url}")

    def _validate_anthropic_provider(self, config: Dict[str, Any]) -> None:
        """Validate Anthropic provider configuration."""
        # Anthropic uses the same base URL format as OpenAI
        base_url = config.get('base_url')
        if base_url and not base_url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid Anthropic base URL format: {base_url}")

    def _validate_gemini_provider(self, config: Dict[str, Any]) -> None:
        """Validate Google Gemini provider configuration."""
        # No additional validation needed beyond API key check

    def get_enabled_providers(self) -> List[str]:
        """
        Get list of enabled provider names sorted by priority.

        Returns:
            List of provider names in priority order (lowest number first)
        """
        if not self._parsed:
            self.parse_environment()

        return [
            name for name, config in sorted(
                self.providers.items(),
                key=lambda x: x[1].priority
            )
        ]

    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfiguration]:
        """
        Get configuration for a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider configuration or None if not found/enabled
        """
        if not self._parsed:
            self.parse_environment()

        return self.providers.get(provider_name.lower())

    def get_all_configs(self) -> Dict[str, ProviderConfiguration]:
        """
        Get all provider configurations.

        Returns:
            Dictionary mapping provider names to their configurations
        """
        if not self._parsed:
            self.parse_environment()

        return self.providers.copy()

    def get_global_settings(self) -> Dict[str, Any]:
        """
        Get global settings that apply to all providers.

        Returns:
            Dictionary of global configuration settings
        """
        global_env_vars = [
            'HEALTH_CHECK_INTERVAL',
            'CIRCUIT_BREAKER_TIMEOUT',
            'MAX_CONSECUTIVE_FAILURES',
            'LOG_LEVEL',
            'LOG_PROVIDER_REQUESTS'
        ]

        global_config = {}

        for var_name in global_env_vars:
            value = os.getenv(var_name)
            if value:
                # Convert numeric values
                if var_name in ['HEALTH_CHECK_INTERVAL', 'CIRCUIT_BREAKER_TIMEOUT', 'MAX_CONSECUTIVE_FAILURES']:
                    try:
                        global_config[var_name.lower()] = float(value)
                    except ValueError:
                        global_config[var_name.lower()] = value
                else:
                    global_config[var_name.lower()] = value

        return global_config

    def generate_config_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of current configuration.

        Useful for debugging and monitoring.

        Returns:
            Dictionary containing configuration summary
        """
        if not self._parsed:
            self.parse_environment()

        summary = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'enabled_providers': [],
            'global_settings': self.get_global_settings(),
            'provider_details': {}
        }

        for name, config in sorted(self.providers.items(), key=lambda x: x[1].priority):
            if config.enabled:
                summary['enabled_providers'].append({
                    'name': name,
                    'priority': config.priority,
                    'has_api_key': bool(os.getenv(f"{self.PROVIDER_PREFIXES[name]}API_KEY"))
                })

                # Don't expose sensitive information
                safe_config = {k: '***REDACTED***' if 'key' in k.lower() else v
                             for k, v in config.config.items()}
                summary['provider_details'][name] = {
                    'enabled': config.enabled,
                    'priority': config.priority,
                    'config': safe_config
                }

        return summary


# Global configuration parser instance
_global_config_parser = EnvironmentConfigParser()


def get_config_parser() -> EnvironmentConfigParser:
    """Get global configuration parser instance."""
    return _global_config_parser


def initialize_configuration_parser() -> None:
    """Initialize global configuration parser."""
    _global_config_parser.parse_environment()
    logger.info("LLM provider configuration initialized")


def get_enabled_provider_names() -> List[str]:
    """Get list of enabled provider names."""
    return _global_config_parser.get_enabled_providers()


def get_provider_config(provider_name: str) -> Optional[ProviderConfiguration]:
    """Get configuration for a specific provider."""
    return _global_config_parser.get_provider_config(provider_name)


def get_global_settings() -> Dict[str, Any]:
    """Get global configuration settings."""
    return _global_config_parser.get_global_settings()


def get_configuration_summary() -> Dict[str, Any]:
    """Get complete configuration summary."""
    return _global_config_parser.generate_config_summary()
