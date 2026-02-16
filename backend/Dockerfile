# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ ./src

# Set python path so it finds your modules
ENV PYTHONPATH=/app/src

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "ai_wildfire_tracker.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]