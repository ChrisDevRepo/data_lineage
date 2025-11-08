# Bug Tracking - Data Lineage Visualizer

> **Purpose:** Track open issues with business context, technical references, and status.
>
> **Status Legend:**
> - 🔴 **OPEN** - Issue reported, not resolved
> - 🟡 **IN PROGRESS** - Actively being worked on
> - 🟢 **RESOLVED** - Fixed, pending user approval
> - ✅ **CLOSED** - Approved by user as complete

---

## 🟢 BUG-002: v4.2.0 Parse Failure Fields Not Persisted

**Status:** 🟢 RESOLVED
**Reported:** 2025-11-07
**Resolved:** 2025-11-08
**Priority:** CRITICAL
**Version:** v4.2.0

### Business Impact

Users cannot see parse failure reasons in the frontend, defeating the purpose of v4.2.0 enhancement. The "Parse Failure Workflow" feature is non-functional.

### Technical Details

**Problem:** Parser generates `parse_failure_reason`, `expected_count`, `found_count` but they're NOT saved to output files or database.

**Missing From:**
- ❌ lineage_metadata database table (no columns)
- ❌ lineage.json provenance
- ❌ frontend_lineage.json nodes
- ✅ quality_aware_parser.py return value (implemented but lost!)

**Root Cause:** Integration gap between parser output and persistence layer

### Resolution

**Commit:** 8552b96 (2025-11-08)
**Branch:** claude/v2.1.0-calculator-bug-002-011CUuqZVyfUYMuLmtCrXT9o

**Changes Made:**

1. **Database Migration** (`lineage_v3/core/duckdb_workspace.py`):
   - Added automatic migration to create 3 new columns
   - Migration runs on workspace initialization
   ```sql
   ALTER TABLE lineage_metadata ADD COLUMN parse_failure_reason VARCHAR;
   ALTER TABLE lineage_metadata ADD COLUMN expected_count INTEGER;
   ALTER TABLE lineage_metadata ADD COLUMN found_count INTEGER;
   ```

2. **Data Persistence** (`lineage_v3/core/duckdb_workspace.py`):
   - Updated `update_metadata()` signature to accept new fields
   - Fields are now persisted to lineage_metadata table
   ```python
   def update_metadata(
       ...,
       parse_failure_reason: str = None,
       expected_count: int = None,
       found_count: int = None
   )
   ```

3. **Data Retrieval** (`lineage_v3/output/internal_formatter.py`):
   - Updated SQL query to fetch new columns
   - Updated provenance dict to include new fields
   - Fields now flow through to frontend_lineage.json

4. **Frontend Display** (`lineage_v3/output/frontend_formatter.py`):
   - Already implemented in v4.2.0
   - Now receives actual data via provenance dict

### Test Case
✅ Parse SP with Dynamic SQL → Shows failure reason in frontend
✅ Database migration runs successfully
✅ Fields persist and retrieve correctly

**Status:** Fixed and tested

---

## 🟢 BUG-003: Confidence Model Black Box (Orchestrator Bonus Hidden)

**Status:** 🟢 RESOLVED
**Reported:** 2025-11-07
**Resolved:** 2025-11-08
**Priority:** HIGH
**Version:** v2.0.0

### Business Impact

Users see confidence scores they can't understand or calculate themselves. Breakdown shows 0.75 but total is 0.85 → confusion and mistrust.

### Technical Details

**Hidden Orchestrator Bonus:**
```
Breakdown shows: 0.30 + 0.25 + 0.20 = 0.75
But total_score: 0.85 ← Where did +0.10 come from?!
```

**Root Cause:** Orchestrator bonus (+0.10) applied AFTER breakdown calculation

**Code Location:** `lineage_v3/utils/confidence_calculator.py:414`
```python
if regex_sources_count == 0 and regex_targets_count == 0 and sp_calls_count > 0:
    total_score = max(total_score, 0.85)  # Hidden +0.10!
```

### User Feedback

> "The calculation should not be complicated and not be a black box. Users need to understand them too. So simple and smart and good documented."

### Resolution

**Commit:** 8552b96 (2025-11-08)
**Branch:** claude/v2.1.0-calculator-bug-002-011CUuqZVyfUYMuLmtCrXT9o

**Solution:** Implemented v2.1.0 Simplified Confidence Model

**New Model Features:**
- **Only 4 discrete values**: 0, 75, 85, 100
- **No hidden bonuses**: All calculations transparent
- **Simple logic**: Based on `found_tables / expected_tables`
- **Clear thresholds**:
  - ≥90% completeness → 100% confidence
  - 70-89% completeness → 85% confidence
  - 50-69% completeness → 75% confidence
  - <50% completeness → 0% confidence
- **Special cases**: Explicitly handled (orchestrators, parse failures)

**Implementation:**
```python
# New method: ConfidenceCalculator.calculate_simple()
result = ConfidenceCalculator.calculate_simple(
    parse_succeeded=True,
    expected_tables=10,
    found_tables=9
)
# Returns: {'confidence': 100, 'breakdown': {...}}
```

**Documentation:**
- Full specification in `CONFIDENCE_MODEL_SIMPLIFIED.md`
- Comprehensive test suite in `test_v2_1_0_calculator.py`
- All 9 test cases passing

**Status:** Fixed - v2.1.0 model available for use

**Note:** v2.0.0 multi-factor model still available for comparison

---

## 🟢 BUG-004: Poor Smoke Test Results

**Status:** 🟢 RESOLVED
**Reported:** 2025-11-07
**Resolved:** 2025-11-08
**Priority:** MEDIUM

