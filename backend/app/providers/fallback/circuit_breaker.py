"""
Circuit breaker implementation for individual LLM providers.
Prevents cascading failures by temporarily disabling providers after consecutive failures.
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Represents the state of a circuit breaker."""
    failure_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    state: str = "closed"  # closed, open, half-open
    timeout: float = 300.0  # 5 minutes default timeout
    failure_threshold: int = 3  # Open after this many failures


class CircuitBreaker:
    """
    Circuit breaker for individual LLM providers.

    Implements the circuit breaker pattern to prevent cascading failures:
    - Closed: Normal operation, requests pass through
    - Open: Requests are blocked (circuit opened due to failures)
    - Half-Open: Limited requests allowed to test if service recovered
    """

    def __init__(self, timeout: float = 300.0, failure_threshold: int = 3):
        """
        Initialize circuit breaker.

        Args:
            timeout: Time in seconds before attempting recovery (half-open state)
            failure_threshold: Number of failures before opening circuit
        """
        self.state = CircuitBreakerState(
            timeout=timeout,
            failure_threshold=failure_threshold
        )
        self.provider_name: Optional[str] = None

    def record_success(self) -> None:
        """Record a successful request."""
        self.state.failure_count = 0
        self.state.last_success_time = time.time()
        self.state.state = "closed"
        logger.debug(f"Circuit breaker for {self.provider_name} reset to closed")

    def record_failure(self) -> None:
        """Record a failed request."""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()

        if self.state.failure_count >= self.state.failure_threshold:
            self.state.state = "open"
            logger.warning(
                f"Circuit breaker for {self.provider_name} opened "
                f"after {self.state.failure_count} failures"
            )

    def can_execute(self) -> bool:
        """
        Check if requests should be allowed through the circuit breaker.

        Returns:
            True if request should proceed, False if circuit is open
        """
        if self.state.state == "closed":
            return True

        elif self.state.state == "open":
            # Check if enough time has passed to try recovery
            current_time = time.time()
            if (current_time - self.state.last_failure_time) >= self.state.timeout:
                self.state.state = "half-open"
                self.state.last_success_time = current_time
                logger.info(f"Circuit breaker for {self.provider_name} moved to half-open")
                return True
            else:
                logger.debug(
                    f"Circuit breaker for {self.provider_name} still open, "
                    f"{self.state.timeout - (current_time - self.state.last_failure_time):.1f}s remaining"
                )
                return False

        elif self.state.state == "half-open":
            # In half-open state, allow only one request to test recovery
            logger.debug(f"Circuit breaker for {self.provider_name} in half-open state")
            return True

        return False

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state as dictionary."""
        current_time = time.time()
        time_until_recovery = (
            max(0, self.state.timeout - (current_time - self.state.last_failure_time))
            if self.state.state == "open"
            else 0
        )

        return {
            "provider": self.provider_name,
            "state": self.state.state,
            "failure_count": self.state.failure_count,
            "last_failure_time": self.state.last_failure_time,
            "last_success_time": self.state.last_success_time,
            "time_until_recovery": time_until_recovery,
            "failure_threshold": self.state.failure_threshold,
            "timeout": self.state.timeout
        }

    def set_provider(self, provider_name: str) -> None:
        """Set the provider name for this circuit breaker."""
        self.provider_name = provider_name


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different providers.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, provider_name: str, **kwargs) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a provider.

        Args:
            provider_name: Name of the provider
            **kwargs: Arguments to pass to CircuitBreaker constructor

        Returns:
            CircuitBreaker instance for the provider
        """
        if provider_name not in self._breakers:
            self._breakers[provider_name] = CircuitBreaker(**kwargs)

        breaker = self._breakers[provider_name]
        breaker.set_provider(provider_name)
        return breaker

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state of all circuit breakers."""
        return {
            name: breaker.get_state() for name, breaker in self._breakers.items()
        }

    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state."""
        for breaker in self._breakers.values():
            breaker.record_success()
        logger.info("All circuit breakers reset")


# Global circuit breaker manager
_circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker(provider_name: str, **kwargs) -> CircuitBreaker:
    """Get circuit breaker for provider (convenience function)."""
    return _circuit_breaker_manager.get_breaker(provider_name, **kwargs)


def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """Get states of all circuit breakers (for monitoring)."""
    return _circuit_breaker_manager.get_all_states()


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers (for testing/recovery)."""
    _circuit_breaker_manager.reset_all()