import base64
import binascii
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Load backend/.env for local demo runs.
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from app.auth import get_current_user, get_optional_user
from app.database import get_db
from app.models import ImageRecognition, User
from app.schemas import AIRecipe, ImageRecognizeRequest, ImageRecognizeResponse, ImageRecognitionOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image", tags=["image"])

DEFAULT_IMAGE_PROVIDER = "moonshot"

# Moonshot / Kimi configuration
DEFAULT_MOONSHOT_BASE_URL = "https://api.kimi.com/coding/v1"
DEFAULT_MOONSHOT_VISION_MODEL = "kimi-for-coding"

# StepFun-compatible provider (currently Xiaomi MiMo via OpenAI-compatible API)
DEFAULT_STEPFUN_BASE_URL = "https://api.xiaomimimo.com/v1"
DEFAULT_STEPFUN_PLAN_BASE_URL = "https://api.xiaomimimo.com/v1"
DEFAULT_STEPFUN_VISION_MODEL = "mimo-v2.5"

DEFAULT_LONGCAT_BASE_URL = "https://api.longcat.chat"
DEFAULT_LONGCAT_VISION_MODEL = "LongCat-Flash-Chat"
LONGCAT_AVAILABLE_MODELS = {
    "LongCat-Flash-Chat",
}

MAX_IMAGE_BYTES = 5 * 1024 * 1024

DEMO_INGREDIENTS = [
    "\u571f\u8c46",
    "\u5e72\u8fa3\u6912",
    "\u7ea2\u6912",
    "\u5c0f\u8471",
]
GENERIC_DEMO_INGREDIENTS = [
    "\u8089\u7c7b",
    "\u9752\u7ea2\u6912",
    "\u8471\u59dc\u849c",
]
DEMO_DISH = {
    "title": "\u9178\u8fa3\u571f\u8c46\u4e1d",
    "ingredients": [
        "\u571f\u8c46 2\u4e2a",
        "\u5e72\u8fa3\u6912 3\u4e2a",
        "\u7ea2\u6912 \u534a\u4e2a",
        "\u5c0f\u8471 1\u6839",
        "\u76d0 \u9002\u91cf",
        "\u918b \u5c11\u8bb8",
    ],
    "steps": [
        "\u571f\u8c46\u5207\u7ec6\u4e1d\u540e\u7528\u6e05\u6c34\u51b2\u6d17\u6389\u8868\u9762\u6dc0\u7c89\uff0c\u6ca5\u5e72\u5907\u7528\u3002",
        "\u70ed\u9505\u4e0b\u6cb9\uff0c\u653e\u5165\u5e72\u8fa3\u6912\u548c\u8471\u6bb5\u7206\u9999\u3002",
        "\u5012\u5165\u571f\u8c46\u4e1d\u548c\u7ea2\u6912\u4e1d\uff0c\u5927\u706b\u5feb\u901f\u7ffb\u7092\u3002",
        "\u52a0\u5165\u76d0\u548c\u5c11\u8bb8\u918b\u8c03\u5473\uff0c\u4fdd\u6301\u571f\u8c46\u4e1d\u723d\u8106\u53e3\u611f\u3002",
        "\u51fa\u9505\u524d\u6492\u8471\u82b1\u5373\u53ef\u3002",
    ],
    "tips": "\u571f\u8c46\u4e1d\u5148\u8fc7\u6c34\uff0c\u7ffb\u7092\u65f6\u7528\u5927\u706b\u5feb\u7092\uff0c\u66f4\u5bb9\u6613\u4fdd\u6301\u6e05\u723d\u8106\u53e3\u3002",
    "cook_time_minutes": 15,
}
SWEET_SOUR_RIBS_INGREDIENTS = [
    "\u5c0f\u6392",
    "\u7cd6",
    "\u918b",
    "\u8471\u59dc",
]
SWEET_SOUR_RIBS_DISH = {
    "title": "\u7cd6\u918b\u5c0f\u6392",
    "ingredients": [
        "\u5c0f\u6392 500g",
        "\u51b0\u7cd6 20g",
        "\u9999\u918b 25ml",
        "\u751f\u62bd 15ml",
        "\u8001\u62bd 5ml",
        "\u8471\u59dc\u9002\u91cf",
    ],
    "steps": [
        "\u5c0f\u6392\u51b7\u6c34\u4e0b\u9505\u712f\u6c34\uff0c\u6ca5\u5e72\u540e\u5907\u7528\u3002",
        "\u9505\u4e2d\u5c11\u6cb9\u5c06\u51b0\u7cd6\u7092\u51fa\u7cd6\u8272\uff0c\u4e0b\u5165\u6392\u9aa8\u7ffb\u7092\u88f9\u8272\u3002",
        "\u52a0\u5165\u8471\u59dc\u3001\u751f\u62bd\u3001\u8001\u62bd\u548c\u70ed\u6c34\uff0c\u5c0f\u706b\u7116\u81f3\u8f6f\u70c2\u3002",
        "\u6700\u540e\u52a0\u7cd6\u548c\u9999\u918b\u6536\u6c41\uff0c\u8ba9\u6c64\u6c41\u88f9\u4f4f\u6392\u9aa8\u5373\u53ef\u3002",
    ],
    "tips": "\u8d77\u9505\u524d\u518d\u52a0\u4e00\u6b21\u918b\uff0c\u9178\u751c\u5473\u4f1a\u66f4\u7a81\u51fa\u3002",
    "cook_time_minutes": 40,
}
KNOWN_FALLBACKS = {
    "238c866605f6a37f78aea436239f08bfe6e982d32d2154ccf3dce7270fc3dab0": {
        "ingredients": {"ingredients": list(SWEET_SOUR_RIBS_INGREDIENTS), "confidence": "\u6f14\u793a"},
        "dish": dict(SWEET_SOUR_RIBS_DISH),
        "message": "\u5df2\u5339\u914d\u6f14\u793a\u6837\u4f8b\u56fe\uff0c\u5df2\u4f7f\u7528\u5bf9\u5e94\u7684\u672c\u5730\u5c55\u793a\u8bc6\u522b\u7ed3\u679c\u3002",
    },
}


