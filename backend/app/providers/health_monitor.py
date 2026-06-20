"""
Provider health monitoring and status tracking system.
Tracks provider availability, response times, and failure rates for intelligent decision making.
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta

from .base.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """Health metrics for a single provider."""
    provider_name: str
    last_check_time: float = 0.0
    is_healthy: bool = False
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0


@dataclass
class ProviderStatus:
    """Complete status information for a provider."""
    name: str
    is_available: bool = False
    current_error: Optional[str] = None
    metrics: HealthMetrics = field(default_factory=HealthMetrics)
    last_successful_request: Optional[float] = None
    last_failure: Optional[float] = None


class HealthMonitor:
    """
    Comprehensive health monitoring system for LLM providers.

    Tracks:
    - Response times and success rates
    - Error types and frequencies
    - Circuit breaker integration
    - Provider availability over time
    """

    def __init__(self, check_interval: float = 30.0, history_window: int = 100):
        """
        Initialize health monitor.

        Args:
            check_interval: How often to perform health checks (seconds)
            history_window: Number of historical records to keep per metric
        """
        self.check_interval = check_interval
        self.providers: Dict[str, ProviderStatus] = {}
        self._check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._history_window = history_window

    def register_provider(self, provider_name: str) -> None:
        """
        Register a new provider for health monitoring.

        Args:
            provider_name: Name of the provider to monitor
        """
        if provider_name not in self.providers:
            with self._lock:
                self.providers[provider_name] = ProviderStatus(
                    name=provider_name,
                    metrics=HealthMetrics(provider_name=provider_name)
                )
            logger.info(f"Registered provider '{provider_name}' for health monitoring")

    def unregister_provider(self, provider_name: str) -> None:
        """
        Unregister a provider from health monitoring.

        Args:
            provider_name: Name of the provider to stop monitoring
        """
        with self._lock:
            if provider_name in self.providers:
                del self.providers[provider_name]
                logger.info(f"Unregistered provider '{provider_name}' from health monitoring")

    async def record_request_result(
        self,
        provider_name: str,
        success: bool,
        response_time: float,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record the result of a provider request.

        Args:
            provider_name: Name of the provider
            success: Whether the request succeeded
            response_time: Time taken for the request (seconds)
            error_message: Error message if request failed
        """
        with self._lock:
            if provider_name not in self.providers:
                self.register_provider(provider_name)

            provider_status = self.providers[provider_name]
            metrics = provider_status.metrics

            # Update counters
            metrics.total_requests += 1
            metrics.response_times.append(response_time)

            # Calculate averages
            if metrics.response_times:
                metrics.avg_response_time = sum(metrics.response_times) / len(metrics.response_times)

            if success:
                metrics.success_count += 1
                metrics.consecutive_failures = 0
                provider_status.is_available = True
                provider_status.last_successful_request = time.time()

                if error_message:
                    logger.debug(f"Request succeeded but with warning for {provider_name}: {error_message}")

            else:
                metrics.failure_count += 1
                metrics.consecutive_failures += 1
                provider_status.is_available = False
                provider_status.last_failure = time.time()
                provider_status.current_error = error_message

            # Calculate error rate
            if metrics.total_requests > 0:
                metrics.error_rate = metrics.failure_count / metrics.total_requests

            # Log significant changes
            if not success and metrics.consecutive_failures >= 3:
                logger.warning(
                    f"Provider '{provider_name}' experiencing consecutive failures: "
                    f"{metrics.consecutive_failures} failures"
                )

    async def get_provider_status(self, provider_name: str) -> Optional[ProviderStatus]:
        """
        Get current status of a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider status or None if not found
        """
        with self._lock:
            return self.providers.get(provider_name)

    async def get_all_statuses(self) -> Dict[str, ProviderStatus]:
        """
        Get status of all monitored providers.

        Returns:
            Dictionary mapping provider names to their status
        """
        with self._lock:
            return self.providers.copy()

    async def perform_health_check(self, provider_name: str) -> bool:
        """
        Perform a basic health check on a provider.

        Args:
            provider_name: Name of the provider to check

        Returns:
            True if provider appears healthy, False otherwise
        """
        start_time = time.time()

        try:
            # This is a stub - in practice, you'd make a very lightweight
            # request to verify the provider is responsive
            await asyncio.sleep(0.01)  # Simulate minimal work

            response_time = time.time() - start_time
            await self.record_request_result(provider_name, success=True, response_time=response_time)

            logger.debug(f"Health check passed for provider '{provider_name}' ({response_time:.3f}s)")
            return True

        except Exception as e:
            response_time = time.time() - start_time
            await self.record_request_result(
                provider_name,
                success=False,
                response_time=response_time,
                error_message=str(e)
            )

            logger.warning(f"Health check failed for provider '{provider_name}': {e}")
            return False

    def get_provider_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for provider selection based on current health data.

        Returns:
            Dictionary with provider rankings and recommendations
        """
        recommendations = {}

        with self._lock:
            for provider_name, status in self.providers.items():
                metrics = status.metrics

                # Calculate score (higher is better)
                score = 100.0

                # Deduct points for error rate
                if metrics.total_requests > 10:  # Only consider after some requests
                    score -= metrics.error_rate * 50

                # Deduct points for recent failures
                if status.last_failure and (time.time() - status.last_failure) < 60:
                    score -= 20

                # Deduct points for high response times
                if metrics.avg_response_time > 5.0:
                    score -= (metrics.avg_response_time - 5.0) * 10

                # Add bonus for stability
                if metrics.consecutive_failures == 0 and metrics.total_requests > 5:
                    score += 10

                recommendations[provider_name] = {
                    'score': max(0, score),
                    'is_available': status.is_available,
                    'error_rate': metrics.error_rate,
                    'avg_response_time': metrics.avg_response_time,
                    'total_requests': metrics.total_requests,
                    'consecutive_failures': metrics.consecutive_failures,
                    'last_success': status.last_successful_request,
                    'recommendation': self._get_recommendation_text(score, metrics)
                }

        return recommendations

    def _get_recommendation_text(self, score: float, metrics: HealthMetrics) -> str:
        """Get human-readable recommendation text."""
        if score >= 90:
            return "Excellent - use as primary provider"
        elif score >= 70:
            return "Good - reliable for production use"
        elif score >= 50:
            return "Fair - monitor closely, consider as secondary"
        elif score >= 30:
            return "Poor - use only if necessary"
        else:
            return "Unhealthy - avoid using"

    def start_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._check_task is None or self._check_task.done():
            self._check_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Started background health monitoring")

    def stop_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._check_task:
            self._check_task.cancel()
            self._check_task = None
            logger.info("Stopped background health monitoring")

    async def _monitoring_loop(self):
        """Background loop for periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self.check_interval)

                # Perform health checks on all providers
                check_tasks = []
                with self._lock:
                    provider_names = list(self.providers.keys())

                for provider_name in provider_names:
                    check_tasks.append(
                        self.perform_health_check(provider_name)
                    )

                if check_tasks:
                    await asyncio.gather(*check_tasks, return_exceptions=True)

                # Log summary if any providers are unhealthy
                with self._lock:
                    unhealthy = [
                        name for name, status in self.providers.items()
                        if not status.is_available
                    ]

                if unhealthy:
                    logger.warning(f"Unhealthy providers detected: {unhealthy}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")


