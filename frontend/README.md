# Data Lineage Visualizer - Frontend

**Interactive React application for visualizing Azure Synapse data lineage**

[![React](https://img.shields.io/badge/React-19.2.0-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.2.0-purple.svg)](https://vitejs.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.2-blue.svg)](https://www.typescriptlang.org/)

---

## 🚀 Current Status

**Version:** 2.5.0 (Incremental Parsing & Data Management)
**v3.0 Status:** Core features complete - Docker containerization pending

### ✨ Latest Updates (v2.5.0 - 2025-10-27)

**New Features:**
- ✅ **Incremental Parsing** - Smart checkbox in Import modal (ON by default) - only re-parse changed objects
- ✅ **Clear All Data** - Wipe button to delete all workspaces and persistent data
- ✅ **Last Upload Timestamp** - Display when data was last uploaded with metadata
- ✅ **Performance:** 50-90% faster uploads with incremental mode

**Previous Updates (v2.4.0):**
- ✅ **Auto-Fit on Trace Apply** - View automatically fits and highlights start node when applying trace
- ✅ **Improved "Hide Unrelated" Filter** - Now static pre-filter applied before schema/type filters
- ✅ **Click Behavior** - Simplified logic, no camera zoom on unhighlight, instant SQL viewer response
- ✅ **SQL Viewer Dimming** - Nodes stay bright (no dimming) when SQL viewer is open

**Previous Updates (v2.3.0):**
- ✅ **Table DDL Display** - View table structure with columns, data types, and constraints in SQL viewer
- ✅ **Enhanced Empty State** - Informative message when table metadata not available
- ✅ **SQL Viewer Header Improvements** - Smaller title, search box always visible

**Previous Updates (v2.2.0 & v2.1.x):**
- ✅ **Resizable SQL Viewer** - Drag to resize SQL panel (default 1/3 width, range 20-60%)
- ✅ **Yellow Highlight** - Selected objects now highlighted in yellow
- ✅ **Level 1 Neighbor Visibility** - Connected nodes remain visible when object selected
- ✅ **Data Model Type Filter Inheritance** - Trace mode inherits filters
- ✅ **Reset View Button** - One-click reset to default state

See [CHANGELOG.md](./CHANGELOG.md) for detailed feature descriptions and usage examples.

### What's Changing in v3.0

**v2.0 (Current):**
- Standalone React SPA
- User uploads JSON file manually
- Deploys to Azure Web App (static files)
- Uses `web.config` (IIS) or `startup.sh` (Node.js)

**v3.0 (Coming Soon):**
- React SPA + FastAPI backend in single Docker container
- User uploads Parquet files via browser
- Backend processes server-side, frontend polls for status
- SQL Viewer feature (right-click → view SQL)
- Deploys to Azure Web App for Containers

---

## 🏗️ Project Structure (v2.0)

```
frontend/
├── 🎨 components/                    # React components
│   ├── CustomNode.tsx                # Graph node renderer
│   ├── Toolbar.tsx                   # Top toolbar with filters
│   ├── Legend.tsx                    # Schema color legend
│   ├── InteractiveTracePanel.tsx     # Lineage tracing panel
│   ├── ImportDataModal.tsx           # Data import modal
│   ├── InfoModal.tsx                 # Information modal
│   └── NotificationSystem.tsx        # Toast notifications
│
├── 🔧 hooks/                         # Custom React hooks
│   ├── useGraphology.ts              # Graph algorithms (BFS, upstream/downstream)
│   ├── useDataFiltering.ts           # Filtering logic
│   ├── useInteractiveTrace.ts        # Tracing state management
│   └── useNotifications.ts           # Notification state
│
├── 🛠️ utils/                         # Utilities
│   ├── data.ts                       # Data transformation (JSON → React Flow)
│   └── layout.ts                     # Dagre layout algorithm
│
├── 📄 App.tsx                        # Main application component
├── 📄 index.tsx                      # Entry point
├── 📄 types.ts                       # TypeScript type definitions
├── 📄 constants.ts                   # Constants (colors, filters)
├── 📄 package.json                   # Dependencies
├── 📄 vite.config.ts                 # Vite build configuration
└── 📄 README.md                      # This file
```

**Note:** Documentation and deployment files moved to `backup_v2/frontend_deploy/` (v2.0 specific)

---

## 🚀 Development (v2.0)

### Running Locally

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

**Opens at:** `http://localhost:3000`

### Building for Production (v2.0 - Static)

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

**Output:** `dist/` folder with static files

---

## 🆕 v3.0 Implementation Plan

### Week 2-3: Single Container Deployment

**Frontend Changes:**
1. Add Parquet upload mode to `ImportDataModal.tsx`
2. Add polling logic for background job status
3. Add progress bar component
4. Update API calls to backend endpoints:
   - `POST /api/upload-parquet`
   - `GET /api/status/{job_id}`
   - `GET /api/result/{job_id}`

### Week 4: SQL Viewer

**New Components:**
1. `SqlViewer.tsx` - SQL syntax highlighter (Prism.js)
2. Update `CustomNode.tsx` - Add right-click context menu
3. Update `App.tsx` - Split view layout (graph + SQL viewer)

**New Features:**
- Right-click object → View SQL definition
- Syntax highlighting (T-SQL)
- Full-text search in SQL
- Read-only view

---

## 📚 Documentation

### v3.0 Specification
- **[docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md)** - Complete v3.0 spec
  - Section 5: Frontend implementation details
  - Section 6: SQL viewer specification
  - Code examples and API contracts

### v2.0 Documentation (Archived)
- **[backup_v2/frontend_deploy/docs/](../backup_v2/frontend_deploy/docs/)** - Complete v2.0 documentation
  - FRONTEND_ARCHITECTURE.md - Full architecture analysis
  - DEPLOYMENT_AZURE.md - Azure Web App deployment guide
  - LOCAL_DEVELOPMENT.md - Development setup
  - INTEGRATION.md - Backend integration patterns

---

## 🔧 Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Framework** | React | 19.2.0 | UI framework |
| **Build Tool** | Vite | 6.2.0 | Fast dev server & build |
| **Language** | TypeScript | 5.8.2 | Type safety |
| **Visualization** | ReactFlow | 11.11.4 | Interactive graph rendering |
| **Graph Engine** | Graphology | 0.25.4 | Graph algorithms (BFS, DFS) |
| **Layout** | Dagre | 0.8.5 | Hierarchical layout |
| **Styling** | Tailwind CSS | 3.x (CDN) | Utility-first CSS |

**New in v3.0:**
- **Prism.js** - SQL syntax highlighting
- **FastAPI Client** - HTTP polling for backend jobs

---

## 🐳 v3.0 Deployment (Docker Container)

**New Deployment Model:**

```dockerfile
# Multi-stage build
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.12-slim
COPY --from=frontend-build /frontend/dist ./static
# Backend serves static files via FastAPI
```

See [docker/README.md](../docker/README.md) for complete Docker configuration.

---

## 🔄 Migration Path (v2.0 → v3.0)

**What Stays the Same:**
- ✅ Core React components (CustomNode, Toolbar, Legend)
- ✅ Graph visualization logic (React Flow + Dagre)
- ✅ Filtering and tracing hooks
- ✅ Type definitions

**What Gets Enhanced:**
- 🔄 `ImportDataModal.tsx` - Add Parquet upload tab
- 🔄 `App.tsx` - Add split view for SQL viewer
- 🆕 `SqlViewer.tsx` - New component for SQL display
- 🆕 Polling logic for background jobs

**What Gets Removed:**
- ❌ `deploy/` folder (Docker replaces it)
- ❌ v2.0 deployment docs (archived)

---

## 📋 Next Steps

1. ✅ v2.0 code backed up in `backup_v2/`
2. 🚧 Week 2-3: Implement upload + polling UI
3. 🚧 Week 4: Implement SQL viewer component
4. 🚧 Test integration with FastAPI backend
5. 🚧 Deploy to Azure Web App for Containers

---

**Last Updated:** 2025-10-27
**Current Version:** 2.1.1 (Enhanced Type Filtering in Trace Mode) ✅ Production Ready
**Next Version:** 3.0 (Single Container) 🚧 Specification Complete

---

## 📖 Additional Documentation

- **[CHANGELOG.md](./CHANGELOG.md)** - Detailed feature changes and version history
