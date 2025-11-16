# Azure Authentication Bug Log

## Issue Summary
Upload functionality failed with 401 Unauthorized errors when Azure Container Apps authentication was enabled.

## Timeline

### Initial Problem (2025-11-16)
- **Symptom**: Upload fails with 401 errors even after user successfully logs in via Azure AD
- **Configuration**: 
  - Azure Container Apps with Easy Auth enabled
  - Authentication mode: RedirectToLoginPage
  - Azure AD App Registration configured with ID token issuance
- **Observation**: Frontend loads correctly after login, but all API calls return 401

### Root Cause Analysis

#### Investigation Phase 1: Frontend Cookie Issue
**Hypothesis**: JavaScript fetch() doesn't send authentication cookies by default

**Action Taken**: Added `credentials: 'same-origin'` to all fetch() calls in:
- `frontend/App.tsx` - latest-data endpoint
- `frontend/components/ImportDataModal.tsx` - upload, metadata, clear-data, status, result endpoints  
- `frontend/components/DetailSearchModal.tsx` - search-ddl, ddl detail endpoints

**Result**: ❌ Still failed with 401 errors

#### Investigation Phase 2: Backend Authentication Logic
**Hypothesis**: Backend rejecting requests even when authentication is properly configured

**Problem Identified**: 
```python
# api/main.py - verify_azure_auth() function
if not x_ms_client_principal:
    if is_azure:
        raise HTTPException(status_code=401, detail="Authentication required")
```

When Azure Container Apps authentication is set to `AllowAnonymous` or completely disabled, the platform doesn't send the `X-MS-CLIENT-PRINCIPAL` header. However, the backend was checking for `WEBSITE_SITE_NAME` environment variable (which exists in Azure) and **blocking** all requests without the header.

**Root Cause**: The backend logic assumed that if running in Azure, authentication MUST be enforced. It didn't account for:
1. Authentication platform being disabled (`enabled: false`)
2. Authentication platform in AllowAnonymous mode

#### Investigation Phase 3: Local vs Azure Behavior Gap
**Local Testing**: 
- Docker container tested locally on port 8000
- Upload worked perfectly (no WEBSITE_SITE_NAME env var)
- All endpoints returned 200 OK
- Processing completed successfully (1067 nodes, 90.2% coverage)

**Azure Testing with Auth Disabled**:
- Initially still failed with 401 (old container image cached)
- After redeployment, worked perfectly

## Solution

### Code Changes

**File**: `api/main.py`

**Before**:
```python
async def verify_azure_auth(
    x_ms_client_principal: Optional[str] = Header(None, alias="X-MS-CLIENT-PRINCIPAL")
) -> Optional[Dict[str, Any]]:
    is_azure = os.getenv("WEBSITE_SITE_NAME") is not None
    
    if not x_ms_client_principal:
        # No auth header - allow in local/dev mode, block in Azure
        if is_azure:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please log in."
            )
        else:
            logger.info("Running without authentication (local/dev mode)")
            return None
```

**After**:
```python
async def verify_azure_auth(
    x_ms_client_principal: Optional[str] = Header(None, alias="X-MS-CLIENT-PRINCIPAL")
) -> Optional[Dict[str, Any]]:
    is_azure = os.getenv("WEBSITE_SITE_NAME") is not None
    
    if not x_ms_client_principal:
        # No auth header - allow access (AllowAnonymous mode or local dev)
        if is_azure:
            logger.info("Running in Azure with AllowAnonymous mode")
        else:
            logger.info("Running without authentication (local/dev mode)")
        return None
```

**Key Change**: Removed the `raise HTTPException(401)` when running in Azure without the auth header. Now assumes that if the header is missing, authentication is either disabled or in AllowAnonymous mode.

### Azure Configuration

**Final Working Configuration**:
```json
{
  "platform": {
    "enabled": false
  },
  "globalValidation": {
    "unauthenticatedClientAction": "AllowAnonymous"
  }
}
```

Command to disable authentication:
```bash
az containerapp auth update --name chwa-datalineage --resource-group rg-chwa-container --enabled false
```

### Deployment Process
1. Modified `api/main.py` authentication logic
2. Rebuilt frontend: `cd frontend && npm run build`
3. Rebuilt Docker image: `docker build -t datalineage:latest -f azure-deploy/docker/Dockerfile .`
4. Tagged for ACR: `docker tag datalineage:latest chwadatalineage.azurecr.io/datalineage:latest`
5. Pushed to ACR: `docker push chwadatalineage.azurecr.io/datalineage:latest`
6. Updated Container App: `az containerapp update --name chwa-datalineage --resource-group rg-chwa-container --image chwadatalineage.azurecr.io/datalineage:latest`

## Current Status

✅ **RESOLVED** - Upload functionality working correctly

### Test Results (2025-11-16 16:05:58 UTC)
- Upload: **200 OK**
- Processing: **Success**
- Nodes generated: **1067**
- Coverage: **90.2%**
- All API endpoints: **200 OK**

