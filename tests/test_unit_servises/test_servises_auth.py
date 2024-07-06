import unittest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.entity.models import Role, User
from src.services.auth import Auth


class TestAuth(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.auth = Auth()
        self.valid_token = "valid_token"
        self.invalid_token = "invalid_token"
        self.user_email = "test_user@example.com"
        self.user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="123456",
            role=Role.admin,
            access_token="valid_token",
            confirmed=True,
            is_active=True,
            image_count=0,
            avatar="example.com/avatar.png",
        )

    async def mock_get_current_user(self, token: str, db: AsyncSession):
        if token == self.valid_token:
            return self.user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    @patch.object(Auth, "get_current_user", new_callable=AsyncMock)
    async def test_get_current_active_user_success(self, mock_get_current_user):
        mock_get_current_user.side_effect = self.mock_get_current_user
        result = await self.auth.get_current_active_user(
            token=self.valid_token, db=self.session
        )
        self.assertEqual(result, self.user)

    @patch.object(Auth, "get_current_user", new_callable=AsyncMock)
    async def test_get_current_active_user_inactive_user(self, mock_get_current_user):
        async def mock_get_current_user_inactive(token, db):
            if token == self.valid_token:
                return User(
                    id=1, email=self.user_email, role=Role.admin, is_active=False
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )

        mock_get_current_user.side_effect = mock_get_current_user_inactive

        with self.assertRaises(HTTPException) as context:
            await self.auth.get_current_active_user(
                token=self.valid_token, db=self.session
            )
        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(context.exception.detail, "You are not active user")

    @patch.object(Auth, "get_current_user", new_callable=AsyncMock)
    async def test_get_current_active_user_insufficient_permissions(
        self, mock_get_current_user
    ):
        async def mock_get_current_user_insufficient_permissions(token, db):
            if token == self.valid_token:
                return User(id=1, email=self.user_email, role=Role.user)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )

        mock_get_current_user.side_effect = (
            mock_get_current_user_insufficient_permissions
        )

        with self.assertRaises(HTTPException) as context:
            await self.auth.get_current_active_user_with_role(
                required_role=["admin"], token=self.valid_token, db=self.session
            )
        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(context.exception.detail, messages.NOT_ACTIVE_USER)

    async def test_create_access_token(self):
        data = {"sub": self.user_email}
        expires_delta = timedelta(minutes=30)
        token = await self.auth.create_access_token(data, expires_delta)
        decoded_token = jwt.decode(
            token, self.auth.SECRET_KEY, algorithms=[self.auth.ALGORITHM]
        )
        self.assertEqual(decoded_token["scope"], "access_token")

    def test_generate_password_reset_token(self):
        email = "test_user@example.com"
        token = self.auth.generate_password_reset_token(email)
        decoded_token = jwt.decode(
            token, self.auth.SECRET_KEY, algorithms=[self.auth.ALGORITHM]
        )
        self.assertEqual(decoded_token["email"], email)

    def test_verify_password_reset_token_success(self):
        email = "test_user@example.com"
        token = self.auth.generate_password_reset_token(email)
        result = self.auth.verify_password_reset_token(token)
        self.assertEqual(result, email)

    def test_verify_password_reset_token_invalid_token(self):
        invalid_token = "invalid_token"
        with self.assertRaises(HTTPException) as context:
            self.auth.verify_password_reset_token(invalid_token)
        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(context.exception.detail, "Could not validate credentials")


if __name__ == "__main__":
    unittest.main()
