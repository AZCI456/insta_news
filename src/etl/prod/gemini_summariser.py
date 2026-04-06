"""
etl/prod/gemini_summariser.py

Production Gemini summariser for scraped Instagram posts.
based on original testing file but with additions in the form of
best practice (and new data types + paths tie in)

Design goals
------------
1) Keep the input/output contract simple:
   - Input: a list of post dicts (from the scraper batch_list)
   - Output: a list of summary records (one per club_id)

2) Be safe for production:
   - Batch the request so we don't underutilise context windows.
   - Never lose raw data (raw JSONL is written by the scraper already).
   - Persist derived summaries to disk under `insta_news_data_root/derived/...`.
   - Best-effort persist to DB (`ai_summaries`) for website reads.

3) Be easy to iterate on:
   - All prompt/model config lives in one place.
   - The file name format makes it easy to re-run and compare versions.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List
from zoneinfo import ZoneInfo

from src.etl.prod import data_paths
from src.etl.prod.post_time_window import infer_summary_time_window
from src.etl.prod.prompts.system_prompts import SYSTEM_PROMPTS

from google import genai
from google.genai import types

# for the db insertion
import sqlite3

from src.etl.prod.db_insertion_tools.db_insert import db_insert_gemini_summaries


DB_PATH = os.getenv("insta_news_db_path")

# -----------------------------------------------------------------------------
# 1) Configuration
# -----------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
DEFAULT_PROMPT_NAME = os.getenv("GEMINI_SYSTEM_PROMPT", "concise_cot")


def _get_system_prompt(name: str) -> str:
    """
    Resolve a system prompt by name from `prompts/system_prompts.py`.

    Teaching note:
    - This lets you quickly try different prompt variants without touching the summariser logic.
    - If you typo the name, we fall back to "concise_cot" instead of crashing mid-run.
    """
    prompt_template = (SYSTEM_PROMPTS.get(name) or SYSTEM_PROMPTS["concise_cot"]).strip()
    # If the template includes a placeholder, inject a fresh "now" string at call time.
    # This is how your `concise_cot` prompt gets the correct CURRENT_TIME value.
    if "{current_time_str}" in prompt_template:
        melb_tz = ZoneInfo("Australia/Melbourne")
        current_time_str = datetime.now(melb_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        prompt_template = prompt_template.replace("{current_time_str}", current_time_str)
        return prompt_template
    raise ValueError(f"SYSTEM PROMPT NAME: {name} is not valid")


def _get_client():
    """
    Create a Gemini client using `genai_api_key` from the environment.

    Teaching note:
    - We keep secrets out of code and rely on `.env` + environment variables.
    - If this key is missing, we fail fast with a clear error.
    """
    api_key = os.getenv("genai_api_key")
    if not api_key:
        raise RuntimeError("Missing env var `genai_api_key` (Gemini API key).")
    return genai.Client(api_key=api_key)


def _chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    """
    Yield successive chunks from a list.

    Teaching note:
    - Chunking lets us control request size (context + cost).
    - We chunk the *posts* list; the raw file layout stays per run/day.
    """
    for i in range(0, len(items), size):
        # analogous to multiple return where the function state is paused at each yield
        yield items[i : i + size]


@dataclass(frozen=True)
class SummaryRecord:
    club_id: int
    run_date: str
    window: Dict[str, str]
    payload: Dict[str, Any]
    output_path: Path


def _summary_header_and_content(payload: Dict[str, Any]) -> tuple[str, str]:
    """
    Map model JSON to website-friendly DB columns.

    Teaching note:
    - Your `ai_summaries` table currently stores two display fields: `header` + `content`.
    - Model prompt variants return slightly different keys, so we pick sensible fallbacks.
    """
    display_header = payload.get("display_header") or {}
    if isinstance(display_header, dict):
        name = str(display_header.get("name") or "").strip()
        food_tag = str(display_header.get("food_tag") or "").strip()
        header = " ".join(part for part in [name, food_tag] if part).strip()
    else:
        header = ""

    if not header:
        header = str(payload.get("main_event") or "Club Update").strip()

    content = str(
        payload.get("summary_text")
        or payload.get("summary_paragraph")
        or payload.get("summary")
        or ""
    ).strip()
    return header, content


def db_insert(json_summary: Dict[str, Any], club_id: int) -> None:
    """
    Persist one summary to `ai_summaries` (best effort).

    Teaching note:
    - Original implementation intended to insert here but had an incomplete statement.
    - We use UPSERT on `club_id` so repeated runs update the latest summary for that club.
    - Failures are logged and ignored so ETL still writes JSON files and keeps moving.
    """
    if not DB_PATH:
        return

    header, content = _summary_header_and_content(json_summary)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO ai_summaries (club_id, header, content)
            VALUES (?, ?, ?)
            ON CONFLICT(club_id) DO UPDATE SET
              header = excluded.header,
              content = excluded.content
            """,
            (club_id, header, content),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as exc:
        print(f"[WARN] ai_summaries insert failed for club_id={club_id}: {exc}")


