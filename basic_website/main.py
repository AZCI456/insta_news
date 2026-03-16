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
from pathlib import Path
import hashlib
# FastAPI, like many modern frameworks, uses Python's typing system
# to make APIs safer and more predictable.
# 
# Here, we import `List` from the `typing` module to specify that certain function
# parameters or variables can hold a list of items (e.g., a list of integers such as List[int]).
# This is especially important for routes that can receive multiple values (like when
# a user checks multiple checkboxes in a form submission), so FastAPI knows to
# parse those inputs as Python lists and provide useful editor/type hints.
from typing import List
from datetime import datetime, timedelta, timezone  
from email_system.email_utilites import (
    encrypt_email,
    generate_manage_token,
    send_magic_link_email,
)

from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. Basic configuration and environment loading
# -----------------------------------------------------------------------------

# Load variables from a .env file into process environment.
# This lets you keep secrets (DB path, encryption keys, SMTP credentials)
# OUT of your code and OUT of version control.
load_dotenv()

# BASE_DIR is the folder this file lives in (e.g. .../basic_website/fast_api_testing)
BASE_DIR = Path(__file__).resolve().parent

# This should point at the SAME DB file your ETL / schema.sql use.
# In .env you might have:
#   insta_news_db_path=/Users/you/dev/insta_news/insta_news.db
DB_PATH_ENV = os.getenv("insta_news_db_path")
if not DB_PATH_ENV:
  raise RuntimeError(
      "insta_news_db_path is not set in your environment.\n"
      "Add it to your .env so this backend talks to the correct SQLite file."
  )

DB_PATH = Path(DB_PATH_ENV)

# -----------------------------------------------------------------------------
# 2. SQLite helper
# -----------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the main insta_news SQLite DB.


    - check_same_thread=False: allows usage from FastAPI's async context
      (we make sure to open/close connections per request to keep it simple).
      ie disabling sqlite protections, so ensure each connection is only used where it’s created
    - PRAGMA journal_mode=WAL: better concurrency for read-heavy workloads.
        Readers can keep reading from the main DB file while writes append to the WAL file
    - PRAGMA foreign_keys=ON: enforces your schema's FK constraints.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------------------------------------------------------
# 3. FastAPI app and template setup
# -----------------------------------------------------------------------------

# This is the main FastAPI application object.
# uvicorn will look for "main:app" when you run `uvicorn main:app --reload`.
app = FastAPI()

# Tell FastAPI/Jinja2 where to find your HTML templates.
# For example, if you place index.html in ../templates/index.html:
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mount a /static path so your CSS, JS, and images can be served.
# e.g. /static/theme.css will read from ../static/theme.css
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

# -----------------------------------------------------------------------------
# 4. Simple health check route
# -----------------------------------------------------------------------------

@app.get("/health", response_class=HTMLResponse)
async def health() -> str:
    """
    Very simple "is the server up?" check.

    You can hit this in your browser at /health or curl it:
      curl http://127.0.0.1:8000/health
    """
    return "OK"

