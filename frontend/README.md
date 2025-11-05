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
- **⚡ High Performance** - Optimized for 5,000+ nodes (debouncing, caching, smart rendering)

## Documentation

- **[CHANGELOG.md](./CHANGELOG.md)** - Version history
- **[docs/FRONTEND_ARCHITECTURE.md](./docs/FRONTEND_ARCHITECTURE.md)** - Architecture deep dive
- **[docs/LOCAL_DEVELOPMENT.md](./docs/LOCAL_DEVELOPMENT.md)** - Development guide
- **[docs/DEPLOYMENT_AZURE.md](./docs/DEPLOYMENT_AZURE.md)** - Azure deployment
- **[docs/UI_STANDARDIZATION_GUIDE.md](./docs/UI_STANDARDIZATION_GUIDE.md)** - UI design system
- **[docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](./docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md)** - Performance optimizations (NEW)

## Build & Deploy

```bash
# Production build
npm run build  # Output: dist/

# Preview production build
npm run preview

# Type checking
npm run type-check
```

**Azure Static Web Apps deployment:** See [docs/DEPLOYMENT_AZURE.md](./docs/DEPLOYMENT_AZURE.md)

## Performance

**v2.9.1 Optimizations:**
- ✅ Supports 5,000+ nodes smoothly
- ✅ **100x faster** schema toggling (freezing → <5ms)
- ✅ Debounced filters (150ms) for large datasets
- ✅ Layout caching (95%+ hit rate)
- ✅ Smooth 60fps pan/zoom

See [PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](./docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md) for details.

---

**Last Updated:** 2025-11-04