def _image_provider() -> str:
    return "stepfun"


def _moonshot_api_key() -> str:
    return os.getenv("MOONSHOT_API_KEY", "").strip()


def _moonshot_base_url() -> str:
    return _normalized_base_url("MOONSHOT_BASE_URL", DEFAULT_MOONSHOT_BASE_URL)


def _moonshot_model() -> str:
    return os.getenv("MOONSHOT_VISION_MODEL", DEFAULT_MOONSHOT_VISION_MODEL).strip() or DEFAULT_MOONSHOT_VISION_MODEL


def _demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "false").strip().lower() == "true"


def _normalized_base_url(env_name: str, default: str) -> str:
    base_url = os.getenv(env_name, default).strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        logger.warning("Invalid %s '%s'; falling back to %s", env_name, base_url, default)
        return default
    return base_url


def _stepfun_base_url() -> str:
    return _normalized_base_url("STEPFUN_BASE_URL", DEFAULT_STEPFUN_BASE_URL)


def _stepfun_api_key() -> str:
    return os.getenv("STEPFUN_API_KEY", "").strip()


def _stepfun_model() -> str:
    return os.getenv("STEPFUN_VISION_MODEL", DEFAULT_STEPFUN_VISION_MODEL).strip() or DEFAULT_STEPFUN_VISION_MODEL


def _longcat_base_url() -> str:
    base_url = _normalized_base_url("LONGCAT_BASE_URL", DEFAULT_LONGCAT_BASE_URL)
    for suffix in ("/openai/v1", "/openai", "/v1"):
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)]
    return base_url


def _longcat_api_key() -> str:
    return os.getenv("LONGCAT_API_KEY", "").strip()


def _longcat_model() -> str:
    model = os.getenv("LONGCAT_VISION_MODEL", DEFAULT_LONGCAT_VISION_MODEL).strip() or DEFAULT_LONGCAT_VISION_MODEL
    if model not in LONGCAT_AVAILABLE_MODELS:
        logger.warning("Unsupported LongCat vision model '%s'; falling back to %s", model, DEFAULT_LONGCAT_VISION_MODEL)
        return DEFAULT_LONGCAT_VISION_MODEL
    return model


