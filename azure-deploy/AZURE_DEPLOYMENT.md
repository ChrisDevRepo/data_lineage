# Azure Container Apps Deployment Guide

**Status:** ✅ Production Deployment - West Europe
**Last Updated:** 2025-11-16

---

## 🚀 Current Deployment

### Live Application
- **URL:** https://chwa-datalineage.agreeablesky-46763c91.westeurope.azurecontainerapps.io/
- **Resource Group:** rg-chwa-container
- **Container App:** chwa-datalineage
- **Region:** West Europe
- **Status:** Running with Azure AD Authentication

### Infrastructure
- **Container Registry:** chwadatalineage.azurecr.io
- **Image:** datalineage:latest
- **Managed Identity:** System-assigned enabled
- **Authentication:** Azure AD (tenant-only)

### Configuration
- **CPU:** 0.5 cores
- **Memory:** 1 Gi
- **Ingress:** External HTTPS on port 8000
- **Environment Variables:**
  - `ALLOWED_ORIGINS=*`
  - `PATH_OUTPUT_DIR=/app/data`
  - `LOG_LEVEL=INFO`

---

## 🔐 Authentication Setup

The application is secured with **Azure AD authentication** requiring tenant login for all access.

### Authentication Configuration

```json
{
  "platform": {
    "enabled": true
  },
  "globalValidation": {
    "redirectToProvider": "azureactivedirectory",
    "unauthenticatedClientAction": "RedirectToLoginPage"
  },
  "identityProviders": {
    "azureActiveDirectory": {
      "registration": {
        "clientId": "d65f76b9-9699-41e2-9f14-24ed1c32c842",
        "openIdIssuer": "https://login.microsoftonline.com/b982b36d-552f-4ac8-8af7-86a7c60a52ed/v2.0"
      }
    }
  }
}
```

### How It Works

1. **Platform-Level Security**: Azure Container Apps Easy Auth blocks ALL unauthenticated requests before they reach the application
2. **No Backend Enforcement**: The application trusts that Azure has already validated authentication
3. **Seamless Experience**: Users are redirected to Azure AD login page when accessing any endpoint

### Backend Authentication Logic

```python
# api/main.py - verify_azure_auth()
async def verify_azure_auth(
    x_ms_client_principal: Optional[str] = Header(None, alias="X-MS-CLIENT-PRINCIPAL")
) -> Optional[Dict[str, Any]]:
    """
    Trust Azure Container Apps Easy Auth platform-level authentication.
    Platform blocks unauthenticated requests - never reject in application code.
    """
    if not x_ms_client_principal:
        logger.info("Request authenticated by platform")
        return None
    
    # Decode user identity if header present (for logging/audit)
    try:
        principal_json = base64.b64decode(x_ms_client_principal).decode('utf-8')
        principal_data = json.loads(principal_json)
        logger.info(f"User: {principal_data.get('userId', 'unknown')}")
        return principal_data
    except Exception as e:
        logger.warning(f"Header decode failed: {e}")
        return None
```

**Key Design Decisions:**
- ✅ Application **never rejects** requests with 401 errors
- ✅ Trusts Azure Easy Auth to enforce authentication
- ✅ Logs user identity when available for audit purposes
- ✅ All endpoints protected (including /health, /api, static files)

### Frontend Configuration

All API calls include credentials for authenticated requests:

```typescript
// Example from ImportDataModal.tsx
const response = await fetch(`${API_BASE_URL}/api/upload-parquet`, {
  method: 'POST',
  body: formData,
  credentials: 'same-origin'  // Include authentication cookies
});
```

---

