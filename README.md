# AI Wildfire Tracker

Foundation scaffold for a Python-based AI Wildfire Tracker. This repo focuses on the early planning structure plus minimal starter code. The frontend will use React + Leaflet (JS/CSS and any other needed frontend languages) to visualize live data from the backend.

## Project goals (draft)
- Track active wildfires and potential ignition risk areas.
- Ingest authoritative datasets, standardize them, and surface alerts.
- Provide a simple API/UI for queries and monitoring.
- Support model experimentation without locking into one stack.

## To-do list

### 0) Product scope
- Define primary user(s): emergency management, researchers, or public.
- Define outputs: alerts, risk heatmaps, incident summaries, or API access.
- Decide geography: global vs. specific region (e.g., US-only).

### 1) Data sources
- Pick authoritative sources for:
  - Active fire detections (e.g., satellite hotspot feeds)
  - Weather and fuel conditions
  - Historical fire perimeters/incidents
  - Land cover / vegetation indices
- Define update cadence per source.
- Document licensing and attribution requirements.

### 2) Data pipeline
- Specify ingestion approach (polling, webhooks, batch snapshots).
- Define canonical schema for detections/incidents.
- Build basic validation + deduping rules.
- Decide on spatial indexing strategy.

### 3) Storage
- Choose storage layers:
  - Raw data (object storage)
  - Curated tables (Postgres + PostGIS, or DuckDB for MVP)
  - Time series (optional)
- Define retention policy.

### 4) Models / analytics
- Start with simple baselines (rules + heuristics).
- Add ML experiments only after baseline is stable.
- Decide evaluation metrics (precision/recall, alert lead time, false positives).

### 5) Serving + alerts
- Decide on output channels (email, SMS, webhook, dashboard).
- Define alert thresholds and suppression rules.
- Build minimal API endpoints for current events + risk.

### 6) UX
- Determine minimal dashboard features:
  - Map with recent detections
  - Filters by time/region/severity
  - Alert history
- Decide frontend stack details:
  - React + Leaflet for the map
  - JS/CSS (and any other required frontend tooling)

### 7) Ops
- Define deployment target (local, cloud, container).
- Add monitoring + logs.
- Set up CI for lint/test.

## Suggested milestones
1. **MVP-0**: Ingest 1 fire detection dataset; store and query recent detections.
2. **MVP-1**: Minimal API serving recent detections + simple alert rule.
3. **MVP-2**: Add weather + fuel layers; generate basic risk scores.
4. **MVP-3**: First UI map (React + Leaflet) + alert history.

## Repository layout
```
src/ai_wildfire_tracker/
  ingest/         # data source connectors
  features/       # feature building + normalization
  models/         # model training + scoring
  alerts/         # alert rules + delivery
  api/            # API layer
  storage/        # storage adapters
  utils/          # shared utilities
frontend/         # React + Leaflet app (JS/CSS)
main.py           # CLI entry point
```

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py --help
```

## Notes
- Add dependencies to `pyproject.toml` once stack decisions are made.
- Prefer lightweight MVP choices (DuckDB + FastAPI) unless scaling is required.
