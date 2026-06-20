from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, Recipe, Like, SavedRecipe, Comment, Follow
from app.schemas import RecipeCreate, RecipeOut, RecipeUpdate
from app.auth import get_current_user, get_optional_user
from app.services.recipe_images import ensure_recipe_image_url

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _enrich_recipe(recipe: Recipe, user: Optional[User], db: Session) -> dict:
    image_url = ensure_recipe_image_url(
        recipe.title,
        recipe.description,
        recipe.ingredients if isinstance(recipe.ingredients, list) else [],
        recipe.image_url,
    )
    if image_url != (recipe.image_url or ""):
        recipe.image_url = image_url

    author = db.query(User).filter(User.id == recipe.author_id).first()
    is_liked = False
    is_saved = False
    if user:
        is_liked = db.query(Like).filter(Like.user_id == user.id, Like.recipe_id == recipe.id).first() is not None
        is_saved = db.query(SavedRecipe).filter(SavedRecipe.user_id == user.id, SavedRecipe.recipe_id == recipe.id).first() is not None
    comment_count = db.query(Comment).filter(Comment.recipe_id == recipe.id).count()
    return RecipeOut(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        ingredients=recipe.ingredients,
        steps=recipe.steps,
        image_url=image_url,
        author_id=recipe.author_id,
        likes_count=recipe.likes_count,
        is_agent_generated=recipe.is_agent_generated or False,
        source_agent=recipe.source_agent or "",
        remix_parent_id=recipe.remix_parent_id,
        cook_time_minutes=recipe.cook_time_minutes,
        prep_time_minutes=recipe.prep_time_minutes or 0,
        difficulty=recipe.difficulty or "",
        tip=recipe.tip or "",
        created_at=recipe.created_at,
        author_name=author.name if author else "",
        is_liked=is_liked,
        is_saved=is_saved,
        comment_count=comment_count,
    )


@router.get("/feed")
def recipe_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("newest"),
    following_only: bool = Query(False),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    q = db.query(Recipe)
    if following_only and current_user:
        following_ids = [f.following_id for f in db.query(Follow).filter(Follow.follower_id == current_user.id).all()]
        q = q.filter(Recipe.author_id.in_(following_ids))
    if sort == "popular":
        q = q.order_by(Recipe.likes_count.desc())
    else:
        q = q.order_by(Recipe.created_at.desc())
    total = q.count()
    recipes = q.offset((page - 1) * page_size).limit(page_size).all()
    missing_before = any(not (r.image_url or "").strip() for r in recipes)
    items = [_enrich_recipe(r, current_user, db) for r in recipes]
    if missing_before:
        db.commit()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/", response_model=RecipeOut)
@router.post("", response_model=RecipeOut)
def create_recipe(req: RecipeCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = Recipe(
        title=req.title,
        description=req.description,
        ingredients=req.ingredients,
        steps=req.steps,
        image_url=ensure_recipe_image_url(
            req.title,
            req.description,
            req.ingredients if isinstance(req.ingredients, list) else [],
            req.image_url,
        ),
        author_id=current_user.id,
        cook_time_minutes=req.cook_time_minutes,
        remix_parent_id=req.remix_parent_id,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return _enrich_recipe(recipe, current_user, db)


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, current_user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    missing_before = not (recipe.image_url or "").strip()
    item = _enrich_recipe(recipe, current_user, db)
    if missing_before:
        db.commit()
    return item


@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: int, req: RecipeUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your recipe")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(recipe, field, value)
    recipe.image_url = ensure_recipe_image_url(
        recipe.title,
        recipe.description,
        recipe.ingredients if isinstance(recipe.ingredients, list) else [],
        recipe.image_url,
    )
    db.commit()
    db.refresh(recipe)
    return _enrich_recipe(recipe, current_user, db)


@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your recipe")
    db.delete(recipe)
    db.commit()
    return {"status": "deleted"}


@router.get("/{recipe_id}/remixes")
def get_remixes(recipe_id: int, current_user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    remixes = db.query(Recipe).filter(Recipe.remix_parent_id == recipe_id).order_by(Recipe.created_at.desc()).all()
    missing_before = any(not (r.image_url or "").strip() for r in remixes)
    items = [_enrich_recipe(r, current_user, db) for r in remixes]
    if missing_before:
        db.commit()
    return items