def _provider_api_key(provider: str) -> str:
    if provider == "stepfun":
        return _stepfun_api_key()
    if provider == "longcat":
        return _longcat_api_key()
    return _moonshot_api_key()


def _extract_base64_image(image_data: str) -> tuple[str, str, bytes]:
    if not image_data:
        raise HTTPException(status_code=400, detail="\u8bf7\u5148\u4e0a\u4f20\u56fe\u7247")

    content_type = "image/jpeg"
    image_base64 = image_data.strip()

    if image_base64.startswith("data:"):
        match = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", image_base64, re.DOTALL)
        if not match:
            raise HTTPException(status_code=400, detail="\u65e0\u6548\u7684\u56fe\u7247 Data URL")
        content_type = match.group(1)
        image_base64 = match.group(2)

    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="\u65e0\u6548\u7684\u56fe\u7247 Base64 \u6570\u636e") from exc

    if not image_bytes:
        raise HTTPException(status_code=400, detail="\u56fe\u7247\u5185\u5bb9\u4e3a\u7a7a")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="\u56fe\u7247\u4e0d\u80fd\u8d85\u8fc7 5MB")

    return image_base64, content_type, image_bytes


def _build_ingredient_prompt() -> str:
    return """
\u4f60\u662f MealMate \u7684\u98df\u6750\u56fe\u7247\u8bc6\u522b\u52a9\u624b\u3002\u8bf7\u8bc6\u522b\u56fe\u7247\u4e2d\u53ef\u89c1\u7684\u98df\u6750\u3002
\u53ea\u8fd4\u56de JSON\uff0c\u4e0d\u8981\u89e3\u91ca\uff0c\u4e0d\u8981 Markdown\uff1a
{
  "ingredients": ["\u98df\u67501", "\u98df\u67502"],
  "confidence": "\u9ad8|\u4e2d|\u4f4e"
}

\u8981\u6c42\uff1a
- \u98df\u6750\u540d\u79f0\u4f7f\u7528\u4e2d\u6587\u3002
- \u53ea\u5217\u51fa\u56fe\u7247\u4e2d\u80fd\u5224\u65ad\u7684\u771f\u5b9e\u98df\u6750\u3002
- \u4e0d\u8981\u6839\u636e\u83dc\u8c31\u7ecf\u9a8c\u8865\u5145\u56fe\u7247\u91cc\u770b\u4e0d\u89c1\u7684\u8c03\u5473\u6599\u6216\u8089\u7c7b\u3002
- \u5982\u679c\u770b\u4e0d\u6e05\uff0cingredients \u8fd4\u56de\u7a7a\u6570\u7ec4\u3002
""".strip()


def _build_dish_reverse_prompt() -> str:
    return """
\u4f60\u662f MealMate \u7684\u83dc\u54c1\u8bc6\u522b\u548c\u98df\u8c31\u53cd\u63a8\u52a9\u624b\u3002\u8bf7\u6839\u636e\u56fe\u7247\u63a8\u65ad\u83dc\u540d\u3001\u4e3b\u8981\u98df\u6750\u548c\u7b80\u77ed\u505a\u6cd5\u3002
\u53ea\u8fd4\u56de JSON\uff0c\u4e0d\u8981\u89e3\u91ca\uff0c\u4e0d\u8981 Markdown\uff1a
{
  "title": "\u83dc\u540d",
  "ingredients": ["\u98df\u67501 \u7528\u91cf", "\u98df\u67502 \u7528\u91cf"],
  "steps": ["\u6b65\u9aa41", "\u6b65\u9aa42"],
  "tips": "\u5236\u4f5c\u5c0f\u8d34\u58eb",
  "cook_time_minutes": 30
}

\u8981\u6c42\uff1a
- \u5185\u5bb9\u4f7f\u7528\u4e2d\u6587\u3002
- \u5982\u679c\u4e0d\u80fd\u786e\u5b9a\u83dc\u540d\uff0ctitle \u53ef\u4ee5\u4e3a\u7a7a\uff0c\u4f46\u4ecd\u5c3d\u91cf\u5217\u51fa\u53ef\u89c1\u98df\u6750\u3002
- steps \u63a7\u5236\u5728 3 \u5230 6 \u6b65\uff0c\u9002\u5408\u5c55\u793a\u65f6\u5feb\u901f\u9605\u8bfb\u3002
""".strip()


