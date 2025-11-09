# DOCUMENTATION MODE - IMPLEMENTATION CHECKLIST
**Purpose:** Step-by-step checklist for implementing Documentation Mode
**Audience:** Developers building the feature

---

## PRE-IMPLEMENTATION

### Setup
- [ ] Read `DOCUMENTATION_MODE_SPECIFICATION.md` (root folder)
- [ ] Read `01_CURRENT_SYSTEM_ARCHITECTURE.md` (this folder)
- [ ] Review React Flow examples:
  - [ ] Node Resizer: https://reactflow.dev/examples/nodes/node-resizer
  - [ ] Drag and Drop: https://reactflow.dev/examples/interaction/drag-and-drop
  - [ ] Undo/Redo: https://reactflow.dev/api-reference/hooks/use-undo-redo
- [ ] Set up local environment:
  - [ ] Run `pip install -r requirements.txt`
  - [ ] Run `cd frontend && npm install`
  - [ ] Run `./start-app.sh`
  - [ ] Verify app loads on http://localhost:3000

---

## PHASE 1: CORE INFRASTRUCTURE (4 days)

### Day 1: Mode Toggle & Separate State

**Goal:** User can enter/exit Documentation Mode

**Tasks:**
- [ ] Add state to `App.tsx`:
  ```typescript
  const [isDocMode, setIsDocMode] = useState(false);
  const [docNodes, setDocNodes] = useState<Node[]>([]);
  const [docEdges, setDocEdges] = useState<Edge[]>([]);
  ```

- [ ] Add "Create Documentation View" button to `Toolbar.tsx`
  - [ ] Position: After "Export SVG" button
  - [ ] Icon: Pencil or document icon
  - [ ] Click handler: Opens node count selector dialog

- [ ] Create `NodeCountSelector` modal component
  - [ ] Input: Number field (default: 50, max: 100)
  - [ ] Buttons: Create, Cancel
  - [ ] Validation: Must be 1-100

- [ ] Create entry function:
  ```typescript
  const enterDocMode = (nodeCount: number) => {
    const filtered = getFilteredNodes(); // Current main app filters
    const initial = filtered.slice(0, nodeCount);
    setDocNodes(initial);
    // Auto-populate edges
    setDocEdges(/* edges between initial nodes */);
    setIsDocMode(true);
  };
  ```

- [ ] Create `DocumentationModeToolbar.tsx` (minimal for now)
  - [ ] "Exit Documentation Mode" button
  - [ ] Node counter: "X/100 nodes"

- [ ] Conditional rendering in `App.tsx`:
  ```typescript
  {isDocMode ? (
    <DocumentationCanvas />
  ) : (
    <MainCanvas />
  )}
  ```

**Testing:**
- [ ] Click "Create Documentation View"
- [ ] Enter 50 nodes
- [ ] Verify 50 nodes appear on new canvas
- [ ] Verify main toolbar hidden, doc toolbar visible
- [ ] Click "Exit Documentation Mode"
- [ ] Verify returns to main app unchanged

---

### Day 2: Node Explorer Sidebar (Part 1)

**Goal:** Sidebar shows all database nodes

**Tasks:**
- [ ] Create `NodeExplorerPanel.tsx`
  - [ ] Position: Left sidebar (absolute position)
  - [ ] Width: 280px
  - [ ] Collapsible header
  - [ ] Search input at top

- [ ] Load all nodes from main app:
  ```typescript
  const allDbNodes = allData; // From main app state
  ```

- [ ] Search/filter logic:
  ```typescript
  const [searchTerm, setSearchTerm] = useState('');
  const filtered = allDbNodes.filter(n =>
    n.name.toLowerCase().includes(searchTerm.toLowerCase())
  );
  ```

- [ ] Group by object type:
  ```typescript
  const grouped = {
    tables: filtered.filter(n => n.object_type === 'TABLE'),
    views: filtered.filter(n => n.object_type === 'VIEW'),
    sps: filtered.filter(n => n.object_type === 'STORED_PROCEDURE'),
  };
  ```

- [ ] Render collapsible sections:
  ```typescript
  <Collapsible title={`Tables (${tables.length})`}>
    {tables.map(node => (
      <div key={node.id} className="explorer-node">
        {node.name}
      </div>
    ))}
  </Collapsible>
  ```

