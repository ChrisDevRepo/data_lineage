# How expected_tables is Calculated

**Version:** v4.3.2
**Date:** 2025-11-12

---

## 🎯 Quick Answer

```python
expected_tables = len(regex_sources) + len(regex_targets)
```

**Source:** Regex scan of ORIGINAL DDL (before any preprocessing)

---

## 📋 Step-by-Step Calculation

### Step 1: Regex Baseline Scan

**File:** `lineage_v3/parsers/quality_aware_parser.py`
**Method:** `_sqlglot_parse()` (line 743)

```python
def _sqlglot_parse(self, cleaned_ddl: str, original_ddl: str):
    # STEP 1: Regex baseline (guaranteed coverage)
    sources, targets, _, _ = self._regex_scan(original_ddl)

    # Store baseline for comparison
    regex_sources = sources.copy()  # e.g., {Table1, Table2, Table3}
    regex_targets = targets.copy()   # e.g., {TargetTable}

    # expected_tables = len(regex_sources) + len(regex_targets)
    # This is the baseline count for confidence calculation
```

**Key Point:** Uses `original_ddl`, NOT `cleaned_ddl`

---

## 🔍 The _regex_scan() Method

**File:** `lineage_v3/parsers/quality_aware_parser.py`
**Lines:** 864-1045

### What It Does

Scans the **full original DDL** for table references using comprehensive regex patterns:

**Source Patterns (Input Tables):**
```python
# FROM clause
r'\bFROM\s+(\[?[\w]+\]?\.)?(\[?[\w]+\]?)'

# JOIN clauses (all types)
r'\b(INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN|JOIN)\s+(\[?[\w]+\]?\.)?(\[?[\w]+\]?)'
```

**Target Patterns (Output Tables):**
```python
# INSERT INTO
r'\bINSERT\s+INTO\s+(\[?[\w]+\]?\.)?(\[?[\w]+\]?)'

# UPDATE
r'\bUPDATE\s+(\[?[\w]+\]?\.)?(\[?[\w]+\]?)'

# DELETE FROM
r'\bDELETE\s+FROM\s+(\[?[\w]+\]?\.)?(\[?[\w]+\]?)'

# MERGE INTO
r'\bMERGE\s+INTO\s+(\[?[\w]+\]?\.)?(\[?[\w]+\]?)'
```

### Returns

```python
sources: Set[str]      # Input tables (FROM, JOIN)
targets: Set[str]      # Output tables (INSERT, UPDATE, DELETE, MERGE)
sp_refs: Set[str]      # Stored procedure calls (EXEC)
udf_refs: Set[str]     # User-defined function calls
```

---

## 📊 Example Calculation

### Example SQL

```sql
CREATE PROCEDURE [dbo].[spLoadFactSales] AS
BEGIN
    -- Statement 1: Metadata check
    DECLARE @count INT = (SELECT COUNT(*) FROM [dbo].[AuditTable]);

    -- Statement 2: Main data load
    INSERT INTO [dbo].[FactSales]
    SELECT
        s.SaleID,
        d.DateKey,
        c.CustomerKey,
        s.Amount
    FROM [dbo].[StagingSales] s
    INNER JOIN [dbo].[DimDate] d ON s.date_id = d.date_id
    LEFT JOIN [dbo].[DimCustomer] c ON s.customer_id = c.customer_id;
END
```

### Regex Scan Results

**Step 1: Scan original DDL**
```python
regex_sources = {
    'dbo.AuditTable',      # FROM in DECLARE
    'dbo.StagingSales',    # FROM in main query
    'dbo.DimDate',         # INNER JOIN
    'dbo.DimCustomer'      # LEFT JOIN
}

regex_targets = {
    'dbo.FactSales'        # INSERT INTO
}

expected_tables = len(regex_sources) + len(regex_targets)
                = 4 + 1
                = 5
```

---

## 🔬 Validation Against Catalog

### Step 2: Filter Non-Persistent Objects

