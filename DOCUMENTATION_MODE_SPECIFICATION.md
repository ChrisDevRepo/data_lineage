# DOCUMENTATION MODE - COMPLETE SPECIFICATION
**Version:** 1.0 FINAL
**Date:** 2025-11-09
**Status:** ✅ Ready for Implementation
**Purpose:** Enable users to create PowerPoint-quality presentation slides from lineage data

---

## 📚 HOW TO USE THIS DOCUMENTATION

**THIS IS THE MAIN SPECIFICATION** - Start here to understand the feature.

**Supporting Documents** (in `docs/documentation-mode/`):
1. **`01_CURRENT_SYSTEM_ARCHITECTURE.md`**
   - Explains existing app architecture
   - Required reading before implementation
   - Answers: "What does the current system look like?"

2. **`02_IMPLEMENTATION_CHECKLIST.md`**
   - Day-by-day implementation guide (15 days)
   - Step-by-step tasks with code examples
   - Testing checkboxes for each phase

**For New AI Agents / Developers:**
1. Read THIS document first (understand the "what" and "why")
2. Read `01_CURRENT_SYSTEM_ARCHITECTURE.md` (understand the existing system)
3. Use `02_IMPLEMENTATION_CHECKLIST.md` as your guide (build it step-by-step)

**Questions This Documentation Answers:**
- ✅ What is Documentation Mode? (see [Feature Overview](#feature-overview))
- ✅ Why is it needed? (see [Executive Summary](#executive-summary))
- ✅ What features does it have? (see [Complete Feature List](#complete-feature-list))
- ✅ How does it integrate with the existing app? (see `01_CURRENT_SYSTEM_ARCHITECTURE.md`)
- ✅ How do I build it? (see `02_IMPLEMENTATION_CHECKLIST.md`)
- ✅ What technology does it use? (see [Technical Architecture](#technical-architecture))

---

## 📖 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Feature Overview](#feature-overview)
3. [User Journey](#user-journey)
4. [Complete Feature List](#complete-feature-list)
5. [Technical Architecture](#technical-architecture)
6. [Component Specifications](#component-specifications)
7. [Implementation Phases](#implementation-phases)
8. [Definition of Done](#definition-of-done)
9. [Success Metrics](#success-metrics)

---

## EXECUTIVE SUMMARY

### Vision
**Documentation Mode transforms the Data Lineage Visualizer from an exploration tool into a presentation creation tool.** Users can select relevant nodes from their 5,000-10,000 node lineage graph, arrange them into clear narratives, add explanatory annotations, and export publication-ready diagrams for PowerPoint presentations and documentation.

### Key Metaphor
**"Like PowerPoint's chart editor for data lineage"** - A separate canvas where users craft presentation-quality diagrams from complex technical data.

### Core Value Proposition
- **From Exploration to Explanation:** Main app explores complexity; Documentation Mode creates clarity
- **Presentation-Ready Output:** Export PNG/SVG images suitable for executive presentations
- **Storytelling with Data:** Add context (labels, notes, groupings) that makes technical lineage understandable

---

## FEATURE OVERVIEW

### What is Documentation Mode?

Documentation Mode is a **separate canvas** (distinct from the main app) where users:
1. Select up to 100 relevant nodes from their lineage graph
2. Arrange nodes for clarity (drag & drop custom positioning)
3. Add explanatory elements (sticky notes, text boxes, arrows, grouping boxes)
4. Label relationships (edge labels explaining data flows)
5. Export as high-quality images (PNG/SVG for presentations)

### Why a Separate Canvas?

**Main App (Current):**
- Purpose: Explore full lineage (5,000-10,000 nodes)
- Layout: Automatic (Dagre algorithm)
- Interaction: Read-only exploration
- Output: Interactive web view

**Documentation Mode (New):**
- Purpose: Create presentation diagrams (max 100 nodes)
- Layout: Manual (user-controlled positioning)
- Interaction: Full editing capabilities
- Output: Static images (PNG/SVG)

**Key Distinction:** Main app = exploration tool. Documentation Mode = presentation creation tool.

---

## USER JOURNEY

### Typical Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Explore in Main App                                 │
│ - User navigates 5,000+ node lineage graph                  │
│ - Applies filters (schema=dbo, type=table)                  │
│ - Result: 200 nodes visible                                 │
│ - User identifies interesting data pipeline                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Create Documentation View                           │
│ - Clicks "Create Documentation View" button                 │
│ - System asks: "How many nodes to start with?"              │
│   • User chooses: ~50 nodes (typical)                       │
│ - Opens separate canvas with 50 filtered nodes              │
│ - Edges auto-populated between nodes                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Refine Node Selection                               │
│ - Remove unnecessary nodes (down to 30 core nodes)          │
│ - Add related nodes from Node Explorer (back to 50)         │
│   • Drag from sidebar to canvas                             │
│   • Edges auto-connect to existing nodes                    │
│ - Remove unwanted edges (delete not needed connections)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Arrange for Clarity                                 │
│ - Drag nodes to optimal positions                           │
│ - Group related objects visually                            │
│ - Create clear flow (left-to-right or top-to-bottom)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Add Context & Annotations                           │
│ - Label edges: "Daily ETL", "Validation Step"               │
│ - Add sticky notes: "Data quality issues occur here"        │
│ - Add text boxes: "Customer Master Data"                    │
│ - Add grouping boxes: "Bronze Layer", "Gold Layer"          │
│ - Add arrows: Point from note to specific node              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Save Work                                            │
│ - Save Layout (JSON file)                                   │
│   • For resuming work later                                 │
│   • For version control (commit to Git)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Export for Presentation                             │
│ - Export PNG → Insert into PowerPoint                       │
│ - Export SVG → Insert into documentation                    │
│ - Result: Professional diagram for stakeholders             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Exit Documentation Mode                             │
│ - Click "Exit Documentation Mode"                           │
│ - Returns to Main App (unchanged)                           │
│ - To resume: Load saved JSON layout                         │
└─────────────────────────────────────────────────────────────┘
```

---

## COMPLETE FEATURE LIST

### Phase 1: Core Infrastructure (MVP)

#### 1.1 Mode Toggle
**Feature:** Switch between Main App and Documentation Mode
- **Entry:** "Create Documentation View" button in toolbar
- **Exit:** "Exit Documentation Mode" button
- **Behavior:** Separate canvas (no back/forth switching)
- **State:** Main app state unchanged while in Documentation Mode

#### 1.2 Initial Node Selection
**Feature:** Start with relevant nodes from Main App
- **Source:** Current filtered view in Main App
- **User Input:** Prompt asks "How many nodes?" (no fixed default)
- **Limit:** Max 100 nodes
- **Edges:** Auto-populated based on selected nodes

#### 1.3 Node Explorer Sidebar
**Feature:** Browse and add nodes from DuckDB
- **Data Source:** All database nodes (5,000-10,000)
- **UI:** Left sidebar panel
- **Features:**
  - Search/filter by name, schema, type
  - Grouped by type (Tables, Views, Stored Procedures)
  - Collapsible sections
- **Interaction:** Drag node from sidebar to canvas
- **Limit Enforcement:** Warning at 90 nodes, hard block at 100

#### 1.4 Node Management
**Feature:** Add, remove, arrange database nodes
- **Add:** Drag from Node Explorer
- **Remove:** Delete key or context menu
- **Behavior:** Remove from canvas (can re-add from Explorer)
- **Edges:** Auto-connect to existing nodes when added
- **Drag:** Free positioning on canvas
- **Colors:** Schema colors (from design tokens)

#### 1.5 Edge Management
**Feature:** Manage connection lines between nodes
- **Auto-Population:** Edges appear when both nodes present
- **Delete:** User can remove edges (if not relevant for diagram)
- **Add:** Cannot manually create edges (use database relationships only)
- **Restore:** Re-add node to restore edges

---

### Phase 2: Annotations & Enrichment

#### 2.1 Text Boxes / Sticky Notes
**Feature:** Add freeform text anywhere on canvas
- **Purpose:** Add explanatory notes ("This is where transformation happens")
- **Creation:** Button "Add Text" or keyboard shortcut T
- **Editing:** Double-click to edit, click outside to save
- **Resizing:** Drag corner handles (NodeResizer component)
- **Styling:**
  - Background colors: Yellow, Blue, White (presets)
  - Font size: Small (12px), Medium (14px), Large (16px)
- **Actions:** Duplicate, Delete (via NodeToolbar)

#### 2.2 Grouping Boxes (Rectangles)
**Feature:** Visual grouping of related nodes
- **Purpose:** Show layers ("Bronze Layer", "Silver Layer")
- **Creation:** Button "Add Rectangle" or keyboard shortcut R
- **Resizing:** Drag corner handles (NodeResizer component)
- **Styling:**
  - Custom color picker (any color)
  - Opacity slider (30%-100%)
  - Dashed border
- **Z-Index:** Renders behind nodes (background element)
- **Actions:** Delete (via NodeToolbar)

#### 2.3 Edge Labels ✅ NEW
**Feature:** Add text labels to connection lines
- **Purpose:** Explain relationships ("Daily sync", "Validation step")
- **Creation:** Double-click edge to add label
- **Editing:** Click label to edit, click outside to save
- **Positioning:** Auto-center on edge (follows edge when nodes move)
- **Styling:**
  - Font size: 11px
  - Background: White semi-transparent box
  - Color: Gray (#6b7280)
- **Actions:** Delete label (press Delete when selected)

#### 2.4 Custom Arrows ✅ NEW
**Feature:** Draw arrows between annotations or from annotations to nodes
- **Purpose:** Point from explanatory notes to specific elements
- **Creation:** Button "Add Arrow" or keyboard shortcut A
- **Interaction:** Click start point → Click end point
- **Styling:**
  - Color: Red (warning), Blue (info), Green (success)
  - Stroke: Solid or dashed
  - Arrow head: Standard triangle
- **Actions:** Delete, change color

---

### Phase 3: Persistence & Export

#### 3.1 Autosave
**Feature:** Automatic recovery from crashes
- **Frequency:** Every 2 seconds (debounced)
- **Storage:** LocalStorage (`doc_mode_autosave`)
- **Recovery:** On page load, prompt to restore
- **Scope:** Documentation Mode only

#### 3.2 Save Layout (JSON Export)
**Feature:** Save work for later or version control
- **Trigger:** Button "Save Layout" or Ctrl+S
- **Format:** JSON file with metadata
- **Contents:**
  - All nodes (DB nodes + annotations + shapes)
  - All edges (including labels)
  - Custom positions
  - Viewport state
  - Metadata (timestamp, node count, etc.)
- **Filename:** `lineage_doc_[timestamp].json`

#### 3.3 Load Layout (JSON Import)
**Feature:** Resume previous work
- **Trigger:** Button "Load Layout"
- **Validation:** Schema validation (reject invalid JSON)
- **Behavior:** Replace current canvas (with confirmation)
- **Error Handling:** Show detailed error messages

#### 3.4 Export PNG/SVG
**Feature:** Create images for presentations
- **Formats:** PNG and SVG (both available)
- **Trigger:** Buttons "Export PNG" and "Export SVG"
- **Quality:** (Phase 2 - TBD based on requirements)
- **Area:** Full canvas content (all visible elements)
- **Filename:** `lineage_diagram_[timestamp].png/svg`

---

### Phase 4: Polish & UX

#### 4.1 Undo/Redo
**Feature:** Recover from mistakes
- **Implementation:** React Flow built-in `useUndoRedo` hook
- **History:** 5 levels
- **Actions Tracked:** Node add/remove/move, annotation edit, delete
- **Keyboard:** Ctrl+Z (undo), Ctrl+Shift+Z (redo)
- **UI:** Toolbar buttons (grayed when unavailable)

#### 4.2 Keyboard Shortcuts
**Feature:** Fast access to common actions
- **Shortcuts:**
  - T: Add text box
  - R: Add rectangle
  - A: Add arrow
  - Delete: Remove selected element
  - Ctrl+Z: Undo
  - Ctrl+Shift+Z: Redo
  - Ctrl+S: Save layout
  - Escape: Deselect / Exit editing
- **Discovery:** Tooltips show shortcuts

#### 4.3 Tooltips & Help
**Feature:** Guide users through interface
- **All Buttons:** Title attribute with description
- **Help Icon:** Link to documentation
- **Empty States:** Hints when canvas is empty

#### 4.4 Toast Notifications
**Feature:** Feedback for actions
- **Events:** Save success, import success, errors, warnings
- **Position:** Top-right
- **Duration:** 3 seconds (auto-dismiss)
- **Types:** Success (green), Error (red), Info (blue), Warning (amber)

---

## TECHNICAL ARCHITECTURE

### State Management

```
Main App State (Unchanged):
├─ nodes: Node[] (5,000-10,000 from DuckDB)
├─ edges: Edge[]
├─ filters: FilterState
└─ viewport: Viewport

Documentation Mode State (Separate):
├─ isDocMode: boolean
├─ docNodes: Node[] (max 100)
│   ├─ Type: 'database' | 'textbox' | 'rectangle'
│   ├─ sourceType: 'database' nodes cannot be edited
│   └─ Custom positions
├─ docEdges: Edge[]
│   └─ labels: EdgeLabel[]
├─ docArrows: Arrow[] (custom arrows)
├─ annotations: Annotation[] (textboxes)
├─ shapes: Shape[] (rectangles)
└─ viewport: Viewport (independent from main app)
```

### Key Architectural Decisions

**1. Separate Canvas:**
- Documentation Mode is NOT an overlay on Main App
- Completely separate React Flow instance
- Separate state, separate rendering
- Main app frozen while in Documentation Mode

**2. Node References:**
- Database nodes are references (not copies)
- Deleting from canvas = remove reference (node still in DuckDB)
- Can re-add from Node Explorer
- Annotations/shapes are new objects (owned by Documentation Mode)

**3. Edge Handling:**
- Edges auto-populated from database relationships
- User cannot create custom edges between DB nodes
- User CAN delete edges (remove from view)
- Custom arrows are separate from DB edges

**4. Persistence:**
- Autosave: LocalStorage (recovery only)
- Save/Load: JSON files (user-controlled)
- Export: PNG/SVG (static images)
- No server-side persistence in MVP

---

## COMPONENT SPECIFICATIONS

### 1. DocumentationModeToolbar
**Location:** Top of canvas (replaces Main App toolbar when active)

**Buttons:**
- Node Explorer toggle (show/hide sidebar)
- Add Text (T)
- Add Rectangle (R)
- Add Arrow (A)
- Undo (Ctrl+Z)
- Redo (Ctrl+Shift+Z)
- Save Layout (Ctrl+S)
- Load Layout
- Export PNG
- Export SVG
- Exit Documentation Mode

**State Indicators:**
- Node count: "50/100 nodes"
- Autosave status: "Saved 2 seconds ago"

---

### 2. NodeExplorerPanel
**Location:** Left sidebar (collapsible)

**Structure:**
```
┌─────────────────────────┐
│ 🔍 Search nodes...      │
├─────────────────────────┤
│ ▼ Tables (1,234)        │
│   □ dbo.customers       │
│   □ dbo.orders          │
│                         │
│ ▶ Views (456)           │
│                         │
│ ▶ Stored Procedures     │
│   (789)                 │
└─────────────────────────┘
```

**Features:**
- Search input (filters all types)
- Grouped by object type
- Collapsible sections
- Drag-and-drop to canvas
- Disabled when at 100 node limit

---

### 3. TextBox Component
**Type:** Custom React Flow node (`textbox`)

**Features:**
- Double-click to edit (contentEditable)
- Resizable (NodeResizer)
- Background color selector (3 presets)
- Font size selector (3 sizes)
- NodeToolbar (Duplicate, Delete)

**Default:**
- Size: 200px × 100px
- Color: Yellow (#fef3c7)
- Font: 14px
- Text: "Double-click to edit"

---

### 4. Rectangle Component
**Type:** Custom React Flow node (`rectangle`)

**Features:**
- Resizable (NodeResizer)
- Color picker (any color)
- Opacity slider (30%-100%)
- Dashed border (3px)
- Z-index: Behind nodes

**Default:**
- Size: 300px × 200px
- Color: User chooses on creation
- Opacity: 50%

---

### 5. Edge Label Component
**Type:** Custom edge label

**Features:**
- Double-click edge to add
- Click label to edit
- Auto-center on edge
- Moves with edge
- Delete with Delete key

**Styling:**
- Font: 11px, gray
- Background: White 80% opacity
- Padding: 4px 8px
- Border radius: 4px

---

### 6. Arrow Component
**Type:** Custom React Flow edge

**Features:**
- Click-to-place (start → end)
- Color selector (red, blue, green)
- Stroke style (solid, dashed)
- Arrow head (triangle)

**Default:**
- Color: Blue
- Stroke: Solid
- Width: 2px

---

## IMPLEMENTATION PHASES

### Phase 1: Core Infrastructure (4 days)

**Goals:**
- Documentation Mode toggle working
- Separate canvas with state management
- Node Explorer sidebar (drag-and-drop)
- 100 node limit enforcement

**Deliverables:**
- User can enter Documentation Mode
- User can add/remove nodes from Node Explorer
- Edges auto-populate
- Basic drag-and-drop positioning works

**Files:**
- `DocumentationModeToolbar.tsx` (NEW)
- `NodeExplorerPanel.tsx` (NEW)
- `App.tsx` (MODIFY - add doc mode state)
- `Toolbar.tsx` (MODIFY - add entry button)

---

### Phase 2: Annotations (3 days)

**Goals:**
- Text boxes working
- Rectangles working
- Resizing (NodeResizer)
- Basic styling options

**Deliverables:**
- User can add/edit text boxes
- User can add/resize rectangles
- Color pickers work
- NodeToolbar actions work (duplicate, delete)

**Files:**
- `TextBox.tsx` (NEW)
- `Rectangle.tsx` (NEW)
- `App.tsx` (MODIFY - register node types)

---

### Phase 3: Advanced Features (3 days)

**Goals:**
- Edge labels working
- Custom arrows working
- Undo/redo integrated

**Deliverables:**
- Double-click edge to add label
- Arrow tool works (click start → end)
- Ctrl+Z / Ctrl+Shift+Z work

**Files:**
- `EdgeLabel.tsx` (NEW)
- `Arrow.tsx` (NEW)
- `App.tsx` (MODIFY - undo/redo integration)

---

### Phase 4: Persistence (2 days)

**Goals:**
- Autosave working
- Save/Load JSON working
- Export PNG/SVG working

**Deliverables:**
- Work auto-saves every 2s
- Can save to/load from JSON
- Can export PNG and SVG

**Files:**
- `hooks/useAutosave.ts` (NEW)
- `utils/layoutPersistence.ts` (NEW)
- `utils/imageExport.ts` (MODIFY - add PNG support)

---

### Phase 5: Polish & Testing (3 days)

**Goals:**
- All keyboard shortcuts working
- Tooltips on all buttons
- Error handling complete
- Cross-browser testing
- Bug fixes

**Deliverables:**
- Professional polish
- No console errors
- Works in Chrome & Edge (Windows)
- Ready for UAT

---

### Total Timeline: 15 days (3 weeks)

**Breakdown:**
- Core: 4 days
- Annotations: 3 days
- Advanced: 3 days
- Persistence: 2 days
- Polish: 3 days

**Buffer:** +2 days for unexpected issues = **17 days total**

---

## DEFINITION OF DONE

### MVP Requirements (Must Have)

**Core Functionality:**
- [x] Can enter/exit Documentation Mode
- [x] Separate canvas from Main App
- [x] Node Explorer sidebar works
- [x] Can add up to 100 database nodes
- [x] Can remove nodes (remain in DuckDB)
- [x] Can drag nodes to custom positions
- [x] Edges auto-populate
- [x] Can delete edges

**Annotations:**
- [x] Can add text boxes
- [x] Can edit text inline (double-click)
- [x] Can resize text boxes (NodeResizer)
- [x] Can change text box colors (3 presets)
- [x] Can change font size (3 sizes)
- [x] Can add rectangles
- [x] Can resize rectangles
- [x] Can change rectangle color (custom picker)
- [x] Can change rectangle opacity

**Advanced Features:**
- [x] Can add labels to edges (double-click)
- [x] Can edit edge labels
- [x] Can add custom arrows
- [x] Arrows support color selection

**Persistence:**
- [x] Autosave every 2s
- [x] Recovery prompt on page load
- [x] Can save layout to JSON
- [x] Can load layout from JSON
- [x] Can export PNG
- [x] Can export SVG

**UX:**
- [x] Undo/redo works (5 levels)
- [x] All keyboard shortcuts work
- [x] All buttons have tooltips
- [x] Toast notifications for actions
- [x] Error messages are clear

**Quality:**
- [x] No console errors
- [x] TypeScript compiles
- [x] Works in Chrome (Windows)
- [x] Works in Edge (Windows)
- [x] Professional visual polish

---

## SUCCESS METRICS

### User Adoption
- **Target:** 50% of active users try Documentation Mode within 1 month
- **Measure:** Track "Create Documentation View" button clicks

### Export Usage
- **Target:** 100 PNG/SVG exports per month
- **Measure:** Track export button clicks

### Layout Saves
- **Target:** 30 layouts saved per month
- **Measure:** Track JSON downloads

### User Feedback
- **Target:** 4+ stars in user survey
- **Questions:**
  - "How easy was it to create a presentation diagram?"
  - "Did the exported image meet your quality expectations?"
  - "Would you use this feature again?"

### Time Saved
- **Target:** Reduce time to create lineage diagram from 2 hours (manual PPT) to 30 minutes
- **Measure:** User time tracking study (5-10 users)

---

## TECHNICAL REQUIREMENTS

### Browser Support
- **Primary:** Chrome (Windows) - Full support
- **Secondary:** Edge (Windows) - Full support
- **Out of Scope:** Safari, mobile browsers

### Performance Targets
- **Max Nodes:** 100 nodes (hard limit)
- **Canvas Rendering:** 60 FPS on drag
- **Autosave:** < 200ms
- **Export PNG:** < 5 seconds for 100 nodes
- **Node Explorer:** < 100ms to filter 10,000 nodes

### Data Limits
- **LocalStorage:** Max 5MB (autosave + 1-2 layouts)
- **JSON Export:** Max 2MB per file
- **PNG Export:** Max 10MB (4K resolution)

---

## DESIGN PRINCIPLES

### 1. PowerPoint Quality
Every export should look professional enough for executive presentations:
- Clear node labels
- Readable text annotations
- Appropriate spacing
- Professional color scheme

### 2. Intuitive Interactions
Follow familiar patterns:
- Double-click to edit (like Word/PPT)
- Drag to move (like PowerPoint shapes)
- Right-click for context menu (like all apps)
- Ctrl+Z to undo (universal)

### 3. Clear Visual Hierarchy
- Database nodes: Bold, colored borders (schema colors)
- Annotations: Subtle backgrounds (yellow/blue/white)
- Arrows: Bright colors for emphasis (red/blue/green)
- Grouping boxes: Low opacity, behind everything

### 4. Forgiving UX
Users should feel safe to experiment:
- Undo/redo (recover mistakes)
- Autosave (never lose work)
- Can re-add deleted nodes (from Node Explorer)
- Confirmation prompts (before destructive actions)

---

## FUTURE ENHANCEMENTS (Post-MVP)

### Phase 2 Candidates
- Export quality selector (1080p, 4K, custom DPI)
- Node custom labels (override database names)
- Icons/symbols (warning, checkmark, star)
- Text formatting (bold, italic, underline)
- Images/logos (company branding)
- Grid/snap-to-grid (alignment aids)
- Alignment tools (distribute, align left/right/center)
- Zoom to selection
- Copy/paste nodes and annotations

### Server-Side Features
- Save layouts to database (team sharing)
- Layout templates library
- Collaborative editing (real-time)
- Comment threads on nodes
- Version history

### Advanced Export
- Export to PDF (multi-page diagrams)
- Export to Visio format
- Export to draw.io XML
- Batch export (multiple views)

---

## APPENDIX

### A. React Flow Components Used

**Built-in Components:**
- `<ReactFlow>` - Main canvas
- `<NodeResizer>` - Resize handles
- `<NodeToolbar>` - Floating toolbar on nodes
- `<Panel>` - Floating UI panels
- `<Controls>` - Zoom/pan controls
- `<Background>` - Grid background

**Built-in Hooks:**
- `useReactFlow()` - Access to instance methods
- `useUndoRedo()` - Undo/redo management
- `useNodesState()` - Node state management
- `useEdgesState()` - Edge state management

### B. Design Tokens Reference

**From `design-tokens.ts`:**

**Schema Colors (30 colors):**
- Used for database node borders
- Tableau-inspired palette
- Accessible contrast ratios

**Semantic Colors:**
- Primary: Blue (#3b82f6)
- Success: Green (#22c55e)
- Warning: Amber (#facc15)
- Error: Red (#ef4444)

**Typography:**
- Font: System sans-serif stack
- Sizes: xs (12px), sm (14px), base (16px), lg (18px)

**Spacing:**
- 8px grid system
- xs (4px), sm (8px), md (12px), lg (16px), xl (24px)

### C. Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| **T** | Add text box |
| **R** | Add rectangle |
| **A** | Add arrow |
| **Delete** | Delete selected |
| **Ctrl+Z** | Undo |
| **Ctrl+Shift+Z** | Redo |
| **Ctrl+S** | Save layout |
| **Escape** | Deselect / Exit edit |
| **Double-click** | Edit node/edge |

### D. JSON Layout Schema

```json
{
  "metadata": {
    "name": "Customer Pipeline Diagram",
    "created": "2025-11-09T10:30:00Z",
    "version": "1.0",
    "nodeCount": 50,
    "annotationCount": 8
  },
  "nodes": [
    {
      "id": "node-123",
      "type": "database",
      "sourceType": "database",
      "position": { "x": 100, "y": 200 },
      "data": { "label": "dbo.customers", "schema": "dbo", "object_type": "Table" }
    },
    {
      "id": "textbox-456",
      "type": "textbox",
      "sourceType": "annotation",
      "position": { "x": 500, "y": 150 },
      "data": { "text": "Main customer data", "bgColor": "#fef3c7", "fontSize": "md" }
    }
  ],
  "edges": [
    {
      "id": "edge-789",
      "source": "node-123",
      "target": "node-456",
      "label": "Daily sync"
    }
  ],
  "arrows": [
    {
      "id": "arrow-101",
      "from": { "x": 500, "y": 150 },
      "to": { "x": 100, "y": 200 },
      "color": "blue",
      "style": "solid"
    }
  ],
  "viewport": {
    "x": 0,
    "y": 0,
    "zoom": 1
  }
}
```

---

## DOCUMENT REVISION HISTORY

**v1.0 (2025-11-09):** Initial comprehensive specification
- Based on critical review of Edit Mode spec v4.0
- Incorporates user feedback on "PowerPoint slide" metaphor
- Includes all features: edge labels, arrows, textboxes, rectangles
- Ready for implementation

---

**Version:** 1.0 FINAL
**Status:** ✅ Ready for Implementation
**Estimated Timeline:** 15-17 days (3-4 weeks)
**Next Steps:** Team review → UAT planning → Begin Phase 1
