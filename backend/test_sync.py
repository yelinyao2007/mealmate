"""Debug where it hangs."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

os.environ["SECONDARY_PROVIDER"] = ""
os.environ["TERTIARY_PROVIDER"] = ""

print("[1] Init...", flush=True)
from app.providers.multi_provider_client import MultiProviderLLMClient

client = MultiProviderLLMClient()
print(f"[2] Providers: {list(client._providers.keys())}", flush=True)

if "openai" not in client._providers:
    print("ERROR: No openai", flush=True)
    sys.exit(1)

provider = client._providers["openai"]

print(f"[3] Provider: {provider}", flush=True)
print(f"[4] Config: {provider.config}", flush=True)
print(f"[5] Async client: {provider.async_client}", flush=True)

# Try sync instead of async
print("[6] Try sync call...", flush=True)
import time
start = time.time()

try:
    # Use sync client directly
    result = provider.client.chat.completions.create(
        model="LongCat-Flash-Chat",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print(f"[7] SUCCESS in {time.time()-start:.1f}s: {result.choices[0].message.content}", flush=True)
except Exception as e:
    print(f"[7] ERROR: {e}", flush=True)