**File:** `lineage_v3/parsers/quality_aware_parser.py`
**Method:** `_post_process_dependencies()` (lines 558-646)

```python
def _post_process_dependencies(self, sources, targets, sp_refs, udf_refs):
    # Remove system schemas
    sources = {s for s in sources if not s.startswith('sys.')}
    targets = {t for t in targets if not t.startswith('sys.')}

    # Remove temp tables
    sources = {s for s in sources if not s.split('.')[-1].startswith('#')}
    targets = {t for t in targets if not t.split('.')[-1].startswith('#')}

    # Remove variables
    sources = {s for s in sources if not s.split('.')[-1].startswith('@')}

    # Validate against catalog (real objects only)
    validated_sources = self._validate_against_catalog(sources)
    validated_targets = self._validate_against_catalog(targets)

    return validated_sources, validated_targets, sp_refs, udf_refs
```

### Step 3: Catalog Validation

**Method:** `_validate_against_catalog()` (lines 647-685)

```python
def _validate_against_catalog(self, table_refs: Set[str]) -> Set[int]:
    """
    Validates table references against catalog.
    Returns set of object_ids (positive for real, negative for phantom).
    """
    validated_ids = set()

    for ref in table_refs:
        # Parse schema.table
        parts = ref.split('.')
        schema = parts[0] if len(parts) == 2 else 'dbo'
        table = parts[1] if len(parts) == 2 else parts[0]

        # Look up in catalog
        object_id = self.workspace.get_object_id(schema, table)

        if object_id:
            # Real object (positive ID)
            validated_ids.add(object_id)
        else:
            # Phantom object (negative ID)
            phantom_id = self.workspace.create_phantom_object(schema, table, 'TABLE')
            validated_ids.add(phantom_id)

    return validated_ids
```

### Final expected_tables

```python
# After validation
validated_sources = {
    object_id_1,  # dbo.AuditTable
    object_id_2,  # dbo.StagingSales
    object_id_3,  # dbo.DimDate
    object_id_4   # dbo.DimCustomer
}

validated_targets = {
    object_id_5   # dbo.FactSales
}

expected_tables = len(validated_sources) + len(validated_targets)
                = 4 + 1
                = 5
```

---

## 🎯 How This Relates to Confidence

### Confidence Calculation

**File:** `lineage_v3/utils/confidence_calculator.py`

```python
def calculate_simple(parse_succeeded, expected_tables, found_tables, is_orchestrator):
    """
    Simplified confidence calculation (v2.1.0).

    expected_tables = Regex baseline count (from original DDL)
    found_tables = Combined count (regex + SQLGlot, after validation)
    """

    if not parse_succeeded:
        return {'confidence': 0, 'completeness_pct': 0}

    if is_orchestrator:
        return {'confidence': 100, 'completeness_pct': 100}

    if expected_tables == 0:
        return {'confidence': 0, 'completeness_pct': 0}

    # Calculate completeness
    completeness_pct = (found_tables / expected_tables) * 100

    # Map to discrete values
    if completeness_pct >= 90:
        confidence = 100
    elif completeness_pct >= 70:
        confidence = 85
    elif completeness_pct >= 50:
        confidence = 75
    else:
        confidence = 0

    return {
        'confidence': confidence,
        'completeness_pct': completeness_pct
    }
```

---

## 📈 Example: Confidence Calculation

### Scenario: Perfect Match

```python
# Regex baseline (expected)
expected_tables = 5  # From _regex_scan(original_ddl)

# SQLGlot + Regex combined (found)
found_tables = 5     # After validation

# Confidence
completeness_pct = (5 / 5) * 100 = 100%
confidence = 100  # ≥90% → 100
```

### Scenario: SQLGlot Adds Bonus Table

```python
# Regex baseline (expected)
expected_tables = 5

# SQLGlot found 1 extra table regex missed
found_tables = 6

# Confidence
completeness_pct = (6 / 5) * 100 = 120%
confidence = 100  # ≥90% → 100 (capped at 100)
```

