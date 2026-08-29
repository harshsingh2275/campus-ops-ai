from .submit import router as submit_router
from .health import router as health_router
from .auth import router as auth_router

__all__ = ["submit_router", "health_router", "auth_router"]
