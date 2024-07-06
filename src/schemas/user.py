from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.entity.models import Role


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None


class UserPublicResponse(BaseModel):
    username: str
    email: EmailStr
    avatar: str
    created_at: datetime
    image_count: int


class UserActiveResponse(BaseModel):
    email: EmailStr
    is_active: bool


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime
    image_count: int

    model_config = ConfigDict(from_attributes=True)


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr
    # new_password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str
