import json
import os
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm_client import get_llm_client
from app.models import User, ChatSession
from app.schemas import AIGenerateRequest, AIChatRequest, AIGenerateResponse, AIChatResponse, AIRecipe
from app.auth import get_current_user
from app.services.recipe_images import ensure_recipe_image_url

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _extract_text_from_content(content) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    parts.append(text)
                continue
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("text"), str) and item.get("text").strip():
                parts.append(item["text"].strip())
                continue
            if item.get("type") == "text":
                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    parts.append(text_value.strip())
        return "\n".join(parts).strip()

    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"].strip()

    return ""


def _strip_recipe_blocks(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"```(?:recipe|json)\s*[\r\n]+[\s\S]*?```", "", text, flags=re.IGNORECASE).strip()


def _recipe_summary(recipe: AIRecipe | None, language: str = "zh") -> str:
    if not recipe:
        return ""

    ingredients = "、".join(recipe.ingredients[:6])
    if language == "zh":
        parts = [f"\u6211\u5df2\u7ecf\u4e3a\u4f60\u751f\u6210\u4e86\u300a{recipe.title}\u300b\u3002"]
        if recipe.description:
            parts.append(recipe.description)
        if ingredients:
            parts.append(f"\u4e3b\u8981\u98df\u6750\uff1a{ingredients}\u3002")
        return " ".join(parts).strip()

    parts = [f"I generated a recipe for {recipe.title}."]
    if recipe.description:
        parts.append(recipe.description)
    if ingredients:
        parts.append(f"Main ingredients: {ingredients}.")
    return " ".join(parts).strip()


def _assistant_message_for_history(reply: str, recipes: list[AIRecipe], language: str = "zh") -> str:
    cleaned = _strip_recipe_blocks(reply)
    if cleaned:
        return cleaned
    summary = _recipe_summary(recipes[0] if recipes else None, language)
    return summary or reply


def _normalized_history_messages(messages: list[dict], language: str = "zh") -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for msg in messages:
        role = str(msg.get("role") or "").strip()
        content = msg.get("content")
        if role not in {"system", "user", "assistant"}:
            continue
        if not isinstance(content, str):
            content = str(content or "")
        if role == "assistant":
            content = _strip_recipe_blocks(content) or content
        normalized.append({"role": role, "content": content})
    return normalized


async def _call_llm_chat(
    messages: list[dict[str, str]],
    temperature: float = 0.8,
    max_tokens: int = 2048,
) -> str:
    client = get_llm_client()
    try:
        reply = client.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not reply:
            raise RuntimeError("LLM returned empty response")
        return reply
    except Exception as e:
        logger = __import__("logging").getLogger(__name__)
        logger.error("LLM chat failed: %s", e)
        raise RuntimeError(f"AI generation failed: {str(e)}")


