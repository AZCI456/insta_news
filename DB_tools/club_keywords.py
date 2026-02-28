"""
Helpers for storing clubs and their data-msl-keywords in the many-to-many schema.
Use from your MSL listing scraper: parse keywords from each <li>, then call
store_club_with_keywords so discovery search works.
"""
import sqlite3


def parse_keywords(keywords_str: str) -> list[str]:
    """
    Parse the data-msl-keywords attribute (comma-separated) into a normalised list.
    Returns lowercased, stripped keywords; skips empty parts.
    """
    if not keywords_str or not keywords_str.strip():
        return []
    return [k.strip().lower() for k in keywords_str.split(",") if k.strip()]


def store_club_with_keywords(
    conn: sqlite3.Connection,
    username: str,
    *,
    name: str | None = None,
    email: str | None = None,
    keywords_list: list[str] | None = None,
) -> None:
    """
    Upsert a club and link it to the given keywords (many-to-many).
    - Club: only non-None name/email are written; existing values are kept otherwise.
    - Keywords: each keyword is INSERT OR IGNORE into keywords; then this club's
      links in club_keywords are replaced by the new list (so re-scrapes stay in sync).
    """
    conn.execute("PRAGMA foreign_keys = ON;")
    # Upsert club (preserve existing name/email if we don't pass new ones)
    conn.execute(
        """
        INSERT INTO clubs (username, name, email, last_scraped_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(username) DO UPDATE SET
          name = COALESCE(excluded.name, name),
          email = COALESCE(excluded.email, email),
          last_scraped_at = datetime('now');
        """,
        (username, name, email),
    )
    if keywords_list is not None:
        # Replace this club's keyword links so we don't accumulate stale ones
        conn.execute("DELETE FROM club_keywords WHERE club_username = ?", (username,))
        for kw in keywords_list:
            conn.execute("INSERT OR IGNORE INTO keywords (keyword) VALUES (?)", (kw,))
            row = conn.execute("SELECT id FROM keywords WHERE keyword = ?", (kw,)).fetchone()
            if row:
                conn.execute(
                    "INSERT OR IGNORE INTO club_keywords (club_username, keyword_id) VALUES (?, ?)",
                    (username, row[0]),
                )
    conn.commit()


def clubs_matching_keyword(conn: sqlite3.Connection, search: str) -> list[tuple[str, str | None]]:
    """
    Discovery query: clubs that have any keyword containing the search term (case-insensitive).
    Returns list of (name, email) for quick use in a search UI.
    """
    conn.execute("PRAGMA foreign_keys = ON;")
    pattern = f"%{search.strip().lower()}%"
    return conn.execute(
        """
        SELECT DISTINCT c.name, c.email
        FROM clubs c
        JOIN club_keywords ck ON c.username = ck.club_username
        JOIN keywords k ON ck.keyword_id = k.id
        WHERE k.keyword LIKE ?
        ORDER BY c.name;
        """,
        (pattern,),
    ).fetchall()
