#!/bin/bash
# ==============================================================================
# Post-Start Script - Dev Container Startup
# ==============================================================================
# Runs every time the dev container starts
# Performs quick checks and displays helpful information
# ==============================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Data Lineage Visualizer - Dev Container Started           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ------------------------------------------------------------------------------
# Environment Information
# ------------------------------------------------------------------------------
echo "📊 Environment Info:"
echo "   Python:   $(python --version 2>&1)"
echo "   Node.js:  $(node --version 2>&1)"
echo "   npm:      $(npm --version 2>&1)"
echo "   Git:      $(git --version 2>&1)"
echo ""

# ------------------------------------------------------------------------------
# Check Python Dependencies
# ------------------------------------------------------------------------------
if python -c "import fastapi, duckdb" 2>/dev/null; then
    echo "✅ Python dependencies installed"
else
    echo "⚠️  Python dependencies not found. Run: pip install -r requirements.txt --break-system-packages"
fi

# ------------------------------------------------------------------------------
# Check Frontend Dependencies
# ------------------------------------------------------------------------------
if [ -d "frontend/node_modules" ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "⚠️  Frontend dependencies not found. Run: cd frontend && npm install"
fi

# ------------------------------------------------------------------------------
# Check .env File
# ------------------------------------------------------------------------------
if [ -f ".env" ]; then
    echo "✅ Configuration file (.env) exists"

    # Display current configuration
    echo ""
    echo "📋 Current Configuration:"
    grep -E "^(RUN_MODE|SQL_DIALECT|LOG_LEVEL|DB_ENABLED)=" .env 2>/dev/null || echo "   ℹ️  Default configuration"
else
    echo "⚠️  Configuration file (.env) not found. Copy from .env.example"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Starting application in production mode..."
echo ""

# Auto-start the application in production mode
cd /workspace
./start-app.sh > /tmp/startup.log 2>&1 &

# Wait a moment for startup
sleep 2

echo "✅ Application startup initiated"
echo ""
echo "📋 Check startup progress: tail -f /tmp/startup.log"
echo "💡 For dev mode with HMR: ./start-app.sh dev"
echo ""
