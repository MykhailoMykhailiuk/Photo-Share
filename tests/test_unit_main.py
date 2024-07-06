import unittest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app
from fastapi import status


class TestApp(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)

    async def asyncSetUp(self):
        self.client = AsyncClient(app=app, base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_banned_ip(self):
        response = await self.client.get(
            "/", headers={"X-Forwarded-For": "192.168.1.1"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = await self.client.get(
            "/", headers={"X-Forwarded-For": "192.168.1.3"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    async def test_index(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Designed for engineers", response.content)

    async def test_healthchecker(self):
        response = await self.client.get("/api/healthchecker")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"message": "Welcome to FastAPI!"})


if __name__ == "__main__":
    unittest.main()