**Testing:**
- [ ] Sidebar appears when in doc mode
- [ ] Search filters nodes correctly
- [ ] Sections collapse/expand
- [ ] Shows correct counts

---

### Day 3: Drag-and-Drop from Sidebar

**Goal:** User can drag nodes from sidebar to canvas

**Tasks:**
- [ ] Make sidebar nodes draggable:
  ```typescript
  <div
    draggable
    onDragStart={(e) => {
      e.dataTransfer.setData('application/reactflow', JSON.stringify(node));
      e.dataTransfer.effectAllowed = 'move';
    }}
  >
  ```

- [ ] Handle drop on canvas:
  ```typescript
  const onDrop = (event) => {
    event.preventDefault();
    const nodeData = JSON.parse(event.dataTransfer.getData('application/reactflow'));
    const position = reactFlowInstance.screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });

    // Check limit
    if (docNodes.length >= 100) {
      addNotification('Cannot add more than 100 nodes', 'error');
      return;
    }

    // Add node
    setDocNodes(nodes => [...nodes, { id: nodeData.id, position, data: nodeData }]);

    // Auto-connect edges
    const newEdges = findEdgesForNode(nodeData.id, docNodes);
    setDocEdges(edges => [...edges, ...newEdges]);
  };
  ```

- [ ] Add to ReactFlow:
  ```typescript
  <ReactFlow
    onDrop={onDrop}
    onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }}
  />
  ```

**Testing:**
- [ ] Drag node from sidebar to canvas
- [ ] Node appears at drop position
- [ ] Edges auto-connect to existing nodes
- [ ] Cannot add 101st node (error toast)

---

### Day 4: Node Management & Limit Enforcement

**Goal:** User can remove nodes, see limit warnings

**Tasks:**
- [ ] Add delete handler:
  ```typescript
  const handleDeleteNode = (nodeId: string) => {
    setDocNodes(nodes => nodes.filter(n => n.id !== nodeId));
    // Remove connected edges
    setDocEdges(edges => edges.filter(e =>
      e.source !== nodeId && e.target !== nodeId
    ));
  };
  ```

- [ ] Add Delete key listener:
  ```typescript
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isDocMode) return;
      if (e.key === 'Delete') {
        const selected = docNodes.filter(n => n.selected);
        selected.forEach(n => handleDeleteNode(n.id));
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isDocMode, docNodes]);
  ```

- [ ] Update node counter in toolbar:
  ```typescript
  <span className={docNodes.length >= 90 ? 'text-warning' : ''}>
    {docNodes.length}/100 nodes
  </span>
  ```

- [ ] Add warning toast at 90 nodes:
  ```typescript
  useEffect(() => {
    if (docNodes.length === 90) {
      addNotification('Approaching limit (90/100 nodes)', 'warning');
    }
  }, [docNodes.length]);
  ```

- [ ] Update context menu (add "Remove from Canvas"):
  ```typescript
  <ContextMenuItem onClick={() => handleDeleteNode(nodeId)}>
    Remove from Canvas
  </ContextMenuItem>
  ```

**Testing:**
- [ ] Right-click node → "Remove from Canvas"
- [ ] Node disappears
- [ ] Can re-add from sidebar
- [ ] Select node → Press Delete key
- [ ] Node disappears
- [ ] Counter updates
- [ ] Warning appears at 90 nodes

---

## PHASE 2: ANNOTATIONS (3 days)

### Day 5: Text Boxes

**Goal:** User can add/edit text boxes

**Tasks:**
- [ ] Create `TextBox.tsx` component:
  ```typescript
  interface TextBoxData {
    text: string;
    bgColor: '#fef3c7' | '#dbeafe' | '#ffffff';
    fontSize: 'sm' | 'md' | 'lg';
  }

  const TextBox: React.FC<NodeProps<TextBoxData>> = ({ id, data, selected }) => {
    const [isEditing, setIsEditing] = useState(false);
    const textRef = useRef<HTMLDivElement>(null);

    return (
      <div style={{ background: data.bgColor }}>
        <NodeResizer isVisible={selected} minWidth={150} minHeight={60} />
        <NodeToolbar isVisible={selected} position="top">
          <ColorButton color="#fef3c7" />
          <ColorButton color="#dbeafe" />
          <ColorButton color="#ffffff" />
          <FontSizeSelect value={data.fontSize} />
          <DeleteButton />
        </NodeToolbar>
        <div
          ref={textRef}
          contentEditable={isEditing}
          suppressContentEditableWarning
          onDoubleClick={() => setIsEditing(true)}
          onBlur={() => setIsEditing(false)}
        >
          {data.text}
        </div>
      </div>
    );
  };
  ```

