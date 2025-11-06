# System Filters Specification

**Date:** 2025-11-03
**Status:** DRAFT - Awaiting Approval
**Purpose:** Replace "Hide Unrelated" toggle with sophisticated system filtering

---

## Executive Summary

Replace the current "Hide Unrelated" boolean toggle with a **System Filters dropdown** that allows granular control over non-business objects (logging, system, and isolated objects). This provides developers with a cleaner default view while maintaining access to system-level information when needed.

---

## Problem Statement

### Current State
- **"Hide Unrelated" toggle:** Boolean on/off
- **Default:** ON (hides objects with no connections)
- **Issue:** Too coarse-grained - hides ALL unconnected objects together

### Issues
1. **ADMIN schema mixed with business data** - clutters graph
2. **Placeholders (parser bugs + isolated tables)** - inflate coverage, no value
3. **No visual distinction** between system vs business objects
4. **All-or-nothing filtering** - can't selectively show system objects

---

## Proposed Solution: System Filters Dropdown

### UI Component Change

**FROM:**
```
[✓] Hide Unrelated
```

**TO:**
```
System Filters: ▼
  [ ] Logging/Admin Objects (ADMIN.*)
  [ ] Placeholder Objects (no dependencies)
  [ ] Isolated Objects (no connections)
```

### Default Behavior
**All filters DISABLED by default** (checkboxes unchecked) = System objects HIDDEN

This means:
- ✅ Clean graph showing only business lineage
- ✅ Developers see relevant dependencies by default
- ❌ ADMIN.*, placeholders, isolated objects are hidden
- ✓ Can enable individually when needed

---

## Filter Categories

### Category 1: Logging/Admin Objects
**Definition:** Objects in the ADMIN schema

**Includes:**
- `ADMIN.Logs`
- `ADMIN.ETL_CONTROL`
- `ADMIN.Parameters`
- `ADMIN.Task`
- `ADMIN.PIPELINE_EXECUTION_LOG`
- All other `ADMIN.*` objects (85 total)

**Why filter:** System/infrastructure objects not part of business data lineage

**Color when visible:** 🤍 White/Light Gray
**Node style:** Border: dashed, opacity: 0.7

### Category 2: Placeholder Objects
**Definition:** Objects marked with `primary_source='placeholder'` and `confidence=0.0`

**Includes:**
- Tables/Views with NO dependencies found
- Mix of parser bugs (36) + truly isolated tables (217)
- Total: 253 objects

**Why filter:**
- No lineage value (empty inputs/outputs)
- Inflate coverage metrics
- Clutter graph with disconnected nodes

**Color when visible:** 🩶 Light Gray
**Node style:** Border: dotted, opacity: 0.5

**SQL Viewer behavior:** Show message "No DDL loaded for placeholder object"

### Category 3: Isolated Objects
**Definition:** Objects that have been parsed (`primary_source != 'placeholder'`) but have no connections

**Query:**
```sql
WHERE (inputs = '[]' OR inputs IS NULL)
AND (outputs = '[]' OR outputs IS NULL)
AND primary_source != 'placeholder'
```

**Includes:**
- Parsed SPs/Views/Tables with zero dependencies
- Could be legitimate standalone objects or parsing issues
- Current count: ~1 object

**Why filter:**
- No impact on other objects (safe to change)
- Clutters graph without adding value

**Color when visible:** Use schema color (maintain consistency)
**Node style:** Border: solid, opacity: 0.6

---

## Implementation Details

### Backend Changes

#### 1. Add Category Flags to Frontend JSON
**File:** `lineage_v3/output/frontend_formatter.py`

Add new fields to each node:
```python
{
    "id": "...",
    "name": "...",
    # ... existing fields ...
    "is_admin_schema": bool,  # True if schema_name == 'ADMIN'
    "is_placeholder": bool,   # True if primary_source == 'placeholder'
    "is_isolated": bool,      # True if inputs=[] AND outputs=[] AND not placeholder
    "system_category": str    # "admin" | "placeholder" | "isolated" | null
}
```

