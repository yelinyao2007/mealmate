"""Simple test of provider discovery and loading."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

print("1. Loading provider_loader...")
from app.providers.provider_loader import ProviderLoader

print("2. Discovering providers...")
loader = ProviderLoader()
loader.discover_providers()

for name, meta in loader._discovered_providers.items():
    print(f"  {name}: valid={meta.is_valid}")

print("3. Loading OpenAI provider class...")
from app.providers.config.provider_config import get_config_parser

config_parser = get_config_parser()
config_parser.parse_environment()

# Get openai config
openai_cfg = config_parser.get_provider_config("openai")
print(f"  OpenAI config: {openai_cfg.config if openai_cfg else None}")

print("4. Validating openai...")
if openai_cfg:
    is_valid, error = loader.validate_provider_implementation("openai", openai_cfg.config)
    print(f"  Validation: {is_valid}, {error}")

print("5. Loading openai...")
if is_valid:
    provider = loader.load_provider("openai", openai_cfg.config)
    print(f"  Loaded: {provider}")

print("Done!")