"""
dependencies/auth.py — JWT Authentication Dependency
=====================================================

Provides ``get_current_user`` — a FastAPI dependency that:

1. Extracts the Bearer token from the ``Authorization`` header using
   ``OAuth2PasswordBearer`` (standard FastAPI pattern).
2. Decodes and verifies the JWT via ``auth_service.decode_access_token``.
3. Fetches the matching ``User`` row from the database.
4. Raises ``401 Unauthorized`` for any invalid/expired token or missing user.
5. Raises ``403 Forbidden`` if the account is disabled.

Usage in a route::

    @router.post("/api/submit")
    async def submit(
        payload: StudentRequestInput,
        current_user: User = Depends(get_current_user),
    ):
        ...
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token

logger = logging.getLogger("campus_ops.auth_dep")

# ---------------------------------------------------------------------------
# OAuth2PasswordBearer
# ---------------------------------------------------------------------------
# Points to the login endpoint that issues tokens.  FastAPI uses this to
# render the "Authorize" button in /docs and to extract the Bearer token from
# the ``Authorization: Bearer <token>`` header on every protected request.
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Verify the JWT and return the authenticated ``User`` ORM object.

    Raises
    ------
    401 Unauthorized
        If the token is missing, expired, malformed, or the user no longer
        exists in the database.
    403 Forbidden
        If the user account is marked ``is_active=False``.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Decode JWT ─────────────────────────────────────────────────────────
    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception

    # ── Fetch user from DB ─────────────────────────────────────────────────
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # ── Active check ───────────────────────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    logger.debug("Authenticated user id=%s email=%s", user.id, user.email)
    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that decodes the JWT and verifies the user has the 'admin' role.

    Raises
    ------
    403 Forbidden
        If the authenticated user does not have the 'admin' role.
    """
    if current_user.role != "admin":
        logger.warning(
            "Forbidden admin access attempt by user id=%s (%s) with role '%s'",
            current_user.id,
            current_user.email,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource.",
        )
    return current_user
