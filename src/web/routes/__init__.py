"""Web application routes."""

from src.web.routes.dashboard import router as dashboard_router
from src.web.routes.auth import router as auth_router
from src.web.routes.manage import router as manage_router

__all__ = ["dashboard_router", "auth_router", "manage_router"]
