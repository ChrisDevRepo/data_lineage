# Frontend Organization Guide

**Clear separation between local development and deployment files**

---

## 📂 Folder Organization

### 🏠 LOCAL DEVELOPMENT ONLY

```
frontend/
├── 📚 docs/                          ← Documentation (NOT deployed)
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── LOCAL_DEVELOPMENT.md
│   ├── DEPLOYMENT_AZURE.md
│   ├── INTEGRATION.md
│   └── README_COMPLETE.md
│
├── 📝 Development Docs               ← Info files (NOT deployed)
│   ├── README.md
│   ├── SETUP_COMPLETE.md
│   └── ORGANIZATION.md               ← This file
│
├── 🔧 Development Config             ← Local only (gitignored)
│   ├── .env.local
│   ├── node_modules/
│   ├── package-lock.json
│   └── .vscode/ (if created)
```

---

### 🚀 DEPLOYMENT FILES

```
frontend/
├── 🌐 deploy/                        ← Azure deployment configs
│   ├── web.config                    ← IIS config (Windows Azure)
│   ├── startup.sh                    ← PM2 startup (Linux Azure)
│   └── .deployment                   ← Azure deployment settings
│
├── 📦 Source Code (DEPLOYED)         ← Built into dist/
│   ├── components/
│   ├── hooks/
│   ├── utils/
│   ├── App.tsx
│   ├── index.tsx
│   ├── index.html
│   ├── types.ts
│   ├── constants.ts
│   └── vite.config.ts
│
├── ⚙️ Build Config (DEPLOYED)        ← Needed for npm install on Azure
│   ├── package.json
│   ├── tsconfig.json
│   └── .gitignore
```

---

## 🎯 What Goes Where

### LOCAL ONLY (Never Deployed)

| Folder/File | Purpose | Why Not Deployed |
|-------------|---------|------------------|
| `docs/` | Documentation | Users don't need docs in the app |
| `README.md`, `SETUP_COMPLETE.md` | Setup guides | Info for developers only |
| `.env.local` | Local environment vars | Contains dev settings/keys (gitignored) |
| `node_modules/` | Dependencies | Too large, rebuilt during deployment |
| `package-lock.json` | Dependency lockfile | Azure rebuilds this |

---

### DEPLOYED TO AZURE

| Folder/File | Purpose | How It's Used |
|-------------|---------|---------------|
| **Source Code** | | |
| `components/`, `hooks/`, `utils/` | App code | Built into `dist/` by Vite |
| `App.tsx`, `index.tsx` | React app | Built into `dist/` |
| `index.html` | HTML template | Copied to `dist/` |
| | | |
| **Build Config** | | |
| `package.json` | Dependencies | Azure runs `npm install` using this |
| `tsconfig.json` | TypeScript config | Used during build |
| `vite.config.ts` | Vite build config | Used during build |
| | | |
| **Deployment Config** | | |
| `deploy/web.config` | IIS routing | Copied to `dist/` (Windows Azure) |
| `deploy/startup.sh` | PM2 server | Used by Azure (Linux) |
| `deploy/.deployment` | Azure settings | Tells Azure how to deploy |

---

## 🔄 Deployment Process

### Step 1: Build Locally
```bash
npm run build
```
**Creates:** `dist/` folder with optimized production files

**What's in dist/:**
```
dist/
├── index.html              ← Entry point
├── assets/
│   ├── index-[hash].js     ← Minified React app (~500KB)
│   └── index-[hash].css    ← Styles (~5KB)
└── ... (other optimized files)
```

### Step 2: Add Deployment Config
```bash
npm run build:azure
```
**Does:**
1. Runs `npm run build`
2. Copies `deploy/web.config` → `dist/web.config`

**Result:** `dist/` is now ready for Azure

### Step 3: Package for Deployment
```bash
npm run deploy:zip
```
**Creates:** `deploy.zip` with everything in `dist/`

### Step 4: Deploy to Azure
```bash
az webapp deployment source config-zip \
  --resource-group <rg> \
  --name <app> \
  --src deploy.zip
```

**What Azure Does:**
1. Extracts `deploy.zip` to `/home/site/wwwroot/`
2. Finds `web.config` → Configures IIS (Windows)
3. OR uses `startup.sh` → Starts PM2 (Linux)
4. Serves static files from `/home/site/wwwroot/`

