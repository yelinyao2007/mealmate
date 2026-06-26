from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Follow
from app.schemas import UserOut, UserUpdate
from app.auth import get_current_user
from app.agents.profile import ProfileAgent

router = APIRouter(prefix="/api/users", tags=["users"])

SUPPORTED_LANGUAGES = ["en", "zh"]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me", response_model=UserOut)
def update_profile(req: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.name is not None:
        current_user.name = req.name
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url
    if req.preferences is not None:
        current_user.preferences = req.preferences.model_dump()
    if req.profile is not None:
        if req.profile.height is not None:
            current_user.height = req.profile.height
        if req.profile.weight is not None:
            current_user.weight = req.profile.weight
        if req.profile.age is not None:
            current_user.age = req.profile.age
        if req.profile.goal is not None:
            current_user.goal = req.profile.goal
        if req.profile.target_calories is not None:
            current_user.target_calories = req.profile.target_calories
        if req.profile.health_conditions is not None:
            current_user.health_conditions = req.profile.health_conditions
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/follow/{user_id}")
def follow_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id, Follow.following_id == user_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "unfollowed"}
    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    return {"status": "followed"}


@router.get("/me/following")
def get_following(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    follows = db.query(Follow).filter(Follow.follower_id == current_user.id).all()
    user_ids = [f.following_id for f in follows]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return [{"id": u.id, "name": u.name, "avatar_url": u.avatar_url} for u in users]


@router.get("/me/followers")
def get_followers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    follows = db.query(Follow).filter(Follow.following_id == current_user.id).all()
    user_ids = [f.follower_id for f in follows]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return [{"id": u.id, "name": u.name, "avatar_url": u.avatar_url} for u in users]


@router.get("/me/language")
def get_language(current_user: User = Depends(get_current_user)):
    """Get user's language preference."""
    return {"language": current_user.language or "en"}


@router.put("/me/language")
def update_language(lang: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user's language preference."""
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            detail=f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    current_user.language = lang
    db.commit()
    db.refresh(current_user)
    return {"language": current_user.language}


@router.post("/me/analyze-profile")
def analyze_profile(current_user: User = Depends(get_current_user)):
    """Analyze user's health profile using ProfileAgent and return recommendations."""
    agent = ProfileAgent()
    result = agent.run({
        "height": current_user.height or 0,
        "weight": current_user.weight or 0,
        "age": current_user.age or 0,
        "goal": current_user.goal or "",
        "target_calories": current_user.target_calories or 0,
        "health_conditions": current_user.health_conditions or [],
        "preferences": current_user.preferences or {},
    })
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
    }
