# Azure Web App Deployment Guide
**Data Lineage Visualizer v4.2.0**

---

## 📦 Quick Deploy (15 minutes via Browser)

### **Prerequisites**
- Active Azure subscription
- Web browser (Chrome, Edge, Firefox, Safari)
- Deployment package: `lineage-visualizer-azure.zip`

---

## 🚀 Deployment Steps (Azure Portal)

### **Step 1: Create Deployment Package**

On your local machine:

```bash
cd azure-deploy
bash create-deployment-package.sh
```

This will:
- Build the frontend (React + Vite)
- Package backend Python code
- Create `lineage-visualizer-azure.zip` (~10MB)

**✅ Result:** `azure-deploy/lineage-visualizer-azure.zip` is ready

---

### **Step 2: Create Azure Web App**

1. **Open Azure Portal**
   - Navigate to: https://portal.azure.com
   - Sign in with your Azure account

2. **Create New Resource**
   - Click **"+ Create a resource"** (top left)
   - Search for: **"Web App"**
   - Click **"Create"**

3. **Configure Basic Settings**
   
   **Project Details:**
   - **Subscription:** Select your subscription
   - **Resource Group:** Create new or select existing (e.g., `lineage-rg`)
   
   **Instance Details:**
   - **Name:** `your-app-name` (must be globally unique)
     - ✅ This will be your URL: `https://your-app-name.azurewebsites.net`
   - **Publish:** Select **"Code"**
   - **Runtime stack:** Select **"Python 3.11"**
   - **Operating System:** Select **"Linux"**
   - **Region:** Select closest region (e.g., `East US`)
   
   **Pricing Plan:**
   - Click **"Create new"** under App Service Plan
   - Name: `lineage-plan`
   - **Pricing Tier:** Click **"Explore pricing plans"**
     - **Minimum Required: B1 (Basic)** - $13/month
     - Recommended: **B1 (Basic)** - Good for dev/test
     - Production: **S1 (Standard)** - $70/month
     - ⚠️ **Free tier (F1) will NOT work** - insufficient memory/CPU

4. **Review + Create**
   - Click **"Review + create"**
   - Verify all settings
   - Click **"Create"**
   - Wait 2-3 minutes for deployment to complete

**✅ Result:** Web App created (currently empty)

---

### 3. Deploy ZIP File via API (Required Method)

**⚠️ CRITICAL:** Do NOT use Azure Portal drag-and-drop or Kudu file upload - they skip dependency installation!

**Get Deployment Credentials:**

1. **Azure Portal** → Your Web App → **Deployment Center**
2. Click **"FTPS credentials"** tab
3. Under **"Application scope"**:
   - Username: `$your-app-name` (copy this)
   - Password: Click **"Show"** and copy the password

**Deploy via curl:**

Open your **local terminal** and run:

```bash
# Navigate to azure-deploy folder
cd /path/to/data_lineage/azure-deploy

# Deploy with proper build
curl -X POST \
  'https://YOUR-APP-NAME.scm.REGION.azurewebsites.net/api/zipdeploy?isAsync=true' \
  -u '$YOUR-APP-NAME:YOUR_PASSWORD_HERE' \
  -H "Content-Type: application/zip" \
  --data-binary @lineage-visualizer-azure.zip
```

**Example:**
```bash
curl -X POST \
  'https://chwa-datalineage.scm.swedencentral-01.azurewebsites.net/api/zipdeploy?isAsync=true' \
  -u '$chwa-datalineage:abcd1234XyZ...' \
  -H "Content-Type: application/zip" \
  --data-binary @lineage-visualizer-azure.zip
```

**Response:** You'll get a deployment URL. The build takes 3-5 minutes.

**Monitor Progress:**
- Kudu → Click **"Deployments"** link
- Watch the build status
- Look for "Success (Active)" status

---

### **Step 4: Configure Application Settings**

1. **Open Configuration**
   - In left menu, click **"Configuration"** (under Settings)

2. **Add Application Settings**
   - Click **"+ New application setting"** button
   - Add each setting below:

   | Name | Value | Description |
   |------|-------|-------------|
   | `ALLOWED_ORIGINS` | `https://your-app-name.azurewebsites.net` | ⚠️ Replace with YOUR actual URL |
   | `PATH_WORKSPACE_FILE` | `/home/site/data/lineage_workspace.duckdb` | Database path |
   | `PATH_OUTPUT_DIR` | `/home/site/data/lineage_output` | Output directory |
   | `PATH_PARQUET_DIR` | `/home/site/data/parquet_snapshots` | Parquet storage |
   | `LOG_LEVEL` | `INFO` | Logging level |
   | `DEBUG_MODE` | `false` | Disable debug mode |
   | `SKIP_QUERY_LOGS` | `false` | Enable query log parsing |

   **For each setting:**
   - Click **"+ New application setting"**
   - Enter **Name** and **Value**
   - Click **"OK"**
   - Repeat for all 7 settings

