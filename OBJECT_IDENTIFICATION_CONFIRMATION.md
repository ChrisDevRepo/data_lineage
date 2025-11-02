# Object Identification Method - Confirmation

**Date:** 2025-11-02
**Question:** Do we use object_id or full name (schema.table)?
**Answer:** ✅ **We use object_id exclusively**

---

## Summary

**✅ CONFIRMED:** The system uses **object_id** (integer) throughout the entire pipeline.

**Flow:**
1. Parser extracts `schema.table` from SQL text
2. Parser resolves `schema.table` → `object_id` via catalog lookup
3. Parser stores `object_id` in lineage_metadata
4. JSON export contains `object_id`
5. Frontend receives `object_id` and resolves back to names for display

---

## Detailed Flow

### Step 1: Parse SQL Text (String → String)

**Input:** DDL text
```sql
CREATE PROC sp_Example AS
SELECT * FROM CONSUMPTION_FINANCE.DimCustomers
INSERT INTO CONSUMPTION_FINANCE.FactSales
```

**Parser extracts:**
```python
regex_sources = {'CONSUMPTION_FINANCE.DimCustomers'}
regex_targets = {'CONSUMPTION_FINANCE.FactSales'}
```

**Code location:** `lineage_v3/parsers/quality_aware_parser.py:420-452`
```python
# Regex patterns extract schema.table
r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?'  # FROM [schema].[table]
r'\bJOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?'  # JOIN [schema].[table]

for schema, table in matches:
    sources.add(f"{schema}.{table}")  # String format: "schema.table"
```

---

### Step 2: Resolve to object_id (String → Integer)

**Method:** `_resolve_table_names(table_names)`

**Code location:** `lineage_v3/parsers/quality_aware_parser.py:1006-1036`

```python
def _resolve_table_names(self, table_names: Set[str]) -> List[int]:
    """Resolve table names to object_ids."""
    object_ids = []

    for name in table_names:
        parts = name.split('.')  # "CONSUMPTION_FINANCE.DimCustomers"
        schema, obj_name = parts

        query = """
        SELECT object_id
        FROM objects
        WHERE LOWER(schema_name) = LOWER(?)
          AND LOWER(object_name) = LOWER(?)
        """

        results = self.workspace.query(query, params=[schema, obj_name])
        if results:
            object_ids.append(results[0][0])  # ← INTEGER object_id

    return object_ids  # List[int]
```

**Example:**
```python
Input:  {'CONSUMPTION_FINANCE.DimCustomers', 'CONSUMPTION_FINANCE.FactSales'}
Lookup: CONSUMPTION_FINANCE.DimCustomers → object_id = 1234567
Lookup: CONSUMPTION_FINANCE.FactSales    → object_id = 7654321
Output: [1234567, 7654321]  # List of integers
```

---

### Step 3: Store in lineage_metadata (Integer)

**Table:** `lineage_metadata`

**Schema:**
```sql
CREATE TABLE lineage_metadata (
    object_id INTEGER,
    primary_source VARCHAR,
    confidence FLOAT,
    inputs VARCHAR,      -- JSON array of object_ids
    outputs VARCHAR,     -- JSON array of object_ids
    ...
)
```

**Sample data:**
```sql
object_id: 184996427
inputs:  "[1167456866, 1612280965]"  -- JSON string containing integer IDs
outputs: "[706008050]"
```

**Verification:**
```python
# Parse JSON
inputs = json.loads("[1167456866, 1612280965]")
# Result: [1167456866, 1612280965]  ← List of integers

# Check types
isinstance(1167456866, int)  # True ✅
```

---

### Step 4: Export to JSON (Integer)

**File:** `lineage_output/lineage.json`

**Format:**
```json
{
    "id": 184996427,
    "name": "spLoadSAPSalesSummary",
    "object_type": "Stored Procedure",
    "inputs": [1167456866, 1612280965],   ← Integer object_ids
    "outputs": [706008050]                 ← Integer object_ids
}
```

**Code location:** `lineage_v3/output/lineage_formatter.py`

```python
# Inputs/outputs are already integers from lineage_metadata
"inputs": json.loads(metadata.inputs),   # List[int]
"outputs": json.loads(metadata.outputs)  # List[int]
```

---

### Step 5: Frontend Display (Integer → String)

**Frontend receives:**
```json
{
    "inputs": [1167456866, 1612280965]  ← Integers
}
```

**Frontend resolves for display:**
```javascript
// Look up object_id in catalog
const inputObject = catalog.find(obj => obj.id === 1167456866)
// Display: "CONSUMPTION_FINANCE.SAP_Sales_Summary"
```

---

## Why object_id (Not schema.table)?

### Advantages of object_id

1. **Unique identifier**
   - object_id is unique across entire database
   - schema.table can have duplicates (different object types)
   - Example: `CONSUMPTION_FINANCE.DimCustomers` could be both a Table and a View

2. **Handles renames gracefully**
   - Object renamed: object_id stays same
   - Lineage graph remains valid
   - Historical data preserved

