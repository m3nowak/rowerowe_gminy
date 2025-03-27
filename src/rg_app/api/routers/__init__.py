from .activities import router as activities_router
from .athletes import router as athletes_router
from .auth import router as auth_router
from .health import router as health_router
from .regions import router as regions_router
from .user import router as user_router

__all__ = ["auth_router", "health_router", "regions_router", "activities_router", "athletes_router", "user_router"]
