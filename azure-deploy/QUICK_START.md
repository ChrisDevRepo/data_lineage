# Azure Web App Deployment - Quick Reference

## 📋 Pre-Flight Checklist

Before you start:
- [ ] Azure subscription active
- [ ] Credit card/payment method configured
- [ ] Decided on app name (must be globally unique)
- [ ] Know which region to deploy to (e.g., East US, West Europe)

## 🚀 Deployment Steps Summary

### 1. Create Deployment Package (5 min)
```bash
cd azure-deploy
bash create-deployment-package.sh
```
**Output:** `lineage-visualizer-azure.zip` (650KB)

### 2. Create Azure Web App (3 min)
- Portal: https://portal.azure.com
- Create Resource → Web App
- Settings:
  - **Name:** `your-unique-name`
  - **Runtime:** Python 3.11
  - **OS:** Linux
  - **Tier:** B1 ($13/mo minimum)

### 3. Deploy ZIP File (3 min)
**IMPORTANT:** Use curl method to trigger proper build (drag-and-drop skips dependency installation!)

Get deployment credentials:
- App Service → Deployment Center → FTPS credentials tab
- Copy username (e.g., `$chwa-datalineage`) and password

Run from your local terminal:
```bash
cd azure-deploy

curl -X POST \
  'https://YOUR-APP-NAME.scm.REGION.azurewebsites.net/api/zipdeploy?isAsync=true' \
  -u '$YOUR-APP-NAME:YOUR_PASSWORD' \
  -H "Content-Type: application/zip" \
  --data-binary @lineage-visualizer-azure.zip
```

Wait for deployment (check Deployments in Kudu for status)

### 4. Configure Environment Variables (3 min)
Configuration → Application settings → Add 7 environment variables:

```
ALLOWED_ORIGINS=https://your-app-name.azurewebsites.net
PATH_WORKSPACE_FILE=/home/site/data/lineage_workspace.duckdb
PATH_OUTPUT_DIR=/home/site/data/lineage_output
PATH_PARQUET_DIR=/home/site/data/parquet_snapshots
LOG_LEVEL=INFO
DEBUG_MODE=false
SKIP_QUERY_LOGS=false
```

**Note:** "Application settings" in Azure = Environment variables for your app

### 5. Configure Startup (1 min)
- Configuration → General settings
- Startup Command: `bash startup.sh`
- File system storage: **On**

### 6. Restart & Test (1 min)
- Overview → Restart
- Test: `https://your-app-name.azurewebsites.net/health`

---

## 🔧 Required Environment Variables

**Set in:** Configuration → Application settings

| Setting | Your Value | Example |
|---------|------------|---------|
| `ALLOWED_ORIGINS` | `https://_____.azurewebsites.net` | `https://mylineage.azurewebsites.net` |
| `PATH_WORKSPACE_FILE` | `/home/site/data/lineage_workspace.duckdb` | (use as-is) |
| `PATH_OUTPUT_DIR` | `/home/site/data/lineage_output` | (use as-is) |
| `PATH_PARQUET_DIR` | `/home/site/data/parquet_snapshots` | (use as-is) |
| `LOG_LEVEL` | `INFO` | (use as-is) |
| `DEBUG_MODE` | `false` | (use as-is) |
| `SKIP_QUERY_LOGS` | `false` | (use as-is) |

---

## ✅ Verification Steps

### Test 1: Health Check
```
URL: https://your-app-name.azurewebsites.net/health
Expected: {"status": "ok", "version": "4.0.3", ...}
```

### Test 2: Frontend
```
URL: https://your-app-name.azurewebsites.net
Expected: Data Lineage Visualizer interface loads
```

### Test 3: API Docs
```
URL: https://your-app-name.azurewebsites.net/docs
Expected: Swagger UI with API endpoints
```

---

## 🔄 Deployment & Updates

### Deploy via Azure CLI (Recommended)
```bash
az webapp deploy \
  --resource-group your-rg \
  --name your-app-name \
  --src-path lineage-visualizer-azure.zip \
  --type zip
```

### Alternative: Kudu Zip Push Deploy
- Kudu → Tools → Zip Push Deploy → Drag ZIP file

**Note:** Azure CLI deployment is more reliable and provides better logging.

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Container exits (code 1) | Download logs, check for path errors, redeploy with `az webapp deploy` |
| uvicorn.workers not found | Set `SCM_DO_BUILD_DURING_DEPLOYMENT=true`, redeploy |
| HTTP 503 | Check startup command: `bash startup.sh` |
| 404 on frontend | Verify static files in ZIP, redeploy |
| CORS errors | Fix `ALLOWED_ORIGINS` to match exact URL |
| Slow first load | Normal - Azure cold start (~30 sec) |
| "cd: No such file" error | Update to latest startup.sh (v4.2.1+) |

---

## 📱 Azure Portal Quick Links

- **Home:** https://portal.azure.com
- **App Services:** Portal → App Services → Your App
- **Configuration:** Your App → Configuration
- **Deployment Center:** Your App → Deployment Center
- **Log Stream:** Your App → Log stream
- **Advanced Tools (Kudu):** Your App → Advanced Tools → Go

---

## 💰 Cost Estimate

| Tier | Monthly Cost | When to Use |
|------|--------------|-------------|
| B1 (Basic) | ~$13 | **Minimum required** - Development, testing, low traffic |
| S1 (Standard) | ~$70 | Production, medium traffic |
| P1V2 (Premium) | ~$117 | High traffic, advanced features |

**Free Tier (F1):** ❌ **Will NOT work** - insufficient memory and CPU for parsing operations

---

## 📞 Support

- **Full Guide:** `INSTALL.md` (detailed step-by-step)
- **Azure Docs:** https://docs.microsoft.com/azure/app-service/
- **Logs:** Azure Portal → Your App → Log stream

---

**Last Updated:** November 15, 2025  
**For:** Data Lineage Visualizer v4.2.1
