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
- Azure CLI installed and logged in (`az login`)
- Docker Desktop installed and running
- Access to Azure subscription
- Git repository synced

---

## Complete Deployment Guide

### Step 1: Sync with Git Repository

Always pull the latest changes before deploying:

```powershell
# Navigate to project directory
cd c:\Users\ChristianWagner\vscode\ws-datalineage\data_lineage

# Pull latest changes from GitHub
git pull origin main
```

**What to check:**
- ✅ No merge conflicts
- ✅ All changes pulled successfully
- ✅ Working directory clean

---

### Step 2: Build Frontend

Build the React application with latest changes:

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies (includes Tailwind CSS v3.4.x, PostCSS, autoprefixer)
npm install

# Build production bundle (Vite processes Tailwind CSS → dist/assets/)
npm run build
```

**Frontend Build Requirements:**
- **Tailwind CSS v3.4.x** - Utility-first CSS framework (npm, not CDN)
- **PostCSS** - CSS processing pipeline with autoprefixer
- **Vite** - Build tool that processes `index.css` with Tailwind directives
- **Output:** Processed CSS bundle in `dist/assets/*.css`

**Expected Output:**
```
✓ 555 modules transformed.
dist/index.html                  3.15 kB │ gzip:   1.20 kB
dist/assets/index-HqpVsFJX.js  648.68 kB │ gzip: 196.73 kB
✓ built in 2.76s
```

**Verify:**
- ✅ `frontend/dist/` directory created
- ✅ `dist/index.html` exists
- ✅ `dist/assets/` contains JavaScript bundle
- ✅ No build errors

---

### Step 3: Build Docker Image

Create a new Docker image with updated code:

```powershell
# Return to project root
cd ..

# Ensure Docker Desktop is running
docker ps

# Build new image
docker build -t datalineage:latest -f azure-deploy/docker/Dockerfile .
```

**Expected Output:**
```
[+] Building 5.8s (15/15) FINISHED
 => [8/9] COPY frontend/dist /app/static
 => [9/9] RUN mkdir -p /app/data
 => exporting to image
 => => naming to docker.io/library/datalineage:latest
```

**What happens:**
- ✅ Uses Python 3.12-slim base image
- ✅ Installs Python dependencies
- ✅ Copies backend code (`api/`, `engine/`)
- ✅ Copies built frontend (`frontend/dist` → `/app/static`)
- ✅ Sets up data directory

**Optional - Test Locally:**
```powershell
# Run container locally
docker run -d --name datalineage-test -p 8000:8000 datalineage:latest

# Test health endpoint
curl http://localhost:8000/health

# Clean up
docker stop datalineage-test
docker rm datalineage-test
```

---

### Step 4: Tag Image for Azure Container Registry

Tag the local image for Azure:

```powershell
docker tag datalineage:latest chwadatalineage.azurecr.io/datalineage:latest
```

**What this does:**
- Creates an alias for the image pointing to ACR
- Prepares image for push to registry
- Uses registry name: `chwadatalineage.azurecr.io`
- Image name: `datalineage`
- Tag: `latest`

---

### Step 5: Push to Azure Container Registry

Upload the image to Azure:

```powershell
# Login to ACR (uses Azure CLI credentials)
az acr login --name chwadatalineage

# Push image to registry
docker push chwadatalineage.azurecr.io/datalineage:latest
```

**Expected Output:**
```
The push refers to repository [chwadatalineage.azurecr.io/datalineage]
99e84f338f83: Pushed
a4f564a4a58f: Layer already exists
...
latest: digest: sha256:db5d84a44d70af9b4863a43e0ed882dca08d581916dac1918a5791de5b99dcbe size: 856
```

**What happens:**
- ✅ Authenticates with ACR using managed identity
- ✅ Uploads changed layers only (fast subsequent pushes)
- ✅ Assigns new digest (unique identifier for this version)
- ✅ Updates `latest` tag to point to new digest

**Time estimate:** 1-3 minutes (first push), 10-30 seconds (subsequent pushes)

---

### Step 6: Update Container App

Deploy the new image to Azure Container Apps:

```powershell
# Update container app with new image
az containerapp update \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --image chwadatalineage.azurecr.io/datalineage:latest
```

**Expected Output:**
```json
{
  "properties": {
    "latestRevisionName": "chwa-datalineage--auth-v2",
    "provisioningState": "Succeeded",
    "runningStatus": "Running",
    ...
  }
}
```

**What happens:**
- ✅ Container App pulls new image from ACR
- ✅ Creates new revision (or updates existing)
- ✅ Updates configuration
- ✅ **Note:** Old containers may still run until manually restarted

---

### Step 7: Restart Container (Force New Deployment)

Force the container to restart with the new image:

```powershell
# Restart the active revision
az containerapp revision restart \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --revision chwa-datalineage--auth-v2
```

**Expected Output:**
```
"Restart succeeded"
```

**What happens:**
- ✅ Terminates existing container replicas
- ✅ Pulls latest image from ACR
- ✅ Starts new container instances
- ✅ Takes 20-30 seconds to fully restart

---

### Step 8: Verify Deployment

Check that the new version is running:

```powershell
# Wait for container to start
Start-Sleep -Seconds 25

# View logs (last 30 lines)
az containerapp logs show \
  --name chwa-datalineage \
  --resource-group rg-chwa-container \
  --follow false \
  --tail 30
```

**Expected Log Output:**
```
Successfully Connected to container: 'chwa-datalineage' [Revision: 'chwa-datalineage--auth-v2', Replica: 'chwa-datalineage--auth-v2-6bcb89844d-vqvjw']
2025-11-17 14:47:23 - 🚀 Data Lineage Visualizer API v4.0.3
2025-11-17 14:47:23 - 📁 Jobs directory: /tmp/jobs
2025-11-17 14:47:23 - 💾 Data directory: /app/data
2025-11-17 14:47:23 - ✅ API ready
[2025-11-17 14:47:23 +0000] [8] [INFO] Application startup complete.
```

**Verify checklist:**
- ✅ New replica ID in logs (different from previous)
- ✅ Recent timestamp (within last minute)
- ✅ "API ready" message appears
- ✅ No error messages
- ✅ Application version correct (v4.0.3)

**Test in browser:**
1. Navigate to: https://chwa-datalineage.agreeablesky-46763c91.westeurope.azurecontainerapps.io/
2. Should redirect to Azure AD login
3. After authentication, app should load with new changes

---

## Quick Reference - Full Deployment Command Sequence

```powershell
# 1. Sync code
git pull origin main

# 2. Build frontend (includes Tailwind CSS)
cd frontend; npm install; npm run build; cd ..

# 3. Build Docker image
docker build -t datalineage:latest -f azure-deploy/docker/Dockerfile .

# 4. Tag for ACR
docker tag datalineage:latest chwadatalineage.azurecr.io/datalineage:latest

# 5. Login and push
az acr login --name chwadatalineage
docker push chwadatalineage.azurecr.io/datalineage:latest

# 6. Update container app
az containerapp update --name chwa-datalineage --resource-group rg-chwa-container --image chwadatalineage.azurecr.io/datalineage:latest

# 7. Restart container
az containerapp revision restart --name chwa-datalineage --resource-group rg-chwa-container --revision chwa-datalineage--auth-v2

# 8. Verify (wait 25 seconds)
Start-Sleep -Seconds 25
az containerapp logs show --name chwa-datalineage --resource-group rg-chwa-container --follow false --tail 30
```

**Total time:** 5-10 minutes

---

## Troubleshooting Deployment Issues

### Issue: Docker build fails

**Check:**
```powershell
# Verify Docker is running
docker ps

# Check if frontend was built
Test-Path frontend/dist/index.html
```

**Solution:** Ensure Docker Desktop is running and frontend build completed

---

### Issue: ACR login fails

**Error:** `unauthorized: authentication required`

**Solution:**
```powershell
# Re-login to Azure
az login

# Login to ACR again
az acr login --name chwadatalineage
```

---

### Issue: Push fails with "denied: requested access to the resource is denied"

**Cause:** Insufficient permissions on Container Registry

**Solution:**
```powershell
# Verify you have AcrPush role
az role assignment list --assignee $(az account show --query user.name -o tsv) --scope /subscriptions/6009a250-7363-474d-85b6-2fba12522cf0/resourceGroups/rg-chwa-container/providers/Microsoft.ContainerRegistry/registries/chwadatalineage
```

---

### Issue: Container app update succeeds but old version still running

**Cause:** Container App cached old image or didn't restart

**Solution:**
```powershell
# Force restart
az containerapp revision restart --name chwa-datalineage --resource-group rg-chwa-container --revision chwa-datalineage--auth-v2

# If still not working, create new revision
az containerapp revision copy --name chwa-datalineage --resource-group rg-chwa-container
```

---

### Issue: UI Styling Not Appearing (Buttons Empty, No Colors)

**Cause:** Frontend built without Tailwind CSS dependencies or using outdated build

**Solution:**
1. Ensure `npm install` runs before `npm run build`:
   ```powershell
   cd frontend
   npm install  # Must install tailwindcss, postcss, autoprefixer
   npm run build
   ```
2. Verify Tailwind CSS is in devDependencies:
   ```powershell
   cat frontend/package.json | findstr tailwindcss
   # Should show: "tailwindcss": "^3.4.x"
   ```
3. Check build output includes CSS files:
   ```powershell
   ls frontend/dist/assets/*.css
   # Should show compiled CSS bundle
   ```
4. Rebuild Docker image with proper frontend build
5. Clear browser cache after redeployment

---

### Issue: Container won't start after deployment

**Check logs:**
```powershell
az containerapp logs show --name chwa-datalineage --resource-group rg-chwa-container --follow --tail 100
```

**Common causes:**
- Missing environment variables
- Port 8000 not exposed
- Frontend dist directory missing
- Python dependencies failed to install

**Solution:** Check Dockerfile and rebuild image

---

## Rollback to Previous Version

If new deployment has issues:

```powershell
# List all revisions
az containerapp revision list --name chwa-datalineage --resource-group rg-chwa-container

# Activate previous revision
az containerapp revision activate --name chwa-datalineage --resource-group rg-chwa-container --revision <previous-revision-name>
```

---

## Deployment Best Practices

1. **Always test locally first** - Run Docker container on localhost before pushing
2. **Build frontend before Docker** - Ensure `frontend/dist/` exists and is current
3. **Sync with Git** - Pull latest changes to avoid conflicts
4. **Check logs after deployment** - Verify new container started successfully
5. **Keep notes of working digests** - Save digest hashes of stable versions
6. **Test authentication** - Verify Azure AD login still works after deployment
7. **Monitor for 5 minutes** - Watch logs for any startup errors

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

### Issue: UI Styling Not Appearing (Buttons Empty, No Colors)

**Cause:** Frontend built without Tailwind CSS dependencies or using outdated build

**Solution:**
1. Ensure `npm install` runs before `npm run build`
2. Verify Tailwind CSS is in devDependencies:
   ```bash
   cat frontend/package.json | grep tailwindcss
   # Should show: "tailwindcss": "^3.4.x"
   ```
3. Check build output includes CSS files:
   ```bash
   ls frontend/dist/assets/*.css
   # Should show compiled CSS bundle
   ```
4. Rebuild Docker image with proper frontend build
5. Clear browser cache after redeployment

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

### 2025-11-18
- ✅ Migrated Tailwind CSS from CDN to npm-based installation (v3.4.x)
- ✅ Fixed visual rendering issues caused by unreliable CDN
- ✅ Added PostCSS processing pipeline with autoprefixer
- ✅ Updated build process to include Tailwind CSS compilation
- **Action Required:** Rebuild Docker image with `npm install` before `npm run build`

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