def _build_system_prompt(user: User, language: str = "zh") -> str:
    prefs = user.preferences or {}
    dietary = ", ".join(prefs.get("dietary", [])) or "不限"
    allergies = ", ".join(prefs.get("allergies", [])) or "无"
    skill = prefs.get("skill_level", "beginner")
    cuisines = ", ".join(prefs.get("cuisines", [])) or "都喜欢"

    skill_map = {"beginner": "厨房新手", "intermediate": "有点基础", "advanced": "大厨级别"}
    skill_zh = skill_map.get(skill, "厨房新手")

    return f"""你是 MealMate 的 AI 大厨——一个超有个性的年轻厨师朋友。

## 你的性格
- 说话活泼、有趣、带点小幽默，像朋友聊天一样自然
- 经常用emoji表情，但不要过度
- 会根据用户的心情给出不同风格的建议（累了推荐简单快手菜，开心了推荐来点仪式感的）
- 会夸用户的食材搭配眼光，给正面情绪价值
- 偶尔讲个跟食物相关的小知识或冷笑话

## 用户信息
- 饮食偏好: {dietary}
- 过敏原: {allergies}
- 厨艺水平: {skill_zh}
- 喜欢的菜系: {cuisines}

## 对话规则
1. 必须用中文回复
2. 先和用户聊几句，了解他们的心情、有什么食材、预算多少、想吃什么口味
3. 在对话中自然地生成菜谱建议
4. 当你推荐菜谱时，用以下JSON格式（嵌入在你的回复文字中，用 ```recipe 和 ``` 包裹）：

```recipe
{{
  "title": "菜名",
  "description": "一句话描述这道菜的灵魂",
  "vibe": "适合的心情/场景，比如'加班后的治愈系'",
  "difficulty": "简单/中等/进阶",
  "time_minutes": 20,
  "cost_estimate": "约15元",
  "ingredients": ["食材1 用量", "食材2 用量"],
  "steps": ["步骤1", "步骤2"],
  "tips": "一个让这道菜更好吃的秘诀",
  "image_keyword": "用于搜索图片的英文关键词，如 stir-fry-noodles"
}}
```

5. 一次最多推荐2道菜，除非用户要求更多
6. 严格遵守过敏原限制，提到可能的过敏风险时要温柔提醒
7. 如果用户说"随便"或"不知道吃什么"，主动推荐应季的、简单的菜"""


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_recipes(req: AIGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    system_prompt = _build_system_prompt(current_user, req.language)

    if req.language == "zh":
        user_message = f"我冰箱里有这些食材：{', '.join(req.ingredients)}。帮我想想做什么好吃的吧！"
    else:
        user_message = f"I have these ingredients: {', '.join(req.ingredients)}. What can I make?"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        reply = await _call_llm_chat(messages, temperature=0.8)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    # Extract recipes from the reply
    recipes = _extract_recipes(reply)
    assistant_history = _assistant_message_for_history(reply, recipes, req.language)

    session = ChatSession(
        user_id=current_user.id,
        messages=messages + [{"role": "assistant", "content": assistant_history}],
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return AIGenerateResponse(recipes=recipes, session_id=session.id)


@router.post("/chat/{session_id}", response_model=AIChatResponse)
async def chat_with_ai(session_id: int, req: AIChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = _normalized_history_messages(list(session.messages) if session.messages else [])
    messages.append({"role": "user", "content": req.message})

    try:
        reply = await _call_llm_chat(messages, temperature=0.8)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")

    messages.append({"role": "assistant", "content": reply})

    # Extract any recipe from the reply
    recipes = _extract_recipes(reply)
    updated_recipe = recipes[0] if recipes else None

    assistant_history = _assistant_message_for_history(reply, recipes, "zh")
    session.messages = messages[:-1] + [{"role": "assistant", "content": assistant_history}]
    db.commit()

    return AIChatResponse(reply=reply, updated_recipe=updated_recipe)


@router.post("/start")
async def start_chat(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start a new conversational chat session with the AI chef."""
    system_prompt = _build_system_prompt(current_user, "zh")

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    session = ChatSession(
        user_id=current_user.id,
        messages=messages,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "greeting": "嘿！今天想吃点什么呀？告诉我你冰箱里有什么食材，或者你现在是什么心情，我来帮你安排~ 🍳",
    }


@router.get("/sessions")
def get_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).limit(20).all()
    return [{"id": s.id, "created_at": s.created_at, "message_count": len(s.messages or [])} for s in sessions]


@router.get("/health")
def ai_health_check():
    """Check if the AI LLM client is properly configured."""
    from app.llm_client import get_llm_client
    import os
    
    client = get_llm_client()
    
    # Check environment variables
    primary_provider = os.getenv("PRIMARY_PROVIDER", "not set")
    longcat_key = os.getenv("LONGCAT_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    demo_mode = os.getenv("DEMO_MODE", "not set")
    
    return {
        "status": "ok",
        "demo_mode": demo_mode,
        "primary_provider": primary_provider,
        "longcat_configured": bool(longcat_key and longcat_key != "sk-..."),
        "openai_configured": bool(openai_key and openai_key != "sk-..."),
        "llm_demo_mode": client.is_demo_mode if hasattr(client, 'is_demo_mode') else "unknown",
    }


def _extract_recipes(text: str) -> list:
    """Extract recipe JSON blocks from AI response text."""
    recipes = []
    import re

    def coerce_recipe(data):
        if not isinstance(data, dict) or not data.get("title"):
            return None

        raw_ingredients = data.get("ingredients", [])
        ingredients = []
        if isinstance(raw_ingredients, list):
            for item in raw_ingredients:
                if isinstance(item, dict):
                    name = str(item.get("item") or item.get("name") or "").strip()
                    qty = str(item.get("qty") or item.get("quantity") or "").strip()
                    unit = str(item.get("unit") or "").strip()
                    text_value = " ".join(part for part in [name, qty, unit] if part).strip()
                    if text_value:
                        ingredients.append(text_value)
                else:
                    text_value = str(item).strip()
                    if text_value:
                        ingredients.append(text_value)
        elif isinstance(raw_ingredients, str):
            ingredients = [raw_ingredients]

        raw_steps = data.get("steps", [])
        steps = [str(step).strip() for step in raw_steps if str(step).strip()] if isinstance(raw_steps, list) else []

        cook_time = data.get("cook_time_minutes") or data.get("time_minutes")
        if cook_time is None:
            cook_time = (data.get("prep_minutes") or 0) + (data.get("cook_minutes") or 0)
        try:
            cook_time = int(cook_time or 30)
        except (TypeError, ValueError):
            cook_time = 30

        return AIRecipe(
            title=str(data.get("title", "")).strip(),
            description=str(data.get("description", "")).strip(),
            ingredients=ingredients,
            steps=steps,
            cook_time_minutes=cook_time,
            image_url=ensure_recipe_image_url(
                str(data.get("title", "")).strip(),
                str(data.get("description", "")).strip(),
                ingredients,
                str(data.get("image_url", "") or "").strip(),
            ),
        )

    def add_from_data(data):
        if isinstance(data, dict) and isinstance(data.get("recipes"), list):
            for item in data["recipes"]:
                recipe = coerce_recipe(item)
                if recipe:
                    recipes.append(recipe)
        elif isinstance(data, list):
            for item in data:
                recipe = coerce_recipe(item)
                if recipe:
                    recipes.append(recipe)
        else:
            recipe = coerce_recipe(data)
            if recipe:
                recipes.append(recipe)

    # Look for fenced recipe/json blocks.
    pattern = r'```(?:recipe|json)\s*\n?(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    for match in matches:
        try:
            data = json.loads(match.strip())
            add_from_data(data)
        except (json.JSONDecodeError, ValueError):
            pass

    # Also try the old format for backward compat
    if not recipes:
        try:
            data = json.loads(text)
            add_from_data(data)
        except (json.JSONDecodeError, ValueError):
            pass

    return recipes
