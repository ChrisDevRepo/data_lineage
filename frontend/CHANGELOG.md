# Changelog - Data Lineage Visualizer Frontend

All notable changes to the frontend application will be documented in this file.

---

## [2.4.0] - 2025-10-27

### ✨ Added

#### **Auto-Fit and Highlight on Trace Apply**
- **Feature:** When applying a trace in Interactive Trace mode, the view automatically fits to show all traced nodes and highlights the start node
- **Benefit:** Better visual feedback and easier navigation when starting a trace
- **Implementation:**
  - Auto-fit view with 800ms smooth animation after applying trace
  - Start node highlighted in yellow immediately
  - 200ms delay allows layout to calculate before fitting
- **Files Changed:**
  - `App.tsx` - Added `handleApplyTraceWithFit` wrapper function

### 🔧 Fixed

#### **Click Behavior Improvements**
- **Fixed:** Simplified click logic - removed complex neighbor tracking that was causing issues
- **Fixed:** Clicking to unhighlight no longer causes camera zoom
- **Fixed:** SQL viewer click now works instantly on first click (consolidated to single handler)
- **Implementation:**
  - Removed duplicate click handlers between CustomNode and App.tsx
  - All click handling now in ReactFlow's `onNodeClick` only
  - `hasInitiallyFittedRef` prevents fitView from running on every state change
- **Files Changed:**
  - `App.tsx` - Simplified `handleNodeClick`, removed fitView from nodes effect
  - `CustomNode.tsx` - Removed `onClick` handler from div element

#### **Dimming Behavior with SQL Viewer**
- **Fixed:** When SQL viewer is open, nodes are no longer dimmed (all stay at full brightness)
- **Benefit:** Easier to read and click nodes when viewing SQL definitions
- **Implementation:**
  - Added `!sqlViewerOpen` condition to `shouldBeDimmed` calculation
  - Dimming only applies when SQL viewer is closed
- **Files Changed:**
  - `App.tsx` - Updated `finalNodes` memo with SQL viewer check

#### **Trace Exit Mode - Multiple Sessions**
- **Fixed:** Trace exit mode now works correctly on 2nd, 3rd, Nth trace sessions
- **Problem:** `isInTraceExitMode` flag wasn't being reset when entering trace again, preventing effect from running on subsequent exits
- **Solution:** Reset flag to false when entering trace mode
- **Files Changed:**
  - `App.tsx` - Added `setIsInTraceExitMode(false)` in trace entry effect

#### **Trace Exit Mode - Show Only Traced Objects**
- **Fixed:** Exiting trace mode now correctly shows ONLY the traced objects at defined depth levels
- **Problem:** Using `ref` instead of `state` meant changes weren't reactive, so `useDataFiltering` couldn't detect updates
- **Solution:** Converted `previousTraceResultsRef` to `traceExitNodes` state
- **Files Changed:**
  - `App.tsx` - Converted ref to state `[traceExitNodes, setTraceExitNodes]`
  - `useDataFiltering.ts` - Added trace exit mode filtering logic

#### **"Hide Unrelated" Filter Improvements**
- **Fixed:** "Hide Unrelated" is now a static pre-filter applied BEFORE schema/type filters
- **Fixed:** Checking/unchecking no longer causes nodes to move around when clicking objects
- **Problem:** Filter was applied after schema/type filters and recalculated on every click
- **Solution:** Separate `preFilteredData` memo that only recalculates when filter checkbox changes
- **Implementation:**
  - Stage 1: Pre-filter removes nodes with zero connections in complete graph
  - Stage 2: Schema/type filters applied to pre-filtered data
  - Independent of click events and node highlighting
- **Files Changed:**
  - `useDataFiltering.ts` - Split into `preFilteredData` and `finalVisibleData` memos

### 📝 Behavior Changes

#### **Dimming Logic**
- **Without SQL Viewer:** Clicked node highlighted (yellow), level 1 neighbors bright, others dimmed (20% opacity)
- **With SQL Viewer:** Clicked node highlighted (yellow), all others at full brightness (no dimming)

