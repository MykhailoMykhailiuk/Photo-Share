import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Image, User
from src.repository.images import (
    delete_image,
    get_all_images,
    get_foravatar_url,
    get_image,
    get_transformed_url,
    save_transformed_image,
    update_image,
    upload_image,
)
from src.schemas.image import ImageUpdateSchema


class TestImageRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="123456",
            confirmed=True,
            avatar="example.com/avatar.png",
            role=1,
            image_count=0,
        )
        self.image = Image(
            id=1,
            description="Test Image",
            url="http://example.com/image.jpg",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user.id,
        )

    @patch("cloudinary.uploader.upload")
    async def test_upload_image(self, mock_upload):
        mock_upload.return_value = {"url": "http://example.com/image.jpg"}
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test_image.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"file_content"
        image = await upload_image(
            file=mock_file, description="Test Image", db=self.session, user=self.user
        )
        self.assertEqual(image.url, "http://example.com/image.jpg")
        self.assertEqual(image.description, "Test Image")
        self.assertEqual(image.user_id, self.user.id)

    async def test_update_image(self):
        body = ImageUpdateSchema(description="New Description")
        image = Image(
            id=1,
            description="Old Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user.id,
        )

        mocked_image_result = MagicMock()
        mocked_image_result.unique.return_value.scalar_one_or_none.return_value = image
        self.session.execute.return_value = mocked_image_result

        updated_image = await update_image(image_id=1, body=body, db=self.session)

        self.assertEqual(updated_image.description, "New Description")
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_with(updated_image)

    async def test_get_all_images(self):
        limit = 10
        offset = 0
        images = [
            Image(
                id=i,
                description=f"Image {i}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(5)
        ]
        mocked_images = MagicMock()
        mocked_images.unique.return_value.scalars.return_value.all.return_value = images
        self.session.execute.return_value = mocked_images
        result = await get_all_images(limit, offset, self.session)
        self.assertEqual(result, images)
        self.assertEqual(len(result), len(images))

    async def test_get_image(self):
        image = Image(
            id=1,
            description="Test Image",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user.id,
        )

        mocked_image = MagicMock()
        mocked_image.unique.return_value.scalar_one_or_none.return_value = image
        self.session.execute.return_value = mocked_image
        result = await get_image(1, self.session, self.user)
        self.assertEqual(result, image)

    @patch("cloudinary.uploader.destroy")
    async def test_delete_image(self, mock_destroy):
        mocked_image_result = MagicMock()
        mocked_image_result.scalar_one_or_none.return_value = self.image
        mocked_user_result = MagicMock()
        mocked_user_result.scalar_one_or_none.return_value = self.user
        self.session.execute.side_effect = [mocked_image_result, mocked_user_result]
        mock_destroy.return_value = {"result": "ok"}

        deleted_image = await delete_image(image_id=1, db=self.session)

        mock_destroy.assert_called_once_with("image")
        self.session.delete.assert_called_once_with(self.image)
        self.session.commit.assert_called_once()
        self.assertEqual(deleted_image, self.image)

    async def test_save_transformed_image(self):
        image_url = "http://example.com/transformed_image.jpg"
        image_description = "Transformed Image"
        saved_image = await save_transformed_image(
            image_url=image_url,
            image_description=image_description,
            user=self.user,
            db=self.session,
        )
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called()
        self.assertEqual(saved_image.url, image_url)
        self.assertEqual(saved_image.description, image_description)
        self.assertEqual(saved_image.user_id, self.user.id)

    @pytest.mark.asyncio
    @patch("cloudinary.CloudinaryImage.build_url")
    async def test_get_transformed_url(self, mock_build_url):
        mock_build_url.return_value = "http://example.com/transformed_image.jpg"

        async def mock_get_image(image_id, db, user):
            mock_image = MagicMock()
            mock_image.url = "http://example.com/image.jpg"
            return mock_image

        with patch("src.repository.images.get_image", side_effect=mock_get_image):
            result = await get_transformed_url(
                image_id=1,
                transformations={"crop": "fill"},
                user=self.user,
                db=self.session,
            )

        expected_url = "http://example.com/transformed_image.jpg"
        assert result == expected_url
        self.session.add.assert_called()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called()

    @pytest.mark.asyncio
    @patch("cloudinary.CloudinaryImage.build_url")
    async def test_get_foravatar_url(self, mock_build_url):
        mock_build_url.return_value = "http://example.com/transformed_image.jpg"

        async def mock_get_image(image_id, db, user):
            mock_image = MagicMock()
            mock_image.url = "http://example.com/image.jpg"
            return mock_image

        with patch("src.repository.images.get_image", side_effect=mock_get_image):
            result = await get_foravatar_url(
                image_id=1,
                transformations={"crop": "fill"},
                user=self.user,
                db=self.session,
            )

        expected_url = "http://example.com/transformed_image.png"
        self.assertEqual(result, expected_url)
        self.session.add.assert_called()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called()


if __name__ == "__main__":
    unittest.main()
