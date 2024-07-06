from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.db import get_db
from src.entity.models import Role, User
from src.schemas.user import UserSchema, UserUpdate


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """The get_user_by_email function returns a user object from the database based on the email address provided.
        If no user is found, None is returned.

    Args:
        email (str): Get the email from the user.
        db (AsyncSession, optional): Pass in the database session.

    Returns:
        User: User or None.
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def get_user_by_username(username: str, db: AsyncSession = Depends(get_db)):
    """The get_user_by_email function returns a user object from the database based on the username provided.
        If no user is found, None is returned.

    Args:
        username (str): Get the username from the user
        db (AsyncSession, optional): Pass in the database session

    Returns:
        User: User or None.
    """
    stmt = select(User).filter_by(username=username)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """The create_user function creates a new user in the database.

    Args:
        body (UserSchema): Validate the request body.
        db (AsyncSession, optional): Pass in the database session.

    Returns:
        User: Created user.
    """
    new_user = User(**body.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """The confirmed_email function marks a user as confirmed in the database.

    Args:
        email (str): Specify the email address of the user to confirm.
        db (AsyncSession): Pass the database session to the function

    Returns:
        None: None.
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """The update_avatar_url function updates the avatar url of a user.

    Args:
        email (str): Find the user in the database.
        url (str | None): Specify that the url parameter can be either a string or none.
        db (AsyncSession): Pass the database session to the function.

    Returns:
        User: A user object
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(
    user: User, new_password: str, db: AsyncSession = Depends(get_db)
) -> None:
    """The update_password function updates the password of a user.

    Args:
        user (User): Pass in the user object that is being updated.
        new_password (str): Pass in the new password for the user.
        db (AsyncSession, optional): Pass in the database session to the function.

    Returns:
        USer: User with updated password.
    """
    user.password = new_password
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    user: User, user_update: UserUpdate, db: AsyncSession = Depends(get_db)
) -> None:
    """The update_user function updates the user's information.

    Args:
        user (User): Pass in the user object that is being updated.
        user_update (UserUpdate): Pass in the new data for the user.
        db (AsyncSession, optional): Pass in the database session to the function.

    Returns:
        User: Updated user.
    """
    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email
    await db.commit()
    await db.refresh(user)
    return user


async def set_user_status(
    email: str, set_status: bool, db: AsyncSession = Depends(get_db)
) -> None:
    """The set_user_status function updates the user's active status.

    Args:
        email (str): User's email to status updating.
        set_status (bool): Bolean value to setting user's status.
        db (AsyncSession, optional): Pass in the database session to the function

    Returns:
        User: User with updated status.
    """
    user = await get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )
    user.is_active = set_status
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_role(
    email: str, update_role: Role, db: AsyncSession = Depends(get_db)
) -> None:
    """The update_user_role function updates the user's role.

    Args:
        email (str): User's email to role updating.
        update_role (Role): Value to user's role updating.
        db (AsyncSession, optional): Pass in the database session to the function.

    Returns:
        User: User with updated role.
    """
    user = await get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )
    if update_role:
        user.role = update_role
    await db.commit()
    await db.refresh(user)
    return user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """The update_token function updates the user's token in database.

    Args:
        user (User): Current user.
        token (str | None): Current user's token.
        db (AsyncSession): Pass in the database session to the function.
    """
    user.access_token = token
    await db.commit()
