# Parser Issue: DECLARE Pattern Removes Business Logic

**Date**: 2025-11-02
**Severity**: HIGH
**Impact**: Affects stored procedures with DECLARE variables followed by business logic without semicolons
**Affected Version**: v3.7.0
**File**: `lineage_v3/parsers/quality_aware_parser.py`

---

## Executive Summary

A greedy regex pattern in the parser preprocessing stage is removing critical business logic (TRUNCATE, INSERT, SELECT statements) from stored procedures, causing them to show empty dependency arrays despite having clear table references. This affects the parsing quality and prevents achievement of the 95% high-confidence goal.

**Example Impact**: `spLoadPrimaReportingSiteEventsWithAllocations`
- **Expected**: 5 inputs, 1 output
- **Actual**: 0 inputs, 0 outputs
- **Confidence**: 0.5 (should be 0.85+)

---

## Root Cause Analysis

### The Problematic Pattern

**Location**: `lineage_v3/parsers/quality_aware_parser.py:119`

```python
ENHANCED_REMOVAL_PATTERNS = [
    # ... other patterns ...

    # Remove DECLARE statements (variable declarations clutter parsing)
    (r'\bDECLARE\s+@\w+\s+[^;]+;', '', 0),  # ← LINE 119: THE PROBLEM

    # ... other patterns ...
]
```

### Why It Fails

The pattern `\bDECLARE\s+@\w+\s+[^;]+;` is designed to remove variable declarations like:
```sql
DECLARE @StartDate DATETIME = GETDATE();
```

**However**, the `[^;]+` portion is **greedy** and matches ANY characters until it finds a semicolon.

In T-SQL:
- Semicolons are **optional** statement terminators
- Most statements don't end with semicolons
- Developers often write multiple statements without semicolons

**Result**: The pattern matches from the first `DECLARE` to the first semicolon it finds, which could be **thousands of characters later**, removing:
- All DECLARE statements
- BEGIN blocks
- SELECT INTO statements
- **TRUNCATE TABLE statements** (outputs)
- **INSERT INTO statements** (outputs)
- **FROM/JOIN clauses** (inputs)
- Column lists
- Everything until the first semicolon

---

## Detailed Example: spLoadPrimaReportingSiteEventsWithAllocations

### Original DDL Structure (11,649 chars)

```sql
CREATE PROC [CONSUMPTION_PRIMAREPORTING].[spLoadPrimaReportingSiteEventsWithAllocations] AS
BEGIN
    SET NOCOUNT ON

    DECLARE @serverName VARCHAR(100) = CAST(SERVERPROPERTY('ServerName') AS VARCHAR(100))
    DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_PRIMAREPORTING].[spLoadPrimaReportingSiteEventsWithAllocations]'
    DECLARE @procid VARCHAR(100) = (SELECT OBJECT_ID(@ProcName))

    -- No semicolons here!

    BEGIN TRY
        -- Temp table creation
        SELECT ... INTO #AllocatedMonitorUnblinded FROM CONSUMPTION_PRIMA.[SiteAllocations] ...

        -- More temp tables
        SELECT ... INTO #AllocatedMonitorBlinded FROM CONSUMPTION_PRIMA.[SiteAllocations] ...

        -- Business logic (THE IMPORTANT PART)
        TRUNCATE TABLE CONSUMPTION_PRIMAREPORTING.[SiteEventsWithAllocations]
        INSERT INTO CONSUMPTION_PRIMAREPORTING.[SiteEventsWithAllocations]
        SELECT
            [Project Code],
            [Project Name],
            [Country ID],
            [Country],
            [Site ID],
            ... (many columns)
        FROM CONSUMPTION_PRIMAREPORTING.SiteEvents s
        LEFT JOIN CONSUMPTION_PRIMA.HrEmployees mm ON ...
        -- First semicolon appears HERE after column list! ← 3,451 characters from first DECLARE
        ;

    END TRY
    BEGIN CATCH
        -- Error handling
    END CATCH
END
```

