# Comment Hints Parser - Developer Guide

**Version:** 4.2.0
**Date:** 2025-11-06
**Status:** Production

---

## Overview

The Comment Hints Parser allows developers to explicitly document table dependencies in stored procedures using special comment syntax. This solves parsing limitations for edge cases like dynamic SQL, complex CATCH blocks, and conditional logic where static analysis fails.

**Key Features:**
- Parse `@LINEAGE_INPUTS` and `@LINEAGE_OUTPUTS` from SQL comments
- Validate hints against database catalog
- UNION hints with parser results (no duplicates)
- Apply confidence boost (+0.10) when hints are present
- Seamless integration with existing quality_aware_parser.py

---

## Architecture

### Components

1. **CommentHintsParser** (`lineage_v3/parsers/comment_hints_parser.py`)
   - Standalone parser for extracting hints from SQL comments
   - Regex-based extraction with validation support
   - Catalog-aware validation (optional)

2. **Integration Layer** (`lineage_v3/parsers/quality_aware_parser.py`)
   - STEP 2b: Extract hints from original DDL
   - UNION hints with SQLGlot results
   - Apply confidence boost if hints present
   - Include hint stats in quality_check output

3. **User Documentation** (`docs/PARSING_USER_GUIDE.md`)
   - End-user facing documentation
   - Syntax examples and best practices
   - When/how to use hints

---

## Implementation Details

### Extraction Flow

```
Input: SQL DDL
    ↓
1. Regex Scan (find hint comments)
    ↓
2. Parse Table Names (comma-separated)
    ↓
3. Normalize Format (schema.table)
    ↓
4. Validate Against Catalog (optional)
    ↓
5. Return Sets (inputs, outputs)
```

### Regex Patterns

**Input Hints:**
```python
INPUT_PATTERN = r'--\s*@LINEAGE_INPUTS:\s*(.+?)(?:\n|$)'
```

**Output Hints:**
```python
OUTPUT_PATTERN = r'--\s*@LINEAGE_OUTPUTS:\s*(.+?)(?:\n|$)'
```

**Features:**
- Case-insensitive matching (`re.IGNORECASE`)
- Multi-line support (`re.MULTILINE`)
- Captures content after colon until end of line
- Handles optional whitespace

### Table Name Normalization

**Supported Formats:**
- `schema.table` → `schema.table`
- `[schema].[table]` → `schema.table`
- `[schema].table` → `schema.table`
- `schema.[table]` → `schema.table`
- `table` → `dbo.table` (default schema)

**Logic:**
```python
def _normalize_table_name(self, table_str: str) -> str:
    parts = table_str.replace('[', '').replace(']', '').split('.')

    if len(parts) == 2:
        return f"{parts[0].strip()}.{parts[1].strip()}"
    elif len(parts) == 1:
        return f"dbo.{parts[0].strip()}"  # Default to dbo
    else:
        return ""  # Invalid format
```

### Catalog Validation

**Purpose:** Ensure hinted tables actually exist in the database

**Process:**
1. Build catalog cache from `objects` table (first call only)
2. Case-insensitive lookup
3. Return only valid tables
4. Log warnings for invalid tables

**Cache Structure:**
```python
self._catalog_cache = {
    'dbo.customers': 'dbo.Customers',  # lowercase key → original case value
    'finance.accounts': 'FINANCE.Accounts',
    ...
}
```

**Performance:**
- Cache built once per parser instance
- O(1) lookup per table
- Case-insensitive matching without repeated queries

---

## Integration with QualityAwareParser

### Modified Workflow

**Before (v4.1.3):**
```
STEP 1: Regex baseline
STEP 2: SQLGlot parse
STEP 3: Quality calculation
STEP 4: Confidence determination
STEP 5: Resolve to object_ids
```

**After (v4.2.0):**
```
STEP 1: Regex baseline
STEP 2: SQLGlot parse
STEP 2b: Extract comment hints ← NEW
STEP 3: Quality calculation (with hints)
STEP 4: Confidence determination (with boost)
STEP 5: Resolve to object_ids (with hints)
```

### Code Integration Points

**1. Import Statement:**
```python
from lineage_v3.parsers.comment_hints_parser import CommentHintsParser
```

**2. Initialize in __init__:**
```python
def __init__(self, workspace: DuckDBWorkspace):
    self.workspace = workspace
    self._object_catalog = None
    self.hints_parser = CommentHintsParser(workspace)  # NEW
```

