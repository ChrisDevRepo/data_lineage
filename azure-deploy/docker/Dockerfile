FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements /app/requirements

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        -r requirements/base.txt \
        -r requirements/parser.txt \
        -r requirements/api.txt

# Copy application code
COPY api /app/api
COPY lineage_v3 /app/lineage_v3

# Copy frontend build (must be built before Docker build)
COPY frontend/dist /app/static

# Create data directory for DuckDB and uploads
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH_OUTPUT_DIR=/app/data
ENV PORT=8000
ENV ALLOWED_ORIGINS=*

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run application with Gunicorn
CMD ["gunicorn", "api.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