### What Gets Matched and Removed

**Match span**: Characters 24-3,475 (**3,451 characters**)

**What's removed**:
```sql
DECLARE @serverName VARCHAR(100) = CAST(SERVERPROPERTY('ServerName') AS VARCHAR(100))
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_PRIMAREPORTING].[spLoadPrimaReportingSiteEventsWithAllocations]'
DECLARE @procid VARCHAR(100) = (SELECT OBJECT_ID(@ProcName))

BEGIN TRY
    SELECT ... INTO #AllocatedMonitorUnblinded FROM CONSUMPTION_PRIMA.[SiteAllocations] ...
    SELECT ... INTO #AllocatedMonitorBlinded FROM CONSUMPTION_PRIMA.[SiteAllocations] ...

    TRUNCATE TABLE CONSUMPTION_PRIMAREPORTING.[SiteEventsWithAllocations]  ← OUTPUT DEPENDENCY!
    INSERT INTO CONSUMPTION_PRIMAREPORTING.[SiteEventsWithAllocations]      ← OUTPUT DEPENDENCY!
    SELECT
        [Project Code],
        [Project Name],
        ... (all columns)
    FROM CONSUMPTION_PRIMAREPORTING.SiteEvents s                            ← INPUT DEPENDENCY!
    LEFT JOIN CONSUMPTION_PRIMA.HrEmployees mm ON ...                       ← INPUT DEPENDENCY!
;  ← STOPS HERE (first semicolon found)
```

**What remains** (5,833 chars):
```sql
-- Only the middle of a subquery!
') from [PrimaStaging].[dbo].[SiteAllocations] sa WHERE sa.SITE_ID = s.[Site ID] and ...
-- Rest of CATCH block
-- Cleanup code
```

---

## Impact on Parser Flow

### Expected Flow (Working Correctly)

```
1. Regex Scan (Baseline)
   ├─ Sources: 5 tables ✓
   │   ├─ CONSUMPTION_PRIMAREPORTING.SiteEvents
   │   ├─ CONSUMPTION_PRIMA.SiteEvents
   │   ├─ CONSUMPTION_PRIMA.SiteAllocations
   │   ├─ CONSUMPTION_PRIMA.HrEmployees
   │   └─ CONSUMPTION_PRIMAREPORTING.SiteEventsWithAllocations (self-ref)
   └─ Targets: 1 table ✓
       └─ CONSUMPTION_PRIMAREPORTING.SiteEventsWithAllocations

2. Catalog Validation
   ├─ Sources: 5 tables ✓ (all exist in database)
   └─ Targets: 1 table ✓ (exists in database)

3. Resolve to Object IDs
   ├─ Input IDs: [827860661, 847336728, 2127341288, 987861231, 447335303] ✓
   └─ Output IDs: [827860661] ✓
```

### Actual Flow (Broken)

```
1. Regex Scan (Baseline)
   ├─ Sources: 5 tables ✓
   └─ Targets: 1 table ✓

2. Catalog Validation
   ├─ Sources: 5 tables ✓
   └─ Targets: 1 table ✓

3. DDL Preprocessing
   ├─ Remove CREATE PROC header ✓
   ├─ Remove control flow (BEGIN TRY → BEGIN /* TRY */) ✓
   ├─ Remove CATCH blocks ✓
   ├─ Remove EXEC statements ✓
   ├─ Remove DECLARE statements... ✗ REMOVES 3,451 CHARS INCLUDING BUSINESS LOGIC!
   └─ Result: Broken DDL fragment starting mid-subquery

4. SQLGlot Parse (on broken DDL)
   ├─ Sources: 1 table (PrimaStaging.dbo - wrong! 3-part name from fragment)
   │   └─ After validation: 0 tables ✗ (doesn't exist in catalog)
   └─ Targets: 0 tables ✗ (TRUNCATE and INSERT were removed)

5. Quality Check
   ├─ Regex baseline: 5 sources, 1 target
   ├─ Parser result: 0 sources, 0 targets
   ├─ Overall match: 0.00 (0% agreement)
   └─ Confidence: 0.5 (low - needs AI)

6. Object ID Resolution
   ⚠️  CRITICAL: Uses parser_sources_valid (SQLGlot), NOT regex_sources_valid
   ├─ Input IDs: [] ✗ (empty - parser found nothing)
   └─ Output IDs: [] ✗ (empty - parser found nothing)

7. AI Disambiguation Check
   ├─ Confidence 0.5 ≤ 0.85? ✓ (should trigger)
   ├─ AI enabled? ✓
   ├─ AI available? ✓
   ├─ Extract ambiguous references...
   │   └─ Found: 0 ✗ (all table names are fully-qualified)
   └─ AI skipped (no ambiguous references to disambiguate)

8. Final Result Stored
   ├─ object_id: 760609673
   ├─ inputs: [] ✗ WRONG!
   ├─ outputs: [] ✗ WRONG!
   ├─ confidence: 0.5
   └─ primary_source: 'parser'
```