3. **Database-native**
   - object_id comes from `sys.objects.object_id`
   - Guaranteed unique by SQL Server/Synapse
   - No collision risk

4. **Efficient storage**
   - Integer: 4 bytes
   - String "CONSUMPTION_FINANCE.DimCustomers": 35+ bytes
   - 8-9x storage savings

5. **Fast lookups**
   - Integer equality: O(1) hash lookup
   - String comparison: O(n) character comparison
   - Significant performance difference at scale

6. **Type safety**
   - Strongly typed (INTEGER)
   - No parsing errors
   - No case sensitivity issues

### Disadvantages of schema.table

1. **Not unique**
   ```sql
   CONSUMPTION_FINANCE.DimCustomers (Table)     ← Same name!
   CONSUMPTION_FINANCE.DimCustomers (View)      ← Same name!
   ```

2. **Case sensitivity**
   ```python
   "CONSUMPTION_FINANCE.DimCustomers"  ≠  "consumption_finance.dimcustomers"
   ```
   Requires LOWER() for all comparisons

3. **Rename fragility**
   ```sql
   -- Table renamed
   ALTER TABLE DimCustomers RENAME TO DimCustomers_v2
   ```
   All lineage references break

4. **Storage inefficiency**
   - String storage expensive
   - Index size larger
   - Query performance worse

---

## Validation Rules

### Parser validates object existence

**Code location:** `lineage_v3/parsers/quality_aware_parser.py:1025-1034`

```python
query = """
SELECT object_id
FROM objects
WHERE LOWER(schema_name) = LOWER(?)
  AND LOWER(object_name) = LOWER(?)
"""

results = self.workspace.query(query, params=[schema, obj_name])
if results:
    object_ids.append(results[0][0])  # ← Only add if found
else:
    # Object doesn't exist in catalog
    # Do NOT add to dependencies
    logger.debug(f"Table {schema}.{obj_name} not found in catalog")
```

**Why this is important:**
- ✅ Prevents phantom dependencies
- ✅ Ensures all object_ids are valid
- ✅ Flags schema mismatches (as we saw with CONSUMPTION_POWERBI example)

### Example: Schema Mismatch

```python
# SP code says:
FROM CONSUMPTION_POWERBI.CadenceBudgetData

# Catalog lookup:
SELECT object_id FROM objects
WHERE schema_name = 'CONSUMPTION_POWERBI'
  AND object_name = 'CadenceBudgetData'
# Result: 0 rows (NOT FOUND)

# Parser action:
# Do NOT add to dependencies (can't use non-existent object_id)
# Result: Missing dependency in lineage (correct behavior!)
```

---

## Data Types Throughout Pipeline

| Stage | Data Type | Example | Location |
|-------|-----------|---------|----------|
| **SQL Text** | String | `"FROM CONSUMPTION_FINANCE.DimCustomers"` | DDL |
| **Regex Extract** | Set[str] | `{'CONSUMPTION_FINANCE.DimCustomers'}` | Parser Step 1 |
| **SQLGlot Extract** | Set[str] | `{'CONSUMPTION_FINANCE.DimCustomers'}` | Parser Step 2 |
| **Merged** | Set[str] | `{'CONSUMPTION_FINANCE.DimCustomers'}` | Parser Step 3 |
| **Resolved** | List[int] | `[1234567]` | Parser Step 5 |
| **lineage_metadata.inputs** | VARCHAR (JSON) | `"[1234567]"` | Database |
| **JSON export** | Array[int] | `[1234567]` | JSON file |
| **Frontend display** | String | `"CONSUMPTION_FINANCE.DimCustomers"` | UI |

---

## Summary Table

| Aspect | Value |
|--------|-------|
| **Primary key** | ✅ object_id (INTEGER) |
| **Storage format** | ✅ Integer |
| **Catalog lookup** | ✅ schema.table → object_id |
| **Validation** | ✅ Only valid object_ids stored |
| **Uniqueness** | ✅ Guaranteed by SQL Server |
| **Performance** | ✅ Fast integer comparisons |
| **Rename resilience** | ✅ object_id doesn't change |

---

## Conclusion

**✅ CONFIRMED:** The system uses **object_id** exclusively after the initial parsing stage.

**Flow:**
```
SQL Text (schema.table)
  ↓ regex/SQLGlot extract
Set[str] (schema.table)
  ↓ _resolve_table_names()
List[int] (object_id)      ← CONVERSION POINT
  ↓ store
lineage_metadata (object_id)
  ↓ export
JSON (object_id)
  ↓ display
Frontend (resolves object_id → schema.table for UI)
```

**Key Benefits:**
- Unique identifier (no collisions)
- Rename-safe (object_id persists)
- Efficient storage (integers)
- Fast lookups (hash-based)
- Database-native (SQL Server object_id)

**Validation:**
- Parser ONLY adds object_ids that exist in catalog
- Schema mismatches result in missing dependencies (correct behavior)
- No phantom or invalid references

---

**Status:** ✅ Confirmed - object_id used throughout, not schema.table
