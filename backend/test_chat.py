"""Test chat completion."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

from app.providers.provider_loader import ProviderLoader
from app.providers.config.provider_config import get_config_parser

loader = ProviderLoader()
loader.discover_providers()

config_parser = get_config_parser()
config_parser.parse_environment()

openai_cfg = config_parser.get_provider_config("openai")

async def test():
    provider = loader.load_provider("openai", openai_cfg.config)
    print(f"Provider loaded: {provider}")
    
    result = await provider.chat_completion(
        messages=[{"role": "user", "content": "Say hi in one word"}],
        temperature=0.7,
        max_tokens=10
    )
    print(f"Result: {result}")
    return result

asyncio.run(test())