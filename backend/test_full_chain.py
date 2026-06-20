"""Full test of LLM provider loading chain."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup path
base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))

# Load .env
load_dotenv(base_path / ".env")

print(f"PRIMARY_PROVIDER: {os.getenv('PRIMARY_PROVIDER')}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '')[:10]}...")
print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'not set')}")

# Test 1: Discover providers
print("\n=== Testing Provider Discovery ===")
from app.providers.provider_loader import ProviderLoader

loader = ProviderLoader()
loader.discover_providers()

for name, meta in loader._discovered_providers.items():
    print(f"Provider {name}: valid={meta.is_valid}, error={meta.error_message}")

# Test 2: Parse config
print("\n=== Testing Config Parser ===")
from app.providers.config.provider_config import EnvironmentConfigParser

config_parser = EnvironmentConfigParser()
config_parser.parse_environment()

enabled = config_parser.get_enabled_providers()
print(f"Enabled providers: {enabled}")

for provider_name in enabled:
    cfg = config_parser.get_provider_config(provider_name)
    if cfg:
        print(f"  {provider_name}: priority={cfg.priority}, model={cfg.config.get('model', 'default')}")

# Test 3: Load provider
print("\n=== Testing Provider Loading ===")
for provider_name in enabled:
    cfg = config_parser.get_provider_config(provider_name)
    if cfg:
        is_valid, error = loader.validate_provider_implementation(provider_name, cfg.config)
        print(f"  {provider_name} validation: {is_valid}, {error}")
        
        if is_valid:
            provider = loader.load_provider(provider_name, cfg.config)
            print(f"  {provider_name} loaded: {provider is not None}")
            
            if provider:
                # Test 4: Make actual call
                print(f"\n=== Testing Chat Completion with {provider_name} ===")
                import asyncio
                
                async def test_chat():
                    result = await provider.chat_completion(
                        messages=[{"role": "user", "content": "Say hi in one word"}],
                        temperature=0.7,
                        max_tokens=10
                    )
                    print(f"Response: {result}")
                    return result
                
                result = asyncio.run(test_chat())
                print(f"SUCCESS! Got response: {result}")
                break