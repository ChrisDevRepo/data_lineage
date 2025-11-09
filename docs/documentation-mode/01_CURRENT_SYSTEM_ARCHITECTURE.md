# CURRENT SYSTEM ARCHITECTURE
**Purpose:** Explain existing app architecture for Documentation Mode implementation
**Audience:** New developers, AI agents implementing the feature

---

## EXISTING APPLICATION OVERVIEW

### What is the Data Lineage Visualizer?

**Purpose:** Visualize SQL Server database object dependencies (tables, views, stored procedures)

**Data Source:** DuckDB database containing:
- 5,000-10,000 database objects from SQL Server
- Lineage relationships (which objects depend on which)
- Metadata (schemas, object types, SQL definitions)

**Core Functionality:**
1. User uploads SQL definitions (ZIP file of .sql files)
2. Backend parses SQL → extracts lineage → stores in DuckDB
3. Frontend queries API → displays interactive graph
4. User explores: search, filter, trace dependencies

---

## CURRENT TECH STACK

### Frontend
- **Framework:** React 19.2.0
- **Language:** TypeScript 5.8.2
- **Graph Library:** React Flow 11.11.4
- **Layout:** Dagre (automatic positioning)
- **Build:** Vite 6.2.0
- **State:** React hooks (no Redux/Zustand)

### Backend
- **Framework:** FastAPI (Python)
- **Database:** DuckDB (embedded)
- **Parser:** v4.2.0 (95.5% accuracy)
- **Models:** Pydantic

---

## EXISTING FILE STRUCTURE

```
frontend/
├── components/
│   ├── CustomNode.tsx          # Database node rendering
│   ├── Toolbar.tsx             # Search, filters, actions
│   ├── Legend.tsx              # Schema color legend
│   ├── NodeContextMenu.tsx     # Right-click menu
│   ├── SqlViewer.tsx           # Show SQL definitions
│   ├── DetailSearchModal.tsx   # Search modal
│   ├── ImportDataModal.tsx     # Upload ZIP files
│   └── ui/                     # Button, Input, etc.
│
├── hooks/
│   ├── useGraphology.ts        # Graph data management
│   ├── useNotifications.ts     # Toast notifications
│   ├── useInteractiveTrace.ts  # Dependency tracing
│   └── useDataFiltering.ts     # Filter logic
│
├── utils/
│   ├── layout.ts               # Dagre layout algorithm
│   ├── data.ts                 # Data transformations
│   └── logger.ts               # Performance logging
│
├── App.tsx                     # Main app component
├── design-tokens.ts            # Color palette, spacing, etc.
├── constants.ts                # App constants
└── types.ts                    # TypeScript types

api/
├── main.py                     # FastAPI endpoints
├── models.py                   # Pydantic models
└── background_tasks.py         # Upload processing
```

---

## CURRENT DATA FLOW

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER UPLOADS SQL FILES                                   │
│    POST /api/upload → ZIP file with .sql files              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. BACKEND PROCESSES                                         │
│    - Extract SQL files from ZIP                             │
│    - Parse SQL (extract tables, columns, dependencies)      │
│    - Calculate lineage (which objects depend on which)      │
│    - Store in DuckDB                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. FRONTEND LOADS DATA                                       │
│    GET /api/latest-data → Returns JSON array of nodes       │
│    - Each node: {id, name, schema, object_type, inputs[]}   │
│    - Frontend transforms to React Flow format               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. LAYOUT & RENDERING                                        │
│    - Dagre algorithm positions nodes automatically          │
│    - React Flow renders interactive graph                   │
│    - User can pan, zoom, search, filter                     │
└─────────────────────────────────────────────────────────────┘
```

---

## EXISTING STATE MANAGEMENT (App.tsx)

```typescript
// Data from API (5,000-10,000 nodes)
const [allData, setAllData] = useState<DataNode[]>([]);

// React Flow state
const [nodes, setNodes, onNodesChange] = useNodesState([]);
const [edges, setEdges, onEdgesChange] = useEdgesState([]);

// Filters
const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());
const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
const [excludeTerms, setExcludeTerms] = useState<string[]>([]);

// Search/Focus
const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
const [searchTerm, setSearchTerm] = useState('');

// Trace mode (dependency exploration)
const [isTraceModeActive, setIsTraceModeActive] = useState(false);
const [traceConfig, setTraceConfig] = useState({ /* ... */ });

// Layout
const [layout, setLayout] = useState<'LR' | 'TB'>('LR'); // Left-Right or Top-Bottom

// Computed data (from hooks)
const { lineageGraph, schemas, schemaColorMap } = useGraphology(allData);
```

---

## EXISTING REACT FLOW SETUP

```typescript
<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  nodeTypes={nodeTypes}              // CustomNode only (currently)
  fitView
  minZoom={0.1}
  maxZoom={2}
  nodesDraggable={false}             // Currently readonly
  nodesConnectable={false}           // No manual edge creation
  elementsSelectable={true}          // Can select for context menu
>
  <Background />
  <Controls />
