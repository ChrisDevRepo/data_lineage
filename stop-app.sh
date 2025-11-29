#!/bin/bash

# Data Lineage Visualizer - Stop Script
# This script stops both frontend and backend servers

echo "🛑 Stopping Data Lineage Visualizer..."
echo ""

# Kill processes on ports 3000 and 8000
echo "Stopping Backend (port 8000)..."
lsof -ti:8000 | xargs -r kill -9 2>/dev/null && echo "   ✅ Backend stopped" || echo "   ⚠️  No backend process found"

echo "Stopping Frontend (port 3000)..."
lsof -ti:3000 | xargs -r kill -9 2>/dev/null && echo "   ✅ Frontend stopped" || echo "   ⚠️  No frontend process found"

echo ""
echo "✅ All services stopped!"