def gemini_summariser(
    posts_batch: List[Dict[str, Any]],
    *,
    batch_size: int = 50,
    model: str = DEFAULT_MODEL,
) -> List[SummaryRecord]:
    """
    Summarise a mixed batch of post dicts coming from the scraper.

    Expected post dict shape (minimum):
      {
        "club_id": int,
        "post_id": str,
        "caption": str,
        "date_local": str,
        "time_metadata_utc": str,
        "link": str
      }

    Behavior:
    - Groups posts by club_id (you want one summary per club, not a cross-club soup).
    - For each club, chunks posts into <= batch_size and summarises each chunk.
    - Writes each summary JSON to:
        derived/summaries/club_id=<ID>/date=<RUN_DATE>/summary_<N>.json
    - Also upserts condensed summary into DB table `ai_summaries`.
    """
    if not posts_batch:
        return []

    client = _get_client()
    paths = data_paths.get_paths()
    system_prompt = _get_system_prompt(DEFAULT_PROMPT_NAME)

    by_club: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for post in posts_batch:
        club_id = post.get("club_id")
        if club_id is None:
            # If club_id is missing, we can't route it to the right folder.
            # Skip rather than corrupting output.
            continue
        by_club[int(club_id)].append(post)

    run_date = datetime.now().date().isoformat()
    results: List[SummaryRecord] = []

    for club_id, club_posts in by_club.items():
        # Keep newest->oldest stable ordering if your scraper appended in that order.
        # If ordering matters later, you can sort by time_metadata_utc here.
        for idx, chunk in enumerate(_chunks(club_posts, batch_size), start=1):
            window = infer_summary_time_window(chunk)
            # Teaching note: we only send the fields the model needs.
            model_input = {
                "club_id": club_id,
                "posts": [
                    {
                        "post_id": p.get("post_id"),
                        "timestamp": p.get("time_metadata_utc") or p.get("date_local"),
                        "caption": p.get("caption") or "",
                        "link": p.get("link"),
                    }
                    for p in chunk
                ],
            }

            response = client.models.generate_content(
                model=model,
                contents=json.dumps(model_input, ensure_ascii=False),
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    # teaching comment: forcing JSON output makes downstream parsing reliable
                    response_mime_type="application/json",
                ),
            )

            # Response should already be JSON, but we parse to enforce correctness.
            try:
                payload = json.loads(response.text or "{}")
            except json.JSONDecodeError:
                payload = {
                    "club_id": club_id,
                    "window": window,
                    "food": {"has_food": False, "details": ""},
                    "summary": (response.text or "").strip(),
                    "source_posts": [
                        {"post_id": p.get("post_id"), "link": p.get("link")} for p in chunk
                    ],
                    "error": "model_returned_non_json",
                }

            db_insert_gemini_summaries(payload, club_id)

            payload.setdefault("club_id", club_id)
            payload.setdefault("window", window)
            payload.setdefault(
                "source_posts",
                [{"post_id": p.get("post_id"), "link": p.get("link")} for p in chunk],
            )

            out_dir = data_paths.ensure_dir(paths.summary_dir(club_id=club_id, date_yyyy_mm_dd=run_date))
            out_path = out_dir / f"summary_{idx:03d}.json"

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            results.append(
                SummaryRecord(
                    club_id=club_id,
                    run_date=run_date,
                    window=window,
                    payload=payload,
                    output_path=out_path,
                )
            )

    return results

