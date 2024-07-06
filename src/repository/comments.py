from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.db import get_db
from src.entity.models import Comment, Image, User
from src.schemas.comments import CommentCreate


async def get_comment(comment_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """The get_comment function returns a comment object from the database based on the comment's id provided.
        If no comment is found, None is returned.

    Args:
        comment_id (int): Comment's id in database.
        db (AsyncSession, optional): Pass in the database session.

    Returns:
        Comment: Existing comment
    """
    stmt = select(Comment).filter_by(id=comment_id)
    comment = await db.execute(stmt)
    comment = comment.scalar_one_or_none()
    return comment


async def create_comment(
    image_id: int,
    current_user: User,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    """The create_comment function creates a new comment.

    Args:
        image_id (int): Image's id for comment it.
        current_user (User): Comment creator.
        body (CommentCreate): Validate the request body.
        db (AsyncSession, optional): Pass in the database session.

    Returns:
        Comment: Created comment
    """
    stmt = select(Image).filter_by(id=image_id)
    image = await db.execute(stmt)
    image = image.scalar_one_or_none()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    new_comment = Comment(name=body.name, image_id=image.id, user_id=current_user.id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


async def update_comment(
    comment_id: int, coment_update: CommentCreate, db: AsyncSession = Depends(get_db)
) -> None:
    """The update_comment function updates the comments.

    Args:
        comment_id (int): Pass in the comment object that is being updated.
        coment_update (CommentCreate): Pass in the new data for the comment updating.
        db (AsyncSession, optional): Pass in the database session to the function.

    Returns:
        Comment: Updated comment.
    """
    comment = await get_comment(comment_id, db)
    if comment:
        comment.name = coment_update.name
        await db.commit()
        await db.refresh(comment)
    return comment


async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """The remove_comment function removes comment from database.

    Args:
        comment_id (int): Pass in the comment object that is being updated.
        db (AsyncSession, optional): Pass in the database session to the function.

    Returns:
        Comment: Deleted comment
    """
    comment = await get_comment(comment_id, db)
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment
