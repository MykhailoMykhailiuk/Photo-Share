import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Comment, Image, User
from src.repository.comments import (
    create_comment,
    delete_comment,
    get_comment,
    update_comment,
)
from src.schemas.comments import CommentCreate


class TestCommentRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="123456",
            role=1,
            access_token="test_access_token",
            confirmed=True,
            is_active=False,
            image_count=0,
            avatar="example.com/avatar.png",
        )
        self.image = Image(
            id=1,
            url="http://example.com/image.jpg",
            description="Test Image",
            user_id=self.user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.comment = Comment(
            id=1,
            name="Test Comment",
            image_id=self.image.id,
            user_id=self.user.id,
        )

    async def test_get_comment_found(self):
        mocked_comment = MagicMock()
        mocked_comment.scalar_one_or_none.return_value = self.comment
        self.session.execute.return_value = mocked_comment
        result = await get_comment(comment_id=1, db=self.session)
        self.assertEqual(result, self.comment)
        self.assertIsNotNone(result)

    async def test_get_comment_not_found(self):
        mocked_comment = MagicMock()
        mocked_comment.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_comment
        result = await get_comment(comment_id=999, db=self.session)
        self.assertIsNone(result)

    async def test_create_comment(self):
        mock_image = MagicMock()
        mock_image.select.return_value.filter_by.return_value = self.image
        mock_image.execute.return_value = mock_image
        mock_image.scalar_one_or_none.return_value = mock_image

        self.session.execute.return_value = mock_image

        body = CommentCreate(name="New Comment")

        result = await create_comment(
            image_id=1, current_user=self.user, body=body, db=self.session
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.image_id, mock_image.id)
        self.assertEqual(result.user_id, self.user.id)
        self.session.execute.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_update_comment(self):
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.name = "Old Comment"
        self.session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_comment)
        )

        updated_body = CommentCreate(name="Updated Comment")

        updated_comment = await update_comment(
            comment_id=1, coment_update=updated_body, db=self.session
        )

        self.assertIsNotNone(updated_comment)
        self.assertEqual(updated_comment.id, 1)
        self.assertEqual(updated_comment.name, updated_body.name)
        mock_comment.name = updated_body.name
        self.session.execute.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(mock_comment)

    @pytest.mark.asyncio
    async def test_delete_comment(self):
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.name = "Test Comment"
        self.session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_comment)
        )

        deleted_comment = await delete_comment(comment_id=1, db=self.session)

        self.assertIsNotNone(deleted_comment)
        self.assertEqual(deleted_comment.id, 1)
        self.assertEqual(deleted_comment.name, "Test Comment")

        self.session.execute.assert_called_once()
        self.session.delete.assert_called_once_with(mock_comment)
        self.session.commit.assert_called_once()
