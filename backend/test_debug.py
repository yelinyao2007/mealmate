"""Quick debug test."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

# Limit to only openai
os.environ["SECONDARY_PROVIDER"] = ""
os.environ["TERTIARY_PROVIDER"] = ""

print("[1] Init MultiProviderLLMClient...", flush=True)
from app.providers.multi_provider_client import MultiProviderLLMClient

client = MultiProviderLLMClient()
print(f"[2] Providers: {list(client._providers.keys())}", flush=True)
print(f"[3] Demo mode: {client._demo_mode_enabled}", flush=True)

if "openai" not in client._providers:
    print("[4] ERROR: openai not loaded!", flush=True)
    sys.exit(1)

print("[4] Test chat...", flush=True)
async def test():
    result = await client.chat_completion([{"role": "user", "content": "Hi"}], max_tokens=10)
    return result

result = asyncio.run(test())
print(f"[5] SUCCESS: {result}", flush=True)