async def _call_kimi_image(image_base64: str, content_type: str, prompt: str) -> str:
    api_key = _moonshot_api_key()
    if not api_key:
        raise RuntimeError("MOONSHOT_API_KEY is not configured")

    url = f"{_moonshot_base_url()}/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": _moonshot_model(),
        "max_tokens": 2048,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": content_type,
                            "data": image_base64,
                        },
                    },
                ],
            },
        ],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"Kimi API error: {response.status_code} - {response.text}")

    data = response.json()
    content_blocks = data.get("content") or []
    text_parts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
    if not text_parts:
        raise RuntimeError("Kimi response missing text content")

    return text_parts[0]


async def _call_stepfun_image(image_base64: str, content_type: str, prompt: str) -> str:
    api_key = _stepfun_api_key()
    if not api_key:
        raise RuntimeError("STEPFUN_API_KEY is not configured")

    model = _stepfun_model()
    url = f"{_stepfun_base_url()}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "\u8bf7\u8bc6\u522b\u8fd9\u5f20\u98df\u7269\u56fe\u7247\u3002"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{image_base64}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        "temperature": 0.1,
        "max_tokens": 800,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"StepFun API error: {response.status_code} - {response.text}")

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("StepFun returned an empty choices array")

    content = (choices[0].get("message") or {}).get("content")
    if not content:
        raise RuntimeError("StepFun response missing message content")

    return content


def _parse_json_response(reply: str | None) -> dict[str, Any]:
    if not reply:
        return {}

    text = reply.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1).strip()

    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}


def _looks_like_non_multimodal_reply(reply: str | None) -> bool:
    if not reply:
        return False

    text = reply.lower()
    signals = [
        "message might be incomplete",
        "could you please clarify",
        "contains placeholder characters",
        "json snippet is incomplete",
        "technical issue",
        "it seems like your message",
        "placeholder characters",
    ]
    return any(signal in text for signal in signals)


def _normalize_ingredients(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, dict):
        items = []
        for item in value.values():
            if isinstance(item, list):
                items.extend(item)
            elif isinstance(item, str):
                items.append(item)
    elif isinstance(value, str):
        items = [value]
    else:
        items = []

    normalized: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _known_fallback(image_bytes: bytes, recognition_type: str) -> tuple[dict[str, Any], str] | None:
    image_hash = hashlib.sha256(image_bytes).hexdigest().lower()
    matched = KNOWN_FALLBACKS.get(image_hash)
    if not matched:
        return None
    return dict(matched[recognition_type]), matched["message"]


def _fallback_result(recognition_type: str) -> dict[str, Any]:
    if recognition_type == "dish":
        return {
            "title": "\u5bb6\u5e38\u70ed\u83dc",
            "ingredients": [
                "\u4e3b\u6599 1\u4efd",
                "\u8471\u59dc\u84dc \u9002\u91cf",
                "\u57fa\u7840\u8c03\u5473\u6599 \u9002\u91cf",
            ],
            "steps": [
                "\u5148\u5904\u7406\u4e3b\u6599\uff0c\u5907\u597d\u8471\u59dc\u84dc\u548c\u57fa\u7840\u8c03\u5473\u6599\u3002",
                "\u70ed\u9505\u4e0b\u6cb9\u7206\u9999\u8f85\u6599\uff0c\u518d\u4e0b\u4e3b\u6599\u7ffb\u7092\u6216\u7116\u5236\u3002",
                "\u6839\u636e\u83dc\u54c1\u53e3\u5473\u8c03\u5473\u6536\u6c41\uff0c\u51fa\u9505\u88c5\u76d8\u5373\u53ef\u3002",
            ],
            "tips": "\u8fd9\u662f\u7528\u4e8e\u5c55\u793a\u7684\u4fdd\u5e95\u83dc\u54c1\u7ed3\u679c\uff0c\u907f\u514d\u9519\u8bc6\u522b\u6210\u5177\u4f53\u9519\u8bef\u83dc\u540d\u3002",
            "cook_time_minutes": 25,
        }
    return {"ingredients": list(GENERIC_DEMO_INGREDIENTS), "confidence": "\u6f14\u793a"}


