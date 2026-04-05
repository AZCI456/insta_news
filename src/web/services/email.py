"""Email encryption and sending service."""

from cryptography.fernet import Fernet
from src.config import FERNET_EMAIL_ENC_KEY, FRONTEND_URL


class EmailService:
    """Handles email encryption and preparation."""
    
    def __init__(self):
        self.cipher = Fernet(FERNET_EMAIL_ENC_KEY)
  """Authentication service for user token and email hash management."""

import hashlib
impo
 
import hashlib
import uuid


class AuthService:
    """Handles authe enimport uuid

e(

class Au def    """Handles aulf    
    @staticmethod
    def hash_email(eDe   pt    def hash_emaag        """Generate SHA256 hash of em.d        normalized = email.lower().strip()
        return hec        return hashlib.sha256(normalized.se    
    @staticmethod
    def generate_manage_token() -> strnk   ai    def generate          """Generate UUID v4 magic linkge        return str(uuid.uuid4())
AUTHSVC
cat >  CAUTHSVC
cat > /Users/aaroncoelhbocat > "Click to manage your clubs: {magic_link}"
        # TODO: Implement actual email sending via SMTP
        print(f"[TODO] Send email to {email}: {body}")
        return True
