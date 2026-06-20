import json
import os
from fastapi import APIRouter, HTTPException, Request
from typing import Dict

router = APIRouter(prefix="/api/i18n", tags=["i18n"])

SUPPORTED_LANGUAGES = ["en", "zh"]

# Load translations at startup
_translations: Dict[str, Dict] = {}


def _load_translations():
    global _translations
    i18n_dir = os.path.join(os.path.dirname(__file__), "i18n")
    for lang in SUPPORTED_LANGUAGES:
        file_path = os.path.join(i18n_dir, f"{lang}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)


# Load on module import
_load_translations()


def _merge_translations(lang: str) -> Dict:
    """Merge translations with fallback to English."""
    result = _translations.get("en", {}).copy()
    if lang != "en" and lang in _translations:
        # Deep merge - override English with specific translations
        _deep_merge(result, _translations[lang])
    return result


def _deep_merge(base: Dict, override: Dict):
    """Deep merge override into base."""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


@router.get("/translations")
def get_translations(lang: str = "en"):
    """Get translations for the specified language."""
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            detail=f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    return _merge_translations(lang)


@router.get("/languages")
def get_supported_languages():
    """Get list of supported languages."""
    return {"languages": SUPPORTED_LANGUAGES}