# Base image
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Python deps first (cache-friendly)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# App code (compose mounts volume for live-reload, but copying helps initial build)
COPY . /app

# Default envs can be overridden by compose
ENV PYTHONUNBUFFERED=1 \
    UVICORN_RELOAD=true

EXPOSE 8000

# Default command (overridden in compose)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