- [ ] Register node type:
  ```typescript
  const nodeTypes = {
    custom: CustomNode,
    textbox: TextBox,
  };
  ```

- [ ] Add "Add Text" button to `DocumentationModeToolbar.tsx`

- [ ] Add creation handler:
  ```typescript
  const addTextBox = () => {
    const center = reactFlowInstance.getViewport();
    setDocNodes(nodes => [...nodes, {
      id: `textbox-${Date.now()}`,
      type: 'textbox',
      position: { x: center.x + 300, y: center.y + 200 },
      data: { text: 'Double-click to edit', bgColor: '#fef3c7', fontSize: 'md' }
    }]);
  };
  ```

- [ ] Add keyboard shortcut (T key)

**Testing:**
- [ ] Click "Add Text" button
- [ ] Text box appears at canvas center
- [ ] Double-click to edit
- [ ] Type text, click outside to save
- [ ] Click color buttons
- [ ] Background changes
- [ ] Change font size
- [ ] Text resizes
- [ ] Drag corners to resize box
- [ ] Press T key → new text box appears

---

### Day 6: Rectangles

**Goal:** User can add/resize rectangles

**Tasks:**
- [ ] Create `RectangleShape.tsx` component:
  ```typescript
  interface RectangleData {
    color: string;
    opacity: number;
  }

  const RectangleShape: React.FC<NodeProps<RectangleData>> = ({ id, data, selected }) => {
    return (
      <div style={{
        border: `3px dashed ${data.color}`,
        background: `${data.color}20`,
        opacity: data.opacity,
        borderRadius: '12px',
        zIndex: -1
      }}>
        <NodeResizer isVisible={selected} minWidth={100} minHeight={50} />
        <NodeToolbar isVisible={selected} position="top">
          <input type="color" value={data.color} onChange={handleColorChange} />
          <input type="range" min="0.3" max="1" step="0.1" value={data.opacity} onChange={handleOpacityChange} />
          <DeleteButton />
        </NodeToolbar>
      </div>
    );
  };
  ```

- [ ] Register node type

- [ ] Add "Add Rectangle" button

- [ ] Add creation handler (similar to text box)

- [ ] Add keyboard shortcut (R key)

**Testing:**
- [ ] Click "Add Rectangle"
- [ ] Rectangle appears
- [ ] Drag corners to resize
- [ ] Change color (color picker)
- [ ] Change opacity (slider)
- [ ] Rectangle renders behind DB nodes
- [ ] Press R key → new rectangle appears

---

### Day 7: Annotation Persistence

**Goal:** Annotations survive save/load

**Tasks:**
- [ ] Update save layout function to include annotations:
  ```typescript
  const saveLayout = () => {
    const layout = {
      nodes: docNodes, // Includes textboxes, rectangles
      edges: docEdges,
      viewport: reactFlowInstance.getViewport(),
    };
    localStorage.setItem('doc_mode_autosave', JSON.stringify(layout));
  };
  ```

- [ ] Update load layout function

- [ ] Test autosave:
  - [ ] Add text box
  - [ ] Wait 2 seconds
  - [ ] Refresh page
  - [ ] Verify text box restored

---

## PHASE 3: ADVANCED FEATURES (3 days)

### Day 8: Edge Labels

**Goal:** User can label connection lines

**Tasks:**
- [ ] Create `EdgeLabel.tsx` component

- [ ] Add double-click handler to edges:
  ```typescript
  const onEdgeDoubleClick = (event, edge) => {
    // Show input field at edge center
    setEditingEdgeId(edge.id);
  };
  ```

- [ ] Add label to edge data:
  ```typescript
  edges: [{
    id: 'edge-1',
    source: 'node-1',
    target: 'node-2',
    label: 'Daily ETL', // NEW
    labelStyle: { fontSize: 11, fill: '#6b7280' }
  }]
  ```

