from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Recipe, Like, Comment, Notification
from app.schemas import CommentCreate, CommentOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/recipes", tags=["social"])


@router.post("/{recipe_id}/like")
def toggle_like(recipe_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    existing = db.query(Like).filter(Like.user_id == current_user.id, Like.recipe_id == recipe_id).first()
    if existing:
        db.delete(existing)
        recipe.likes_count = max(0, recipe.likes_count - 1)
        db.commit()
        return {"status": "unliked", "likes_count": recipe.likes_count}
    like = Like(user_id=current_user.id, recipe_id=recipe_id)
    db.add(like)
    recipe.likes_count += 1
    if recipe.author_id != current_user.id:
        notif = Notification(
            user_id=recipe.author_id,
            type="like",
            message=f"{current_user.name or current_user.email} liked your recipe '{recipe.title}'",
            recipe_id=recipe_id,
        )
        db.add(notif)
    db.commit()
    return {"status": "liked", "likes_count": recipe.likes_count}


@router.get("/{recipe_id}/comments")
def get_comments(recipe_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.recipe_id == recipe_id).order_by(Comment.created_at.desc()).all()
    result = []
    for c in comments:
        author = db.query(User).filter(User.id == c.author_id).first()
        result.append(CommentOut(
            id=c.id,
            text=c.text,
            author_id=c.author_id,
            author_name=author.name if author else "",
            recipe_id=c.recipe_id,
            created_at=c.created_at,
        ))
    return result


@router.post("/{recipe_id}/comments", response_model=CommentOut)
def add_comment(recipe_id: int, req: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    comment = Comment(text=req.text, author_id=current_user.id, recipe_id=recipe_id)
    db.add(comment)
    if recipe.author_id != current_user.id:
        notif = Notification(
            user_id=recipe.author_id,
            type="comment",
            message=f"{current_user.name or current_user.email} commented on your recipe '{recipe.title}'",
            recipe_id=recipe_id,
        )
        db.add(notif)
    db.commit()
    db.refresh(comment)
    return CommentOut(
        id=comment.id,
        text=comment.text,
        author_id=comment.author_id,
        author_name=current_user.name,
        recipe_id=comment.recipe_id,
        created_at=comment.created_at,
    )
