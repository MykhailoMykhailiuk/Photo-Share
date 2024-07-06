from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.db import get_db
from src.entity.models import Comment, User
from src.repository import comments as repositories_comments
from src.schemas.comments import (
    CommentCreate,
    CommentResponse,
)
from src.services.auth import auth_service, role_required


router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/create", response_model=CommentResponse)
async def create_comment(
    image_id: int,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """The create_comment function creates a new comment.

    Args:
        image_id (int): Pass in the image object in database.
        comment (CommentCreate): Validate the request body.
        db (AsyncSession, optional): Pass in the database session.
        current_user (User, optional): Comment's creator.

    Returns:
        Comment: Created comment.
    """
    new_comment = await repositories_comments.create_comment(image_id, current_user, comment, db)
    return new_comment


@router.put("/update/{comment_id}",
            response_model=CommentResponse,
            dependencies=[Depends(auth_service.get_current_active_user)]
)
async def update_comment(
    comment_id: int,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    """The create_comment function creates a new comment.

    Args:
        comment_id (int): Pass in the comment object in database.
        comment (CommentCreate): Validate the request body for comment updating.
        db (AsyncSession, optional): Pass in the database session.

    Returns:
        Comment: Updated comment.
    """
    new_comment = await repositories_comments.update_comment(comment_id, comment, db)
    if new_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.COMMENT_NOT_FOUND)
    return new_comment


@router.delete("/delete/{comment_id}", dependencies=[Depends(role_required(["admin", "moderator"]))])
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """The create_comment function creates a new comment.

    Args:
        comment_id (int): Pass in the comment object in database.
        db (AsyncSession, optional): Pass in the database session.

    Returns:
        Str: Confirmation message.
    """
    new_comment = await repositories_comments.delete_comment(comment_id, db)
    if new_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.COMMENT_NOT_FOUND)
    return "Comment deleted successfully"