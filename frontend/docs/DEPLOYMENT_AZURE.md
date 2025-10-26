# Azure Web App Deployment Guide

**Application:** Data Lineage Visualizer
**Target Platform:** Azure Web App (App Service)
**Recommended Tier:** Free (F1) or Basic (B1)
**Last Updated:** 2025-10-26

---

## Table of Contents

1. [Azure Web App Free Tier Assessment](#azure-web-app-free-tier-assessment)
2. [Prerequisites](#prerequisites)
3. [Deployment Methods](#deployment-methods)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Configuration](#configuration)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Cost Analysis](#cost-analysis)

---

## Azure Web App Free Tier Assessment

### ✅ Compatibility: **EXCELLENT**

The Data Lineage Visualizer is **perfectly suited** for Azure Web App Free tier deployment:

| Requirement | Free Tier Limit | This App | Status |
|-------------|-----------------|----------|--------|
| **App Type** | Static SPA supported | React SPA | ✅ Perfect fit |
| **Disk Space** | 1 GB | ~2-5 MB (built) | ✅ <1% usage |
| **Memory** | Shared (60 min/day CPU) | Client-side rendering | ✅ No server CPU |
| **Bandwidth** | 165 MB/day | ~500 KB per user | ✅ ~330 users/day |
| **Runtime** | Node.js, .NET, etc. | Static files only | ✅ No runtime needed |
| **Custom Domain** | ❌ Not available | *.azurewebsites.net | ⚠️ Limitation |
| **SSL/HTTPS** | ✅ Free SSL | Required | ✅ Included |

### Why This App Is Perfect for Free Tier

1. **Pure Static SPA:** No server-side rendering, no API calls, no backend
2. **Small Bundle Size:** ~500 KB - 1.5 MB total (CSS via CDN)
3. **Client-Side Only:** All computation happens in the browser
4. **No Persistent State:** No database or storage needed
5. **Low Bandwidth:** Users load once, interact locally

### Recommended Tier Upgrade Path

| Tier | When to Upgrade | Monthly Cost (USD) |
|------|-----------------|---------------------|
| **F1 (Free)** | Development, testing, <100 users/day | $0.00 |
| **B1 (Basic)** | Production, custom domain, 1000+ users/day | ~$13.14 |
| **S1 (Standard)** | High traffic, auto-scaling, staging slots | ~$69.35 |

**Start with F1, upgrade to B1 when you need:**
- Custom domain (e.g., `lineage.yourcompany.com`)
- More than 60 CPU minutes/day
- Deployment slots (staging/production)

---

## Prerequisites

### Required Tools

1. **Azure Account**
   - [Sign up for free](https://azure.microsoft.com/free/)
   - $200 free credit for 30 days + 12 months free services

2. **Azure CLI** (Recommended)
   ```bash
   # Install on Linux/WSL
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

   # Verify installation
   az --version
   ```

3. **Node.js & npm** (for building)
   ```bash
   # Check versions
   node --version  # Should be 18.x or 20.x
   npm --version   # Should be 9.x or 10.x
   ```

4. **Optional: VS Code + Extensions**
   - [Azure App Service Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureappservice)
   - [Azure Account Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode.azure-account)

### Azure Resource Requirements

You'll create:
- 1× Resource Group (container for resources)
- 1× App Service Plan (F1 tier)
- 1× Web App (Node.js stack)

---

## Deployment Methods

Choose one of these three methods:

### Method 1: Azure CLI (Recommended) ⭐
**Best for:** Automation, CI/CD, command-line users
**Time:** ~5 minutes

### Method 2: VS Code Extension
**Best for:** Visual Studio Code users, GUI preference
**Time:** ~5 minutes

### Method 3: Azure Portal + ZIP Deploy
**Best for:** GUI users, manual deployments
**Time:** ~10 minutes

---

## Step-by-Step Deployment

### Method 1: Azure CLI Deployment (Recommended)

#### Step 1: Login to Azure

```bash
# Login and follow browser prompt
az login

# Verify subscription
az account show

# (Optional) Set default subscription if you have multiple
az account set --subscription "<subscription-id>"
```

#### Step 2: Create Resource Group

```bash
# Choose a location near your users
# Examples: eastus, westus2, westeurope, southeastasia
LOCATION="eastus"
RESOURCE_GROUP="rg-lineage-visualizer"

az group create --name $RESOURCE_GROUP --location $LOCATION
```

#### Step 3: Create App Service Plan (Free Tier)

```bash
APP_SERVICE_PLAN="plan-lineage-free"

az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku F1 \
  --is-linux
```

**Notes:**
- `--sku F1`: Free tier
- `--is-linux`: Linux is more efficient for Node.js
- Windows alternative: Remove `--is-linux` flag

#### Step 4: Create Web App

```bash
# Choose a unique name (must be globally unique)
WEB_APP_NAME="lineage-viz-yourname-$(date +%s)"

az webapp create \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "NODE:20-lts"
```

**Your app will be available at:** `https://${WEB_APP_NAME}.azurewebsites.net`

#### Step 5: Build the Application

```bash
# Navigate to frontend directory
cd /workspaces/ws-psidwh/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

**Output:** `dist/` folder with optimized static files

#### Step 6: Deploy to Azure

```bash
# Navigate to dist folder
cd dist

# Create deployment package
zip -r ../deploy.zip .

# Deploy using Azure CLI
cd ..
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src deploy.zip
```

#### Step 7: Configure Web App (SPA Routing)

```bash
# Enable SPA routing (redirect all routes to index.html)
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --startup-file "pm2 serve /home/site/wwwroot --no-daemon --spa"
```

**Alternative (using web.config for Windows):**
- See [web.config](#webconfigxml-for-windows) section below

#### Step 8: Verify Deployment

```bash
# Open in browser
az webapp browse --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

# Or manually visit
echo "Visit: https://${WEB_APP_NAME}.azurewebsites.net"
```

---

### Method 2: VS Code Extension Deployment

#### Step 1: Install Extensions

1. Open VS Code
2. Install "Azure App Service" extension
3. Install "Azure Account" extension
4. Sign in to Azure (click Azure icon in sidebar)

#### Step 2: Build Application

```bash
cd /workspaces/ws-psidwh/frontend
npm install
npm run build
```

#### Step 3: Deploy via Extension

1. Click **Azure icon** in VS Code sidebar
2. Right-click on **App Services** → "Create New Web App... (Advanced)"
3. Follow prompts:
   - **Name:** `lineage-viz-yourname`
   - **OS:** Linux
   - **Runtime:** Node 20 LTS
   - **Pricing Tier:** F1 Free
   - **Resource Group:** Create new or select existing
   - **App Service Plan:** Create new (F1)
4. Right-click the created app → **Deploy to Web App**
5. Select `frontend/dist` folder
6. Confirm deployment

#### Step 4: Configure Startup

1. In VS Code Azure panel, right-click your app
2. Select "Open in Portal"
3. Navigate to **Configuration** → **General Settings**
4. Set **Startup Command:**
   ```
   pm2 serve /home/site/wwwroot --no-daemon --spa
   ```
5. Click **Save**

---

### Method 3: Azure Portal + ZIP Deploy

#### Step 1: Create Resources via Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search "Web App"
3. Fill in details:
   - **Resource Group:** Create new (e.g., `rg-lineage-visualizer`)
   - **Name:** `lineage-viz-yourname` (must be unique)
   - **Publish:** Code
   - **Runtime stack:** Node 20 LTS
   - **Operating System:** Linux
   - **Region:** Choose nearest
   - **Pricing Plan:** Free F1
4. Click **Review + Create** → **Create**

#### Step 2: Build Application Locally

```bash
cd /workspaces/ws-psidwh/frontend
npm install
npm run build
cd dist
zip -r ../deploy.zip .
```

#### Step 3: Deploy via Kudu

1. In Azure Portal, navigate to your Web App
2. Go to **Advanced Tools** (Kudu) → **Go**
3. Click **Tools** → **ZIP Push Deploy**
4. Drag `deploy.zip` into the deployment window
5. Wait for extraction to complete

#### Step 4: Configure Startup

1. Back in Azure Portal, go to **Configuration** → **General Settings**
2. Set **Startup Command:**
   ```
   pm2 serve /home/site/wwwroot --no-daemon --spa
   ```
3. Click **Save** → **Continue**
4. Wait for app to restart

---

## Configuration

### Environment Variables

This app currently doesn't require environment variables for production. The `GEMINI_API_KEY` in `.env.local` is only for AI Studio development and is **not used** in the deployed app.

**To add environment variables in the future:**

```bash
# Via Azure CLI
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings KEY1=value1 KEY2=value2
```

**Via Portal:**
1. Go to **Configuration** → **Application settings**
2. Click **+ New application setting**
3. Add key-value pairs
4. Click **Save**

### SPA Routing Configuration

#### Option A: PM2 Serve (Linux - Recommended)

**Startup Command:**
```bash
pm2 serve /home/site/wwwroot --no-daemon --spa
```

**What it does:**
- Serves static files from `/home/site/wwwroot` (deployment directory)
- `--spa` flag: Redirects all routes to `index.html` (React Router support)
- `--no-daemon`: Keeps process running (required for Azure)

#### Option B: web.config (Windows)

See [web.config section](#web-config-for-windows) below for XML configuration.

### CORS Configuration (If Needed)

If you add a backend API later:

```bash
az webapp cors add \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --allowed-origins https://yourapi.example.com
```

---

## Post-Deployment

### Verify Deployment

1. **Check App Status:**
   ```bash
   az webapp show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --query state
   ```
   Should return: `"Running"`

2. **Open in Browser:**
   ```bash
   az webapp browse --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
   ```

3. **Check Logs:**
   ```bash
   az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
   ```

### Performance Optimization

1. **Enable Compression:**
   ```bash
   # Already enabled by default in Azure App Service
   ```

2. **Enable CDN (Optional, for high traffic):**
   - Create Azure CDN profile
   - Point to your Web App
   - Reduces bandwidth usage on Free tier

3. **Monitor Performance:**
   - Go to **Monitoring** → **Metrics** in Azure Portal
   - Watch: Response time, HTTP 4xx/5xx errors

### Update Deployment

To deploy updates:

```bash
# Rebuild
cd /workspaces/ws-psidwh/frontend
npm run build

# Redeploy
cd dist
zip -r ../deploy.zip .
cd ..
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src deploy.zip
```

### Custom Domain (Requires B1 or higher)

1. Upgrade to Basic tier:
   ```bash
   az appservice plan update \
     --name $APP_SERVICE_PLAN \
     --resource-group $RESOURCE_GROUP \
     --sku B1
   ```

2. Add custom domain:
   ```bash
   az webapp config hostname add \
     --webapp-name $WEB_APP_NAME \
     --resource-group $RESOURCE_GROUP \
     --hostname lineage.yourdomain.com
   ```

3. Configure DNS:
   - Add CNAME record pointing to `${WEB_APP_NAME}.azurewebsites.net`

---

## Troubleshooting

### Common Issues

#### 1. App Shows "Application Error"

**Symptoms:** Blank page or error message

**Solutions:**
```bash
# Check logs
az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

# Verify startup command
az webapp config show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP \
  --query appCommandLine
```

**Fix startup command:**
```bash
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --startup-file "pm2 serve /home/site/wwwroot --no-daemon --spa"
```

#### 2. 404 on Refresh (React Router)

**Cause:** SPA routing not configured

**Solution:** Ensure `--spa` flag is in startup command or web.config is correct

#### 3. Deployment Fails (Disk Space)

**Symptoms:** "Insufficient storage" error

**Solution:**
```bash
# Clean up old deployments
az webapp deployment list --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
# Delete old deployment if needed via Portal > Deployment Center > Logs
```

#### 4. Slow Performance

**Cause:** Free tier CPU throttling (60 min/day limit reached)

**Solutions:**
- Wait for CPU quota to reset (daily)
- Upgrade to B1 tier (~$13/month)
- Optimize bundle size (check if Tailwind can be purged more)

#### 5. "App name not available"

**Cause:** Name already taken globally

**Solution:** Choose a different unique name (add random suffix)

### Debug Commands

```bash
# View all app settings
az webapp config appsettings list \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP

# View deployment history
az webapp deployment list \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Restart app
az webapp restart \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP

# SSH into container (Linux only)
az webapp ssh --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
```

### Get Help

- **Azure Portal:** Use "Diagnose and solve problems" feature
- **Azure CLI:** `az webapp --help`
- **Logs:** Always check Application Insights or Log Stream
- **Community:** [Stack Overflow - azure-web-app-service](https://stackoverflow.com/questions/tagged/azure-web-app-service)

---

## Cost Analysis

### Free Tier (F1)

| Component | Cost | Limit |
|-----------|------|-------|
| Web App | $0.00/month | 1 GB disk, 60 CPU min/day |
| Bandwidth | $0.00 | 165 MB/day outbound |
| SSL Certificate | $0.00 | *.azurewebsites.net |
| **Total** | **$0.00/month** | **Good for <100 users/day** |

### Basic Tier (B1)

| Component | Cost (USD) | Benefit |
|-----------|------------|---------|
| Web App | $13.14/month | 10 GB disk, 1 core, 1.75 GB RAM |
| Custom Domain | Included | Your own domain + SSL |
| Always On | Included | No cold starts |
| **Total** | **$13.14/month** | **Production ready** |

### Cost Optimization Tips

1. **Use Free Tier for Dev/Test:** Switch to B1 only for production
2. **Delete Unused Apps:** Remove test deployments
3. **Share App Service Plan:** Deploy multiple apps to same plan
4. **Monitor Usage:** Set billing alerts in Azure Portal
5. **Auto-shutdown:** Delete resources when not in use (dev environments)

---

## Production Checklist

Before going live:

- [ ] Test app thoroughly in Free tier
- [ ] Verify all features work (import, export, trace)
- [ ] Check mobile responsiveness
- [ ] Enable HTTPS (automatic with Azure)
- [ ] Set up monitoring (Application Insights - optional)
- [ ] Configure custom domain (if upgrading to B1)
- [ ] Set up backup/restore (B1+)
- [ ] Document app URL for users
- [ ] Create deployment runbook for updates
- [ ] Set up staging slot (S1+ only)

---

## Next Steps

1. **Load Production Data:**
   - Generate `frontend_lineage.json` from Python backend
   - Upload via Import Data modal
   - Or rebuild app with production data in `utils/data.ts`

2. **Integrate with Backend:**
   - See [INTEGRATION.md](INTEGRATION.md) for connecting to lineage parser

3. **Monitor & Scale:**
   - Add Application Insights for telemetry
   - Upgrade to B1 when traffic increases
   - Set up auto-scaling (S1+)

---

## web.config for Windows

If deploying to **Windows** App Service instead of Linux, create this file:

**File:** `frontend/dist/web.config`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <!-- Redirect HTTP to HTTPS -->
        <rule name="Force HTTPS" stopProcessing="true">
          <match url="(.*)" />
          <conditions>
            <add input="{HTTPS}" pattern="^OFF$" />
          </conditions>
          <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
        </rule>

        <!-- SPA Routing: Redirect all requests to index.html -->
        <rule name="React Routes" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/" />
        </rule>
      </rules>
    </rewrite>

    <!-- Enable gzip compression -->
    <urlCompression doStaticCompression="true" doDynamicCompression="true" />

    <!-- Set default document -->
    <defaultDocument>
      <files>
        <clear />
        <add value="index.html" />
      </files>
    </defaultDocument>

    <!-- MIME types for modern file extensions -->
    <staticContent>
      <mimeMap fileExtension=".json" mimeType="application/json" />
      <mimeMap fileExtension=".woff" mimeType="application/font-woff" />
      <mimeMap fileExtension=".woff2" mimeType="application/font-woff2" />
      <mimeMap fileExtension=".svg" mimeType="image/svg+xml" />
    </staticContent>
  </system.webServer>
</configuration>
```

**To deploy with web.config:**

```bash
# Copy web.config to dist folder BEFORE zipping
cp web.config dist/
cd dist
zip -r ../deploy.zip .
cd ..
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src deploy.zip
```

---

## References

- [Azure App Service Documentation](https://learn.microsoft.com/en-us/azure/app-service/)
- [Azure App Service Pricing](https://azure.microsoft.com/en-us/pricing/details/app-service/)
- [Deploy React App to Azure](https://learn.microsoft.com/en-us/azure/app-service/quickstart-nodejs)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html)
- [PM2 Documentation](https://pm2.keymetrics.io/docs/usage/expose/)

---

**End of Deployment Guide**
