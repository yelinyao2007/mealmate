"""Agent 1: The Direct Chef — ingredients → immediate recipe → chat refinement."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, ChatSession, Recipe
from app.schemas import Agent1StartRequest, Agent1ChatRequest, Agent1Response, RecipeOut
from app.auth import get_current_user
from app.llm_client import get_llm_client

router = APIRouter(prefix="/api/agent1", tags=["agent1-direct-chef"])

SYSTEM_PROMPT_TEMPLATE = """You are a culinary AI assistant for young home cooks. Rules you MUST follow:

1. The user will provide a list of available ingredients.
2. IMMEDIATELY output ONE complete recipe. NEVER ask clarifying questions on the first message.
3. Prioritize ingredients that spoil quickly (fresh produce, dairy, meat) over pantry staples.
4. Consider the user's profile preferences (provided below) for diet, allergies, skill level, and preferred cuisines.
5. Format your response EXACTLY as:

**🍳 [Recipe Title]**
⏱ Prep: X min | Cook: Y min | Total: Z min
Difficulty: [Easy/Medium/Hard]

**Ingredients:**
- [qty] [ingredient]
...

**Steps:**
1. [step]
2. [step]
...

**💡 Tip:** [one practical cooking tip relevant to this dish]

6. If the user sends follow-up messages (e.g., "make it spicy", "remove the cheese", "under 15 minutes"), IMMEDIATELY rewrite the FULL recipe with adjustments. Do NOT just list the changes — always output the complete updated recipe.
7. Keep language casual, encouraging, and suitable for young adults (18-25).
8. ALSO output a JSON block at the very end wrapped in ```json and ``` with this structure:
```json
{{"title":"...","description":"...","ingredients":[{{"item":"...","qty":"...","unit":"..."}}],"steps":["Step 1: ..."],"prep_minutes":0,"cook_minutes":0,"difficulty":"Easy","tip":"..."}}
```

USER PROFILE:
{user_prefs}"""


def _build_system_prompt(user: User) -> str:
    prefs = user.preferences or {}
    base = SYSTEM_PROMPT_TEMPLATE.format(user_prefs=json.dumps(prefs, ensure_ascii=False))
    user_lang = getattr(user, 'language', None) or 'en'
    if user_lang == 'zh':
        base += "\n\nIMPORTANT: You MUST respond in Chinese (中文). All recipe titles, ingredients, steps, tips, and descriptions must be in Chinese."
    return base


def _parse_recipe_json(text: str) -> dict | None:
    """Extract the JSON block from the assistant reply."""
    import re
    m = re.search(r'```json\s*\n?(.*?)```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    return None


def _recipe_to_out(r: Recipe, user: User) -> RecipeOut:
    return RecipeOut(
        id=r.id, title=r.title, description=r.description, ingredients=r.ingredients,
        steps=r.steps, image_url=r.image_url, author_id=r.author_id, likes_count=r.likes_count,
        is_agent_generated=r.is_agent_generated, source_agent=r.source_agent,
        remix_parent_id=r.remix_parent_id, cook_time_minutes=r.cook_time_minutes,
        prep_time_minutes=r.prep_time_minutes, difficulty=r.difficulty, tip=r.tip,
        created_at=r.created_at, author_name=user.name,
    )


@router.post("/start", response_model=Agent1Response)
def start_chef_chat(req: Agent1StartRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """User sends ingredients → AI immediately returns a full recipe."""
    llm = get_llm_client()
    system_prompt = _build_system_prompt(current_user)

    user_msg = f"I have these ingredients: {', '.join(req.ingredients)}. Give me a recipe!"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    try:
        reply = llm.chat_completion(messages, temperature=0.7)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 1 failed: {str(e)}")

    messages.append({"role": "assistant", "content": reply})

    # Parse recipe from reply
    recipe_data = _parse_recipe_json(reply)
    recipe_obj = None
    if recipe_data:
        recipe_obj = Recipe(
            title=recipe_data.get("title", "Untitled"),
            description=recipe_data.get("description", ""),
            ingredients=recipe_data.get("ingredients", []),
            steps=recipe_data.get("steps", []),
            prep_time_minutes=recipe_data.get("prep_minutes", 0),
            cook_time_minutes=recipe_data.get("cook_minutes", 0),
            difficulty=recipe_data.get("difficulty", ""),
            tip=recipe_data.get("tip", ""),
            author_id=current_user.id,
            is_agent_generated=True,
            source_agent="agent_1",
        )
        db.add(recipe_obj)
        db.flush()

    session = ChatSession(
        user_id=current_user.id,
        messages=messages,
        agent_type="agent_1",
        is_active=True,
        current_recipe_id=recipe_obj.id if recipe_obj else None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    if recipe_obj:
        db.refresh(recipe_obj)

    return Agent1Response(
        reply=reply,
        session_id=session.id,
        recipe=_recipe_to_out(recipe_obj, current_user) if recipe_obj else None,
    )


@router.post("/chat/{session_id}", response_model=Agent1Response)
def chef_followup(session_id: int, req: Agent1ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Follow-up chat to refine the recipe (e.g., 'make it spicy')."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.agent_type == "agent_1",
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    llm = get_llm_client()
    messages = list(session.messages or [])
    messages.append({"role": "user", "content": req.message})

    try:
        reply = llm.chat_completion(messages, temperature=0.7)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 1 failed: {str(e)}")

    messages.append({"role": "assistant", "content": reply})
    session.messages = messages

    # Update existing recipe or create new one
    recipe_data = _parse_recipe_json(reply)
    recipe_obj = None
    if recipe_data and session.current_recipe_id:
        recipe_obj = db.query(Recipe).get(session.current_recipe_id)
        if recipe_obj:
            recipe_obj.title = recipe_data.get("title", recipe_obj.title)
            recipe_obj.description = recipe_data.get("description", recipe_obj.description)
            recipe_obj.ingredients = recipe_data.get("ingredients", recipe_obj.ingredients)
            recipe_obj.steps = recipe_data.get("steps", recipe_obj.steps)
            recipe_obj.prep_time_minutes = recipe_data.get("prep_minutes", recipe_obj.prep_time_minutes)
            recipe_obj.cook_time_minutes = recipe_data.get("cook_minutes", recipe_obj.cook_time_minutes)
            recipe_obj.difficulty = recipe_data.get("difficulty", recipe_obj.difficulty)
            recipe_obj.tip = recipe_data.get("tip", recipe_obj.tip)
    elif recipe_data:
        recipe_obj = Recipe(
            title=recipe_data.get("title", "Untitled"),
            description=recipe_data.get("description", ""),
            ingredients=recipe_data.get("ingredients", []),
            steps=recipe_data.get("steps", []),
            prep_time_minutes=recipe_data.get("prep_minutes", 0),
            cook_time_minutes=recipe_data.get("cook_minutes", 0),
            difficulty=recipe_data.get("difficulty", ""),
            tip=recipe_data.get("tip", ""),
            author_id=current_user.id,
            is_agent_generated=True,
            source_agent="agent_1",
        )
        db.add(recipe_obj)
        db.flush()
        session.current_recipe_id = recipe_obj.id

    db.commit()
    if recipe_obj:
        db.refresh(recipe_obj)

    return Agent1Response(
        reply=reply,
        session_id=session.id,
        recipe=_recipe_to_out(recipe_obj, current_user) if recipe_obj else None,
    )
