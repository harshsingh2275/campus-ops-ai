import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import submit_router, health_router
from .models.run_log import RunLogEventType, RunLogStatus
from .services.notion_service import log_submission_event
from .services.engine import execution_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("campus_ops.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Allowed CORS Origins: {settings.cors_origins_list}")
    logger.info(f"Notion Live Configured: {settings.is_notion_configured}")
    
    log_submission_event(
        event_type=RunLogEventType.SYSTEM_STARTUP,
        status=RunLogStatus.SUCCESS,
        details=f"FastAPI Server initialized on port {settings.PORT}. CORS origins: {settings.cors_origins_list}. Notion mode: {'live' if settings.is_notion_configured else 'simulated'}.",
        execution_time_ms=0.0
    )

    # Start automated background poller and execution engine (10s interval)
    execution_engine.start()

    yield

    # Shutdown
    logger.info("Campus Ops AI Backend shutting down.")
    execution_engine.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Campus Operations API for parsing unstructured student requests, syncing with Notion databases, and automated background execution.",
    lifespan=lifespan
)

# Enable CORS for localhost:3000 and configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(submit_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Campus Ops AI Backend API is running with Background Execution Engine.",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "submit_url": "/api/submit"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
