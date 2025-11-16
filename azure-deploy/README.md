# Azure Deployment

## 🚀 Production Deployment

**Status:** ✅ Production deployment with Azure AD authentication  
**Live URL:** https://chwa-datalineage.agreeablesky-46763c91.westeurope.azurecontainerapps.io/

---

## 📖 Documentation

### Current Deployment
- **[AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)** - Complete production deployment guide with authentication
  - Live deployment details
  - Authentication configuration
  - Deployment workflow
  - Management commands
  - Troubleshooting

### Initial Setup Guide
- **[docker/AZURE_CONTAINER_DEPLOYMENT.md](docker/AZURE_CONTAINER_DEPLOYMENT.md)** - Step-by-step GUI deployment guide
  - For first-time deployments
  - Detailed Azure Portal instructions
  - Container Registry setup
  - Container Apps configuration

---

## 🐳 Quick Start - Local Testing

```powershell
cd azure-deploy/docker
.\docker-run.ps1
```
Opens container at http://localhost:8000

---

## 📂 Files

```
azure-deploy/
  ├── docker/
  │   ├── Dockerfile                         # Docker image definition
  │   ├── docker-compose.yml                 # Local development setup
  │   ├── .dockerignore                      # Build exclusions
  │   ├── docker-run.ps1                     # Windows: build & run script
  │   ├── docker-build.sh                    # Linux/Mac: build script
  │   └── AZURE_CONTAINER_DEPLOYMENT.md      # Initial setup guide
  ├── AZURE_DEPLOYMENT.md                    # Production deployment docs (NEW)
  ├── .env.example                           # Environment variables template
  └── README.md                              # This file
```

---

