"""Agent 3: Weekly Planner & Shopper — 7-day meal plan from saved recipes, consolidated grocery list, savings."""
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, SavedRecipe, Recipe, WeeklyPlan, Notification
from app.schemas import Agent3Response
from app.auth import get_current_user
from app.llm_client import get_llm_client

router = APIRouter(prefix="/api/agent3", tags=["agent3-weekly-planner"])

SYSTEM_PROMPT_TEMPLATE = """You are a weekly meal planning assistant for young adults. You will receive:
- A list of the user's favorite/saved recipes (titles and ingredients)
- The user's dietary preferences and allergies

Your tasks:

1. CREATE A 7-DAY MEAL PLAN (dinner only, unless the user asks for more):
   - Use the provided favorite recipes as the primary source
   - Ensure variety (don't repeat the same recipe within the week)
   - If there aren't enough saved recipes, suggest 1-2 new ones that match the user's taste profile

2. GENERATE A CONSOLIDATED GROCERY LIST:
   - Combine duplicate ingredients across all 7 days
   - Subtract common pantry staples the user likely already has (salt, pepper, oil, sugar)
   - Group by grocery store section (Produce, Dairy, Meat, Pantry, etc.)

3. ESTIMATE WEEKLY SAVINGS:
   - Estimate the rough cost of buying all ingredients
   - Estimate what meals would cost if ordered from a restaurant
   - Calculate the difference as "savings"

Format your ENTIRE response as valid JSON (no markdown wrapper):
{{
  "weekly_plan": {{
    "monday": {{"meal": "Recipe Title", "is_new_suggestion": false}},
    "tuesday": {{"meal": "Recipe Title", "is_new_suggestion": false}},
    "wednesday": {{"meal": "Recipe Title", "is_new_suggestion": false}},
    "thursday": {{"meal": "Recipe Title", "is_new_suggestion": true}},
    "friday": {{"meal": "Recipe Title", "is_new_suggestion": false}},
    "saturday": {{"meal": "Recipe Title", "is_new_suggestion": false}},
    "sunday": {{"meal": "Recipe Title", "is_new_suggestion": true}}
  }},
  "grocery_list": {{
    "produce": [{{"item": "onion", "qty": 3, "unit": "whole", "est_price": 1.50}}],
    "dairy": [],
    "meat": [],
    "pantry": [],
    "other": []
  }},
  "total_estimated_cost": 45.00,
  "estimated_restaurant_cost": 140.00,
  "estimated_savings": 95.00,
  "savings_tip": "Buying a whole chicken instead of pre-cut saves about $4 this week!"
}}

USER PREFERENCES:
{user_prefs}"""


@router.post("/generate", response_model=Agent3Response)
async def generate_weekly_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a 7-day meal plan from the user's saved/favorited recipes."""
    # Gather saved recipes
    saved_entries = db.query(SavedRecipe).filter(
        SavedRecipe.user_id == current_user.id
    ).order_by(SavedRecipe.created_at.desc()).limit(15).all()

    # Also include user's own agent-generated recipes
    own_recipes = db.query(Recipe).filter(
        Recipe.author_id == current_user.id,
        Recipe.is_agent_generated == True,
    ).order_by(Recipe.created_at.desc()).limit(10).all()

    # Compile recipe info
    compiled = []
    seen_ids = set()
    for se in saved_entries:
        r = se.recipe
        if r and r.id not in seen_ids:
            compiled.append({"title": r.title, "ingredients": r.ingredients})
            seen_ids.add(r.id)
    for r in own_recipes:
        if r.id not in seen_ids:
            compiled.append({"title": r.title, "ingredients": r.ingredients})
            seen_ids.add(r.id)

    if not compiled:
        raise HTTPException(status_code=400, detail="You need at least a few saved recipes to generate a weekly plan. Try favoriting some recipes from the feed or generating some with the chef!")

    llm = get_llm_client()
    prefs = json.dumps(current_user.preferences or {}, ensure_ascii=False)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_prefs=prefs)

    user_msg = f"""Here are my saved recipes:
{json.dumps(compiled, ensure_ascii=False, indent=2)}

Please create my weekly meal plan and grocery list."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    try:
        reply = llm.chat_completion(messages, temperature=0.6)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 3 failed: {str(e)}")

    # Parse JSON response
    try:
        import re
        clean = reply.strip()
        if clean.startswith("```"):
            m = re.search(r'```(?:json)?\s*\n?(.*?)```', clean, re.DOTALL)
            if m:
                clean = m.group(1).strip()
        data = json.loads(clean)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Agent 3 returned invalid JSON")

    # Calculate week start (next Monday)
    today = datetime.date.today()
    days_ahead = 0 - today.weekday()  # Monday
    if days_ahead < 0:
        days_ahead += 7
    week_start = today + datetime.timedelta(days=days_ahead)

    plan = WeeklyPlan(
        user_id=current_user.id,
        week_start=datetime.datetime.combine(week_start, datetime.time()),
        plan=data.get("weekly_plan", {}),
        grocery_list=data.get("grocery_list", {}),
        total_estimated_cost=data.get("total_estimated_cost", 0),
        estimated_restaurant_cost=data.get("estimated_restaurant_cost", 0),
        estimated_savings=data.get("estimated_savings", 0),
        savings_tip=data.get("savings_tip", ""),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return Agent3Response(
        plan_id=plan.id,
        weekly_plan=plan.plan,
        grocery_list=plan.grocery_list,
        total_estimated_cost=plan.total_estimated_cost,
        estimated_restaurant_cost=plan.estimated_restaurant_cost,
        estimated_savings=plan.estimated_savings,
        savings_tip=plan.savings_tip,
    )


@router.get("/latest")
def get_latest_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the user's most recent weekly plan."""
    plan = db.query(WeeklyPlan).filter(
        WeeklyPlan.user_id == current_user.id
    ).order_by(WeeklyPlan.created_at.desc()).first()
    if not plan:
        return {"plan": None}
    return {
        "plan_id": plan.id,
        "week_start": plan.week_start,
        "weekly_plan": plan.plan,
        "grocery_list": plan.grocery_list,
        "total_estimated_cost": plan.total_estimated_cost,
        "estimated_restaurant_cost": plan.estimated_restaurant_cost,
        "estimated_savings": plan.estimated_savings,
        "savings_tip": plan.savings_tip,
    }