#### **Trace Mode Flow**
1. Click "Start Trace" → Opens trace panel
2. Select start node + configure levels
3. Click "Apply Trace" → **Auto-fits view + highlights start node** (NEW)
4. Click "Exit" → Shows only traced objects in detail view
5. Click outside → Clears trace, shows all with filters

#### **"Hide Unrelated" Behavior**
- Applied as first filter (before schema/type)
- Only hides nodes with zero connections in entire dataset
- Does NOT recalculate when clicking nodes
- Truly independent of other filters

---

## [2.3.0] - 2025-10-27

### ✨ Added - Table Structure Display in SQL Viewer

#### **Table DDL Display with Column Metadata**
- **Feature:** SQL viewer now displays CREATE TABLE statements with full column information for tables
- **Benefit:** Users can view table structure (columns, data types, constraints) directly in the UI without querying the database
- **Implementation:**
  - Backend generates CREATE TABLE DDL from `table_columns.parquet` metadata
  - Shows column names, data types, precision/scale, max length, and NULL constraints
  - Proper formatting for varchar(n), nvarchar(n), decimal(p,s), etc.
  - Handles MAX length columns (varchar(MAX), nvarchar(MAX))
  - Object ID mapping via `correct_object_id` column to handle ID changes between extractions
- **Files Changed:**
  - `lineage_v3/output/frontend_formatter.py` - Enhanced `_generate_table_ddl()` method
  - `lineage_v3/core/duckdb_workspace.py` - Added `table_columns` table support
  - `types.ts` - `ddl_text` field now populated for Tables (previously Views/SPs only)

**Data Format Example:**
```sql
CREATE TABLE [CONSUMPTION_FINANCE].[DimCustomers] (
    [CustomerID] int NOT NULL,
    [CustomerName] nvarchar(200) NULL,
    [Email] nvarchar(255) NULL,
    [CreatedDate] datetime NOT NULL,
    [Balance] decimal(18,2) NULL
);
```

**Requirements:**
- Backend must include `table_columns.parquet` file when uploading data
- File contains: object_id, schema_name, table_name, column_name, data_type, max_length, precision, scale, is_nullable, column_id

#### **Enhanced Empty State for Tables Without Metadata**
- **Feature:** Informative message displayed when table column metadata is not available
- **Benefit:** Clear user guidance on why table DDL isn't showing and how to enable it
- **Implementation:**
  - Shows table icon (SVG) with professional styling
  - "Table Structure Not Available" heading
  - Bulleted list explaining what would be displayed:
    - Column names and data types
    - Precision and scale for numeric columns
    - Max length for string columns
    - Nullable constraints
  - Clear instruction to include `table_columns.parquet` in dataset
- **Files Changed:**
  - `components/SqlViewer.tsx` - Enhanced empty state UI with educational content

**Empty State Display:**
- Professional dark theme styling matching VSCode
- Table icon for visual clarity
- Educational content explaining missing feature
- Actionable guidance for users

