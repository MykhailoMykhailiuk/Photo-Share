from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import config
from src.services.auth import auth_service

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="PhotoShare_01",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str) -> None:
    """The send_email function sends an email to the user with a link to verify their email address.
        
    Args:
        email (EmailStr): Specify the email address of the user.
        username (str): Pass the username of the user to be sent in the email.
        host (str): Pass the hostname of your server to the email template

    Returns:
        None: None, so the return value of send_email is none
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_reset_password_email(email: str, token: str, host: str):
    """The send_reset_password_email function sends a password reset email to the user.

    Args:
        email (str): The user's email address.
        token (str): A unique token that will be used to verify the request is valid.
        host (str): The URL of your website, e.g., https://example.com/reset-password?token=abc123xyz789
    
    Returns:
        None: None.
    """
    try:
        message = MessageSchema(
            subject="Password reset request",
            recipients=[email],
            template_body={
                "host": host,
                "token": token,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as err:
        print(err)
