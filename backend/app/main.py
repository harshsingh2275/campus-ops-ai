"""
main.py — Campus Ops AI Backend Entry Point
============================================

This module bootstraps the FastAPI application that powers the Campus Ops AI
platform. The high-level flow is:

  1. **Startup (lifespan)**:
     - Logs configuration state (CORS origins, Notion connectivity).
     - Writes a SYSTEM_STARTUP event to the Notion Run Log database so every
       server boot is auditable.
     - Starts the background ExecutionEngine poller which continuously checks
       Notion for approved tickets and auto-executes them.

  2. **Runtime**:
     - Exposes ``/api/submit`` (request ingestion, AI parsing → Notion sync)
       and ``/api/health`` (liveness/readiness probes).
     - CORS is configured to allow the Next.js frontend (localhost:3000) and
       any additional origins specified in the environment.

  3. **Shutdown**:
     - Gracefully cancels the ExecutionEngine background task.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import create_db_tables
from .routes import submit_router, health_router, auth_router, admin_router
from .models.run_log import RunLogEventType, RunLogStatus
from .services.notion_service import log_submission_event
from .services.engine import execution_engine

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
# All modules under ``campus_ops.*`` inherit this root format so that every
# log line includes a timestamp, severity level, and originating logger name.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("campus_ops.main")


# ---------------------------------------------------------------------------
# Application Lifespan (Startup / Shutdown)
# ---------------------------------------------------------------------------
# FastAPI's ``lifespan`` context manager replaces the older ``on_event``
# hooks. Everything before ``yield`` runs on startup; everything after runs
# on shutdown.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Allowed CORS Origins: {settings.cors_origins_list}")
    logger.info(f"Notion Live Configured: {settings.is_notion_configured}")

    # Initialise SQLite database and create tables (no-op if already exist).
    create_db_tables()
    logger.info("SQLite database initialised (campus_ops.db).")

    # Persist a startup event in the Notion Run Log database so operators
    # can audit when each server instance was brought online.
    log_submission_event(
        event_type=RunLogEventType.SYSTEM_STARTUP,
        status=RunLogStatus.SUCCESS,
        details=f"FastAPI Server initialized on port {settings.PORT}. CORS origins: {settings.cors_origins_list}. Notion mode: {'live' if settings.is_notion_configured else 'simulated'}.",
        execution_time_ms=0.0
    )

    # Start automated background poller and execution engine (10s interval).
    # The engine queries Notion for "Approved" tickets and auto-generates
    # gatepasses — see engine.py for the full extraction flow.
    execution_engine.start()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────
    # Cancel the ExecutionEngine's asyncio polling task so the process
    # exits cleanly without dangling coroutines.
    logger.info("Campus Ops AI Backend shutting down.")
    execution_engine.stop()


# ---------------------------------------------------------------------------
# FastAPI Application Instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Campus Operations API for parsing unstructured student requests, syncing with Notion databases, and automated background execution.",
    lifespan=lifespan
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
# The Next.js frontend runs on a different origin (localhost:3000) during
# development, so cross-origin requests must be explicitly permitted.
# ``settings.cors_origins_list`` merges defaults with any env-level overrides.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------
# ``health_router`` → /api/health  (liveness & readiness probes)
# ``submit_router`` → /api/submit  (request ingestion, AI parse, Notion sync)
# ---------------------------------------------------------------------------
app.include_router(health_router)
app.include_router(submit_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/", tags=["Root"])
async def root():
    """Return a simple JSON payload confirming the API is alive and listing
    key endpoint URLs for quick developer reference."""
    return {
        "message": "Campus Ops AI Backend API is running with Background Execution Engine.",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "submit_url": "/api/submit"
    }


# ---------------------------------------------------------------------------
# Direct Execution (``python -m app.main``)
# ---------------------------------------------------------------------------
# When run directly (rather than via ``uvicorn app.main:app``), this block
# starts uvicorn programmatically with hot-reload enabled in dev mode.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
