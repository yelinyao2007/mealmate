"""Smart Chef router — Natural language cooking with multi-agent orchestration."""
from fastapi import APIRouter, Depends
from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.agents.smart_chef import SmartChefAgent

router = APIRouter(prefix="/api/smart-chef", tags=["smart-chef"])


@router.post("/generate")
def smart_generate(request_data: dict, current_user: User = Depends(get_current_user)):
    user_input = request_data.get("user_input", "")

    user_profile = {
        "height": current_user.height or 0,
        "weight": current_user.weight or 0,
        "age": current_user.age or 0,
        "goal": current_user.goal or "",
        "target_calories": current_user.target_calories or 0,
        "health_conditions": current_user.health_conditions or [],
        "allergies": (current_user.preferences or {}).get("allergies", []),
        "dietary": (current_user.preferences or {}).get("dietary", []),
        "skill_level": (current_user.preferences or {}).get("skill_level", "beginner"),
    }

    agent = SmartChefAgent()
    result = agent.run({
        "user_input": user_input,
        "user_profile": user_profile,
    })

    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "steps": [
            {
                "step_number": s.step_number if hasattr(s, 'step_number') else (i + 1),
                "agent_name": s.agent_name if hasattr(s, 'agent_name') else "SmartChefAgent",
                "status": s.status if hasattr(s, 'status') else "completed",
                "action": s.action if hasattr(s, 'action') else "analyze",
                "duration_ms": s.duration_ms if hasattr(s, 'duration_ms') else 0,
            }
            for i, s in enumerate(result.steps)
        ],
    }
