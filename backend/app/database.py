"""
database.py — SQLAlchemy Database Configuration
================================================

Sets up the SQLite connection engine, session factory, and declarative base
that all ORM models inherit from.

Usage
-----
* Import ``Base`` in any model module and subclass it.
* Import ``get_db`` in route handlers to obtain a request-scoped session via
  FastAPI's ``Depends`` mechanism (wired in once routes are built).
* ``create_db_tables()`` is called once at application startup via the
  lifespan hook in ``main.py`` to materialise all mapped tables.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------
# SQLite file stored at  backend/campus_ops.db  (resolved relative to this
# file's location so it works regardless of the working directory).
# ---------------------------------------------------------------------------
import os

_DB_DIR = os.path.dirname(os.path.abspath(__file__))          # …/backend/app
_DB_PATH = os.path.join(_DB_DIR, "..", "campus_ops.db")       # …/backend/campus_ops.db
_DB_PATH = os.path.normpath(_DB_PATH)

DATABASE_URL = f"sqlite:///{_DB_PATH}"

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# ``check_same_thread=False`` is required for SQLite when used with FastAPI
# because requests may be handled across multiple threads.
# ---------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,   # Set to True to log all SQL statements during debugging
)

# ---------------------------------------------------------------------------
# Session Factory
# ---------------------------------------------------------------------------
# ``autocommit=False`` — changes are only persisted when session.commit() is
# called explicitly, giving full transactional control.
# ``autoflush=False``  — prevents implicit flushes before every query, which
# can mask bugs and cause unexpected DB hits.
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
# All ORM models (User, etc.) inherit from this Base so SQLAlchemy can
# discover them for table creation and relationship mapping.
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# Table Initialisation
# ---------------------------------------------------------------------------
def create_db_tables() -> None:
    """Create all tables that have been registered via ``Base.metadata``.

    This is a no-op if the tables already exist, so it is safe to call on
    every application startup.  Must be called *after* all model modules have
    been imported so that their table definitions are registered on ``Base``.
    """
    # Import all model modules here so their classes are registered on Base
    # before create_all() is invoked.
    from app.models import user  # noqa: F401  — side-effect import
    from sqlalchemy import text, inspect

    Base.metadata.create_all(bind=engine)

    # ── Auto-migrate missing columns for SQLite ────────────────────────────
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "role" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'student' NOT NULL"))
                conn.commit()


# ---------------------------------------------------------------------------
# Dependency — request-scoped DB session
# ---------------------------------------------------------------------------
def get_db():
    """Yield a database session and guarantee it is closed after the request.

    Intended for use with FastAPI's ``Depends`` in route handlers::

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
