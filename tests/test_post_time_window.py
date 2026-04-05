"""Pure logic tests (no Gemini / no google-genai import)."""

from __future__ import annotations

from src.etl.prod.post_time_window import infer_summary_time_window


def test_infer_window_sorts_iso_timestamps():
    posts = [
        {"time_metadata_utc": "2026-04-05T12:00:00+00:00"},
        {"time_metadata_utc": "2026-04-01T08:00:00+00:00"},
        {"time_metadata_utc": "2026-04-03T10:00:00+00:00"},
    ]
    w = infer_summary_time_window(posts)
    assert w["start"] == "2026-04-01T08:00:00+00:00"
    assert w["end"] == "2026-04-05T12:00:00+00:00"


def test_infer_window_falls_back_to_date_local():
    posts = [{"date_local": "2026-04-02"}]
    w = infer_summary_time_window(posts)
    assert w["start"] == "2026-04-02"
    assert w["end"] == "2026-04-02"


def test_infer_window_empty_yields_same_start_and_end():
    w = infer_summary_time_window([])
    assert w["start"] == w["end"]
    assert w["start"].startswith("20")