**3. Extract Hints (STEP 2b):**
```python
# STEP 2b: Extract comment hints (v4.2.0)
hint_inputs, hint_outputs = self.hints_parser.extract_hints(ddl, validate=True)

# Log extraction
if hint_inputs or hint_outputs:
    logger.info(f"Comment hints found: {len(hint_inputs)} inputs, {len(hint_outputs)} outputs")

# UNION with parser results
parser_sources_with_hints = parser_sources_valid | hint_inputs
parser_targets_with_hints = parser_targets_valid | hint_outputs
```

**4. Update Quality Calculation:**
```python
# Use results WITH hints
quality = self._calculate_quality(
    len(regex_sources_valid),
    len(regex_targets_valid),
    len(parser_sources_with_hints),  # Changed
    len(parser_targets_with_hints)    # Changed
)
```

**5. Apply Confidence Boost:**
```python
has_hints = bool(hint_inputs or hint_outputs)
confidence = self._determine_confidence(
    quality,
    regex_sources_count=len(regex_sources_valid),
    regex_targets_count=len(regex_targets_valid),
    sp_calls_count=len(regex_sp_calls_valid),
    has_hints=has_hints  # NEW parameter
)
```

**6. Update _determine_confidence Method:**
```python
def _determine_confidence(self, quality, ..., has_hints: bool = False):
    base_confidence = ConfidenceCalculator.from_quality_match(...)

    # Apply hint boost (v4.2.0)
    if has_hints:
        boosted_confidence = min(base_confidence + 0.10, 0.95)
        logger.debug(f"Confidence boost: {base_confidence:.2f} → {boosted_confidence:.2f}")
        return boosted_confidence

    return base_confidence
```

**7. Update Return Value:**
```python
return {
    'object_id': object_id,
    'inputs': input_ids,  # Uses parser_sources_with_hints
    'outputs': output_ids,  # Uses parser_targets_with_hints
    'confidence': confidence,  # Includes boost
    'source': 'parser_with_hints' if has_hints else 'parser',  # NEW
    'quality_check': {
        'hint_inputs': len(hint_inputs),  # NEW
        'hint_outputs': len(hint_outputs),  # NEW
        'final_sources': len(parser_sources_with_hints),  # NEW
        'final_targets': len(parser_targets_with_hints),  # NEW
        ...
    }
}
```

---

## Confidence Boost Logic

### Formula

**Without Hints:**
```
confidence = base_confidence  # 0.50, 0.75, or 0.85
```

**With Hints:**
```
confidence = min(base_confidence + 0.10, 0.95)  # Max 0.95
```

### Examples

| Base Confidence | Has Hints | Final Confidence | Explanation |
|-----------------|-----------|------------------|-------------|
| 0.50 | No | 0.50 | Low confidence (parser disagreement) |
| 0.50 | Yes | 0.60 | Hints provide missing dependencies |
| 0.75 | No | 0.75 | Medium confidence (partial agreement) |
| 0.75 | Yes | 0.85 | Hints complete gaps → high confidence |
| 0.85 | No | 0.85 | High confidence (parser agreement) |
| 0.85 | Yes | 0.95 | Hints validate parser → very high |

### Rationale

**Why +0.10?**
- Hints indicate developer intervention for known edge cases
- Provides meaningful boost without over-confidence
- Distinguishes developer-validated SPs from automated parses

**Why cap at 0.95?**
- Only DMV metadata gets 1.0 (ground truth from SQL Server)
- Parsed results always have some uncertainty
- 0.95 = highest achievable for parsed SPs

---

## Testing

### Unit Tests

**Location:** `tests/test_comment_hints_parser.py`

**Coverage:**
- Basic hint extraction (inputs, outputs, both)
- Table name formats (brackets, no schema, mixed)
- Multiple hint comments (UNION behavior)
- CATCH block hints
- Conditional logic hints
- Dynamic SQL hints
- No hints present
- Invalid formats (graceful handling)
- Case insensitivity
- Statistics calculation

**Run Tests:**
```bash
# With pytest (if available)
pytest tests/test_comment_hints_parser.py -v

# Standalone (no dependencies)
python temp/test_hints_standalone.py
```

### Integration Tests

**Manual Test Workflow:**
1. Create test SP with hints:
```sql
CREATE PROC dbo.spTestHints
AS
BEGIN
    -- @LINEAGE_INPUTS: dbo.TestSource
    -- @LINEAGE_OUTPUTS: dbo.TestTarget

    DECLARE @sql NVARCHAR(MAX);
    SET @sql = 'INSERT INTO dbo.TestTarget SELECT * FROM dbo.TestSource';
    EXEC sp_executesql @sql;
END
```

2. Run parser:
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/
```

3. Check results:
```python
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

workspace = DuckDBWorkspace("lineage_workspace.duckdb", read_only=True)

