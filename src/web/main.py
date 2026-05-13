# I need a web dev lol - bottom code reviewed tho seems airtight enough for the timebeing
# main.py

"""
Minimal FastAPI backend template for UniMelb Club Oracle.

This file focuses on:
- Setting up FastAPI
- Connecting to your existing SQLite DB
- Defining a couple of simple routes you can extend later

Everything is written with "explain the boilerplate" in mind.
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import os
import sqlite3
import smtplib
from pathlib import Path
import hashlib
from typing import List
from datetime import datetime, timedelta, timezone

try:
    from src.web.email_system.email_utilites import (
        encrypt_email,
        generate_manage_token,
        send_magic_link_email,
    )
except ModuleNotFoundError:  # pragma: no cover
    from email_system.email_utilites import (
        encrypt_email,
        generate_manage_token,
        send_magic_link_email,
    )

from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. Basic configuration and environment loading
# -----------------------------------------------------------------------------
# teaching comment:
# Load the repo-root `.env` first (where your real secrets usually live), then
# fall back to dotenv's default search (current working directory).
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DB_PATH_ENV = os.getenv("insta_news_db_path")
if not DB_PATH_ENV:
    raise RuntimeError(
        "insta_news_db_path is not set in your environment.\n"
        "Add it to your .env so this backend talks to the correct SQLite file."
    )

DB_PATH = Path(DB_PATH_ENV)


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the main insta_news SQLite DB.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/health", response_class=HTMLResponse)
async def health() -> str:
    return "OK"


@app.get("/", response_class=HTMLResponse)
async def show_home(request: Request) -> HTMLResponse:
    # Starlette 1.x+ expects `TemplateResponse(request, template_name, context)`.
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/signup")
async def signup(email: str = Form(...)) -> RedirectResponse:
    normalized_email = email.strip().lower()
    email_hash = hashlib.sha256(normalized_email.encode()).hexdigest()
    encrypted_email = encrypt_email(normalized_email)
    manage_token = generate_manage_token()

    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO users (email_hash, encrypted_email, manage_token) VALUES (?, ?, ?)",
        (email_hash, encrypted_email, manage_token),
    )
    conn.commit()
    manage_token = conn.execute("SELECT manage_token FROM users WHERE email_hash = ?", (email_hash,)).fetchone()[0]
    conn.close()

    # teaching comment:
    # In SES sandbox mode, SMTP rejects non-verified recipients with 554.
    # We should not crash signup if email sending fails; user data is already
    # safely stored, so we redirect with a flag the frontend can display.
    try:
        send_magic_link_email(normalized_email, manage_token)
        return RedirectResponse(url="/?sent=1", status_code=303)
    except smtplib.SMTPException as exc:
        print(f"[WARN] Failed to send magic link email to {normalized_email}: {exc}")
        return RedirectResponse(url="/?sent=0&email_error=1", status_code=303)


@app.get("/manage", response_class=HTMLResponse)
async def manage(request: Request, token: str) -> HTMLResponse:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE manage_token = ?;", (token,))
    row = cur.fetchone()

    if row is None:
        conn.close()
        return templates.TemplateResponse(request, "manage_invalid.html", {})

    user_id = row["user_id"]
    cur.execute(
        """
        SELECT
            c.club_id,
            c.name,
            IFNULL(GROUP_CONCAT(k.keyword, ','), '') AS keywords
        FROM clubs AS c
        LEFT JOIN club_keywords AS ck ON ck.club_id = c.club_id
        LEFT JOIN keywords AS k ON k.keyword_id = ck.keyword_id
        GROUP BY c.club_id, c.name
        ORDER BY c.name COLLATE NOCASE;
        """
    )
    clubs = cur.fetchall()

    cur.execute("SELECT club_id FROM subscriptions WHERE user_id = ?;", (user_id,))
    selected_rows = cur.fetchall()
    selected_club_ids = {r["club_id"] for r in selected_rows}
    conn.close()

    return templates.TemplateResponse(
        request,
        "manage.html",
        {
            "token": token,
            "clubs": clubs,
            "selected_club_ids": selected_club_ids,
        },
    )


@app.post("/manage")
async def update_manage(
    request: Request,
    token: str,
    club_id: List[int] = Form([]),
) -> RedirectResponse:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE manage_token = ?;", (token,))
    row = cur.fetchone()

    if row is None:
        conn.close()
        return RedirectResponse(url="/manage?token=invalid", status_code=303)

    user_id = row["user_id"]
    selected_ids: List[int] = [int(cid) for cid in club_id]

    cur.execute("DELETE FROM subscriptions WHERE user_id = ?;", (user_id,))
    if selected_ids:
        cur.executemany(
            "INSERT INTO subscriptions (user_id, club_id) VALUES (?, ?);",
            [(user_id, cid) for cid in selected_ids],
        )

    two_weeks_ago_iso = (datetime.now(timezone.utc) - timedelta(weeks=2)).isoformat(timespec="seconds")
    cur.execute(
        """
        UPDATE clubs
        SET last_scraped_at = ?
        WHERE last_scraped_at IS NULL
          AND club_id IN (
              SELECT DISTINCT club_id FROM subscriptions
          );
        """,
        (two_weeks_ago_iso,),
    )

    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/manage?token={token}&saved=1", status_code=303)


if __name__ == "__main__":
    import uvicorn

    # teaching comment:
    # When you run `python main.py` from `src/web/`, the app module name is
    # `main`, not `src.web.main`. Uvicorn's reloader must use the same string
    # Python would use to import the module, or the worker process fails with
    # `ModuleNotFoundError: No module named 'src'`.
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