</ReactFlow>
```

---

## EXISTING COMPONENTS

### CustomNode.tsx
Renders database objects (tables, views, stored procedures)

**Props:**
```typescript
interface CustomNodeData {
  label: string;           // e.g., "dbo.customers"
  name: string;
  schema: string;
  object_type: string;     // TABLE, VIEW, STORED_PROCEDURE
  confidence: number;      // 0, 75, 85, 100
  inputs: string[];        // Dependencies
  outputs: string[];       // Dependents
}
```

**Styling:**
- Border color: Schema color (from design-tokens.ts)
- Background: White
- Size: 192px × 48px (fixed)
- Shows confidence badge (colored circle)

---

### Toolbar.tsx
Main toolbar with:
- Search input (with autocomplete)
- Exclude filter
- Schema filter (multi-select dropdown)
- Type filter (Table, View, SP)
- Layout toggle (LR/TB)
- Export SVG button
- Import button
- Help button

---

### NodeContextMenu.tsx
Right-click menu on nodes:
- "Start Tracing from [node]"
- "Show SQL Definition"
- "Fit View"

---

## EXISTING SVG EXPORT

**Location:** `App.tsx` line 737

**Function:** `handleExportSVG()`

**What it does:**
- Captures all visible nodes/edges
- Generates SVG markup manually
- Includes legend
- Downloads as .svg file

**Note:** PNG export does NOT exist (need to add for Documentation Mode)

---

## EXISTING COLOR SYSTEM (design-tokens.ts)

### Schema Colors (30 unique colors)
Used for node borders based on schema:
```typescript
tokens.colors.schema.colors = [
  '#4E79A7',  // Blue
  '#F28E2B',  // Orange
  '#E15759',  // Red
  '#76B7B2',  // Teal
  // ... 26 more colors
];
```

**Usage:**
```typescript
const schemaIndex = schemas.indexOf(node.schema);
const color = tokens.colors.schema.colors[schemaIndex % 30];
```

### Semantic Colors
- Primary: Blue (#3b82f6)
- Success: Green (#22c55e)
- Warning: Amber (#facc15)
- Error: Red (#ef4444)

---

## EXISTING NOTIFICATION SYSTEM

**Hook:** `useNotifications()`

**Functions:**
```typescript
addNotification(message: string, type: 'info' | 'success' | 'error' | 'warning');
```

**Display:** Toast notifications (top-right, auto-dismiss 3s)

---

## WHAT DOCUMENTATION MODE NEEDS

### 1. Separate State
Documentation Mode needs its own state (does NOT modify main app state)

```typescript
// Add to App.tsx
const [isDocMode, setIsDocMode] = useState(false);
const [docNodes, setDocNodes] = useState<Node[]>([]);
const [docEdges, setDocEdges] = useState<Edge[]>([]);
```

### 2. Conditional Rendering
```typescript
{isDocMode ? (
  <DocumentationCanvas nodes={docNodes} edges={docEdges} />
) : (
  <MainAppCanvas nodes={nodes} edges={edges} />
)}
```

### 3. New Node Types
Register annotation node types:
```typescript
const nodeTypes = {
  custom: CustomNode,           // Existing
  textbox: TextBox,             // NEW
  rectangle: RectangleShape,    // NEW
};
```

### 4. Enable Dragging (Doc Mode Only)
```typescript
<ReactFlow
  nodesDraggable={isDocMode}    // Enable in doc mode
  nodesConnectable={false}      // Still no manual connections
/>
```

---

## INTEGRATION POINTS

### Entry to Documentation Mode
**Location:** Toolbar.tsx

**Add button:**
```typescript
<Button onClick={() => setIsDocMode(true)}>
  Create Documentation View
</Button>
```

### Exit from Documentation Mode
**Location:** DocumentationModeToolbar.tsx (new component)

**Add button:**
```typescript
<Button onClick={() => setIsDocMode(false)}>
  Exit Documentation Mode
</Button>
```

---

## KEY CONSTRAINTS

### 1. No Backend Changes
Documentation Mode is frontend-only:
- No new API endpoints
- No database schema changes
- Uses existing data from `GET /api/latest-data`

### 2. Browser Support
- **Windows only:** Chrome, Edge
- **No Safari/mobile:** Out of scope

### 3. Performance
- Max 100 nodes in Documentation Mode (enforced by UI)
- LocalStorage limit: 5MB (for autosave)

---

## EXISTING LIBRARIES AVAILABLE

Already in package.json (can use immediately):
- `react-flow` 11.11.4 → NodeResizer, NodeToolbar, useUndoRedo
- `dagre` 0.8.5 → Layout algorithm (not needed in doc mode)
- `graphology` 0.25.4 → Graph utilities
- `@monaco-editor/react` 4.7.0 → SQL viewer

**Need to add:**
- `zod` → JSON validation for import
- (Optional) `html-to-image` → PNG export if SVG insufficient

---

## QUESTIONS A NEW DEVELOPER MIGHT ASK

### Q: Where does the data come from?
**A:** `GET /api/latest-data` returns array of nodes with lineage metadata

### Q: How are nodes positioned?
**A:** Main app uses Dagre algorithm (`utils/layout.ts`). Documentation Mode uses manual positioning.

### Q: How are colors assigned?
**A:** Schema colors from `design-tokens.ts`, assigned based on schema index

### Q: Can I modify existing components?
**A:** Yes, but keep main app behavior unchanged. Use conditional logic for doc mode features.

### Q: Do I need to modify the backend?
**A:** No. Documentation Mode is frontend-only. Use existing API.

### Q: How do I test with real data?
**A:** Import a ZIP file via the Import button, or use the sample data (generates on first load if API unavailable)

---

**This document should answer all "current system" questions. If you have more questions, the documentation is still incomplete.**
