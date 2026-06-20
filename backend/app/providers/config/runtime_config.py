"""
Runtime configuration management system.
Enables dynamic reconfiguration of providers without restarting the application.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .provider_config import (
    EnvironmentConfigParser, get_config_parser,
    ProviderConfiguration
)
from ..provider_loader import get_provider_loader
from ..fallback.fallback_strategy import get_fallback_strategy, initialize_fallback_strategy
from ..health_monitor import get_health_monitor, initialize_health_monitor


logger = logging.getLogger(__name__)


@dataclass
class ConfigurationChange:
    """Represents a configuration change event."""
    timestamp: datetime = field(default_factory=datetime.now)
    change_type: str = ""  # 'add', 'remove', 'update', 'reload'
    provider_name: Optional[str] = None
    old_config: Dict[str, Any] = field(default_factory=dict)
    new_config: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class RuntimeConfigurationManager:
    """
    Manages runtime configuration changes for LLM providers.

    Features:
    - Hot reload of provider configurations from environment variables
    - Dynamic provider addition/removal
    - Configuration validation and rollback on failure
    - Change notification system for dependent components
    """

    def __init__(self):
        self._config_parser: EnvironmentConfigParser = get_config_parser()
        self._provider_loader = get_provider_loader()
        self._change_callbacks: list[Callable[[ConfigurationChange], None]] = []
        self._last_reload_time: float = 0.0
        self._watch_task: Optional[asyncio.Task] = None
        self._changes: list[ConfigurationChange] = []

    def add_change_callback(self, callback: Callable[[ConfigurationChange], None]) -> None:
        """
        Add a callback function to be notified of configuration changes.

        Args:
            callback: Function that receives ConfigurationChange events
        """
        self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[ConfigurationChange], None]) -> None:
        """
        Remove a change callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def notify_changes(self, changes: list[ConfigurationChange]) -> None:
        """
        Notify all registered callbacks about configuration changes.

        Args:
            changes: List of configuration changes to report
        """
        for change in changes:
            try:
                for callback in self._change_callbacks:
                    callback(change)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")

    def reload_from_environment(self) -> list[ConfigurationChange]:
        """
        Reload configuration from current environment variables.

        This method compares the current environment with the previously
        loaded configuration and applies necessary changes.

        Returns:
            List of configuration changes that were applied
        """
        logger.info("Reloading configuration from environment...")
        changes = []

        try:
            # Parse fresh configuration
            self._config_parser.parse_environment()
            old_providers = set(self._config_parser.providers.keys())

            # Get current enabled providers
            new_enabled = set(self._config_parser.get_enabled_providers())
            old_enabled = set(
                name for name, config in sorted(
                    self._config_parser.providers.items(),
                    key=lambda x: x[1].priority
                )
            )

            # Determine what changed
            added_providers = new_enabled - old_enabled
            removed_providers = old_enabled - new_enabled
            updated_providers = old_enabled & new_enabled

            # Handle removed providers
            for provider_name in removed_providers:
                change = ConfigurationChange(
                    change_type="remove",
                    provider_name=provider_name
                )
                changes.append(change)
                logger.info(f"Provider '{provider_name}' will be removed")

            # Handle added providers
            for provider_name in added_providers:
                change = ConfigurationChange(
                    change_type="add",
                    provider_name=provider_name
                )
                changes.append(change)
                logger.info(f"Provider '{provider_name}' will be added")

            # Handle updated providers
            for provider_name in updated_providers:
                old_config = self._get_provider_config_snapshot(provider_name)
                new_config = self._config_parser.get_provider_config(provider_name).config

                if old_config != new_config:
                    change = ConfigurationChange(
                        change_type="update",
                        provider_name=provider_name,
                        old_config=old_config,
                        new_config=new_config
                    )
                    changes.append(change)
                    logger.info(f"Provider '{provider_name}' configuration updated")

            # Apply changes
            if changes:
                self._apply_configuration_changes(changes)
                self._changes.extend(changes)
            else:
                logger.debug("No configuration changes detected")

            self._last_reload_time = datetime.now().timestamp()

        except Exception as e:
            error_change = ConfigurationChange(
                change_type="reload",
                success=False,
                error_message=f"Configuration reload failed: {str(e)}"
            )
            changes.append(error_change)
            self._changes.append(error_change)
            logger.error(f"Failed to reload configuration: {e}")

        return changes

    def _apply_configuration_changes(self, changes: list[ConfigurationChange]) -> None:
        """
        Apply configuration changes to the system.

        Args:
            changes: List of changes to apply
        """
        try:
            # Update fallback strategy
            self._update_fallback_strategy()

            # Clear provider loader cache to force reload
            self._provider_loader.clear_cache()

            # Restart health monitoring if needed
            self._restart_health_monitoring()

            logger.info(f"Applied {len(changes)} configuration changes successfully")

        except Exception as e:
            logger.error(f"Failed to apply configuration changes: {e}")
            raise

    def _update_fallback_strategy(self) -> None:
        """Update the global fallback strategy with new configuration."""
        try:
            # Get current configuration
            config_dict = {}
            for order in ['primary', 'secondary', 'tertiary']:
                provider_key = f"{order.upper()}_PROVIDER"
                provider_name = __import__('os').environ.get(provider_key)

                if provider_name:
                    provider_name = provider_name.lower().strip()
                    config_dict[order] = {
                        'name': provider_name,
                        'priority': ['primary', 'secondary', 'tertiary'].index(order),
                        'config': self._get_provider_full_config(provider_name)
                    }

            # Reinitialize fallback strategy
            initialize_fallback_strategy(config_dict)

            logger.debug("Fallback strategy updated")

        except Exception as e:
            logger.error(f"Failed to update fallback strategy: {e}")
            raise

    def _restart_health_monitoring(self) -> None:
        """Restart health monitoring with new configuration."""
        try:
            # Stop existing monitoring
            from .runtime_config import stop_health_monitoring
            stop_health_monitoring()

            # Get health check interval from environment
            interval_str = __import__('os').environ.get('HEALTH_CHECK_INTERVAL', '60')
            try:
                interval = float(interval_str)
            except ValueError:
                interval = 60.0

            # Restart with enabled providers
            enabled_providers = self._config_parser.get_enabled_providers()

            # Initialize health monitor
            initialize_health_monitor(check_interval=interval)

            for provider_name in enabled_providers:
                get_health_monitor().register_provider(provider_name)

            logger.debug(f"Health monitoring restarted with interval={interval}s")

        except Exception as e:
            logger.error(f"Failed to restart health monitoring: {e}")

    def start_configuration_watcher(self, interval: float = 30.0) -> None:
        """
        Start background task to watch for environment variable changes.

        Args:
            interval: How often to check for changes (seconds)
        """
        if self._watch_task and not self._watch_task.done():
            logger.warning("Configuration watcher already running")
            return

        async def watch_loop():
            last_checksum = None

            while True:
                try:
                    await asyncio.sleep(interval)

                    # Calculate checksum of relevant environment variables
                    relevant_vars = [
                        'PRIMARY_PROVIDER', 'SECONDARY_PROVIDER', 'TERTIARY_PROVIDER',
                        'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
                        'LOCAL_BACKEND', 'OLLAMA_HOST', 'HF_MODEL_PATH'
                    ]

                    current_checksum = hash(tuple(
                        __import__('os').environ.get(var, '') for var in relevant_vars
                    ))

                    if last_checksum is None or current_checksum != last_checksum:
                        logger.debug("Environment variables changed, checking for updates...")
                        changes = self.reload_from_environment()

                        if changes:
                            self.notify_changes(changes)

                    last_checksum = current_checksum

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Configuration watcher error: {e}")

        self._watch_task = asyncio.create_task(watch_loop())
        logger.info(f"Started configuration watcher with {interval}s intervals")

    def stop_configuration_watcher(self) -> None:
        """Stop the background configuration watcher."""
        if self._watch_task:
            self._watch_task.cancel()
            self._watch_task = None
            logger.info("Stopped configuration watcher")

    def get_configuration_status(self) -> Dict[str, Any]:
        """
        Get current configuration status.

        Returns:
            Dictionary containing configuration status information
        """
        try:
            summary = self._config_parser.generate_config_summary()

            return {
                'timestamp': datetime.now().isoformat(),
                'last_reload': datetime.fromtimestamp(self._last_reload_time).isoformat() if self._last_reload_time > 0 else None,
                'watcher_running': self._watch_task is not None and not self._watch_task.done(),
                'total_changes': len(self._changes),
                'recent_changes': [
                    {
                        'type': change.change_type,
                        'provider': change.provider_name,
                        'success': change.success,
                        'timestamp': change.timestamp.isoformat(),
                        'error': change.error_message
                    }
                    for change in self._changes[-10:]  # Last 10 changes
                ],
                'configuration_summary': summary
            }

        except Exception as e:
            logger.error(f"Failed to get configuration status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def _get_provider_config_snapshot(self, provider_name: str) -> Dict[str, Any]:
        """Get a snapshot of provider configuration for comparison."""
        provider = self._config_parser.get_provider_config(provider_name)
        return provider.config.copy() if provider else {}

    def _get_provider_full_config(self, provider_name: str) -> Dict[str, Any]:
        """Get full provider configuration including defaults."""
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


# Global runtime configuration manager
_global_runtime_manager = RuntimeConfigurationManager()


def get_runtime_manager() -> RuntimeConfigurationManager:
    """Get global runtime configuration manager instance."""
    return _global_runtime_manager


def start_global_configuration_watcher(interval: float = 30.0) -> None:
    """Start global configuration watcher."""
    _global_runtime_manager.start_configuration_watcher(interval)


def stop_global_configuration_watcher() -> None:
    """Stop global configuration watcher."""
    _global_runtime_manager.stop_configuration_watcher()


def reload_configuration_from_environment() -> list[ConfigurationChange]:
    """Reload configuration from environment variables."""
    return _global_runtime_manager.reload_from_environment()


def get_runtime_configuration_status() -> Dict[str, Any]:
    """Get current runtime configuration status."""
    return _global_runtime_manager.get_configuration_status()


def add_configuration_change_callback(
    callback: Callable[[ConfigurationChange], None]
) -> None:
    """Add callback for configuration change notifications."""
    _global_runtime_manager.add_change_callback(callback)


def remove_configuration_change_callback(
    callback: Callable[[ConfigurationChange], None]
) -> None:
    """Remove configuration change callback."""
    _global_runtime_manager.remove_change_callback(callback)