# Azure Container Apps Deployment Guide (GUI)

## ✅ Prerequisites Verified
- ✅ Docker container built and tested locally
- ✅ Application working at http://localhost:8000
- ✅ Upload functionality verified

---

## 📋 Deployment Overview

This guide will walk you through deploying the Data Lineage Visualizer to **Azure Container Apps** using the Azure Portal GUI. Azure Container Apps runs your Docker container without the Oryx build system issues.

**Estimated Time:** 15-20 minutes  
**Cost:** ~$30-50/month for Basic tier

---

## Step-by-Step Deployment

### Phase 1: Create Azure Container Registry (ACR)

Azure Container Registry stores your Docker images securely in Azure.

#### 1.1 Navigate to Azure Portal
1. Open https://portal.azure.com
2. Sign in with your Azure account

#### 1.2 Create Container Registry
1. Click **"Create a resource"** (top-left or search bar)
2. Search for **"Container Registry"**
3. Click **"Create"**

#### 1.3 Configure Registry Basics
**Project Details:**
- **Subscription:** Select your subscription
- **Resource Group:** `rg-chwa-app` (or create new)
- **Registry name:** `chwadatalineage` (must be globally unique, lowercase, no hyphens)
- **Location:** `Sweden Central` (same as your resource group)
- **SKU:** `Basic` (sufficient for small projects, ~$5/month)

Click **"Review + create"** → **"Create"**

Wait 1-2 minutes for deployment to complete, then click **"Go to resource"**

