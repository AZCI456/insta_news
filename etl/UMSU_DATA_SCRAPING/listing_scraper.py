"""
MSL buddy-up clubs listing scraper (Beautiful Soup).
Fetches the main listing page, finds each club <li>, extracts keywords and join link,
then optionally stores in DB and/or enqueues detail-page fetches.
"""
import sqlite3
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# Config: set base URL for MSL (e.g. https://msl.unimelb.edu.au)
# -----------------------------------------------------------------------------
LISTING_URL = "https://msl.unimelb.edu.au/buddy-up/clubs/clubs-listing/"
# Or read from env: os.getenv("UMSU_LISTING_URL", LISTING_URL)


def fetch_listing_html(url: str) -> str:
    """GET the listing page and return raw HTML."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_listing(html: str) -> list[dict]:
    """
    Parse listing HTML and return one dict per club with keys:
    - club_id: from data-msl-grouping-id (use as clubs.username if you have no Instagram yet)
    - name: from .msl-gl-link text
    - join_path: e.g. /buddy-up/clubs/clubs-listing/join/6141/
    - keywords: list of strings (from data-msl-keywords, comma-split, normalised)
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # All clubs live in ul.msl_organisation_list; each li has data-msl-grouping-id
    for li in soup.select("ul.msl_organisation_list li[data-msl-grouping-id]"):
        grouping_id = li.get("data-msl-grouping-id")
        if not grouping_id:
            continue

        # Join link and display name
        link = li.select_one("a.msl-gl-link")
        join_path = None
        name = None
        if link:
            join_path = link.get("href", "").strip()
            name = (link.get_text() or "").strip()

        # Keywords (optional on the listing)
        keywords_attr = li.get("data-msl-keywords") or ""
        keywords = [
            k.strip().lower()
            for k in keywords_attr.split(",")
            if k.strip()
        ]

        results.append({
            "club_id": grouping_id,
            "name": name or None,
            "join_path": join_path or None,
            "keywords": keywords,
        })

    return results


def store_listing_to_db(conn: sqlite3.Connection, clubs: list[dict]) -> None:
    """
    Persist parsed listing into clubs + keywords + club_keywords.
    Uses club_id as clubs.username; name/keywords from listing; email left for detail scraper.
    """
    from DB_tools.club_keywords import store_club_with_keywords

    for c in clubs:
        store_club_with_keywords(
            conn,
            c["club_id"],
            name=c.get("name"),
            keywords_list=c.get("keywords") or None,
        )


def main():
    html = fetch_listing_html(LISTING_URL)
    clubs = parse_listing(html)
    print(f"Parsed {len(clubs)} clubs from listing")

    # Optional: write to DB (set DB_PATH or pass conn)
    # conn = sqlite3.connect("/opt/insta_news_data/sqlite3/insta_news.sqlite3")
    # store_listing_to_db(conn, clubs)
    # conn.close()

    # Optional: enqueue detail-page fetches (your child script)
    # for c in clubs:
    #     detail_url = urljoin(LISTING_URL, c["join_path"])
    #     fetch_club_detail(detail_url, c["club_id"])


if __name__ == "__main__":
    main()
