# Azure Web App Deployment Files

This directory contains everything needed to deploy the Data Lineage Visualizer as an Azure Web App via browser-based ZIP deployment.

## 📁 Files

| File | Purpose |
|------|---------|
| `create-deployment-package.sh` | **Creates deployment ZIP** - Builds frontend, packages all files |
| `deploy-azure-cli.sh` | **Deploy via Azure CLI** - Recommended automated deployment |
| `deploy-to-azure.sh` | **Deploy via API** - Alternative deployment with curl |
| `startup.sh` | **Azure startup script** - Runs on container start (v4.2.1) |
| `INSTALL.md` | **Complete deployment guide** - Detailed step-by-step instructions |
| `QUICK_START.md` | **Quick reference** - Cheat sheet for deployment |
| `.env.example` | **Configuration template** - Shows required settings |
| `lineage-visualizer-azure.zip` | **Deployment package** - Created by script (do not commit) |

## 🚀 Quick Start

### 1. Create Deployment Package
```bash
cd azure-deploy
bash create-deployment-package.sh
```

This will:
- Build the frontend React app (`npm run build`)
- Copy backend Python code
- Create `lineage-visualizer-azure.zip` (~500KB)

### 2. Deploy to Azure

**Option A: Azure CLI (Recommended)**
```bash
bash deploy-azure-cli.sh
```
Interactive script that handles login, configuration, and deployment.

**Option B: Manual Azure CLI**
```bash
az webapp deploy \
  --resource-group your-rg \
  --name your-app-name \
  --src-path lineage-visualizer-azure.zip \
  --type zip
```

**Option C: Detailed Guide**  
Follow the step-by-step guide in **INSTALL.md** or quick reference in **QUICK_START.md**

## 📦 Package Contents

The ZIP file contains:

```
lineage-visualizer-azure.zip
├── api/                    # FastAPI backend
│   ├── main.py
│   ├── models.py
│   ├── background_tasks.py
│   └── ...
├── lineage_v3/             # Parser engine
│   ├── core/
│   ├── parsers/
│   ├── extractor/
│   └── ...
├── static/                 # Built frontend (React)
│   ├── index.html
│   └── assets/
├── requirements/           # Python dependencies
│   ├── base.txt
│   ├── parser.txt
│   └── api.txt
├── requirements.txt        # Main requirements file
├── startup.sh              # Azure startup script
├── .env.example            # Config template
└── INSTALL.md              # Installation guide
```

## 🔧 Configuration

The app requires these Azure Application Settings:

```bash
ALLOWED_ORIGINS=https://your-app-name.azurewebsites.net
PATH_WORKSPACE_FILE=/home/site/data/lineage_workspace.duckdb
PATH_OUTPUT_DIR=/home/site/data/lineage_output
PATH_PARQUET_DIR=/home/site/data/parquet_snapshots
LOG_LEVEL=INFO
DEBUG_MODE=false
SKIP_QUERY_LOGS=false
```

Set these in: **Azure Portal → Configuration → Application settings**

## 🎯 Deployment Methods

### API-Based Deployment (Required)
- **Guide:** `INSTALL.md`
- **Summary:** `QUICK_START.md`
- **Method:** curl command with deployment credentials
- **Time:** ~15 minutes
- **Prerequisites:** Terminal/command line, Azure subscription
- **⚠️ IMPORTANT:** Portal upload and drag-and-drop skip dependency installation!

### Azure CLI (Alternative)
```bash
az login
az webapp deployment source config-zip \
  --resource-group lineage-rg \
  --name your-app-name \
  --src lineage-visualizer-azure.zip \
  --build-remote true
```

Note: Add `--build-remote true` to ensure dependencies are installed!

## 📋 Deployment Checklist

- [ ] Created deployment package: `bash create-deployment-package.sh`
- [ ] Verified package size: ~650KB
- [ ] Created Azure Web App (Python 3.11, Linux, B1+)
- [ ] Uploaded ZIP via Deployment Center
- [ ] Added 7 application settings
- [ ] Set startup command: `bash startup.sh`
- [ ] Enabled file system storage
- [ ] Restarted app
- [ ] Tested `/health` endpoint
- [ ] Verified frontend loads

## ✅ Verification

### Health Check
```bash
curl https://your-app-name.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "4.0.3",
  "uptime_seconds": 123
}
```

### Frontend
```
https://your-app-name.azurewebsites.net
```

### API Docs
```
https://your-app-name.azurewebsites.net/docs
```

## 🐛 Troubleshooting

### Package creation fails
- Ensure Node.js installed: `node --version`
- Check npm dependencies: `cd frontend && npm install`
- Python 3 required for ZIP creation

### Deployment succeeds but app won't start
- Check startup command: `bash startup.sh`
- View logs: Azure Portal → Log stream
- Verify Python 3.11 or 3.12 runtime selected
- Ensure `SCM_DO_BUILD_DURING_DEPLOYMENT=true` is set

### Container exits immediately (exit code 1)
- Download logs: `az webapp log download --name your-app --resource-group your-rg --log-file logs.zip`
- Look for "cd: No such file or directory" errors
- Solution: Redeploy using latest startup.sh (fixed in v4.2.1)
- Ensure using `az webapp deploy` command, not manual portal upload

### CORS errors
- Update `ALLOWED_ORIGINS` to match your exact URL
- Include `https://` prefix
- Restart app after changing settings

## 📖 Documentation

- **INSTALL.md** - Complete deployment guide with screenshots
- **QUICK_START.md** - Quick reference for experienced users
- **.env.example** - Configuration template with descriptions
- **Startup script** - `startup.sh` (runs Gunicorn with Uvicorn workers)

## 💡 Tips

- Package size should be ~650KB (if much larger, something's wrong)
- First deployment takes 2-3 minutes
- Cold starts take ~30 seconds (normal for Azure)
- **B1 tier is the absolute minimum** ($13/month) - Free tier (F1) will NOT work
- Enable Application Insights for monitoring
- Data persists in `/home/site/data` with file system storage enabled

## 🔄 Updating

To deploy a new version:

1. Pull latest code: `git pull`
2. Rebuild package: `bash create-deployment-package.sh`
3. Deploy via Azure CLI:
   ```bash
   az webapp deploy \
     --resource-group your-rg \
     --name your-app-name \
     --src-path lineage-visualizer-azure.zip \
     --type zip
   ```
4. Wait for deployment to complete (~2 minutes)
5. Verify: Test `/health` endpoint

Configuration changes (no code update):
- Update Application settings in Azure Portal
- Restart app

## 📋 Changelog

### v4.2.1 (2025-11-15)
- **Fixed:** Startup script now handles Azure Oryx dynamic directory extraction
- **Fixed:** Container exit code 1 issue resolved
- **Improved:** Better error handling in startup.sh
- **Updated:** Documentation with troubleshooting for container exits

### v4.2.0
- Initial Azure deployment support
- Gunicorn + Uvicorn workers
- Static file serving

## 🆘 Getting Help

1. Check **INSTALL.md** troubleshooting section
2. View Azure Log Stream for errors
3. Test health endpoint: `/health`
4. Verify configuration matches `.env.example`

---

**Version:** 4.2.1  
**Target:** Azure App Service (Linux, Python 3.11/3.12)  
**Method:** ZIP Deploy via Azure CLI or Kudu  
**Last Updated:** 2025-11-15
