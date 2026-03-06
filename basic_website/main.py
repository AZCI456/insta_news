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
    print(f"[DEBUG] Received signup email: {normalized_email}")

    # Flash a message to the user that an email has been "sent" (placeholder).
    # FastAPI doesn't have built-in "flash messages" like Flask, so here's an easy teaching workaround:
    # We'll set a special query string (e.g. ?sent=1) on redirect, and then add logic in your index.html
    # template to display a confirmation message if "sent" is present in the URL.
    #
    # After you wire this up in your template, users will see "Confirmation email sent!" after submitting.


    # TODO:
    # 1) Compute email_hash and encrypted_email

    #TODO: add salt to make it more secure (add a random string to the email before hashing)
    email_hash = hashlib.sha256(normalized_email.encode()).hexdigest() # built in hash function - still susseptible to randow table attacks - would need some salt and pepper to make it more secure
    encrypted_email = encrypt_email(normalized_email)

    manage_token = generate_manage_token()
    
    # 2) Upsert into the users table
    conn = get_connection()
    conn.execute("INSERT INTO users (email_hash, encrypted_email, manage_token) VALUES (?, ?, ?)", (email_hash, encrypted_email, manage_token))
    conn.commit()
    conn.close()

    # 4) Send magic-link email
    send_magic_link_email(normalized_email, manage_token)

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

    For now it just shows a tiny debug page so you can confirm the flow.
    """
    # TODO later: validate token, load user + clubs + subscriptions
    return templates.TemplateResponse(
        "manage.html",  # you'll create this later
        {
            "request": request,
            "token": token,
        },
    )

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