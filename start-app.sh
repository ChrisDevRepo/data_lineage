#!/bin/bash

# Data Lineage Visualizer - Startup Script
# Usage: ./start-app.sh [mode]
#   mode: prod (default) - Production build for fast performance
#         dev           - Development mode with HMR

# Determine mode (default to production)
MODE="${1:-prod}"

if [ "$MODE" == "dev" ]; then
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🚀 Starting Data Lineage Visualizer (DEVELOPMENT MODE)       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
else
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🚀 Starting Data Lineage Visualizer (PRODUCTION MODE)        ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
fi
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill any existing processes on ports 3000 and 8000
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs -r kill -9 2>/dev/null
lsof -ti:3000 | xargs -r kill -9 2>/dev/null
sleep 1

# Start Backend (FastAPI)
echo "🔧 Starting Backend API on port 8000..."

# Determine Python executable to use
# Check if we're in a devcontainer (system Python with packages installed)
if [ -f "/.dockerenv" ] || [ -n "$REMOTE_CONTAINERS" ] || [ -n "$CODESPACES" ]; then
    echo "   🐳 Running in container - using system Python..."
    PYTHON_BIN="python3"
    PIP_BIN="pip3"
    PIP_FLAGS="--break-system-packages"
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "   📦 Using virtual environment (./venv)..."
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
    PIP_BIN="$SCRIPT_DIR/venv/bin/pip"
    PIP_FLAGS=""
elif [ -f "$SCRIPT_DIR/../venv/bin/activate" ]; then
    echo "   📦 Using virtual environment (../venv)..."
    PYTHON_BIN="$SCRIPT_DIR/../venv/bin/python"
    PIP_BIN="$SCRIPT_DIR/../venv/bin/pip"
    PIP_FLAGS=""
elif [ -f "$SCRIPT_DIR/api/venv/bin/activate" ]; then
    echo "   📦 Using virtual environment (./api/venv)..."
    PYTHON_BIN="$SCRIPT_DIR/api/venv/bin/python"
    PIP_BIN="$SCRIPT_DIR/api/venv/bin/pip"
    PIP_FLAGS=""
else
    echo "   ⚠️  No virtual environment found - using system Python"
    echo "   💡 Create one with: python3 -m venv $SCRIPT_DIR/venv"
    PYTHON_BIN="python3"
    PIP_BIN="pip3"
    PIP_FLAGS=""
fi

# Check if FastAPI is installed
if ! $PYTHON_BIN -c "import fastapi" 2>/dev/null; then
    echo "   ❌ FastAPI not found! Installing dependencies..."
    $PIP_BIN install -r "$SCRIPT_DIR/requirements.txt" $PIP_FLAGS -q
    echo "   ✅ Dependencies installed"
fi

cd "$SCRIPT_DIR/api"
nohup env PYTHONPATH=$SCRIPT_DIR $PYTHON_BIN main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend started (PID: $BACKEND_PID)"
echo "   📋 Logs: tail -f /tmp/backend.log"
sleep 2

# Start Frontend
cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   ❌ Node modules not found! Installing dependencies..."
    npm install
    echo "   ✅ Node dependencies installed"
fi

if [ "$MODE" == "dev" ]; then
    # Development mode with HMR
    echo "🎨 Starting Frontend in DEV mode on port 3000..."
    echo "   ⚠️  First load will take ~2 minutes for Vite compilation"
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
    echo "   📋 Logs: tail -f /tmp/frontend.log"
    sleep 3
else
    # Production mode - build and serve
    echo "🎨 Starting Frontend in PRODUCTION mode on port 3000..."

    # Build if needed
    if [ ! -d "dist" ] || [ "$2" == "--rebuild" ]; then
        echo "   🔨 Building production bundle with preview config..."
        # Build with preview mode to use localhost:8000 API
        VITE_API_URL=http://localhost:8000 npm run build > /tmp/frontend-build.log 2>&1
        if [ $? -eq 0 ]; then
            echo "   ✅ Production build complete"
        else
            echo "   ❌ Build failed! Check logs: tail -f /tmp/frontend-build.log"
            exit 1
        fi
    else
        echo "   ✅ Using existing production build (use --rebuild to force rebuild)"
    fi

    # Start production preview server
    nohup npm run preview > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
    echo "   📋 Logs: tail -f /tmp/frontend.log"
    sleep 3
fi

# Verify services are running
echo ""
echo "🔍 Verifying services..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend: http://localhost:8000 (healthy)"
else
    echo "   ❌ Backend: Failed to start"
    echo "   Check logs: tail -f /tmp/backend.log"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend: http://localhost:3000 (ready)"
else
    echo "   ⚠️  Frontend: Starting... (may take a few seconds)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$MODE" == "dev" ]; then
    echo "✅ Application is running in DEVELOPMENT MODE"
    echo ""
    echo "⚠️  Note: First page load takes ~2 minutes for Vite compilation"
    echo "   Subsequent loads are instant with HMR"
else
    echo "✅ Application is running in PRODUCTION MODE"
    echo ""
    echo "🚀 Performance: Optimized build, fast initial load (<5 seconds)"
fi
echo ""
echo "📍 Access Points:"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "📋 View Logs:"
echo "   • Backend: tail -f /tmp/backend.log"
echo "   • Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 Stop Services:"
echo "   • Run: stop-app.sh"
echo "   • Or: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "💡 Usage:"
echo "   • Production mode (default): ./start-app.sh"
echo "   • Development mode with HMR: ./start-app.sh dev"
echo "   • Force rebuild: ./start-app.sh --rebuild"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
