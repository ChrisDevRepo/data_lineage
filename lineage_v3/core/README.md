# Core Engine Module (Phase 3)

**Status:** ✅ Complete
**Version:** 3.0.0
**Date:** 2025-10-26

## Overview

The Core Engine is the DuckDB-based foundation of the Vibecoding Lineage Parser v2.0. It provides persistent workspace management, Parquet ingestion, incremental load tracking, and query interfaces for DMV data access.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DuckDB Workspace                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Parquet Snapshots (Input)     DuckDB Tables               │
│  ├─ objects.parquet      ────► objects                     │
│  ├─ dependencies.parquet ────► dependencies                │
│  ├─ definitions.parquet  ────► definitions                 │
│  └─ query_logs.parquet   ────► query_logs (optional)       │
│                                                             │
│  Metadata Tables (Persistent)                              │
│  ├─ lineage_metadata (incremental load tracking)           │
│  └─ lineage_results (final merged graph)                   │
│                                                             │
│  Query Interface                                            │
│  ├─ get_objects_to_parse() - Incremental load logic        │
│  ├─ get_dmv_dependencies() - Baseline dependencies         │
│  ├─ get_object_definition() - DDL text retrieval           │
│  ├─ resolve_table_names_to_ids() - Name → ID mapping       │
│  └─ update_metadata() - Track parsing results              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. DuckDBWorkspace (`duckdb_workspace.py`)

The main workspace manager that handles:

- **Connection Management**: Persistent DuckDB database with automatic schema initialization
- **Parquet Ingestion**: Load 4 required Parquet files into DuckDB tables
- **Incremental Load**: Track object modification timestamps to skip unchanged objects
- **Query Interface**: Unified API for accessing DMV data

#### Key Methods

```python
from lineage_v3.core import DuckDBWorkspace

# Initialize workspace
with DuckDBWorkspace(workspace_path="lineage_workspace.duckdb") as db:
    # Load Parquet files
    row_counts = db.load_parquet("parquet_snapshots/", full_refresh=True)

    # Get objects needing analysis (respects incremental logic)
    objects = db.get_objects_to_parse(full_refresh=False)

    # Get DMV dependencies (confidence 1.0)
    deps = db.get_dmv_dependencies()

    # Get DDL for parsing
    ddl = db.get_object_definition(object_id=1001)

    # Resolve table names to IDs
    ids = db.resolve_table_names_to_ids(['dbo.Table1', 'dbo.Table2'])

    # Update metadata after parsing
    db.update_metadata(
        object_id=1001,
        modify_date=datetime.now(),
        primary_source='dmv',
        confidence=1.0,
        inputs=[1002],
        outputs=[1003]
    )
```

### 2. Database Schema

#### Input Tables (from Parquet)

| Table | Source | Columns | Purpose |
|-------|--------|---------|---------|
| `objects` | objects.parquet | object_id, schema_name, object_name, object_type, modify_date | Authoritative object catalog |
| `dependencies` | dependencies.parquet | referencing_object_id, referenced_object_id | DMV dependencies (confidence 1.0) |
| `definitions` | definitions.parquet | object_id, definition | DDL text for parsing |
| `query_logs` | query_logs.parquet | command_text, submit_time | Optional runtime logs (confidence 0.9) |

#### Metadata Tables (persistent)

```sql
-- Incremental load tracking
CREATE TABLE lineage_metadata (
    object_id INTEGER PRIMARY KEY,
    last_parsed_modify_date TIMESTAMP,
    last_parsed_at TIMESTAMP,
    primary_source TEXT,           -- dmv, query_log, parser, ai
    confidence REAL,                -- 0.0-1.0
    inputs TEXT,                    -- JSON array of object_ids
    outputs TEXT                    -- JSON array of object_ids
);

-- Final lineage results
CREATE TABLE lineage_results (
    object_id INTEGER PRIMARY KEY,
    object_name TEXT,
    schema_name TEXT,
    object_type TEXT,
    inputs TEXT,                    -- JSON array of object_ids
    outputs TEXT,                   -- JSON array of object_ids
    primary_source TEXT,
    confidence REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Incremental Load Logic

The workspace implements smart incremental parsing to minimize redundant work:

### Decision Flow

```
For each object in objects.parquet:
  ├─ IF full_refresh=True
  │  └─ PARSE (force re-parse)
  │
  └─ ELSE (incremental mode)
     ├─ IF object_id NOT IN lineage_metadata
     │  └─ PARSE (never parsed before)
     │
     ├─ IF modify_date > last_parsed_modify_date
     │  └─ PARSE (object changed since last parse)
     │
     ├─ IF confidence < 0.85
     │  └─ PARSE (low confidence, needs re-analysis)
     │
     └─ ELSE
        └─ SKIP (object up to date, reuse metadata)
```

### Usage

```bash
# Incremental mode (default) - skips unchanged objects
python lineage_v3/main.py run --parquet parquet_snapshots/

# Full refresh mode - re-parses all objects
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