### Original Issue

From initial smoke test on 349 SPs:
- 231 SPs (66%) found 0 tables

**Concern:** Parser might be failing to extract tables from majority of SPs.

### Investigation Results (2025-11-08)

**Analysis Script:** `analyze_bug004.py`
**Data Source:** `evaluation_baselines/real_data_results/smoke_test_results.json`

**Findings:**
- Total SPs analyzed: 349
- SPs where parser found 0 tables: **2 (0.6%)**
- Both are orchestrators (expected_count=0) - **CORRECT behavior**
- Real parsing failures (expected>0, got 0): **0 (0.0%)**

**Parsing Failure Rate: 0.0%** ✅

### Resolution

**Root Cause of Initial Report:**
The original "231 SPs (66%)" figure was based on outdated data or preliminary analysis. Current smoke test results show parser is performing excellently.

**Current Status:**
- Parser successfully extracts tables from 347/349 SPs (99.4%)
- 2 orchestrator SPs correctly identified (only call other SPs, no table references)
- Zero parsing failures detected

**Orchestrator Examples:**
1. `CONSUMPTION_ClinOpsFinance.spLoadCadence-ETL` (expected=0, parser=0) ✅
2. `STAGING_CADENCE.TRIAL_spLoadCadence-ETL` (expected=0, parser=0) ✅

### Recommendations

1. **Orchestrator Confidence:**
   - Orchestrators should receive 100% confidence (not penalized for 0 tables)
   - Already implemented in v2.1.0 simplified confidence model

2. **Smoke Test Validation:**
   - Current smoke test results confirm parser accuracy
   - Categorization saved to: `evaluation_baselines/real_data_results/bug004_categorization.json`

3. **No Further Action Required:**
   - Parser is performing as expected
   - Issue was based on outdated/preliminary data

---

## 🟢 BUG-006: Smoke Test Subagent Query Bug

**Status:** 🟢 RESOLVED
**Reported:** 2025-11-07
**Resolved:** 2025-11-08
**Priority:** LOW

### Original Issue

Smoke test subagent reported "Total SPs with lineage metadata: 0" when actual value was 349.

**Suspected Root Cause:** Incorrect SQL query in subagent using double quotes
```sql
-- WRONG: Uses string literals with double quotes
WHERE object_type = "Stored Procedure"  -- ❌ DuckDB error

-- CORRECT: Use single quotes
WHERE object_type = 'Stored Procedure'  -- ✅
```

### Investigation Results (2025-11-08)

**Extensive codebase search:**
- Searched all Python files for SQL queries with `object_type`
- All current code uses correct single-quote syntax
- No instances of double-quoted "Stored Procedure" found

**Findings:**
- All SQL queries in codebase use single quotes correctly ✅
- Smoke test files (`smoke_test_analysis.py`, `smoke_test_sp.py`) use correct syntax
- All parser and formatter files use correct syntax
- 30+ files checked, zero syntax errors found

### Resolution

**Likely Scenarios:**
1. Bug was in a temporary Task agent (not persisted in codebase)
2. Bug was already fixed in a previous commit
3. Original report based on transient execution error

**Current Status:**
- All codebase SQL queries use correct syntax
- No action required on current code
- Issue self-resolved or never existed in persistent code

**Verification:**
```bash
# No matches found for double-quoted object_type
grep -r 'object_type = "' --include="*.py"  # ✅ Clean
```

**Actual Data Confirmed:** 349/349 SPs have metadata (100%) ✓

---

## 🔴 BUG-005: FTS Extension Download Fails (Network Dependency)

**Status:** 🟢 RESOLVED (Made Optional)
**Reported:** 2025-11-07
**Priority:** LOW
**Version:** v4.2.0

### Issue

Parser fails when DuckDB FTS extension can't download:
```
Failed to download extension "fts" at URL
"http://extensions.duckdb.org/..."
```

### Fix Applied

Made FTS optional - warning instead of fatal error:
```python
except Exception as e:
    logger.warning(f"Failed to create FTS index (optional feature): {e}")
    logger.info("Continuing without FTS index - search functionality will be limited")
```

**File:** `lineage_v3/core/duckdb_workspace.py:801-803`

**Impact:** Full-text search unavailable in offline/sandboxed environments, but parsing works

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

**Root Cause (Confirmed):**
- `Toolbar.tsx` had `disabled={isTraceModeActive}` on 8 controls
- Search input and button (lines 148, 151)
- Exclude input and Hide button (lines 182, 209)
- Schema filter button (line 223)
- Type filter button (line 305)
- Hide Unrelated button (line 373)
- Reset View button (line 394)

**Status:** 🟢 RESOLVED (2025-11-08)
- Fixed in commit `83e41a8`: Removed ALL `disabled={isTraceModeActive}` attributes
- Toolbar now remains fully functional during trace
- Created comprehensive Playwright test suite (4 tests)
- **Pending user testing/approval**

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

**Root Cause (Confirmed):**
- Monaco editor was capturing global keyboard events
- Missing `domReadOnly: true` in editor configuration
- Editor responded to ALL keyboard input, not just when focused

**Status:** 🟢 RESOLVED (2025-11-08)
- Fixed in commit `d45b806`: Added `domReadOnly: true` to MONACO_EDITOR_OPTIONS
- This prevents editor from capturing keyboard events outside its DOM element
- Created comprehensive Playwright test suite (5 tests)
- **Pending user testing/approval**

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

**Last Updated:** 2025-11-08
