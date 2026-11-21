# ==============================================================================
# Multi-Stage Production Dockerfile for Universal AI Video Production Studio
# ==============================================================================
# Stage 1: Build & Dependencies
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libsndfile1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Stage 2: Final Production Runtime
FROM python:3.11-slim-bookworm AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    STUDIO_ENV=production \
    PORT=8000

# Install runtime FFmpeg, media codecs, and system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system user and group
RUN groupadd -g 10001 studio && \
    useradd -u 10001 -g studio -m -s /bin/bash appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder --chown=appuser:studio /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:studio . /app

# Ensure directories exist with correct permissions
RUN mkdir -p /app/assets /app/projects /app/temp /app/logs /app/backups && \
    chown -R appuser:studio /app/assets /app/projects /app/temp /app/logs /app/backups

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/system/telemetry || exit 1

ENTRYPOINT ["uvicorn", "departments.studio_application.api:app", "--host", "0.0.0.0", "--port", "8000"]

