# SQL Viewer - Backward Compatibility Plan

**Date:** 2025-10-27
**Concern:** Ensure SQL Viewer works with both old and new JSON formats
**Status:** ✅ PLANNED

---

## 🎯 Problem Statement

**Current JSON (v2.0 - without DDL):**
```json
{
  "id": "1001",
  "name": "spLoadDimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Stored Procedure",
  "inputs": ["2001"],
  "outputs": ["3001"]
}
```

**New JSON (v3.0 - with DDL):**
```json
{
  "id": "1001",
  "name": "spLoadDimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Stored Procedure",
  "inputs": ["2001"],
  "outputs": ["3001"],
  "ddl_text": "CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimCustomers]..."
}
```

**Requirement:** Frontend must work with BOTH formats!

---

## ✅ Solution: Optional Field with Graceful Degradation

### 1. TypeScript Type (Already Correct!)

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
  ddl_text?: string | null;  // ← OPTIONAL (backward compatible)
};
```

**The `?` makes it optional** - old JSON without `ddl_text` will still validate ✅

---

### 2. JSON Import Validation (Already Handles It!)

**File:** `frontend/components/ImportDataModal.tsx`

**Current validation logic:**
```typescript
const validateAndCleanData = (nodes: any[]): { data: DataNode[], errors: string[], warnings: string[] } => {
    // Only validates REQUIRED fields
    const requiredFields = ['name', 'schema', 'object_type', 'inputs', 'outputs'];

    // ddl_text is NOT in requiredFields
    // Therefore, it's optional and validation passes without it ✅
}
```

**No changes needed!** The validation already treats `ddl_text` as optional.

---

### 3. SQL Viewer Button Logic

**File:** `frontend/App.tsx`

**Detection logic:**
```typescript
// Detect if ANY node has DDL data
const hasDdlData = useMemo(() => {
  return allData.some(node => node.ddl_text != null && node.ddl_text !== '');
}, [allData]);

// Enable SQL viewer button only if DDL exists
const sqlViewerEnabled = hasDdlData && viewMode === 'detail';
```

**Behavior:**

| JSON Format | `hasDdlData` | Button State | User Experience |
|-------------|--------------|--------------|-----------------|
| **Old (no DDL)** | `false` | Disabled | Tooltip: "No DDL data available. Upload Parquet files to view SQL." |
| **New (with DDL)** | `true` | Enabled | Button clickable, SQL viewer works |
| **Mixed (some nodes have DDL)** | `true` | Enabled | SQL shows for nodes with DDL, message for nodes without |

---

### 4. Sample Data Generator

**File:** `frontend/utils/data.ts`

**Current implementation:** Does NOT include `ddl_text`

**Updated implementation (optional):**
```typescript
export const generateSampleData = (): DataNode[] => {
    // ... existing logic ...

    let nodes: DataNode[] = Array.from({ length: numNodes }, (_, i) => ({
        id: `node_${i}`,
        name: `${names[i % names.length]}_${i}`,
        schema: schemas[Math.floor(Math.random() * schemas.length)].toUpperCase(),
        object_type: types[Math.floor(Math.random() * types.length)],
        description: descriptions[i % descriptions.length],
        data_model_type: modelTypes[Math.floor(Math.random() * modelTypes.length)],
        inputs: [],
        outputs: [],
        // NEW: Add sample DDL for SPs and Views
        ddl_text: undefined  // ← Sample data doesn't need DDL (optional)
    }));

    return nodes;
};
```

**Decision:** Keep sample data WITHOUT `ddl_text` to demonstrate backward compatibility ✅

---

### 5. SQL Viewer Component - Handling Missing DDL

**File:** `frontend/components/SqlViewer.tsx`

**Empty state logic:**
```typescript
{!selectedNode ? (
  // No node selected yet
  <div className="sql-viewer-empty">
    <p>Click on any Stored Procedure or View to see its SQL definition</p>
  </div>
) : !selectedNode.ddlText ? (
  // Node selected but no DDL available
  <div className="sql-viewer-empty">
    <p>No SQL definition available for this object</p>
    <p className="hint">
      {selectedNode.objectType === 'Table'
        ? '(Tables don\'t have DDL definitions)'
        : '(DDL not included in this dataset)'}  {/* ← Handles old JSON */}
    </p>
  </div>
) : (
  // DDL available, show it
  <pre className="language-sql">
    <code dangerouslySetInnerHTML={{ __html: highlightedDdl }} />
  </pre>
)}
```

**User Experience:**
- Old JSON without DDL → Message: "DDL not included in this dataset"
- Table (even with new JSON) → Message: "Tables don't have DDL definitions"
- SP/View with DDL → Shows syntax-highlighted SQL

---

## 🧪 Testing Backward Compatibility

### Test Case 1: Import Old JSON (v2.0 format)

**Input:** `frontend_lineage.json` without `ddl_text` field

**Expected Behavior:**
1. ✅ JSON imports successfully (no validation errors)
2. ✅ Graph renders normally
3. ✅ SQL viewer button appears
4. ✅ SQL viewer button is DISABLED
5. ✅ Tooltip shows: "No DDL data available. Upload Parquet files to view SQL."
6. ✅ User cannot open SQL viewer (button unclickable)

**Test Command:**
```bash
# Use existing v2.0 JSON file
cp lineage_output/frontend_lineage.json test_old_format.json

