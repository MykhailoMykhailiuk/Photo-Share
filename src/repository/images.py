from datetime import datetime

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from cloudinary import CloudinaryImage
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.conf.config import config
from src.entity.models import Image, User
from src.schemas.image import ImageUpdateSchema

cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
)


async def upload_image(
    file: UploadFile, description: str, db: AsyncSession, user: User
):
    """The upload_image function uploads an image to Cloudinary and saves the image URL and description to the database.

    Args:
        file (file): The image file to upload.
        description (str): The description of the image.
        user_id (int): The ID of the user uploading the image.
        db (AsyncSession, optional): Pass in the database session.

    Returns:
        Image: Uploaded image
    """
    result = await run_in_threadpool(cloudinary.uploader.upload, file)
    image_url = result.get("url")

    image = Image(
        url=image_url,
        description=description,
        user_id=user.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(image)
    user = await db.merge(user)
    user.image_count += 1
    await db.commit()
    await db.refresh(user)
    await db.refresh(image)
    return image


async def update_image(
    image_id: int,
    body: ImageUpdateSchema,
    db: AsyncSession,
):
    """The update_image function updates the description of an existing image in the database.

    Args:
        image_id (int): Pass in the image object that is being updated.
        body (ImageUpdateSchema): The new description of the image.
        db (AsyncSession): Pass in the database session.

    Returns:
        Image: Updated image
    """
    stmt = (
        select(Image)
        .options(joinedload(Image.comments))
        .options(joinedload(Image.tags))
        .filter_by(id=image_id)
    )
    result = await db.execute(stmt)
    image = result.unique().scalar_one_or_none()
    if image:
        image.description = body.description
        image.updated_at = datetime.now()
        await db.commit()
        await db.refresh(image)
    return image


async def get_all_images(limit: int, offset: int, db: AsyncSession):
    """The get_all_images function displays a list of images with specified pagination parameters.

    Args:
        limit (int): The maximum number of images to return.
        offset (int): Skips the offset rows before beginning to return the rows.
        db (AsyncSession): Pass in the database session.

    Returns:
        List: List of image objects.
    """
    stmt = (
        select(Image)
        .options(joinedload(Image.comments))
        .options(joinedload(Image.tags))
        .offset(offset)
        .limit(limit)
    )
    images = await db.execute(stmt)
    return images.unique().scalars().all()


async def get_image(image_id: int, db: AsyncSession, user: User):
    """The get_image function displays specific user's image.

    Args:
        image_id (int): Pass in the image object in database.
        db (AsyncSession): Pass in the database session.
        user (User): Specific user.

    Returns:
        Image: Image
    """
    stmt = (
        select(Image)
        .options(joinedload(Image.comments))
        .options(joinedload(Image.tags))
        .filter_by(id=image_id, user=user)
    )
    image = await db.execute(stmt)
    return image.unique().scalar_one_or_none()


async def delete_image(image_id, db: AsyncSession):
    """The delete_image  function deletes an image from Cloudinary and the database.

    Args:
        image_id (int): Pass in the image object in database.
        db (AsyncSession): Pass in the database session.

    Returns:
        Image: Deleted image
    """

    # Retrieve the image from the database
    stmt = select(Image).filter_by(id=image_id)
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()
    stmt = select(User).filter_by(id=image.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    # Delete the image from Cloudinary
    parts = image.url.split("/")
    public_id_with_format = parts[-1]  # останній елемент у шляху
    public_id = public_id_with_format.split(".")[0]
    cloudinary.uploader.destroy(public_id)

    # Delete the image from the database
    await db.delete(image)
    user = await db.merge(user)
    user.image_count -= 1
    await db.commit()
    await db.refresh(user)
    return image


async def save_transformed_image(
    image_url: str, image_description: str, user: User, db: AsyncSession
):
    image = Image(
        url=image_url,
        description=image_description,
        user_id=user.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(image)
    user = await db.merge(user)
    user.image_count += 1
    await db.commit()
    await db.refresh(user)
    await db.refresh(image)
    return image


async def get_transformed_url(
    image_id: int, transformations: dict, user: User, db: AsyncSession
) -> str:
    image = await get_image(image_id, db, user)
    parts = image.url.split("/")
    public_id_with_format = parts[-1]
    trans_descriptions = parts[-2]
    transformed_url = CloudinaryImage(public_id_with_format).build_url(
        **transformations
    )
    new_image = await save_transformed_image(
        transformed_url, trans_descriptions, user, db
    )
    return new_image.url


async def get_foravatar_url(
    image_id: int, transformations: dict, user: User, db: AsyncSession
) -> str:
    image = await get_image(image_id, db, user)
    parts = image.url.split("/")
    public_id_with_format = parts[-1]
    trans_descriptions = parts[-2]
    transformed_url = CloudinaryImage(public_id_with_format).build_url(
        **transformations
    )
    piesces = transformed_url.split(".")
    new_image_url = ".".join(piesces[:-1]) + ".png"
    new_image = await save_transformed_image(
        new_image_url, trans_descriptions, user, db
    )
    return new_image.url
