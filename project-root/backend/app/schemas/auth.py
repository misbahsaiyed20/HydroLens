import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.enums import UserRole


class SignupRequest(BaseModel):
    """
    Public signup input. Deliberately has NO `role` field — role is never
    client-supplied; every account created here is CITIZEN (see
    auth_service.create_user). A REVIEWER can only be created through the
    controlled bootstrap script.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserOut(BaseModel):
    """Never includes password_hash — only fields safe to return to the client."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None = None
    display_name: str | None = None
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
