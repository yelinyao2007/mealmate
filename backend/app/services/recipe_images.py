import hashlib
import html
import json
import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


def _kimi_api_key() -> str:
    return os.getenv("MOONSHOT_API_KEY", "").strip()


def _kimi_base_url() -> str:
    return os.getenv("MOONSHOT_BASE_URL", "https://api.kimi.com/coding/v1").strip().rstrip("/")


def _get_stepfun_style(title: str, description: str, ingredients: list[str]) -> dict | None:
    """Use StepFun to determine dish visual style (type + colors)."""
    api_key = os.getenv("STEPFUN_API_KEY", "").strip()
    base_url = os.getenv("STEPFUN_BASE_URL", "https://api.xiaomimimo.com/v1").strip().rstrip("/")
    model = os.getenv("STEPFUN_VISION_MODEL", "mimo-v2.5").strip() or "mimo-v2.5"
    if not api_key:
        return None
    prompt = (
        f'食谱：{title}\n描述：{description}\n食材：{"、".join(ingredients[:6])}\n'
        f'请分析这道菜的视觉风格，返回JSON：{{"type":"meat|noodle|soup|seafood|dish","bg1":"背景主色hex","bg2":"背景辅色hex","accent":"强调色hex"}}\n只返回JSON。'
    )
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "max_tokens": 200, "messages": [{"role": "user", "content": prompt}]}
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            return None
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return None
        text = (choices[0].get("message") or {}).get("content", "").strip()
        if not text:
            return None
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)
    except Exception as e:
        logger.debug("StepFun style API error: %s", e)
        return None


def _get_kimi_style(title: str, description: str, ingredients: list[str]) -> dict | None:
    """Use Kimi kimi-k2.6 to determine dish visual style (type + colors)."""
    key = _kimi_api_key()
    if not key:
        return None
    prompt = (
        f'食谱：{title}\n描述：{description}\n食材：{"、".join(ingredients[:6])}\n'
        f'请分析这道菜的视觉风格，返回JSON：{{"type":"meat|noodle|soup|seafood|dish","bg1":"背景主色hex","bg2":"背景辅色hex","accent":"强调色hex"}}\n只返回JSON。'
    )
    url = f"{_kimi_base_url()}/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    }
    payload = {"model": "kimi-k2.6", "max_tokens": 200, "messages": [{"role": "user", "content": prompt}]}
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            return None
        data = resp.json()
        texts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        if not texts:
            return None
        text = texts[0].strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)
    except Exception as e:
        logger.debug("Kimi style API error: %s", e)
        return None


def _normalize_ingredient_texts(ingredients: list | None) -> list[str]:
    normalized: list[str] = []
    for item in ingredients or []:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("item") or "").strip()
            qty = str(item.get("quantity") or item.get("qty") or "").strip()
            unit = str(item.get("unit") or "").strip()
            text = " ".join(part for part in [name, qty, unit] if part).strip()
        else:
            text = str(item).strip()

        if text:
            normalized.append(text)
    return normalized


def _pick_palette(text: str) -> tuple[str, str, str]:
    source = text.lower()
    if any(token in source for token in ["辣", "香辣", "麻辣", "川", "红油", "spicy"]):
        return "#7a1f1a", "#d94a2f", "#f6c16a"
    if any(token in source for token in ["糖醋", "sweet", "sour", "茄汁", "番茄"]):
        return "#6f241d", "#c84d34", "#f4b65d"
    if any(token in source for token in ["清蒸", "白灼", "蔬菜", "沙拉", "凉拌", "green"]):
        return "#365a38", "#76a66e", "#dce8b2"
    if any(token in source for token in ["咖喱", "南洋", "curry"]):
        return "#6b4b14", "#d39b2a", "#f3d27b"
    return "#5f341f", "#d37a3b", "#f0c987"


def _detect_dish_type(text: str) -> str:
    source = text.lower()
    if any(token in source for token in ["排", "肉", "牛", "鸡", "鸭", "猪", "pork", "beef", "ribs", "steak"]):
        return "meat"
    if any(token in source for token in ["面", "粉", "意面", "pasta", "noodle"]):
        return "noodle"
    if any(token in source for token in ["汤", "粥", "羹", "soup"]):
        return "soup"
    if any(token in source for token in ["虾", "鱼", "海鲜", "shrimp", "fish", "seafood"]):
        return "seafood"
    return "dish"


