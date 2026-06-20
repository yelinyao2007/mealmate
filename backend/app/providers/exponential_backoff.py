"""
Exponential backoff implementation for retry attempts.
Provides intelligent delay calculation and jitter to prevent thundering herd problems.
"""

import asyncio
import logging
import random
import time
from typing import Callable, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Available backoff strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


@dataclass
class BackoffConfig:
    """
    Configuration for exponential backoff behavior.

    Args:
        base_delay: Base delay in seconds (minimum wait time)
        max_delay: Maximum delay in seconds (upper bound)
        multiplier: Multiplier for each retry attempt
        jitter_factor: Factor for adding randomness (0.0 to 1.0)
        max_attempts: Maximum number of retry attempts
        strategy: Type of backoff algorithm to use
    """
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter_factor: float = 0.1
    max_attempts: int = 3
    strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL


class ExponentialBackoff:
    """
    Exponential backoff with jitter for retry logic.

    Implements various backoff strategies to handle transient failures gracefully:
    - Exponential backoff: delay *= multiplier for each attempt
    - Linear backoff: delay += increment for each attempt  
    - Fixed backoff: constant delay regardless of attempt count

    Includes jitter to prevent thundering herd problems when multiple clients
    simultaneously retry after a service outage.
    """

    def __init__(self, config: Optional[BackoffConfig] = None):
        """
        Initialize backoff mechanism.

        Args:
            config: Backoff configuration (uses defaults if not provided)
        """
        self.config = config or BackoffConfig()
        self._attempt_count = 0
        self._last_attempt_time = 0.0

    def reset(self) -> None:
        """Reset attempt counter and timing information."""
        self._attempt_count = 0
        self._last_attempt_time = 0.0

    def can_retry(self) -> bool:
        """
        Check if another retry attempt should be made.

        Returns:
            True if retry should proceed, False if maximum attempts exceeded
        """
        return self._attempt_count < self.config.max_attempts

    def calculate_delay(self) -> float:
        """
        Calculate the delay before next retry attempt.

        Returns:
            Delay in seconds before next attempt
        """
        if self._attempt_count == 0:
            return 0.0  # First attempt - no delay needed

        base_delay = self._get_base_delay()

        # Add jitter to prevent thundering herd
        jittered_delay = self._add_jitter(base_delay)

        # Ensure delay doesn't exceed maximum
        final_delay = min(jittered_delay, self.config.max_delay)

        logger.debug(
            f"Calculated backoff delay: {final_delay:.3f}s "
            f"(attempt {self._attempt_count + 1}/{self.config.max_attempts})"
        )

        return final_delay

    def _get_base_delay(self) -> float:
        """Calculate base delay without jitter."""
        if self.config.strategy == BackoffStrategy.EXPONENTIAL:
            return self.config.base_delay * (self.config.multiplier ** self._attempt_count)

        elif self.config.strategy == BackoffStrategy.LINEAR:
            return self.config.base_delay + (self.config.multiplier * self._attempt_count)

        elif self.config.strategy == BackoffStrategy.FIXED:
            return self.config.base_delay

        else:
            # Default to exponential
            return self.config.base_delay * (self.config.multiplier ** self._attempt_count)

    def _add_jitter(self, delay: float) -> float:
        """
        Add random jitter to delay to prevent thundering herd.

        Args:
            delay: Base delay value

        Returns:
            Jittered delay value
        """
        if self.config.jitter_factor <= 0:
            return delay

        # Calculate jitter range: ±jitter_factor * delay
        jitter_range = delay * self.config.jitter_factor
        jitter_amount = random.uniform(-jitter_range, jitter_range)

        # Ensure result is non-negative
        jittered_delay = max(0.0, delay + jitter_amount)

        return jittered_delay

    def record_attempt(self) -> None:
        """Record that an attempt has been made."""
        self._attempt_count += 1
        self._last_attempt_time = time.time()

    @property
    def current_attempt(self) -> int:
        """Get current attempt number (1-based)."""
        return self._attempt_count + 1

    @property
    def remaining_attempts(self) -> int:
        """Get remaining retry attempts."""
        return max(0, self.config.max_attempts - self._attempt_count)

    @property
    def is_exhausted(self) -> bool:
        """Check if all retry attempts have been exhausted."""
        return self._attempt_count >= self.config.max_attempts


class RetryableTask:
    """
    Wrapper for making retryable function calls with exponential backoff.

    Provides a clean interface for executing functions with automatic retries
    and configurable backoff behavior.
    """

    def __init__(
        self,
        func: Callable[..., Any],
        backoff_config: Optional[BackoffConfig] = None,
        exception_types: Tuple[type, ...] = (Exception,)
    ):
        """
        Initialize retryable task wrapper.

        Args:
            func: Function to execute with retry logic
            backoff_config: Backoff configuration
            exception_types: Exception types that should trigger retries
        """
        self.func = func
        self.backoff = ExponentialBackoff(backoff_config)
        self.exception_types = exception_types

    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute function with retry logic and exponential backoff.

        Args:
            *args: Positional arguments to pass to function
            **kwargs: Keyword arguments to pass to function

        Returns:
            Result from successful function execution

        Raises:
            Last exception if all retry attempts fail
        """
        last_exception = None

        while self.backoff.can_retry():
            try:
                self.backoff.record_attempt()
                result = await self.func(*args, **kwargs)
                logger.info(f"Function succeeded on attempt {self.backoff.current_attempt}")
                return result

            except self.exception_types as e:
                last_exception = e
                self.backoff.record_attempt()

                if self.backoff.is_exhausted:
                    logger.error(
                        f"All {self.backoff.config.max_attempts} retry attempts exhausted"
                    )
                    break

                # Calculate and apply delay
                delay = self.backoff.calculate_delay()
                if delay > 0:
                    logger.warning(
                        f"Attempt {self.backoff.current_attempt} failed: {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

        # All attempts failed
        raise last_exception

    def reset(self) -> None:
        """Reset retry state."""
        self.backoff.reset()


# Global retry manager for common patterns
_global_retry_manager = RetryableTask(
    func=lambda: None,  # Placeholder - will be replaced by specific functions
    backoff_config=BackoffConfig(
        base_delay=1.0,
        max_delay=30.0,
        multiplier=2.0,
        jitter_factor=0.1,
        max_attempts=3
    )
)


def create_retryable_task(
    func: Callable[..., Any],
    backoff_config: Optional[BackoffConfig] = None,
    exception_types: Tuple[type, ...] = (Exception,)
) -> RetryableTask:
    """
    Create a new retryable task with specified parameters.

    Args:
        func: Function to make retryable
        backoff_config: Custom backoff configuration
        exception_types: Exception types that trigger retries

    Returns:
        Configured RetryableTask instance
    """
    return RetryableTask(func, backoff_config, exception_types)


def get_default_backoff_config() -> BackoffConfig:
    """Get default backoff configuration."""
    return BackoffConfig()


def get_retryable_function(
    func: Callable[..., Any],
    exception_types: Tuple[type, ...] = (Exception,)
) -> RetryableTask:
    """
    Get a retryable version of a function using global configuration.

    Args:
        func: Function to make retryable
        exception_types: Exception types that trigger retries

    Returns:
        RetryableTask wrapping the function
    """
    return create_retryable_task(
        func,
        backoff_config=_global_retry_manager.backoff.config,
        exception_types=exception_types
    )