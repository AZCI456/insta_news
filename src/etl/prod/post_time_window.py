"""
Pure helpers for inferring a time window from scraped post dicts.

Teaching note:
- This module has *no* imports from Gemini or Instaloader, so unit tests can run
  on any machine without API keys or heavy dependencies.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def infer_summary_time_window(posts: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Infer [start, end] from post timestamps.

    Uses `time_metadata_utc` when present, else `date_local`. If nothing is
    available, both bounds are set to the current UTC time (ISO8601).
    """
    timestamps: List[str] = []
    for p in posts:
        ts = p.get("time_metadata_utc") or p.get("date_local")
        if ts:
            timestamps.append(ts)

    if not timestamps:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return {"start": now, "end": now}

    timestamps.sort()
    return {"start": timestamps[0], "end": timestamps[-1]}
