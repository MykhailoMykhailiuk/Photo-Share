import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.entity.models import Role, User
from src.repository.users import (
    confirmed_email,
    create_user,
    get_user_by_email,
    get_user_by_username,
    set_user_status,
    update_avatar_url,
    update_password,
    update_token,
    update_user,
    update_user_role,
)
from src.schemas.user import UserSchema, UserUpdate


class TestAsyncUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.username = "test_user"
        self.user = User(
            id=1,
            username=self.username,
            email="test_user@example.com",
            password="123456",
            role=1,
            access_token="test_access_token",
            confirmed=True,
            is_active=False,
            image_count=0,
            avatar="example.com/avatar.png",
        )

    async def test_get_user_by_email(self):
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user
        result = await get_user_by_email("test_email_1@example.com", self.session)
        self.assertEqual(result, self.user)

    async def test_get_user_by_username_found(self):
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user
        result = await get_user_by_username(self.username, self.session)
        self.assertEqual(result, self.user)

    async def test_get_user_by_username_not_found(self):
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_user
        result = await get_user_by_username("unknown_user", self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="123456",
            confirmed=False,
        )
        body = UserSchema(
            username="test_user", email="test_user@example.com", password="123456"
        )
        result = await create_user(body, self.session)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertEqual(result.username, user.username)
        self.assertEqual(result.email, user.email)
        self.assertEqual(result.password, user.password)

    async def test_confirmed_email(self):
        email = "test_user@example.com"
        user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="123456",
            confirmed=False,
        )

        with unittest.mock.patch(
            "src.repository.users.get_user_by_email", return_value=user
        ):
            await confirmed_email(email, self.session)

            self.assertTrue(user.confirmed)
            self.session.commit.assert_called_once()

    async def test_update_avatar_url(self):
        email = "test_user@example.com"
        avatar_url = "example.com/avatar.png"
        user = User(
            id=1,
            username="test_user",
            email=email,
            password="123456",
            confirmed=False,
            avatar=None,
        )

        with unittest.mock.patch(
            "src.repository.users.get_user_by_email", return_value=user
        ):
            result = await update_avatar_url(email, avatar_url, self.session)
            self.assertEqual(result.avatar, avatar_url)
            self.session.commit.assert_called_once()
            self.session.refresh.assert_called_once_with(user)

    async def test_update_password(self):
        user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="old_password",
            confirmed=False,
        )
        new_password = "new_password"

        result = await update_password(user, new_password, self.session)
        self.assertEqual(result.password, new_password)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(user)

    async def test_update_user(self):
        user_update = UserUpdate(username="new_username", email="new_email@example.com")

        updated_user = await update_user(
            user=self.user, user_update=user_update, db=self.session
        )

        self.assertEqual(updated_user.username, "new_username")
        self.assertEqual(updated_user.email, "new_email@example.com")
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(updated_user)

    async def test_update_user_partial(self):
        user_update = UserUpdate(username=None, email="new_email@example.com")

        updated_user = await update_user(
            user=self.user, user_update=user_update, db=self.session
        )

        self.assertEqual(updated_user.username, self.username)
        self.assertEqual(updated_user.email, "new_email@example.com")
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(updated_user)

    @patch("src.repository.users.get_user_by_email")
    async def test_set_user_status_found(self, mock_get_user_by_email):
        mock_get_user_by_email.return_value = self.user

        updated_user = await set_user_status(
            email=self.user.email, set_status=True, db=self.session
        )

        self.assertTrue(updated_user.is_active)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(updated_user)

    @patch("src.repository.users.get_user_by_email")
    async def test_set_user_status_not_found(self, mock_get_user_by_email):
        mock_get_user_by_email.return_value = None

        with self.assertRaises(HTTPException) as context:
            await set_user_status(
                email="unknown@example.com", set_status=True, db=self.session
            )

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, messages.USER_NOT_FOUND)
        self.session.commit.assert_not_called()
        self.session.refresh.assert_not_called()

    @patch("src.repository.users.get_user_by_email")
    async def test_update_user_role_found(self, mock_get_user_by_email):
        mock_get_user_by_email.return_value = self.user

        new_role = Role.admin

        updated_user = await update_user_role(
            email=self.user.email, update_role=new_role, db=self.session
        )

        self.assertEqual(updated_user.role, new_role)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(updated_user)

    @patch("src.repository.users.get_user_by_email")
    async def test_update_user_role_not_found(self, mock_get_user_by_email):
        mock_get_user_by_email.return_value = None

        with self.assertRaises(HTTPException) as context:
            await update_user_role(
                email="unknown@example.com", update_role=Role.admin, db=self.session
            )

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, messages.USER_NOT_FOUND)
        self.session.commit.assert_not_called()
        self.session.refresh.assert_not_called()

    async def test_update_token(self):
        token = "test_token"
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user
        await update_token(self.user, token, self.session)
        self.session.commit.assert_called_once()
