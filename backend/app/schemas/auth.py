"""
schemas/auth.py — Pydantic Schemas for Authentication
======================================================

These are *request/response* shapes only — they are intentionally separate
from the SQLAlchemy ORM model (``models/user.py``) so that we never
accidentally expose the ``hashed_password`` field in API responses.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Payload expected by ``POST /auth/register``."""

    email: EmailStr = Field(..., description="User's email address (used as login identity).")
    name: str = Field(..., min_length=1, max_length=255, description="Full display name.")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password (min 8 chars). Hashed server-side before storage.",
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    """Payload expected by ``POST /auth/login``."""

    email: EmailStr = Field(..., description="Registered email address.")
    password: str = Field(..., description="Plaintext password to verify.")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class UserPublic(BaseModel):
    """Safe public representation of a user — no password fields included."""

    id: int
    email: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Returned by ``POST /auth/login`` on success."""

    access_token: str = Field(..., description="Signed JWT access token.")
    token_type: str = Field(default="bearer", description="Always 'bearer'.")
    expires_in: int = Field(..., description="Token lifetime in seconds.")
    user: UserPublic = Field(..., description="Public user data for the authenticated account.")


class RegisterResponse(BaseModel):
    """Returned by ``POST /auth/register`` on success."""

    message: str = "Account created successfully."
    user: UserPublic
