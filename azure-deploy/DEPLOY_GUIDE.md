# Azure Web App Deployment Guide - Browser Method

**Data Lineage Visualizer** - Complete browser-based deployment using Azure Portal

---

## ✅ Prerequisites

- Azure subscription
- Web browser
- `lineage-visualizer-azure.zip` package

---

## 📦 Step 1: Build Deployment Package

On your local machine:

```bash
cd azure-deploy
bash create-deployment-package.sh
```

This creates `lineage-visualizer-azure.zip` ready for upload.

---

## ☁️ Step 2: Create Azure Web App

1. **Open Azure Portal**: https://portal.azure.com

2. **Create Resource**:
   - Click **"+ Create a resource"**
   - Search: **"Web App"**
   - Click **"Create"**

3. **Configure**:
   - **Name**: `your-app-name` (globally unique)
   - **Runtime**: **Python 3.11**
   - **OS**: **Linux**
   - **Region**: Your preferred region
   - **Plan**: **B1 Basic** minimum ($13/month)
     - ⚠️ F1 Free tier will NOT work

4. **Create**: Wait 2-3 minutes for provisioning

---

## ⚙️ Step 3: Configure Build Automation

**CRITICAL - Do this BEFORE deploying:**

1. **Go to your Web App** → **Configuration** (left menu)

2. **Application Settings** → **+ New application setting**

3. **Add**:
   - **Name**: `SCM_DO_BUILD_DURING_DEPLOYMENT`
   - **Value**: `true`

4. **Click "OK"** → **Click "Save"** → **Continue**

This enables Azure to install Python dependencies from your ZIP file.

---

## 📤 Step 4: Deploy ZIP via Kudu (Browser)

### Method A: Kudu Zip Push Deploy UI (Recommended)

1. **Open Kudu**:
   - Azure Portal → Your Web App
   - Left menu → **Development Tools** → **Advanced Tools**
   - Click **"Go"** (opens Kudu in new tab)
   - URL will be: `https://your-app-name.scm.region.azurewebsites.net`

2. **Navigate to Deployment**:
   - In Kudu, top menu → **Tools** → **Zip Push Deploy**

3. **Upload ZIP**:
   - **Drag and drop** `lineage-visualizer-azure.zip` into the file explorer area
   - OR use the upload button to browse and select the file

4. **Monitor Deployment**:
   - Progress icon shows in top-right corner
   - Watch messages below for deployment status
   - Wait 3-5 minutes for:
     - ZIP extraction
     - Python dependency installation (pip install)
     - Virtual environment creation
     - Build completion
   - Final message: **"Deployment successful"**

---

### Method B: Azure CLI (Alternative)

If you prefer command line:

```bash
az login

az webapp config appsettings set \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true

az webapp deploy \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME \
  --src-path lineage-visualizer-azure.zip
```

---

## 🔧 Step 5: Configure Startup Command

1. **Azure Portal** → Your Web App → **Configuration**

2. **General Settings** tab

3. **Startup Command**:
   ```bash
   bash startup.sh
   ```

4. **Save** → **Continue**

---

## 🌐 Step 6: Configure Environment Variables

1. **Configuration** → **Application settings**

2. **Add these settings** (click "+ New application setting" for each):

   | Name | Value |
   |------|-------|
   | `ALLOWED_ORIGINS` | `https://your-app-name.azurewebsites.net` |
   | `PATH_WORKSPACE_FILE` | `/home/site/data/lineage_workspace.duckdb` |
   | `PATH_OUTPUT_DIR` | `/home/site/data/output` |
   | `PATH_PARQUET_DIR` | `/home/site/data/parquet` |
   | `LOG_LEVEL` | `INFO` |
   | `DEBUG_MODE` | `false` |
   | `SKIP_QUERY_LOGS` | `true` |

3. **Save** → **Continue**

---

## ✅ Step 7: Restart & Test

1. **Restart App**:
   - Azure Portal → Your Web App → **Overview**
   - Click **"Restart"** → **"Yes"**

2. **Wait 30-60 seconds** for app to start

3. **Test**:
   - **Health**: `https://your-app-name.azurewebsites.net/health`
   - **API Docs**: `https://your-app-name.azurewebsites.net/docs`
   - **App**: `https://your-app-name.azurewebsites.net`

---

## 📊 Monitor Deployment

### Check Kudu Deployment Logs

1. **Kudu** → **Deployments** (left menu)
2. Look for latest deployment
3. Status should be: **"Success (Active)"**
4. Click on deployment to see detailed logs

### Check Application Logs

1. **Azure Portal** → Your Web App → **Log stream**
2. Watch for:
   - `Starting gunicorn`
   - `Uvicorn running on 0.0.0.0:8000`
   - No error messages

---

## 🐛 Troubleshooting

### ❌ "Module not found" errors

**Cause**: Build automation not enabled

**Solution**:
1. Verify `SCM_DO_BUILD_DURING_DEPLOYMENT=true` in Configuration
2. Re-deploy the ZIP via Kudu Zip Push Deploy

### ❌ App won't start

**Cause**: Wrong startup command

**Solution**:
1. Configuration → General settings
2. Set Startup Command: `bash startup.sh`
3. Save and Restart

### ❌ Can't access Kudu

**Cause**: Network restrictions

**Solution**:
1. Configuration → Networking
2. Check SCM site is accessible

### ❌ Deployment takes too long

**Normal**: First deployment takes 3-5 minutes
- Installing Python packages
- Building dependencies
- Creating virtual environment

---

## 📝 Important Notes

### ✅ What WORKS:
- ✅ Kudu Zip Push Deploy UI (drag & drop in Kudu)
- ✅ Azure CLI `az webapp deploy`
- ✅ curl with `/api/zipdeploy` endpoint

### ❌ What DOESN'T WORK:
- ❌ Azure Portal "Deployment Center" ZIP upload (UI bug)
- ❌ Kudu file manager drag & drop (doesn't trigger build)
- ❌ FTP upload (no build automation)

### 🔑 Key Requirements:
1. **Must set** `SCM_DO_BUILD_DURING_DEPLOYMENT=true` BEFORE deploying
2. **Must use** Kudu Zip Push Deploy or API method
3. **Minimum** B1 pricing tier
4. **Linux** App Service only
5. **Python 3.11** runtime

---

## 🔄 Updating Your App

To deploy updates:

1. **Rebuild package**:
   ```bash
   bash create-deployment-package.sh
   ```

2. **Upload via Kudu**:
   - Kudu → Tools → Zip Push Deploy
   - Drag new ZIP file

3. **Wait for deployment** (usually faster, ~2 minutes)

4. **App restarts automatically**

---

## 📚 Additional Resources

- **Official Docs**: https://learn.microsoft.com/en-us/azure/app-service/deploy-zip
- **Kudu Info**: https://github.com/projectkudu/kudu/wiki
- **Python on Azure**: https://learn.microsoft.com/en-us/azure/app-service/quickstart-python
