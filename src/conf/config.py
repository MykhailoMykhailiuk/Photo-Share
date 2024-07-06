from dotenv import load_dotenv
from pydantic import ConfigDict, EmailStr, Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = Field(env="SQLALCHEMY_DATABASE_URL")
    SECRET_KEY_JWT: str = "1234567890"
    ALGORITHM: str = "HS256"
    MAIL_USERNAME: EmailStr = "postgres@meail.com"
    MAIL_PASSWORD: str = "postgres"
    MAIL_FROM: str = "postgres"
    MAIL_PORT: int = 567234
    MAIL_SERVER: str = "postgres"
    REDIS_DOMAIN: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = ConfigDict(
        extra="ignore", env_file="../.env", env_file_encoding="utf-8"
    )


config = Settings()
