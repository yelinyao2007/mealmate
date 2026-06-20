"""Very simple direct test."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

# Initialize just the provider loader
print("[1] Load provider...", flush=True)

from app.providers.provider_loader import ProviderLoader
from app.providers.config.provider_config import get_config_parser

loader = ProviderLoader()
loader.discover_providers()

config = get_config_parser()
config.parse_environment()

openai_cfg = config.get_provider_config("openai")
print(f"[2] Config: {openai_cfg.config.get('model')}", flush=True)

is_valid, error = loader.validate_provider_implementation("openai", openai_cfg.config)
print(f"[3] Valid: {is_valid}", flush=True)

provider = loader.load_provider("openai", openai_cfg.config)
print(f"[4] Provider: {provider}", flush=True)

# Test chat directly
print("[5] Test chat_completion...", flush=True)
result = asyncio.run(provider.chat_completion(
    messages=[{"role": "user", "content": "Hi"}],
    max_tokens=5
))
print(f"[6] SUCCESS: {result}", flush=True)