import pickle
from datetime import datetime, timedelta
from typing import Optional

import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.conf.config import config
from src.database.db import get_db
from src.entity.models import User
from src.repository import users as repository_users
from src.repository.images import get_image


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """The verify_password function takes a plain-text password and a hashed password,
            and returns True if the passwords match, False otherwise.

        Args:
            plain_password (str): Pass in the password that is being verified.
            hashed_password (str): Pass in the hashed password from the database.

        Returns:
            bool: A boolean value.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """The get_password_hash function takes a password as input and returns the hash of that password.
            The function uses the pwd_context object to generate a hash from the given password.

        Args:
            password (str): Create a password hash.

        Returns:
            str: A hash of the password.
        """
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    async def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """The create_access_token function creates a new access token.

        Args:
            data (dict): Pass the data that you want to encode in your token.
            expires_delta (Optional[timedelta], optional): Set the expiration time of the token.

        Returns:
            str: Encoded access token.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta if expires_delta else timedelta(minutes=120)
        )
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ):
        """The get_current_user function is a dependency that will be used in the
            protected endpoints. It uses the OAuth2 token to retrieve and validate
            the user, and assign them to `current_user`.

        Args:
            token (str, optional):  Pass the token to the function.
            db (AsyncSession, optional): Get the database connection.

        Returns:
            _type_: _description_
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") == "access_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user_hash = str(email)

        user = self.cache.get(user_hash)

        if user is None:
            print("User from database")
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, 300)
        else:
            print("User from cache")
            user = pickle.loads(user)
        return user

    async def get_current_active_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ):
        """The get_current_active_user function returns the current active user based on the access token.

        Args:
            token (str, optional): Pass the token to the function.
            db (AsyncSession, optional): Get the database connection.

        Returns:
            User: A user object.
        """
        user = await self.get_current_user(token, db)
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are not active user",
            )
        return user

    async def get_current_active_user_with_role(
        self,
        required_role: list,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ):
        """The get_current_active_user_with_role function returns the current
            active user based on the access token and check their role.

        Args:
            required_role (list): List of strings with role values.
            token (str, optional): Pass the token to the function.
            db (AsyncSession, optional): Get the database connection.

        Returns:
            User: A user object.
        """
        user = await self.get_current_active_user(token, db)
        if user.role.name not in required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=messages.NOT_ENOUGH_PERMISSIONS,
            )
        return user

    def create_email_token(self, data: dict):
        """The create_email_token function takes a dictionary of data and returns a JWT token.
            The token is encoded with the SECRET_KEY and ALGORITHM defined in the class.
            The expiration date is set to 1 day from now.

        Args:
            data (dict): Pass in the email address of the user.

        Returns:
            Str: Created token.
        """
        to_encode = data.copy()
        expire = datetime.now() + timedelta(days=1)
        to_encode.update({"iat": datetime.now(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        The function uses the jwt library to decode the token, which is then used to retrieve the email address from within it.

        Args:
            token (str): Pass in the token that is sent to the user's email.

        Returns:
            str: email
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )

    def generate_password_reset_token(self, email: str) -> str:
        """The generate_password_reset_token function generates a JWT token that expires in 1 hour.
        The payload contains the email of the user who requested to reset their password.

        Args:
            email (str): Specify the email of the user who is requesting a password reset.

        Returns:
            str: A jwt token
        """
        expire = datetime.now() + timedelta(hours=1)
        payload = {"exp": expire, "email": email}
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """The verify_password_reset_token function takes a token as an argument and returns the email address associated with that token.
        If the token is invalid, it raises an HTTPException.

        Args:
            token (str): Pass the token to the function.

        Raises:
            HTTPException: _description_

        Returns:
            Optional[str]: The email of the user who requested a password reset.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload["email"]
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )


auth_service = Auth()


def role_required(required_role: list):
    async def wrapper(
        token: str = Depends(auth_service.oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ):
        user = await auth_service.get_current_active_user_with_role(
            required_role, token, db
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=messages.NOT_ENOUGH_PERMISSIONS,
            )
        return user

    return wrapper


def image_owner_or_admin():
    async def wrapper(
        image_id: int,
        current_user: User = Depends(auth_service.get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ):
        image = await get_image(image_id, db, current_user)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
            )

        if current_user.id != image.user_id and current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        return current_user

    return wrapper
