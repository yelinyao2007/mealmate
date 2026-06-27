import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), default="")
    avatar_url = Column(String(512), default="")
    preferences = Column(JSON, default=dict)
    ai_memory = Column(JSON, default=dict)  # Agent 2 writes taste patterns here
    language = Column(String(10), default="en")  # User's language preference
    height = Column(Float, default=0.0)  # cm
    weight = Column(Float, default=0.0)  # kg
    age = Column(Integer, default=0)
    goal = Column(String(50), default="")  # lose_fat / gain_muscle / sugar_control / general
    target_calories = Column(Integer, default=0)
    health_conditions = Column(JSON, default=list)  # ["diabetes", "hypertension"]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recipes = relationship("Recipe", back_populates="author", foreign_keys="Recipe.author_id")
    comments = relationship("Comment", back_populates="author")
    chat_sessions = relationship("ChatSession", back_populates="user")
    notifications = relationship("Notification", back_populates="user", foreign_keys="[Notification.user_id]")
    weekly_plans = relationship("WeeklyPlan", back_populates="user")
    saved_recipes = relationship("SavedRecipe", back_populates="user")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    ingredients = Column(JSON, default=list)
    steps = Column(JSON, default=list)
    image_url = Column(String(512), default="")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    likes_count = Column(Integer, default=0)
    is_agent_generated = Column(Boolean, default=False)
    source_agent = Column(String(50), default="")  # "agent_1" / "agent_2" / "agent_3"
    remix_parent_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    cook_time_minutes = Column(Integer, default=0)
    prep_time_minutes = Column(Integer, default=0)
    difficulty = Column(String(50), default="")  # Easy / Medium / Hard
    tip = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    author = relationship("User", back_populates="recipes", foreign_keys=[author_id])
    comments = relationship("Comment", back_populates="recipe", cascade="all, delete-orphan")
    remixes = relationship("Recipe", backref="parent", remote_side=[id])
    likes = relationship("Like", back_populates="recipe", cascade="all, delete-orphan")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recipe = relationship("Recipe", back_populates="likes")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    is_ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    author = relationship("User", back_populates="comments")
    recipe = relationship("Recipe", back_populates="comments")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    messages = Column(JSON, default=list)
    current_recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    agent_type = Column(String(50), default="agent_1")  # agent_1 / agent_2 / agent_3
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    current_recipe = relationship("Recipe", foreign_keys=[current_recipe_id])


class SavedRecipe(Base):
    __tablename__ = "saved_recipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    source = Column(String(100), default="")  # "favorited_from_feed" / "agent_generated" / "weekly_plan"
    inferred_tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="saved_recipes")
    recipe = relationship("Recipe")


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_start = Column(DateTime, nullable=False)
    plan = Column(JSON, default=dict)
    grocery_list = Column(JSON, default=dict)
    total_estimated_cost = Column(Float, default=0.0)
    estimated_restaurant_cost = Column(Float, default=0.0)
    estimated_savings = Column(Float, default=0.0)
    savings_tip = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="weekly_plans")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    message = Column(Text, default="")
    source_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])
    source_user = relationship("User", foreign_keys=[source_user_id])


class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workflow_type = Column(String(100), nullable=False)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    steps_log = Column(JSON, default=list)
    status = Column(String(50), default="pending")  # pending | running | completed | error
    total_duration_ms = Column(Integer, default=0)
    steps_count = Column(Integer, default=0)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ImageRecognition(Base):
    __tablename__ = "image_recognitions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String(512), default="")  # Base64 or URL
    recognition_type = Column(String(50), nullable=False)  # "ingredients" | "dish"
    result_json = Column(JSON, default=dict)  # {ingredients: [], recipe: {}}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
