# Data Lineage Visualizer - Frontend

**Interactive React application for visualizing Azure Synapse data lineage**

[![React](https://img.shields.io/badge/React-19.2.0-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.2.0-purple.svg)](https://vitejs.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.2-blue.svg)](https://www.typescriptlang.org/)

---

## 🚀 Current Status

**Version:** 2.9.0 (UI Simplification & Detail Search Enhancements)
**v3.0 Status:** Core features complete - Docker containerization pending

### ✨ Latest Updates (v2.9.0 - 2025-10-31)

**UI Simplification:**
- 🗑️ **Removed Schema View** - Focused exclusively on Detail View for better UX
  - Removed "Detail View / Schema View" toggle button
  - Dagre layout now optimized only for object-level visualization
  - Cleaner, simpler interface

**Detail Search Enhancements:**
- 📏 **Resizable Panels** - Drag divider to adjust search results vs DDL viewer height
- 🔍 **Filter Dropdowns** - Added schema and object type filters next to search box
- ❓ **Search Syntax Help** - Help button showing DuckDB FTS advanced operators

### ✨ Previous Updates (v2.8.0 - 2025-10-29)

**New Features:**
- 🎯 **Path-Based Tracing Mode** - Find all direct lineage paths between two nodes
  - Added "Path Between Nodes" option in Interactive Trace panel
  - Two modes: "By Levels" (default) or "Path Between Nodes"
  - Define start AND end nodes, see all intermediate steps
  - Bidirectional search: downstream (start→end) and upstream (end→start)
  - Direct paths only - no zigzag routes, follows data flow direction
  - Use cases: "How does Table A flow to Table B?", "Show me the path between these SPs"
- ✨ **SQL Viewer Dimming Persistence** - Node dimming effect now persists when SQL viewer is open
  - Previously: Dimming disabled when SQL viewer opened
  - Now: Consistent visual focus whether viewer is open or closed
  - Distant nodes (>1 level away) stay blurred, adjacent nodes stay visible

### ✨ Previous Updates (v2.7.0 - 2025-10-28)

**Major Upgrade:**
- 🚀 **Monaco Editor Integration** - Replaced Prism.js with VS Code's Monaco Editor
  - Professional SQL code viewing experience
  - Built-in search dialog with next/previous navigation
  - Match counter ("3 of 15 results")
  - Overview ruler with yellow markers on scrollbar (Notepad++ style)
  - Keyboard shortcuts: `Ctrl+F` to search, `F3` next, `Shift+F3` previous
  - Optimized for large SQL files (10K+ lines) with virtual scrolling
  - Case sensitive, whole word, and regex search support
  - No auto-search lag (triggers on Enter/button, not every keystroke)


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
| **Code Editor** | Monaco Editor | 4.7.0 | SQL viewer (VS Code engine) |

**New in v3.0:**
- **Monaco Editor** - Professional SQL syntax highlighting and search (✅ **IMPLEMENTED v2.7**)
- **FastAPI Client** - HTTP polling for backend jobs

---

## 📖 Additional Documentation

- **[CHANGELOG.md](./CHANGELOG.md)** - Detailed feature changes and version history
