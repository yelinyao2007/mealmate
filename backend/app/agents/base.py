"""
Base Agent class for the MealMate multi-agent system.
Each agent is an autonomous unit that can:
  - Receive structured input
  - Call the LLM with specialized prompts
  - Return structured output
  - Log its execution steps
"""
import time
import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.llm_client import get_llm_client

logger = logging.getLogger(__name__)


@dataclass
class AgentStep:
    """A single execution step in an agent's workflow."""
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    duration_ms: int
    status: str = "success"  # success | error
    error_message: str = ""


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_name: str
    success: bool
    data: Dict[str, Any]
    steps: List[AgentStep] = field(default_factory=list)
    error: str = ""


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    name: str = "BaseAgent"
    description: str = "Base agent"

    def __init__(self):
        self.llm = get_llm_client()
        self.steps: List[AgentStep] = []

    def _log_step(self, action: str, input_summary: str, output_summary: str,
                  duration_ms: int, status: str = "success", error_message: str = ""):
        step = AgentStep(
            agent_name=self.name,
            action=action,
            input_summary=input_summary[:200],
            output_summary=output_summary[:200],
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
        )
        self.steps.append(step)
        logger.info("[%s] %s (%dms) - %s", self.name, action, duration_ms, status)

    def _call_llm(self, messages: List[Dict[str, str]], json_mode: bool = False,
                  temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Call LLM with timing and logging."""
        start = time.time()
        try:
            if json_mode:
                result = self.llm.chat_completion(messages, temperature=temperature, max_tokens=max_tokens, json_mode=True)
            else:
                result = self.llm.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
            duration = int((time.time() - start) * 1000)
            self._log_step("llm_call", messages[-1]["content"][:100], result[:100], duration)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self._log_step("llm_call", messages[-1]["content"][:100], "", duration, "error", str(e))
            raise

    def _call_llm_json(self, messages: List[Dict[str, str]], temperature: float = 0.7,
                       max_tokens: int = 4096) -> dict:
        """Call LLM and parse response as JSON, with timing and logging."""
        start = time.time()
        try:
            result = self.llm.chat_completion_json(messages, temperature=temperature, max_tokens=max_tokens)
            duration = int((time.time() - start) * 1000)
            self._log_step("llm_call_json", messages[-1]["content"][:100], str(result)[:100], duration)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self._log_step("llm_call_json", messages[-1]["content"][:100], "", duration, "error", str(e))
            raise

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute the agent's main task. Must be implemented by subclasses."""
        pass

    def run(self, input_data: Dict[str, Any]) -> AgentResult:
        """Run the agent with error handling and step tracking."""
        self.steps = []
        start = time.time()
        try:
            result = self.execute(input_data)
            result.steps = self.steps
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self._log_step("execute", str(input_data)[:100], "", duration, "error", str(e))
            return AgentResult(
                agent_name=self.name,
                success=False,
                data={},
                steps=self.steps,
                error=str(e),
            )