# Import via UI
# Verify button is disabled
```

---

### Test Case 2: Import New JSON (v3.0 format)

**Input:** `frontend_lineage.json` WITH `ddl_text` field

**Expected Behavior:**
1. ✅ JSON imports successfully
2. ✅ Graph renders normally
3. ✅ SQL viewer button appears
4. ✅ SQL viewer button is ENABLED
5. ✅ User can click button to open SQL viewer
6. ✅ Clicking SP/View nodes shows DDL
7. ✅ Clicking Table nodes shows "Tables don't have DDL" message

---

### Test Case 3: Import Sample Data (no DDL)

**Input:** Click "Load Sample Data" button

**Expected Behavior:**
1. ✅ Sample data loads (40 nodes)
2. ✅ Graph renders normally
3. ✅ SQL viewer button is DISABLED (sample data has no DDL)
4. ✅ Tooltip shows: "No DDL data available"

---

### Test Case 4: Mixed Data (some nodes with DDL, some without)

**Input:** Manually edited JSON with DDL for some objects only

```json
[
  {
    "id": "1",
    "name": "spLoadData",
    "object_type": "Stored Procedure",
    "ddl_text": "CREATE PROCEDURE..."  // ← Has DDL
  },
  {
    "id": "2",
    "name": "DimCustomers",
    "object_type": "Table"
    // ← No ddl_text field
  }
]
```

**Expected Behavior:**
1. ✅ JSON imports successfully
2. ✅ SQL viewer button is ENABLED (at least one node has DDL)
3. ✅ Click SP → Shows DDL
4. ✅ Click Table → Shows "No SQL definition available"

---

## 📋 Implementation Checklist for Backward Compatibility

### Backend (frontend_formatter.py)

- [ ] Add `include_ddl` parameter (default: `True`)
- [ ] When `include_ddl=False`, omit `ddl_text` field entirely (for v2.0 compatibility)
- [ ] When `include_ddl=True`, add `ddl_text` field (v3.0 format)

**Example:**
```python
def generate(self, internal_lineage, output_path, include_ddl=True):
    for node in internal_lineage:
        frontend_node = {
            'id': node['id'],
            'name': node['name'],
            # ... other fields ...
        }

        # Conditionally add ddl_text
        if include_ddl and node['object_type'] in ['Stored Procedure', 'View']:
            frontend_node['ddl_text'] = get_ddl(node['id'])
        elif include_ddl:
            # Tables get null explicitly
            frontend_node['ddl_text'] = None
        # If include_ddl=False, don't add the field at all

        yield frontend_node
```

---

### Frontend (types.ts)

- [x] Make `ddl_text` optional with `?` ✅ Already done!

```typescript
ddl_text?: string | null;
```

---

### Frontend (ImportDataModal.tsx)

- [x] Validation does NOT require `ddl_text` ✅ Already correct!

**No changes needed** - current validation only checks required fields.

---

### Frontend (App.tsx)

- [ ] Detect DDL availability with `hasDdlData` check
- [ ] Disable SQL viewer button when `hasDdlData === false`
- [ ] Show appropriate tooltip message

```typescript
const hasDdlData = useMemo(() => {
  return allData.some(node => node.ddl_text != null && node.ddl_text !== '');
}, [allData]);

