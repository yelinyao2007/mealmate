"""
Compatibility LLM client shim.
This module preserves the old synchronous `get_llm_client()` API while delegating
to the new multi-provider client (initialized via `llm_client_new`).
"""
import os
import asyncio
import threading
import logging
import time
from collections import defaultdict
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# ── LLM Call Timing Interceptor ──────────────────────────────────────────────

class LLMTimingInterceptor:
    """Intercepts all LLM calls to track per-agent timing."""

    def __init__(self):
        self._records: List[Dict] = []
        self._lock = threading.Lock()

    def wrap(self, client):
        """Wrap an LLM client instance with timing instrumentation."""
        original_chat = client.chat_completion
        original_chat_json = client.chat_completion_json

        def timed_chat_completion(messages, temperature=0.7, max_tokens=2048, json_mode=False):
            agent = _detect_agent_from_messages(messages)
            start = time.time()
            try:
                result = original_chat(messages, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
                elapsed = time.time() - start
                self._record(agent, "chat_completion", elapsed, len(messages), len(result), "success")
                return result
            except Exception as e:
                elapsed = time.time() - start
                self._record(agent, "chat_completion", elapsed, len(messages), 0, f"error: {e}")
                raise

        def timed_chat_completion_json(messages, temperature=0.7, max_tokens=4096):
            agent = _detect_agent_from_messages(messages)
            start = time.time()
            try:
                result = original_chat_json(messages, temperature=temperature, max_tokens=max_tokens)
                elapsed = time.time() - start
                self._record(agent, "chat_completion_json", elapsed, len(messages), len(str(result)), "success")
                return result
            except Exception as e:
                elapsed = time.time() - start
                self._record(agent, "chat_completion_json", elapsed, len(messages), 0, f"error: {e}")
                raise

        client.chat_completion = timed_chat_completion
        client.chat_completion_json = timed_chat_completion_json
        return client

    def _record(self, agent, call_type, duration, msg_count, resp_len, status):
        with self._lock:
            self._records.append({
                "agent": agent,
                "type": call_type,
                "duration_s": round(duration, 3),
                "messages": msg_count,
                "response_len": resp_len,
                "status": status,
                "timestamp": time.strftime("%H:%M:%S"),
            })

    def report(self) -> str:
        """Return a formatted timing report."""
        with self._lock:
            if not self._records:
                return "No LLM calls recorded yet."
            lines = ["\n" + "=" * 72,
                     "  LLM CALL TIMING REPORT",
                     "=" * 72,
                     f"  Total calls: {len(self._records)}"]
            by_agent = defaultdict(list)
            for r in self._records:
                by_agent[r["agent"]].append(r)
            for agent, calls in sorted(by_agent.items()):
                durations = [c["duration_s"] for c in calls]
                avg_s = sum(durations) / len(durations)
                total = sum(durations)
                lines.append(f"  ├─ {agent or 'unknown'}:")
                lines.append(f"  │   calls={len(calls)}, "
                             f"total={total:.1f}s, "
                             f"avg={avg_s:.1f}s, "
                             f"min={min(durations):.1f}s, "
                             f"max={max(durations):.1f}s")
                for c in calls:
                    symbol = "✅" if c["status"] == "success" else "❌"
                    lines.append(f"  │     {symbol} {c['timestamp']} {c['type']} "
                                 f"({c['duration_s']:.1f}s, msgs={c['messages']})")
            total_time = sum(r["duration_s"] for r in self._records)
            lines.append(f"  └─ Total wall time: {total_time:.1f}s")
            lines.append("=" * 72)
            return "\n".join(lines)

    def reset(self):
        with self._lock:
            self._records.clear()

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "total_calls": len(self._records),
                "total_time_s": sum(r["duration_s"] for r in self._records),
                "records": list(self._records),
            }


# Global interceptor instance
_timing_interceptor = LLMTimingInterceptor()


def get_timing_interceptor() -> LLMTimingInterceptor:
    return _timing_interceptor


def _detect_agent_from_messages(messages) -> str:
    """Heuristic: detect which agent is calling based on system prompt content."""
    for m in messages:
        if m.get("role") == "system":
            content = m.get("content", "")
            if "智膳大厨" in content or "MenuPlanner" in content:
                return "MenuPlannerAgent"
            if "营养分析" in content or "NutritionAnalyzer" in content:
                return "NutritionAnalyzerAgent"
            if "采购清单" in content or "Procurement" in content:
                return "ProcurementAgent"
            if "膳食定制" in content or "MealCustomizer" in content:
                return "MealCustomizerAgent"
            if "智能大厨" in content or "SmartChef" in content:
                return "SmartChefAgent"
            if "健康画像" in content or "ProfileAgent" in content:
                return "ProfileAgent"
            return "UnknownAgent"
    return "UnknownAgent"

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
        # Apply timing interceptor to self (wrap our own chat methods)
        _timing_interceptor.wrap(self)

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
        return self._run_async(coro, timeout=300)

    def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict:
        coro = self._client.chat_completion_json(
            messages=messages, temperature=temperature, max_tokens=max_tokens
        )
        return self._run_async(coro, timeout=300)

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