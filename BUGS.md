# Bug Tracking - Data Lineage Visualizer

> **Purpose:** Track open issues with business context, technical references, and status.
>
> **Status Legend:**
> - 🔴 **OPEN** - Issue reported, not resolved
> - 🟡 **IN PROGRESS** - Actively being worked on
> - 🟢 **RESOLVED** - Fixed, pending user approval
> - ✅ **CLOSED** - Approved by user as complete

---

## 🔴 BUG-001: Trace Filter Interaction & Toolbar Behavior

**Status:** 🔴 OPEN
**Reported:** 2025-11-07
**Priority:** HIGH

### Business Expectation

**What the user wants:**

The trace feature should work as **an additional filter layer** (not a separate "mode"), combining seamlessly with existing toolbar filters using AND logic.

**Expected User Workflow:**

1. **Start Trace** (Right-click node → "Start Trace"):
   - Trace controls panel appears below toolbar
   - No mode announcement or banner
   - Main toolbar remains **fully functional** during trace
   - User can change schemas, types, search, exclude terms at any time
   - Graph shows current base-filtered nodes (no preview yet)

2. **Adjust Parameters** (Inside trace controls):
   - User changes upstream/downstream levels
   - User optionally changes start node
   - Main toolbar stays **fully active and responsive**
   - Graph updates if toolbar filters change
   - No graph changes from trace until Apply is clicked

3. **Apply Trace** (Click "Apply" button):
   - System calculates traced nodes (within specified levels from start node)
   - Applies **ALL filters as AND condition**:
     - Trace filter (nodes within levels) AND
     - Schema filter (selected schemas) AND
     - Type filter (selected types) AND
     - Exclude filter (exclude terms)
   - Graph updates to show only nodes matching ALL conditions
   - Main toolbar **remains fully active** - user can continue changing filters
   - Each Apply click **re-runs** the trace with current parameters and filters
   - User can adjust levels and click Apply again → trace re-runs

4. **End Trace** (Click "End Trace" button):
   - Trace controls panel closes
   - IF Apply was clicked:
     - Trace filter **stays active** (persistent)
     - Amber banner appears: "🔍 Trace Filter Active - Showing X nodes from 'NodeName' (Y up / Z down)"
     - Graph shows same filtered nodes
     - Main toolbar **stays fully active** for further filtering
     - No notification needed (banner is the indicator)
   - IF Apply was NOT clicked:
     - Trace controls close silently
     - No banner, no notification
     - Graph returns to base filtered state

5. **Traced Filtered Mode** (After End Trace with applied filter):
   - Amber banner visible at top
   - User can change toolbar filters → graph updates with trace AND new filters
   - User can search → highlights within traced set
   - Click "Reset View" or X on banner → clears trace filter + banner

**Key Principle:** Trace is just another filter. All filters work together as AND conditions. No "entering/exiting modes" - just applying/removing filters.

### Technical Reference

**Files Involved:**
- `frontend/App.tsx` (lines 94-634)
  - State: `isTraceModeActive`, `isTraceFilterApplied`, `isInTracedFilterMode`, `tracedFilterConfig`
  - Handlers: `handleInlineTraceApply`, `handleEndTracing`, `handleResetView`

- `frontend/hooks/useDataFiltering.ts` (lines 238-276)
  - Filter logic: `finalVisibleData` useMemo
  - Must combine: trace + schemas + types + exclude as AND

- `frontend/hooks/useInteractiveTrace.ts` (lines 102-189)
  - Trace calculation: `performInteractiveTrace`
  - Apply handler: `handleApplyTrace`

- `frontend/components/InlineTraceControls.tsx`
  - Trace controls panel UI

- `frontend/components/TracedFilterBanner.tsx`
  - Amber banner component for persistent trace filter indicator

### Current Reported Issues

**Issue 1.1: Main Toolbar Disabled/Unresponsive During Trace**

**What happens:**
- When trace controls are open (`isTraceModeActive = true`), main toolbar appears disabled or unresponsive
- User cannot change schema/type selections while trace controls are visible
- Toolbar controls may be visually greyed out or clicks don't register

**Expected:**
- Main toolbar should be **fully active and responsive** at all times during trace
- User should be able to change any filter while trace controls are open
- Changing toolbar filters should update the graph immediately (combined with trace if Apply was clicked)

**Suspected Root Cause:**
- Check `Toolbar.tsx` for disabled props based on `isTraceModeActive`
- Check if event handlers are blocked when trace is active
- Check if there's CSS preventing interaction (pointer-events, z-index issues)

---

**Issue 1.2: Trace Filter Shows All Objects After "End Trace"**

**What happens:**
- User applies trace filter (clicks Apply) → correct filtered nodes shown
- User clicks "End Trace" → graph shows ALL objects instead of maintaining trace filter
- Amber banner may or may not appear

**Expected:**
- After "End Trace", trace filter should **stay active**
- Graph should show same filtered nodes (trace AND base filters)
- Amber banner should appear showing trace parameters

**Status:** 🟢 RESOLVED (2025-11-07)
- Fixed in commit `65dc87c`: Changed condition from `isTraceModeActive && isTraceFilterApplied` to just `isTraceFilterApplied`
- Now persists after End Trace
- **Pending user testing/approval**

---

**Issue 1.3: Base Filters Ignored During Trace**

