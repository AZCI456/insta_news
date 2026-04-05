"""Authentication routes for user signup and login."""

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import TEMPLATES_DIR
from src.web.services.auth_service import AuthService
from src.web.services.email import EmailService
from src.database.manager import DatabaseManager

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
auth_svc = AuthService()
email_svc = EmailService()
db = DatabaseManager()


@router.post("/signup")
async def signup(email: str = Form(...)) -> RedirectResponse:
    """Handle user signup with magic link."""
    
    # Normalize email
    normalized_email = email.strip().lower()
    
    # Hash email for lookup
    email_hash = auth_svc.hash_email(normalized_email)
    
    # Generate token
    manage_token = auth_svc.generate_manage_token()
    
    # Encrypt email
    encrypted_email = email_svc.encrypt_email(normalized_email)
    
    # Create or update user in database
    db.create_user(email_hash, encrypted_email, manage_token)
    
    # Send magic link email
    await email_svc.send_magic_link(normalized_email, manage_token)
    
    # Redirect to landing page with success message
    return RedirectResponse(url="/?sent=1", status_code=303)
