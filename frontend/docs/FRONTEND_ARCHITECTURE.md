# Data Lineage Visualizer - Frontend Architecture

**Version:** 1.0
**Last Updated:** 2025-10-26
**Framework:** React 19.2.0 + Vite 6.2.0

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Application Architecture](#application-architecture)
4. [Component Breakdown](#component-breakdown)
5. [Data Flow](#data-flow)
6. [State Management](#state-management)
7. [Core Features](#core-features)
8. [File Structure](#file-structure)
9. [Performance Considerations](#performance-considerations)
10. [Bundle Analysis](#bundle-analysis)

---

## Overview

The **Data Lineage Visualizer** is a client-side React application that provides interactive visualization of data dependencies in Azure Synapse data warehouses. It uses React Flow for graph rendering and Graphology for graph algorithms, allowing users to:

- Visualize data object dependencies (tables, views, stored procedures)
- Trace lineage paths upstream and downstream
- Filter by schema and data model type
- Search and focus on specific objects
- Export visualizations as SVG
- Import custom lineage data

**Deployment Type:** Static SPA (Single Page Application)
**Backend Requirements:** None (purely client-side)
**Data Source:** JSON files loaded at runtime

---

## Technology Stack

### Core Framework
| Package | Version | Purpose |
|---------|---------|---------|
| **React** | 19.2.0 | UI framework with modern concurrent features |
| **React DOM** | 19.2.0 | DOM rendering library |
| **Vite** | 6.2.0 | Build tool & dev server |
| **TypeScript** | 5.8.2 | Type safety and developer experience |

### Visualization Libraries
| Package | Version | Purpose |
|---------|---------|---------|
| **ReactFlow** | 11.11.4 | Interactive graph visualization with panning, zooming, and minimap |
| **Dagre** | 0.8.5 | Graph layout algorithm (hierarchical positioning) |
| **Graphology** | 0.25.4 | Graph data structure and algorithms |
| **Graphology-Traversal** | 0.3.1 | Graph traversal utilities (DFS, BFS) |

### Styling
| Technology | Source | Purpose |
|------------|--------|---------|
| **Tailwind CSS** | CDN (v3.x) | Utility-first CSS framework |
| **ReactFlow CSS** | CDN (v11.11.3) | Graph component styles |

### Build & Dev Tools
| Package | Version | Purpose |
|---------|---------|---------|
| **@vitejs/plugin-react** | 5.0.0 | React Fast Refresh & JSX transform |
| **@types/node** | 22.14.0 | Node.js type definitions |

---

## Application Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Toolbar    │  │   Legend    │  │  Trace Panel (RHS) │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   React Flow Canvas                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Custom Nodes (Tables/Views/SPs)                    │   │
│  │  Edges (Dependency Arrows)                          │   │
│  │  Controls (Zoom, Pan, Fit View)                     │   │
│  │  MiniMap                                             │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    State Management Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Data State  │  │  View State  │  │  Filter State   │  │
│  │  (allData)   │  │ (viewMode)   │  │  (schemas)      │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Business Logic Layer                    │
│  ┌───────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │  Graphology   │ │  Dagre       │ │  Trace Logic     │  │
│  │  (Graph Ops)  │ │  (Layout)    │ │  (BFS/DFS)       │  │
│  └───────────────┘ └──────────────┘ └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                       Data Layer                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  JSON Data (DataNode[])                              │  │
│  │  - Sample data (40 nodes, 10 schemas)                │  │
│  │  - Imported data (from frontend_lineage.json)        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

1. **Component Composition:** Small, focused components composed into complex UI
2. **Custom Hooks:** Business logic extracted into reusable hooks
3. **Controlled Components:** All state managed by React (no uncontrolled inputs)
4. **Memoization:** Heavy computations cached with `useMemo`
5. **Separation of Concerns:** UI, logic, and data clearly separated

---

## Component Breakdown

### Main Application Components

#### 1. **App.tsx** (Main Container)
**Responsibility:** Root application wrapper

```typescript
export default function App() {
  return (
    <ReactFlowProvider>
      <DataLineageVisualizer />
    </ReactFlowProvider>
  );
}
```

**Key Features:**
- Wraps app in `ReactFlowProvider` for React Flow context
- Delegates all logic to `DataLineageVisualizer`

#### 2. **DataLineageVisualizer** (Core Component)
**Responsibility:** Main application orchestrator

**State:**
- `allData`: Complete dataset (DataNode[])
- `nodes/edges`: React Flow graph elements
- `viewMode`: 'detail' | 'schema'
- `layout`: 'LR' (horizontal) | 'TB' (vertical)
- `focusedNodeId`: Currently selected node

**Custom Hooks:**
- `useNotifications()`: Toast notification system
- `useGraphology()`: Graph data structure & schema colors
- `useInteractiveTrace()`: Upstream/downstream tracing
- `useDataFiltering()`: Schema/type filtering logic

**Event Handlers:**
- `handleNodeClick()`: Focus node & highlight neighbors
- `handleDataImport()`: Load new JSON data
- `handleExportSVG()`: Generate SVG export
- `executeSearch()`: Find and focus specific nodes

### UI Components

#### 3. **Toolbar.tsx**
**Location:** Top of screen
**Functionality:**
- View mode toggle (Detail ↔ Schema)
- Search bar with autocomplete
- Schema filter dropdown (multi-select)
- Data model type filter dropdown
- Layout toggle (Horizontal ↔ Vertical)
- "Hide Unrelated" checkbox
- Action buttons: Trace, Export SVG, Import Data, Info

#### 4. **CustomNode.tsx**
**Responsibility:** Renders individual graph nodes

**Visual Styles:**
- **Tables:** Rounded pill shape (`rounded-full`)
- **Views:** Rounded rectangle (`rounded-md`)
- **Stored Procedures:** Dashed border (`border-dashed`)

**States:**
- `isHighlighted`: Blue border + ring effect
- `isDimmed`: Reduced opacity (20%)
- Background color: Schema-based color with 30% opacity

#### 5. **Legend.tsx**
**Location:** Bottom-left overlay (collapsible)
**Content:**
- Schema color mapping
- Node shape legend (Table/View/SP)
- Collapsible panel

#### 6. **InteractiveTracePanel.tsx**
**Location:** Right-side slide-in panel
**Functionality:**
1. **Start Node Selection:** Autocomplete search
2. **Trace Levels:** Upstream/downstream depth (0-99 or "All")
3. **Schema Inclusion:** Multi-select checkboxes
4. **Exclusion Patterns:** Wildcard filters (e.g., `_TEMP_*`, `STG_*`)

**Output:** Filtered graph showing only traced paths

#### 7. **ImportDataModal.tsx**
**Functionality:**
- JSON editor with syntax highlighting
- File upload (.json)
- Load sample data button
- Data contract definition viewer
- Validation with auto-fix (bidirectional edges)

**Validation:**
- Required fields: `id`, `name`, `schema`, `object_type`, `inputs`, `outputs`
- Valid object_type: "Table", "View", "Stored Procedure"
- Auto-fix: Ensures bidirectional inputs/outputs consistency

#### 8. **InfoModal.tsx**
**Content:**
- Application instructions
- Feature descriptions
- Keyboard shortcuts (if any)

#### 9. **NotificationSystem.tsx**
**Components:**
- `NotificationContainer`: Toast notifications (top-center)
- `NotificationHistory`: Dropdown history viewer

**Types:**
- `info`: Blue background
- `error`: Red background

### Custom Hooks

#### useGraphology.ts
**Purpose:** Build and maintain graph data structure

**Outputs:**
- `lineageGraph`: Graphology directed graph
- `schemas`: Unique schema list (sorted)
- `schemaColorMap`: Schema → color mapping
- `dataModelTypes`: Unique data model types

**Algorithm:**
```
1. Create directed graph from allData
2. Add all nodes with attributes
3. Add edges from inputs/outputs arrays
4. Extract unique schemas & assign colors
5. Extract unique data model types
```

#### useInteractiveTrace.ts
**Purpose:** Perform lineage tracing

**Algorithm (BFS):**
```
1. Start from selected node
2. Traverse upstream (forEachInNeighbor) N levels
3. Traverse downstream (forEachOutNeighbor) N levels
4. Filter by included schemas
5. Stop at exclusion pattern matches
6. Return Set<string> of visible node IDs
```

#### useDataFiltering.ts
**Purpose:** Apply filters to visible nodes

**Filter Logic:**
1. **Trace Mode:** Show only traced nodes
2. **Focus Mode:** Show only highlighted + neighbors
3. **Schema Filter:** Show selected schemas
4. **Type Filter:** Show selected data model types
5. **Hide Unrelated:** Remove isolated nodes (no visible edges)

#### useNotifications.ts
**Purpose:** Manage toast notifications

**Features:**
- Auto-dismiss after 5 seconds
- Manual dismiss
- History tracking
- Notification ID generation

### Utilities

#### utils/layout.ts
**`getDagreLayoutedElements()`**

**Purpose:** Position nodes using Dagre hierarchical layout

**Process:**
```
1. Convert DataNode[] to ReactFlow nodes/edges
2. Create Dagre graph with rankdir (LR or TB)
3. Set node dimensions (192×48 for detail, 200×80 for schema)
4. Calculate positions
5. Assign source/target handle positions
6. Return positioned nodes & edges
```

**Schema View Special Logic:**
- Aggregate edges by schema pair
- Label edges with dependency count

#### utils/data.ts
**`generateSampleData()`**

**Output:** 40 sample nodes with random:
- Schemas (10 schemas)
- Object types (Table/View/Stored Procedure)
- Data model types (Dimension/Fact/Lookup/Other)
- Lineage connections (1.5× nodes = 60 edges)

---

## Data Flow

### Data Loading Flow

```
┌──────────────────────┐
│  Application Start   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│  generateSampleData()        │  ← Default sample data (40 nodes)
│  or Load frontend_lineage.json │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  setAllData(DataNode[])      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  useGraphology(allData)      │  ← Build graph + extract schemas
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  useDataFiltering(...)       │  ← Apply filters
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  getDagreLayoutedElements()  │  ← Position nodes
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  React Flow Render           │  ← Display graph
└──────────────────────────────┘
```

### Interactive Trace Flow

```
User clicks "Start Trace"
  ↓
InteractiveTracePanel opens
  ↓
User selects start node, levels, schemas, exclusions
  ↓
Click "Apply Trace"
  ↓
performInteractiveTrace(config)
  ↓
BFS traversal upstream & downstream
  ↓
Filter by schemas & exclusion patterns
  ↓
Return Set<visibleNodeIds>
  ↓
useDataFiltering filters allData to traced nodes
  ↓
Graph re-renders with traced subgraph
```

### Search Flow

```
User types in search box
  ↓
Auto-complete shows matching nodes (max 5)
  ↓
User presses Enter or clicks suggestion
  ↓
executeSearch(query)
  ↓
Find node in allData by name
  ↓
Check if node is visible in current React Flow nodes
  ↓
If found: setCenter() to node position + highlight
  ↓
If not found: Show error notification
```

---

## State Management

### State Hierarchy

**Global State (DataLineageVisualizer):**
```typescript
allData: DataNode[]                    // Complete dataset
sampleData: DataNode[]                  // Default sample (immutable)
nodes: ReactFlowNode[]                  // Positioned graph nodes
edges: Edge[]                           // Graph edges
viewMode: 'detail' | 'schema'
layout: 'LR' | 'TB'
focusedNodeId: string | null
```

**Derived State (via useMemo):**
```typescript
lineageGraph: Graph                     // Graphology graph
schemas: string[]                       // Unique schemas
schemaColorMap: Map<string, string>     // Schema colors
finalVisibleData: DataNode[]            // Filtered data
layoutedElements: { nodes, edges }      // Positioned elements
```

**Filter State (useDataFiltering):**
```typescript
selectedSchemas: Set<string>
selectedTypes: Set<string>
searchTerm: string
hideUnrelated: boolean
highlightedNodes: Set<string>
```

**Trace State (useInteractiveTrace):**
```typescript
isTraceModeActive: boolean
traceConfig: TraceConfig | null {
  startNodeId: string
  upstreamLevels: number
  downstreamLevels: number
  includedSchemas: Set<string>
  exclusionPatterns: string[]
}
```

### State Updates Trigger Chain

```
allData changes
  ↓
useGraphology recalculates graph
  ↓
useDataFiltering recalculates finalVisibleData
  ↓
useMemo recalculates layoutedElements
  ↓
useEffect updates React Flow nodes/edges
  ↓
React Flow re-renders
```

---

## Core Features

### 1. Detail View
- Shows individual nodes (tables, views, stored procedures)
- Edges represent dependencies
- Color-coded by schema
- Shape-coded by object type

### 2. Schema View
- Aggregates nodes by schema
- Edges show inter-schema dependency count
- Larger nodes (200×80 vs 192×48)

### 3. Interactive Tracing
- **Upstream:** Show all parent dependencies (N levels)
- **Downstream:** Show all child dependencies (N levels)
- **Schema Filtering:** Include only specific schemas in trace
- **Exclusion Patterns:** Skip temporary/staging tables (wildcards)

### 4. Filtering
- **Schema Filter:** Multi-select schemas
- **Type Filter:** Multi-select data model types (Dim/Fact/Lookup)
- **Search:** Find node by name with autocomplete
- **Hide Unrelated:** Show only nodes with visible connections

### 5. Node Interaction
- **Click:** Highlight node + immediate neighbors (1 level)
- **Double-click (same node):** Clear highlight
- **Hover:** Show tooltip with full metadata

### 6. Export
- **SVG Export:** Generate static SVG with current layout
- Preserves colors, shapes, edges
- Optimized for print/documentation

### 7. Data Import
- **JSON Upload:** Load custom lineage data
- **JSON Editor:** Edit data directly in browser
- **Validation:** Ensures data contract compliance
- **Auto-fix:** Corrects bidirectional edge inconsistencies

---

## File Structure

```
frontend/
├── App.tsx                       # Main app component
├── index.tsx                     # React entry point
├── index.html                    # HTML template
├── types.ts                      # TypeScript type definitions
├── constants.ts                  # App constants (colors, shapes)
│
├── components/
│   ├── CustomNode.tsx            # Graph node component
│   ├── Toolbar.tsx               # Top toolbar
│   ├── Legend.tsx                # Schema legend (bottom-left)
│   ├── InteractiveTracePanel.tsx # Right-side trace panel
│   ├── ImportDataModal.tsx       # Data import modal
│   ├── InfoModal.tsx             # Help modal
│   └── NotificationSystem.tsx    # Toast notifications
│
├── hooks/
│   ├── useGraphology.ts          # Graph construction
│   ├── useInteractiveTrace.ts    # Lineage tracing
│   ├── useDataFiltering.ts       # Filter logic
│   └── useNotifications.ts       # Notification management
│
├── utils/
│   ├── layout.ts                 # Dagre layout logic
│   └── data.ts                   # Sample data generator
│
├── package.json                  # Dependencies & scripts
├── vite.config.ts                # Vite configuration
├── tsconfig.json                 # TypeScript configuration
├── .env.local                    # Environment variables (GEMINI_API_KEY)
├── .gitignore                    # Git ignore rules
├── README.md                     # Original AI Studio README
└── metadata.json                 # App metadata
```

---

## Performance Considerations

### Optimization Strategies

1. **Memoization:**
   - `layoutedElements` (Dagre layout) - Only recalculates on data/filter changes
   - `finalVisibleData` - Only recalculates on filter changes
   - `lineageGraph` - Only rebuilds on `allData` changes

2. **React.memo():**
   - `CustomNode` component memoized to prevent unnecessary re-renders
   - Only re-renders when node data/highlight state changes

3. **Debouncing:**
   - Window resize events debounced (150ms)
   - Autocomplete suggestions throttled by React state updates

4. **Lazy Calculations:**
   - Graph layout only calculated for visible nodes
   - Autocomplete limited to 5 suggestions

5. **Event Delegation:**
   - React Flow handles canvas clicks efficiently
   - No individual click handlers on nodes

### Performance Metrics (Estimated)

| Dataset Size | Nodes | Edges | Layout Time | Render Time |
|--------------|-------|-------|-------------|-------------|
| Small        | 40    | 60    | <50ms       | <100ms      |
| Medium       | 200   | 400   | <200ms      | <300ms      |
| Large        | 1000  | 2000  | <500ms      | <800ms      |

**Note:** Actual performance depends on browser and hardware

---

## Bundle Analysis

### Production Build Output (Estimated)

```
dist/
├── index.html                    # ~2 KB
├── assets/
│   ├── index-[hash].js           # ~450 KB (minified, gzipped)
│   └── index-[hash].css          # ~5 KB (Tailwind purged)
└── ... (other assets)

Total Bundle Size: ~500 KB - 1.5 MB (uncompressed)
Gzipped Size: ~150 KB - 300 KB
```

### Dependency Breakdown

| Package | Approx Size | Purpose |
|---------|-------------|---------|
| React + React DOM | ~140 KB | Core framework |
| ReactFlow | ~200 KB | Graph visualization |
| Graphology | ~50 KB | Graph algorithms |
| Dagre | ~40 KB | Layout engine |
| Other (TypeScript runtime, etc.) | ~20 KB | Utilities |

**Note:** Tailwind CSS is loaded via CDN, not bundled

---

## Data Contract

### DataNode Type Definition

```typescript
export type DataNode = {
  id: string;                          // Unique identifier (e.g., "node_0")
  name: string;                        // Display name (e.g., "DimCustomers")
  schema: string;                      // Database schema (e.g., "CONSUMPTION_FINANCE")
  object_type: 'Table' | 'View' | 'Stored Procedure';
  description?: string;                 // Optional description
  data_model_type?: 'Dimension' | 'Fact' | 'Lookup' | 'Other';
  inputs: string[];                     // Array of input node IDs
  outputs: string[];                    // Array of output node IDs
};
```

### Sample JSON Structure

```json
[
  {
    "id": "node_0",
    "name": "DimCustomers",
    "schema": "SALES",
    "object_type": "Table",
    "description": "Customer dimension table",
    "data_model_type": "Dimension",
    "inputs": ["node_5"],
    "outputs": ["node_1", "node_3"]
  }
]
```

---

## Browser Compatibility

**Tested & Supported:**
- Chrome 120+ ✅
- Edge 120+ ✅
- Firefox 120+ ✅
- Safari 17+ ✅

**Required Browser Features:**
- ES2022 support
- CSS Grid & Flexbox
- Fetch API
- LocalStorage (for future enhancements)

---

## Future Enhancements (Roadmap)

1. **Performance:**
   - Virtualization for 10K+ node graphs
   - Web Workers for layout calculation
   - Progressive loading

2. **Features:**
   - Column-level lineage
   - Lineage change history (diff viewer)
   - Saved trace configurations
   - Export to PNG/PDF
   - Zoom-to-selection

3. **Data Integration:**
   - Real-time backend API integration
   - Refresh lineage without page reload
   - Confidence score visualization

4. **UX Improvements:**
   - Dark mode
   - Keyboard shortcuts
   - Undo/redo for filters
   - Multi-node selection

---

## Troubleshooting

### Common Issues

**1. Graph not rendering:**
- Check browser console for errors
- Ensure `allData` is valid JSON array
- Verify React Flow CSS is loaded

**2. Layout looks broken:**
- Check Dagre is imported correctly
- Verify node dimensions are set
- Try changing layout direction (LR ↔ TB)

**3. Search not working:**
- Ensure node names match exactly (case-insensitive)
- Check if node is filtered out by schema/type filters
- Verify node exists in `allData`

**4. Import fails:**
- Validate JSON syntax (use JSONLint)
- Check required fields are present
- Review validation error messages

---

## Credits & License

**Developed for:** Azure Synapse Data Warehouse Lineage Visualization
**Framework:** React + Vite
**Graph Library:** ReactFlow (MIT License)
**Layout Engine:** Dagre (MIT License)

**Original Template:** Google AI Studio (React Flow Data Lineage template)
**Customizations:** Vibecoding team (2024-2025)

---

**End of Documentation**