**Example:**
```json
{
  "id": "194475792",
  "name": "Logs",
  "schema": "ADMIN",
  "is_admin_schema": true,
  "is_placeholder": false,
  "is_isolated": false,
  "system_category": "admin"
}
```

#### 2. Update Summary Stats
**File:** `lineage_v3/output/summary_formatter.py`

Add to summary JSON:
```json
{
  "total_objects": 763,
  "parsed_objects": 763,
  "coverage": 100.0,
  "system_objects": {
    "admin_count": 85,
    "placeholder_count": 253,
    "isolated_count": 1,
    "total_system": 339
  },
  "business_objects": {
    "with_dependencies": 509,
    "percentage": 66.7
  }
}
```

### Frontend Changes

#### 1. Replace Toggle with Dropdown
**File:** `frontend/components/FilterPanel.tsx` (or equivalent)

**Current:**
```tsx
<Toggle
  label="Hide Unrelated"
  checked={hideUnrelated}
  onChange={setHideUnrelated}
/>
```

**New:**
```tsx
<Dropdown label="System Filters">
  <Checkbox
    label="Logging/Admin Objects (ADMIN.*)"
    checked={showAdminObjects}
    onChange={setShowAdminObjects}
  />
  <Checkbox
    label="Placeholder Objects (no dependencies)"
    checked={showPlaceholders}
    onChange={setShowPlaceholders}
  />
  <Checkbox
    label="Isolated Objects (no connections)"
    checked={showIsolated}
    onChange={setShowIsolated}
  />
</Dropdown>
```

**State management:**
```tsx
const [showAdminObjects, setShowAdminObjects] = useState(false);
const [showPlaceholders, setShowPlaceholders] = useState(false);
const [showIsolated, setShowIsolated] = useState(false);
```

#### 2. Update Filtering Logic
**File:** `frontend/hooks/useDataFiltering.ts`

**Add to filtering logic:**
```typescript
const preFilteredData = useMemo(() => {
    return allData.filter(node => {
        // Filter by system category
        if (node.system_category === 'admin' && !showAdminObjects) return false;
        if (node.system_category === 'placeholder' && !showPlaceholders) return false;
        if (node.system_category === 'isolated' && !showIsolated) return false;

        // Keep all other nodes
        return true;
    });
}, [allData, showAdminObjects, showPlaceholders, showIsolated]);
```

#### 3. Node Styling
**File:** `frontend/components/Graph.tsx` or node rendering logic

```typescript
const getNodeStyle = (node: DataNode) => {
    // Base style
    let style = {
        backgroundColor: getSchemaColor(node.schema),
        borderColor: '#333',
        borderStyle: 'solid',
        borderWidth: 2,
        opacity: 1.0
    };

    // Override for system categories
    if (node.system_category === 'admin') {
        style.backgroundColor = '#f5f5f5';  // Light gray
        style.borderStyle = 'dashed';
        style.opacity = 0.7;
    }

    if (node.system_category === 'placeholder') {
        style.backgroundColor = '#e0e0e0';  // Darker gray
        style.borderStyle = 'dotted';
        style.opacity = 0.5;
    }

    if (node.system_category === 'isolated') {
        style.opacity = 0.6;
    }

    return style;
};
```

#### 4. Dynamic Legend
**File:** `frontend/components/Legend.tsx`

**Add system categories ONLY when visible:**
```typescript
const legendItems = [];

// Schema colors (always visible)
schemas.forEach(schema => {
    legendItems.push({
        label: schema,
        color: getSchemaColor(schema),
        visible: true
    });
});

// System categories (only when enabled)
if (showAdminObjects) {
    legendItems.push({
        label: 'Logging/Admin (ADMIN.*)',
        color: '#f5f5f5',
        borderStyle: 'dashed',
        visible: true
    });
}

if (showPlaceholders) {
    legendItems.push({
        label: 'Placeholder (no dependencies)',
        color: '#e0e0e0',
        borderStyle: 'dotted',
        visible: true
    });
}

if (showIsolated) {
    legendItems.push({
        label: 'Isolated (no connections)',
        note: 'Uses schema color, reduced opacity',
        visible: true
    });
}
```

