import sqlite3
from typing import Dict, Any
from dotenv import load_dotenv

import os
load_dotenv()
DB_PATH = os.getenv("insta_news_db_path")

def db_insert_gemini_summaries(json_summary: Dict[str, Any]) -> None:

    conn = sqlite3.connect(DB_PATH)

    conn.execute("INSERT INTO ai_summaries (club_id, header, content)" \
               "VALUES (?, ?, ?)", (json_summary["club_id"], json_summary["header"], json_summary["content"]))

    conn.commit()
    conn.close()


def db_insert_posts(json_posts: Dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_PATH)

    conn.execute("INSERT INTO posts (club_id, caption, likes, time_metadata_utc, date_scraped, shortcode)" \
               "VALUES (?, ?, ?, ?, ?, ?)", (json_posts["club_id"], json_posts["caption"], json_posts["likes"], json_posts["time_metadata_utc"], json_posts["date_scraped"], json_posts["shortcode"]))

    conn.commit()
    conn.close()

# first decide on events schema
def db_insert_food_events(json_food_events: Dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_PATH)
    pass # TODO: implement this