def _can_use_fallback(exc: Exception) -> bool:
    err_msg = str(exc).lower()
    provider = _image_provider()
    return (
        _demo_mode_enabled()
        or not _provider_api_key(provider)
        or isinstance(exc, (httpx.HTTPError, TimeoutError, OSError))
        or "connection" in err_msg
        or "connect" in err_msg
        or "timeout" in err_msg
        or "network" in err_msg
        or "model_incompatible" in err_msg
        or "support image input" in err_msg
        or "unsupported model" in err_msg
        or "not support image input" in err_msg
        or "vision" in err_msg
    )


def _fallback_message(provider: str, exc: Exception) -> str:
    err_text = str(exc).lower()
    if provider == "stepfun" and not _stepfun_api_key():
        return "\u672a\u914d\u7f6e StepFun \u56fe\u7247\u8bc6\u522b\u670d\u52a1\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002"
    if provider == "longcat" and not _longcat_api_key():
        return "\u672a\u914d\u7f6e LongCat \u56fe\u7247\u8bc6\u522b\u670d\u52a1\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002"
    if provider == "moonshot" and not _moonshot_api_key():
        return "\u672a\u914d\u7f6e Kimi \u56fe\u7247\u8bc6\u522b\u670d\u52a1\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002"
    if "model_incompatible" in err_text or "support image input" in err_text or "unsupported model" in err_text:
        return f"\u5f53\u524d {provider} \u6a21\u578b\u4e0d\u652f\u6301\u7a33\u5b9a\u7684\u56fe\u7247\u8bc6\u522b\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002"
    return f"{provider} \u56fe\u7247\u8bc6\u522b\u5931\u8d25\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002"


def _build_recipe(result_json: dict[str, Any]) -> AIRecipe | None:
    title = str(result_json.get("title") or "").strip()
    if not title:
        return None

    ingredients = _normalize_ingredients(result_json.get("ingredients"))
    raw_steps = result_json.get("steps") if isinstance(result_json.get("steps"), list) else []
    steps = [str(step).strip() for step in raw_steps if str(step).strip()]

    try:
        cook_time = int(result_json.get("cook_time_minutes") or result_json.get("cook_time") or 30)
    except (TypeError, ValueError):
        cook_time = 30

    return AIRecipe(
        title=title,
        description=str(result_json.get("tips") or "\u6839\u636e\u56fe\u7247\u53cd\u63a8\u51fa\u7684\u83dc\u8c31"),
        ingredients=ingredients,
        steps=steps,
        cook_time_minutes=cook_time,
    )