---

## Why AI Didn't Save This

The AI disambiguator (added in v3.7.0) is designed to handle **ambiguous table references** - unqualified table names that could refer to multiple schemas:

**Example of what AI can fix**:
```sql
-- Ambiguous: Could be dbo.Customers, Sales.Customers, or Archive.Customers
SELECT * FROM Customers
```

**This SP's situation**:
```sql
-- Not ambiguous - fully qualified
SELECT * FROM CONSUMPTION_PRIMAREPORTING.SiteEvents
```

**AI trigger requirements**:
1. ✓ Low confidence (0.5 ≤ 0.85 threshold)
2. ✓ AI enabled and has credentials
3. ✗ **Needs ambiguous references** - none found!

**AI's `_extract_ambiguous_references()` looks for**:
- Unqualified table names (`FROM TableName` not `FROM schema.TableName`)
- Multiple candidates in the catalog with same name but different schemas

**This SP has**:
- Fully-qualified names: `CONSUMPTION_PRIMA.SiteAllocations`
- No ambiguity to resolve
- Problem is preprocessing, not disambiguation

**Result**: AI never runs, even though confidence is 0.5.

---

## Design Flaws Identified

### 1. No Fallback to Regex Results

**Current behavior**:
```python
# Line 199-200 in quality_aware_parser.py
input_ids = self._resolve_table_names(parser_sources_valid)   # Always uses SQLGlot
output_ids = self._resolve_table_names(parser_targets_valid)  # Never falls back to regex
```

**Why this is wrong**:
- Regex is used as quality baseline (compares counts)
- But regex results are **discarded** even when SQLGlot fails
- If SQLGlot finds 0 but regex finds 5, should use regex as fallback

**Quality check shows the problem**:
```
Regex: 5 sources, 1 target
Parser: 0 sources, 0 targets
Overall match: 0.00 (complete failure)
→ Still uses parser (empty) results!
```

### 2. AI Only Handles Disambiguation, Not Parse Failures

**AI is designed for**:
- Schema disambiguation (`Customers` → `Sales.Customers` vs `dbo.Customers`)
- Resolving ambiguous unqualified references
- Uses Azure OpenAI with catalog context

**AI cannot handle**:
- Preprocessing that removes business logic
- SQLGlot parse failures
- Cases where DDL is malformed/truncated

