from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Image, Tag, User, image_tag_table
from src.schemas.tag import TagSchema, TagUpdateSchema


async def create_tags(body: TagSchema, db: AsyncSession) -> List[Tag]:
    """The create_tags function creates a new tags.

    Args:
        body (TagSchema): Validate the request body.
        db (AsyncSession): Pass in the database session.

    Returns:
        List[Tag]: List of created tags.
    """
    existing_tags_query = await db.execute(
        select(Tag).where(Tag.name.in_(body.tag_list))
    )
    existing_tags = {tag.name for tag in existing_tags_query.scalars().all()}
    tags_in_db = []
    new_tags = []
    for tag_name in body.tag_list:
        if tag_name not in existing_tags:
            new_tag = Tag(name=tag_name)
            db.add(new_tag)
            new_tags.append(new_tag)
        else:
            tags_in_db.append(tag_name)

    await db.commit()
    for new_tag in new_tags:
        await db.refresh(new_tag)
    for tag_name in tags_in_db:
        tag = await get_tag(tag_name, db)
        new_tags.append(tag)
    return new_tags


async def get_tags(skip: int, limit: int, db: AsyncSession) -> List[Tag]:
    """The get_tags function displays existing tags.

    Args:
        skip (int): The number of images to skip.
        limit (int): The maximum number of images to return.
        db (AsyncSession): Pass in the database session.

    Returns:
        List[Tag]: List of all tags
    """
    stmt = select(Tag).offset(skip).limit(limit)
    tags = await db.execute(stmt)
    return tags.scalars().all()


async def get_tag(tag_name: str, db: AsyncSession) -> Optional[Tag]:
    """The get_tag function displays a tag by given name.

    Args:
        tag_name (str): Pass in the tag object in database.
        db (AsyncSession): Pass in the database session.

    Returns:
        Optional[Tag]: Existing tag
    """
    stmt = select(Tag).filter_by(name=tag_name)
    tag = await db.execute(stmt)
    return tag.scalar_one_or_none()


async def update_tag(tag_id: int, body: TagUpdateSchema, db: AsyncSession):
    """The update_tag function updates a tag.

    Args:
        tag_id (int): Pass in the tag object in database.
        body (TagSchema): Validate the request body.
        db (AsyncSession): Pass in the database session.

    Returns:
        Tag: Updated tag.
    """
    stmt = select(Tag).filter_by(id=tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if tag:
        tag.name = body.name
        await db.commit()
        await db.refresh(tag)
    return tag


async def remove_tag(tag_id: int, db: AsyncSession):
    """The remove_tag function removes a tag.

    Args:
        tag_id (int): Pass in the tag object in database.
        db (AsyncSession): Pass in the database session.

    Returns:
        Tag: Removed tag
    """
    stmt = select(Tag).filter_by(id=tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if tag:
        await db.delete(tag)
        await db.commit()
    return tag


async def add_tags_for_image(
    tags_data: TagSchema, image_id: int, user: User, db: AsyncSession
) -> Optional[List[Tag]]:
    """The add_tags_for_image function adds tags to image.

    Args:
        tags_data (TagSchema): List of tags.
        image_id (int): Pass in the image object in database.
        user (User): Current user.
        db (AsyncSession): Pass in the database session.

    Returns:
        Optional[List[Tag]]: List of tags.
    """
    # Пошук зображення за ID, що належить користувачеві
    stmt = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()

    if image:
        # Перевірка кількості існуючих тегів, прив'язаних до зображення
        existing_tags_query = select(image_tag_table.c.tag_id).where(
            image_tag_table.c.image_id == image_id
        )
        existing_tags_result = await db.execute(existing_tags_query)
        existing_tag_ids = existing_tags_result.scalars().all()
        existing_tag_count = len(existing_tag_ids)

        if existing_tag_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many tags, maximum 5 tags allowed",
            )

        # Створення тегів, якщо їх ще не існує
        created_tags = await create_tags(tags_data, db)

        # Додавання зв'язків між зображенням та створеними тегами у проміжну таблицю
        values = []
        for tag in created_tags:
            if (
                tag.id not in existing_tag_ids
            ):  # перевірка чи тег вже доданий до зображення
                if existing_tag_count < 5:
                    values.append({"image_id": image_id, "tag_id": tag.id})
                    existing_tag_count += 1
                else:
                    break

        if values:
            stmt = image_tag_table.insert().values(values)
            try:
                await db.execute(stmt)
                await db.commit()
            except IntegrityError:
                await (
                    db.rollback()
                )  # обробка помилки, якщо тег вже доданий до зображення
                pass

        return created_tags

    return None