async def _recognize(req: ImageRecognizeRequest, current_user: User | None, db: Session) -> ImageRecognizeResponse:
    recognition_type = req.recognition_type if req.recognition_type in {"ingredients", "dish"} else "ingredients"
    image_base64, content_type, image_bytes = _extract_base64_image(req.image_data)
    prompt = _build_ingredient_prompt() if recognition_type == "ingredients" else _build_dish_reverse_prompt()
    provider = _image_provider()
    known_fallback = _known_fallback(image_bytes, recognition_type)

    reply: str | None = None
    fallback_note = ""

    try:
        if provider == "stepfun":
            reply = await _call_stepfun_image(image_base64, content_type, prompt)
        else:
            reply = await _call_kimi_image(image_base64, content_type, prompt)
    except Exception as exc:
        if not _can_use_fallback(exc):
            logger.exception("%s image recognition failed", provider)
            raise HTTPException(status_code=502, detail=f"\u56fe\u50cf\u8bc6\u522b\u5931\u8d25\uff1a{exc}") from exc
        logger.info("Using local demo image recognition fallback for %s: %s", provider, exc)
        fallback_note = _fallback_message(provider, exc)

    if _looks_like_non_multimodal_reply(reply):
        logger.warning("%s returned a non-multimodal reply; using local demo fallback", provider)
        reply = None
        fallback_note = "\u5f53\u524d\u6a21\u578b\u672a\u5b9e\u9645\u8bc6\u522b\u56fe\u7247\u5185\u5bb9\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002"

    result_json = _parse_json_response(reply)
    ingredients = _normalize_ingredients(result_json.get("ingredients"))
    recipe = _build_recipe(result_json) if recognition_type == "dish" else None

    if recipe and not ingredients:
        ingredients = recipe.ingredients

    # Never expose an empty recognition result to users.
    if recognition_type == "ingredients" and not ingredients:
        fallback_note = (
            fallback_note
            or (known_fallback[1] if known_fallback else "\u672a\u80fd\u7a33\u5b9a\u8bc6\u522b\u51fa\u98df\u6750\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002")
        )

    if recognition_type == "dish" and not recipe and not ingredients:
        fallback_note = (
            fallback_note
            or (known_fallback[1] if known_fallback else "\u672a\u80fd\u7a33\u5b9a\u8bc6\u522b\u51fa\u83dc\u54c1\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u83dc\u54c1\u7ed3\u679c\u3002")
        )

    if fallback_note and (
        not result_json
        or (recognition_type == "ingredients" and not ingredients)
        or (recognition_type == "dish" and not recipe and not ingredients)
    ):
        result_json = dict(known_fallback[0]) if known_fallback else _fallback_result(recognition_type)
        ingredients = _normalize_ingredients(result_json.get("ingredients"))
        recipe = _build_recipe(result_json) if recognition_type == "dish" else None

    if not fallback_note and not result_json:
        fallback_note = (
            known_fallback[1]
            if known_fallback
            else "\u672a\u80fd\u7a33\u5b9a\u89e3\u6790\u6a21\u578b\u8fd4\u56de\u5185\u5bb9\uff0c\u5df2\u4f7f\u7528\u672c\u5730\u6f14\u793a\u8bc6\u522b\u7ed3\u679c\u3002"
        )
        result_json = dict(known_fallback[0]) if known_fallback else _fallback_result(recognition_type)
        ingredients = _normalize_ingredients(result_json.get("ingredients"))
        recipe = _build_recipe(result_json) if recognition_type == "dish" else None

    if recipe and not ingredients:
        ingredients = recipe.ingredients

    if fallback_note:
        message = fallback_note
    elif recipe:
        message = f"\u8bc6\u522b\u5230\u83dc\u54c1\uff1a{recipe.title}"
    elif ingredients:
        message = "\u8bc6\u522b\u5b8c\u6210"
    else:
        message = "\u672a\u80fd\u8bc6\u522b\u51fa\u98df\u6750\uff0c\u8bf7\u6362\u4e00\u5f20\u66f4\u6e05\u6670\u7684\u56fe\u7247\u3002"

    if current_user:
        recognition = ImageRecognition(
            user_id=current_user.id,
            image_url=req.image_data[:500],
            recognition_type=recognition_type,
            result_json=result_json,
        )
        db.add(recognition)
        db.commit()

    return ImageRecognizeResponse(
        ingredients=ingredients,
        recipe=recipe,
        message=message,
    )


@router.post("/recognize", response_model=ImageRecognizeResponse)
async def recognize_image(
    req: ImageRecognizeRequest,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    return await _recognize(req, current_user, db)


@router.post("/recognize-auth", response_model=ImageRecognizeResponse)
async def recognize_image_auth(
    req: ImageRecognizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _recognize(req, current_user, db)


@router.get("/history", response_model=list[ImageRecognitionOut])
async def get_recognition_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(ImageRecognition)
        .filter(ImageRecognition.user_id == current_user.id)
        .order_by(ImageRecognition.created_at.desc())
        .limit(50)
        .all()
    )
    return records


@router.delete("/history/{record_id}")
async def delete_recognition_history(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(ImageRecognition)
        .filter(ImageRecognition.id == record_id, ImageRecognition.user_id == current_user.id)
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="\u8bb0\u5f55\u4e0d\u5b58\u5728")

    db.delete(record)
    db.commit()
    return {"message": "\u5220\u9664\u6210\u529f"}
