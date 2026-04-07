"""
Tests for ETL summary DB insertion helper.

Teaching note:
- This test uses a temporary SQLite file with a minimal schema.
- It verifies both:
  1) main summary row insertion into `ai_summaries`
  2) junction-table links in `summary_to_posts`
"""

from __future__ import annotations

import sqlite3

from src.etl.prod.db_insertion_tools import db_insert as db_insert_module


def _create_minimal_schema(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute(
            """
            CREATE TABLE posts (
                post_id INTEGER PRIMARY KEY
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE ai_summaries (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                club_id INTEGER NOT NULL,
                header TEXT,
                content TEXT,
                created_at DATETIME
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE summary_to_posts (
                summary_id INTEGER,
                post_id INTEGER,
                PRIMARY KEY (summary_id, post_id),
                FOREIGN KEY (summary_id) REFERENCES ai_summaries(summary_id),
                FOREIGN KEY (post_id) REFERENCES posts(post_id)
            );
            """
        )
        conn.executemany("INSERT INTO posts(post_id) VALUES (?)", [(101,), (102,)])
        conn.commit()
    finally:
        conn.close()


def test_db_insert_gemini_summaries_inserts_summary_and_links(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.sqlite")
    _create_minimal_schema(db_path)
    monkeypatch.setattr(db_insert_module, "DB_PATH", db_path)

    payload = {
        "club_id": 7,
        "header": "MUMS FREE FOOD WED",
        "content": "Pizza and board games this week.",
        "source_posts": [{"post_id": 101}, {"post_id": 102}],
    }

    db_insert_module.db_insert_gemini_summaries(payload)

    conn = sqlite3.connect(db_path)
    try:
        summary = conn.execute(
            "SELECT summary_id, club_id, header, content FROM ai_summaries"
        ).fetchone()
        assert summary is not None
        summary_id, club_id, header, content = summary
        assert club_id == 7
        assert header == "MUMS FREE FOOD WED"
        assert content == "Pizza and board games this week."

        links = conn.execute(
            "SELECT post_id FROM summary_to_posts WHERE summary_id = ? ORDER BY post_id",
            (summary_id,),
        ).fetchall()
        assert links == [(101,), (102,)]
    finally:
        conn.close()