const sqlViewerEnabled = hasDdlData && viewMode === 'detail';
```

---

### Frontend (SqlViewer.tsx)

- [ ] Handle `ddlText === null` case
- [ ] Handle `ddlText === undefined` case
- [ ] Show appropriate message for each case

```typescript
if (!selectedNode.ddlText) {
  const reason = selectedNode.objectType === 'Table'
    ? '(Tables don\'t have DDL definitions)'
    : '(DDL not included in this dataset)';

  return <EmptyState message="No SQL definition available" hint={reason} />;
}
```

---

### Frontend (data.ts)

- [x] Sample data does NOT include `ddl_text` ✅ Demonstrates backward compatibility!

**No changes needed** - sample data intentionally excludes DDL to test old format.

---

## 🎨 User Experience Summary

### Scenario 1: User has old v2.0 JSON

```
User: "I have my old lineage JSON from last week"
      ↓
Imports JSON → Graph renders perfectly
      ↓
SQL Viewer button appears but is grayed out
      ↓
Hovers over button → Tooltip: "No DDL data available. Upload Parquet files to view SQL."
      ↓
User understands: Need to re-generate with Parquet upload to get SQL viewer
```

**Result:** ✅ No breaking changes, clear path to upgrade

---

### Scenario 2: User uploads Parquet files (v3.0)

```
User: "I'll upload my Parquet files"
      ↓
Backend generates JSON with DDL
      ↓
SQL Viewer button is ENABLED (blue)
      ↓
Clicks button → Split view opens
      ↓
Clicks nodes → SQL appears instantly
```

**Result:** ✅ Full SQL viewer functionality

---

### Scenario 3: User loads sample data

```
User: "Let me try the sample data first"
      ↓
Clicks "Load Sample Data"
      ↓
Graph renders with 40 sample nodes
      ↓
SQL Viewer button is DISABLED
      ↓
Hovers → Tooltip: "No DDL data available"
```

**Result:** ✅ Sample data demonstrates core features, SQL viewer shown but disabled

---

## 🔄 Migration Path

### For Users with Old JSON:

**Option A: Keep using old JSON (v2.0)**
- ✅ Everything works except SQL viewer
- ✅ No action required

**Option B: Regenerate with Parquet upload (v3.0)**
- Upload Parquet files via UI
- Backend generates new JSON with DDL
- ✅ SQL viewer now available

**Option C: Manually add DDL (advanced users)**
- Edit JSON file manually
- Add `ddl_text` field to nodes
- Re-import JSON
- ✅ SQL viewer works

---

## 📊 Compatibility Matrix

| JSON Format | Graph Rendering | Filtering | Trace Mode | SQL Viewer |
|-------------|----------------|-----------|------------|------------|
| **v1.0 (deprecated)** | ❌ Not supported | ❌ | ❌ | ❌ |
| **v2.0 (no DDL)** | ✅ Works | ✅ Works | ✅ Works | ⚠️ Button disabled |
| **v2.1 (with ddl_text=null)** | ✅ Works | ✅ Works | ✅ Works | ⚠️ Button disabled |
| **v3.0 (with DDL)** | ✅ Works | ✅ Works | ✅ Works | ✅ Fully functional |

---

## ✅ Backward Compatibility Guaranteed

**Summary:**

1. ✅ **Type safety** - `ddl_text` is optional in TypeScript
2. ✅ **Validation** - Imports work with or without `ddl_text`
3. ✅ **Detection** - Frontend detects DDL availability automatically
4. ✅ **Graceful degradation** - SQL viewer disabled when DDL unavailable
5. ✅ **Clear messaging** - Tooltips explain why button is disabled
6. ✅ **No breaking changes** - Old JSON files continue to work
7. ✅ **Upgrade path** - Clear instructions to enable SQL viewer

**Zero Breaking Changes** ✅

---

**Document Status:** ✅ COMPLETE - Backward Compatibility Planned
**Last Updated:** 2025-10-27
