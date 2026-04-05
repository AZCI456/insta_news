"""
Production Gemini summariser for scraped Instagram posts.
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


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
DEFAULT_PROMPT_NAME = os.getenv("GEMINI_SYSTEM_PROMPT", "concise_cot")


def _get_system_prompt(name: str) -> str:
    """
    Resolve a system prompt by name from `prompts/system_prompts.py`.
    """
    prompt_template = (SYSTEM_PROMPTS.get(name) or SYSTEM_PROMPTS["concise_cot"]).strip()
    if "{current_time_str}" in prompt_template:
        melb_tz = ZoneInfo("Australia/Melbourne")
        current_time_str = datetime.now(melb_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        prompt_template = prompt_template.replace("{current_time_str}", current_time_str)
        return prompt_template
    raise ValueError(f"SYSTEM PROMPT NAME: {name} is not valid")


def _get_client():
    """
    Create a Gemini client using `genai_api_key` from the environment.
    """
    api_key = os.getenv("genai_api_key")
    if not api_key:
        raise RuntimeError("Missing env var `genai_api_key` (Gemini API key).")
    return genai.Client(api_key=api_key)


def _chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    """Yield successive chunks from a list."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


@dataclass(frozen=True)
class SummaryRecord:
    club_id: int
    run_date: str
    window: Dict[str, str]
    payload: Dict[str, Any]
    output_path: Path


def gemini_summariser(
    posts_batch: List[Dict[str, Any]],
    *,
    batch_size: int = 50,
    model: str = DEFAULT_MODEL,
) -> List[SummaryRecord]:
    """
    Summarise a mixed batch of post dicts coming from the scraper.
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
            continue
        by_club[int(club_id)].append(post)

    run_date = datetime.now().date().isoformat()
    results: List[SummaryRecord] = []

    for club_id, club_posts in by_club.items():
        for idx, chunk in enumerate(_chunks(club_posts, batch_size), start=1):
            window = infer_summary_time_window(chunk)
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
                    response_mime_type="application/json",
                ),
            )

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

