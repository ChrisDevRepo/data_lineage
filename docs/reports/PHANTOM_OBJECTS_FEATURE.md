# Phantom Objects Feature (v4.3.0) + UDF Support

## Overview

Phantom objects are **tables/views/functions referenced in SQL but NOT in your metadata catalog**. Previously, these were silently dropped during parsing. Now they are:

- ✅ **Tracked** with negative IDs in `phantom_objects` table
- ✅ **Visualized** in the lineage graph with ❓ icon
- ✅ **Monitored** for promotion when metadata becomes available

## Problem Solved

**Before (v4.2.0):**
- SP references `consumption_powerbi.employeeutilization` (not in catalog)
- Parser silently drops it → Missing edge in graph
- No way to know which tables are missing from metadata

**After (v4.3.0):**
- SP references `consumption_powerbi.employeeutilization` (not in catalog)
- Parser creates phantom with ID=-1
- Graph shows: SP → ❓ `consumption_powerbi.employeeutilization`
- Tooltip warns: "⚠️ Phantom object (not in catalog)"

## Database Schema Changes

### New Tables

**phantom_objects**
```sql
CREATE TABLE phantom_objects (
    object_id BIGINT PRIMARY KEY,              -- Negative IDs (-1, -2, -3...)
    schema_name VARCHAR NOT NULL,
    object_name VARCHAR NOT NULL,
    object_type VARCHAR DEFAULT 'Table',
    phantom_reason VARCHAR DEFAULT 'not_in_catalog',
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    is_promoted BOOLEAN DEFAULT FALSE,
    promoted_to_id BIGINT,                     -- Real object_id after promotion
    UNIQUE(schema_name, object_name)
);
```

**phantom_references**
```sql
CREATE TABLE phantom_references (
    phantom_id BIGINT NOT NULL,                -- Links to phantom_objects
    referencing_sp_id BIGINT NOT NULL,         -- SP that uses the phantom
    dependency_type VARCHAR,                   -- 'input' or 'output'
    PRIMARY KEY (phantom_id, referencing_sp_id, dependency_type)
);
```

### Modified Tables

**dependencies** - Added column:
```sql
ALTER TABLE dependencies ADD COLUMN referenced_id BIGINT;
```
- Positive = real object
- Negative = phantom object

## Parser Changes

**quality_aware_parser.py** - New methods:

1. `_detect_phantom_tables()` - Finds tables not in catalog
2. `_create_or_get_phantom_objects()` - Creates phantom entries with negative IDs
3. `_track_phantom_references()` - Links SPs to phantoms

**Key behavior:**
- Phantoms appear in `inputs`/`outputs` for visualization
- Phantoms do **NOT** count in `found_count` for confidence
- Confidence based ONLY on real catalog matches ✅

## Frontend JSON Changes

**Phantom nodes have additional fields:**
```json
{
  "id": "-1",
  "name": "employeeutilization",
  "schema": "consumption_powerbi",
  "object_type": "Table",
  "is_phantom": true,                         // NEW
  "phantom_reason": "not_in_catalog",         // NEW
  "description": "⚠️ Phantom object (not in catalog)",
  "confidence": null,                         // null for phantoms
  "inputs": [],
  "outputs": ["123", "456"]
}
```

## UDF Support (v4.3.0)

**NEW: User-Defined Functions (UDFs) are now tracked and visualized!**

### Function Detection
Parser now detects:
- **Table-valued functions**: `FROM dbo.GetOrders() o`
- **Scalar functions**: `SELECT dbo.CalculatePrice(id)`
- **CROSS/OUTER APPLY**: `CROSS APPLY dbo.GetDetails(id)`

### Function Visualization
- **Real functions** → ◆ Diamond symbol (object_type='Function')
- **Phantom functions** → ❓ Question mark (not in catalog)
- **Direction**: Functions are INPUTS (func → SP)

### Example
```sql
CREATE PROCEDURE dbo.ProcessOrders AS
BEGIN
    SELECT dbo.CalculateTotal(order_id)  -- ◆ or ❓
    FROM dbo.GetActiveOrders() o         -- ◆ or ❓
END
```
- If functions in catalog: Diamond nodes
- If not in catalog: Question mark nodes (phantom functions)

## Frontend Tasks (User Action Required)

**React changes needed:**

1. **Node Symbol** - Use `node.node_symbol` field:
```jsx
switch (node.node_symbol) {
  case 'question_mark': return <QuestionMarkIcon />;  // ❓ Phantoms
  case 'diamond': return <DiamondIcon />;             // ◆ Functions
  case 'square': return <SquareIcon />;               // ■ SPs
  case 'circle': return <CircleIcon />;               // ● Tables/Views
}
```

2. **Tooltip** - Show appropriate message:
```jsx
{node.is_phantom && (
  <Tooltip>⚠️ {node.phantom_reason}</Tooltip>
)}
{node.object_type.includes('Function') && (
  <Tooltip>User-Defined Function</Tooltip>
)}
```

3. **Edge Styling** - Dotted lines for phantoms:
```jsx
const isPhantomEdge = sourceId < 0 || targetId < 0;
const edgeStyle = isPhantomEdge
  ? { strokeDasharray: '5,5' }  // Dotted
  : {};
```

## Phantom Promotion

When metadata is uploaded and phantom becomes real:

```python
from lineage_v3.utils.phantom_promotion import promote_and_reparse

workspace = DuckDBWorkspace("lineage_workspace.duckdb")
workspace.connect()

# After metadata upload, promote phantoms
results = promote_and_reparse(workspace)

print(f"Promoted: {results['promotion']['summary']['phantoms_promoted']}")
print(f"Re-parsed: {results['reparse']['success_count']} SPs")
```

**What happens:**
1. Phantom marked as `is_promoted=TRUE`
2. Linked to real `object_id` via `promoted_to_id`
3. Affected SPs re-parsed automatically
4. Phantom disappears from graph (replaced by real object)

## Testing

Run integration test:
```bash
python test_phantom_objects.py
```

Expected output:
```
✅ phantom_objects table exists
✅ phantom_references table exists
✅ Created phantom with negative ID: -2
✅ Duplicate phantom prevented by UNIQUE constraint
✅ ALL TESTS PASSED!
```

## Synapse Compatibility

✅ **Safe for Synapse**
- Phantoms only exist in local DuckDB workspace
- Synapse extraction unchanged (only positive IDs)
- `objects` table remains Synapse-sourced

## Current Data

Based on `catalog_coverage_analysis.json`:
- **37 phantom objects** will be created on first run
- **26 real business tables** missing from metadata:
  - `consumption_powerbi.*` (3 tables)
  - `consumption_prima_2.*` (11 tables)
  - `staging_prima.*` (3 tables)
  - Others (9 tables)
- **7 dummy.* temp tables** (filtered out, not created as phantoms)
- **4 system schema refs** (sys.*, information_schema.* - filtered out)

## Version

- **Feature:** Phantom Objects
- **Version:** v4.3.0
- **Date:** 2025-11-11
- **Parser:** quality_aware_parser.py
- **Database:** DuckDB schema v4.3.0

## Next Steps

After full reload:
1. ✅ Parser detects 26 real phantom objects
2. ✅ Frontend shows them with ❓ icon (user implements)
3. ✅ Graph edges dotted for phantom connections (user implements)
4. ✅ When metadata uploaded, auto-promotion + re-parse

---

**Questions?** Check test_phantom_objects.py for working examples.
