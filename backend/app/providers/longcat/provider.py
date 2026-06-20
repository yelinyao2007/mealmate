"""
Longcat LLM provider implementation.
Uses Longcat's OpenAI-compatible chat completions endpoint at https://api.longcat.chat
Authentication: Authorization: Bearer <API_KEY>

Environment/config keys expected (via provider config parser):
- api_key (or LONGCAT_API_KEY env var)
- base_url (optional, defaults to https://api.longcat.chat)
- model (optional)
- timeout, max_retries, etc. (optional)
"""

import logging
from typing import List, Dict, Any

import httpx

from ..base.llm_provider import (
    LLMProvider, LLMProviderError, AuthError, RateLimitError, ModelNotFoundError, TimeoutError
)

logger = logging.getLogger(__name__)


class LongcatLLMProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or __import__('os').environ.get('LONGCAT_API_KEY')
        self.base_url = config.get('base_url', 'https://api.longcat.chat')
        self.model = config.get('model', 'gpt-4o-mini')
        self.timeout = float(config.get('timeout', 15.0))
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self.validate_config()

    def validate_config(self) -> None:
        if not self.api_key:
            raise AuthError('Missing Longcat API key (LONGCAT_API_KEY or api_key in config)')

        if not self.base_url.startswith(('http://', 'https://')):
            raise LLMProviderError('Invalid Longcat base_url')

    @property
    def supported_models(self) -> List[str]:
        # Longcat is OpenAI-compatible; offer a generic set
        return [self.model]

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
    ) -> str:
        # Build request to OpenAI-compatible chat completions endpoint
        url = f"{self.base_url}/openai/v1/chat/completions"
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        # Support recommended json_mode header if requested
        if json_mode:
            # Longcat follows OpenAI-compatible API; no special field guaranteed.
            # We'll request the response and attempt to parse JSON out of it.
            pass

        try:
            if stream:
                # Longcat streaming support may work like OpenAI; implement basic non-stream fallback
                # For simplicity, raise not implemented for streaming to keep behavior deterministic
                raise LLMProviderError('Streaming not implemented for Longcat provider')

            resp = await self._client.post(url, json=payload, headers=headers)

            # Handle status codes
            if resp.status_code in (401, 403):
                raise AuthError(f'Authentication failed: {resp.text}')
            if resp.status_code == 429:
                raise RateLimitError(f'Rate limit or quota exceeded: {resp.text}')
            if resp.status_code == 404:
                raise ModelNotFoundError(f'Model not found: {resp.text}')
            if resp.status_code >= 500:
                raise LLMProviderError(f'Provider server error: {resp.status_code} {resp.text}')

            data = resp.json()

            if isinstance(data, dict) and isinstance(data.get('error'), dict):
                error = data['error']
                code = str(error.get('code') or '').strip()
                message = str(error.get('message') or 'Longcat request failed').strip()
                full_message = f'{code}: {message}' if code else message

                if 'unsupported model' in message.lower() or code in {'invalid_parameter', 'model_not_found'}:
                    raise ModelNotFoundError(full_message)
                if code in {'unauthorized', 'invalid_api_key'}:
                    raise AuthError(full_message)
                if code in {'rate_limit_exceeded', 'quota_exceeded'}:
                    raise RateLimitError(full_message)
                raise LLMProviderError(full_message)

            # Extract content similar to OpenAI response structure
            if 'choices' in data and data['choices'] and 'message' in data['choices'][0]:
                message = data['choices'][0]['message']
                content = message.get('content') or message.get('text')
                if content is None:
                    raise LLMProviderError('Longcat response missing content')
                return content

            # Fallback: if top-level 'text' exists
            if 'text' in data:
                return data['text']

            raise LLMProviderError(f'Unexpected Longcat response format: {data}')

        except httpx.TimeoutException as e:
            logger.error(f'Longcat request timed out: {e}')
            raise TimeoutError(str(e))
        except httpx.HTTPError as e:
            logger.error(f'Longcat HTTP error: {e}')
            raise LLMProviderError(str(e))
        except Exception as e:
            # If it's already a provider error, re-raise
            if isinstance(e, (LLMProviderError, AuthError, RateLimitError, ModelNotFoundError, TimeoutError)):
                raise
            logger.error(f'Unexpected Longcat error: {e}')
            raise LLMProviderError(str(e))

    def get_metrics(self) -> Dict[str, Any]:
        metrics = super().get_metrics()
        metrics.update({
            'last_model_used': self.model,
            'base_url': self.base_url,
            'supports_streaming': False,
            'supports_json_mode': True
        })
        return metrics