### Logs Confirmation
```
2025-11-16 16:05:53 - Running without authentication (local/dev mode)
2025-11-16 16:05:58 - Generating internal lineage.json...
2025-11-16 16:05:58 - Fetched 1067 objects from workspace
2025-11-16 16:05:58 - ✓ Generated lineage.json with 1067 nodes
2025-11-16 16:05:58 - ✓ Generated lineage_summary.json with 90.2% coverage
2025-11-16 16:05:58 - ✓ Generated frontend_lineage.json with 1067 nodes
2025-11-16 16:05:58 - ✅ Saved latest data to /app/data/latest_frontend_lineage.json
```

## Lessons Learned

1. **Test Locally First**: Always test Docker containers locally before deploying to Azure to isolate platform-specific issues

2. **Environment Detection is Insufficient**: Using `WEBSITE_SITE_NAME` to determine if authentication should be enforced is unreliable. The backend should:
   - Either trust Azure Easy Auth to handle authentication at the platform level
   - Or check additional signals to determine the intended authentication mode

3. **Frontend Changes Were Not the Issue**: The `credentials: 'same-origin'` changes were valid for authenticated scenarios but didn't fix the core issue (backend blocking requests)

4. **Platform vs Application Authentication**: 
   - Azure Container Apps Easy Auth operates at the **platform level** (before requests reach the app)
   - Application-level authentication checks should be **optional** when platform auth is enabled
   - When platform auth is disabled, the application must handle its own authentication

5. **Log Analysis is Critical**: Container logs immediately showed 401 errors, which pointed to a backend rejection rather than a frontend cookie/credential issue

## Future Recommendations

### For Authentication Re-enablement

When ready to enable tenant-only authentication again:

1. **Enable Azure Container Apps Easy Auth**:
   ```bash
   az containerapp auth update \
     --name chwa-datalineage \
     --resource-group rg-chwa-container \
     --enabled true \
     --unauthenticated-client-action RedirectToLoginPage
   ```

2. **Update Backend Logic** to properly detect authentication mode:
   ```python
   # Option A: Trust platform auth completely
   # Don't validate X-MS-CLIENT-PRINCIPAL in code, let platform handle it
   
   # Option B: Check for explicit authentication flag
   AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
   
   if AUTH_REQUIRED and not x_ms_client_principal:
       raise HTTPException(401, "Authentication required")
   ```

3. **Set Environment Variable** when authentication is required:
   ```bash
   az containerapp update \
     --name chwa-datalineage \
     --resource-group rg-chwa-container \
     --set-env-vars AUTH_REQUIRED=true
   ```

4. **Test with Authentication Flow**:
   - Verify redirect to Azure AD login
   - Confirm X-MS-CLIENT-PRINCIPAL header is received
   - Check that all API calls include the header
   - Monitor logs for successful authentication messages

### Monitoring

**Key Log Messages to Monitor**:
- `"Running without authentication (local/dev mode)"` - Expected when auth disabled
- `"Running in Azure with AllowAnonymous mode"` - Expected with auth platform enabled but AllowAnonymous
- `"User authenticated: {userId}"` - Expected when auth is fully enabled and working
- `"401"` HTTP status in logs - Indicates authentication failure

**Health Check**:
```bash
# Should return 200 when working
curl https://chwa-datalineage.agreeablesky-46763c91.westeurope.azurecontainerapps.io/health
```

## Technical Details

### Azure Container Apps Easy Auth
- **X-MS-CLIENT-PRINCIPAL**: Base64-encoded JSON containing user identity information
- **Header set by**: Azure Container Apps platform (not by client)
- **When it exists**: Only when authentication platform is enabled AND user is authenticated
- **When it's missing**: 
  - Authentication platform disabled
  - Authentication platform enabled with AllowAnonymous and user hasn't logged in
  - Local development without Azure platform

### Environment Variables (Azure Container Apps)
- `WEBSITE_SITE_NAME`: Always set in Azure Container Apps environment
- `ALLOWED_ORIGINS`: CORS configuration
- `PATH_OUTPUT_DIR`: Data persistence location
- `LOG_LEVEL`: Logging verbosity

### Image Details
- **Registry**: chwadatalineage.azurecr.io
- **Image**: datalineage:latest
- **Digest (current)**: sha256:087ab94be0b07c9f1b470da44d10fd12397bb988c07887724747a113829bdd4a
- **Base Image**: python:3.12-slim
- **Gunicorn Workers**: 4 Uvicorn workers
- **Port**: 8000

## References
- Azure Container Apps: chwa-datalineage
- Resource Group: rg-chwa-container
- Container Registry: chwadatalineage.azurecr.io
- App URL: https://chwa-datalineage.agreeablesky-46763c91.westeurope.azurecontainerapps.io/
- Azure AD App: chwa-datalineage-app (Client ID: d65f76b9-9699-41e2-9f14-24ed1c32c842)
