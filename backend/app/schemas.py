from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ── Auth ──
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ──
class UserPreferences(BaseModel):
    dietary: List[str] = []
    allergies: List[str] = []
    skill_level: str = "beginner"
    cuisines: List[str] = []


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    avatar_url: str
    preferences: Any
    ai_memory: Any = None
    language: str = "en"
    height: float = 0.0
    weight: float = 0.0
    age: int = 0
    goal: str = ""
    target_calories: int = 0
    health_conditions: Any = []
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    goal: Optional[str] = None  # lose_fat / gain_muscle / sugar_control / general
    target_calories: Optional[int] = None
    health_conditions: Optional[List[str]] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    profile: Optional[UserProfile] = None


# ── Recipe ──
class RecipeCreate(BaseModel):
    title: str
    description: str = ""
    ingredients: Any = []  # JSON array
    steps: List[str] = []
    image_url: str = ""
    cook_time_minutes: int = 0
    remix_parent_id: Optional[int] = None


class RecipeOut(BaseModel):
    id: int
    title: str
    description: str
    ingredients: Any
    steps: Any
    image_url: str
    author_id: int
    likes_count: int
    is_agent_generated: bool = False
    source_agent: str = ""
    remix_parent_id: Optional[int] = None
    cook_time_minutes: int
    prep_time_minutes: int = 0
    difficulty: str = ""
    tip: str = ""
    created_at: datetime
    author_name: str = ""
    is_liked: bool = False
    is_saved: bool = False
    comment_count: int = 0

    class Config:
        from_attributes = True


class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[Any] = None
    steps: Optional[List[str]] = None
    image_url: Optional[str] = None
    cook_time_minutes: Optional[int] = None


# ── Comment ──
class CommentCreate(BaseModel):
    text: str


class CommentOut(BaseModel):
    id: int
    text: str
    author_id: int
    author_name: str = ""
    recipe_id: int
    is_ai_generated: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ── Agent 1: Direct Chef ──
class Agent1StartRequest(BaseModel):
    ingredients: List[str]


class Agent1ChatRequest(BaseModel):
    message: str


class Agent1Response(BaseModel):
    reply: str
    session_id: int
    recipe: Optional[RecipeOut] = None


# ── Agent 2: Social Vision ──
class Agent2AnalyzeRequest(BaseModel):
    recipe_id: int  # the feed recipe to analyze


class Agent2Response(BaseModel):
    recipe_title: str
    ingredients: Any
    steps: List[str]
    preference_tags: List[str]
    auto_comment: str
    confidence: str
    saved_recipe_id: int
    new_recipe_id: int


# ── Agent 3: Weekly Planner ──
class Agent3GenerateRequest(BaseModel):
    pass  # uses saved recipes automatically


class Agent3Response(BaseModel):
    plan_id: int
    weekly_plan: Any
    grocery_list: Any
    total_estimated_cost: float
    estimated_restaurant_cost: float
    estimated_savings: float
    savings_tip: str


# ── SavedRecipe ──
class SavedRecipeOut(BaseModel):
    id: int
    user_id: int
    recipe_id: int
    source: str
    inferred_tags: Any
    created_at: datetime
    recipe: Optional[RecipeOut] = None

    class Config:
        from_attributes = True


# ── WeeklyPlan ──
class WeeklyPlanOut(BaseModel):
    id: int
    user_id: int
    week_start: datetime
    plan: Any
    grocery_list: Any
    total_estimated_cost: float
    estimated_restaurant_cost: float
    estimated_savings: float
    savings_tip: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Notification ──
class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    recipe_id: Optional[int]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Pagination ──
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int


# ── Legacy (kept for backward compat) ──
class AIGenerateRequest(BaseModel):
    ingredients: List[str]
    language: str = "en"


class AIChatRequest(BaseModel):
    message: str


class AIRecipe(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    steps: List[str]
    cook_time_minutes: int = 30
    image_url: str = ""


class AIGenerateResponse(BaseModel):
    recipes: List[AIRecipe]
    session_id: int


class AIChatResponse(BaseModel):
    reply: str
    updated_recipe: Optional[AIRecipe] = None


class ImageRecognizeRequest(BaseModel):
    image_data: str  # Base64 encoded image
    recognition_type: str = "ingredients"  # "ingredients" or "dish"


class ImageRecognizeResponse(BaseModel):
    ingredients: List[str] = []
    recipe: Optional[AIRecipe] = None
    message: str = ""


class ImageRecognitionOut(BaseModel):
    id: int
    user_id: int
    image_url: str
    recognition_type: str
    result_json: dict
    created_at: datetime

    class Config:
        from_attributes = True
