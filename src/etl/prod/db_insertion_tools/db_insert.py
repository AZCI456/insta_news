import sqlite3
from typing import Dict, Any
from dotenv import load_dotenv
from datetime import datetime, UTC

import os
load_dotenv()
DB_PATH = os.getenv("insta_news_db_path")

#TODO: switch dictionary calls to .get() so auto None if not present (maps to NULL in db)
#       make conn.execute cursor.execute for better practice and speed

def db_insert_gemini_summaries(json_summary: Dict[str, Any]) -> None:
    """
    Insert one Gemini summary and link it to source posts.

    Teaching note:
    - We use `cursor.lastrowid` to get the inserted summary_id reliably.
    - `INSERT OR IGNORE` on `summary_to_posts` makes re-runs idempotent.
    - `source_posts` defaults to [] so missing payload keys do not crash ETL.
    """
    if not DB_PATH:
        raise RuntimeError("insta_news_db_path is not set; cannot insert Gemini summaries.")

    print(f"current json for {json_summary.get('display_header').get('name')}:\n {json_summary}")

    gen_time_utc = datetime.now(UTC).isoformat(timespec="seconds")
    conn = sqlite3.connect(DB_PATH)

    try:
        # insert main data regarding the summary
        cursor = conn.execute(
            "INSERT INTO ai_summaries (club_id, header, content, created_at) VALUES (?, ?, ?, ?)",
            (
                json_summary.get("club_id"),
                json_summary.get("main_event"),
                json_summary.get("summary_text"),
                gen_time_utc,
            ),
        )
        summary_id = cursor.lastrowid

        # ensure that the summary is also linked to the posts in the junction table
        for post in json_summary.get("source_posts", []):
            shortcode = post.get("post_id")
            if shortcode is None:
                continue

            post_id = cursor.execute("SELECT post_id FROM posts WHERE shortcode = ?", (shortcode,)).fetchone()
            # create connection between existing post and new summary
            conn.execute(
                "INSERT OR IGNORE INTO summary_to_posts (summary_id, post_id) VALUES (?, ?)",
                (summary_id, post_id[0]),
            )

        conn.commit()
    finally:
        conn.close()


def db_insert_posts(json_posts: Dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_PATH)

    # TODO: 
    conn.execute("INSERT OR IGNORE INTO posts (club_id, caption, likes, time_metadata_utc, date_scraped, shortcode)" \
               "VALUES (?, ?, ?, ?, ?, ?)", (json_posts["club_id"], json_posts["caption"], json_posts["likes"], json_posts["time_metadata_utc"], json_posts["date_scraped"], json_posts["shortcode"]))

    conn.commit()
    conn.close()

# first decide on events schema
def db_insert_food_events(json_food_events: Dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_PATH)
    pass # TODO: implement this