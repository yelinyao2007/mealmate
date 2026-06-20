"""
Compatibility LLM client shim.
This module preserves the old synchronous `get_llm_client()` API while delegating
to the new multi-provider client (initialized via `llm_client_new`).
"""
import os
import asyncio
import threading
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy import of the multi-provider implementation
_multi_provider = None


def _ensure_multi_provider_initialized():
    global _multi_provider
    if _multi_provider is None:
        try:
            from app.llm_client_new import initialize_llm_client, get_llm_client as _get_mp
            initialize_llm_client()
            _multi_provider = _get_mp()
        except Exception as e:
            logger.exception("Failed to initialize multi-provider LLM client: %s", e)
            raise


class _SyncMultiProviderWrapper:
    """Synchronous wrapper around the async MultiProviderLLMClient.
    
    Uses a persistent background thread with a dedicated event loop
    to avoid "Event loop is closed" errors.
    """

    def __init__(self):
        _ensure_multi_provider_initialized()
        self._client = _multi_provider
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        """Run the persistent event loop forever."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_async(self, coro, timeout: int = 60):
        """Run an async coroutine on the persistent event loop with timeout."""
        done = threading.Event()
        result = []
        error = []

        def callback(fut):
            try:
                result.append(fut.result())
            except Exception as e:
                error.append(e)
            finally:
                done.set()

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        future.add_done_callback(callback)

        if not done.wait(timeout=timeout):
            raise Exception(f"LLM request timed out after {timeout}s")

        if error:
            raise error[0]

        return result[0]

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        coro = self._client.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            stream=False,
        )
        return self._run_async(coro, timeout=30)

    def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict:
        coro = self._client.chat_completion_json(
            messages=messages, temperature=temperature, max_tokens=max_tokens
        )
        return self._run_async(coro, timeout=30)

    @property
    def is_demo_mode(self) -> bool:
        try:
            return (
                getattr(self._client, "is_demo_mode")()
                if callable(getattr(self._client, "is_demo_mode", None))
                else bool(getattr(self._client, "is_demo_mode", False))
            )
        except Exception:
            return False


# Singleton instance to preserve previous semantics
_llm_client_instance: Optional[Any] = None


def get_llm_client():
    """Return a synchronous LLM client compatible with existing code."""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = _SyncMultiProviderWrapper()
    return _llm_client_instance