#!/bin/bash

# Data Lineage Visualizer - Startup Script
# This script starts both frontend and backend servers

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Starting Data Lineage Visualizer                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
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
cd "$SCRIPT_DIR/api"
source ../venv/bin/activate
nohup python main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend started (PID: $BACKEND_PID)"
echo "   📋 Logs: tail -f /tmp/backend.log"
sleep 2

# Start Frontend (Vite)
echo "🎨 Starting Frontend on port 3000..."
cd "$SCRIPT_DIR/frontend"
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
echo "   📋 Logs: tail -f /tmp/frontend.log"
sleep 3

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
echo "✅ Application is starting!"
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
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
