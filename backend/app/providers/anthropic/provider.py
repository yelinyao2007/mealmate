"""
Anthropic Claude LLM provider implementation.
Provides chat completion using Anthropic's API with proper message format conversion and error handling.
"""

import logging
from typing import List, Dict, Any, Optional

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None
from ..base.llm_provider import (
    LLMProvider, LLMProviderError, AuthError, RateLimitError,
    ModelNotFoundError, TimeoutError
)

logger = logging.getLogger(__name__)


class AnthropicLLMProvider(LLMProvider):
    """
    Anthropic Claude LLM provider implementation.

    Converts OpenAI-style messages to Anthropic format and handles
    Claude-specific features like system prompts and token limits.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if AsyncAnthropic is None:
            raise ImportError("Anthropic Python package not installed. Please install anthropic to use this provider.")
        self.async_client: Optional[AsyncAnthropic] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Anthropic client with configuration."""
        try:
            api_key = self.config.get('api_key')

            self.async_client = AsyncAnthropic(
                api_key=api_key,
                timeout=self.config.get('timeout', 30.0),
                max_retries=self.config.get('max_retries', 2)
            )

            logger.info(f"Initialized Anthropic client for model: {self.config.get('model', 'claude-3-sonnet-20240229')}")

        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise AuthError(f"Invalid Anthropic configuration: {str(e)}")

    def validate_config(self) -> None:
        """Validate Anthropic provider configuration."""
        required_keys = ['api_key']
        missing_keys = [key for key in required_keys if not self.config.get(key)]

        if missing_keys:
            raise AuthError(f"Missing required Anthropic configuration: {', '.join(missing_keys)}")

        if not self.config.get('api_key').startswith('sk-ant-'):
            raise AuthError("Invalid Anthropic API key format")

    @property
    def supported_models(self) -> List[str]:
        """Return list of Anthropic models supported by this provider."""
        return [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-2.1',
            'claude-2.0'
        ]

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
    ) -> str:
        """
        Send a chat completion request to Anthropic.

        Converts OpenAI message format to Anthropic format and handles
        streaming appropriately.
        """
        if not self.async_client:
            raise LLMProviderError("Anthropic client not initialized")

        try:
            # Convert messages to Anthropic format
            system_prompt, conversation_messages = self._convert_messages(messages)

            # Build request parameters
            kwargs = {
                'model': self.config.get('model', 'claude-3-sonnet-20240229'),
                'messages': conversation_messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'stream': stream
            }

            # Add system prompt if present
            if system_prompt:
                kwargs['system'] = system_prompt

            logger.debug(f"Sending request to Anthropic with model: {kwargs['model']}")

            # Make the request
            if stream:
                result = ""
                async for chunk in await self.async_client.messages.create(**kwargs):
                    if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                        result += chunk.delta.text
                return result
            else:
                response = await self.async_client.messages.create(**kwargs)

                if response.content and len(response.content) > 0:
                    content = response.content[0].text
                    logger.info(f"Anthropic response received ({len(content)} chars)")
                    return content
                else:
                    logger.warning("Anthropic returned empty response")
                    raise LLMProviderError("Empty response from Anthropic")

        except Exception as e:
            self._handle_anthropic_error(e)

    def _convert_messages(
        self,
        messages: List[Dict[str, str]]
    ) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        Convert OpenAI message format to Anthropic format.

        Returns:
            Tuple of (system_prompt, conversation_messages)
        """
        system_prompt = None
        conversation_messages = []

        for msg in messages:
            role = msg.get('role', '').lower()
            content = msg.get('content', '')

            if not content:
                continue

            if role == 'system':
                # System messages go to the system parameter
                if system_prompt is None:
                    system_prompt = content
                else:
                    # Combine multiple system messages
                    system_prompt += f"\n\n{content}"
            elif role == 'user':
                conversation_messages.append({'role': 'user', 'content': content})
            elif role == 'assistant':
                conversation_messages.append({'role': 'assistant', 'content': content})
            else:
                # Unknown role, treat as user message
                logger.warning(f"Unknown message role '{role}', treating as user")
                conversation_messages.append({'role': 'user', 'content': content})

        return system_prompt, conversation_messages

    def _handle_anthropic_error(self, error: Exception) -> None:
        """Translate Anthropic specific errors to common exception types."""
        error_str = str(error).lower()

        if hasattr(error, 'status_code'):
            status_code = error.status_code

            if status_code == 401 or status_code == 403:
                logger.error(f"Anthropic authentication failed: {error}")
                raise AuthError(f"Anthropic authentication failed: {str(error)}")

            elif status_code == 429:
                logger.warning(f"Anthropic rate limit exceeded: {error}")
                raise RateLimitError(f"Rate limit exceeded: {str(error)}")

            elif status_code == 404:
                logger.error(f"Anthropic model not found: {error}")
                raise ModelNotFoundError(f"Model not found: {str(error)}")

            elif status_code == 408 or status_code == 504:
                logger.error(f"Anthropic request timeout: {error}")
                raise TimeoutError(f"Request timed out: {str(error)}")

        # Handle other Anthropic-specific error types
        if "authentication" in error_str or "invalid api key" in error_str:
            logger.error(f"Anthropic auth error: {error}")
            raise AuthError(f"Authentication failed: {str(error)}")

        elif "rate limit" in error_str or "too many requests" in error_str:
            logger.warning(f"Anthropic rate limit: {error}")
            raise RateLimitError(f"Rate limit exceeded: {str(error)}")

        elif "model not found" in error_str or "model does not exist" in error_str:
            logger.error(f"Anthropic model error: {error}")
            raise ModelNotFoundError(f"Model not available: {str(error)}")

        elif "token limit" in error_str or "context window" in error_str:
            logger.error(f"Anthropic token limit: {error}")
            raise ModelNotFoundError(f"Token limit exceeded: {str(error)}")

        elif "timeout" in error_str or "timed out" in error_str:
            logger.error(f"Anthropic timeout: {error}")
            raise TimeoutError(f"Request timed out: {str(error)}")

        # Generic error handling
        logger.error(f"Anthropic unexpected error: {error}")
        raise LLMProviderError(f"Anthropic request failed: {str(error)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Return Anthropic-specific metrics."""
        metrics = super().get_metrics()
        metrics.update({
            'last_model_used': self.config.get('model', 'unknown'),
            'api_version': 'v1',
            'supports_streaming': True,
            'supports_system_prompts': True,
            'max_context_tokens': self.config.get('model', '').startswith('claude-3') and 200000 or 100000
        })
        return metrics