# Check confidence boost
result = workspace.conn.execute("""
    SELECT
        o.schema_name || '.' || o.object_name AS sp_name,
        m.confidence,
        m.primary_source
    FROM lineage_metadata m
    JOIN objects o ON m.object_id = o.object_id
    WHERE o.object_name = 'spTestHints'
""").fetchone()

print(f"SP: {result[0]}")
print(f"Confidence: {result[1]}")  # Should be 0.60 (0.50 + 0.10)
print(f"Source: {result[2]}")  # Should be "parser_with_hints"
```

4. Verify lineage:
```python
# Check that hinted tables appear in lineage
inputs = workspace.conn.execute("""
    SELECT DISTINCT o.object_name
    FROM dependencies d
    JOIN objects o ON d.input_object_id = o.object_id
    WHERE d.object_id = (SELECT object_id FROM objects WHERE object_name = 'spTestHints')
""").fetchall()

outputs = workspace.conn.execute("""
    SELECT DISTINCT o.object_name
    FROM dependencies d
    JOIN objects o ON d.output_object_id = o.object_id
    WHERE d.object_id = (SELECT object_id FROM objects WHERE object_name = 'spTestHints')
""").fetchall()

print(f"Inputs: {[r[0] for r in inputs]}")  # Should include TestSource
print(f"Outputs: {[r[0] for r in outputs]}")  # Should include TestTarget
```

---

## UAT Feedback Integration

### Workflow

When UAT user reports missing dependency:

**1. User Reports Issue:**
```bash
cd temp/uat_feedback
python capture_feedback.py \
    --sp "dbo.spProblemProc" \
    --issue missing_input \
    --missing "dbo.MissingTable" \
    --notes "Table accessed in dynamic SQL" \
    --reporter "user@company.com"
```

**2. Developer Adds Hint:**
```sql
ALTER PROC dbo.spProblemProc
AS
BEGIN
    -- @LINEAGE_INPUTS: dbo.MissingTable
    -- Reason: Dynamic SQL - reported via UAT feedback UAT_20251106_082812

    DECLARE @sql NVARCHAR(MAX);
    SET @sql = 'SELECT * FROM dbo.MissingTable';
    EXEC sp_executesql @sql;
END
```

**3. Re-run Parser:**
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/
```

**4. Verify Fix:**
- Confidence improved (0.50 → 0.60)
- Missing table now in lineage
- `primary_source` = "parser_with_hints"

**5. Update UAT Feedback:**
```bash
# Mark issue as fixed
cd temp/uat_feedback
# Edit reports/UAT_20251106_082812.json:
# "status": "fixed"
# "resolution": "Added comment hint for dynamic SQL table"
```

---

## Troubleshooting

### Issue: Hints Not Extracted

**Symptoms:**
- Hints in SP but not reflected in lineage
- Confidence not boosted
- `primary_source` = "parser" (not "parser_with_hints")

**Debug Steps:**

1. **Check Hint Syntax:**
```sql
-- ✅ CORRECT
-- @LINEAGE_INPUTS: dbo.Table1

-- ❌ WRONG (missing colon)
-- @LINEAGE_INPUTS dbo.Table1

-- ❌ WRONG (typo in keyword)
-- @LINEAGE_INPUT: dbo.Table1
```

2. **Check Parser Logs:**
```bash
# Enable debug logging
python lineage_v3/main.py run --parquet parquet_snapshots/ --log-level DEBUG

# Look for:
# "Comment hints found: X inputs, Y outputs"
# "Confidence boost from hints: 0.50 → 0.60"
```

3. **Verify Catalog Validation:**
```python
from lineage_v3.parsers.comment_hints_parser import CommentHintsParser
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

workspace = DuckDBWorkspace("lineage_workspace.duckdb", read_only=True)
parser = CommentHintsParser(workspace)

# Test hint extraction
ddl = "-- @LINEAGE_INPUTS: dbo.MissingTable"
inputs, outputs = parser.extract_hints(ddl, validate=True)

print(f"Extracted: {inputs}")
# If empty, table not in catalog (check spelling, schema)
```

### Issue: Wrong Tables Extracted

**Symptoms:**
- Hints extracted but wrong table names
- Invalid tables in lineage

**Debug Steps:**

1. **Check Table Name Format:**
```sql
-- ✅ CORRECT
-- @LINEAGE_INPUTS: FINANCE.Accounts, dbo.Customers

-- ❌ WRONG (3-part names not supported)
-- @LINEAGE_INPUTS: MyDB.dbo.Customers
```

2. **Verify Case Sensitivity:**
```python
# Catalog lookup is case-insensitive, but returns original case
# Hint: dbo.customers → Catalog: dbo.Customers (OK)
```

