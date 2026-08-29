"""
routes/auth.py — Authentication Endpoints
==========================================

Exposes two public endpoints under the ``/auth`` prefix:

``POST /auth/register``
    Accepts an email, name, and password.  Checks for duplicate emails,
    hashes the password with Argon2id, persists the new user, and returns
    the public user data.

``POST /auth/login``
    Validates credentials against the DB.  On success, issues a signed JWT
    access token and returns it alongside the public user profile.

No route here requires authentication — that will come later when
``get_current_user`` is wired to protected endpoints via ``Depends``.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserPublic,
)
from ..services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger("campus_ops.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Creates a new local user account. "
        "Returns 409 if the email is already registered."
    ),
)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    """Register a new user.

    - Rejects duplicate emails with ``409 Conflict``.
    - Hashes the password with Argon2id before storage.
    - Returns the created user's public profile (no password fields).
    """
    # ── Duplicate check ────────────────────────────────────────────────────
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{body.email}' already exists.",
        )

    # ── Create and persist user ────────────────────────────────────────────
    user = User(
        email=body.email,          # normalised to lowercase by ORM validator
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: id=%s email=%s", user.id, user.email)

    return RegisterResponse(
        message="Account created successfully.",
        user=UserPublic.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
    description=(
        "Validates email/password credentials. "
        "Returns a signed JWT access token on success. "
        "Returns 401 for any invalid credential combination (intentionally vague)."
    ),
)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and issue a JWT.

    Uses a generic 401 error for both 'user not found' and 'wrong password'
    to avoid leaking which emails are registered (user-enumeration hardening).
    """
    _INVALID = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Look up user ───────────────────────────────────────────────────────
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise _INVALID

    # ── Verify password ────────────────────────────────────────────────────
    if not verify_password(body.password, user.hashed_password):
        raise _INVALID

    # ── Check account is active ────────────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # ── Issue JWT ──────────────────────────────────────────────────────────
    token, expires_in = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "name": user.name},
    )

    logger.info("User logged in: id=%s email=%s", user.id, user.email)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserPublic.model_validate(user),
    )
