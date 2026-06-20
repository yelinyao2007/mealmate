"""
Multi-provider fallback strategy implementation.
Implements priority-based provider selection with health monitoring and circuit breaker integration.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from ..base.llm_provider import LLMProvider, LLMProviderError
from .circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a single provider in the fallback chain."""
    name: str
    priority: int  # Lower number = higher priority
    enabled: bool = True
    config: Dict[str, Any] = None


class FallbackStrategy:
    """
    Priority-based multi-provider fallback strategy.

    Implements the following logic:
    1. Try providers in order of priority (configurable via environment)
    2. Each provider has its own circuit breaker
    3. If provider fails, move to next priority level
    4. Continue until all providers exhausted or success achieved
    5. Fall back to demo mode if no providers available
    """

    def __init__(self):
        self.providers: List[ProviderConfig] = []
        self.enabled_providers: List[ProviderConfig] = []
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._health_check_interval: float = 60.0  # seconds

    def add_provider(self, name: str, priority: int = 0, **kwargs) -> None:
        """
        Add a provider to the fallback chain.

        Args:
            name: Provider name (must match provider class name)
            priority: Priority level (lower numbers = higher priority)
            **kwargs: Additional configuration options
        """
        provider_config = ProviderConfig(
            name=name,
            priority=priority,
            enabled=kwargs.get('enabled', True),
            config=kwargs.get('config', {})
        )

        self.providers.append(provider_config)
        logger.debug(f"Added provider '{name}' with priority {priority}")

    def initialize_from_config(self, provider_configs: Dict[str, Any]) -> None:
        """
        Initialize providers from configuration dictionary.

        Args:
            provider_configs: Dictionary containing provider configurations
        """
        self.providers.clear()

        # Sort providers by priority (ascending - lower numbers first)
        priority_order = ['primary', 'secondary', 'tertiary']

        for order in priority_order:
            if order in provider_configs:
                provider_name = provider_configs[order]
                if provider_name:
                    self.add_provider(
                        name=provider_name.lower(),
                        priority=priority_order.index(order),
                        config=provider_configs.get(f"{order}_config", {})
                    )

        # Filter enabled providers and sort by priority
        self.enabled_providers = [
            p for p in self.providers if p.enabled
        ]
        self.enabled_providers.sort(key=lambda x: x.priority)

        logger.info(
            f"Fallback strategy initialized with {len(self.enabled_providers)} "
            f"enabled providers: {[p.name for p in self.enabled_providers]}"
        )

    @property
    def provider_names(self) -> List[str]:
        """Get list of provider names in fallback order."""
        return [p.name for p in self.enabled_providers]

    async def execute_with_fallback(
        self,
        request_func: Callable[[LLMProvider], Any],
        fallback_to_demo: bool = True,
        **request_kwargs
    ) -> Any:
        """
        Execute request with automatic provider fallback.

        Args:
            request_func: Function that takes a provider and executes the request
            fallback_to_demo: Whether to fall back to demo mode if all providers fail
            **request_kwargs: Arguments to pass to the request function

        Returns:
            Result from successful provider execution

        Raises:
            LLMProviderError: If all providers fail and no demo fallback
        """
        last_error = None

        for provider_config in self.enabled_providers:
            try:
                # Check circuit breaker before attempting request
                circuit_breaker = get_circuit_breaker(
                    provider_config.name,
                    timeout=provider_config.config.get('circuit_breaker_timeout', 300.0),
                    failure_threshold=provider_config.config.get('failure_threshold', 3)
                )

                if not circuit_breaker.can_execute():
                    logger.warning(
                        f"Circuit breaker open for provider '{provider_config.name}', "
                        f"skipping to next provider"
                    )
                    continue

                # Execute request with this provider
                logger.info(f"Attempting request with provider '{provider_config.name}'")
                result = await request_func(provider_config.config, **request_kwargs)

                # Record success and reset circuit breaker
                circuit_breaker.record_success()
                logger.info(f"Request succeeded with provider '{provider_config.name}'")
                return result

            except Exception as e:
                last_error = e
                circuit_breaker.record_failure()

                # Log the error but continue to next provider
                logger.warning(
                    f"Provider '{provider_config.name}' failed: {type(e).__name__}: {e}, "
                    f"moving to next provider"
                )

                # If this was the last provider, break to handle demo fallback
                if provider_config == self.enabled_providers[-1]:
                    break

        # All configured providers failed
        if fallback_to_demo:
            logger.error(
                f"All {len(self.enabled_providers)} providers failed. "
                f"Last error: {last_error}. Falling back to demo mode."
            )
            raise LLMProviderError(
                f"All providers failed: {last_error}. Using demo mode."
            )
        else:
            logger.error(
                f"All {len(self.enabled_providers)} providers failed: {last_error}"
            )
            raise last_error

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all providers.

        Returns:
            Dictionary mapping provider names to health status (True = healthy)
        """
        results = {}

        for provider_config in self.enabled_providers:
            try:
                # Create a lightweight test request
                circuit_breaker = get_circuit_breaker(provider_config.name)

                if not circuit_breaker.can_execute():
                    results[provider_config.name] = False
                    continue

                # Simple health check - try a minimal request
                # This is a basic check; real providers might need different health checks
                test_request = {
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10,
                    "temperature": 0.1
                }

                # We'll use a timeout to prevent hanging
                try:
                    await asyncio.wait_for(
                        self._test_provider_health(provider_config.config),
                        timeout=5.0
                    )
                    results[provider_config.name] = True
                    circuit_breaker.record_success()

                except Exception as e:
                    results[provider_config.name] = False
                    circuit_breaker.record_failure()
                    logger.warning(f"Health check failed for '{provider_config.name}': {e}")

            except Exception as e:
                results[provider_config.name] = False
                logger.error(f"Health check error for '{provider_config.name}': {e}")

        return results

    async def _test_provider_health(self, provider_config: Dict[str, Any]) -> None:
        """Test individual provider health (stub implementation)."""
        # In a real implementation, this would make a very lightweight
        # request to each provider to verify they're responsive
        # For now, we'll just simulate a delay
        await asyncio.sleep(0.1)

    def start_health_monitoring(self, interval: float = 60.0) -> None:
        """
        Start background health monitoring task.

        Args:
            interval: Health check interval in seconds
        """
        self._health_check_interval = interval

        async def health_monitor_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    health_status = await self.health_check_all()
                    unhealthy = [name for name, healthy in health_status.items() if not healthy]

                    if unhealthy:
                        logger.warning(f"Unhealthy providers detected: {unhealthy}")

                    # Log circuit breaker states
                    cb_states = get_all_circuit_breaker_states()
                    for provider, state in cb_states.items():
                        if state['state'] != 'closed':
                            logger.info(f"Circuit breaker for {provider}: {state['state']}")

                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")

        self._health_monitor_task = asyncio.create_task(health_monitor_loop())
        logger.info(f"Started health monitoring with {interval}s intervals")

    def stop_health_monitoring(self) -> None:
        """Stop background health monitoring task."""
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            self._health_monitor_task = None
            logger.info("Stopped health monitoring")


# Global fallback strategy instance
_fallback_strategy = FallbackStrategy()


def get_fallback_strategy() -> FallbackStrategy:
    """Get global fallback strategy instance."""
    return _fallback_strategy


def initialize_fallback_strategy(config: Dict[str, Any]) -> None:
    """Initialize global fallback strategy from configuration."""
    _fallback_strategy.initialize_from_config(config)


def start_global_health_monitoring(interval: float = 60.0) -> None:
    """Start global health monitoring."""
    _fallback_strategy.start_health_monitoring(interval)


def stop_global_health_monitoring() -> None:
    """Stop global health monitoring."""
    _fallback_strategy.stop_health_monitoring()