#### 1.4 Enable Admin Access
1. In your Container Registry, go to **Settings** → **Access keys** (left menu)
2. Toggle **"Admin user"** to **Enabled**
3. **Copy and save** the following (you'll need them):
   - **Login server:** `chwadatalineage.azurecr.io`
   - **Username:** `chwadatalineage`
   - **Password:** (copy either password)

---

### Phase 2: Push Docker Image to ACR

Now we'll upload your local Docker image to Azure.

#### 2.1 Login to ACR from PowerShell
Open PowerShell in your project directory and run:

```powershell
# Login to Azure Container Registry
docker login chwadatalineage.azurecr.io
```

When prompted:
- **Username:** `chwadatalineage`
- **Password:** (paste the password you copied)

You should see: **"Login Succeeded"**

#### 2.2 Tag Your Image
```powershell
# Tag the local image for ACR
docker tag datalineage:latest chwadatalineage.azurecr.io/datalineage:latest
```

#### 2.3 Push Image to ACR
```powershell
# Push to Azure Container Registry
docker push chwadatalineage.azurecr.io/datalineage:latest
```

This will take 2-5 minutes depending on your internet speed. You'll see progress for each layer.

#### 2.4 Verify Upload
1. Go back to Azure Portal → Your Container Registry
2. Click **Services** → **Repositories** (left menu)
3. You should see **"datalineage"** repository
4. Click on it → you should see **"latest"** tag

✅ Image successfully uploaded to Azure!

---

### Phase 3: Create Azure Container App

#### 3.1 Navigate to Container Apps
1. Click **"Create a resource"**
2. Search for **"Container App"**
3. Click **"Create"**

#### 3.2 Configure Basics
**Project Details:**
- **Subscription:** Select your subscription
- **Resource Group:** `rg-chwa-app`
- **Container app name:** `chwa-datalineage`
- **Region:** `Sweden Central`

**Container Apps Environment:**
- Click **"Create new"**
- **Environment name:** `datalineage-env`
- **Zone redundancy:** Disabled (to save costs)
- Click **"Create"**

Click **"Next: App settings >"**

#### 3.3 Configure Container
**Container settings:**
- **Name:** `datalineage-app`
- **Image source:** Select **"Azure Container Registry"**
- **Registry:** `chwadatalineage.azurecr.io`
- **Image:** `datalineage`
- **Image tag:** `latest`

**Container resource allocation:**
- **CPU cores:** `0.5` (can increase later if needed)
- **Memory (Gi):** `1` (can increase later if needed)

**Application ingress settings:**
- **Ingress:** ✅ **Enabled**
- **Ingress traffic:** Select **"Accepting traffic from anywhere"**
- **Ingress type:** **HTTP**
- **Target port:** `8000`

Click **"Next: Bindings >"** (skip this)

Click **"Next: Tags >"** (skip this)

#### 3.4 Review and Create
1. Click **"Review + create"**
2. Review your configuration
3. Click **"Create"**

Wait 3-5 minutes for deployment. Azure will:
- Create the Container Apps environment
- Deploy your container
- Configure networking and ingress
- Start your application

---

### Phase 4: Configure Environment Variables

#### 4.1 Navigate to Your Container App
1. Once deployment completes, click **"Go to resource"**
2. Or find it: Home → Resource Groups → rg-chwa-app → chwa-datalineage

#### 4.2 Add Environment Variables
1. In the left menu, go to **Settings** → **Environment variables**
2. Click **"+ Add"**

Add these variables one by one:

**Variable 1:**
- **Name:** `ALLOWED_ORIGINS`
- **Value:** `*`
- **Source:** Manual entry
- Click **"Add"**

**Variable 2:**
- **Name:** `PATH_OUTPUT_DIR`
- **Value:** `/app/data`
- **Source:** Manual entry
- Click **"Add"**

**Variable 3:**
- **Name:** `LOG_LEVEL`
- **Value:** `INFO`
- **Source:** Manual entry
- Click **"Add"**

3. Click **"Apply"** (top of page)
4. Click **"Confirm"** when prompted (this will restart the app)

Wait 1-2 minutes for the app to restart.

---

### Phase 5: Test Your Deployment

#### 5.1 Get Application URL
1. In your Container App overview page, find **"Application Url"**
2. It will look like: `https://chwa-datalineage.sweetforest-12345678.swedencentral.azurecontainerapps.io`
3. **Copy this URL**

#### 5.2 Test Endpoints
**Test Health Endpoint:**
```
https://your-app-url/health
```
Should return: `{"status":"ok","version":"4.0.3","uptime_seconds":...}`

**Test Application:**
```
https://your-app-url
```
Should load the Data Lineage Visualizer interface.

**Test API Docs:**
```
https://your-app-url/docs
```
Should show the FastAPI Swagger documentation.

#### 5.3 Test Upload Functionality
1. Open the application URL in your browser
2. Click **"Upload Parquet File"** or similar
3. Select a `.parquet` file from your computer
4. Verify it uploads successfully
5. Verify the data visualization appears

✅ **Deployment Complete!**

---

## 📊 Monitoring and Management

### View Logs
1. Go to your Container App in Azure Portal
2. **Monitoring** → **Log stream** (left menu)
3. View real-time logs from your application

### View Metrics
1. **Monitoring** → **Metrics** (left menu)
2. View CPU, Memory, Request count, Response time

### Restart Application
1. **Overview** (top)
2. Click **"Restart"**

### Scale Application (if needed)
1. **Application** → **Scale** (left menu)
2. Increase CPU cores (0.5 → 1.0 → 2.0)
3. Increase Memory (1 Gi → 2 Gi → 4 Gi)
4. Click **"Save"**

---

## 🔄 Updating Your Application

When you make changes to your code and want to update Azure:

### 1. Rebuild Docker Image Locally
```powershell
cd c:\Users\ChristianWagner\vscode\ws-datalineage\data_lineage
cd frontend

# Install dependencies (including Tailwind CSS)
npm install

# Build frontend with Vite (includes Tailwind CSS processing)
npm run build

cd ..
docker build -t datalineage:latest .
```

**Note:** The frontend now uses Tailwind CSS v3 installed via npm (not CDN). The build process includes:
- `tailwindcss` (v3.4.x) - CSS utility framework
- `postcss` & `autoprefixer` - CSS processing pipeline
- Build output includes processed CSS in `dist/assets/`

### 2. Test Locally (Optional but Recommended)
```powershell
docker stop datalineage-app
docker rm datalineage-app
docker run -d --name datalineage-app -p 8000:8000 datalineage:latest
# Test at http://localhost:8000
```

### 3. Push Updated Image to ACR
```powershell
docker tag datalineage:latest chwadatalineage.azurecr.io/datalineage:latest
docker push chwadatalineage.azurecr.io/datalineage:latest
```

### 4. Restart Container App
**Option A: Via Portal (GUI)**
1. Go to Azure Portal → Your Container App
2. Click **"Restart"** (it will pull the latest image)

**Option B: Via CLI**
```powershell
az containerapp update `
  --name chwa-datalineage `
  --resource-group rg-chwa-app `
  --image chwadatalineage.azurecr.io/datalineage:latest
```

---

## 💾 Persistent Storage (Optional)

By default, Container Apps are stateless. If you need to persist uploaded files and database:

### Add Azure Files Storage
1. Go to your Container App
2. **Settings** → **Volumes**
3. Click **"+ Add"**
4. **Volume type:** Azure Files
5. Follow wizard to create/connect Azure Storage Account
6. Mount path: `/app/data`

**Note:** For most use cases, re-uploading parquet files on restart is acceptable and simpler.

---

## 💰 Cost Optimization

**Current Setup (Basic):**
- Container Registry Basic: ~$5/month
- Container Apps: ~$0.000012/vCPU-second + $0.000002/GiB-second
- Estimated total: **~$30-50/month** for light usage

**To Reduce Costs:**
1. **Stop when not in use:**
   - Container Apps → Overview → Stop
   - Start only when needed
   
2. **Scale down:**
   - Reduce to minimum replicas: 0 (scales to 0 when idle)
   - Settings → Scale → Min replicas: 0

3. **Delete when not needed:**
   - Can delete/recreate easily since you have Docker image
   - Keep ACR with images for quick redeployment

---

## 🔧 Troubleshooting

### Issue: Application not loading
**Check:**
1. Logs: Monitoring → Log stream
2. Verify environment variables are set
3. Check Application Ingress is enabled
4. Verify port 8000 is configured

### Issue: Upload fails
**Check:**
1. ALLOWED_ORIGINS environment variable includes your domain
2. Check logs for specific error messages
3. Verify sufficient memory allocation (increase if needed)

### Issue: Container won't start
**Check:**
1. Image exists in ACR: Repositories → datalineage → latest
2. Registry credentials are correct
3. Check revision history: Revisions and replicas (left menu)
4. View failed revision logs

### Issue: Performance is slow
**Solutions:**
1. Increase CPU: Scale → CPU cores → 1.0 or higher
2. Increase Memory: Scale → Memory → 2 Gi or higher
3. Enable zone redundancy for production

---

## 🔐 Security Best Practices

### 1. Disable Public Registry Access
Once deployed:
1. Container Registry → Networking
2. Public access → Disabled
3. Add Container App to allowed networks

### 2. Use Managed Identity (Advanced)
Replace admin credentials with managed identity:
1. Container App → Settings → Identity
2. Enable System-assigned identity
3. Grant ACRPull role to Container Registry

### 3. Configure Custom Domain (Optional)
1. Container App → Settings → Custom domains
2. Add your domain (e.g., datalineage.yourdomain.com)
3. Configure DNS records
4. Add SSL certificate

### 4. Restrict CORS
Update environment variable:
- `ALLOWED_ORIGINS` → `https://your-actual-domain.com`

---

## 📚 Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Registry Documentation](https://learn.microsoft.com/en-us/azure/container-registry/)
- [Docker Documentation](https://docs.docker.com/)

---

## ✅ Deployment Checklist

- [ ] Created Azure Container Registry
- [ ] Enabled admin access on ACR
- [ ] Pushed Docker image to ACR
- [ ] Created Container App
- [ ] Configured environment variables
- [ ] Tested health endpoint
- [ ] Tested application UI
- [ ] Tested upload functionality
- [ ] Reviewed logs
- [ ] Saved application URL
- [ ] Documented any custom configuration

---

**🎉 Congratulations!** Your Data Lineage Visualizer is now running on Azure Container Apps!

**Your Application URL:** (save this)
```
https://chwa-datalineage.[generated-subdomain].swedencentral.azurecontainerapps.io
```
