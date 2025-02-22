from .activities import router as activities_router
from .athlete import router as athlete_router
from .auth import router as auth_router
from .health import router as health_router
from .regions import router as regions_router

__all__ = ["auth_router", "health_router", "regions_router", "activities_router", "athlete_router"]