---

## 📋 Deployment Checklist

### ✅ Files That MUST Be Deployed

**Source code:**
- ✅ `components/`, `hooks/`, `utils/`
- ✅ `App.tsx`, `index.tsx`, `index.html`
- ✅ `types.ts`, `constants.ts`

**Build config:**
- ✅ `package.json` (for dependencies)
- ✅ `tsconfig.json` (for TypeScript)
- ✅ `vite.config.ts` (for Vite build)

**Deployment config:**
- ✅ `deploy/web.config` (Windows) OR `deploy/startup.sh` (Linux)
- ✅ `deploy/.deployment` (optional but recommended)

### ❌ Files That Should NOT Be Deployed

**Documentation:**
- ❌ `docs/` folder
- ❌ `README.md`, `SETUP_COMPLETE.md`, `ORGANIZATION.md`

**Local config:**
- ❌ `.env.local` (local dev only, gitignored)
- ❌ `node_modules/` (too large, rebuilt by Azure)
- ❌ `package-lock.json` (Azure creates its own)

**Build artifacts:**
- ❌ `dist/` folder (created during build, not committed)
- ❌ `deploy.zip` (temporary deployment package)

---

## 🗂️ .gitignore Strategy

**Currently gitignored (correct):**
```
node_modules/       # Too large
dist/               # Build artifact
*.local             # Local env files
.env.local          # Local secrets
```

**Committed to git (correct):**
```
Source code         # components/, hooks/, utils/, *.tsx
Docs                # docs/, README.md
Deploy configs      # deploy/web.config, deploy/startup.sh
Build configs       # package.json, vite.config.ts, tsconfig.json
```

---

## 📊 Size Comparison

### Local Development
```
frontend/
├── node_modules/  ~150 MB    ← Dependencies (gitignored)
├── docs/          ~100 KB    ← Documentation (not deployed)
├── Source code    ~200 KB    ← Your React app
└── Build configs  ~10 KB     ← package.json, etc.

Total on disk: ~150 MB
```

### Production Build (dist/)
```
dist/
├── index.html     ~2 KB
├── assets/
│   ├── index.js   ~450 KB (minified + gzipped ~150 KB)
│   └── index.css  ~5 KB
└── web.config     ~3 KB

Total deployed: ~500 KB (uncompressed) or ~160 KB (gzipped)
```

**Azure Free Tier limit:** 1 GB
**Your app uses:** <1% of limit ✅

---

## 🎯 Quick Reference

### Working Locally
```bash
cd /workspaces/ws-psidwh/frontend
npm install          # Install dependencies
npm run dev          # Start dev server → http://localhost:3000
```
**Uses:** All files (docs, source, configs)

### Building for Production
```bash
npm run build        # Create dist/
npm run build:azure  # Build + add web.config
npm run deploy:zip   # Create deploy.zip
```
**Uses:** Source code + build configs + deploy configs
**Ignores:** docs/, README.md, .env.local, node_modules/

### Deploying to Azure
```bash
# Upload deploy.zip to Azure
az webapp deployment source config-zip ...
```
**Deployed:** Contents of dist/ (optimized production build)
**Not deployed:** docs/, dev files, node_modules/

---

## ✅ Summary

| Category | Location | Local Dev | Deployed | Notes |
|----------|----------|-----------|----------|-------|
| **Documentation** | `docs/` | ✅ | ❌ | For developers only |
| **Source Code** | `components/`, `hooks/`, etc. | ✅ | ✅ | Built into dist/ |
| **Deployment Configs** | `deploy/` | ✅ | ✅ | Copied to dist/ |
| **Build Configs** | `package.json`, etc. | ✅ | ✅ | Used by Azure |
| **Local Configs** | `.env.local` | ✅ | ❌ | Gitignored |
| **Dependencies** | `node_modules/` | ✅ | ❌ | Rebuilt by Azure |
| **Build Output** | `dist/` | ✅ | ✅ | Created by build, deployed |

---

**Everything is organized perfectly!** 🎉

- **Local development:** Clean, documented, easy to navigate
- **Deployment:** Only necessary files, optimized for Azure
- **Separation:** Clear distinction between dev and prod