def _shape_for_type(dish_type: str) -> str:
    if dish_type == "meat":
        return """
        <ellipse cx="420" cy="305" rx="160" ry="110" fill="#f7f1e5"/>
        <ellipse cx="420" cy="305" rx="140" ry="96" fill="#fffaf0"/>
        <ellipse cx="420" cy="305" rx="150" ry="103" fill="none" stroke="#d4c5b2" stroke-width="2"/>
        <ellipse cx="380" cy="278" rx="50" ry="30" fill="#8b3a25" transform="rotate(-10 380 278)"/>
        <ellipse cx="380" cy="278" rx="44" ry="24" fill="#a84e32" transform="rotate(-10 380 278)"/>
        <ellipse cx="450" cy="310" rx="55" ry="32" fill="#7a2e1a" transform="rotate(8 450 310)"/>
        <ellipse cx="450" cy="310" rx="48" ry="26" fill="#9e452a" transform="rotate(8 450 310)"/>
        <ellipse cx="410" cy="340" rx="45" ry="26" fill="#8f3d25" transform="rotate(-5 410 340)"/>
        <ellipse cx="410" cy="340" rx="40" ry="22" fill="#b05335" transform="rotate(-5 410 340)"/>
        <ellipse cx="395" cy="305" rx="25" ry="8" fill="rgba(139,58,37,0.6)"/>
        <ellipse cx="440" cy="328" rx="20" ry="6" fill="rgba(122,46,26,0.5)"/>
        <circle cx="355" cy="260" r="5" fill="#5a8a3c"/>
        <circle cx="470" cy="290" r="4" fill="#5a8a3c"/>
        <circle cx="390" cy="355" r="4" fill="#5a8a3c"/>
        <path d="M400 230 Q395 210 405 195" stroke="rgba(255,255,255,0.5)" stroke-width="3" fill="none"/>
        <path d="M430 225 Q425 200 435 185" stroke="rgba(255,255,255,0.4)" stroke-width="2.5" fill="none"/>
        """
    if dish_type == "noodle":
        return """
        <ellipse cx="420" cy="305" rx="160" ry="110" fill="#f7f1e5"/>
        <ellipse cx="420" cy="305" rx="140" ry="96" fill="#fffaf0"/>
        <ellipse cx="420" cy="305" rx="150" ry="103" fill="none" stroke="#d4c5b2" stroke-width="2"/>
        <ellipse cx="420" cy="320" rx="100" ry="60" fill="#e8ddd2"/>
        <ellipse cx="420" cy="320" rx="95" ry="56" fill="#f5f0e8"/>
        <path d="M360 310 C380 290, 410 285, 440 290 C460 295, 475 305, 470 320" stroke="#f0d58c" stroke-width="6" fill="none"/>
        <path d="M355 320 C375 300, 415 295, 445 300 C465 305, 480 315, 475 330" stroke="#e8c97a" stroke-width="5" fill="none"/>
        <path d="M365 330 C385 310, 420 305, 450 310 C465 315, 475 325, 470 340" stroke="#f2da96" stroke-width="5" fill="none"/>
        <path d="M370 305 C390 285, 425 280, 455 285 C470 290, 480 300, 475 315" stroke="#e5c46e" stroke-width="4" fill="none"/>
        <line x1="300" y1="260" x2="350" y2="350" stroke="#8b6f4e" stroke-width="4" stroke-linecap="round"/>
        <line x1="315" y1="258" x2="365" y2="348" stroke="#8b6f4e" stroke-width="4" stroke-linecap="round"/>
        <path d="M400 260 Q395 240 405 225" stroke="rgba(255,255,255,0.5)" stroke-width="3" fill="none"/>
        <path d="M430 255 Q425 230 435 215" stroke="rgba(255,255,255,0.4)" stroke-width="2.5" fill="none"/>
        """
    if dish_type == "soup":
        return """
        <ellipse cx="420" cy="310" rx="155" ry="108" fill="#f7f1e5"/>
        <ellipse cx="420" cy="310" rx="135" ry="94" fill="#fffaf0"/>
        <ellipse cx="420" cy="310" rx="145" ry="100" fill="none" stroke="#d4c5b2" stroke-width="2"/>
        <ellipse cx="420" cy="325" rx="105" ry="50" fill="#d4b896"/>
        <ellipse cx="420" cy="325" rx="100" ry="46" fill="#f0dbb8"/>
        <ellipse cx="420" cy="318" rx="90" ry="38" fill="#d9a95a"/>
        <ellipse cx="420" cy="316" rx="85" ry="34" fill="#e8c07a"/>
        <circle cx="390" cy="308" r="10" fill="#d48c4a"/>
        <circle cx="445" cy="320" r="8" fill="#b8723a"/>
        <circle cx="415" cy="330" r="7" fill="#5a8a3c"/>
        <circle cx="375" cy="325" r="6" fill="#d48c4a"/>
        <circle cx="455" cy="305" r="5" fill="#5a8a3c"/>
        <path d="M400 260 C395 240, 405 225, 398 210" stroke="rgba(255,255,255,0.5)" stroke-width="3" fill="none"/>
        <path d="M430 255 C425 235, 435 220, 428 205" stroke="rgba(255,255,255,0.4)" stroke-width="2.5" fill="none"/>
        <path d="M415 250 C410 230, 420 215, 413 200" stroke="rgba(255,255,255,0.3)" stroke-width="2" fill="none"/>
        """
    if dish_type == "seafood":
        return """
        <ellipse cx="420" cy="305" rx="160" ry="110" fill="#f7f1e5"/>
        <ellipse cx="420" cy="305" rx="140" ry="96" fill="#fffaf0"/>
        <ellipse cx="420" cy="305" rx="150" ry="103" fill="none" stroke="#d4c5b2" stroke-width="2"/>
        <ellipse cx="420" cy="300" rx="75" ry="38" fill="#c4794a"/>
        <ellipse cx="420" cy="298" rx="68" ry="32" fill="#da9460"/>
        <circle cx="360" cy="295" r="22" fill="#c4794a"/>
        <circle cx="358" cy="293" r="18" fill="#da9460"/>
        <circle cx="352" cy="289" r="3" fill="#2a1a12"/>
        <path d="M490 285 L510 270 L505 300 L510 330 L490 315 Z" fill="#b0683a"/>
        <path d="M410 265 L420 250 L430 268 Z" fill="#b0683a"/>
        <path d="M405 335 L415 350 L425 333 Z" fill="#b0683a"/>
        <circle cx="375" cy="330" r="5" fill="#5a8a3c"/>
        <circle cx="460" cy="280" r="4" fill="#e8a020"/>
        <circle cx="445" cy="340" r="4" fill="#5a8a3c"/>
        """
    return """
    <ellipse cx="420" cy="305" rx="160" ry="110" fill="#f7f1e5"/>
    <ellipse cx="420" cy="305" rx="140" ry="96" fill="#fffaf0"/>
    <ellipse cx="420" cy="305" rx="150" ry="103" fill="none" stroke="#d4c5b2" stroke-width="2"/>
    <ellipse cx="420" cy="290" rx="80" ry="50" fill="#d48c4a"/>
    <ellipse cx="420" cy="285" rx="72" ry="42" fill="#e0a05a"/>
    <ellipse cx="405" cy="275" rx="30" ry="20" fill="#e8b070"/>
    <ellipse cx="440" cy="300" rx="35" ry="22" fill="#c87a3a"/>
    <path d="M380 270 Q390 255 405 268" stroke="#5a8a3c" stroke-width="5" fill="none" stroke-linecap="round"/>
    <path d="M450 280 Q460 265 470 278" stroke="#5a8a3c" stroke-width="4" fill="none" stroke-linecap="round"/>
    <circle cx="395" cy="310" r="4" fill="#e8a020"/>
    <circle cx="450" cy="295" r="3" fill="#e8a020"/>
    <circle cx="415" cy="330" r="4" fill="#5a8a3c"/>
    """


