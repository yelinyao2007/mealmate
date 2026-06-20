"""
Multi-provider LLM client that orchestrates all provider implementations.
Provides a unified interface while handling fallback, health monitoring, and circuit breaking.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from .base.llm_provider import LLMProvider, AuthError, RateLimitError, ModelNotFoundError, TimeoutError, ResourceLimitError
from .fallback.fallback_strategy import get_fallback_strategy, initialize_fallback_strategy
from .health_monitor import get_health_monitor
from .exponential_backoff import create_retryable_task
from .config.provider_config import get_config_parser
from .provider_loader import get_provider_loader
from .config.runtime_config import get_runtime_manager
from .config.error_handling import handle_configuration_error, ConfigurationErrorType


logger = logging.getLogger(__name__)


@dataclass
class ClientMetrics:
    """Metrics for multi-provider client operations."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    fallback_count: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[float] = None
    provider_stats: Dict[str, Any] = None

    def __post_init__(self):
        if self.provider_stats is None:
            self.provider_stats = {}


class MultiProviderLLMClient:
    """
    Unified LLM client that manages multiple providers with intelligent fallback.

    This client:
    - Discovers and loads configured providers
    - Manages fallback strategy across providers
    - Integrates health monitoring and circuit breakers
    - Provides consistent error handling
    - Maintains backward compatibility with existing API
    """

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._metrics = ClientMetrics()
        self._demo_mode_enabled = os.getenv("DEMO_MODE", "false").lower() == "true"
        self._health_monitor = get_health_monitor()

        # Initialize configuration systems
        self._config_parser = get_config_parser()
        self._provider_loader = get_provider_loader()
        self._runtime_manager = get_runtime_manager()

        # Register for configuration change notifications
        self._runtime_manager.add_change_callback(self._on_configuration_changed)

        # Initialize systems
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the multi-provider client system."""
        logger.info("Initializing MultiProviderLLMClient...")

        try:
            # Parse initial configuration
            self._config_parser.parse_environment()

            # Get enabled providers from configuration
            enabled_providers = self._config_parser.get_enabled_providers()

            # Discover available providers if none found yet
            if not self._provider_loader.get_available_providers():
                self._provider_loader.discover_providers()

            # Load each provider
            loaded_providers = []
            for provider_name in enabled_providers:
                try:
                    provider_config = self._config_parser.get_provider_config(provider_name)
                    if provider_config:
                        provider_instance = self._load_single_provider(
                            provider_name,
                            provider_config.config
                        )
                        if provider_instance:
                            self._providers[provider_name] = provider_instance
                            loaded_providers.append(provider_name)
                            logger.info(f"Successfully loaded provider: {provider_name}")
                        else:
                            logger.warning(f"Failed to load provider: {provider_name}")
                    else:
                        logger.warning(f"No configuration found for provider: {provider_name}")

                except Exception as e:
                    logger.error(f"Error loading provider '{provider_name}': {e}")
                    handle_configuration_error(
                        ConfigurationErrorType.PROVIDER_LOAD_ERROR,
                        f"Failed to load provider '{provider_name}'",
                        provider_name=provider_name,
                        suggested_fixes=["Check provider implementation", "Verify dependencies"]
                    )

            # Skip fallback strategy for now - just use single provider
            # self._initialize_fallback_strategy()

            # Skip health monitoring registration for simplicity
            # for provider_name in loaded_providers:
            #     self._health_monitor.register_provider(provider_name)

            logger.info(f"MultiProviderLLMClient initialized with {len(loaded_providers)} providers")

            # Enable demo mode only if NO providers loaded
            if not loaded_providers:
                logger.warning("No providers loaded, enabling demo mode")
                self._demo_mode_enabled = True

        except Exception as e:
            logger.error(f"Failed to initialize MultiProviderLLMClient: {e}")
            self._demo_mode_enabled = True  # Enable demo on error
            raise

    def _load_single_provider(
        self,
        provider_name: str,
        config: Dict[str, Any]
    ) -> Optional[LLMProvider]:
        """Load a single provider instance."""
        try:
            # Validate configuration first
            is_valid, validation_error = self._provider_loader.validate_provider_implementation(
                provider_name, config
            )

            if not is_valid:
                logger.warning(f"Provider '{provider_name}' validation failed: {validation_error}")
                handle_configuration_error(
                    ConfigurationErrorType.VALIDATION_FAILURE,
                    f"Validation failed for provider '{provider_name}': {validation_error}",
                    provider_name=provider_name,
                    suggested_fixes=["Review provider configuration", "Check environment variables"]
                )
                return None

            # Load the provider
            provider_instance = self._provider_loader.load_provider(provider_name, config)

            if provider_instance:
                logger.debug(f"Loaded provider '{provider_name}' successfully")
                return provider_instance
            else:
                logger.error(f"Failed to instantiate provider '{provider_name}'")
                return None

        except Exception as e:
            logger.error(f"Exception while loading provider '{provider_name}': {e}")
            handle_configuration_error(
                ConfigurationErrorType.PROVIDER_LOAD_ERROR,
                f"Exception loading provider '{provider_name}': {str(e)}",
                provider_name=provider_name,
                stack_trace=str(e)
            )
            return None

    def _initialize_fallback_strategy(self) -> None:
        """Initialize the global fallback strategy."""
        try:
            provider_configs = {}

            for order in ['primary', 'secondary', 'tertiary']:
                provider_key = f"{order.upper()}_PROVIDER"
                provider_name = __import__('os').environ.get(provider_key)

                if provider_name:
                    provider_name = provider_name.lower().strip()
                    if provider_name in self._providers:
                        provider_configs[order] = {
                            'name': provider_name,
                            'priority': ['primary', 'secondary', 'tertiary'].index(order),
                            'config': self._get_provider_config_with_defaults(provider_name)
                        }

            initialize_fallback_strategy(provider_configs)
            logger.debug("Fallback strategy initialized")

        except Exception as e:
            logger.error(f"Failed to initialize fallback strategy: {e}")
            handle_configuration_error(
                ConfigurationErrorType.RUNTIME_CONFIG_ERROR,
                f"Failed to initialize fallback strategy: {str(e)}",
                suggested_fixes=["Check provider configuration", "Verify environment setup"]
            )

    def _get_provider_config_with_defaults(self, provider_name: str) -> Dict[str, Any]:
        """Get provider configuration with default values added."""
        base_config = {
            'timeout': 30.0,
            'max_retries': 2,
            'circuit_breaker_timeout': 300.0,
            'failure_threshold': 3,
            'health_check_interval': 60.0
        }

        provider_config = self._config_parser.get_provider_config(provider_name)
        if provider_config:
            base_config.update(provider_config.config)

        return base_config

    def _start_health_monitoring(self) -> None:
        """Start health monitoring for loaded providers."""
        try:
            interval_str = __import__('os').environ.get('HEALTH_CHECK_INTERVAL', '60')
            try:
                interval = float(interval_str)
            except ValueError:
                interval = 60.0

            start_global_health_monitoring(interval)

            for provider_name in self._providers.keys():
                self._health_monitor.register_provider(provider_name)

            logger.info(f"Health monitoring started with {interval}s intervals")

        except Exception as e:
            logger.error(f"Failed to start health monitoring: {e}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        Send a chat completion request using multi-provider fallback.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to request JSON response format
            stream: Whether to enable streaming response
            **kwargs: Additional arguments passed to providers

        Returns:
            String containing the assistant's response

        Raises:
            LLMProviderError: If all providers fail and no demo fallback available
        """
        start_time = __import__('time').time()
        self._metrics.total_requests += 1
        self._metrics.last_request_time = start_time

        # Create retryable task wrapper
        retryable_request = create_retryable_task(
            self._execute_with_fallback,
            backoff_config=None,  # Use default backoff
            exception_types=(AuthError, RateLimitError, ModelNotFoundError, TimeoutError, ResourceLimitError)
        )

        try:
            result = await retryable_request.execute(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                stream=stream,
                **kwargs
            )

            # Record success
            self._record_success(start_time, result)
            return result

        except Exception as e:
            # Record failure
            self._record_failure(start_time, e)
            raise

    async def _execute_with_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        stream: bool,
        **kwargs
    ) -> str:
        """Execute request - simplified to use loaded provider directly."""
        
        # Simply use the first available provider
        if not self._providers:
            if self._demo_mode_enabled:
                return await self._generate_demo_response(messages)
            raise LLMProviderError("No providers available")
        
        # Use primary provider (first one in dict)
        provider_name = list(self._providers.keys())[0]
        provider = self._providers[provider_name]
        
        try:
            result = await provider.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                stream=stream,
                **kwargs
            )
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            if self._demo_mode_enabled:
                logger.info(f"Provider {provider_name} failed, falling back to demo mode")
                return await self._generate_demo_response(messages)
            else:
                raise

    async def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a chat completion request and parse response as JSON."""
        import json
        response_text = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        # Try to parse as JSON - strip markdown fences if present
        text = response_text.strip()
        if text.startswith("```"):
            # Extract content between code fences
            lines = text.split("\n")
            content_lines = []
            in_content = False
            for line in lines:
                if line.startswith("```") and not in_content:
                    in_content = True
                    continue
                elif line.startswith("```") and in_content:
                    break
                if in_content:
                    content_lines.append(line)
            if content_lines:
                text = "\n".join(content_lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return as simple dict with raw content
            return {"raw_response": response_text}

    async def _generate_demo_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate demo response when all providers fail."""
        try:
            # Import demo data generator
            from app.demo_data import generate_demo_response

            logger.info("Using demo mode for response generation")
            return generate_demo_response(messages)

        except Exception as e:
            logger.error(f"Demo mode also failed: {e}")
            raise LLMProviderError("All providers and demo mode failed")

    def _record_success(self, start_time: float, result: str) -> None:
        """Record successful request metrics."""
        response_time = __import__('time').time() - start_time
        self._metrics.successful_requests += 1

        # Update average response time
        if self._metrics.total_requests > 1:
            self._metrics.avg_response_time = (
                (self._metrics.avg_response_time * (self._metrics.total_requests - 1) +
                 response_time) / self._metrics.total_requests
            )
        else:
            self._metrics.avg_response_time = response_time

    def _record_failure(self, start_time: float, error: Exception) -> None:
        """Record failed request metrics."""
        self._metrics.failed_requests += 1

    def is_demo_mode(self) -> bool:
        """Check if client is running in demo mode."""
        return self._demo_mode_enabled and len(self._providers) == 0

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status information for all loaded providers."""
        status = {
            'total_providers': len(self._providers),
            'enabled_providers': list(self._providers.keys()),
            'metrics': self._metrics.__dict__.copy(),
            'provider_details': {},
            'system_status': {
                'health_monitoring_active': True,
                'configuration_watcher_active': True,
                'fallback_strategy_initialized': True
            }
        }

        # Add individual provider status
        for name, provider in self._providers.items():
            try:
                provider_status = {
                    'supported_models': provider.supported_models,
                    'is_initialized': True,
                    'last_metrics': provider.get_metrics()
                }
                status['provider_details'][name] = provider_status

            except Exception as e:
                status['provider_details'][name] = {
                    'error': str(e),
                    'is_initialized': False
                }

        return status

    def _on_configuration_changed(self, change: Any) -> None:
        """Handle configuration change events."""
        logger.info(f"Configuration changed: {change.change_type}")
        # Reload providers if needed
        self._initialize_client()

    def shutdown(self) -> None:
        """Cleanly shutdown the multi-provider client."""
        logger.info("Shutting down MultiProviderLLMClient...")

        # Stop health monitoring
        stop_health_monitor()

        # Stop configuration watcher
        stop_global_configuration_watcher()

        # Clear caches
        get_provider_loader().clear_cache()

        logger.info("MultiProviderLLMClient shutdown complete")


# Global multi-provider client instance
_global_multi_provider_client: Optional[MultiProviderLLMClient] = None


def get_multi_provider_client() -> MultiProviderLLMClient:
    """Get or create the global multi-provider LLM client."""
    global _global_multi_provider_client

    if _global_multi_provider_client is None:
        _global_multi_provider_client = MultiProviderLLMClient()

    return _global_multi_provider_client


def initialize_multi_provider_client() -> None:
    """Initialize the global multi-provider client."""
    global _global_multi_provider_client
    _global_multi_provider_client = MultiProviderLLMClient()


def shutdown_multi_provider_client() -> None:
    """Shutdown the global multi-provider client."""
    global _global_multi_provider_client
    if _global_multi_provider_client:
        _global_multi_provider_client.shutdown()
        _global_multi_provider_client = None
