# Azure Deployment - Quick Start
**Data Lineage Visualizer v4.2.0**

---

## 📦 **Deployment Package Ready**

**File:** `lineage-visualizer-azure.zip` (383KB)
**Location:** Root directory

---

## 🚀 **Deploy in 5 Steps**

### **1. Download Package**
```bash
# Package is already in root: lineage-visualizer-azure.zip
```

### **2. Create Azure Web App**
- Go to: https://portal.azure.com
- Create: App Service
- Runtime: **Python 3.11**
- OS: **Linux**
- Plan: **B1 or higher**

### **3. Upload Package**
- Navigate to: **Deployment Center**
- Select: **Zip Deploy**
- Upload: `lineage-visualizer-azure.zip`

### **4. Configure Settings**
Go to: **Configuration > Application Settings**

Add these:
```
ALLOWED_ORIGINS=https://your-app-name.azurewebsites.net
PATH_WORKSPACE_FILE=/home/site/data/lineage_workspace.duckdb
LOG_LEVEL=INFO
```

### **5. Set Startup Command**
Go to: **Configuration > General Settings**

Startup Command:
```bash
bash startup.sh
```

**Save** and **Restart** the app.

---

## ✅ **Verify Deployment**

### Test Health Endpoint:
```bash
curl https://your-app-name.azurewebsites.net/health
```

### Access Frontend:
```
https://your-app-name.azurewebsites.net
```

---

## 📖 **Full Documentation**

See `azure-deploy/INSTALL.md` for:
- Detailed Azure CLI commands
- Configuration reference
- Troubleshooting guide
- Performance tuning
- Security checklist

---

## 🔧 **What's Included**

✅ **Backend:** FastAPI + Parser Engine
✅ **Frontend:** Production React build
✅ **Static Serving:** SPA routing enabled
✅ **Configuration:** Azure-optimized paths
✅ **Startup Script:** Auto-deployment ready
✅ **Documentation:** Complete installation guide

---

## 📊 **Package Contents**

```
lineage-visualizer-azure.zip (383KB)
├── api/                    # FastAPI backend
├── lineage_v3/             # Parser engine
├── static/                 # React frontend (built)
├── requirements.txt        # Dependencies
├── startup.sh              # Startup command
├── .env.example            # Config template
└── INSTALL.md              # Full guide
```

---

## ⚡ **Quick Troubleshooting**

**App won't start?**
→ Check: Configuration > General Settings > Startup Command = `bash startup.sh`

**CORS errors?**
→ Check: ALLOWED_ORIGINS matches your azurewebsites.net URL

**Frontend 404?**
→ Verify: static/ folder exists in deployment

---

**Deployment Time:** ~5 minutes
**Prerequisites:** Azure subscription only
**Support:** See BUGS.md for known issues

---

**Ready for UAT!** 🎉
