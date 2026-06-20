from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Recipe, SavedRecipe
from app.auth import get_current_user
from app.services.recipe_images import ensure_recipe_image_url

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


@router.post("/{recipe_id}")
def toggle_bookmark(recipe_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    existing = db.query(SavedRecipe).filter(
        SavedRecipe.user_id == current_user.id, SavedRecipe.recipe_id == recipe_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed"}
    saved = SavedRecipe(user_id=current_user.id, recipe_id=recipe_id)
    db.add(saved)
    db.commit()
    return {"status": "saved"}


@router.get("")
def get_bookmarks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    saved = db.query(SavedRecipe).filter(SavedRecipe.user_id == current_user.id).order_by(SavedRecipe.created_at.desc()).all()
    recipe_ids = [s.recipe_id for s in saved]
    recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
    result = []
    missing_before = False
    for r in recipes:
        image_url = ensure_recipe_image_url(
            r.title,
            r.description,
            r.ingredients if isinstance(r.ingredients, list) else [],
            r.image_url,
        )
        if image_url != (r.image_url or ""):
            r.image_url = image_url
            missing_before = True
        author = db.query(User).filter(User.id == r.author_id).first()
        result.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "image_url": image_url,
            "author_name": author.name if author else "",
            "likes_count": r.likes_count,
            "cook_time_minutes": r.cook_time_minutes,
            "created_at": r.created_at,
        })
    if missing_before:
        db.commit()
    return result