#### 5. SQL Viewer Special Handling
**File:** `frontend/components/SQLViewer.tsx` (or detail panel)

```typescript
const getDDLContent = (node: DataNode) => {
    if (node.system_category === 'placeholder') {
        return {
            content: '',
            message: 'No DDL loaded for placeholder object. This object has no dependencies.'
        };
    }

    return {
        content: node.ddl_text || '',
        message: node.ddl_text ? null : 'No DDL available'
    };
};
```

---

## Visual Design

### Color Palette

| Category | Background | Border | Opacity | Border Style |
|----------|-----------|--------|---------|--------------|
| Business Objects | Schema color | #333 | 1.0 | solid |
| Logging/Admin | #f5f5f5 (white/light gray) | #999 | 0.7 | dashed |
| Placeholder | #e0e0e0 (gray) | #999 | 0.5 | dotted |
| Isolated | Schema color | #333 | 0.6 | solid |

### Legend Examples

**Default view (all system filters OFF):**
```
Legend:
  🟦 CONSUMPTION_FINANCE
  🟩 CONSUMPTION_PRIMA
  🟨 CONSUMPTION_ClinOpsFinance
  ... (business schemas only)
```

**With Admin Objects enabled:**
```
Legend:
  🟦 CONSUMPTION_FINANCE
  🟩 CONSUMPTION_PRIMA
  🤍 Logging/Admin (ADMIN.*) [dashed border]
```

**With all system filters enabled:**
```
Legend:
  🟦 CONSUMPTION_FINANCE
  🟩 CONSUMPTION_PRIMA
  🤍 Logging/Admin (ADMIN.*) [dashed border]
  🩶 Placeholder (no dependencies) [dotted border]
  ⚪ Isolated (no connections) [reduced opacity]
```

---

## User Flow Examples

### Scenario 1: Default Developer Experience
1. Open lineage graph
2. **System filters: ALL OFF (default)**
3. See: Clean graph with only business objects (509 nodes)
4. Hidden: 85 ADMIN + 253 placeholders + 1 isolated = 339 hidden
5. Result: **66.7% business coverage visible**

### Scenario 2: Investigating System Dependencies
1. Developer suspects ADMIN.Logs is used
2. Enable "Logging/Admin Objects" filter
3. See: ADMIN objects appear in light gray with dashed borders
4. Legend updates to show "Logging/Admin" category
5. Can now trace dependencies involving ADMIN schema

### Scenario 3: Debugging Coverage Issues
1. Coverage shows 100% but seems inflated
2. Enable "Placeholder Objects" filter
3. See: 253 gray dotted nodes appear with no connections
4. Click placeholder node → SQL Viewer shows "No DDL loaded"
5. Understand: These are not parsed, just tracked

---

## Questions for Clarification

### 1. Category Overlap
**Question:** Some ADMIN objects are also placeholders. How should we handle overlap?

**Options:**
- A) Prioritize ADMIN category (if ADMIN schema, show as admin even if placeholder)
- B) Allow multiple categories (show as both admin AND placeholder)
- C) Create hierarchy (admin > placeholder > isolated)

**Recommendation:** Option A - Prioritize by schema (ADMIN > placeholder > isolated)

### 2. "Isolated" Category Precision
**Question:** Should "Isolated" include:
- A) Only objects with inputs=[] AND outputs=[] AND parsed?
- B) Also objects with only self-references (table references itself)?
- C) Objects with connections but in a disconnected graph component?

**Current:** Option A
**Recommendation:** Stick with A for simplicity

### 3. Color Scheme Flexibility
**Question:** Should system category colors be:
- A) Fixed (as specified above)
- B) User-customizable
- C) Theme-dependent (light/dark mode)

**Recommendation:** Option C - Theme-dependent with sensible defaults

### 4. Filter Persistence
**Question:** Should filter selections persist across:
- A) Page refreshes (localStorage)
- B) Only during session
- C) Never (reset to default)

**Recommendation:** Option A - Save to localStorage for better UX