**This SP needs**:
- Fixed preprocessing (don't remove business logic)
- OR fallback to regex results
- NOT AI disambiguation (no ambiguous names)

### 3. Regex Pattern Doesn't Account for Optional Semicolons

**The pattern**: `\bDECLARE\s+@\w+\s+[^;]+;`

**Assumptions**:
- Each DECLARE statement ends with semicolon
- Variables are declared in isolation

**T-SQL reality**:
- Semicolons are optional
- Developers rarely use semicolons
- First semicolon might be hundreds/thousands of chars away
- Business logic sits between DECLARE and first semicolon

**Why `[^;]+` is dangerous**:
- `[^;]` = match any character except semicolon
- `+` = greedy (match as much as possible)
- Result: matches everything until first semicolon

---

## Scope of Impact

### How Many SPs Are Affected?

**Characteristics of affected SPs**:
1. Have DECLARE variable statements
2. Don't use semicolons after DECLARE
3. Have business logic (TRUNCATE/INSERT/SELECT) before first semicolon
4. Use fully-qualified table names (so AI doesn't help)

**To find affected SPs**:
```sql
-- Query workspace to find low-confidence SPs with this pattern
SELECT
    o.schema_name,
    o.object_name,
    lm.confidence,
    lm.primary_source,
    json_array_length(lm.inputs) as input_count,
    json_array_length(lm.outputs) as output_count
FROM objects o
JOIN lineage_metadata lm ON o.object_id = lm.object_id
WHERE o.object_type = 'Stored Procedure'
  AND lm.confidence < 0.85
  AND lm.primary_source = 'parser'
  AND json_array_length(lm.inputs) = 0
  AND json_array_length(lm.outputs) = 0
ORDER BY o.object_name;
```

**Expected impact**:
- Current stats: 163/202 SPs at ≥0.85 confidence (80.7%)
- Target: 95% high-confidence
- This bug likely affects 10-20% of low-confidence SPs

---

## Proposed Solutions

### Option 1: Fix DECLARE Pattern (Recommended)

**Change the pattern to be less greedy**:

**Current** (line 119):
```python
(r'\bDECLARE\s+@\w+\s+[^;]+;', '', 0),
```

**Proposed**:
```python
# Match DECLARE statements more carefully
# Stop at newline followed by non-whitespace keyword (TRUNCATE, INSERT, SELECT, etc.)
(r'\bDECLARE\s+@\w+\s+[^\n]+(?:\n\s*DECLARE\s+@\w+\s+[^\n]+)*', '', 0),
```

**Better approach - Match single-line DECLARE only**:
```python
# Only match DECLARE on a single line (stops at newline)
(r'\bDECLARE\s+@\w+[^\n]*\n', '\n', 0),
```

**Even better - Don't remove DECLARE at all**:
```python
# Comment them out instead of removing (preserves structure)
(r'\bDECLARE\s+@\w+[^\n]*', '-- DECLARE removed', 0),
```

**Test cases to validate**:
1. Single DECLARE with semicolon: `DECLARE @x INT = 1;`
2. Multiple DECLAREs without semicolons
3. DECLARE followed by SELECT INTO
4. DECLARE followed by TRUNCATE/INSERT

### Option 2: Add Fallback to Regex Results

**When to use fallback**:
- SQLGlot finds 0 dependencies
- Regex found >0 dependencies
- Quality check shows complete failure (match < 0.5)

**Implementation** (add after line 200):
```python
# STEP 5: Resolve to object_ids
input_ids = self._resolve_table_names(parser_sources_valid)
output_ids = self._resolve_table_names(parser_targets_valid)

# FALLBACK: If parser found nothing but regex found dependencies, use regex
if (not input_ids and not output_ids) and (regex_sources_valid or regex_targets_valid):
    logger.warning(f"Parser found no dependencies but regex found {len(regex_sources_valid)} sources "
                   f"and {len(regex_targets_valid)} targets. Falling back to regex results.")
    input_ids = self._resolve_table_names(regex_sources_valid)
    output_ids = self._resolve_table_names(regex_targets_valid)
    confidence = 0.75  # Medium confidence (regex-based)
```

**Pros**:
- Immediate fix for affected SPs
- Regex results are already validated against catalog
- Better than empty arrays

**Cons**:
- Doesn't fix root cause (preprocessing bug)
- Regex might have false positives
- Bypasses SQLGlot quality check

### Option 3: Hybrid Approach (Best)

**Combine both solutions**:

1. **Fix the DECLARE pattern** (long-term fix)
   - Prevents removing business logic
   - Improves SQLGlot parse success rate

2. **Add regex fallback** (safety net)
   - Handles edge cases
   - Prevents empty results when regex succeeded

**Benefits**:
- Fixes root cause (pattern)
- Safety net for other preprocessing failures
- Incremental improvement path

---

## Testing Strategy

### Regression Testing (MANDATORY)

**Before making changes**:
```bash
# 1. Create baseline
/sub_DL_OptimizeParsing init --name baseline_before_declare_fix

# 2. Capture affected SPs
python3 << 'EOF'
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

with DuckDBWorkspace("data/lineage_workspace.duckdb") as db:
    result = db.connection.execute("""
        SELECT o.object_name, lm.confidence,
               json_array_length(lm.inputs) as inputs,
               json_array_length(lm.outputs) as outputs
        FROM objects o
        JOIN lineage_metadata lm ON o.object_id = lm.object_id
        WHERE o.object_type = 'Stored Procedure'
          AND lm.confidence < 0.85
        ORDER BY lm.confidence, o.object_name
    """).fetchall()

    with open('affected_sps_before.txt', 'w') as f:
        for row in result:
            f.write(f"{row[0]}: conf={row[1]:.2f}, in={row[2]}, out={row[3]}\n")
EOF
```

**After making changes**:
```bash
# 1. Full refresh parse
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# 2. Run evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_before_declare_fix

# 3. Check specific test case
python3 << 'EOF'
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

with DuckDBWorkspace("data/lineage_workspace.duckdb") as db:
    result = db.connection.execute("""
        SELECT
            lm.confidence,
            json_array_length(lm.inputs) as inputs,
            json_array_length(lm.outputs) as outputs,
            lm.primary_source
        FROM objects o
        JOIN lineage_metadata lm ON o.object_id = lm.object_id
        WHERE o.object_name = 'spLoadPrimaReportingSiteEventsWithAllocations'
    """).fetchone()

    print(f"Confidence: {result[0]:.2f} (expected: ≥0.85)")
    print(f"Inputs: {result[1]} (expected: 5)")
    print(f"Outputs: {result[2]} (expected: 1)")
    print(f"Source: {result[3]} (expected: 'parser' or 'ai')")

    # Assertions
    assert result[0] >= 0.75, f"Confidence too low: {result[0]}"
    assert result[1] > 0, "No inputs found"
    assert result[2] > 0, "No outputs found"
    print("\n✓ All checks passed!")
EOF
```

### Unit Tests

**Test the DECLARE pattern specifically**:

```python
# tests/test_declare_pattern.py
import pytest
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

def test_declare_pattern_single_line():
    """Test DECLARE with semicolon on same line"""
    ddl = "DECLARE @x INT = 1;"
    # Should remove or comment out

def test_declare_pattern_multiple_lines():
    """Test multiple DECLARE without semicolons"""
    ddl = """
    DECLARE @x INT = 1
    DECLARE @y VARCHAR(100) = 'test'
    TRUNCATE TABLE dbo.Target
    """
    # Should NOT remove TRUNCATE

def test_declare_pattern_with_business_logic():
    """Test DECLARE followed by business logic (the bug case)"""
    ddl = """
    DECLARE @x INT = 1
    DECLARE @y VARCHAR(100) = 'test'

    TRUNCATE TABLE dbo.Target
    INSERT INTO dbo.Target
    SELECT * FROM dbo.Source;
    """
    # Should preserve TRUNCATE and INSERT

def test_preprocessing_preserves_dependencies():
    """Integration test: Full preprocessing should preserve table refs"""
    ddl = """
    CREATE PROC dbo.TestProc AS
    BEGIN
        DECLARE @x INT = 1
        TRUNCATE TABLE dbo.Target
        INSERT INTO dbo.Target SELECT * FROM dbo.Source;
    END
    """

    parser = QualityAwareParser(workspace)
    cleaned = parser._preprocess_ddl(ddl)

    # Assertions
    assert 'TRUNCATE' in cleaned, "TRUNCATE was removed"
    assert 'INSERT' in cleaned, "INSERT was removed"
    assert 'Source' in cleaned, "Source table reference removed"
```

---

## Success Criteria

### Before Fix

```
spLoadPrimaReportingSiteEventsWithAllocations:
  ✗ Confidence: 0.50
  ✗ Inputs: 0 (expected: 5)
  ✗ Outputs: 0 (expected: 1)
  ✗ Primary source: parser
  ✗ Quality match: 0.00 (regex: 5/1, parser: 0/0)
```

### After Fix (Minimum)

```
spLoadPrimaReportingSiteEventsWithAllocations:
  ✓ Confidence: ≥0.75
  ✓ Inputs: ≥4 (allows for some variance)
  ✓ Outputs: ≥1
  ✓ Primary source: parser or ai
  ✓ Quality match: ≥0.75
```

### After Fix (Ideal)

```
spLoadPrimaReportingSiteEventsWithAllocations:
  ✓ Confidence: ≥0.85
  ✓ Inputs: 5
  ✓ Outputs: 1
  ✓ Primary source: parser
  ✓ Quality match: ≥0.90 (regex and parser agree)
```

### Overall Metrics

**Current** (v3.7.0):
- High confidence (≥0.85): 163/202 = 80.7%
- Average confidence: 0.800

**Target after fix**:
- High confidence: ≥170/202 = 84%+ (expect 5-10 SPs to improve)
- Average confidence: ≥0.820

**Long-term goal**: 95% high-confidence (192/202)

---

## Implementation Checklist

- [ ] Create baseline: `/sub_DL_OptimizeParsing init --name baseline_before_declare_fix`
- [ ] Capture affected SPs list (`confidence < 0.85`, `inputs=0`, `outputs=0`)
- [ ] Implement fix (Option 1, 2, or 3)
- [ ] Write unit tests for DECLARE pattern
- [ ] Run full parser refresh
- [ ] Verify test case: `spLoadPrimaReportingSiteEventsWithAllocations`
- [ ] Run evaluation: `/sub_DL_OptimizeParsing run --mode full`
- [ ] Compare before/after metrics
- [ ] Check for regressions (no high-confidence SPs should drop)
- [ ] Update `docs/PARSER_EVOLUTION_LOG.md`
- [ ] Commit with message: "fix(parser): Prevent DECLARE pattern from removing business logic"

---

## Related Files

- **Parser**: `lineage_v3/parsers/quality_aware_parser.py`
  - Line 119: DECLARE pattern (root cause)
  - Lines 199-200: Object ID resolution (no fallback)
  - Lines 212-265: AI disambiguation logic

- **Evolution Log**: `docs/PARSER_EVOLUTION_LOG.md`
  - Add entry for this fix

- **Workspace**: `lineage_v3/core/duckdb_workspace.py`
  - Line 557: `update_metadata()` method (stores results)

- **Main Flow**: `lineage_v3/main.py`
  - Line 322: Calls `update_metadata()` with parser results

---

## Questions for Discussion

1. **Which solution do you prefer?**
   - Option 1: Fix DECLARE pattern only
   - Option 2: Add regex fallback only
   - Option 3: Both (hybrid)

2. **Should we remove DECLARE or comment it out?**
   - Remove: `(r'\bDECLARE...', '', 0)` (current)
   - Comment: `(r'\bDECLARE...', '-- DECLARE', 0)` (safer)

3. **Should regex fallback boost or maintain confidence?**
   - Boost to 0.75 (medium confidence)
   - Keep at 0.50 (low confidence, flag for review)

4. **How aggressive should we be with preprocessing cleanup?**
   - Current approach: Remove everything not needed for lineage
   - Conservative approach: Only remove comments and formatting

---

**Document Version**: 1.0
**Last Updated**: 2025-11-02
**Next Review**: After fix implementation