3. **Check for Typos:**
```python
# Run validation separately
parser = CommentHintsParser(workspace)
stats = parser.get_hint_stats(ddl)

print(f"Total hints: {stats['total_hints']}")
print(f"Valid hints: {stats['valid_hints']}")
print(f"Invalid hints: {stats['invalid_hints']}")  # Should be 0

# Check logs for warnings:
# "Invalid input hints (not in catalog): {'dbo.NonExistentTable'}"
```

### Issue: Confidence Not Boosted

**Symptoms:**
- Hints extracted successfully
- But confidence remains 0.50 (no boost)

**Debug:**

1. **Check has_hints Flag:**
```python
# In quality_aware_parser.py parse_object()
# Should see:
has_hints = bool(hint_inputs or hint_outputs)  # Should be True
```

2. **Check _determine_confidence:**
```python
# Should enter this block:
if has_hints:
    boosted_confidence = min(base_confidence + 0.10, 0.95)
    # Should see debug log:
    # "Confidence boost from hints: 0.50 → 0.60"
```

3. **Verify Return Value:**
```python
# Check quality_check in result:
'quality_check': {
    'hint_inputs': 1,  # Should be > 0
    'hint_outputs': 1,  # Should be > 0
    ...
}
```

---

## Performance Considerations

### Extraction Performance

**Complexity:**
- Regex scan: O(n) where n = DDL length
- Table normalization: O(m) where m = number of hints
- Catalog validation: O(1) per table (cached lookup)

**Typical Performance:**
- 100 KB DDL: <10ms extraction
- 10 hints: <1ms validation
- Negligible impact on overall parse time

### Catalog Cache

**Built Once Per Parser Instance:**
```python
# First call: builds cache (~50-100ms for 1000 objects)
hints_parser.extract_hints(ddl1, validate=True)

# Subsequent calls: use cache (~1ms)
hints_parser.extract_hints(ddl2, validate=True)
hints_parser.extract_hints(ddl3, validate=True)
```

**Cache Invalidation:**
- Cache tied to parser instance
- New parser instance = rebuild cache
- For production: cache persists for all SPs in batch

### Optimization Tips

1. **Reuse Parser Instance:**
```python
# ✅ GOOD (cache reused)
parser = CommentHintsParser(workspace)
for sp in stored_procedures:
    parser.extract_hints(sp.ddl, validate=True)

# ❌ BAD (cache rebuilt every time)
for sp in stored_procedures:
    parser = CommentHintsParser(workspace)  # Don't do this!
    parser.extract_hints(sp.ddl, validate=True)
```

2. **Skip Validation When Unnecessary:**
```python
# If you don't need catalog validation:
parser.extract_hints(ddl, validate=False)  # Faster, no catalog query
```

---

## Future Enhancements

### Potential Improvements

1. **Multi-word Comments:**
```sql
-- @LINEAGE_INPUTS:
--   dbo.Table1  -- Customer data
--   dbo.Table2  -- Order data
```

2. **Inline Hints:**
```sql
SELECT * FROM dbo.Customers  -- @LINEAGE_INPUT: dbo.Customers
```

3. **Conditional Hints:**
```sql
-- @LINEAGE_INPUTS: dbo.Table1 IF @mode = 'full'
-- @LINEAGE_INPUTS: dbo.Table2 IF @mode = 'delta'
```

4. **Dependency Reasons:**
```sql
-- @LINEAGE_INPUTS: dbo.Table1 (REASON: Dynamic SQL in loop)
```

### Backward Compatibility

**Versioning:**
- Hints introduced in v4.2.0
- Old parser versions ignore hints (comments are no-op)
- Forward compatible: Future parsers can enhance syntax

**Migration Path:**
- No action required for existing SPs
- Add hints incrementally as UAT issues reported
- Monitor confidence improvements over time

---

## References

### Related Documentation

- **User Guide:** `docs/PARSING_USER_GUIDE.md` - End-user documentation
- **UAT Feedback:** `temp/uat_feedback/README.md` - Bug reporting system
- **Parsing Review:** `PARSING_REVIEW_STATUS.md` - Architecture analysis

### Code Locations

- **Parser:** `lineage_v3/parsers/comment_hints_parser.py`
- **Integration:** `lineage_v3/parsers/quality_aware_parser.py`
- **Tests:** `tests/test_comment_hints_parser.py`

### Version History

- **v4.2.0 (2025-11-06):** Initial release
  - Basic hint extraction (INPUT/OUTPUT)
  - Catalog validation
  - Confidence boost (+0.10)
  - Integration with quality_aware_parser

---

**Questions or Issues?** Contact the Vibecoding team or file a UAT feedback report.
