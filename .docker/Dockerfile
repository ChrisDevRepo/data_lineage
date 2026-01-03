# ==============================================================================
# Data Lineage Visualizer - Production Docker Image
# ==============================================================================
# Author: Christian Wagner
# Version: 1.0.1
# License: MIT
# Purpose: Public Docker image for local production deployment
# ==============================================================================

FROM python:3.12-slim AS base

LABEL maintainer="Christian Wagner"
LABEL description="Data Lineage Visualizer - Interactive data lineage analysis for Microsoft SQL Server family"
LABEL version="1.0.1"
LABEL org.opencontainers.image.source="https://github.com/your-org/data_lineage"
LABEL org.opencontainers.image.authors="Christian Wagner"

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Python Dependencies
# ==============================================================================
COPY requirements /app/requirements

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        -r requirements/base.txt \
        -r requirements/parser.txt \
        -r requirements/api.txt

# ==============================================================================
# Application Code (Static)
# ==============================================================================
COPY api /app/api
COPY engine /app/engine
COPY LICENSE /app/LICENSE

# Copy pre-built frontend (must run `npm run build` in frontend/ first)
COPY frontend/dist /app/static

# ==============================================================================
# External Volume Setup
# ==============================================================================
RUN mkdir -p /app/config/data \
             /app/config/logs \
             /app/config/rules/defaults \
             /app/config/rules/tsql \
             /app/config/queries/tsql \
             /app/config/uploads \
             /app/config/util

# Copy defaults to image (will be copied to volume on first run if not exists)
COPY engine/rules/defaults/*.yaml /app/engine/rules/defaults/
COPY engine/rules/tsql/*.yaml /app/engine/rules/tsql/
COPY engine/connectors/queries/tsql/*.yaml /app/engine/connectors/queries/tsql/

# Copy .env.example template (required by docker-entrypoint.sh)
COPY .env.example /app/.env.example

# ==============================================================================
# Runtime Configuration
# ==============================================================================
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PATH_OUTPUT_DIR=/app/config/data \
    PATH_WORKSPACE_FILE=/app/config/data/lineage_workspace.duckdb \
    PATH_PARQUET_DIR=/app/config/data/parquet_snapshots \
    PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# ==============================================================================
# Startup
# ==============================================================================
COPY .docker/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["gunicorn", "api.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
