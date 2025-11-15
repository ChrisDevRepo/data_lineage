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
# Note: Azure Oryx may extract app to a different location
# Use current directory if WEBAPP_DIR doesn't exist
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

# Install dependencies (Oryx build is broken, so we do it here)
# requirements.txt is renamed to requirements_app.txt to avoid Oryx detection
if [ -f "requirements_app.txt" ]; then
    echo "📦 Installing Python dependencies..."
    python -m pip install --upgrade pip --quiet
    python -m pip install -r requirements_app.txt --no-cache-dir --quiet
    echo "✅ Dependencies installed"
else
    echo "⚠️  Warning: requirements_app.txt not found"
fi

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

# Don't change directory - Azure Oryx sets up the correct working directory
# If WEBAPP_DIR exists and is different from PWD, try to cd there
if [ -d "$WEBAPP_DIR" ] && [ "$PWD" != "$WEBAPP_DIR" ]; then
    echo "Changing to $WEBAPP_DIR"
    cd "$WEBAPP_DIR" || echo "Warning: Could not cd to $WEBAPP_DIR, using current directory $(pwd)"
else
    echo "Using current directory: $(pwd)"
fi

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
