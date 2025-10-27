# Phase 4: SQLGlot Parser - Implementation Plan

**Status:** 🚧 Ready to Start
**Prerequisites:** Phase 3 Complete ✅
**Estimated Duration:** 2-3 hours
**Date:** 2025-10-26

---

## Overview

Phase 4 implements the SQLGlot-based SQL parser to extract table-level lineage from DDL definitions. This fills gaps where DMV dependencies are missing or incomplete.

**Goal:** Parse stored procedure DDL using SQLGlot AST to extract source (FROM/JOIN) and target (INSERT/UPDATE) table references, then resolve them to object_ids.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Detect Gaps (Gap Detector)                         │
├─────────────────────────────────────────────────────────────┤
│ • Query lineage_metadata for unresolved objects             │
│ • Identify SPs with no inputs/outputs                       │
│ • Return list of object_ids needing parsing                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: SQLGlot Parser (SQL Parser)                        │
├─────────────────────────────────────────────────────────────┤
│ For each gap:                                               │
│ 1. Fetch DDL from definitions table                         │
│ 2. Parse with SQLGlot (T-SQL dialect)                       │
│ 3. Traverse AST to extract:                                 │
│    • Source tables: FROM, JOIN clauses                      │
│    • Target tables: INSERT INTO, UPDATE, MERGE              │
│ 4. Resolve table names → object_ids (via workspace)         │
│ 5. Return {object_id, inputs[], outputs[], confidence=0.85} │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Update lineage_metadata                                     │
│ • primary_source: "parser"                                  │
│ • confidence: 0.85                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Components to Implement

### 1. Gap Detector (`lineage_v3/core/gap_detector.py`)

**Purpose:** Identify objects with missing dependencies

**Methods:**
```python
class GapDetector:
    def __init__(self, workspace: DuckDBWorkspace):
        """Initialize with DuckDB workspace."""

    def detect_gaps(self) -> List[Dict[str, Any]]:
        """
        Find objects with no resolved dependencies.

        Returns:
            List of dicts with:
            - object_id
            - schema_name
            - object_name
            - object_type
        """
```

**Query Logic:**
```sql
-- Find objects with no dependencies in lineage_metadata
SELECT
    o.object_id,
    o.schema_name,
    o.object_name,
    o.object_type
FROM objects o
LEFT JOIN lineage_metadata m ON o.object_id = m.object_id
WHERE
    o.object_type = 'Stored Procedure'
    AND (
        m.object_id IS NULL  -- Never parsed
        OR (m.inputs = '[]' AND m.outputs = '[]')  -- No dependencies found
    )
```

---

### 2. SQLGlot Parser (`lineage_v3/parsers/sqlglot_parser.py`)

**Purpose:** Extract lineage from DDL using AST traversal

**Methods:**
```python
class SQLGlotParser:
    def __init__(self, workspace: DuckDBWorkspace):
        """Initialize with DuckDB workspace."""

    def parse_object(self, object_id: int) -> Dict[str, Any]:
        """
        Parse DDL for a single object.

        Args:
            object_id: Object to parse

        Returns:
            {
                'object_id': int,
                'inputs': List[int],   # source tables (FROM/JOIN)
                'outputs': List[int],  # target tables (INSERT/UPDATE)
                'confidence': 0.85,
                'source': 'parser'
            }
        """

    def _extract_table_references(self, ddl: str) -> Dict[str, List[str]]:
        """
        Extract table names from DDL using SQLGlot AST.

        Args:
            ddl: DDL text

        Returns:
            {
                'sources': ['schema.table1', 'schema.table2'],
                'targets': ['schema.table3']
            }
        """

    def _resolve_table_names(self, table_names: List[str]) -> List[int]:
        """
        Resolve table names to object_ids.

        Args:
            table_names: List of table names (schema.table format)

        Returns:
            List of object_ids (excludes unresolved names)
        """
```

**SQLGlot AST Traversal Example:**
```python
import sqlglot
from sqlglot import exp

def extract_source_tables(ddl: str) -> List[str]:
    """Extract source tables (FROM, JOIN)."""
    tables = []

    # Parse T-SQL
    parsed = sqlglot.parse_one(ddl, dialect='tsql')

    # Find all FROM clauses
    for table in parsed.find_all(exp.Table):
        # Get schema.table format
        schema = table.db if table.db else 'dbo'
        name = table.name
        tables.append(f"{schema}.{name}")

    return list(set(tables))  # Deduplicate

def extract_target_tables(ddl: str) -> List[str]:
    """Extract target tables (INSERT, UPDATE, MERGE)."""
    tables = []

    parsed = sqlglot.parse_one(ddl, dialect='tsql')

    # Find INSERT statements
    for insert in parsed.find_all(exp.Insert):
        table = insert.this
        schema = table.db if table.db else 'dbo'
        name = table.name
        tables.append(f"{schema}.{name}")

    # Find UPDATE statements
    for update in parsed.find_all(exp.Update):
        table = update.this
        schema = table.db if table.db else 'dbo'
        name = table.name
        tables.append(f"{schema}.{name}")

    return list(set(tables))
```

---

### 3. Integration into Main Pipeline

**File:** `lineage_v3/main.py`

Add Steps 4-5 after Parquet ingestion:

