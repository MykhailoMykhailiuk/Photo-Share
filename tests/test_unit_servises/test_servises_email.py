import unittest
from unittest.mock import AsyncMock, patch

from fastapi_mail import MessageType

from src.services.email import send_email, send_reset_password_email


class TestEmailService(unittest.IsolatedAsyncioTestCase):
    @patch("src.services.email.FastMail")
    async def test_send_email_success(self, MockFastMail):
        mock_fm_instance = MockFastMail.return_value
        mock_fm_instance.send_message = AsyncMock()

        email = "test_user@example.com"
        username = "test_user"
        host = "example.com"

        await send_email(email, username, host)

        mock_fm_instance.send_message.assert_called_once()
        args, kwargs = mock_fm_instance.send_message.call_args
        message = args[0]

        self.assertEqual(message.subject, "Confirm your email ")
        self.assertEqual(message.recipients, [email])
        self.assertEqual(message.subtype, MessageType.html)

    @patch("src.services.email.FastMail")
    async def test_send_reset_password_email_success(self, MockFastMail):
        mock_fm_instance = MockFastMail.return_value
        mock_fm_instance.send_message = AsyncMock()

        email = "test_user@example.com"
        token = "random_token"
        host = "example.com"

        await send_reset_password_email(email, token, host)

        mock_fm_instance.send_message.assert_called_once()
        args, kwargs = mock_fm_instance.send_message.call_args
        message = args[0]

        self.assertEqual(message.subject, "Password reset request")
        self.assertEqual(message.recipients, [email])
        self.assertEqual(message.subtype, MessageType.html)


if __name__ == "__main__":
    unittest.main()
