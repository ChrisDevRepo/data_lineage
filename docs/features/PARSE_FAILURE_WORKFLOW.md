# Parse Failure Workflow - User Guidance Feature

**Status:** Implemented

---

## Overview

Provides **actionable feedback** to users when stored procedure parsing fails, with clear explanations of WHY parsing failed and HOW to fix it using comment hints.

### Problem Solved

**Before v4.2.0:**
```json
{
  "confidence": 0.0,
  "description": "Confidence: 0.00"  // ❌ User has NO IDEA why or how to fix!
}
```

**After v4.2.0:**
```json
{
  "confidence": 0.0,
  "description": "❌ Parse Failed: 0.00 | Dynamic SQL: sp_executesql @variable - table names unknown at parse time | Expected 8 tables, found 1 (7 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints"
}
```

---

## Architecture

### 1. Detection Layer (`quality_aware_parser.py`)

New method: `_detect_parse_failure_reason()`

**Detected Patterns:**
1. **Dynamic SQL** - `EXEC(@var)`, `sp_executesql`
2. **WHILE loops** - Iterative processing
3. **CURSOR** - Row-by-row processing
4. **Deep nesting** - 5+ BEGIN/END blocks
5. **Complex CASE** - 10+ CASE statements
6. **Multiple CTEs** - 10+ WITH clauses

**Output:**
```python
{
    'parse_failure_reason': "Dynamic SQL: sp_executesql @variable... → Add @LINEAGE hints",
    'expected_count': 8,    # From smoke test
    'found_count': 1        # Parser extracted
}
```

### 2. Formatting Layer (`frontend_formatter.py`)

New method: `_format_sp_description()`

**Generates User-Friendly Descriptions:**

| Confidence | Description Format |
|------------|-------------------|
| **≥ 0.85** | `✅ High Confidence: 0.95` |
| **0.65-0.84** | `⚠️ Medium Confidence: 0.75 \| Manual hints used` |
| **0.01-0.64** | `⚠️ Low Confidence: 0.50 \| Dynamic SQL → Add @LINEAGE hints` |
| **0.00** | `❌ Parse Failed: 0.00 \| WHILE loop \| Expected 8, found 0 → Add hints` |

---

## Complete Workflow

### Step 1: Parser Detects Failure

```python
# quality_aware_parser.py (lines 376-390)

expected_count = len(regex_sources_valid) + len(regex_targets_valid)
found_count = len(input_ids) + len(output_ids) - len(sp_ids)

if confidence < 0.65:
    parse_failure_reason = self._detect_parse_failure_reason(
        ddl=ddl,
        parse_error=None,
        expected_count=expected_count,
        found_count=found_count
    )
```

### Step 2: Store in lineage_metadata

```json
{
  "object_id": 8606994,
  "confidence": 0.0,
  "parse_failure_reason": "Dynamic SQL: sp_executesql @variable - table names unknown at parse time | Expected 8 tables, found 1 (7 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints",
  "expected_count": 8,
  "found_count": 1
}
```

### Step 3: Frontend Formats Description

```python
# frontend_formatter.py (lines 225-294)

description = self._format_sp_description(
    confidence=0.0,
    parse_failure_reason=parse_failure_reason,
    expected_count=8,
    found_count=1,
    source='parser',
    confidence_breakdown=None
)
```

### Step 4: Frontend Displays

```json
{
  "id": "8606994",
  "name": "spLoadProjectRegions",
  "description": "❌ Parse Failed: 0.00 | Dynamic SQL: sp_executesql @variable - table names unknown at parse time | Expected 8 tables, found 1 (7 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints",
  "confidence": 0.0
}
```

---

## Real Examples

### Example 1: Dynamic SQL

#### DDL:
```sql
CREATE PROC [CONSUMPTION_PRIMAREPORTING].[spLoadProjectRegions] AS
BEGIN
    DECLARE @SQL NVARCHAR(MAX);
    SET @SQL = 'INSERT INTO Target SELECT * FROM Source';
    EXEC sp_executesql @SQL;
END
```

#### Parser Output:
```json
{
  "confidence": 0.0,
  "parse_failure_reason": "Dynamic SQL: sp_executesql @variable - table names unknown at parse time | Expected 8 tables, found 0 (8 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints"
}
```

#### Frontend Description:
```
❌ Parse Failed: 0.00 | Dynamic SQL: sp_executesql @variable - table names unknown at parse time | Expected 8 tables, found 0 (8 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints
```

#### User Action:
Add hints to DDL:
```sql
CREATE PROC [CONSUMPTION_PRIMAREPORTING].[spLoadProjectRegions] AS
BEGIN
    -- @LINEAGE_INPUTS: CONSUMPTION_PRIMA.ProjectRegions, CONSUMPTION_PRIMA.Regions
    -- @LINEAGE_OUTPUTS: CONSUMPTION_PRIMAREPORTING.ProjectRegions

    DECLARE @SQL NVARCHAR(MAX);
    SET @SQL = 'INSERT INTO Target SELECT * FROM Source';
    EXEC sp_executesql @SQL;
END
```

#### After Hints Added:
```json
{
  "confidence": 0.75,
  "source": "parser_with_hints",
  "description": "⚠️ Medium Confidence: 0.75 | Manual hints used"
}
```

---

### Example 2: WHILE Loop

