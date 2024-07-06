import unittest

from src.repository.qr import (
    generate_qr_code,
    generate_qr_code_with_url,
)


class TestQRCodeGeneration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.url = "https://example.com"

    def test_generate_qr_code_with_url(self):
        response = generate_qr_code_with_url(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")

    def test_generate_qr_code(self):
        response = generate_qr_code(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")


if __name__ == "__main__":
    unittest.main()
