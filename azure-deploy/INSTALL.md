# Azure Web App Deployment Guide
**Data Lineage Visualizer v4.2.0**

---

## 📦 Quick Deploy (5 minutes)

### **Prerequisites**
- Azure subscription with App Service
- Azure CLI installed (optional, for CLI deployment)

---

## 🚀 Deployment Steps

### **Option 1: Azure Portal (Recommended)**

#### **1. Create Azure Web App**
```bash
# Via Azure Portal:
- Resource: "App Service"
- Runtime: Python 3.11
- Operating System: Linux
- Region: Your choice
- App Service Plan: B1 or higher (Basic+)
```

#### **2. Upload Deployment Package**
```bash
# Via Portal > Deployment Center:
1. Go to your App Service
2. Navigate to: Deployment Center > Zip Deploy
3. Upload: lineage-visualizer-azure.zip
4. Wait for deployment to complete (~2-3 minutes)
```

#### **3. Configure Environment Variables**
```bash
# Navigate to: Configuration > Application Settings
# Add these settings:

ALLOWED_ORIGINS=https://your-app-name.azurewebsites.net
PATH_WORKSPACE_FILE=/home/site/data/lineage_workspace.duckdb
PATH_OUTPUT_DIR=/home/site/data/lineage_output
PATH_PARQUET_DIR=/home/site/data/parquet_snapshots
LOG_LEVEL=INFO
DEBUG_MODE=false
SKIP_QUERY_LOGS=false
```

#### **4. Configure Startup Command**
```bash
# Navigate to: Configuration > General Settings
# Startup Command:
bash startup.sh
```

#### **5. Enable Persistent Storage**
```bash
# Navigate to: Configuration > General Settings
# Set "Mount Storage" = True
```

---

### **Option 2: Azure CLI**

```bash
# Login
az login

# Create Resource Group
az group create --name lineage-rg --location eastus

# Create App Service Plan
az appservice plan create \
  --name lineage-plan \
  --resource-group lineage-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name your-app-name \
  --resource-group lineage-rg \
  --plan lineage-plan \
  --runtime "PYTHON:3.11"

# Deploy ZIP
az webapp deployment source config-zip \
  --resource-group lineage-rg \
  --name your-app-name \
  --src lineage-visualizer-azure.zip

# Configure App Settings
az webapp config appsettings set \
  --resource-group lineage-rg \
  --name your-app-name \
  --settings \
    ALLOWED_ORIGINS=https://your-app-name.azurewebsites.net \
    PATH_WORKSPACE_FILE=/home/site/data/lineage_workspace.duckdb \
    PATH_OUTPUT_DIR=/home/site/data/lineage_output \
    LOG_LEVEL=INFO

# Set Startup Command
az webapp config set \
  --resource-group lineage-rg \
  --name your-app-name \
  --startup-file "bash startup.sh"

# Restart App
az webapp restart --resource-group lineage-rg --name your-app-name
```

---

## ✅ Verify Deployment

### **1. Check Health Endpoint**
```bash
curl https://your-app-name.azurewebsites.net/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "api_version": "4.0.3",
  "uptime_seconds": 120
}
```

### **2. Access Frontend**
```
Open: https://your-app-name.azurewebsites.net
```

### **3. Monitor Logs**
```bash
# Via Portal:
Monitoring > Log Stream

# Via CLI:
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

## 📖 Additional Resources

- **Azure App Service Docs:** https://docs.microsoft.com/azure/app-service/
- **Application Setup:** See README.md in repo
- **API Documentation:** https://your-app.azurewebsites.net/docs
- **Support:** See BUGS.md for known issues

---

**Version:** v4.2.0
**Last Updated:** 2025-11-08
**Deployment Target:** Azure App Service (Linux, Python 3.11)