```python
# Step 4: Detect gaps
from lineage_v3.core.gap_detector import GapDetector

gap_detector = GapDetector(db)
gaps = gap_detector.detect_gaps()

click.echo(f"🔍 Objects with missing dependencies: {len(gaps)}")

# Step 5: Run SQLGlot parser
from lineage_v3.parsers.sqlglot_parser import SQLGlotParser

parser = SQLGlotParser(db)

for obj in gaps:
    try:
        result = parser.parse_object(obj['object_id'])

        # Update metadata
        db.update_metadata(
            object_id=result['object_id'],
            modify_date=obj['modify_date'],
            primary_source='parser',
            confidence=0.85,
            inputs=result['inputs'],
            outputs=result['outputs']
        )

    except Exception as e:
        click.echo(f"⚠️  Failed to parse {obj['schema_name']}.{obj['object_name']}: {e}")
```

---

## Testing

### Unit Tests (`tests/test_sqlglot_parser.py`)

```python
def test_extract_source_tables():
    """Test FROM/JOIN extraction."""
    ddl = """
    CREATE PROCEDURE test AS
    SELECT * FROM dbo.Table1
    JOIN CONSUMPTION_FINANCE.Table2 ON ...
    """

    parser = SQLGlotParser(workspace)
    tables = parser._extract_table_references(ddl)

    assert 'dbo.Table1' in tables['sources']
    assert 'CONSUMPTION_FINANCE.Table2' in tables['sources']

def test_extract_target_tables():
    """Test INSERT/UPDATE extraction."""
    ddl = """
    CREATE PROCEDURE test AS
    INSERT INTO dbo.TargetTable
    SELECT * FROM dbo.SourceTable
    """

    parser = SQLGlotParser(workspace)
    tables = parser._extract_table_references(ddl)

    assert 'dbo.TargetTable' in tables['targets']

def test_resolve_table_names():
    """Test name → ID resolution."""
    # Requires sample data in workspace
    parser = SQLGlotParser(workspace)
    ids = parser._resolve_table_names(['dbo.Table1', 'dbo.NonExistent'])

    assert len(ids) == 1  # Only Table1 resolved
```

---

## Files to Create

1. **`lineage_v3/core/gap_detector.py`** (~150 lines)
   - GapDetector class
   - SQL query to find gaps
   - Integration with workspace

2. **`lineage_v3/parsers/sqlglot_parser.py`** (~300 lines)
   - SQLGlotParser class
   - AST traversal logic
   - Table name resolution
   - Error handling

3. **`lineage_v3/parsers/__init__.py`** (~10 lines)
   - Module exports

4. **`tests/test_gap_detector.py`** (~100 lines)
   - Unit tests for gap detection

5. **`tests/test_sqlglot_parser.py`** (~200 lines)
   - Unit tests for parser
   - Sample DDL test cases

6. **`lineage_v3/parsers/README.md`** (~100 lines)
   - Parser documentation
   - Supported SQL patterns
   - Limitations

---

## Files to Modify

1. **`lineage_v3/main.py`**
   - Add Steps 4-5 to run command
   - Import gap detector and parser
   - Add progress reporting

2. **`lineage_v3/core/__init__.py`**
   - Export GapDetector

---

## Supported SQL Patterns

### ✅ Will Parse Successfully

```sql
-- Simple SELECT
SELECT * FROM dbo.Table1

-- JOINs
SELECT * FROM dbo.Table1
JOIN schema.Table2 ON ...

-- INSERT INTO
INSERT INTO dbo.Target
SELECT * FROM dbo.Source

-- UPDATE
UPDATE dbo.Table1
SET col = val
FROM dbo.Table2

-- MERGE
MERGE INTO dbo.Target AS t
USING dbo.Source AS s
ON ...

-- Subqueries
SELECT * FROM (SELECT * FROM dbo.Table1) sub

-- CTEs
WITH cte AS (SELECT * FROM dbo.Table1)
SELECT * FROM cte
```

### ❌ Limitations (Phase 4)

```sql
-- Dynamic SQL (cannot parse)
DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM ' + @tableName
EXEC(@sql)

-- Temp tables (out of scope)
CREATE TABLE #temp (...)
SELECT * FROM #temp

-- Cross-database references (may not resolve)
SELECT * FROM OtherDB.dbo.Table1

-- System tables (filtered out)
SELECT * FROM sys.objects
```

---

## Success Criteria

- [x] Gap detector identifies unresolved stored procedures
- [x] SQLGlot parser extracts source/target tables
- [x] Table names resolve to object_ids
- [x] Confidence assigned as 0.85
- [x] Metadata updated in lineage_metadata table
- [x] Unit tests passing (>80% coverage)
- [x] Integration with main.py CLI
- [x] Documentation complete

---

## Next Phase: Phase 5

**AI Fallback Framework (Microsoft Agent Framework)**
- Handle objects still unresolved after SQLGlot
- Multi-agent orchestration
- Confidence: 0.7

---

## Timeline

| Task | Estimated Time |
|------|---------------|
| Gap Detector implementation | 30 min |
| SQLGlot Parser implementation | 60 min |
| Unit tests | 30 min |
| Integration & testing | 30 min |
| Documentation | 30 min |
| **Total** | **3 hours** |

---

**Ready to Start:** ✅ All prerequisites complete (Phase 3 done)

**Next Command:**
```bash
# When ready, tell me to start Phase 4
```
