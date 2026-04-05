"""Dashboard routes for displaying landing page and food events."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import TEMPLATES_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/health", response_class=HTMLResponse)
async def health() -> str:
    """Health check endpoint."""
    return "OK"


@router.get("/", response_class=HTMLResponse)
async def show_home(request: Request) -> HTMLResponse:
    """Show main landing page with today's food events."""
    return templates.TemplateResponse(request, "index.html", {})