**Testing:**
- [ ] Double-click edge
- [ ] Input field appears
- [ ] Type "Daily ETL"
- [ ] Press Enter
- [ ] Label appears on edge
- [ ] Label moves with edge

---

### Day 9: Custom Arrows

**Goal:** User can draw arrows

**Tasks:**
- [ ] Create `Arrow.tsx` component (custom edge type)

- [ ] Add "Add Arrow" tool:
  ```typescript
  const [arrowMode, setArrowMode] = useState(false);
  const [arrowStart, setArrowStart] = useState(null);

  const onCanvasClick = (event) => {
    if (!arrowMode) return;

    const position = reactFlowInstance.screenToFlowPosition({
      x: event.clientX,
      y: event.clientY
    });

    if (!arrowStart) {
      setArrowStart(position);
    } else {
      // Create arrow from arrowStart to position
      addArrow(arrowStart, position);
      setArrowStart(null);
      setArrowMode(false);
    }
  };
  ```

- [ ] Add color selector

- [ ] Add keyboard shortcut (A key)

**Testing:**
- [ ] Click "Add Arrow"
- [ ] Click start point
- [ ] Click end point
- [ ] Arrow appears
- [ ] Change color
- [ ] Arrow color updates

---

### Day 10: Undo/Redo Integration

**Goal:** Ctrl+Z works for all actions

**Tasks:**
- [ ] Import React Flow hook:
  ```typescript
  import { useUndoRedo } from 'reactflow';

  const { undo, redo, canUndo, canRedo, takeSnapshot } = useUndoRedo({
    maxHistorySize: 5,
    enableShortcuts: true
  });
  ```

- [ ] Add undo/redo buttons to toolbar:
  ```typescript
  <button onClick={undo} disabled={!canUndo}>↶ Undo</button>
  <button onClick={redo} disabled={!canRedo}>↷ Redo</button>
  ```

- [ ] Test all actions:
  - [ ] Add node → Ctrl+Z → node removed
  - [ ] Delete node → Ctrl+Z → node restored
  - [ ] Drag node → Ctrl+Z → position reverted
  - [ ] Edit text box → Ctrl+Z → text reverted

---

## PHASE 4: PERSISTENCE (2 days)

### Day 11: Autosave & Recovery

**Goal:** Never lose work

**Tasks:**
- [ ] Create `useAutosave.ts` hook:
  ```typescript
  export const useAutosave = (docNodes, docEdges, isDocMode) => {
    const timeoutRef = useRef();

    useEffect(() => {
      if (!isDocMode) return;

      clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        const layout = { nodes: docNodes, edges: docEdges, timestamp: Date.now() };
        localStorage.setItem('doc_mode_autosave', JSON.stringify(layout));
      }, 2000);
    }, [docNodes, docEdges, isDocMode]);
  };
  ```

- [ ] Use in App.tsx:
  ```typescript
  useAutosave(docNodes, docEdges, isDocMode);
  ```

- [ ] Add recovery prompt:
  ```typescript
  useEffect(() => {
    const saved = localStorage.getItem('doc_mode_autosave');
    if (saved) {
      const layout = JSON.parse(saved);
      const confirm = window.confirm(`Restore unsaved work from ${new Date(layout.timestamp).toLocaleString()}?`);
      if (confirm) {
        setDocNodes(layout.nodes);
        setDocEdges(layout.edges);
      } else {
        localStorage.removeItem('doc_mode_autosave');
      }
    }
  }, []);
  ```

**Testing:**
- [ ] Add some nodes/annotations
- [ ] Wait 3 seconds
- [ ] Refresh page
- [ ] Confirm prompt appears
- [ ] Click "OK"
- [ ] Verify work restored

---

### Day 12: Save/Load JSON & Export

**Goal:** User can save/load layouts and export images