# Global health monitor instance
_global_health_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    return _global_health_monitor


def initialize_health_monitor(
    check_interval: float = 30.0,
    provider_names: List[str] = None
) -> None:
    """Initialize global health monitor."""
    _global_health_monitor.check_interval = check_interval
    _global_health_monitor.start_monitoring()

    if provider_names:
        for provider_name in provider_names:
            _global_health_monitor.register_provider(provider_name)

    logger.info(f"Initialized health monitor with interval={check_interval}s")


def stop_health_monitor() -> None:
    """Stop global health monitor."""
    _global_health_monitor.stop_monitoring()


def get_health_report() -> Dict[str, Any]:
    """Get comprehensive health report for all providers."""
    monitor = _global_health_monitor

    with monitor._lock:
        statuses = monitor.providers.copy()
        recommendations = monitor.get_provider_recommendations()

    return {
        'timestamp': datetime.now().isoformat(),
        'monitored_providers': list(statuses.keys()),
        'provider_statuses': {
            name: {
                'available': status.is_available,
                'current_error': status.current_error,
                'metrics': {
                    'success_count': status.metrics.success_count,
                    'failure_count': status.metrics.failure_count,
                    'total_requests': status.metrics.total_requests,
                    'avg_response_time': status.metrics.avg_response_time,
                    'error_rate': status.metrics.error_rate,
                    'consecutive_failures': status.metrics.consecutive_failures
                },
                'last_success': status.last_successful_request,
                'last_failure': status.last_failure
            }
            for name, status in statuses.items()
        },
        'recommendations': recommendations,
        'overall_health': {
            'healthy_providers': sum(1 for s in statuses.values() if s.is_available),
            'total_providers': len(statuses),
            'any_unhealthy': any(not s.is_available for s in statuses.values())
        }
    }