**What happens:**
- User has schemas/types selected in toolbar
- User applies trace filter
- Graph shows traced nodes, but ignores schema/type selections from toolbar
- Only trace + exclude filters are applied

**Expected:**
- ALL filters should combine as AND:
  - Nodes in trace range AND
  - Nodes in selected schemas AND
  - Nodes in selected types AND
  - Nodes not matching exclude terms

**Status:** 🟢 RESOLVED (2025-11-07)
- Fixed in commit `65dc87c`: Added schema and type filters to trace condition
- Now combines all filters as AND
- **Pending user testing/approval**

---

**Issue 1.4: Apply Button Doesn't Re-run Trace**

**What happens:**
- User clicks Apply with levels 2/2
- User changes to levels 3/3
- User clicks Apply again
- Graph doesn't update with new levels

**Expected:**
- Each Apply click should re-calculate trace with current parameters
- Graph should update immediately with new traced nodes (combined with base filters)

**Status:** 🟢 RESOLVED (2025-11-07)
- Fixed in commit `16bbb13`: Create NEW Set/Array instances for filters to trigger React updates
- Apply now re-runs trace every time
- **Pending user testing/approval**

---

## 🔴 BUG-002: Full Text Search / Detail Search Issues

**Status:** 🔴 OPEN
**Reported:** 2025-11-07
**Priority:** MEDIUM

### Business Expectation

**What the user wants:**

The Detail Search modal should provide a **manual, serial search process** for finding objects by DDL content, with clear separation between search input and code viewing.

**Expected User Workflow:**

1. **Open Detail Search** (Click "Detail Search" button in toolbar)
2. **Type Search Query** (In search input field):
   - User types search term (e.g., "CREATE TABLE", "JOIN", "WHERE")
   - Typing should **NOT trigger any actions** in Monaco editor
   - Search is **manual only** - nothing happens until Enter is pressed
   - Placeholder: "Type to search DDL definitions, then press Enter to search..."
3. **Execute Search** (Press Enter key):
   - System searches through all DDL definitions
   - First panel shows **list of object names** that match
   - User can see how many results found
4. **View Details** (Click on object name):
   - Second panel shows DDL content for selected object
   - Monaco editor displays the code
   - Search term is highlighted in the code
   - User can read and examine the DDL
5. **Refine Search** (Type new query → Press Enter):
   - Process repeats with new search term
   - Results update in first panel

**Serial Process:** Type → Enter → See Object Names → Click → See Details

**Key Requirements:**
- No search icon button (removed)
- Manual trigger only (Enter key)
- Monaco editor should not capture keystrokes from search input
- Clear visual separation between search input and code viewer

**Visual Reference:** See screenshot (if available) showing the search modal layout

### Technical Reference

**Files Involved:**
- `frontend/components/DetailSearchModal.tsx`
  - Search input field
  - Results list panel
  - Monaco editor integration
  - Keyboard event handling

- `frontend/constants/monacoConfig.ts`
  - Shared Monaco editor configuration
  - Read-only settings
  - Find widget configuration

### Current Reported Issues

**Issue 2.1: Search Icon Still Present**

**What happens:**
- Detail Search modal shows a search icon button
- May be clickable and trigger search

**Expected:**
- Remove search icon completely
- Only Enter key should trigger search

**Status:** 🟢 RESOLVED (2025-11-07)
- Fixed in commit `882f459`: Removed search icon button, updated placeholder text
- **Pending user testing/approval**

---

**Issue 2.2: Typing Triggers Actions in Monaco Editor**

**What happens:**
- User types in search input field
- Monaco editor reacts to keystrokes (cursor moves, text input, etc.)
- Search input and Monaco editor are fighting for keyboard focus

**Expected:**
- Typing in search input should **only affect the search input**
- Monaco editor should **not respond** to keystrokes from search input
- Clear focus management between search input and code viewer

**Suspected Root Cause:**
- Monaco editor may be capturing global keyboard events
- Search input may not be properly preventing event propagation
- Focus may be jumping between input and editor

**Investigation Needed:**
- Check event handlers on search input (onKeyDown, onKeyPress, onChange)
- Check if Monaco editor has autofocus or global keyboard capture enabled
- Check CSS/DOM hierarchy for focus management issues

---

**Issue 2.3: Search Not Manual (Triggers on Typing)**

**What happens:**
- Typing in search input may trigger search automatically (debounced or on-change)
- Search executes without pressing Enter

**Expected:**
- Search should **only execute when Enter key is pressed**
- Typing alone should not trigger search
- User controls when to search

**Status:** 🟢 RESOLVED (2025-11-07)
- Fixed in commit `882f459`: Search triggers only on Enter key
- **Pending user testing/approval**

---

## Notes

- **Resolution Process:**
  1. Developer implements fix
  2. Status changes to 🟢 RESOLVED
  3. User tests the fix
  4. If approved → Status changes to ✅ CLOSED
  5. If not approved → Status reverts to 🔴 OPEN with additional notes

- **Adding New Bugs:**
  - Use next sequential number (BUG-003, BUG-004, etc.)
  - Follow same format: Business Expectation → Technical Reference → Current Issues
  - Include priority (HIGH/MEDIUM/LOW)

- **Closing Bugs:**
  - Only user can approve closure
  - Add closure date and final notes
  - Keep in file for historical reference

---

**Last Updated:** 2025-11-07
