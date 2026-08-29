"""
services/auth_service.py — Authentication Utilities
====================================================

Provides two self-contained responsibilities:

1. **Password hashing / verification** via ``pwdlib`` with the Argon2id
   algorithm (memory-hard, resistant to GPU brute-force attacks).

2. **JWT generation / decoding** via ``PyJWT`` (HS256 by default).

Neither responsibility depends on the database layer — keeping this module
pure and unit-testable without a running DB.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import settings

logger = logging.getLogger("campus_ops.auth_service")

# ---------------------------------------------------------------------------
# Password Hashing — Argon2id via pwdlib
# ---------------------------------------------------------------------------
# Argon2id is the winner of the Password Hashing Competition and is the
# recommended algorithm for new projects.  pwdlib wraps argon2-cffi so the
# heavy computation happens in C, not Python.
# ---------------------------------------------------------------------------
_pwd_hash = PasswordHash((Argon2Hasher(),))


def hash_password(plaintext: str) -> str:
    """Return an Argon2id hash of *plaintext*.

    The hash includes the salt and all parameters inline, so it is safe to
    store directly in the ``hashed_password`` column.
    """
    return _pwd_hash.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return ``True`` if *plaintext* matches the stored *hashed* value.

    Uses constant-time comparison internally to prevent timing attacks.
    """
    try:
        return _pwd_hash.verify(plaintext, hashed)
    except Exception:
        # Any exception from the hasher (malformed hash, etc.) is a mismatch.
        return False


# ---------------------------------------------------------------------------
# JWT — Generation and Decoding
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str | int,
    extra_claims: Optional[dict] = None,
) -> tuple[str, int]:
    """Encode and sign a JWT access token.

    Parameters
    ----------
    subject:
        The ``sub`` claim — conventionally the user's ``id`` cast to string,
        but any hashable identifier works.
    extra_claims:
        Optional dict of additional claims to merge into the payload
        (e.g. ``{"email": "...", "name": "..."}``) for convenience on the
        frontend so it avoids an extra /me round-trip.

    Returns
    -------
    (token_string, expires_in_seconds)
        The signed JWT and its remaining lifetime in seconds.
    """
    expire_seconds = settings.JWT_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    expire = now + timedelta(seconds=expire_seconds)

    payload: dict = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, expire_seconds


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT, returning its payload dict.

    Raises
    ------
    jwt.ExpiredSignatureError
        If the token has passed its ``exp`` claim.
    jwt.InvalidTokenError
        For any other verification failure (bad signature, malformed, etc.).
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]