### 5. Performance Considerations
**Question:** With 763 objects, filtering by category:
- Will this cause performance issues?
- Should we implement virtual scrolling for large graphs?
- Need to optimize filtering logic?

**Recommendation:** Monitor performance, optimize if > 1000 nodes

### 6. Metrics Display
**Question:** Should the UI show:
- A) Total coverage (100%) with breakdown
- B) Only business coverage (66.7%) by default
- C) Both with toggle

**Example:**
```
Coverage: 100% (763/763)
  Business: 509 (66.7%)
  System: 254 (33.3%)
```

**Recommendation:** Option C - Show both for transparency

---

## Implementation Plan

### Phase 1: Backend (Parser/Output)
1. Add category detection logic to `frontend_formatter.py`
2. Add `is_admin_schema`, `is_placeholder`, `is_isolated` flags
3. Update summary stats with system object counts
4. Test with current data

**Estimated effort:** 2-3 hours

### Phase 2: Frontend (UI Components)
1. Create System Filters dropdown component
2. Add state management for 3 filter checkboxes
3. Update filtering logic in `useDataFiltering.ts`
4. Implement node styling based on categories

**Estimated effort:** 3-4 hours

### Phase 3: Visual Polish
1. Implement color scheme
2. Add dynamic legend updates
3. Add SQL Viewer placeholder message
4. Test with various filter combinations

**Estimated effort:** 2-3 hours

### Phase 4: Testing & Documentation
1. Test with real data (763 objects)
2. Performance testing
3. Update user documentation
4. Create developer guide

**Estimated effort:** 2 hours

**Total estimated effort:** 10-12 hours

---

## Success Criteria

1. ✅ Default view shows only business objects (clean graph)
2. ✅ System objects can be enabled individually
3. ✅ Visual distinction clear (colors, borders, opacity)
4. ✅ Legend updates dynamically
5. ✅ SQL Viewer handles placeholders gracefully
6. ✅ Performance acceptable (<500ms filter toggle)
7. ✅ Coverage metrics accurate and transparent

---

## Risks & Mitigation

### Risk 1: User Confusion
**Risk:** Users don't understand system categories
**Mitigation:** Add tooltips, help text, onboarding tour

### Risk 2: Performance with Large Graphs
**Risk:** Filtering 1000+ nodes causes lag
**Mitigation:** Implement efficient filtering, virtual scrolling

### Risk 3: Category Misclassification
**Risk:** Objects incorrectly categorized
**Mitigation:** Extensive testing, allow manual override

---

## Open Questions (Need Decisions)

1. **Should we add a 4th category for "Test Objects"?**
   - Example: Tables ending in `_Test`, `_Temp`
   - Pro: Further cleanup
   - Con: More complexity

2. **Should filtering affect trace mode?**
   - When tracing dependencies, should system objects be:
     - A) Always included in trace (even if filtered)
     - B) Excluded if filtered
   - Recommendation: Option A

3. **Should we provide a "Show All" quick toggle?**
   - One-click to enable all system filters
   - Pro: Easier for debugging
   - Con: More UI clutter

4. **Should filter state be per-schema or global?**
   - Example: Show ADMIN for CONSUMPTION_FINANCE but not others?
   - Recommendation: Global for simplicity

---

## Recommendation

**PROCEED with implementation** with the following priorities:

**Must Have:**
- System Filters dropdown (3 categories)
- Default: ALL OFF (clean view)
- Color coding: admin (white), placeholder (gray), isolated (schema color dimmed)
- Dynamic legend

**Should Have:**
- SQL Viewer placeholder message
- Performance optimization
- localStorage persistence

**Nice to Have:**
- Tooltips explaining each category
- Metrics breakdown (business vs system)
- Onboarding tour

**DO NOT implement yet:**
- Test object category (wait for feedback)
- Schema-specific filtering (too complex)
- Manual category override (not needed initially)

---

## Next Steps

1. **Get approval on specification**
2. **Clarify open questions** (especially category overlap handling)
3. **Start with Phase 1** (backend changes)
4. **Iterate based on feedback**

---

**Awaiting your feedback and decisions on open questions before proceeding with implementation.**
