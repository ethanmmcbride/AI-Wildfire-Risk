# ── Backend (FastAPI + DuckDB) ───────────────────────────────────────────────
FROM python:3.10-slim AS backend

WORKDIR /app

# Install build deps (if any C extensions are needed later)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first for layer caching
COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

# Copy the rest of the project
COPY . .

EXPOSE 8000

CMD ["uvicorn", "ai_wildfire_tracker.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
