"""
OpenAI LLM provider implementation.
Uses httpx directly for compatibility with Longcat and OpenAI-compatible APIs.
"""

import logging
import httpx
from typing import List, Dict, Any, Optional

from ..base.llm_provider import (
    LLMProvider, LLMProviderError, AuthError, RateLimitError,
    ModelNotFoundError, TimeoutError
)

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    """
    OpenAI LLM provider using httpx for HTTP requests.
    Compatible with OpenAI and Longcat APIs.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('baseUrl') or config.get('base_url', 'https://api.openai.com/v1')
        # Add /v1 suffix if not present for OpenAI compatibility
        if not self.base_url.endswith('/v1'):
            self.base_url = self.base_url.rstrip('/') + '/v1'
        self.model = config.get('model', 'gpt-4o-mini')
        self.timeout = float(config.get('timeout', 30.0))
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            raise AuthError("Missing API key")
        if not self.api_key.startswith(('sk-', 'ak_')):
            pass  # Allow any format for compatibility

    @property
    def supported_models(self) -> List[str]:
        return [self.model, 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
    ) -> str:
        """Send a chat completion request via httpx."""
        if stream:
            raise LLMProviderError("Streaming not implemented")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        processed_messages = []
        for msg in messages:
            if isinstance(msg.get('content'), list):
                processed_messages.append(msg)
            elif isinstance(msg.get('content'), dict):
                processed_messages.append(msg)
            else:
                processed_messages.append({"role": msg["role"], "content": msg["content"]})
        
        payload = {
            "model": self.model,
            "messages": processed_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            resp = await self._client.post(url, json=payload, headers=headers)
            
            if resp.status_code == 401 or resp.status_code == 403:
                raise AuthError(f"Authentication failed: {resp.text}")
            if resp.status_code == 429:
                raise RateLimitError(f"Rate limit: {resp.text}")
            if resp.status_code == 404:
                raise ModelNotFoundError(f"Model not found: {resp.text}")
            if resp.status_code >= 500:
                raise LLMProviderError(f"Server error: {resp.status_code}")
            
            data = resp.json()
            if 'choices' in data and data['choices']:
                content = data['choices'][0]['message'].get('content', '')
                if content:
                    return content
            
            raise LLMProviderError(f"Empty response: {data}")
            
        except httpx.TimeoutException:
            raise TimeoutError("Request timed out")
        except httpx.HTTPError as e:
            raise LLMProviderError(f"HTTP error: {str(e)}")
        except LLMProviderError:
            raise
        except Exception as e:
            raise LLMProviderError(f"Request failed: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Return provider metrics."""
        metrics = super().get_metrics()
        metrics.update({
            'last_model_used': self.model,
            'supports_streaming': False,
            'supports_json_mode': True
        })
        return metrics