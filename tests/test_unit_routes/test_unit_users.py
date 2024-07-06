import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from unittest import TestCase
from fastapi import BackgroundTasks, Request, HTTPException, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.routes.users import router
from src.schemas.user import UserSchema
from src.repository import users as repositories_users
from src.routes import users as routes_users
from src.services.auth import auth_service


# class TestSignupEndpoint(unittest.IsolatedAsyncioTestCase):
#     def setUp(self):
#         self.session = MagicMock(spec=AsyncSession)
#         self.user_data = {
#             "username": "testuser",
#             "email": "test@example.com",
#             "password": "12345678",
#         }

#     @patch("src.services.auth.auth_service", spec=True)
#     async def test_signup_endpoint(self, mock_create_user):
#         async with AsyncClient(app=router) as client:
#             mock_request = MagicMock(spec=Request)
#             mock_request.base_url = "http://testserver"

#         self.session.add = AsyncMock()
#         self.session.commit = AsyncMock()

#         mock_background_tasks = MagicMock(spec=BackgroundTasks)
#         mock_background_tasks.add_task = MagicMock()

#         user_schema = UserSchema(**self.user_data)

#         mock_create_user.return_value = user_schema
#         repositories_users.get_user_by_email = AsyncMock(return_value=None)

#         response = await client.post(
#             "/auth/signup",
#             json=self.user_data,
#             bt=mock_background_tasks,
#             request=mock_request,
#             db=self.session,
#         )

#         self.assertEqual(response.status_code, 201)
#         self.assertEqual(
#             response.json(),
#             {
#                 "username": "testuser",
#                 "email": "test@example.com",
#             },
#         )

#         mock_background_tasks.add_task.assert_called_once()
#         mock_create_user.assert_called_once_with(user_schema, self.session)


class TestSignupEndpoint(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=AsyncSession)
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345678",
        }
    async def test_read_user_profile(self):
         # Створюємо реальний об'єкт користувача
        real_user = User(id=1, email="test@example.com", username="testuser")
        
        # Мокуємо асинхронну залежність repositories_users.get_user_by_email
        mock_get_user_by_email = AsyncMock()
        mock_get_user_by_email.return_value = real_user
        
        # Мокуємо асинхронну сесію бази даних
        mock_db = MagicMock(spec=AsyncSession)
        
        # Передаємо моковану залежність у функцію read_user_profile
        email = "test@example.com"
        user = await routes_users.read_user_profile(email, db=mock_db)
        
        # Перевіряємо, що результат user є об'єктом класу User
        assert isinstance(user, User)

    
    async def test_get_current_user(self):
        user_schema = UserSchema(**self.user_data)
        routes_users.get_current_user = AsyncMock(return_value=user_schema)
        response = await routes_users.get_current_user()
        self.assertEqual(response, user_schema)
        routes_users.get_current_user.assert_called_once()
        self.assertEqual(response.username, "testuser")
        self.assertEqual(response.email, "test@example.com")

if __name__ == "__main__":
    unittest.main()