## 🏗️ Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Azure AD Authentication                    │
│              (Tenant: b982b36d-552f-4ac8-8af7...)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure Container Apps (Easy Auth)                │
│          Blocks ALL unauthenticated requests                 │
│          Redirects to Azure AD login page                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼ (Only authenticated traffic)
┌─────────────────────────────────────────────────────────────┐
│                 Container App: chwa-datalineage              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Application Container (datalineage:latest)           │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Gunicorn + 4 Uvicorn Workers                   │  │  │
│  │  │  Port 8000                                      │  │  │
│  │  │  ┌──────────────┐  ┌────────────────────────┐  │  │  │
│  │  │  │   Frontend   │  │   Backend API          │  │  │  │
│  │  │  │  React SPA   │  │   FastAPI + DuckDB     │  │  │  │
│  │  │  │  (static)    │  │   Parser Engine        │  │  │  │
│  │  │  └──────────────┘  └────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Persistent Storage: /app/data (container filesystem)       │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          Azure Container Registry (ACR)                      │
│          chwadatalineage.azurecr.io                         │
│          Managed Identity: AcrPull access                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Deployment Workflow

### Prerequisites
- Azure CLI installed and logged in
- Docker installed locally
- Access to Azure subscription

### 1. Build and Test Locally

```powershell
# Build frontend
cd frontend
npm install
npm run build

# Build Docker image
cd ..
docker build -t datalineage:latest -f azure-deploy/docker/Dockerfile .

# Test locally
docker run -d --name datalineage-test -p 8000:8000 datalineage:latest

# Verify
curl http://localhost:8000/health
```

### 2. Push to Azure Container Registry

```powershell
# Login to ACR
az acr login --name chwadatalineage

# Tag image
docker tag datalineage:latest chwadatalineage.azurecr.io/datalineage:latest

# Push to registry
docker push chwadatalineage.azurecr.io/datalineage:latest
```

**Expected Output:**
```
The push refers to repository [chwadatalineage.azurecr.io/datalineage]
latest: digest: sha256:69622959a78b4e04c70c728b959155765b653faa06bd245eb6a3de46670bb3e2 size: 3884
```

### 3. Update Container App

```powershell
# Update to latest image
az containerapp update \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --image chwadatalineage.azurecr.io/datalineage:latest

# Restart container
az containerapp revision restart \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --revision chwa-datalineage--auth-v2
```

### 4. Verify Deployment

```powershell
# Check logs (wait 20-30 seconds after restart)
az containerapp logs show \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --follow false \
  --tail 50
```

**Expected Log Output:**
```
2025-11-16 17:12:10 - 🚀 Data Lineage Visualizer API v4.0.3
2025-11-16 17:12:10 - Running as: production
2025-11-16 17:12:10 - Log level: INFO
2025-11-16 17:12:10 - ✅ API ready on http://0.0.0.0:8000
```

### 5. Test Authenticated Access

```powershell
# Check authentication config
az containerapp auth show \
  --name chwa-datalineage \
  --resource-group rg-chwa-container
```

**Verify:**
- `platform.enabled`: true
- `unauthenticatedClientAction`: RedirectToLoginPage
- All endpoints require authentication

---

## 🛠️ Management Commands

### View Current Configuration

```powershell
# Show container app details
az containerapp show \
  --name chwa-datalineage \
  --resource-group rg-chwa-container

# Show authentication status
az containerapp auth show \
  --name chwa-datalineage \
  --resource-group rg-chwa-container

# List revisions
az containerapp revision list \
  --name chwa-datalineage \
  --resource-group rg-chwa-container
```

### Update Environment Variables

```powershell
az containerapp update \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --set-env-vars LOG_LEVEL=DEBUG
```

### Scale Resources

```powershell
# Increase CPU and memory
az containerapp update \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --cpu 1.0 \
  --memory 2.0Gi
```

### Enable/Disable Authentication

```powershell
# Enable authentication (current state)
az containerapp auth update \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --enabled true \
  --unauthenticated-client-action RedirectToLoginPage

# Disable authentication (for testing only)
az containerapp auth update \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --enabled false
```

---

## 📊 Monitoring

### View Logs in Real-Time