#### **SQL Viewer Header Improvements**
- **Feature:** Optimized header layout with better responsive behavior
- **Changes:**
  - Title font size reduced from 1.1rem to 0.95rem (smaller, cleaner)
  - Title color changed to softer gray (#cccccc) for less visual weight
  - Title truncates with ellipsis (...) when too long
  - Search box now has flexShrink: 0 to prevent being pushed off-screen
  - Search box reduced from 250px to 200px width with 150px minimum
  - Header padding reduced for more compact layout
  - Added minHeight: 52px for consistent header size
- **Benefit:** Search box always visible even with scrollbars; cleaner, more professional appearance
- **Files Changed:**
  - `components/SqlViewer.tsx` - Updated header styles and layout

**Visual Improvements:**
- Title never obscures search box
- Better space management in narrow panels
- Consistent header height across different content states
- Search box always accessible regardless of scrollbar width

---

## [2.2.0] - 2025-10-27

### ✨ Added - SQL Viewer Enhancements

#### **Resizable SQL Viewer with User Control**
- **Feature:** SQL viewer panel is now resizable with 1/3 screen width default (previously fixed at 50%)
- **Benefit:** Users can customize their workspace layout for optimal viewing
- **Implementation:**
  - Added drag handle between graph and SQL viewer panels
  - Default width: 33% (1/3 of screen) for SQL viewer, 67% for graph
  - Resize range constrained between 20% and 60% for usability
  - Smooth drag behavior with visual feedback (blue highlight on handle)
  - Disabled CSS transitions during resize to prevent "jumping" effect
  - Cursor changes to `col-resize` during drag operation
- **Files Changed:**
  - `App.tsx` - Added resize state, handlers, and dynamic width calculation
  - Layout uses inline styles for precise width control

**Usage:**
1. Open SQL viewer (click "View SQL" button)
2. Drag the gray vertical bar between graph and SQL panel
3. Panel resizes smoothly as you drag left/right
4. Release to set your preferred width

#### **Yellow Highlight for Selected Objects**
- **Feature:** Selected objects now highlighted in yellow instead of blue
- **Benefit:** Better visual distinction from blue trace mode indicators
- **Implementation:**
  - Changed border color from `border-blue-500` to `border-yellow-400`
  - Changed ring glow from `ring-blue-500/50` to `ring-yellow-400/50`
- **Files Changed:**
  - `components/CustomNode.tsx` - Updated highlight color classes

#### **Level 1 Neighbors Visibility**
- **Feature:** When an object is selected, its directly connected neighbors (level 1) remain fully visible
- **Benefit:** Easier to see immediate lineage context without visual clutter
- **Implementation:**
  - Build set of level 1 neighbors using `lineageGraph.neighbors()`
  - Modified dimming logic to exclude both highlighted nodes AND their neighbors
  - Only unrelated nodes (level 2+) are dimmed with opacity
- **Files Changed:**
  - `App.tsx` - Enhanced `finalNodes` useMemo with neighbor detection

**Behavior:**
- Selected node: Yellow highlight (border + ring glow)
- Level 1 neighbors: Full opacity, no highlight
- Unrelated nodes: Dimmed (opacity-20)

#### **UI Text Updates**
- **Change:** SQL viewer title changed from "SQL Definition" to "DDL"
- **Change:** Title text is now normal weight (not bold)
- **Files Changed:**
  - `components/SqlViewer.tsx` - Updated header text and font weight

---

## [2.1.1] - 2025-10-27

### ✨ Added - Data Model Type Filter Inheritance

#### **Data Model Type Filter Inheritance in Trace Mode**
- **Feature:** Trace mode now inherits data model type filters (Dimension, Fact, Lookup, Other) from detail mode
- **Benefit:** Complete filtering context preservation when entering trace mode
- **Implementation:**
  - Extended `TraceConfig` type with `includedTypes: Set<string>`
  - Pass `selectedTypes` from detail mode to `InteractiveTracePanel`
  - Panel initializes with inherited type filters instead of all types
  - Added filtering logic in graph traversal to respect type filters
  - User can modify type filters within trace mode for additional filtering
- **Files Changed:**
  - `types.ts` - Added `includedTypes` to `TraceConfig`
  - `components/InteractiveTracePanel.tsx` - Added type filter UI and inheritance
  - `App.tsx` - Pass type filters to trace panel
  - `hooks/useInteractiveTrace.ts` - Filter by data model type during traversal

**Usage Example:**
```
Detail Mode: User filters to show only "Dimension" and "Fact" tables
              ↓
Trace Mode: Opens with same 2 types pre-selected (section 4: Included Types)
              ↓
User can: Uncheck types to further narrow trace scope
              ↓
Trace Result: Only includes nodes matching both schema AND type filters
```

**New UI Section:**
- **Section 4: Included Types** - Checkboxes for Dimension, Fact, Lookup, Other
- Shows count: "Included Types (2/4)" when 2 out of 4 types selected
- Located between "Included Schemas" and "Exclusion Patterns" sections

**Behavior:**
- Type filters inherited automatically when entering trace mode
- Works in combination with schema filters (both must match)
- Reset button in trace panel resets types to all available types
- Nodes without `data_model_type` are included by default

---

### 🔧 Technical Details

**Type Filtering Logic:**
```typescript
// In useInteractiveTrace.ts
if (neighborNode.data_model_type && !config.includedTypes.has(neighborNode.data_model_type)) {
  return; // Skip this node if its type is not in the filter
}
```

**State Management:**
- Added `includedTypes` state in `InteractiveTracePanel`
- Inherited via `inheritedTypeFilter` prop from `App.tsx`
- Reset along with other filters via `handleReset()`

---

### 📝 Files Modified

| File | Changes | LOC Changed |
|------|---------|-------------|
| `types.ts` | Added `includedTypes` to `TraceConfig` | +1 line |
| `components/InteractiveTracePanel.tsx` | Added type filter UI and inheritance | ~20 lines |
| `App.tsx` | Pass type filters to trace panel | +2 lines |
| `hooks/useInteractiveTrace.ts` | Filter by type during traversal | +3 lines |

**Total:** ~26 lines of new/modified code

---

### 🧪 Testing

- [x] TypeScript compilation (no errors)
- [x] Vite dev server runs without errors
- [x] Type filter inheritance working
- [x] Type filtering in graph traversal working
- [x] UI displays type checkboxes correctly
- [x] Reset button resets type filters

---

### 🚀 How to Test

**Test Scenario: Type Filter Inheritance**
1. In detail mode, filter by specific types (e.g., only "Dimension" and "Fact")
2. Click "Start Trace"
3. Check trace panel section "4. Included Types"
4. ✅ **Expected:** Only "Dimension" and "Fact" are checked
5. Select a start node and apply trace
6. ✅ **Expected:** Trace only includes nodes matching selected types

---

**Previous Version:** 2.1.0
**Current Version:** 2.1.1
**Status:** ✅ Development Complete, Ready for Testing

---

## [2.1.0] - 2025-10-27

### ✨ Added - Interactive Trace Mode Enhancements

#### 1. **Preserve Selection When Exiting Trace Mode**
- **Feature:** Node selections from trace mode are now preserved when returning to detail view
- **Benefit:** Maintains user context when switching between trace and detail modes
- **Implementation:**
  - Stores trace results in a ref during trace mode
  - Applies stored results as highlighted nodes when exiting trace mode
  - Clears focused node to show all traced nodes equally
- **Files Changed:**
  - `App.tsx` - Added `previousTraceResultsRef` and effects
  - `hooks/useInteractiveTrace.ts` - Modified exit handler

**Usage Example:**
```
1. Filter to specific schemas in detail mode
2. Enter trace mode, select start node, apply trace
3. Click "Exit" on trace mode banner
4. ✨ All nodes from the trace are now highlighted in detail mode
```

---

#### 2. **Reset View Button**
- **Feature:** New reset button in toolbar to return to default view state
- **Benefit:** Quick way to clear all filters and selections with one click
- **Implementation:**
  - Reset button with circular arrows icon
  - Disabled during trace mode (can't reset while tracing)
  - Clears all filters, selections, and highlighted nodes
  - Shows notification: "View reset to default"
  - Automatically fits view after reset
- **Files Changed:**
  - `App.tsx` - Added `handleResetView()` function
  - `components/Toolbar.tsx` - Added reset button UI

**Resets:**
- ✅ Schema filters → All selected
- ✅ Type filters → All selected
- ✅ Highlighted nodes → Cleared
- ✅ Focused node → Cleared
- ✅ Search term → Cleared
- ✅ Hide unrelated → Disabled
- ✅ View mode → Detail
- ✅ Previous trace results → Cleared

**Location:** Toolbar, right side, between "Start Trace" and "Toggle Overlays" buttons

---

#### 3. **Schema Filter Inheritance (Detail → Trace Mode)**
- **Feature:** Trace mode now inherits the current schema filter from detail mode
- **Benefit:** Maintains filtering context when entering trace mode
- **Implementation:**
  - Pass `selectedSchemas` from detail mode to `InteractiveTracePanel`
  - Panel initializes with inherited filters instead of all schemas
  - User can still modify filters within trace mode (additional filtering)
- **Files Changed:**
  - `App.tsx` - Added `inheritedSchemaFilter` prop
  - `components/InteractiveTracePanel.tsx` - Updated initialization logic

**Behavior:**
```
Detail Mode: User filters to ["CONSUMPTION_FINANCE", "CONSUMPTION_ClinOpsFinance"]
              ↓
Trace Mode: Opens with same 2 schemas pre-selected
              ↓
User can: Uncheck schemas to further narrow trace scope
```

---

#### 4. **Additional Filtering Within Trace Mode**
- **Feature:** Ability to further refine schema filters within trace mode
- **Status:** ✅ Already existed, confirmed working with inherited filters
- **Implementation:**
  - Schema checkboxes in trace panel (section "3. Included Schemas")
  - Works independently from detail mode filter
  - Allows narrowing down the inherited schema set

**Workflow:**
```
Detail Mode: 5 schemas selected
    ↓
Trace Mode: Opens with 5 schemas inherited
    ↓
User Action: Unchecks 2 schemas in trace panel
    ↓
Trace Result: Only includes the remaining 3 schemas
```

---

### 🔧 Technical Details

**State Management:**
- Used `useRef` for `previousTraceResultsRef` to avoid unnecessary re-renders
- Effects properly synchronized to preserve selections across mode transitions
- Reset function comprehensively clears all stateful filters

**UI/UX Improvements:**
- Reset button tooltip: "Reset View to Default"
- Reset button disabled during trace mode for safety
- Notification feedback for reset action
- Schema inheritance happens automatically and transparently

**Backward Compatibility:**
- ✅ All existing functionality preserved
- ✅ No breaking changes to existing components
- ✅ Graceful degradation if features not used

---

### 📝 Files Modified

| File | Changes | LOC Changed |
|------|---------|-------------|
| `App.tsx` | Added reset handler, trace result preservation, schema inheritance | ~40 lines |
| `components/Toolbar.tsx` | Added reset button prop and UI | ~10 lines |
| `components/InteractiveTracePanel.tsx` | Added schema filter inheritance | ~5 lines |
| `hooks/useInteractiveTrace.ts` | Modified exit handler to preserve config | ~3 lines |

**Total:** ~58 lines of new/modified code

---

### 🧪 Testing Checklist

- [x] TypeScript compilation (no errors)
- [x] Vite dev server runs without errors
- [x] No runtime console errors
- [x] Reset button functional
- [x] Schema inheritance working
- [x] Selection preservation working
- [x] Additional trace filtering working

---

### 📚 Documentation Updated

- [x] CHANGELOG.md (this file)
- [ ] README.md (pending)
- [ ] CLAUDE.md (pending)

---

### 🚀 How to Test

**Dev Server:** `npm run dev` → http://localhost:3000

**Test Scenario 1: Preserve Selection on Exit**
1. Apply schema filters in detail mode
2. Click "Start Trace"
3. Configure trace (select start node, set levels)
4. Click "Apply Trace"
5. Click "Exit" on trace mode banner
6. ✅ **Expected:** Trace nodes are highlighted in detail mode

**Test Scenario 2: Reset Button**
1. Apply various filters (schemas, types, search)
2. Click some nodes to highlight them
3. Click reset button (circular arrows icon)
4. ✅ **Expected:** All filters cleared, full view restored

**Test Scenario 3: Schema Filter Inheritance**
1. Filter to 2-3 schemas in detail mode
2. Click "Start Trace"
3. Check trace panel schema section
4. ✅ **Expected:** Only the 2-3 schemas are checked

**Test Scenario 4: Additional Trace Filtering**
1. Start from previous scenario
2. Uncheck 1 schema in trace panel
3. Apply trace
4. ✅ **Expected:** Trace only includes remaining schemas

---

**Previous Version:** 2.0.0
**Current Version:** 2.1.0
**Status:** ✅ Deployed and Stable
