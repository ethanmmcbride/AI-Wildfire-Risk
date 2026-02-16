# ── Backend (FastAPI + DuckDB) ───────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (layer cached separately from source)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "ai_wildfire_tracker.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
