from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.db import get_db
from src.entity.models import User
from src.repository import tags as repository_tags
from src.schemas.tag import TagResponse, TagSchema, TagUpdateSchema
from src.services.auth import auth_service, role_required

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=List[TagResponse])
async def read_tags(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """The get_tags function displays existing tags.

    Args:
        skip (int): The number of images to skip.
        limit (int): The maximum number of images to return.
        db (AsyncSession): Pass in the database session.

    Returns:
        List[Tag]: List of all tags
    """
    tags = await repository_tags.get_tags(skip, limit, db)
    if tags is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.TAG_NOT_FOUND
        )
    return tags


@router.get("/{tag_name}", response_model=TagResponse)
async def read_tag(tag_name: str, db: AsyncSession = Depends(get_db)):
    """The get_tag function displays a tag by given name.

    Args:
        tag_name (str): Pass in the tag object in database.
        db (AsyncSession): Pass in the database session.

    Returns:
        Optional[Tag]: Existing tag
    """
    tag = await repository_tags.get_tag(tag_name, db)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.TAG_NOT_FOUND
        )
    return tag


@router.post("/", response_model=List[TagResponse], status_code=status.HTTP_201_CREATED)
async def create_tags(body: TagSchema, db: AsyncSession = Depends(get_db)):
    """The create_tags function creates a new tags.

    Args:
        body (TagSchema): Validate the request body.
        db (AsyncSession): Pass in the database session.

    Returns:
        List[Tag]: List of created tags.
    """
    try:
        tags = await repository_tags.create_tags(body, db)
        return tags
    except ValidationError as e:
        print(e.json())  # Додатковий лог для відлагодження
        raise HTTPException(status_code=422, detail=e.errors())


@router.put(
    "/update/{tag_id}",
    response_model=TagResponse,
    dependencies=[Depends(role_required(["admin", "moderator"]))],
)
async def update_tag(
    body: TagUpdateSchema, tag_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)
):
    """The update_tag function updates a tag.

    Args:
        tag_id (int): Pass in the tag object in database.
        body (TagSchema): Validate the request body.
        db (AsyncSession): Pass in the database session.

    Returns:
        Tag: Updated tag.
    """
    tag = await repository_tags.update_tag(tag_id, body, db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.TAG_NOT_FOUND
        )
    return tag


@router.delete(
    "/delete/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(role_required(["admin", "moderator"]))],
)
async def remove_tag(tag_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    """The remove_tag function removes a tag.

    Args:
        tag_id (int): Pass in the tag object in database.
        db (AsyncSession): Pass in the database session.

    Returns:
        Tag: Removed tag
    """
    tag = await repository_tags.remove_tag(tag_id, db)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.TAG_NOT_FOUND
        )
    return tag


@router.post(
    "/add_tags_for_image",
    status_code=status.HTTP_201_CREATED,
)
async def add_tags_for_image_route(
    tags_list: TagSchema,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """The add_tags_for_image function adds tags to image.

    Args:
        tags_list (TagSchema): List of tags.
        image_id (int): Pass in the image object in database.
        user (User): Current user.
        db (AsyncSession): Pass in the database session.

    Returns:
        Dict: A dictionary with the message key.
    """
    created_tags = await repository_tags.add_tags_for_image(
        tags_list, image_id, user, db
    )
    if not created_tags:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found or does not belong to the user",
        )
    return {"message": "Tags added successfully"}
