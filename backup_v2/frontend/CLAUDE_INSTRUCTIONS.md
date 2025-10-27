# Instructions for Claude Code - Frontend

**Quick reference for Claude when working with the frontend**

---

## ✅ What Claude Should Know

### Folder Organization

```
frontend/
├── 📚 docs/              ← Documentation ONLY (never deployed)
├── 🚀 deploy/            ← Azure deployment configs ONLY
├── 🎨 components/        ← React components (source code)
├── 🪝 hooks/             ← Custom hooks (source code)
├── 🛠️ utils/             ← Utilities (source code)
└── 📝 README.md          ← Main entry point
```

**Key Rules:**
- ✅ Documentation files go in `docs/`
- ✅ Deployment configs go in `deploy/`
- ✅ Source code stays in organized folders
- ❌ Never create .md files in root (use docs/)
- ❌ Never put configs in root (use deploy/)

---

## 🎯 Common Tasks

### Starting the Frontend
```bash
cd /workspaces/ws-psidwh/frontend
npm install  # Only first time
npm run dev  # http://localhost:3000
```

**Important:** Node.js and npm are already installed in devcontainer!

### Building for Azure
```bash
npm run build:azure  # Build + copy web.config
npm run deploy:zip   # Create deploy.zip
```

### Documentation References
When users ask about frontend:
- Quick start → [frontend/README.md](README.md)
- Organization → [frontend/ORGANIZATION.md](ORGANIZATION.md)
- Development → [frontend/docs/LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md)
- Deployment → [frontend/docs/DEPLOYMENT_AZURE.md](docs/DEPLOYMENT_AZURE.md)
- Architecture → [frontend/docs/FRONTEND_ARCHITECTURE.md](docs/FRONTEND_ARCHITECTURE.md)
- Backend integration → [frontend/docs/INTEGRATION.md](docs/INTEGRATION.md)

---

## 📋 File Placement Guidelines

### Creating New Documentation
**DO:**
```bash
# Create in docs/ folder
frontend/docs/NEW_GUIDE.md
```

**DON'T:**
```bash
# Never create in root
frontend/NEW_GUIDE.md  ❌
```

### Adding Deployment Configs
**DO:**
```bash
# Create in deploy/ folder
frontend/deploy/new-config.yml
```

**DON'T:**
```bash
# Never in root
frontend/new-config.yml  ❌
```

### Adding React Components
**DO:**
```bash
# Create in components/ folder
frontend/components/NewComponent.tsx
```

---

## 🔧 Package.json Scripts

**Available commands:**
```json
{
  "dev": "vite",                    // Start dev server
  "build": "vite build",            // Build for production
  "build:azure": "...",             // Build + prepare for Azure
  "deploy:prepare": "...",          // Copy web.config to dist/
  "deploy:zip": "...",              // Create deploy.zip
  "preview": "vite preview",        // Preview build
  "type-check": "tsc --noEmit",     // Type check
  "clean": "rm -rf dist ..."        // Clean artifacts
}
```

**Important:** `deploy:prepare` copies from `deploy/web.config` to `dist/`

---

## 🚫 Common Mistakes to Avoid

### ❌ DON'T
```bash
# Don't tell users to install Node/npm (already installed)
npm install node  ❌

# Don't create docs in root
echo "# Guide" > frontend/GUIDE.md  ❌

# Don't put configs in root
cp web.config frontend/  ❌

# Don't use old paths
cp web.config dist/  ❌ (should be: cp deploy/web.config dist/)
```

### ✅ DO
```bash
# Use correct paths
cp deploy/web.config dist/  ✅

# Create docs in docs/
echo "# Guide" > frontend/docs/GUIDE.md  ✅

# Reference organized structure
"See frontend/docs/LOCAL_DEVELOPMENT.md"  ✅
```

---

## 🔗 Integration with Backend

**Frontend ← JSON ← Backend**

The frontend and backend are **decoupled**:
1. Backend generates: `lineage_output/frontend_lineage.json`
2. Frontend imports via: **Import Data** button in UI
3. No real-time API or shared server

**Both run independently in the same devcontainer:**
```bash
# Terminal 1: Backend
python lineage_v3/main.py run --parquet parquet_snapshots/

# Terminal 2: Frontend
cd frontend && npm run dev

# User loads JSON via Import Data UI
```

---

## 📖 Documentation Structure

All comprehensive docs are in `frontend/docs/`:

| File | Purpose | Lines |
|------|---------|-------|
| `FRONTEND_ARCHITECTURE.md` | Complete architecture analysis | ~600 |
| `DEPLOYMENT_AZURE.md` | Azure deployment guide | ~800 |
| `LOCAL_DEVELOPMENT.md` | Development workflow | ~400 |
| `INTEGRATION.md` | Backend integration patterns | ~500 |
| `README_COMPLETE.md` | Full setup summary | ~300 |

**Root level docs:**
- `README.md` - Quick start (entry point)
- `ORGANIZATION.md` - Folder structure guide
- `SETUP_COMPLETE.md` - Setup summary
- `CLAUDE_INSTRUCTIONS.md` - This file

---

## 🎯 Quick Answers

**Q: How do I start the frontend?**
```bash
cd frontend && npm run dev
```

**Q: Where is the documentation?**
- `frontend/docs/` folder

**Q: How do I deploy to Azure?**
- See `frontend/docs/DEPLOYMENT_AZURE.md`

**Q: Where do deployment configs go?**
- `frontend/deploy/` folder

**Q: Do I need to install Node.js?**
- No, it's already installed in devcontainer

**Q: How does frontend connect to backend?**
- Via JSON files, see `frontend/docs/INTEGRATION.md`

---

## ✅ Summary for Claude

**When working with frontend:**
1. ✅ Know the folder structure (docs/, deploy/, components/, etc.)
2. ✅ Reference docs in the correct folders
3. ✅ Don't create new files in root (use organized folders)
4. ✅ Remember npm is already installed
5. ✅ Frontend and backend are decoupled (JSON integration)
6. ✅ Always point users to organized documentation

**This keeps the frontend clean, organized, and maintainable!**
