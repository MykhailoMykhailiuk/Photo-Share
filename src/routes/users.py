import pickle

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.database.db import get_db
from src.entity.models import User, Role
from src.repository import users as repositories_users
from src.schemas.user import (
    UserResponse,
    UserUpdate,
    UserPublicResponse,
    UserActiveResponse
)
from src.services.auth import auth_service, role_required

router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)


@router.get(
    "/profile/{email}",
    response_model=UserPublicResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def read_user_profile(email: str, db: AsyncSession = Depends(get_db)) -> User:
    """The  read_user_profile function displays the user profile by email.

    Args:
        email (str): Email for the user in database.
        db (AsyncSession, optional): Pass the database session to the function.

    Returns:
        User: User.
    """
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def get_current_user(
    user: User = Depends(auth_service.get_current_active_user),
) -> User:
    """The get_current_user function is a dependency that will be injected into the
        get_current_user endpoint. It uses the auth_service to retrieve the current user,
        and returns it if found.

    Args:
        user (User, optional): Get the current user.

    Returns:
        User: Current user.
    """
    return user


@router.put(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> User:
    """The update_current_user function is a dependency that will be injected into the
        update_current_user endpoint. It uses the auth_service to update the current user information,
        and returns it if found.

    Args:
        user_update (UserUpdate): Validate the data for user's info updating
        db (AsyncSession, optional): Pass the database session to the function.
        current_user (User, optional): Get the current user from the database.

    Returns:
        User: Updated user.
    """
    current_user = await db.merge(current_user)
    user = await repositories_users.update_user(current_user, user_update, db)
    return user


@router.put("/ban/{email}",
            response_model=UserActiveResponse,
            dependencies=[Depends(role_required(["admin"]))]
)
async def bun_user(
    email: str,
    db: AsyncSession = Depends(get_db)):
    """The bun_user function sets the False active status for user by given email, depends on user's role, 'admin' required.

    Args:
        email (str): Email of the user to ban.
        db (AsyncSession, optional): Pass the database session to the function.

    Returns:
        User: User with False active status.
    """
    try:
        user = await repositories_users.set_user_status(email, False, db)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/unban/{email}",
            response_model=UserActiveResponse,
            dependencies=[Depends(role_required(["admin"]))]
)
async def unbun_user(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    """The unbun_user function sets the True active status for user by given email, depends on user's role, 'admin' required. 

    Args:
        email (str): Email of the user to unban.
        db (AsyncSession, optional): Pass the database session to the function.

    Returns:
        User: User with True active status.
    """
    try:
        user = await repositories_users.set_user_status(email, True, db)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def avatar_user(
    file: UploadFile = File(),
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The avatar_user function is used to upload a user's avatar image.
        The function takes in an UploadFile object, which contains the file that was uploaded by the user.
        It also takes in a User object, which is obtained from the auth_service module and represents the current logged-in user.
        Finally, it also accepts an AsyncSession object for interacting with our database.

    Args:
        file (UploadFile, optional): Get the file from the request.
        user (User, optional): Get the current user from the database.
        db (AsyncSession, optional): Pass the database session to the function.

    Returns:
        User: An object of type user
    """
    public_id = f"restapp/{user.email}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, owerite=True)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = await repositories_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user


@router.put("/role/{email}", response_model=UserResponse, dependencies=[Depends(role_required("admin"))])
async def set_role(
    email: str,
    update_role: Role,
    db: AsyncSession = Depends(get_db)
):
    """The set_role function updates the user's role in database.

    Args:
        email (str): Email of the user to setting role.
        update_role (Role): Role to update for user.
        db (AsyncSession, optional): Pass the database session to the function

    Returns:
        User: User with role updated.
    """
    user = await repositories_users.update_user_role(email, update_role, db)
    return user
