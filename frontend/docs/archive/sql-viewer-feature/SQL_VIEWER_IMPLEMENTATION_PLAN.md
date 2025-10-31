# SQL Viewer Implementation Plan - FINAL

**Date:** 2025-10-27
**Version:** 3.0 Feature Implementation
**Approach:** Embed DDL in JSON (Approach A)
**Status:** ✅ APPROVED - Ready for Implementation

---

## 📋 Executive Summary

### Architecture Verified

**Current System (v3.0 Web API):**
```
User Browser
    ↓
1. Upload Parquet files via ImportDataModal
    ↓
2. POST /api/upload-parquet (FastAPI backend in same container)
    ↓
3. Background processing (LineageProcessor class)
   - DuckDB workspace loads Parquet files
   - Parsers analyze Stored Procedures and Views
   - Generates JSON with lineage + DDL text
    ↓
4. Frontend polls GET /api/status/{job_id} (every 2 seconds)
    ↓
5. GET /api/result/{job_id} returns complete lineage JSON
    ↓
6. React Flow renders graph with all data in memory
```

**Key Finding:** Frontend and backend are in the **same Docker container**
**Network Latency:** <1ms (localhost communication)
**Deployment:** Single container via Azure Web App for Containers

---

## 🎯 Decision: Approach A (Embed DDL in JSON)

### Rationale

1. **Network is NOT a bottleneck** - Same container = <1ms latency (NOT 4G/WiFi)
2. **Dataset is manageable** - 211 objects (903 KB DDL) currently
3. **Instant UX** - Click node → SQL appears with 0ms delay
4. **Simpler architecture** - No new `/api/ddl/{id}` endpoint needed
5. **Backend already supports it** - `FrontendFormatter` can include DDL

### File Size Analysis

| Dataset | Nodes | DDL Size | Total JSON | Load Time (same container) |
|---------|-------|----------|------------|---------------------------|
| **Current (test)** | 85 visible | 903 KB (211 objects) | ~925 KB | <10ms ✅ |
| **Typical production** | 500 | ~2.2 MB | ~2.5 MB | <20ms ✅ |
| **Large production** | 10,000 | ~44 MB | ~45 MB | <100ms ✅ |

**Acceptable for same-container deployment** ✅

### What Gets Embedded

```json
{
  "id": "1001",
  "name": "spLoadDimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Stored Procedure",
  "description": "Confidence: 0.85",
  "data_model_type": "Other",
  "inputs": ["2001"],
  "outputs": ["3001"],
  "ddl_text": "CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimCustomers]\nAS\nBEGIN\n    INSERT INTO DimCustomers\n    SELECT * FROM StagingCustomers;\nEND"
}
```

