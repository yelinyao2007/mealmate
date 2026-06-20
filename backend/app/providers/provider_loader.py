"""
Dynamic LLM provider loader and factory.
Handles discovery, instantiation, and validation of provider implementations.
"""

import importlib
import logging
import os
import sys
from typing import Dict, Any, Type, Optional, List, Tuple
from dataclasses import dataclass

from .base.llm_provider import LLMProvider
from .config.provider_config import (
    get_config_parser, EnvironmentConfigParser
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderMetadata:
    """Metadata about a discovered provider implementation."""
    name: str
    class_name: str
    module_path: str
    file_path: str
    is_valid: bool = False
    error_message: Optional[str] = None


class ProviderLoader:
    """
    Dynamic provider discovery and loading system.

    Responsibilities:
    - Discover available provider implementations
    - Validate provider classes and their interfaces
    - Instantiate providers with proper configuration
    - Handle provider loading errors gracefully
    """

    # Mapping of provider names to their expected module and class paths
    PROVIDER_MAPPING = {
        'openai': ('providers.openai', 'OpenAILLMProvider'),
        'anthropic': ('providers.anthropic', 'AnthropicLLMProvider'),
        'gemini': ('providers.gemini', 'GeminiLLMProvider'),
        'local': ('providers.local', 'LocalLLMProvider'),
        'longcat': ('providers.longcat', 'LongcatLLMProvider'),
        'moonshot': ('providers.openai', 'OpenAILLMProvider')
    }

    def __init__(self):
        self._discovered_providers: Dict[str, ProviderMetadata] = {}
        self._instantiated_providers: Dict[str, LLMProvider] = {}
        self._validation_cache: Dict[str, bool] = {}

    def discover_providers(self) -> Dict[str, ProviderMetadata]:
        """
        Discover all available provider implementations.

        Scans the providers directory structure and validates each
        provider's interface compliance.

        Returns:
            Dictionary mapping provider names to their metadata
        """
        from pathlib import Path
        base_path = Path(__file__).parent.parent.parent
        env_path = base_path / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
        
        logger.info("Discovering LLM provider implementations...")

        for provider_name in self.PROVIDER_MAPPING.keys():
            try:
                module_path, class_name = self.PROVIDER_MAPPING[provider_name]
                file_path = str(base_path / "app" / module_path.replace('.', '/') / "provider.py")

                # Check if provider module exists
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        f"{provider_name}_provider",
                        file_path
                    )
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Cannot find module at {file_path}")
                    
                    # Load using parent package to handle relative imports
                    import sys
                    parent_name = f"app.providers.{provider_name}"
                    if parent_name in sys.modules:
                        parent = sys.modules[parent_name]
                    else:
                        # Create a fake parent module
                        import types
                        parent = types.ModuleType(parent_name)
                        parent.__file__ = str(base_path / "app" / "providers" / "__init__.py")
                        sys.modules[parent_name] = parent
                    
                    spec.submodule_search_locations = [str(base_path / "app" / "providers")]
                    module = importlib.util.module_from_spec(spec)
                    module.__package__ = parent_name
                    spec.loader.exec_module(module)

                    # Get the provider class
                    provider_class = getattr(module, class_name)
                    is_valid = issubclass(provider_class, LLMProvider) and provider_class != LLMProvider

                    metadata = ProviderMetadata(
                        name=provider_name,
                        class_name=class_name,
                        module_path=module_path,
                        file_path=file_path,
                        is_valid=True
                    )

                except (ImportError, AttributeError, TypeError) as e:
                    metadata = ProviderMetadata(
                        name=provider_name,
                        class_name=self.PROVIDER_MAPPING[provider_name][1],
                        module_path=self.PROVIDER_MAPPING[provider_name][0],
                        file_path=f"app/{self.PROVIDER_MAPPING[provider_name][0].replace('.', '/')}/provider.py",
                        is_valid=False,
                        error_message=str(e)
                    )

                self._discovered_providers[provider_name] = metadata

                if metadata.is_valid:
                    logger.debug(f"Discovered valid provider: {provider_name}")
                else:
                    logger.warning(f"Discovered invalid provider: {provider_name} - {metadata.error_message}")

            except Exception as e:
                logger.error(f"Error discovering provider {provider_name}: {e}")
                self._discovered_providers[provider_name] = ProviderMetadata(
                    name=provider_name,
                    class_name="Unknown",
                    module_path="unknown",
                    file_path="unknown",
                    is_valid=False,
                    error_message=f"Discovery failed: {str(e)}"
                )

        return self._discovered_providers.copy()

    def validate_provider_implementation(
        self,
        provider_name: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a provider can be instantiated with given configuration.

        Args:
            provider_name: Name of the provider to validate
            config: Configuration dictionary for the provider

        Returns:
            Tuple of (is_valid, error_message)
        """
        cache_key = f"{provider_name}_{hash(str(sorted(config.items())))}"

        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key], None

        if provider_name not in self._discovered_providers:
            error_msg = f"Provider '{provider_name}' not discovered"
            self._validation_cache[cache_key] = False
            return False, error_msg

        metadata = self._discovered_providers[provider_name]

        if not metadata.is_valid:
            self._validation_cache[cache_key] = False
            return False, f"Provider implementation invalid: {metadata.error_message}"

        try:
            # Attempt to instantiate the provider
            provider_class = self._get_provider_class(provider_name)
            provider_instance = provider_class(config)

            # Test basic validation
            provider_instance.validate_config()

            # Cache success
            self._validation_cache[cache_key] = True
            return True, None

        except ImportError as e:
            error_msg = f"Failed to import provider '{provider_name}': {str(e)}"
            self._validation_cache[cache_key] = False
            return False, error_msg

        except AttributeError as e:
            error_msg = f"Invalid provider class '{provider_name}': missing required methods"
            self._validation_cache[cache_key] = False
            return False, error_msg

        except Exception as e:
            error_msg = f"Provider validation failed for '{provider_name}': {str(e)}"
            self._validation_cache[cache_key] = False
            return False, error_msg

    def load_provider(
        self,
        provider_name: str,
        config: Dict[str, Any],
        force_reload: bool = False
    ) -> Optional[LLMProvider]:
        """
        Load and instantiate a provider with the given configuration.

        Args:
            provider_name: Name of the provider to load
            config: Configuration dictionary for the provider
            force_reload: Whether to reload even if already loaded

        Returns:
            Instantiated provider instance or None if failed
        """
        if not force_reload and provider_name in self._instantiated_providers:
            logger.debug(f"Using cached provider instance: {provider_name}")
            return self._instantiated_providers[provider_name]

        # Validate first
        is_valid, error_msg = self.validate_provider_implementation(provider_name, config)
        if not is_valid:
            logger.error(f"Cannot load provider '{provider_name}': {error_msg}")
            return None

        try:
            # Get the provider class and instantiate
            provider_class = self._get_provider_class(provider_name)
            provider_instance = provider_class(config)

            # Cache the instance
            self._instantiated_providers[provider_name] = provider_instance

            logger.info(f"Successfully loaded provider '{provider_name}'")
            return provider_instance

        except Exception as e:
            logger.error(f"Failed to instantiate provider '{provider_name}': {str(e)}")
            return None

    def _get_provider_class(self, provider_name: str) -> Type[LLMProvider]:
        """
        Get the provider class for a given provider name.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider class type
        """
        if provider_name not in self._discovered_providers:
            raise ValueError(f"Provider '{provider_name}' not discovered")

        metadata = self._discovered_providers[provider_name]

        try:
            # Use the same method as discovery - load from file spec
            from pathlib import Path
            base_path = Path(__file__).parent.parent.parent
            module_path, class_name = self.PROVIDER_MAPPING[provider_name]
            file_path = str(base_path / "app" / module_path.replace('.', '/') / "provider.py")
            
            spec = importlib.util.spec_from_file_location(
                f"{provider_name}_provider",
                file_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find module at {file_path}")
            
            # Create parent module for relative imports
            import sys
            import types
            parent_name = f"app.providers.{provider_name}"
            if parent_name not in sys.modules:
                parent = types.ModuleType(parent_name)
                parent.__file__ = str(base_path / "app" / "providers" / "__init__.py")
                sys.modules[parent_name] = parent
            
            module = importlib.util.module_from_spec(spec)
            module.__package__ = parent_name
            spec.loader.exec_module(module)
            
            provider_class = getattr(module, class_name)
            return provider_class

        except (ImportError, AttributeError) as e:
            raise ImportError(f"Cannot load provider class '{provider_name}': {str(e)}")

    def get_available_providers(self) -> List[str]:
        """
        Get list of providers that are available and valid.

        Returns:
            List of provider names
        """
        if not self._discovered_providers:
            self.discover_providers()

        return [
            name for name, metadata in self._discovered_providers.items()
            if metadata.is_valid
        ]

    def get_provider_metadata(self, provider_name: str) -> Optional[ProviderMetadata]:
        """
        Get metadata for a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider metadata or None if not found
        """
        return self._discovered_providers.get(provider_name)

    def get_all_metadata(self) -> Dict[str, ProviderMetadata]:
        """
            Get metadata for all discovered providers.

            Returns:
                Dictionary mapping provider names to metadata
            """
        return self._discovered_providers.copy()

    def clear_cache(self) -> None:
        """Clear all caches and cached instances."""
        self._validation_cache.clear()
        self._instantiated_providers.clear()
        logger.info("Cleared provider loader cache")

    def create_loading_summary(self) -> Dict[str, Any]:
        """
        Create a summary of provider loading status.

        Useful for debugging and monitoring.

        Returns:
            Dictionary containing loading status information
        """
        available_providers = self.get_available_providers()
        instantiated_count = len(self._instantiated_providers)

        return {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'total_discovered': len(self._discovered_providers),
            'available_providers': available_providers,
            'instantiated_providers': list(self._instantiated_providers.keys()),
            'cache_size': len(self._validation_cache),
            'status': 'healthy' if instantiated_count > 0 else 'no_instances',
            'provider_details': {
                name: {
                    'valid': metadata.is_valid,
                    'error': metadata.error_message,
                    'loaded': name in self._instantiated_providers
                }
                for name, metadata in self._discovered_providers.items()
            }
        }


# Global provider loader instance
_global_provider_loader = ProviderLoader()


def get_provider_loader() -> ProviderLoader:
    """Get global provider loader instance."""
    return _global_provider_loader


def initialize_provider_loader() -> None:
    """Initialize global provider loader."""
    _global_provider_loader.discover_providers()
    logger.info("LLM provider loader initialized")


def load_provider_with_config(
    provider_name: str,
    config: Dict[str, Any]
) -> Optional[LLMProvider]:
    """
    Convenience function to load a provider with configuration.

    Args:
        provider_name: Name of the provider to load
        config: Configuration dictionary

    Returns:
        Loaded provider instance or None
    """
    return _global_provider_loader.load_provider(provider_name, config)


def get_loading_summary() -> Dict[str, Any]:
    """Get provider loading summary."""
    return _global_provider_loader.create_loading_summary()


def validate_all_enabled_providers(
    config_parser: Optional[EnvironmentConfigParser] = None
) -> Dict[str, bool]:
    """
    Validate all enabled providers from configuration.

    Args:
        config_parser: Configuration parser instance (creates new if None)

    Returns:
        Dictionary mapping provider names to validation results
    """
    if config_parser is None:
        config_parser = get_config_parser()

    results = {}

    for provider_name in config_parser.get_enabled_providers():
        provider_config = config_parser.get_provider_config(provider_name)
        if provider_config:
            is_valid, _ = _global_provider_loader.validate_provider_implementation(
                provider_name,
                provider_config.config
            )
            results[provider_name] = is_valid
        else:
            results[provider_name] = False

    return results