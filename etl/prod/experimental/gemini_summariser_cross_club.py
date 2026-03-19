"""
etl/prod/experimental/gemini_summariser_cross_club.py

Cross-club batching approach (your original plan):
- Send ~50 posts total to Gemini in one request (posts from many clubs mixed together).
- Ask Gemini to "route" posts by club_id and return one summary per club_id.

Why this is experimental
------------------------
This can reduce request count dramatically when you have a low daily request quota.
However, it increases risk:
- The model may mis-group posts (wrong club_id) or omit clubs.
- Harder to deterministically verify correctness vs doing grouping in Python.

This module is intentionally not wired into `insta_scraper_prod.py` yet.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import data_paths


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")


# A dedicated prompt for "routing" many clubs in one call.
SYSTEM_PROMPT_CROSS_CLUB = """
You are a careful data extraction assistant for university students.

You will receive a JSON object with a list of Instagram posts from MANY university clubs.
Each post includes a club_id that must be treated as ground-truth.

Your job:
1) Group posts by club_id.
2) For each club_id, extract event information students care about (especially free food).
3) Be concise and do NOT guess. If details are missing, omit them.
4) Ignore posts that are not announcements/events.

Return STRICT JSON (no markdown). Schema:
{
  "run_date": "<YYYY-MM-DD>",
  "clubs": [
    {
      "club_id": <int>,
      "food": { "has_food": <true|false>, "details": "<string or empty>" },
      "summary": "<string>",
      "source_posts": [{"post_id": "<string>", "link": "<string>"}]
    }
  ]
}

Rules:
- Every output club_id MUST be one of the input club_ids.
- Do not invent post_ids or links.
""".strip()


def _get_client():
    """
    Create a Gemini client using `genai_api_key` from the environment.

    Teaching note:
    - We import lazily so this module can be imported without `google-genai` installed.
    """
    try:
        from google import genai  # type: ignore
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Missing dependency `google-genai`.\n"
            "Install it with: pip install -r etl/prod/requirements.txt"
        ) from e

    api_key = os.getenv("genai_api_key")
    if not api_key:
        raise RuntimeError("Missing env var `genai_api_key` (Gemini API key).")
    return genai.Client(api_key=api_key)


@dataclass(frozen=True)
class CrossClubBatchResult:
    run_date: str
    output_path: Path
    payload: Dict[str, Any]


def gemini_summariser_cross_club(
    posts_batch: List[Dict[str, Any]],
    *,
    max_posts_per_request: int = 50,
    model: str = DEFAULT_MODEL,
    output_subdir: str = "derived/summaries/batches",
) -> Optional[CrossClubBatchResult]:
    """
    Send up to `max_posts_per_request` posts (across many clubs) in one Gemini request.

    Output is written as one JSON file per batch under:
      <insta_news_data_root>/<output_subdir>/date=<RUN_DATE>/batch_<timestamp>.json
    """
    if not posts_batch:
        return None

    # Keep this function strict: it only handles one request worth of posts.
    chunk = posts_batch[:max_posts_per_request]

    # Minimal payload: keep tokens low.
    model_input = {
        "posts": [
            {
                "club_id": p.get("club_id"),
                "username": p.get("username"),
                "post_id": p.get("post_id"),
                "timestamp": p.get("time_metadata_utc") or p.get("date_local"),
                "caption": p.get("caption") or "",
                "link": p.get("link"),
            }
            for p in chunk
        ]
    }

    # Lazy import for types config.
    try:
        from google.genai import types  # type: ignore
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Missing dependency `google-genai`.\n"
            "Install it with: pip install -r etl/prod/requirements.txt"
        ) from e

    client = _get_client()
    run_date = datetime.now().date().isoformat()

    response = client.models.generate_content(
        model=model,
        contents=json.dumps(model_input, ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_CROSS_CLUB,
            response_mime_type="application/json",
        ),
    )

    try:
        payload = json.loads(response.text or "{}")
    except json.JSONDecodeError:
        payload = {"run_date": run_date, "clubs": [], "raw_text": (response.text or "").strip()}

    # Persist a single batch file (you can fan-out per club later if you want).
    paths = data_paths.get_paths()
    out_dir = data_paths.ensure_dir(paths.root / output_subdir / f"date={run_date}")
    out_path = out_dir / f"batch_{datetime.now().strftime('%H%M%S')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return CrossClubBatchResult(run_date=run_date, output_path=out_path, payload=payload)

