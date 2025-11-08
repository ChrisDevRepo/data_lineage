#!/bin/bash
# Azure Web App Startup Script for Data Lineage Visualizer
# This script starts the FastAPI backend server

echo "Starting Data Lineage Visualizer..."

# Install requirements (Azure does this automatically, but explicit is better)
pip install -r requirements.txt

# Start the FastAPI server
# Note: Azure Web App expects the app to bind to 0.0.0.0:8000
cd /home/site/wwwroot
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