3. **Save Changes**
   - Click **"Save"** button at the top
   - Click **"Continue"** in confirmation dialog
   - Wait for settings to update (~30 seconds)

**✅ Result:** Environment variables configured

---

### **Step 5: Configure Startup Command**

1. **Open General Settings**
   - Still in **"Configuration"** page
   - Click **"General settings"** tab (at the top)

2. **Set Startup Command**
   - Scroll down to **"Startup Command"** field
   - Enter: `bash startup.sh`
   - Leave other settings as default

3. **Enable Persistent Storage**
   - Find **"File system storage"** setting
   - Toggle to **"On"** (this enables `/home/site/data` persistence)

4. **Save Changes**
   - Click **"Save"** at the top
   - Click **"Continue"** in confirmation dialog

**✅ Result:** Startup configuration complete

---

### **Step 6: Restart Application**

1. **Navigate to Overview**
   - In left menu, click **"Overview"** (at the top)

2. **Restart Web App**
   - Click **"Restart"** button at the top
   - Click **"Yes"** in confirmation dialog
   - Wait 1-2 minutes for restart

**✅ Result:** Application restarted with new configuration

---

### **Step 7: Verify Deployment**

1. **Check Health Endpoint**
   - Copy your app URL: `https://your-app-name.azurewebsites.net`
   - In browser, navigate to: `https://your-app-name.azurewebsites.net/health`
   - **Expected response:**
     ```json
     {
       "status": "ok",
       "version": "4.0.3",
       "uptime_seconds": 123
     }
     ```

2. **Access Frontend**
   - Navigate to: `https://your-app-name.azurewebsites.net`
   - You should see the Data Lineage Visualizer interface
   - Initially no data will be shown (upload Parquet files first)

3. **Test API Documentation**
   - Navigate to: `https://your-app-name.azurewebsites.net/docs`
   - You should see interactive API documentation (Swagger UI)

4. **Monitor Logs (Optional)**
   - In Azure Portal, left menu, click **"Log stream"**
   - You'll see real-time application logs
   - Look for: `🚀 Data Lineage Visualizer API v4.0.3`

**✅ Result:** Deployment verified and working!

---

### **Step 8: Upload Data (First Use)**

1. **Open Application**
   - Navigate to: `https://your-app-name.azurewebsites.net`

2. **Upload Parquet Files**
   - Click **"Upload Data"** button
   - Select your Parquet files:
     - `objects.parquet` (required)
     - `dependencies.parquet` (required)
     - `definitions.parquet` (required)
     - `query_logs.parquet` (optional)
     - `table_columns.parquet` (optional)
   - Click **"Start Processing"**

3. **Wait for Processing**
   - Progress bar will show parsing status
   - Typically takes 2-5 minutes
   - When complete, lineage graph will appear

**✅ Result:** Your data is now visualized!

---

## 🔧 Configuration Reference

### **Required Application Settings**
| Setting | Value | Description |
|---------|-------|-------------|
| `ALLOWED_ORIGINS` | `https://your-app.azurewebsites.net` | CORS - MUST match your actual URL |
| `PATH_WORKSPACE_FILE` | `/home/site/data/lineage_workspace.duckdb` | DuckDB database path |
| `PATH_OUTPUT_DIR` | `/home/site/data/lineage_output` | Lineage output directory |

### **Optional Settings**
| Setting | Default | Description |
|---------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging: DEBUG, INFO, WARNING, ERROR |
| `DEBUG_MODE` | `false` | Enable debug features |
| `SKIP_QUERY_LOGS` | `false` | Skip query log parsing |

### **Pricing Tiers**
- **B1 (Basic):** $13/month - Minimum required, good for development/testing
- **S1 (Standard):** $70/month - Recommended for production
- **P1V2 (Premium):** $117/month - High performance, multiple instances
- **F1 (Free):** ❌ Not supported - insufficient resources for parsing workloads

---

## 🐛 Troubleshooting

### **App won't start (HTTP 503)**