### Scenario: Some Tables Filtered

```python
# Regex baseline (expected)
expected_tables = 5

# After filtering (removed temp table, CTE, etc.)
found_tables = 4

# Confidence
completeness_pct = (4 / 5) * 100 = 80%
confidence = 85  # 70-89% → 85
```

---

## 🔑 Key Insights

### 1. Why Original DDL?

```
Regex scan uses ORIGINAL DDL because:
- Full text preserved (no preprocessing artifacts)
- All tables captured (even in DECLARE, IF EXISTS, etc.)
- Provides most comprehensive baseline
- Used ONLY for expected_tables count
```

### 2. Why Cleaned DDL for SQLGlot?

```
SQLGlot uses CLEANED DDL because:
- Removes T-SQL syntax that breaks parsing
- Removes administrative queries (error logging, metadata checks)
- Simplifies complex expressions
- Used for ENHANCEMENT, not baseline
```

### 3. Expected vs Found

```
expected_tables (Regex baseline):
- Scans ORIGINAL DDL
- Includes ALL table references
- Used as denominator in confidence formula

found_tables (Combined results):
- Union of regex + SQLGlot
- After validation and filtering
- Used as numerator in confidence formula
```

---

## 📊 Real Example from Database

### SP: spLoadFactLaborCostForEarnedValue_Post

**Regex Baseline:**
```python
regex_sources = {
    'dbo.DimProject',
    'dbo.DimDate',
    'dbo.FactLaborCost',
    'dbo.DimEmployee'
}

regex_targets = {
    'dbo.FactLaborCostForEarnedValue'
}

expected_tables = 4 + 1 = 5
```

**SQLGlot Enhancement:**
```python
# SQLGlot successfully parsed INSERT statement
sqlglot_sources = {
    'dbo.DimProject',
    'dbo.DimDate',
    'dbo.FactLaborCost',
    'dbo.DimEmployee'
}

sqlglot_targets = {
    'dbo.FactLaborCostForEarnedValue'
}
```

**Combined (Union):**
```python
combined_sources = regex_sources ∪ sqlglot_sources
                 = {DimProject, DimDate, FactLaborCost, DimEmployee}

combined_targets = regex_targets ∪ sqlglot_targets
                 = {FactLaborCostForEarnedValue}

found_tables = 4 + 1 = 5
```

**Confidence:**
```python
completeness_pct = (5 / 5) * 100 = 100%
confidence = 100
```

---

## ✅ Summary

### How expected_tables is Calculated

```
1. Regex scan runs on ORIGINAL DDL (full text)
2. Extracts all FROM, JOIN, INSERT, UPDATE, DELETE, MERGE references
3. Filters out system schemas, temp tables, variables
4. Validates against catalog (creates phantoms if needed)
5. Counts validated sources + targets = expected_tables
```

### Formula

```
expected_tables = len(validated_sources) + len(validated_targets)

Where:
- validated_sources = Tables from FROM/JOIN clauses (after filtering)
- validated_targets = Tables from INSERT/UPDATE/DELETE/MERGE (after filtering)
- Both come from regex scan of ORIGINAL DDL
```

### Why This Works

```
✅ Comprehensive: Regex captures ALL table references
✅ Validated: Only real objects counted (phantoms tracked separately)
✅ Baseline: Provides expected count for confidence calculation
✅ Transparent: Simple count, no magic
```

---

**File:** `lineage_v3/parsers/quality_aware_parser.py`
**Key Methods:**
- `_regex_scan()` (lines 864-1045) - Extracts table references from original DDL
- `_post_process_dependencies()` (lines 558-646) - Filters and validates
- `_validate_against_catalog()` (lines 647-685) - Creates phantoms if needed

**Related:** See `SUCCESS_AND_CONFIDENCE_EXPLAINED.md` for how this relates to confidence calculation
