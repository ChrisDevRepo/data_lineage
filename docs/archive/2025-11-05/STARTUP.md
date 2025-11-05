# Data Lineage Visualizer - Quick Start Guide

## Starting the Application

### Option 1: Using the Startup Script (Recommended)

```bash
cd /home/chris/sandbox
./start-app.sh
```

This will:
- ✅ Kill any existing processes on ports 3000 and 8000
- ✅ Start the backend API on port 8000
- ✅ Start the frontend on port 3000
- ✅ Verify both services are running

### Option 2: Manual Start (Step by Step)

#### Start Backend:
```bash
cd /home/chris/sandbox/api
source /home/chris/sandbox/venv/bin/activate
python main.py
```

#### Start Frontend (in a new terminal):
```bash
cd /home/chris/sandbox/frontend
npm run dev
```

---

## Stopping the Application

### Using the Stop Script:
```bash
cd /home/chris/sandbox
./stop-app.sh
```

### Manual Stop:
```bash
# Kill backend
lsof -ti:8000 | xargs kill -9

# Kill frontend
lsof -ti:3000 | xargs kill -9
```

---

## Access Points

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Viewing Logs

```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i:8000

# Check what's using port 3000
lsof -i:3000

# Kill processes
./stop-app.sh
```

### Backend Not Starting
```bash
# Check if virtual environment is activated
source /home/chris/sandbox/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Check logs
tail -f /tmp/backend.log
```

### Frontend Not Starting
```bash
# Install dependencies
cd /home/chris/sandbox/frontend
npm install

# Check logs
tail -f /tmp/frontend.log
```

---

## Directory Structure

```
/home/chris/sandbox/
├── start-app.sh          # Start both services
├── stop-app.sh           # Stop both services
├── api/                  # Backend (FastAPI)
├── frontend/             # Frontend (React + Vite)
├── parquet_snapshots/    # Place parquet files here
├── venv/                 # Python virtual environment
└── STARTUP.md           # This file
```

---

## Parquet File Upload

1. Copy your parquet files to `/home/chris/sandbox/parquet_snapshots/`
2. Open http://localhost:3000
3. Click "Import Data"
4. Select "Parquet Upload" tab
5. Choose files and click "Upload and Parse"

---

## Quick Commands Cheat Sheet

```bash
# Start everything
./start-app.sh

# Stop everything
./stop-app.sh

# Check status
curl http://localhost:8000/health
curl http://localhost:3000

# View logs
tail -f /tmp/backend.log
tail -f /tmp/frontend.log
```