**Tasks:**
- [ ] Create `layoutPersistence.ts`:
  ```typescript
  export const saveLayoutToFile = (docNodes, docEdges) => {
    const layout = {
      metadata: { created: new Date().toISOString(), version: '1.0' },
      nodes: docNodes,
      edges: docEdges
    };
    const blob = new Blob([JSON.stringify(layout, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `lineage_doc_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  export const loadLayoutFromFile = (onSuccess, onError) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const layout = JSON.parse(event.target.result);
          onSuccess(layout);
        } catch (error) {
          onError('Invalid JSON file');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };
  ```

- [ ] Add Save/Load buttons to toolbar

- [ ] Add PNG export (copy existing SVG export, adapt for PNG)

**Testing:**
- [ ] Click "Save Layout"
- [ ] JSON file downloads
- [ ] Click "Load Layout"
- [ ] Select JSON file
- [ ] Layout restored
- [ ] Click "Export PNG"
- [ ] PNG file downloads
- [ ] Open in image viewer → looks good

---

## PHASE 5: POLISH & TESTING (3 days)

### Day 13: Keyboard Shortcuts & Tooltips

**Goal:** All shortcuts work, all buttons have tooltips

**Tasks:**
- [ ] Add tooltips to every button:
  ```typescript
  <button title="Add Text Box (T)">Add Text</button>
  ```

- [ ] Test all keyboard shortcuts:
  - [ ] T → Add text box ✓
  - [ ] R → Add rectangle ✓
  - [ ] A → Add arrow ✓
  - [ ] Delete → Remove selected ✓
  - [ ] Ctrl+Z → Undo ✓
  - [ ] Ctrl+Shift+Z → Redo ✓
  - [ ] Ctrl+S → Save layout ✓
  - [ ] Escape → Deselect / Exit editing ✓

---

### Day 14: Cross-Browser Testing

**Goal:** Works in Chrome and Edge (Windows)

**Tasks:**
- [ ] Test in Chrome:
  - [ ] All features work
  - [ ] No console errors
  - [ ] Performance acceptable (60 FPS drag)

- [ ] Test in Edge:
  - [ ] All features work
  - [ ] No console errors
  - [ ] Performance acceptable

**Known Issues to Check:**
- [ ] contentEditable cursor position (browser-specific)
- [ ] Color picker UI (different in Chrome vs Edge)
- [ ] Drag-and-drop ghost images

---

### Day 15: Bug Fixes & Final Polish

**Goal:** Production-ready quality

**Tasks:**
- [ ] Fix all bugs found during testing
- [ ] Code review (self-review checklist):
  - [ ] No console.log() statements
  - [ ] No TypeScript errors
  - [ ] No unused imports
  - [ ] Comments explain complex logic
  - [ ] Functions have clear names

- [ ] Visual polish:
  - [ ] Consistent spacing
  - [ ] Professional shadows
  - [ ] Smooth transitions
  - [ ] Accessible contrast ratios

- [ ] Update CLAUDE.md with Documentation Mode info

**Final Testing Checklist:**
- [ ] Can enter Documentation Mode
- [ ] Can add nodes from sidebar (drag-and-drop)
- [ ] Can add text boxes
- [ ] Can add rectangles
- [ ] Can add edge labels
- [ ] Can add arrows
- [ ] Can resize annotations
- [ ] Can undo/redo
- [ ] Can save layout (JSON)
- [ ] Can load layout (JSON)
- [ ] Can export PNG
- [ ] Can export SVG
- [ ] Autosave works
- [ ] Recovery prompt works
- [ ] 100 node limit enforced
- [ ] All keyboard shortcuts work
- [ ] All tooltips present
- [ ] No console errors
- [ ] Works in Chrome & Edge

---

## POST-IMPLEMENTATION

### Deployment to UAT
- [ ] Create pull request
- [ ] Code review by team
- [ ] Merge to UAT branch
- [ ] Deploy to UAT environment
- [ ] Smoke test in UAT
- [ ] Notify stakeholders for testing

### User Acceptance Testing
- [ ] Provide test scenarios to users
- [ ] Collect feedback
- [ ] Prioritize issues
- [ ] Fix critical bugs
- [ ] Re-deploy to UAT

### Production Deployment
- [ ] Final smoke test
- [ ] Merge to main
- [ ] Deploy to production
- [ ] Monitor for errors (first 24 hours)
- [ ] Gather usage metrics

---

## SUCCESS CRITERIA

**MVP is complete when:**
- [x] All checkboxes in this document are checked
- [x] All items in Definition of Done (main spec) are met
- [x] No blocking bugs
- [x] Works in Chrome & Edge (Windows)
- [x] Passes UAT

**Timeline:** 15 days (3 weeks)

**Next steps after MVP:**
- Gather user feedback
- Plan Phase 2 features (if needed)
- Monitor usage metrics
- Iterate based on data
