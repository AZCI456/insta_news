# syntax=docker/dockerfile:1

# -----------------------------------------------------------------------------
# What this file does (high level)
# -----------------------------------------------------------------------------
# 1) Start from an official Python image whose major/minor you control.
# 2) Install *this repo* with `pip install .` so dependencies come only from
#    pyproject.toml (same source of truth as local development).
# 3) Run the FastAPI app with Uvicorn (included via `fastapi[standard]` in TOML).
# -----------------------------------------------------------------------------

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

COPY . .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
