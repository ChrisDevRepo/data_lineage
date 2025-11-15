#!/bin/bash
# ==============================================================================
# Azure Web App Startup Script for Data Lineage Visualizer
# ==============================================================================
# This script is executed when the Azure Web App container starts.
# It runs the FastAPI backend using Gunicorn with Uvicorn workers.
# The frontend is served as static files by FastAPI.
# ==============================================================================

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Data Lineage Visualizer - Azure Web App Startup          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Azure Web App defaults
WEBAPP_DIR="${HOME}/site/wwwroot"
DATA_DIR="${HOME}/site/data"

echo "📁 Working Directory: $WEBAPP_DIR"
echo "💾 Data Directory: $DATA_DIR"

# Create data directory if it doesn't exist (for persistent storage)
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/lineage_output"
mkdir -p "$DATA_DIR/parquet_snapshots"

# Set Python path to include the app directory
export PYTHONPATH="${WEBAPP_DIR}:${PYTHONPATH}"

# Azure Web App uses port 8000 by default (or PORT env var if set)
PORT="${PORT:-8000}"
echo "🌐 Server Port: $PORT"

# Log environment info
echo ""
echo "🔍 Environment Check:"
echo "   Python: $(python --version)"
echo "   Working Dir: $(pwd)"
echo "   PYTHONPATH: $PYTHONPATH"
echo ""

# Start the application with Gunicorn
echo "🚀 Starting FastAPI application with Gunicorn..."
echo ""

cd "$WEBAPP_DIR"

# Use Gunicorn with Uvicorn workers for production
# - 4 workers for parallel request handling
# - Uvicorn worker for async FastAPI support
# - Bind to 0.0.0.0:8000 (Azure default)
# - Timeout 120s for long-running parsing jobs
# - Access logs for monitoring
exec gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
