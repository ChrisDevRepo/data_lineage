# Changelog - Data Lineage Visualizer Frontend

All notable changes to the frontend application will be documented in this file.

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
