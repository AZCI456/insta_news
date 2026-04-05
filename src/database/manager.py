import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Set
from pathlib import Path

from src.config import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_CONFIG["path"]
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user by manage token."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT user_id, email_hash, encrypted_email FROM users WHERE manage_token = ?",
                (token,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_user_by_hash(self, email_hash: str) -> Optional[Dict[str, Any]]:
        """Get user by email hash."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT user_id, email_hash, encrypted_email FROM users WHERE email_hash = ?",
                (email_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def create_user(self, email_hash: str, encrypted_email: str, manage_token: str) -> int:
        """Create or update user with magic link token."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT OR REPLACE INTO users (email_hash, encrypted_email, manage_token, created_at)
                   VALUES (?, ?, ?, ?)""",
                (email_hash, encrypted_email, manage_token, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_manage_token_by_hash(self, email_hash: str) -> Optional[str]:
        """Get manage token from email hash."""
        user = self.get_user_by_hash(email_hash)
        return user["manage_token"] if user else None
    
    def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs with their keywords."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """SELECT c.club_id, c.club_name, 
                          GROUP_CONCAT(k.keyword, ', ') as keywords
                   FROM clubs c
                   LEFT JOIN club_keywords ck ON c.club_id = ck.club_id
                   LEFT JOIN keywords k ON ck.keyword_id = k.keyword_id
                   GROUP BY c.club_id
                   ORDER BY c.club_name"""
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_user_subscriptions(self, user_id: int) -> List[int]:
        """Get list of club IDs user is subscribed to."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT club_id FROM subscriptions WHERE user_id = ?",
                (user_id,)
            )
            return [row["club_id"] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def update_user_subscriptions(self, user_id: int, club_ids: List[int]) -> None:
        """Update user's club subscriptions."""
        conn = self.get_connection()
        try:
            # Delete existing subscriptions
            conn.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
            
            # Insert new subscriptions
            for club_id in club_ids:
                conn.execute(
                    "INSERT INTO subscriptions (user_id, club_id) VALUES (?, ?)",
                    (user_id, club_id)
                )
            
            conn.commit()
        finally:
            conn.close()
