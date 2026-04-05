"""Smoke tests for the FastAPI app (cheap confidence checks)."""

from __future__ import annotations


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.text.strip() == "OK"


def test_homepage_renders(client):
    """Regression: Starlette 1.x TemplateResponse(request, name, context) order."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
