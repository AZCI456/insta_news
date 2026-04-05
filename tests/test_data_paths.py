"""Tests for path helpers (no network, no API keys)."""

from __future__ import annotations

from pathlib import Path

from src.etl.prod.data_paths import InstaNewsPaths, _as_path, ensure_dir, get_data_root


def test_as_path_strips_quotes():
    assert _as_path('  "/tmp/foo"  ') == _as_path("/tmp/foo")


def test_get_data_root_respects_env(monkeypatch, tmp_path):
    monkeypatch.setenv("insta_news_data_root", str(tmp_path / "data"))
    root = get_data_root()
    assert root == tmp_path / "data"


def test_partitioned_paths():
    paths = InstaNewsPaths(root=Path("/data"))
    assert paths.raw_posts_jsonl_path(42, "2026-04-05") == (
        paths.root
        / "raw"
        / "instagram_posts"
        / "club_id=42"
        / "date=2026-04-05"
        / "posts.jsonl"
    )
    assert paths.summary_dir(42, "2026-04-05") == (
        paths.root / "derived" / "summaries" / "club_id=42" / "date=2026-04-05"
    )


def test_ensure_dir_creates_nested(tmp_path):
    target = tmp_path / "a" / "b"
    ensure_dir(target)
    assert target.is_dir()
