"""Agent 2: Social Memory & Vision — analyze food photos, reverse-engineer recipes, auto-comment, learn taste."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Recipe, SavedRecipe, Comment, Notification
from app.schemas import Agent2AnalyzeRequest, Agent2Response
from app.auth import get_current_user
from app.llm_client import get_llm_client

router = APIRouter(prefix="/api/agent2", tags=["agent2-social-vision"])

SYSTEM_PROMPT_TEMPLATE = """You are a food vision and social AI assistant. You will receive a food recipe's title, description, and ingredient list (since we cannot send images directly, use these details to infer the dish).

Your tasks — complete ALL of them in ONE response:

1. ANALYZE the dish based on the provided information.
2. REVERSE-ENGINEER a detailed recipe:
   - Recipe title (can improve on the original)
   - Full ingredient list with quantities
   - Clear cooking steps (5-8 steps max)
3. EXTRACT PREFERENCE TAGS: Output 3-5 tags about this dish (e.g., "high-protein", "Asian", "comfort-food", "quick", "avocado").
4. GENERATE A FRIENDLY COMMENT: Write a short, enthusiastic comment (1-2 sentences) that the user could leave on this post. Make it sound natural, like a real young person wrote it — not robotic.

Format your ENTIRE response as valid JSON (no markdown wrapper):
{{
  "recipe_title": "...",
  "description": "A short appetizing description",
  "ingredients": [{{"item":"...","qty":"...","unit":"..."}}],
  "steps": ["Step 1: ...", "Step 2: ..."],
  "preference_tags": ["tag1","tag2","tag3"],
  "auto_comment": "...",
  "confidence": "high"
}}

USER'S EXISTING TASTE MEMORY:
{ai_memory}"""


@router.post("/analyze", response_model=Agent2Response)
async def analyze_and_favorite(req: Agent2AnalyzeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """User taps favorite on a feed photo → AI analyzes, reverse-engineers recipe, auto-comments, updates taste memory."""
    # Get the original recipe
    orig_recipe = db.query(Recipe).filter(Recipe.id == req.recipe_id).first()
    if not orig_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    llm = get_llm_client()
    ai_memory = json.dumps(current_user.ai_memory or {}, ensure_ascii=False)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(ai_memory=ai_memory)

    # Build user message with recipe details
    user_msg = f"""Analyze this dish and generate a detailed recipe:
Title: {orig_recipe.title}
Description: {orig_recipe.description}
Ingredients listed: {json.dumps(orig_recipe.ingredients, ensure_ascii=False)}
Posted by: {orig_recipe.author.name if orig_recipe.author else 'unknown'}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    try:
        reply = llm.chat_completion(messages, temperature=0.6)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 2 failed: {str(e)}")

    # Parse JSON response
    try:
        # Try to parse directly, or extract from markdown
        import re
        clean = reply.strip()
        if clean.startswith("```"):
            m = re.search(r'```(?:json)?\s*\n?(.*?)```', clean, re.DOTALL)
            if m:
                clean = m.group(1).strip()
        data = json.loads(clean)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Agent 2 returned invalid JSON")

    # Create new recipe (reverse-engineered version)
    new_recipe = Recipe(
        title=data.get("recipe_title", orig_recipe.title),
        description=data.get("description", ""),
        ingredients=data.get("ingredients", []),
        steps=data.get("steps", []),
        image_url=orig_recipe.image_url,
        author_id=current_user.id,
        is_agent_generated=True,
        source_agent="agent_2",
        remix_parent_id=orig_recipe.id,
    )
    db.add(new_recipe)
    db.flush()

    # Create SavedRecipe
    saved = SavedRecipe(
        user_id=current_user.id,
        recipe_id=new_recipe.id,
        source="favorited_from_feed",
        inferred_tags=data.get("preference_tags", []),
    )
    db.add(saved)

    # Auto-comment on original recipe
    comment = Comment(
        text=data.get("auto_comment", "Looks delicious! 🔥"),
        author_id=current_user.id,
        recipe_id=orig_recipe.id,
        is_ai_generated=True,
    )
    db.add(comment)

    # Update likes count on original
    orig_recipe.likes_count = (orig_recipe.likes_count or 0) + 1

    # Update user's AI memory
    memory = dict(current_user.ai_memory or {})
    liked_styles = memory.get("liked_styles", [])
    new_tags = data.get("preference_tags", [])
    for tag in new_tags:
        if tag not in liked_styles:
            liked_styles.append(tag)
    memory["liked_styles"] = liked_styles
    memory["liked_count"] = memory.get("liked_count", 0) + 1
    current_user.ai_memory = memory

    # Notify the original recipe author
    if orig_recipe.author_id != current_user.id:
        notif = Notification(
            user_id=orig_recipe.author_id,
            type="like",
            message=f"{current_user.name} loved your dish and saved it!",
            source_user_id=current_user.id,
            recipe_id=orig_recipe.id,
        )
        db.add(notif)

    db.commit()
    db.refresh(new_recipe)
    db.refresh(saved)

    return Agent2Response(
        recipe_title=data.get("recipe_title", ""),
        ingredients=data.get("ingredients", []),
        steps=data.get("steps", []),
        preference_tags=data.get("preference_tags", []),
        auto_comment=data.get("auto_comment", ""),
        confidence=data.get("confidence", "medium"),
        saved_recipe_id=saved.id,
        new_recipe_id=new_recipe.id,
    )
