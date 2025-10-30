# Base image
FROM python:3.11-slim

# Keep image minimal: no compiler toolchain unless absolutely required
# If a wheel is missing and a build is needed, re-add build-essential.

# Workdir
WORKDIR /app

# Python deps first (cache-friendly)
COPY requirements.txt /app/requirements.txt
ENV PIP_NO_CACHE_DIR=1
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# App code (compose mounts volume for live-reload; copy only needed paths for initial run)
COPY src /app/src
COPY sample_papers /app/sample_papers
COPY README.md /app/README.md

# Create non-root user to avoid permission issues with volume mounts
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /cache && chmod 777 /cache && \
    mkdir -p /home/appuser && chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Default envs can be overridden by compose
ENV PYTHONUNBUFFERED=1 \
    UVICORN_RELOAD=true \
    HF_HOME=/cache \
    TRANSFORMERS_CACHE=/cache/transformers

EXPOSE 8000

# Default command (overridden in compose)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
