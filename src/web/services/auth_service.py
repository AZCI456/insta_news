"""Authentication service for user token and email hash management."""

import hashlib
import uuid


class AuthService:
    """Handles authentication operations."""
    
    @staticmethod
    def hash_email(email: str) -> str:
        """Generate SHA256 hash of email for user lookup."""
        normalized = email.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    @staticmethod
    def generate_manage_token() -> str:
        """Generate UUID v4 magic link token."""
        return str(uuid.uuid4())
