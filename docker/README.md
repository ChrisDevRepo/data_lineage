# Docker Container Configuration

**Status:** 🚧 **Week 2-3 Implementation** (Not yet started)

## Overview

Multi-stage Docker build combining frontend (React) and backend (FastAPI + Python) in a single container.

## Files

- `Dockerfile` - Multi-stage build configuration
- `api_main.py` - FastAPI app with static file serving
- `nginx.conf` - Nginx configuration (optional alternative)
- `.dockerignore` - Files to exclude from build

## Architecture

```
Single Container:
  ├── Frontend (React SPA) - Built in stage 1
  ├── Backend (FastAPI + Python) - Stage 2
  └── Static file serving (FastAPI or Nginx)

Routes:
  /api/* → FastAPI (port 8000)
  /* → React static files
```

## Multi-Stage Build

### Stage 1: Frontend Build
```dockerfile
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build
# Result: /frontend/dist/
```

### Stage 2: Backend + Serve
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN pip install fastapi uvicorn python-multipart
COPY lineage_v3/ ./lineage_v3/
COPY --from=frontend-build /frontend/dist ./static
COPY docker/api_main.py ./main.py
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Build & Run

```bash
# Build
docker build -t vibecoding-lineage:latest .

# Run locally
docker run -p 8000:8000 vibecoding-lineage:latest

# Test
curl http://localhost:8000/health
open http://localhost:8000
```

## Deployment

See [docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md) - Section 10 (Deployment Guide)

## System Requirements

- Base Image: `python:3.12-slim`
- RAM: 2-4 GB (4 GB recommended for concurrent users)
- CPU: 2 cores minimum
- Disk: 10 GB

## Implementation Timeline

**Week 2-3:**
- Day 9: Create Dockerfile and test local build
- Day 10: Integration testing

## Reference

See [docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md) - Section 5.6
