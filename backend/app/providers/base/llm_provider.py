"""
Abstract base class for LLM providers.
Defines the common interface that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class AuthError(LLMProviderError):
    """Authentication/authorization error from provider."""
    pass


class RateLimitError(LLMProviderError):
    """Rate limit exceeded by provider."""
    pass


class ModelNotFoundError(LLMProviderError):
    """Requested model not found by provider."""
    pass


class TimeoutError(LLMProviderError):
    """Request timed out to provider."""
    pass


class ResourceLimitError(LLMProviderError):
    """Local resource limits (memory, GPU) exceeded."""
    pass


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    All concrete provider implementations MUST inherit from this class and
    implement the chat_completion method with identical signature.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.provider_name = self.__class__.__name__.lower()

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
    ) -> str:
        """
        Send a chat completion request to the provider.

        This is the main interface that callers will use. All providers must
        implement this method with identical signature to maintain compatibility.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to request JSON response format
            stream: Whether to enable streaming response

        Returns:
            String containing the assistant's response

        Raises:
            AuthError: If authentication fails
            RateLimitError: If rate limit is exceeded
            ModelNotFoundError: If specified model doesn't exist
            TimeoutError: If request times out
            LLMProviderError: For other provider-specific errors
        """
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of models supported by this provider."""
        pass

    def validate_config(self) -> None:
        """
        Validate provider configuration.

        Should raise appropriate exceptions if configuration is invalid.
        Called during initialization.
        """
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """
        Return provider-specific metrics (response time, token usage, etc.).

        Used by health monitoring system.
        """
        return {
            "provider": self.provider_name,
            "status": "unknown",
            "last_check": None,
            "success_count": 0,
            "failure_count": 0,
            "avg_response_time": None,
        }