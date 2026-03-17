"""
etl/prod/data_paths.py

Small path utility module for production ETL.

Why this file exists
--------------------
Your scraper produces *two* kinds of artifacts:

1) Raw scraped post payloads (JSON Lines / .jsonl)
2) Derived artifacts (Gemini summaries, etc.)

Those should live outside the git repo (e.g. under /opt/insta_news_data),
and the scraper should be able to run on a fresh machine/container without
manually creating folders.

This module centralizes:
- Reading the "data root" from your `.env`
- Creating folders idempotently (safe to call every run)
- Generating consistent partitioned paths (by club_id and date)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import dotenv

dotenv.load_dotenv()

# DATA_ROOT_ENV_VAR = os.getenv("insta_news_data_root")


def _as_path(value: str) -> Path:
    """
    Convert an env var string into a Path, stripping quotes/whitespace.

    Teaching note:
    - In `.env`, values may be quoted.
    - We normalize to a real filesystem path so joins are reliable.
    """
    return Path(value.strip().strip('"').strip("'")).expanduser()


def get_data_root() -> Path:
    """
    Return the configured base folder where ETL data is stored.

    Expected `.env`:
      insta_news_data_root="/opt/insta_news_data/data/"

    If the env var is missing, we default to `/opt/insta_news_data/data` .
    """
    raw = os.getenv("insta_news_data_root", "/opt/insta_news_data/data")
    root = _as_path(raw)
    return root


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists on disk.

    Teaching note:
    - `parents=True` creates any missing parent folders.
    - `exist_ok=True` means "don't error if it's already there".
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class InstaNewsPaths:
    """
    A convenience container for the standard folder layout.

    Keeping these in one place prevents "data soup" and makes it easy to
    reprocess a club/day later.
    """

    root: Path

    @property
    def raw_root(self) -> Path:
        return self.root / "raw"

    @property
    def derived_root(self) -> Path:
        return self.root / "derived"

    @property
    def raw_instagram_posts_root(self) -> Path:
        return self.raw_root / "instagram_posts"

    @property
    def derived_summaries_root(self) -> Path:
        return self.derived_root / "summaries"

    def raw_posts_dir(self, club_id: int, date_yyyy_mm_dd: str) -> Path:
        """
        Partition raw posts by club + date:
          raw/instagram_posts/club_id=<ID>/date=YYYY-MM-DD/
        """
        return (
            self.raw_instagram_posts_root
            / f"club_id={club_id}"
            / f"date={date_yyyy_mm_dd}"
        )

    def raw_posts_jsonl_path(self, club_id: int, date_yyyy_mm_dd: str) -> Path:
        """
        The JSONL file we append raw post objects into.
        """
        return self.raw_posts_dir(club_id, date_yyyy_mm_dd) / "posts.jsonl"

    def summary_dir(self, club_id: int, date_yyyy_mm_dd: str) -> Path:
        """
        Partition summaries by club + date:
          derived/summaries/club_id=<ID>/date=YYYY-MM-DD/
        """
        return (
            self.derived_summaries_root
            / f"club_id={club_id}"
            / f"date={date_yyyy_mm_dd}"
        )


def get_paths() -> InstaNewsPaths:
    """
    Main entry point: returns an InstaNewsPaths object rooted at `insta_news_data_root`.

    Typical usage in the scraper:

      paths = get_paths()
      out_dir = ensure_dir(paths.raw_posts_dir(club_id, date_str))
      raw_jsonl = paths.raw_posts_jsonl_path(club_id, date_str)
    """
    root = get_data_root()
    # Ensure the top-level root exists so downstream ensure_dir calls can be simpler.
    ensure_dir(root)
    return InstaNewsPaths(root=root)