#### DDL:
```sql
CREATE PROC [dbo].[spProcessBatches] AS
BEGIN
    DECLARE @Counter INT = 1;

    WHILE @Counter <= 100
    BEGIN
        INSERT INTO dbo.ProcessedData
        SELECT * FROM dbo.StagingData WHERE BatchID = @Counter;

        SET @Counter = @Counter + 1;
    END
END
```

#### Parser Output:
```json
{
  "confidence": 0.0,
  "parse_failure_reason": "WHILE loop: Iterative logic not supported by parser | Expected 2 tables, found 0 (2 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints"
}
```

#### Frontend Description:
```
❌ Parse Failed: 0.00 | WHILE loop: Iterative logic not supported by parser | Expected 2 tables, found 0 (2 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints
```

---

### Example 3: Deep Nesting

#### DDL:
```sql
CREATE PROC [dbo].[spDeepNesting] AS
BEGIN  -- Level 1
    BEGIN TRY  -- Level 2
        IF EXISTS (...) BEGIN  -- Level 3
            IF condition BEGIN  -- Level 4
                IF condition BEGIN  -- Level 5
                    INSERT INTO Target SELECT * FROM Source;
                END
            END
        END
    END TRY
    BEGIN CATCH
        INSERT INTO ErrorLog VALUES (ERROR_MESSAGE());
    END CATCH
END
```

#### Parser Output:
```json
{
  "confidence": 0.0,
  "parse_failure_reason": "Deep nesting: 7 BEGIN/END blocks (limit: 4) | Expected 3 tables, found 0 (3 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints"
}
```

---

## Detection Patterns

### Pattern Matching (Regex)

```python
# Dynamic SQL with EXEC(@variable)
r'EXEC\s*\(\s*@\w+\s*\)'

# Dynamic SQL with sp_executesql
r'sp_executesql\s+@\w+'

# WHILE loops
r'\bWHILE\b'

# CURSOR usage
r'\bCURSOR\b'

# BEGIN/END count
len(re.findall(r'\bBEGIN\b', ddl, re.IGNORECASE))

# CASE statements count
len(re.findall(r'\bCASE\b', ddl, re.IGNORECASE))

# CTEs count
len(re.findall(r'\bWITH\s+\w+\s+AS\s*\(', ddl, re.IGNORECASE))
```

---

## Benefits

### 1. **Transparency**
Users understand **WHY** parsing failed instead of seeing mysterious 0.00 confidence.

### 2. **Actionable Guidance**
Clear instruction: "→ Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints"

### 3. **Confidence Progression**
Users can track improvement:
```
0.0 (failed) → 0.75 (hints added) → 0.85 (complete) → 0.95 (UAT validated)
```

### 4. **Smoke Test Integration**
Shows expected vs found counts so users know how many tables are missing.

---

## Implementation Files

| File | Changes | Lines |
|------|---------|-------|
| `lineage_v3/parsers/quality_aware_parser.py` | Added `_detect_parse_failure_reason()` | 1224-1307 |
| `lineage_v3/parsers/quality_aware_parser.py` | Enhanced parser output metadata | 376-419 |
| `lineage_v3/parsers/quality_aware_parser.py` | Enhanced exception handler | 434-440 |
| `lineage_v3/output/frontend_formatter.py` | Added `_format_sp_description()` | 225-294 |
| `lineage_v3/output/frontend_formatter.py` | Enhanced description generation | 136-156 |

---

## Testing

### Unit Tests (Covered Patterns)

1. ✅ Dynamic SQL with `EXEC(@var)`
2. ✅ Dynamic SQL with `sp_executesql`
3. ✅ WHILE loops
4. ✅ CURSOR usage
5. ✅ Deep nesting (5+ BEGIN/END)
6. ✅ Complex CASE (10+ statements)
7. ✅ Multiple CTEs (10+ WITH)

### Integration Test

Run parser on real database and verify:
- Low confidence SPs show actionable reasons
- Expected vs found counts are accurate
- Hints improve confidence as expected

```bash
# Run parser
python lineage_v3/main.py run --parquet parquet_snapshots/

# Check frontend_lineage.json
grep -A 5 '"confidence": 0.0' lineage_output/frontend_lineage.json
```

---

## User Experience

### Before (v4.1.x)
```
User sees red node with "Confidence: 0.00"
↓
User confused: "Why did it fail? What do I do?"
↓
User gives up or asks support
```

### After (v4.2.0)
```
User sees red node with detailed description
↓
User reads: "Dynamic SQL detected → Add @LINEAGE hints"
↓
User adds hints to DDL
↓
Confidence improves to 0.75
↓
User happy! 🎉
```

---

## Next Steps

### Short-Term
1. Monitor user feedback on description clarity
2. Refine pattern detection if needed
3. Add more patterns based on real failures

### Long-Term
1. Machine learning to suggest which hints to add
2. Auto-generate hints from parse errors
3. Interactive hint editor in frontend

---

## Related Documentation

- [PARSER_SPECIFICATION.md](../reference/PARSER_SPECIFICATION.md) - Parser architecture
- [COMMENT_HINTS_DEVELOPER_GUIDE.md](../guides/COMMENT_HINTS_DEVELOPER_GUIDE.md) - How to add hints
- [PARSER_EVOLUTION_LOG.md](../reference/PARSER_EVOLUTION_LOG.md) - Version history

---

**Status:** Implemented and documented
