#!/bin/bash
# Azure Web App Startup Script for Linux
#
# Purpose: Start the static file server for the React SPA
# Platform: Linux Azure App Service (Node.js runtime)
#
# This script is referenced in Azure Portal > Configuration > Startup Command
# OR set via Azure CLI:
#   az webapp config set --startup-file "startup.sh" ...

set -e  # Exit on error

echo "======================================"
echo "Data Lineage Visualizer - Starting..."
echo "======================================"

# Environment info
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"
echo "Working directory: $(pwd)"
echo "Contents:"
ls -la

# Check if PM2 is available
if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2 globally..."
    npm install -g pm2
fi

# Verify dist folder exists
if [ ! -d "/home/site/wwwroot" ]; then
    echo "ERROR: /home/site/wwwroot not found!"
    echo "This likely means deployment failed or is incomplete."
    exit 1
fi

echo "Deployment folder contents:"
ls -la /home/site/wwwroot

# Check for index.html
if [ ! -f "/home/site/wwwroot/index.html" ]; then
    echo "WARNING: index.html not found in /home/site/wwwroot"
    echo "Deployment may be incomplete. Expected structure:"
    echo "/home/site/wwwroot/"
    echo "  ├── index.html"
    echo "  ├── assets/"
    echo "  └── ..."
fi

# Start PM2 static file server
echo "Starting PM2 server..."
pm2 serve /home/site/wwwroot \
    --port 8080 \
    --name "lineage-visualizer" \
    --spa \
    --no-daemon

# The --no-daemon flag keeps PM2 running in foreground
# This is required for Azure App Service (container must not exit)

# Note: Azure App Service expects the app to listen on port 8080 by default
# This is configured via the PORT environment variable (automatically set)
