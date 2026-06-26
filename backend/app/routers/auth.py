from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut, UserUpdate
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(User.email == req.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if not req.password or len(req.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        user = User(
            email=req.email,
            password_hash=hash_password(req.password),
            name=req.name or "",
            preferences={"dietary": [], "allergies": [], "skill_level": "beginner", "cuisines": []},
            health_conditions=[],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(user.id)
        return TokenResponse(access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(req: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