**Rules:**
- Stored Procedures: Include full DDL from `definitions.parquet`
- Views: Include full DDL from `definitions.parquet`
- Tables: `ddl_text: null` (Tables don't have DDL)

---

## 🛠️ Implementation Tasks

### Phase 1: Backend Changes

**File:** `lineage_v3/output/frontend_formatter.py`

**Objective:** Add DDL text to frontend JSON output

**Changes Required:**

1. **Add parameter to `generate()` method:**
```python
def generate(
    self,
    internal_lineage: List[Dict[str, Any]],
    output_path: str = "lineage_output/frontend_lineage.json",
    include_ddl: bool = True  # ← NEW PARAMETER
) -> Dict[str, Any]:
```

2. **Modify `_transform_to_frontend()` method:**
```python
def _transform_to_frontend(self, internal_lineage):
    frontend_nodes = []

    for node in internal_lineage:
        # Existing transformation logic...

        # NEW: Add DDL text
        ddl_text = None
        if node['object_type'] in ['Stored Procedure', 'View']:
            # Query definitions table
            result = self.workspace.query("""
                SELECT definition
                FROM definitions
                WHERE object_id = ?
            """, [node['id']])

            if result and len(result) > 0:
                ddl_text = result[0][0]

        # Add to frontend node
        frontend_node = {
            # ... existing fields ...
            'ddl_text': ddl_text  # ← NEW FIELD
        }

        frontend_nodes.append(frontend_node)

    return frontend_nodes
```

**Testing:**
- Run backend with sample data
- Verify `frontend_lineage.json` has `ddl_text` field
- Check SPs/Views have DDL, Tables have `null`

**Estimated Time:** 30 minutes

---

### Phase 2: Frontend Type Updates

**File:** `frontend/types.ts`

**Objective:** Add DDL field to TypeScript type definition

**Changes Required:**

```typescript
export type DataNode = {
  id: string;
  name: string;
  schema: string;
  object_type: 'Table' | 'View' | 'Stored Procedure';
  description?: string;
  data_model_type?: 'Dimension' | 'Fact' | 'Lookup' | 'Other';
  inputs: string[];
  outputs: string[];
  ddl_text?: string | null;  // ← NEW FIELD (optional for backward compatibility)
};
```

**⚠️ IMPORTANT - Backward Compatibility:**

The `?` makes `ddl_text` **optional**, which means:
- ✅ Old JSON files (v2.0) without `ddl_text` will still import successfully
- ✅ New JSON files (v3.0) with `ddl_text` will work
- ✅ Sample data without DDL will work
- ✅ No breaking changes!

See [BACKWARD_COMPATIBILITY_PLAN.md](./BACKWARD_COMPATIBILITY_PLAN.md) for full details.

**Testing:**
- Run `npx tsc --noEmit` to verify no type errors

**Estimated Time:** 5 minutes

---

### Phase 3: Install Prism.js

**File:** `frontend/package.json`

**Objective:** Add syntax highlighting library

**Changes Required:**

```json
{
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "reactflow": "^11.11.4",
    "dagre": "0.8.5",
    "graphology": "0.25.4",
    "graphology-traversal": "0.3.1",
    "prismjs": "^1.29.0"  // ← NEW DEPENDENCY
  }
}
```

**Commands:**
```bash
cd frontend
npm install prismjs@^1.29.0
```

**Bundle Impact:** +4 KB gzipped (negligible)

**Estimated Time:** 5 minutes

---

### Phase 4: SQL Viewer Component

**File:** `frontend/components/SqlViewer.tsx` (NEW FILE)

**Objective:** Create split-view panel for SQL display

**Component Structure:**

```typescript
import React, { useState, useEffect, useRef } from 'react';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';  // Dark theme
import 'prismjs/components/prism-sql';        // SQL syntax

type SqlViewerProps = {
  isOpen: boolean;
  selectedNode: {
    id: string;
    name: string;
    schema: string;
    objectType: string;
    ddlText: string | null;
  } | null;
};

export const SqlViewer: React.FC<SqlViewerProps> = ({ isOpen, selectedNode }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedDdl, setHighlightedDdl] = useState('');
  const codeRef = useRef<HTMLPreElement>(null);

  // Syntax highlight DDL when node changes
  useEffect(() => {
    if (selectedNode?.ddlText) {
      const highlighted = Prism.highlight(
        selectedNode.ddlText,
        Prism.languages.sql,
        'sql'
      );
      setHighlightedDdl(highlighted);
      setSearchQuery('');
    }
  }, [selectedNode]);

  // Handle search highlighting
  useEffect(() => {
    if (!searchQuery || !codeRef.current) return;

    const regex = new RegExp(searchQuery, 'gi');
    let html = highlightedDdl.replace(
      regex,
      (match) => `<mark class="search-highlight">${match}</mark>`
    );

    if (codeRef.current) {
      codeRef.current.innerHTML = html;

      // Scroll to first match
      const firstMatch = codeRef.current.querySelector('.search-highlight');
      if (firstMatch) {
        firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [searchQuery, highlightedDdl]);

  if (!isOpen) return null;

  return (
    <div className="sql-viewer-panel">
      {/* Header */}
      <div className="sql-viewer-header">
        <h2>
          {selectedNode
            ? `${selectedNode.schema}.${selectedNode.name} - SQL Definition`
            : 'SQL Definition Viewer'}
        </h2>

        {/* Search box */}
        {selectedNode?.ddlText && (
          <input
            type="text"
            placeholder="Search SQL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="sql-search"
          />
        )}
      </div>

      {/* SQL content */}
      <div className="sql-viewer-content">
        {!selectedNode ? (
          <div className="sql-viewer-empty">
            <p>Click on any Stored Procedure or View to see its SQL definition</p>
          </div>
        ) : !selectedNode.ddlText ? (
          <div className="sql-viewer-empty">
            <p>No SQL definition available for this object</p>
            <p className="hint">
              {selectedNode.objectType === 'Table'
                ? '(Tables don\'t have DDL definitions)'
                : '(DDL not found in definitions)'}
            </p>
          </div>
        ) : (
          <pre ref={codeRef} className="language-sql">
            <code
              className="language-sql"
              dangerouslySetInnerHTML={{ __html: highlightedDdl }}
            />
          </pre>
        )}
      </div>
    </div>
  );
};
```

**Features:**
- ✅ Syntax highlighting with Prism.js (T-SQL)
- ✅ Empty state instructions
- ✅ Search with highlighting
- ✅ Scroll to first match
- ✅ Handles Tables (no DDL)
- ✅ Dark theme (prism-tomorrow.css)

**Estimated Time:** 2 hours

---

### Phase 5: Toolbar Button

**File:** `frontend/components/Toolbar.tsx`

**Objective:** Add toggle button for SQL viewer

**Changes Required:**

Add new button in toolbar (after "Hide Overlays" button):

```typescript
{/* SQL Viewer Toggle Button */}
<button
  onClick={onToggleSqlViewer}
  disabled={!sqlViewerEnabled}
  className={`toolbar-button ${sqlViewerOpen ? 'active' : ''}`}
  title={
    !hasDdlData
      ? 'Upload Parquet files to view SQL'
      : viewMode !== 'detail'
      ? 'Switch to Detail View to view SQL'
      : sqlViewerOpen
      ? 'Close SQL Viewer'
      : 'View SQL Definitions'
  }
>
  {sqlViewerOpen ? '✕ Close SQL' : '📄 View SQL'}
</button>
```

**Props to Add:**
```typescript
type ToolbarProps = {
  // ... existing props ...
  sqlViewerOpen: boolean;
  onToggleSqlViewer: () => void;
  sqlViewerEnabled: boolean;
  hasDdlData: boolean;
};
```

**Button States:**
- **Enabled:** When in Detail View + DDL data available
- **Disabled:** When in Overview mode OR no DDL data
- **Active (red):** When SQL viewer is open
- **Inactive (blue):** When SQL viewer is closed

**Estimated Time:** 30 minutes

---

### Phase 6: Node Click Handler

**File:** `frontend/components/CustomNode.tsx`

**Objective:** Make nodes clickable when SQL viewer is open

**Changes Required:**

```typescript
export const CustomNode = ({ data }) => {
  const handleClick = () => {
    // Only trigger if SQL viewer is open and node has DDL
    if (data.sqlViewerOpen && data.onNodeClick) {
      data.onNodeClick({
        id: data.id,
        name: data.name,
        schema: data.schema,
        objectType: data.object_type,
        ddlText: data.ddl_text
      });
    }
  };

  return (
    <div
      className={`custom-node ${data.sqlViewerOpen && data.ddl_text ? 'sql-clickable' : ''}`}
      onClick={handleClick}
      style={{
        cursor: data.sqlViewerOpen && data.ddl_text ? 'pointer' : 'default'
      }}
      title={
        data.sqlViewerOpen && data.ddl_text
          ? "Click to view SQL definition"
          : ""
      }
    >
      {/* Existing node content */}
      <Handle type="target" position={Position.Left} />
      <div className="node-content">
        <strong>{data.name}</strong>
        <div className="node-schema">{data.schema}</div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
};
```

**Visual Feedback:**
- Cursor changes to pointer on hover
- Hover effect (blue glow)
- Title tooltip shows "Click to view SQL"

**Estimated Time:** 30 minutes

---

### Phase 7: App Integration

**File:** `frontend/App.tsx`

**Objective:** Connect all components and manage SQL viewer state

**Changes Required:**

1. **Add State:**
```typescript
// SQL Viewer state
const [sqlViewerOpen, setSqlViewerOpen] = useState(false);
const [selectedNodeForSql, setSelectedNodeForSql] = useState<{
  id: string;
  name: string;
  schema: string;
  objectType: string;
  ddlText: string | null;
} | null>(null);
```

2. **Detect DDL Availability (memoized for performance):**
```typescript
// Check if ANY node has DDL data (backward compatible)
const hasDdlData = useMemo(() => {
  return allData.some(node => node.ddl_text != null && node.ddl_text !== '');
}, [allData]);
```

**⚠️ IMPORTANT - Backward Compatibility:**

This detection automatically handles:
- ✅ Old JSON (no `ddl_text` field) → `hasDdlData = false` → Button disabled
- ✅ New JSON (with `ddl_text`) → `hasDdlData = true` → Button enabled
- ✅ Sample data (no DDL) → `hasDdlData = false` → Button disabled
- ✅ Mixed data (some with DDL) → `hasDdlData = true` → Button enabled

3. **Add Handlers:**
```typescript
// Enable SQL viewer only in Detail View with DDL data
const sqlViewerEnabled = hasDdlData && viewMode === 'detail';

// Toggle SQL viewer
const handleToggleSqlViewer = () => {
  if (!sqlViewerEnabled) return;

  setSqlViewerOpen(!sqlViewerOpen);
  if (sqlViewerOpen) {
    setSelectedNodeForSql(null); // Clear selection when closing
  }
};

// Handle node click
const handleNodeClickForSql = (nodeData: any) => {
  if (sqlViewerOpen) {
    setSelectedNodeForSql(nodeData);
  }
};
```

4. **Update Layout:**
```typescript
return (
  <div className="app-container">
    <Toolbar
      // ... existing props ...
      sqlViewerOpen={sqlViewerOpen}
      onToggleSqlViewer={handleToggleSqlViewer}
      sqlViewerEnabled={sqlViewerEnabled}
      hasDdlData={hasDdlData}
    />

    <div className="main-content">
      {/* Graph container - 50% width when SQL viewer open */}
      <div className={`graph-container ${sqlViewerOpen ? 'split-view' : ''}`}>
        <ReactFlow
          nodes={nodes.map(n => ({
            ...n,
            data: {
              ...n.data,
              sqlViewerOpen,
              onNodeClick: handleNodeClickForSql,
              ddl_text: allData.find(d => d.id === n.id)?.ddl_text
            }
          }))}
          edges={edges}
          // ... existing props ...
        />
      </div>

      {/* SQL Viewer - 50% width, slides in from right */}
      {sqlViewerOpen && (
        <div className="sql-viewer-container">
          <SqlViewer
            isOpen={sqlViewerOpen}
            selectedNode={selectedNodeForSql}
          />
        </div>
      )}
    </div>
  </div>
);
```

**Estimated Time:** 1 hour

---

### Phase 8: CSS Styling

**File:** `frontend/App.tsx` (add inline styles or separate CSS file)

**Objective:** Style split view and SQL viewer panel

**Styles Required:**

```css
/* Split view layout */
.main-content {
  display: flex;
  height: calc(100vh - 60px);
  width: 100vw;
}

.graph-container {
  flex: 1;
  transition: all 0.3s ease;
}

.graph-container.split-view {
  flex: 0 0 50%;
}

.sql-viewer-container {
  flex: 0 0 50%;
  border-left: 2px solid #3e3e42;
}

/* SQL viewer panel */
.sql-viewer-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
}

.sql-viewer-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.sql-viewer-header h2 {
  flex: 1;
  margin: 0;
  color: #ffffff;
  font-size: 1.1rem;
}

.sql-search {
  width: 250px;
  padding: 0.5rem;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  background: #3c3c3c;
  color: #ffffff;
}

.sql-search:focus {
  outline: none;
  border-color: #007acc;
}

/* SQL content */
.sql-viewer-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.sql-viewer-content pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #d4d4d4;
}

/* Empty state */
.sql-viewer-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888888;
  text-align: center;
  padding: 2rem;
}

.sql-viewer-empty p {
  margin: 0.5rem 0;
  font-size: 16px;
}

.sql-viewer-empty .hint {
  font-size: 14px;
  color: #666666;
  font-style: italic;
}

/* Search highlighting */
.search-highlight {
  background-color: #ffd700;
  color: #000000;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: bold;
}

/* Clickable nodes */
.custom-node.sql-clickable {
  cursor: pointer;
}

.custom-node.sql-clickable:hover {
  box-shadow: 0 0 8px rgba(0, 122, 204, 0.6);
  border-color: #007acc;
}

/* Toolbar button */
.toolbar-button.active {
  background: #ff6b6b;
}

.toolbar-button:disabled {
  background: #555555;
  color: #888888;
  cursor: not-allowed;
  opacity: 0.5;
}

/* Scrollbar */
.sql-viewer-content::-webkit-scrollbar {
  width: 12px;
}

.sql-viewer-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.sql-viewer-content::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 6px;
}

.sql-viewer-content::-webkit-scrollbar-thumb:hover {
  background: #555555;
}
```

**Note:** Prism.js theme (prism-tomorrow.css) provides syntax highlighting colors automatically.

**Estimated Time:** 30 minutes

---

### Phase 9: Testing

**Test Plan:**

**Backend Tests:**
1. ✅ Generate JSON with `include_ddl=True`
2. ✅ Verify SPs have DDL text
3. ✅ Verify Views have DDL text
4. ✅ Verify Tables have `null` for DDL
5. ✅ Check large SP (47 KB) included
6. ✅ Check file size (should be ~925 KB for 211 objects)

**Frontend Tests:**
1. ✅ Import JSON with DDL field
2. ✅ SQL viewer button appears
3. ✅ Button is disabled in Overview mode
4. ✅ Button is disabled when JSON has no DDL
5. ✅ Click button → Split view opens (50/50)
6. ✅ Empty state shows instructions
7. ✅ Click SP node → SQL appears with syntax highlighting
8. ✅ Click View node → SQL appears
9. ✅ Click Table node → Message "Tables don't have DDL"
10. ✅ Click different node → SQL updates
11. ✅ Search "INSERT" → Highlights all matches
12. ✅ Large SQL (47 KB) → Scrolls smoothly, no lag
13. ✅ Close SQL viewer → Returns to full-width graph
14. ✅ Type check passes: `npx tsc --noEmit`

**Performance Tests:**
1. ✅ JSON load time < 100ms (925 KB file)
2. ✅ Graph rendering not affected by DDL data
3. ✅ Syntax highlighting < 50ms per node
4. ✅ Search highlighting < 100ms
5. ✅ Memory usage < 50 MB for 211 objects

**Commands:**
```bash
# Type check
cd frontend
npx tsc --noEmit

# Start dev server
npm run dev

# Test with real data
cd api
python main.py  # Backend on 8000
# Upload Parquet files via UI
# Verify SQL viewer works
```

**Estimated Time:** 1 hour

---

## 📋 Complete File Checklist

### Files to Modify (6 files):

- [ ] `lineage_v3/output/frontend_formatter.py`
  - Add `include_ddl` parameter
  - Query definitions table
  - Add `ddl_text` field to output

- [ ] `frontend/types.ts`
  - Add `ddl_text?: string | null` to DataNode type

- [ ] `frontend/package.json`
  - Add `prismjs: ^1.29.0` dependency

- [ ] `frontend/components/Toolbar.tsx`
  - Add SQL viewer toggle button
  - Add button state props

- [ ] `frontend/components/CustomNode.tsx`
  - Add click handler
  - Add visual feedback for clickable state

- [ ] `frontend/App.tsx`
  - Add SQL viewer state management
  - Add split-view layout
  - Connect all components
  - Add CSS styles (inline or import)

### Files to Create (1 file):

- [ ] `frontend/components/SqlViewer.tsx`
  - Complete component with Prism.js integration
  - Search functionality
  - Empty states
  - Syntax highlighting

---

## ⏱️ Timeline Summary

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Backend changes (frontend_formatter.py) | 30 mins |
| 2 | Type updates (types.ts) | 5 mins |
| 3 | Install Prism.js | 5 mins |
| 4 | SQL Viewer component | 2 hours |
| 5 | Toolbar button | 30 mins |
| 6 | Node click handler | 30 mins |
| 7 | App integration | 1 hour |
| 8 | CSS styling | 30 mins |
| 9 | Testing | 1 hour |
| **TOTAL** | | **~6.5 hours (1 day)** |

---

## 🎯 Success Criteria

- [ ] Backend generates `ddl_text` field in result JSON
- [ ] JSON file size < 5 MB for typical datasets (current: 925 KB ✅)
- [ ] SQL viewer toggle button works correctly
- [ ] Button disabled in Overview mode
- [ ] Button disabled when no DDL data
- [ ] Split view layout renders at 50/50 width
- [ ] Syntax highlighting displays T-SQL properly
- [ ] Keywords, strings, comments colored correctly
- [ ] Search highlights all matches in yellow
- [ ] Clicking nodes updates SQL instantly
- [ ] Tables show "No DDL available" message
- [ ] Large SQL (47 KB) scrolls smoothly
- [ ] No performance impact on graph rendering
- [ ] TypeScript compilation passes with no errors
- [ ] Works in Chrome, Firefox, Edge, Safari

---

## 📚 Dependencies Added

**NPM Package:**
- `prismjs@^1.29.0` (~4 KB gzipped)

**Prism.js Files:**
- Core: `prismjs`
- Theme: `prismjs/themes/prism-tomorrow.css`
- Language: `prismjs/components/prism-sql`

**Total Bundle Impact:** +4 KB gzipped (+0.8% of current bundle)

---

## 🚨 Edge Cases Handled

1. **No DDL data in JSON**
   - Button disabled with tooltip: "Upload Parquet files to view SQL"

2. **Overview mode**
   - Button disabled with tooltip: "Switch to Detail View to view SQL"

3. **Table clicked (no DDL)**
   - Show message: "No SQL definition available for this object (Tables don't have DDL definitions)"

4. **Very large SQL (>50 KB)**
   - Scrollbar appears automatically
   - Syntax highlighting still fast (<100ms)

5. **Search with no matches**
   - No highlighting, search box stays visible

6. **Empty search**
   - Original syntax highlighting restored

7. **User closes SQL viewer**
   - Selected node cleared
   - Graph returns to 100% width
   - Smooth transition (300ms)

---

## 📝 Notes

**DDL Inclusion Rules:**
- Stored Procedures: ✅ Include DDL
- Views: ✅ Include DDL
- Tables: ❌ `ddl_text: null` (no DDL for tables)

**SQL Viewer Activation:**
- Only works in **Detail View** mode
- Disabled in **Overview** mode (schema-level view)

**Performance:**
- DDL embedded at generation time (backend)
- No runtime fetching needed
- All data in memory for instant access

**⚠️ Backward Compatibility:**
- ✅ Old JSON files (v2.0 without `ddl_text`) continue to work
- ✅ SQL viewer button automatically disables when no DDL available
- ✅ Clear tooltips explain why button is disabled
- ✅ No breaking changes to existing functionality
- ✅ Sample data works without DDL
- 📄 See [BACKWARD_COMPATIBILITY_PLAN.md](./BACKWARD_COMPATIBILITY_PLAN.md) for full details

**Future Enhancements (not in scope for v3.0):**
- Copy SQL button
- Download SQL as .sql file
- Line numbers
- Diff view (compare versions)
- Syntax validation
- Format/beautify SQL

---

## ✅ Ready for Implementation

This plan has been reviewed and approved. All tasks are clearly defined with:
- Specific file changes required
- Code examples provided
- Testing criteria established
- Timeline estimated
- Success criteria defined

**Next Step:** Begin Phase 1 (Backend Changes)

---

**Document Status:** ✅ FINAL - APPROVED FOR IMPLEMENTATION
**Last Updated:** 2025-10-27