## Testing

### Unit Tests

Located in [tests/test_duckdb_workspace.py](../../tests/test_duckdb_workspace.py)

```bash
# Run with pytest
pytest tests/test_duckdb_workspace.py -v

# Run manual test (no pytest required)
python3 tests/manual_test_workspace.py
```

### Test Coverage

- ✅ Connection management and schema initialization
- ✅ Parquet loading with full refresh
- ✅ Incremental load logic (skip unchanged objects)
- ✅ DMV dependency retrieval
- ✅ Object definition retrieval
- ✅ Table name → ID resolution
- ✅ Metadata updates
- ✅ Workspace statistics
- ✅ Context manager support
- ✅ Error handling for missing files

## Integration with Main Pipeline

The Core Engine is integrated into [main.py](../main.py) as Step 1:

```python
from lineage_v3.core import DuckDBWorkspace

# Step 1: Ingest Parquet files into DuckDB
with DuckDBWorkspace(workspace_path=workspace) as db:
    # Load Parquet files
    row_counts = db.load_parquet(parquet, full_refresh=full_refresh)

    # Get objects requiring analysis
    objects_to_parse = db.get_objects_to_parse(full_refresh=full_refresh)

    # TODO: Steps 2-8 (upcoming phases)
```

## Performance Considerations

### Optimization Features

1. **Persistent DuckDB Workspace**: Database file persists between runs, avoiding re-ingestion
2. **Incremental Load**: Only processes changed objects (can reduce work by 90%+)
3. **Batch Name Resolution**: `resolve_table_names_to_ids()` handles multiple lookups in one query
4. **DuckDB Parquet Reader**: Native Parquet support (faster than pandas → SQL)
5. **JSON Storage**: Inputs/outputs stored as JSON strings for flexibility

### Benchmarks (Estimated)

| Dataset Size | Full Refresh | Incremental (5% changed) |
|--------------|--------------|--------------------------|
| 1,000 objects | ~5 seconds | ~1 second |
| 10,000 objects | ~30 seconds | ~3 seconds |
| 100,000 objects | ~5 minutes | ~30 seconds |

*Note: Actual performance depends on hardware and data complexity*

## Known Limitations

1. **No Column-Level Lineage**: Only tracks object-level dependencies (by design)
2. **No Dynamic SQL**: Cannot parse `EXEC(@sql)` statements (by design)
3. **Query Log Limit**: DMV retains only ~10,000 recent queries (Synapse limitation)
4. **JSON Storage**: Inputs/outputs stored as text (not native arrays) for DuckDB compatibility

## Future Enhancements (Post-Phase 3)

- [ ] **Phase 4**: SQLGlot parser integration for gap-filling
- [ ] **Phase 5**: AI fallback framework for complex SPs
- [ ] **Phase 6**: Output formatters (internal + frontend JSON)
- [ ] **Phase 7**: Full incremental pipeline with Steps 2-7
- [ ] **Phase 8**: Integration testing with real Synapse data

## Dependencies

```
duckdb>=1.4.1          # DuckDB engine
pyarrow>=22.0.0        # Parquet I/O
pandas>=2.3.3          # DataFrame operations
```

## API Reference

### DuckDBWorkspace Class

#### Constructor

```python
DuckDBWorkspace(
    workspace_path: Optional[str] = "lineage_workspace.duckdb",
    read_only: bool = False
)
```

#### Core Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `connect()` | `DuckDBPyConnection` | Connect to workspace |
| `disconnect()` | `None` | Close connection |
| `load_parquet(parquet_dir, full_refresh)` | `Dict[str, int]` | Load Parquet files |
| `get_objects_to_parse(full_refresh, confidence_threshold)` | `List[Dict]` | Get objects needing analysis |
| `get_dmv_dependencies()` | `List[Dict]` | Get baseline dependencies |
| `get_object_definition(object_id)` | `Optional[str]` | Get DDL text |
| `resolve_table_names_to_ids(table_names)` | `Dict[str, Optional[int]]` | Map names → IDs |
| `update_metadata(object_id, ...)` | `None` | Update lineage metadata |
| `query(sql, params)` | `List[tuple]` | Execute arbitrary SQL |
| `get_stats()` | `Dict[str, Any]` | Get workspace statistics |

## Changelog

### v3.0.0 (2025-10-26) - Phase 3 Complete

- ✅ Implemented DuckDB workspace manager
- ✅ Parquet ingestion for 4 required files
- ✅ Incremental load metadata tracking
- ✅ Query interface for DMV data access
- ✅ Full test coverage (manual tests passing)
- ✅ Integration with main.py CLI
- ✅ Context manager support
- ✅ Comprehensive documentation

---

**Next Phase:** Phase 4 - SQLGlot Parser Integration

For more information, see:
- [lineage_specs.md](../../lineage_specs.md) - Full specification (v2.1)
- [CLAUDE.md](../../CLAUDE.md) - Project overview
- [main.py](../main.py) - CLI integration
