FROM python:3.12-slim

WORKDIR /app

# SILENCE WARNINGS: Set these environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore

# Install build-essential (quietly)
RUN apt-get update && apt-get install -y -q build-essential

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "ai_wildfire_tracker.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
