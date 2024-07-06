import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Image, Tag, User
from src.repository.tags import (
    add_tags_for_image,
    create_tags,
    get_tag,
    get_tags,
    remove_tag,
    update_tag,
)
from src.schemas.tag import TagSchema, TagUpdateSchema


class TestTagRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.tags = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3")]

    @patch("src.repository.tags.get_tag")
    async def test_create_tags(self, mock_get_tag):
        body = TagSchema(tag_list=["new_tag1", "existing_tag1", "new_tag2"])
        existing_tags = [Tag(name="existing_tag1"), Tag(name="existing_tag2")]
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = existing_tags
        self.session.execute.return_value = execute_result
        mock_get_tag.side_effect = lambda name, db: Tag(name=name)

        result = await create_tags(body, self.session)

        self.session.execute.assert_called_once()
        self.assertEqual(self.session.add.call_count, 2)
        self.session.commit.assert_called_once()
        self.assertEqual(self.session.refresh.call_count, 2)
        result_tag_names = [tag.name for tag in result]
        self.assertSetEqual(set(result_tag_names), set(body.tag_list))

    async def test_get_tags(self):
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = self.tags
        self.session.execute.return_value = execute_result
        skip = 0
        limit = 3

        result = await get_tags(skip, limit, self.session)

        self.session.execute.assert_called_once()
        self.assertEqual(result, self.tags)

    async def test_get_tag(self):
        tag = Tag(name="existing_tag")
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = tag
        self.session.execute.return_value = execute_result

        tag_name = "existing_tag"
        result = await get_tag(tag_name, self.session)

        self.session.execute.assert_called_once()
        self.assertEqual(result, tag)

    async def test_update_tag_success(self):
        tag = Tag(id=1, name="existing_tag")
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = tag
        self.session.execute.return_value = execute_result

        body = TagUpdateSchema(name="updated_tag")

        tag_id = 1
        result = await update_tag(tag_id, body, self.session)

        self.session.execute.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(tag)

        self.assertEqual(result.name, "updated_tag")
        self.assertEqual(result.id, 1)

    async def test_update_tag_not_found(self):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = execute_result

        body = TagUpdateSchema(name="updated_tag")

        tag_id = 1
        result = await update_tag(tag_id, body, self.session)

        self.session.execute.assert_called_once()
        self.session.commit.assert_not_called()
        self.session.refresh.assert_not_called()

        self.assertIsNone(result)

    async def test_remove_tag_success(self):
        tag = Tag(id=1, name="test_tag")
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = tag
        self.session.execute.return_value = execute_result

        tag_id = 1
        result = await remove_tag(tag_id, self.session)

        self.session.execute.assert_called_once()
        self.session.delete.assert_called_once_with(tag)
        self.session.commit.assert_called_once()

        self.assertEqual(result, tag)

    async def test_remove_tag_not_found(self):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = execute_result

        tag_id = 1
        result = await remove_tag(tag_id, self.session)

        self.session.execute.assert_called_once()
        self.session.delete.assert_not_called()
        self.session.commit.assert_not_called()

        self.assertIsNone(result)


class TestRepositoryTagForImage(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock()
        self.image_id = 1
        self.tag_schema = TagSchema(tag_list=["tag1", "tag2", "tag3"])
        self.user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="123456",
            confirmed=True,
            avatar="example.com/avatar.png",
            is_active=True,
        )

    async def test_add_tags_for_image_success(self):
        # Mocking the db.execute call to return an existing image
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = Image(
            id=self.image_id, user_id=self.user.id
        )
        self.session.execute.return_value = execute_result

        # Mocking the create_tags function
        mock_created_tags = [Tag(id=1, name="tag1"), Tag(id=2, name="tag2")]
        create_tags_mock = AsyncMock(return_value=mock_created_tags)

        # Calling the function
        with unittest.mock.patch("src.repository.tags.create_tags", create_tags_mock):
            result = await add_tags_for_image(
                self.tag_schema, self.image_id, self.user, self.session
            )

        # Asserting database operations
        create_tags_mock.assert_called_once_with(self.tag_schema, self.session)
        self.session.commit.assert_called_once()

        # Asserting the result
        self.assertEqual(result, mock_created_tags)

    async def test_add_tags_for_image_image_not_found(self):
        # Mocking the db.execute call to return None (image not found)
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = execute_result

        # Calling the function
        result = await add_tags_for_image(
            self.tag_schema, self.image_id, self.user, self.session
        )

        # Asserting database operations
        self.session.execute.assert_called_once()

        # Asserting the result
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