1. **Check Startup Command**
   - Configuration > General settings
   - Should be: `bash startup.sh`
   - Save and restart

2. **View Logs**
   - Log stream (in Azure Portal)
   - Look for Python import errors
   - Verify `gunicorn` is starting

3. **Common Issues**
   - ❌ Startup command missing → Set `bash startup.sh`
   - ❌ Python version wrong → Use Python 3.11
   - ❌ Dependencies not installed → Redeploy ZIP

### **Frontend shows 404**

1. **Verify Static Files**
   - Go to: Advanced Tools > Go → Opens Kudu console
   - Navigate to: `/home/site/wwwroot/static`
   - Should contain: `index.html`, `assets/`
   
2. **If Missing**
   - Rebuild deployment package
   - Ensure `npm run build` completed successfully
   - Redeploy ZIP file

### **API returns 500 errors**

1. **Check Environment Variables**
   - Configuration > Application settings
   - Verify `ALLOWED_ORIGINS` matches your URL exactly
   - Should include `https://` prefix

2. **View Error Logs**
   - Log stream shows stack traces
   - Common: CORS errors, database connection issues

### **CORS errors in browser console**

**Symptom:** Browser shows: `Access to fetch at '...' has been blocked by CORS policy`

**Fix:**
1. Configuration > Application settings
2. Find `ALLOWED_ORIGINS` setting
3. Update value to: `https://your-app-name.azurewebsites.net`
   - ⚠️ Must match EXACTLY (including `https://`)
   - ❌ Don't use wildcards in production (`*`)
4. Save and restart app

### **Deployment package too large**

**Symptom:** Upload fails or takes too long

**Fix:**
1. Check package size: `du -h lineage-visualizer-azure.zip`
2. Should be ~10-15MB
3. If larger, check for:
   - `node_modules/` in package (should be excluded)
   - `.git/` directory (should be excluded)
4. Rebuild package with `create-deployment-package.sh`

---

## 📊 Monitoring & Maintenance

### **View Application Logs**
1. Azure Portal > Your Web App
2. **Log stream** (left menu) - Real-time logs
3. **Monitoring > Logs** - Query historical logs

### **Performance Monitoring**
1. Enable **Application Insights** (recommended)
   - Monitoring > Application Insights
   - Click "Turn on Application Insights"
   - Creates automatic monitoring dashboard

### **Scale Application**
1. **Scale Up (Bigger Instance)**
   - Settings > Scale up (App Service plan)
   - Choose higher tier: S1, S2, S3, P1V2, etc.

2. **Scale Out (More Instances)**
   - Settings > Scale out (App Service plan)
   - Increase instance count: 2, 3, 4, etc.
   - Enables load balancing

### **Backup Data**
- Data in `/home/site/data` persists across restarts
- Consider periodic backups of `lineage_workspace.duckdb`
- Use Azure Storage for long-term retention

---

## 🔒 Security Checklist

Before going to production:

