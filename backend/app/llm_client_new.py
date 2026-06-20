"""
Updated LLM Client - Multi-provider interface for Dell AIA Gateway LLM and alternative providers.
Supports OpenAI, Anthropic, Google Gemini, and local models with intelligent fallback.
"""

import logging
from typing import List, Dict, Any, Optional

# Import the new multi-provider client
from app.providers.multi_provider_client import get_multi_provider_client, initialize_multi_provider_client


logger = logging.getLogger(__name__)


def get_llm_client() -> 'MultiProviderLLMClient':
    """Get or create the singleton multi-provider LLM client."""
    return get_multi_provider_client()


def initialize_llm_client() -> None:
    """Initialize the multi-provider LLM client system."""
    initialize_multi_provider_client()
    logger.info("Multi-provider LLM client initialized")


# For backward compatibility, keep the old function name
def get_llm_client_old():
    """Legacy function name for backward compatibility."""
    return get_llm_client()