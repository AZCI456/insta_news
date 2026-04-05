"""Club management routes for users to manage subscriptions."""

from typing import List
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import TEMPLATES_DIR
from src.database.manager import DatabaseManager

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
db = DatabaseManager()


@router.get("/manage", response_class=HTMLResponse)
async def manage(request: Request, token: str) -> HTMLResponse:
    """Show club management page for user with magic link token."""
    
    # Look up user by token
    user = db.get_user_by_token(token)
    
    if not user:
        return templates.TemplateResponse(request, "manage_invalid.html", {})
    
    user_id = user["user_id"]
    
    # Get all clubs and user's subscriptions
    clubs = db.get_all_clubs()
    selected_club_ids = db.get_user_subscriptions(user_id)
    
    return templates.TemplateResponse(
        request,
        "manage.html",
        {
            "token": token,
            "clubs": clubs,
            "selected_club_ids": selected_club_ids,
        },
    )


@router.post("/manage")
async def update_manage(
    request: Request,
    token: str = Form(...),
    club_id: List[int] = Form(default=[]),
) -> RedirectResponse:
    """Handle club subscription updates."""
    
    # Look up user by token
    user = db.get_user_by_token(token)
    
    if not user:
        return RedirectResponse(url="/manage?token=invalid", status_code=303)
    
    user_id = user["user_id"]
    
    # Update subscriptions
    selected_ids = [int(cid) for cid in club_id]
    db.update_user_subscriptions(user_id, selected_ids)
    
    # Redirect back to manage page
    return RedirectResponse(
        url=f"/manage?token={token}&saved=1",
        status_code=303
    )
