"""
Link UMSU listing keywords to clubs in the insta_news database.

This module is kept separate from scrape_website_information.py so that:
- scraping club metadata (names, emails, insta URLs) stays focused, and
- this file just worries about the "keywords" many-to-many relationship.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tqdm import tqdm
from urllib.parse import urljoin

# ---------------------------------------------------------------------------
# 1. Basic configuration
# ---------------------------------------------------------------------------

# We re-use the same base URL as in scrape_website_information.py.
BASE_URL = "https://umsu.unimelb.edu.au/"

# Load .env so we can read the insta_news_db_path used everywhere else.
load_dotenv()
DB_PATH = os.getenv("insta_news_db_path")
if not DB_PATH:
    raise RuntimeError(
        "insta_news_db_path is not set in your environment. "
        "Set it in .env so keyword linking can write to the correct DB."
    )


def get_connection() -> sqlite3.Connection:
    """
    Small helper to open a connection to the insta_news SQLite DB.

    We keep it here instead of re-importing the one from the web app so this
    script can be run stand-alone from the command line.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def extract_grouping_keywords() -> list[tuple[int, list[str]]]:
    """
    Scrape the main clubs listing page once and extract:

        (umsu_grouping_id, [keyword strings])

    for each <li> that has a data-msl-keywords attribute.
    """
    resp = requests.get(
        urljoin(BASE_URL, "/buddy-up/clubs/clubs-listing/"),
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    results: list[tuple[int, list[str]]] = []

    # Each club lives inside:
    #   <ul class="msl_organisation_list">
    #       <li data-msl-grouping-id="6029" data-msl-keywords="accounting, ...">
    #           ...
    #       </li>
    #   </ul>
    for li in soup.select("ul.msl_organisation_list li[data-msl-grouping-id]"):
        grouping_id_str = li.get("data-msl-grouping-id")
        raw_keywords = li.get("data-msl-keywords")

        # Some list items may not have any data-msl-keywords attribute at all.
        if not grouping_id_str or not raw_keywords:
            continue

        try:
            grouping_id = int(grouping_id_str)
        except ValueError:
            # If UMSU ever changes to a non-integer ID, skip gracefully.
            continue

        # Split the comma-separated string and normalise:
        # - strip whitespace
        # - lowercase for consistency
        # - drop any empty entries
        keywords = [
            kw.strip().lower()
            for kw in raw_keywords.split(",")
            if kw.strip()
        ]

        if not keywords:
            continue

        results.append((grouping_id, keywords))

    return results


def link_grouping_keywords() -> None:
    """
    Main entry point:

    - Reads the club listing page and extracts (grouping_id, [keywords]).
    - For each grouping_id:
        * finds the corresponding club_id in your clubs table
          (using clubs.umsu_grouping_id)
        * upserts each keyword into the keywords table
        * links club_id <-> keyword_id in the club_keywords junction table
    """
    pairs = extract_grouping_keywords()
    if not pairs:
        print("No grouping/keyword pairs found on the listing page.")
        return

    conn = get_connection()
    cur = conn.cursor()

    for grouping_id, keywords in tqdm(
        pairs, desc="Linking keywords to clubs"
    ):
        # 1) Find the club row for this UMSU grouping id.
        cur.execute(
            "SELECT club_id FROM clubs WHERE umsu_grouping_id = ?;",
            (grouping_id,),
        )
        club_row = cur.fetchone()
        if club_row is None:
            # This means we haven't yet inserted this club into the DB (for
            # example if scraping failed). Skip gracefully.
            continue

        club_id = club_row["club_id"]

        # 2) For each keyword string:
        for kw in keywords:
            # (a) Ensure it exists in the master keywords table.
            cur.execute(
                "INSERT OR IGNORE INTO keywords (keyword) VALUES (?);",
                (kw,),
            )

            # (b) Find its keyword_id (we know it's there now).
            cur.execute(
                "SELECT keyword_id FROM keywords WHERE keyword = ?;",
                (kw,),
            )
            kw_row = cur.fetchone()
            if kw_row is None:
                continue

            keyword_id = kw_row["keyword_id"]

            # (c) Link club <-> keyword in the junction table.
            cur.execute(
                """
                INSERT OR IGNORE INTO club_keywords (club_id, keyword_id)
                VALUES (?, ?);
                """,
                (club_id, keyword_id),
            )

    conn.commit()
    conn.close()

    print("Finished linking grouping keywords into club_keywords.")

# Here's a simple main block to let this script be run directly.
# This will execute the link_grouping_keywords function to link keywords,
# but won't perform any DB reset or destructive operations.
# Teaching comment:
# This pattern lets you run: python link_keywords.py
# and see the keyword linking in action without altering any core data or doing resets.
if __name__ == "__main__":
    # We import the function from this file itself and call it.
    # It extracts keywords from UMSU, inserts into the master keyword table,
    # and links keywords to clubs using the many-to-many association table.
    link_grouping_keywords()
    print("Finished linking grouping keywords into club_keywords.")