```powershell
# Follow logs
az containerapp logs show \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --follow

# Last 100 lines
az containerapp logs show \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --tail 100
```

### Check Application Health

```bash
# Health endpoint (requires authentication)
curl -I https://chwa-datalineage.agreeablesky-46763c91.westeurope.azurecontainerapps.io/health
```

**Expected:** 302 redirect to Azure AD login page (if not authenticated)

### Monitor Metrics via Azure Portal

1. Navigate to: https://portal.azure.com
2. Resource Groups → rg-chwa-container → chwa-datalineage
3. Monitoring → Metrics
4. View: CPU usage, Memory usage, Request count, Response time

---

## 🐛 Troubleshooting

### Issue: 401 Unauthorized Errors

**Cause:** Authentication configuration mismatch between frontend and backend

**Solution:**
1. Verify frontend includes `credentials: 'same-origin'` in all fetch calls
2. Verify backend `verify_azure_auth()` never raises HTTPException(401)
3. Confirm Azure Easy Auth is enabled with RedirectToLoginPage

See: `docs/AZURE_AUTH_BUG_LOG.md` for detailed analysis

### Issue: Container Won't Start

**Check logs:**
```powershell
az containerapp logs show --name chwa-datalineage --resource-group rg-chwa-container --tail 100
```

**Common causes:**
- Missing environment variables
- Image pull failure (check ACR access)
- Port configuration mismatch

### Issue: Upload Functionality Fails

**Verify:**
1. Authentication is working (user can access UI)
2. CORS configuration allows your domain
3. Sufficient memory allocated (min 1 Gi)
4. Check logs for specific error messages

### Issue: Performance is Slow

**Solutions:**
1. Increase CPU: `--cpu 1.0` or `--cpu 2.0`
2. Increase memory: `--memory 2.0Gi`
3. Enable multiple replicas: `--min-replicas 2 --max-replicas 5`

---

## 🔐 Security Checklist

- ✅ Azure AD authentication enabled (tenant-only access)
- ✅ Admin credentials disabled on ACR
- ✅ Managed identity used for ACR pull access
- ✅ HTTPS enabled by default (Container Apps)
- ✅ Platform-level authentication (no bypasses)
- ✅ All endpoints protected (including /health, /api)
- ✅ CORS configured with credentials support
- ⚠️ Consider: Custom domain for production
- ⚠️ Consider: Private networking for sensitive data

---

## 📚 Additional Documentation

- **Initial Setup:** `azure-deploy/docker/AZURE_CONTAINER_DEPLOYMENT.md`
- **Authentication Details:** `docs/AZURE_AUTH_BUG_LOG.md`
- **Docker Configuration:** `azure-deploy/docker/Dockerfile`
- **API Documentation:** `api/ENDPOINTS.md`

---

## 📝 Deployment History

### 2025-11-16
- ✅ Initial deployment to Azure Container Apps
- ✅ Configured Azure AD authentication
- ✅ Fixed authentication flow (platform-level trust)
- ✅ Verified upload functionality with authentication
- **Image Digest:** sha256:69622959a78b4e04c70c728b959155765b653faa06bd245eb6a3de46670bb3e2

### Configuration
- **Container App Created:** West Europe region
- **Authentication Enabled:** Azure AD tenant-only access
- **Managed Identity:** Enabled for ACR access
- **Resources:** 0.5 CPU, 1 Gi memory
- **Status:** Production ready

---

## 💰 Cost Estimate

**Current Configuration:**
- Azure Container Apps: ~$0.000012/vCPU-second + ~$0.000002/GiB-second
- Container Registry (Basic): ~$5/month
- Estimated Total: **~$30-50/month** for light usage

**Cost Optimization:**
- Scale to 0 replicas when not in use
- Use consumption-based pricing (current setup)
- Delete/recreate for development environments

---

**Deployment Status:** ✅ Production  
**Last Verified:** 2025-11-16 17:12 UTC  
**Maintained by:** Christian Wagner
