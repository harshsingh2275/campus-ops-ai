"""
user.py — User ORM Model
========================

Defines the ``users`` table that persists local authentication credentials.

Columns
-------
id              : Integer primary key, auto-incremented.
email           : Unique, non-nullable email address (used as login identity).
name            : Human-readable display name.
hashed_password : Bcrypt hash of the user's password — the plaintext is
                  *never* stored.  Hashing is handled in the auth service
                  layer (not here).
is_active       : Boolean flag to soft-disable accounts without deletion.
created_at      : UTC timestamp set automatically at insertion time.
updated_at      : UTC timestamp updated automatically on every row mutation.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import validates

from app.database import Base


class User(Base):
    """SQLAlchemy ORM model for the ``users`` table."""

    __tablename__ = "users"

    # ── Primary Key ────────────────────────────────────────────────────────
    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Identity Fields ────────────────────────────────────────────────────
    email: str = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address used as the login credential.",
    )
    name: str = Column(
        String(255),
        nullable=False,
        doc="Full display name of the user.",
    )

    # ── Authentication ─────────────────────────────────────────────────────
    hashed_password: str = Column(
        String(255),
        nullable=False,
        doc="Bcrypt hash of the user's password. Never store plaintext here.",
    )

    # ── Account State ──────────────────────────────────────────────────────
    is_active: bool = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="When False the account is disabled and cannot log in.",
    )

    # ── Audit Timestamps ───────────────────────────────────────────────────
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC datetime when the record was first inserted.",
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC datetime of the most recent update to this record.",
    )

    # ── Validation ─────────────────────────────────────────────────────────
    @validates("email")
    def normalise_email(self, key: str, value: str) -> str:
        """Strip whitespace and force lowercase on assignment."""
        if value is None:
            return value
        return value.strip().lower()

    # ── Repr ───────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<User id={self.id!r} email={self.email!r} "
            f"name={self.name!r} is_active={self.is_active!r}>"
        )
