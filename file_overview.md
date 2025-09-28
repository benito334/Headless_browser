# Project File Overview

A quick reference describing the purpose of each significant file / directory in this repository.  Use this as an orientation guide when onboarding or reviewing changes.

---

## Backend ‑ Core

| Path | Purpose |
|------|---------|
| `backend/__init__.py` | Adds project root to `sys.path` and creates shim so legacy `src.*` imports still resolve. |
| `backend/config.py` | Centralised environment / runtime configuration (env-vars → constants). |
| `backend/main.py` | FastAPI application entry-point. Mounts `/static`, starts AsyncIO scheduler, registers API routers, exposes `/api/health`. |
| `backend/db/db.py` | Lightweight SQLite helpers – initialises `posts` table, CRUD helpers, plus `ingested_content` metadata fetch/insert. |

## Ingestion – Instagram

| Path | Purpose |
|------|---------|
| `backend/ingestion/instagram_ingestion/instagram_scraper.py` | Headless Playwright scraper. Downloads videos, extracts duration via `ffprobe`, builds metadata dict and writes sidecar/DB row. |
| `backend/ingestion/instagram_ingestion/metadata_utils.py` | Utility: `build_metadata`, `write_sidecar`, `insert_metadata_to_db`. Ensures schema consistency. |

## Scheduler

| Path | Purpose |
|------|---------|
| `backend/ingestion/scheduler/scheduler_app.py` | Blocking scrape job logic (original). Now called asynchronously by the FastAPI scheduler wrapper. |
| `backend/ingestion/scheduler/async_bridge.py` | Thin async wrapper – runs blocking scraper in a worker thread via `asyncio.to_thread`. |

## API

| Path | Purpose |
|------|---------|
| `backend/api/routes.py` | FastAPI router: `/metadata`, `POST /ingest/instagram/{username}`, `GET /logs/ingestion/{username}`. |

## Frontend (React)

| Path | Purpose |
|------|---------|
| `frontend/src/api/client.js` | Fetch helpers: GET metadata etc. |
| `frontend/src/components/MetadataTable.jsx` | UI table listing ingested metadata; supports filtering, pagination, download & JSON view. |
| `frontend/src/components/MetadataModal.jsx` | Simple modal to show JSON sidecar. |
| `frontend/src/App.jsx` | Mounts `MetadataTable` inside basic layout. |

## Infrastructure / Ops

| Path | Purpose |
|------|---------|
| `Dockerfile` | Builds app image, installs system deps & ffmpeg, runs `uvicorn backend.main:app`. |
| `docker-compose.yml` | Single-service stack exposing port 8000, mounting `./data` volume. |
| `.env` | Runtime env-vars (target account, scrape interval, etc.). |

## Tests

| Path | Purpose |
|------|---------|
| `tests/test_static_files.py` | Integration test: seeds sample files and asserts `/static` serves them. |

## Documentation / Planning

| Path | Purpose |
|------|---------|
| `planning.md` | Roadmap & milestone tracker. |
| `file_overview.md` | **(this file)** quick reference map. |

---

## Next Steps

* Milestone 1 – remaining work:
  * ✅ Scraper & metadata done.
  * ⏳ Integrate async scheduler helper with settings UI.
  * ⏳ Expand FastAPI endpoints (start/stop/check-now) and surface logs in React UI.
* Milestone 2 – Scheduler & Settings configuration UI.
* Milestone 3+ – YouTube, PDF, ePub ingestion pipelines.