- ✅ Set `DEBUG_MODE=false` (never true in production)
- ✅ Configure `ALLOWED_ORIGINS` to exact URL (no wildcards)
- ✅ Use HTTPS only (Azure default - don't disable)
- ✅ Review who has access to Azure Portal
- ✅ Enable Application Insights for monitoring
- ✅ Set up automated backups if using paid tier
- ✅ Consider Azure AD authentication for sensitive data
- ✅ Review App Service authentication settings

---

## 📂 Package Contents

The deployment ZIP contains:

```
lineage-visualizer-azure.zip
├── api/                        # FastAPI backend
│   ├── main.py                 # API entry point
│   ├── models.py               # Response models
│   └── background_tasks.py     # Job processing
├── lineage_v3/                 # Parser engine
│   ├── core/                   # DuckDB workspace
│   ├── parsers/                # SQL parsers
│   └── extractor/              # Lineage extraction
├── static/                     # React frontend (built)
│   ├── index.html              # Entry page
│   └── assets/                 # JS, CSS, images
├── requirements/               # Python dependencies
│   ├── base.txt
│   ├── parser.txt
│   └── api.txt
├── requirements.txt            # Main dependencies
├── startup.sh                  # Azure startup script
├── .env.example                # Configuration template
├── .deployment                 # Azure deployment config
└── INSTALL.md                  # This guide
```

---

## 🎯 Why Not Use Portal Upload?

**The Azure Portal "Zip Deploy" and Kudu drag-and-drop methods skip the Oryx build system**, which means:
- ❌ Python dependencies are NOT installed
- ❌ App will fail with "module not found" errors
- ❌ No virtual environment created

**The curl API method triggers the proper build process:**
- ✅ Runs Oryx build system
- ✅ Installs all Python packages from requirements.txt
- ✅ Creates proper virtual environment
- ✅ App starts correctly

---

## 🎯 Alternative: Azure CLI Deployment

If you have Azure CLI installed:

```bash
# Prerequisites: Install Azure CLI
# https://docs.microsoft.com/cli/azure/install-azure-cli

# 1. Login to Azure
az login

# 2. Create Resource Group
az group create --name lineage-rg --location eastus

# 3. Create App Service Plan
az appservice plan create \
  --name lineage-plan \
  --resource-group lineage-rg \
  --sku B1 \
  --is-linux

# 4. Create Web App
az webapp create \
  --name your-app-name \
  --resource-group lineage-rg \
  --plan lineage-plan \
  --runtime "PYTHON:3.11"

# 5. Deploy ZIP
az webapp deployment source config-zip \
  --resource-group lineage-rg \
  --name your-app-name \
  --src azure-deploy/lineage-visualizer-azure.zip

# 6. Configure App Settings
az webapp config appsettings set \
  --resource-group lineage-rg \
  --name your-app-name \
  --settings \
    ALLOWED_ORIGINS=https://your-app-name.azurewebsites.net \
    PATH_WORKSPACE_FILE=/home/site/data/lineage_workspace.duckdb \
    PATH_OUTPUT_DIR=/home/site/data/lineage_output \
    PATH_PARQUET_DIR=/home/site/data/parquet_snapshots \
    LOG_LEVEL=INFO \
    DEBUG_MODE=false \
    SKIP_QUERY_LOGS=false

# 7. Set Startup Command
az webapp config set \
  --resource-group lineage-rg \
  --name your-app-name \
  --startup-file "bash startup.sh"

# 8. Enable Persistent Storage
az webapp config set \
  --resource-group lineage-rg \
  --name your-app-name \
  --generic-configurations '{"acrUseManagedIdentityCreds": false, "alwaysOn": false, "httpLoggingEnabled": true, "logsDirectorySizeLimit": 35}'

# 9. Restart App
az webapp restart --resource-group lineage-rg --name your-app-name

# 10. View logs
az webapp log tail --resource-group lineage-rg --name your-app-name
```

---

## 📂 Package Contents

```
lineage-visualizer-azure.zip
├── api/                    # FastAPI backend
├── lineage_v3/             # Parser engine
├── static/                 # React frontend (built)
│   ├── index.html
│   └── assets/
├── requirements.txt        # Python dependencies
├── startup.sh              # Azure startup script
├── .env.example            # Configuration template
└── INSTALL.md              # This file
```

---

## 🔧 Configuration Reference

### **Required Settings**
| Setting | Value | Description |
|---------|-------|-------------|
| `ALLOWED_ORIGINS` | `https://your-app.azurewebsites.net` | CORS allowed origins |
| `PATH_WORKSPACE_FILE` | `/home/site/data/lineage_workspace.duckdb` | DuckDB database path |

### **Optional Settings**
| Setting | Default | Description |
|---------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DEBUG_MODE` | `false` | Enable debug features |
| `SKIP_QUERY_LOGS` | `false` | Skip query log analysis |

---

## 🐛 Troubleshooting

### **App won't start**
```bash
# Check logs:
az webapp log tail --resource-group lineage-rg --name your-app-name

# Common issues:
# 1. Startup command not set → Set "bash startup.sh"
# 2. Python version mismatch → Use Python 3.11
# 3. Missing dependencies → Check requirements.txt
```

### **Frontend shows 404**
```bash
# Verify static files exist:
az webapp ssh --resource-group lineage-rg --name your-app-name
ls /home/site/wwwroot/static

# If missing: Redeploy the ZIP package
```

### **API returns 500**
```bash
# Check environment variables:
az webapp config appsettings list \
  --resource-group lineage-rg \
  --name your-app-name

# Verify ALLOWED_ORIGINS matches your URL
```

### **CORS errors**
```bash
# Update ALLOWED_ORIGINS:
az webapp config appsettings set \
  --resource-group lineage-rg \
  --name your-app-name \
  --settings ALLOWED_ORIGINS=https://your-app-name.azurewebsites.net

# Restart:
az webapp restart --resource-group lineage-rg --name your-app-name
```

---

## 📊 Performance Tuning

### **Recommended App Service Plan**
- **Development:** B1 (Basic) - $13/month
- **Production:** S1 (Standard) - $70/month
- **High Volume:** P1V2 (Premium) - $117/month

### **Scaling**
```bash
# Scale up (bigger instance):
az appservice plan update \
  --name lineage-plan \
  --resource-group lineage-rg \
  --sku S1

# Scale out (more instances):
az appservice plan update \
  --name lineage-plan \
  --resource-group lineage-rg \
  --number-of-workers 2
```

---

## 🔒 Security Checklist

- ✅ Set `DEBUG_MODE=false`
- ✅ Configure `ALLOWED_ORIGINS` (no wildcards in production)
- ✅ Enable HTTPS only (Azure default)
- ✅ Review App Service authentication if needed
- ✅ Enable Application Insights for monitoring
- ✅ Set up automated backups for persistent data

---

## 💡 Tips & Best Practices

### **Cost Optimization**
- Use **B1 tier** for development/testing ($13/month)
- Stop the app when not in use (Settings > Overview > Stop)
- Use **auto-scaling** only for production workloads
- Set up **budget alerts** in Azure Cost Management

### **Performance Tips**
- Enable **Always On** for production (General settings)
- Use **Application Insights** to identify bottlenecks
- Consider **Azure CDN** for global users
- Scale up before scale out for better cost efficiency

### **Data Management**
- DuckDB workspace persists in `/home/site/data`
- Old job files are auto-cleaned after retrieval
- Use **incremental mode** for faster re-parsing
- Download workspace file for local analysis if needed

### **Development Workflow**
1. Test locally first: `bash start-app.sh`
2. Build and verify package: `bash create-deployment-package.sh`
3. Deploy to Azure staging slot (optional)
4. Test on Azure before production release
5. Monitor logs after deployment

---

## 📞 Support & Resources

### **Documentation**
- **Azure App Service:** https://docs.microsoft.com/azure/app-service/
- **Python on Azure:** https://docs.microsoft.com/azure/app-service/quickstart-python
- **Project README:** See main README.md in repository

### **API Documentation**
- **Interactive Docs:** `https://your-app.azurewebsites.net/docs`
- **OpenAPI Spec:** `https://your-app.azurewebsites.net/openapi.json`

### **Getting Help**
- Check troubleshooting section above
- Review Azure Log Stream for errors
- Test health endpoint: `/health`
- Verify configuration settings

### **Common URLs**
- **Azure Portal:** https://portal.azure.com
- **App Service Plans Pricing:** https://azure.microsoft.com/pricing/details/app-service/linux/
- **Azure Status:** https://status.azure.com

---

## 🔄 Updates & Redeployment

### **To Update the Application:**

1. **Pull Latest Code**
   ```bash
   cd /path/to/data_lineage
   git pull origin main
   ```

2. **Rebuild Package**
   ```bash
   cd azure-deploy
   bash create-deployment-package.sh
   ```

3. **Redeploy via Azure Portal**
   - App Services > Your App > Deployment Center
   - Upload new `lineage-visualizer-azure.zip`
   - Wait for deployment
   - Restart app

4. **Verify Update**
   - Check `/health` endpoint for new version
   - Test functionality
   - Monitor logs for errors

### **To Update Configuration Only:**
- Configuration > Application settings
- Modify settings as needed
- Save and restart

---

## 📋 Pre-Deployment Checklist

Before deploying to production:

- [ ] Built deployment package successfully
- [ ] Verified package contains all required files
- [ ] Created Azure Web App with Python 3.11
- [ ] Configured all 7 application settings
- [ ] Set startup command: `bash startup.sh`
- [ ] Enabled file system storage
- [ ] Deployed ZIP file successfully
- [ ] Restarted application
- [ ] Verified `/health` endpoint returns 200 OK
- [ ] Tested frontend loads correctly
- [ ] Uploaded test Parquet files
- [ ] Verified lineage graph displays
- [ ] Checked that CORS settings match URL
- [ ] Reviewed security settings
- [ ] Set up monitoring/alerts
- [ ] Documented URL and credentials

---

**Version:** v4.2.0  
**Last Updated:** November 15, 2025  
**Deployment Target:** Azure App Service (Linux, Python 3.11)  
**Deployment Method:** Browser-based ZIP Deploy  

---

**Questions?** Review the troubleshooting section or check Azure Log Stream for detailed error messages.
