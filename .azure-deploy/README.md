# Azure Container Apps Deployment

Automated infrastructure-as-code deployment for Azure Container Apps.

**Version:** 1.0.1 • **Author:** Christian Wagner

---

## Quick Start

### Prerequisites
- Azure CLI (`az --version`)
- Docker Desktop (`docker ps`)
- Node.js v18+ (`node --version`)

### Deploy

**Option 1: Public Access (No Authentication)**
```bash
# Set deployment prefix
export PREFIX="demo"            # Customize: prod, staging, dev

# Run automated deployment
cd .azure-deploy
chmod +x deploy.sh  # Unix/Mac only
./deploy.sh
```

**Option 2: With Azure AD Authentication**
```bash
# Get your tenant ID
export TENANT_ID=$(az account show --query tenantId -o tsv)
export PREFIX="demo"
export ENABLE_AUTH="true"

# Run deployment with authentication
cd .azure-deploy
./deploy.sh
```

**Windows PowerShell:**
```powershell
# Without authentication
$env:PREFIX = "demo"
cd .azure-deploy
bash deploy.sh

# With authentication
$env:TENANT_ID = (az account show --query tenantId -o tsv)
$env:PREFIX = "demo"
$env:ENABLE_AUTH = "true"
bash deploy.sh
```

**Deployment time:** 10-15 minutes • **Creates:** Resource Group, ACR, Log Analytics, Container Apps Environment, Container App

---

## What Gets Deployed

```
Resource Group:     rg-demo-datalineage
ACR:               demodatalineage.azurecr.io
Container App:     demo-datalineage-app
Environment:       demo-datalineage-env
Log Analytics:     demo-datalineage-logs
```

**Application URL:** `https://demo-datalineage-app.....azurecontainerapps.io`

---

## Configuration

### Environment Variables

```bash
PREFIX="demo"                    # Resource name prefix (required)
LOCATION="westeurope"            # Azure region (default)
SUBSCRIPTION_ID="..."            # Azure subscription (optional, uses current)
```

### Container Configuration

Set via `deploy.sh` or update manually:

```bash
ALLOWED_ORIGINS=*                # CORS (change for production)
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
RUN_MODE=production              # production, debug, demo
SQL_DIALECT=tsql                 # tsql, postgres, snowflake
```

---

## Redeployment (Updates)

```bash
# Update existing deployment
export PREFIX="demo"
./deploy.sh
```

Script detects existing resources and updates them.

---

## Management

### View Logs

```bash
az containerapp logs show \
  --name demo-datalineage-app \
  --resource-group rg-demo-datalineage \
  --follow
```

### Update Configuration

```bash
az containerapp update \
  --name demo-datalineage-app \
  --resource-group rg-demo-datalineage \
  --set-env-vars "LOG_LEVEL=DEBUG"
```

### Scale Resources

```bash
az containerapp update \
  --name demo-datalineage-app \
  --resource-group rg-demo-datalineage \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 2 \
  --max-replicas 5
```

### Delete Deployment

```bash
az group delete --name rg-demo-datalineage --yes
```

---

## Azure AD Authentication (Optional)

**Via Azure Portal:**
1. Navigate to Container App → Authentication
2. Add identity provider → Microsoft (Azure AD)
3. Create new app registration
4. Set unauthenticated access → Require authentication

---

## Troubleshooting

### Script Fails at ACR Login

```bash
az login  # Re-authenticate
az acr login --name demodatalineage
```

### Container Won't Start

```bash
# Check logs
az containerapp logs show \
  --name demo-datalineage-app \
  --resource-group rg-demo-datalineage \
  --tail 100
```

Common causes:
- Frontend not built (`npm run build` in frontend/)
- Missing environment variables
- Image pull failure

### Frontend Not Rendering

Ensure Tailwind CSS dependencies installed:

```bash
cd frontend
npm install  # Must include tailwindcss, postcss, autoprefixer
npm run build
```

---

## Folder Structure

```
.azure-deploy/
├── deploy.sh              # Automated deployment script
├── README.md              # This file
└── docker/
    ├── Dockerfile         # Azure-optimized image
    └── docker-compose.yml # Local testing
```

---

## Cost Estimate

- Container Apps: ~$0.000012/vCPU-second (consumption)
- Container Registry (Basic): ~$5/month
- Log Analytics: ~$2.30/GB

**Monthly:** $30-50 for light usage

---

**Status:** Production Ready • **Maintainer:** Christian Wagner
