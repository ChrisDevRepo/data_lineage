# Setup & Configuration Guide

Complete guide for installing, configuring, and deploying the Data Lineage Visualizer.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install

# 2. Start application
./start-app.sh  # Backend (8000) + Frontend (3000)
```

## Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- 8GB RAM minimum

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python lineage_v3/main.py --help
```

### Frontend Setup

```bash
cd frontend
npm install
npm run build  # Production build
```

## Configuration

**Default works out-of-the-box!** No `.env` needed for local development.

### Optional Custom Settings

```bash
# Create .env file
cp .env.example .env

# OR use interactive setup
./setup-env.sh
```

### Environment Variables

**Backend (`api/.env`):**
```bash
# Server
PORT=8000
HOST=0.0.0.0

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Data directories
DATA_DIR=./data
UPLOAD_DIR=./data/uploads
```

**Frontend (`frontend/.env`):**
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Deployment

### Azure Static Web Apps

```bash
# Build for production
cd frontend
npm run build:azure

# Deploy (manual)
az staticwebapp deploy \
  --name <app-name> \
  --resource-group <rg-name> \
  --source-path ./dist
```

### Docker

```bash
# Build image
docker build -t lineage-viz .

# Run
docker run -p 8000:8000 -p 3000:3000 lineage-viz
```

## Troubleshooting

**Port Conflicts:**
```bash
./stop-app.sh  # Kill processes on ports 3000 & 8000
```

**Missing Dependencies:**
```bash
pip install -r requirements.txt
cd frontend && npm install
```

**CORS Errors:**
Check `ALLOWED_ORIGINS` in `.env` includes your frontend URL.

See [USAGE.md](USAGE.md) for parsing and maintenance guides.