def _build_svg(title: str, description: str = "", ingredients: list[str] | None = None, style: dict | None = None) -> str:
    ingredients = _normalize_ingredient_texts(ingredients)
    joined = " ".join([title, description, " ".join(ingredients[:6])])
    if style:
        bg1 = style.get("bg1", "#5f341f")
        bg2 = style.get("bg2", "#d37a3b")
        accent = style.get("accent", "#f0c987")
        dish_type = style.get("type", "dish")
    else:
        bg1, bg2, accent = _pick_palette(joined)
        dish_type = _detect_dish_type(joined)
    escaped_title = html.escape((title or "").strip()[:32] or "Chef Special")
    escaped_subtitle = html.escape((description or "").strip()[:60] or "Freshly prepared, richly flavored")
    garnish = "、".join([item.strip() for item in ingredients[:4] if item.strip()]) or "美味热菜"
    escaped_garnish = html.escape(garnish[:40])

    # Build ingredient tags
    ingredient_tags = ""
    for i, item in enumerate(ingredients[:6]):
        x = 690 + (i % 2) * 185
        y = 510 + (i // 2) * 50
        ingredient_tags += f"""
        <rect x="{x}" y="{y}" width="170" height="36" rx="18" fill="rgba(255,250,241,0.25)"/>
        <text x="{x + 85}" y="{y + 24}" font-size="16" fill="#fff8eb" text-anchor="middle"
              font-family="'Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif">{html.escape(item[:20])}</text>"""

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1.2" y2="1.2">
          <stop offset="0%" stop-color="{bg1}" />
          <stop offset="100%" stop-color="{bg2}" />
        </linearGradient>
        <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255,250,241,0.97)" />
          <stop offset="100%" stop-color="rgba(245,238,228,0.97)" />
        </linearGradient>
        <radialGradient id="glow" cx="45%" cy="38%" r="55%">
          <stop offset="0%" stop-color="rgba(255,255,255,0.20)" />
          <stop offset="100%" stop-color="rgba(255,255,255,0)" />
        </radialGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="18" stdDeviation="24" flood-color="rgba(0,0,0,0.35)"/>
        </filter>
        <filter id="innerShadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="rgba(0,0,0,0.15)"/>
        </filter>
      </defs>

      <!-- Background -->
      <rect width="1200" height="900" fill="url(#bg)" />
      <!-- Decorative circles -->
      <circle cx="980" cy="120" r="260" fill="rgba(255,255,255,0.06)" />
      <circle cx="120" cy="800" r="300" fill="rgba(255,255,255,0.04)" />
      <circle cx="600" cy="-100" r="350" fill="rgba(255,255,255,0.03)" />
      <!-- Center glow -->
      <ellipse cx="580" cy="320" rx="420" ry="240" fill="url(#glow)" />

      <!-- Left: Plate with food -->
      <g filter="url(#shadow)">
        <!-- Plate shadow -->
        <ellipse cx="420" cy="320" rx="172" ry="118" fill="rgba(0,0,0,0.12)"/>
        <!-- Plate -->
        {_shape_for_type(dish_type)}
      </g>

      <!-- Right: Info card -->
      <rect x="640" y="120" width="500" height="660" rx="40" fill="url(#card)" filter="url(#innerShadow)"/>
      <rect x="640" y="120" width="500" height="660" rx="40" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1"/>

      <!-- Category badge -->
      <rect x="670" y="145" width="100" height="30" rx="15" fill="{accent}"/>
      <text x="720" y="165" font-size="14" fill="#fff" text-anchor="middle" font-weight="600"
            font-family="'Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif">今日推荐</text>

      <!-- Title -->
      <text x="670" y="230" font-size="48" font-weight="800" fill="#2d1810"
            font-family="'Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif">{escaped_title}</text>

      <!-- Description -->
      <text x="670" y="280" font-size="20" fill="#7a5a48"
            font-family="'Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif">{escaped_subtitle}</text>

      <!-- Divider -->
      <line x1="670" y1="310" x2="1110" y2="310" stroke="rgba(45,24,16,0.08)" stroke-width="1"/>

      <!-- Section: 主要食材 -->
      <text x="670" y="350" font-size="18" font-weight="700" fill="#4a2e22"
            font-family="'Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif">主要食材</text>
      {ingredient_tags}

      <!-- MealMate branding -->
      <rect x="670" y="680" width="160" height="44" rx="22" fill="{accent}" opacity="0.15"/>
      <text x="750" y="708" font-size="16" font-weight="700" fill="{accent}" text-anchor="middle"
            font-family="'Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif">MealMate</text>

      <!-- Decorative dots -->
      <circle cx="670" cy="750" r="4" fill="{accent}" opacity="0.3"/>
      <circle cx="690" cy="750" r="4" fill="{accent}" opacity="0.3"/>
      <circle cx="710" cy="750" r="4" fill="{accent}" opacity="0.3"/>
    </svg>
    """.strip()

    return svg

def ensure_recipe_image_url(title: str, description: str = "", ingredients: list[str] | None = None, image_url: str = "") -> str:
    if image_url and str(image_url).strip():
        return str(image_url).strip()

    ingredients = _normalize_ingredient_texts(ingredients)
    digest = hashlib.sha256(
        f"{title}|{description}|{'|'.join(ingredients[:8])}".encode("utf-8")
    ).hexdigest()[:16]
    static_root = Path(__file__).resolve().parents[2] / "static"
    output_dir = static_root / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"recipe-{digest}.svg"

    if not output_path.exists():
        # Try StepFun-generated style first, fallback to Kimi, then default
        style = _get_stepfun_style(title, description, ingredients)
        if style:
            logger.info("Using StepFun style for recipe: %s", title)
        else:
            style = _get_kimi_style(title, description, ingredients)
            if style:
                logger.info("Using Kimi style for recipe: %s", title)
        if style:
            svg = _build_svg(title, description, ingredients, style=style)
        else:
            logger.info("Using default style for recipe: %s", title)
            svg = _build_svg(title, description, ingredients)
        output_path.write_text(svg, encoding="utf-8")

    return f"/generated/{output_path.name}"
