# Data Lineage Visualizer - Frontend

**Version:** 2.9.4 (Schema Filter Enhancements)
React application for visualizing Azure Synapse data lineage.

## Quick Start

```bash
cd frontend
npm install
npm run dev  # Opens at http://localhost:3000
```

**Restart after code changes:**
```bash
cd frontend && lsof -ti:3000 | xargs -r kill && npm run dev
```

## Technology Stack

- React 19.2.0 + TypeScript 5.8.2
- Vite 6.2.0 (build tool)
- ReactFlow 11.11.4 (graph visualization)
- Graphology 0.25.4 (graph algorithms)
- Dagre 0.8.5 (layout engine)
- Monaco Editor 4.7.0 (SQL viewer)
- Tailwind CSS 3.x

## Key Features

- **Interactive Graph** - ReactFlow-based lineage visualization with zoom/pan
- **Path Tracing** - Upstream/downstream exploration, path-between-nodes mode
- **SQL Viewer** - Monaco Editor with syntax highlighting, search (Ctrl+F)
- **Detail Search** - Full-text search with schema/type filters, resizable panels
- **DDL Display** - View table structures and stored procedure definitions
- **Smart Filtering** - Schema, object type, pattern-based filtering
- **Trace Lock** - Preserve traced subset after exiting trace mode
## Build & Deploy

```bash
# Production build
npm run build  # Output: dist/

# Preview production build
npm run preview

# Type checking
npm run type-check
```

---

**Last Updated:** 2025-01-23
