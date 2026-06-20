"""Test blocking issue."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import concurrent.futures

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

from app.providers.provider_loader import ProviderLoader
from app.providers.config.provider_config import get_config_parser

loader = ProviderLoader()
loader.discover_providers()

config = get_config_parser()
config.parse_environment()

provider = loader.load_provider("openai", config.get_provider_config("openai").config)

print("[1] Use sync client in thread...", flush=True)

def call_sync():
    return provider.client.chat.completions.create(
        model="LongCat-Flash-Chat",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    ).choices[0].message.content

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
    future = ex.submit(call_sync)
    result = future.result(timeout=10)

print(f"[2] SUCCESS: {result}", flush=True)