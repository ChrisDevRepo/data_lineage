# Data Lineage Visualizer - Setup & Deployment Guide

**Version:** 1.0
**Last Updated:** 2025-11-06
**Target:** Production Deployment

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Running the Application](#running-the-application)
5. [Azure Deployment](#azure-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Troubleshooting Setup Issues](#troubleshooting-setup-issues)

---

## Prerequisites

### System Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Operating System** | Linux, macOS, or WSL2 | Windows via WSL2 Ubuntu recommended |
| **Python** | 3.12 or higher | Check: `python3 --version` |
| **Node.js** | 24.x or higher | Check: `node --version` |
| **npm** | 10.x or higher | Check: `npm --version` |
| **Git** | Any recent version | For cloning repository |
| **Disk Space** | 1GB free | For dependencies and DuckDB files |
| **Memory** | 4GB RAM | 8GB recommended for large datasets |

### Development Tools (Optional)

- **VS Code** - Recommended IDE
- **Python Extension** - For Python development
- **ESLint Extension** - For TypeScript linting
- **Prettier** - Code formatting

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd sandbox
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows WSL: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import duckdb, sqlglot, fastapi; print('✅ Python dependencies installed')"
```

**Expected Packages:**
- FastAPI 0.115+
- DuckDB 1.4.1
- SQLGlot 25.x
- Pydantic 2.x
- uvicorn (ASGI server)

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install

# Verify installation
npm list react react-flow-renderer monaco-editor

cd ..
```

**Expected Packages:**
- React 19.2.0
- TypeScript 5.8.2
- Vite 6.2.0
- ReactFlow 11.11.4
- Monaco Editor 4.7.0

### 4. Verify Installation

```bash
# Test parser module
python3 -c "from lineage_v3.parsers import QualityAwareParser; print('✅ Parser module OK')"

# Test frontend build
cd frontend && npm run type-check && cd ..
```

---

## Environment Configuration

### 1. Create Environment File

```bash
cp .env.template .env
```

### 2. Configure Environment Variables

Edit `.env` file:

```bash
# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Frontend Configuration
VITE_API_URL=http://localhost:8000

# CORS Configuration (Development)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Job Storage (Local Development)
JOBS_DIR=/tmp/jobs

# Parser Configuration
DEFAULT_CONFIDENCE_THRESHOLD=0.85
INCREMENTAL_PARSING_DEFAULT=true

# Logging
LOG_LEVEL=INFO
```

**Development vs Production:**

| Variable | Development | Production |
|----------|-------------|------------|
| `API_HOST` | `0.0.0.0` | `0.0.0.0` |
| `ALLOWED_ORIGINS` | `*` or `http://localhost:3000` | `https://your-frontend.azurewebsites.net` |
| `VITE_API_URL` | `http://localhost:8000` | `https://your-api.azurewebsites.net` |
| `LOG_LEVEL` | `DEBUG` or `INFO` | `WARNING` or `ERROR` |

### 3. Verify Configuration

```bash
# Check .env file exists and is not committed
ls -la .env  # Should exist
git status | grep .env  # Should NOT appear (gitignored)

# Verify environment loading
python3 -c "from dotenv import load_dotenv; load_dotenv(); print('✅ Environment loaded')"
```

---

## Running the Application

### Option 1: Automated Startup (Recommended)

```bash
# Start both backend and frontend
./start-app.sh

# Check logs
tail -f /tmp/backend.log
tail -f /tmp/frontend.log

# Stop services
./stop-app.sh
```

**What start-app.sh does:**
1. Kills existing processes on ports 3000 and 8000
2. Starts backend API in background (logs to `/tmp/backend.log`)
3. Starts frontend dev server in background (logs to `/tmp/frontend.log`)
4. Shows startup status

### Option 2: Manual Startup

#### Terminal 1 - Backend API

```bash
cd sandbox
source venv/bin/activate  # If using virtual environment
python3 api/main.py

# Expected output:
# 🚀 Data Lineage Visualizer API v4.0.3
# 📁 Jobs directory: /tmp/jobs
# 🌐 Server: http://localhost:8000
# 📚 API Docs: http://localhost:8000/docs
```

**Verify Backend:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"4.0.3"}
```

#### Terminal 2 - Frontend

```bash
cd sandbox/frontend
npm run dev

# Expected output:
# VITE v6.2.0 ready in XXX ms
# ➜ Local: http://localhost:3000
```

**Verify Frontend:**
- Open browser: http://localhost:3000
- Should see "Data Lineage Visualizer" interface

### Option 3: Production Build (Testing)

```bash
# Build frontend for production
cd frontend
npm run build  # Output: dist/

# Preview production build
npm run preview  # Opens at http://localhost:4173
```

---

## Azure Deployment

### Architecture

```
┌────────────────────────────────────────────────────┐
│ Azure Static Web Apps                              │
│ - Frontend (React build)                           │
│ - CDN distribution                                 │
│ - Custom domain support                            │
└─────────────────┬──────────────────────────────────┘
                  │
                  │ HTTPS/REST calls
                  │
┌─────────────────▼──────────────────────────────────┐
│ Azure App Service (Linux)                          │
│ - Backend API (FastAPI)                            │
│ - Python 3.12 runtime                              │
│ - Built-in authentication                          │
│ - Ephemeral storage (/tmp/jobs)                    │
└────────────────────────────────────────────────────┘
```

### Prerequisites for Azure

1. **Azure Subscription** - Active subscription
2. **Azure CLI** - Installed and authenticated (`az login`)
3. **GitHub Repository** - For deployment automation
4. **Domain (Optional)** - Custom domain for production

### Backend Deployment (Azure App Service)

#### 1. Create App Service

```bash
# Variables
RESOURCE_GROUP="rg-lineage-prod"
LOCATION="eastus"
APP_SERVICE_PLAN="asp-lineage-prod"
API_APP_NAME="lineage-api-prod"  # Must be globally unique

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan (Linux, Python 3.12)
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1  # Basic tier, upgrade to P1V2 for production

# Create Web App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $API_APP_NAME \
  --runtime "PYTHON:3.12"
```

#### 2. Configure App Settings

```bash
# Set environment variables
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    API_PORT=8000 \
    ALLOWED_ORIGINS="https://your-frontend.azurewebsites.net" \
    LOG_LEVEL="WARNING" \
    INCREMENTAL_PARSING_DEFAULT="true"
```

#### 3. Deploy Backend Code

**Option A: GitHub Actions (Recommended)**

1. Enable deployment from GitHub:
```bash
az webapp deployment source config \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --repo-url <your-github-repo-url> \
  --branch main \
  --manual-integration
```

2. Create `.github/workflows/deploy-backend.yml`:
```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'api/**'
      - 'lineage_v3/**'
      - 'requirements.txt'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: azure/webapps-deploy@v2
        with:
          app-name: 'lineage-api-prod'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

**Option B: Manual ZIP Deployment**

```bash
# Create deployment package
cd sandbox
zip -r deploy.zip api/ lineage_v3/ requirements.txt

# Deploy
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src deploy.zip
```

#### 4. Configure Startup Command

```bash
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "python3 api/main.py"
```

#### 5. Enable Application Insights (Monitoring)

```bash
az monitor app-insights component create \
  --app lineage-api-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Link to Web App
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="<connection-string>"
```

### Frontend Deployment (Azure Static Web Apps)

#### 1. Create Static Web App

```bash
STATIC_APP_NAME="lineage-frontend-prod"

az staticwebapp create \
  --name $STATIC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --source <your-github-repo-url> \
  --branch main \
  --app-location "frontend" \
  --output-location "dist" \
  --login-with-github
```

#### 2. Configure Build Settings

Create `frontend/staticwebapp.config.json`:

```json
{
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["authenticated"]
    },
    {
      "route": "/*",
      "serve": "/index.html",
      "statusCode": 200
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html"
  },
  "platform": {
    "apiRuntime": "node:18"
  }
}
```

#### 3. Update Frontend API URL

Edit `frontend/.env.production`:

```bash
VITE_API_URL=https://lineage-api-prod.azurewebsites.net
```

Rebuild frontend:
```bash
cd frontend
npm run build
```

#### 4. Configure Custom Domain (Optional)

```bash
az staticwebapp hostname set \
  --name $STATIC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname lineage.yourdomain.com
```

---

## Post-Deployment Configuration

### 1. Enable Azure Authentication

**Backend (App Service):**

```bash
# Enable Microsoft Entra ID authentication
az webapp auth update \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --enabled true \
  --action LoginWithAzureActiveDirectory \
  --aad-client-id <your-app-registration-client-id>
```

**Frontend (Static Web App):**
- Configure in Azure Portal
- Authentication → Add identity provider → Microsoft
- Require authentication for all routes

### 2. Update CORS Settings

```bash
# Backend: Allow only frontend domain
az webapp cors add \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --allowed-origins "https://lineage-frontend-prod.azurewebsites.net"

# Verify
az webapp cors show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME
```

### 3. Configure Logging

```bash
# Enable application logging
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --application-logging filesystem \
  --level warning

# Stream logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME
```

### 4. Set Up Alerts

Create alert for API health:

```bash
az monitor metrics alert create \
  --name "API Health Check Failed" \
  --resource-group $RESOURCE_GROUP \
  --scopes /subscriptions/<subscription-id>/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$API_APP_NAME \
  --condition "avg Percentage HTTP 5xx > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action <action-group-id>
```

### 5. Verify Deployment

**Backend Health Check:**
```bash
curl https://lineage-api-prod.azurewebsites.net/health
# Expected: {"status":"healthy","version":"4.0.3"}
```

**Frontend Access:**
- Navigate to https://lineage-frontend-prod.azurewebsites.net
- Verify authentication prompt appears
- After login, verify application loads

**API Docs:**
- Navigate to https://lineage-api-prod.azurewebsites.net/docs
- Verify Swagger UI loads and shows all endpoints

---

## Troubleshooting Setup Issues

### Python Dependency Errors

**Error:** `ModuleNotFoundError: No module named 'duckdb'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify
python3 -c "import duckdb; print(duckdb.__version__)"
```

### Frontend Build Failures

**Error:** `npm ERR! code ENOENT`

**Solution:**
```bash
# Clean npm cache
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Rebuild
npm run build
```

### Port Already in Use

**Error:** `Address already in use: 8000` or `3000`

**Solution:**
```bash
# Kill processes on ports
lsof -ti:8000 | xargs -r kill
lsof -ti:3000 | xargs -r kill

# Or use stop script
./stop-app.sh

# Restart
./start-app.sh
```

### Azure Deployment Failures

**Error:** `Deployment failed with status 500`

**Solution:**
```bash
# Check application logs
az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME

# Verify startup command
az webapp config show --resource-group $RESOURCE_GROUP --name $API_APP_NAME --query "linuxFxVersion"

# Restart app
az webapp restart --resource-group $RESOURCE_GROUP --name $API_APP_NAME
```

### CORS Issues After Deployment

**Error:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**
1. Verify backend CORS settings:
```bash
az webapp cors show --resource-group $RESOURCE_GROUP --name $API_APP_NAME
```

2. Update allowed origins:
```bash
az webapp cors add --resource-group $RESOURCE_GROUP --name $API_APP_NAME --allowed-origins "https://your-frontend-domain"
```

3. Ensure `allow_credentials=True` in `api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[...],
    allow_credentials=True,  # Required for Azure Auth
    ...
)
```

---

## Related Documentation

- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - Architecture and components
- [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md) - Operations and troubleshooting
- [api/README.md](../api/README.md) - Backend API documentation
- [frontend/README.md](../frontend/README.md) - Frontend guide

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Status:** ✅ Production Ready