# -----------------------------------------------------------------------------
# 5. Home page route (GET) – serves your retro index.html
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def show_home(request: Request) -> HTMLResponse:
    """
    Render the main landing page.

    - `request` must be passed into the template for Jinja2 integration.
    - index.html lives in templates/index.html (one level up from this file).
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            # You can add more context variables here later if needed, e.g.:
            # "some_flag": True
        },
    )

# -----------------------------------------------------------------------------
# 6. Email capture route (POST) – placeholder for your signup logic
# -----------------------------------------------------------------------------

@app.post("/signup")
async def signup(email: str = Form(...)) -> RedirectResponse:
    """
    Handle the email form submission from the landing page.

    Right now this is a minimal placeholder that just prints to stdout
    and redirects back to "/". You will later:

    - Hash + encrypt the email
    - Upsert into `users` (using email_hash + encrypted_email + manage_token)
    - Send a magic-link email containing /manage?token=...
    - Maybe flash a "check your email" message

    `email: str = Form(...)` tells FastAPI to read an HTML form field called "email".
    """
    normalized_email = email.strip().lower()
    # print(f"[DEBUG] Received signup email: {normalized_email}")


    # 1) Compute email_hash and encrypted_email
    # TODO: add pepper (or salt - maybe better for this use case) in .env to make it more secure (add a random string to the email before hashing)
    # BIG ISSUE: losing it breaks lookups - how to make system robust to this? (still susceptible to randow table attacks)
    # For now unimelb limits the email search lookup of students per student - good enough for now to keep safe
    email_hash = hashlib.sha256(normalized_email.encode()).hexdigest() 
    encrypted_email = encrypt_email(normalized_email)

    # generate uuidv4
    manage_token = generate_manage_token()

    # 2) Upsert into the users table
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO users (email_hash, encrypted_email, manage_token) VALUES (?, ?, ?)", (email_hash, encrypted_email, manage_token))
    conn.commit()
    # get the manage token for the user - in the case that they're already in the db - hash collision
    manage_token = conn.execute("SELECT manage_token FROM users WHERE email_hash = ?", (email_hash,)).fetchone()[0]
    conn.close()

    # 4) Send magic-link email
    send_magic_link_email(normalized_email, manage_token)

    # 5) Redirect to the manage page (static message shows )
    return RedirectResponse(url="/?sent=1", status_code=303)


# -----------------------------------------------------------------------------
# 7. Manage page (GET) – skeleton for magic-link page
# -----------------------------------------------------------------------------

@app.get("/manage", response_class=HTMLResponse)
async def manage(request: Request, token: str) -> HTMLResponse:
    """
    Magic-link entry point.

    - Users arrive here via an emailed link containing ?token=MANAGE_TOKEN.
    - You will:
        * Look up the user by manage_token
        * Load their current club subscriptions
        * Render a page that lets them tick/untick clubs and save

    For now this loads clubs + the user’s current subscriptions
    (if the token is valid) and renders a management page.
    """
    # TODO later: validate token, load user + clubs + subscriptions

    # 1) Look up user by manage_token.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE manage_token = ?;",
        (token,),
    )
    row = cur.fetchone()

    if row is None:
        # Invalid or expired token: show a simple error page that links back home.
        conn.close()
        return templates.TemplateResponse(
            "manage_invalid.html",
            {
                "request": request,
            },
        )

    user_id = row["user_id"]

    # 2) Load all clubs, along with their associated keywords.
    #    We use LEFT JOINs so clubs without any keywords still appear.
    #    GROUP_CONCAT returns a comma-separated string of keywords per club.
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

    # 3) Load this user's current subscriptions (club_ids).
    cur.execute(
        "SELECT club_id FROM subscriptions WHERE user_id = ?;",
        (user_id,),
    )
    selected_rows = cur.fetchall()
    # NOTE:
    #    make the Jinja check `if club["club_id"] in selected_club_ids`
    selected_club_ids = {r["club_id"] for r in selected_rows}

    conn.close()

    return templates.TemplateResponse(
        "manage.html",
        {
            "request": request,
            "token": token,
            "clubs": clubs,
            "selected_club_ids": selected_club_ids,
        },
    )


@app.post("/manage")
async def update_manage(
    request: Request,
    token: str,  # comes from the query string: /manage?token=...
    club_id: List[int] = Form([]),
) -> RedirectResponse:
    """
    Handle the form submission from manage.html when the user clicks
    "Save my club list".

    IMPORTANT pieces:
    - `token: str` is the same magic link token as in the GET route, but here
      FastAPI reads it from the query string on the POST request.
    - `club_id: List[int] = Form([])`:
        * In the HTML, each checkbox is named "club_id".
        * When several checkboxes are ticked, the browser sends a list of
          values for "club_id".
        * FastAPI collects those into a Python list of ints.
    """
    # 1) Look up the user associated with this manage_token.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE manage_token = ?;",
        (token,),
    )
    row = cur.fetchone()

    if row is None:
        # Token is invalid or expired: close the connection and send the user
        # to the same "invalid" page used by the GET handler.
        conn.close()
        return RedirectResponse(url="/manage?token=invalid", status_code=303)

    user_id = row["user_id"]

    # 2) Normalize the incoming list of club_ids.
    #    If the user unticks everything, club_id will be an empty list.
    selected_ids: List[int] = [int(cid) for cid in club_id]

    # 3) We want to know which clubs this user was previously subscribed to so we can
    #    detect *newly* added clubs on this save.
    cur.execute(
        "SELECT club_id FROM subscriptions WHERE user_id = ?;",
        (user_id,),
    )
    previous_rows = cur.fetchall()
    previous_ids = {r["club_id"] for r in previous_rows}

    # 4) Replace this user's subscriptions in a single transaction:
    #    - DELETE all existing rows for this user_id
    #    - INSERT new rows for each selected club_id
    cur.execute(
        "DELETE FROM subscriptions WHERE user_id = ?;",
        (user_id,),
    )

    # Only insert if there is at least one selected club to avoid an empty executemany().
    if selected_ids:
        cur.executemany(
            "INSERT INTO subscriptions (user_id, club_id) VALUES (?, ?);",
            [(user_id, cid) for cid in selected_ids],
        )

    # 5) Activate scraping only for clubs that now have at least one subscriber
    #    and have never been scraped before (last_scraped IS NULL).
    #    We set last_scraped to "9 days ago" (in UTC) so your scraper logic treats them as due.
    nine_days_ago_iso = (datetime.now(timezone.utc) - timedelta(days=9)).isoformat(timespec="seconds")
    cur.execute(
        """
        UPDATE clubs
        SET last_scraped_at = ?
        WHERE last_scraped_at IS NULL           -- brilliant sql v clean
          AND club_id IN (
              SELECT DISTINCT club_id FROM subscriptions
          );
        """,
        (nine_days_ago_iso,),
    )

    conn.commit()
    conn.close()

    # TODO: implement this as a optimisation for when not being used (first need subscribers lol)
    #       handle the case where the club now has no subscribers - set last_scraped to NULL (see SQL folder)

    # 4) Redirect back to the manage page so the user sees their updated list.
    #    We add ?saved=1 so the template can show a small "updated" banner.
    return RedirectResponse(url=f"/manage?token={token}&saved=1", status_code=303)

# -----------------------------------------------------------------------------
# 8. Local development entry point (optional)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Allows you to run this file directly with:
        python main.py

    Instead of typing the uvicorn command each time.
    """
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # auto-reload on code changes; great for dev
    )