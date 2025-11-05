# Metrics Package

**Version:** 3.7.0
**Date:** 2025-11-02
**Purpose:** Single source of truth for all lineage metrics

## Overview

The `MetricsService` class is the **ONLY** place where lineage metrics should be calculated. All consumers (CLI, JSON output, tests, subagents) MUST use this service to ensure consistency.

## Why MetricsService?

**Problem (before v3.7.0):**
- Metrics calculated in multiple places (main.py, summary_formatter.py, tests)
- Different scopes mixed together ("Stored Procedure" vs "ALL objects")
- Numbers appeared "out of sync" (160 vs 471)

**Solution (v3.7.0+):**
- Single source of truth: `MetricsService`
- Explicit scope in all outputs
- Consistent calculations across all consumers

## Usage

### Basic Usage

```python
from lineage_v3.metrics import MetricsService
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

# Connect to workspace
workspace = DuckDBWorkspace('lineage_workspace.duckdb')
workspace.connect()

# Create metrics service
metrics = MetricsService(workspace)

# Get SP-only metrics
sp_metrics = metrics.get_parse_metrics(object_type='Stored Procedure')
print(f"High confidence SPs: {sp_metrics['confidence']['high']['count']}")

# Get ALL objects metrics
all_metrics = metrics.get_parse_metrics()  # object_type=None
print(f"Total parsed objects: {all_metrics['parsed']}")
```

### All Methods

#### 1. `get_parse_metrics(object_type=None)`

Get parse statistics with explicit scope.

**Parameters:**
- `object_type` (str, optional): 'Stored Procedure', 'View', 'Table', or None for ALL

**Returns:**
```python
{
    'scope': 'Stored Procedure' | 'View' | 'Table' | 'ALL',
    'total': 202,
    'parsed': 201,
    'parse_rate': 99.5,
    'confidence': {
        'high': {'count': 160, 'pct': 79.2, 'threshold': '≥0.85'},
        'medium': {'count': 10, 'pct': 5.0, 'threshold': '0.75-0.84'},
        'low': {'count': 32, 'pct': 15.8, 'threshold': '<0.75'}
    },
    'by_source': {
        'parser': 160,
        'dmv': 41,
        'metadata': 0
    }
}
```

#### 2. `get_dependency_metrics()`

Get dependency relationship metrics.

**Returns:**
```python
{
    'sp_to_sp': 62,
    'sp_to_table': 584,
    'sp_to_view': 23,
    'view_to_table': 259,
    'view_to_view': 5,
    'total': 933
}
```

#### 3. `get_isolation_metrics()`

Get isolated objects metrics.

**Returns:**
```python
{
    'total_isolated': 223,
    'by_type': {
        'Stored Procedure': 5,
        'Table': 212,
        'View': 6
    },
    'isolation_rate': 29.2  # % of all objects
}
```

#### 4. `get_all_metrics()`

Get all metrics in one call.

**Returns:**
```python
{
    'overall': {...},  # All objects
    'by_object_type': {
        'stored_procedures': {...},
        'views': {...},
        'tables': {...}
    },
    'dependencies': {...},
    'isolation': {...}
}
```

## Consumers

All these components use MetricsService (as of v3.7.0):

1. **CLI** (`lineage_v3/main.py`)
   - Shows SP-only metrics during parse
   - Explicit scope: "Stored Procedure"

2. **JSON Summary** (`lineage_v3/output/summary_formatter.py`)
   - Top-level: ALL objects metrics
   - Includes `by_object_type` breakdown

3. **Tests** (`test_isolated_objects.py`)
   - Test 4: Confidence distribution
   - Uses same calculation as production code

4. **Future subagents**
   - All subagents should use MetricsService

## Key Principles

### 1. Explicit Scope

Every metric MUST state what it measures:

```python
# GOOD: Explicit scope
sp_metrics = metrics.get_parse_metrics(object_type='Stored Procedure')
print(f"Scope: {sp_metrics['scope']}")  # "Stored Procedure"
print(f"High conf: {sp_metrics['confidence']['high']['count']}")  # 160

# ALSO GOOD: ALL objects
all_metrics = metrics.get_parse_metrics()
print(f"Scope: {all_metrics['scope']}")  # "ALL"
print(f"High conf: {all_metrics['confidence']['high']['count']}")  # 468
```

### 2. Single Calculation Point

**DO:**
```python
# Use MetricsService
from lineage_v3.metrics import MetricsService
metrics = MetricsService(workspace)
sp_count = metrics.get_parse_metrics(object_type='Stored Procedure')['total']
```

**DON'T:**
```python
# Manual SQL queries
count = workspace.query("SELECT COUNT(*) FROM objects WHERE object_type = 'Stored Procedure'")[0][0]
```

### 3. Consistency Across Consumers

All consumers should show identical numbers for the same scope:

| Consumer | Scope | High Confidence |
|----------|-------|-----------------|
| CLI | Stored Procedure | 160 |
| JSON (`by_object_type.stored_procedures`) | stored_procedures | 160 |
| Tests | Stored Procedure | 160 |

If numbers differ, there's a bug in MetricsService (not in the consumer).

## Understanding "160 vs 468"

This is **NOT** a bug or "out of sync":

- **160** = High confidence **Stored Procedures** only
- **468** = High confidence **ALL objects** (160 SPs + 60 Views + 248 Tables)

Both are correct - they measure different scopes.

## Implementation Details

### Data Sources

MetricsService queries these tables:
1. **objects** - Total object counts
2. **lineage_metadata** - Parse results, confidence scores
3. **dependencies** - Dependency relationships

### SQL Optimization

- Single query per metric type
- Uses CASE expressions for aggregation
- Efficient indexing on object_id

### Graceful Degradation

If tables don't exist, returns empty metrics:
```python
{
    'scope': 'Stored Procedure',
    'total': 0,
    'parsed': 0,
    'parse_rate': 0.0,
    ...
}
```

## Migration Guide

### For Existing Code

If you have code that calculates metrics manually:

**Before:**
```python
high_count = 0
for sp in stored_procedures:
    if sp.confidence >= 0.85:
        high_count += 1
```

**After:**
```python
from lineage_v3.metrics import MetricsService

metrics = MetricsService(workspace)
sp_metrics = metrics.get_parse_metrics(object_type='Stored Procedure')
high_count = sp_metrics['confidence']['high']['count']
```

### For Tests

**Before:**
```python
result = conn.execute("SELECT COUNT(*) FROM lineage_metadata WHERE confidence >= 0.85")
count = result.fetchone()[0]
```

**After:**
```python
from lineage_v3.metrics import MetricsService

metrics = MetricsService(workspace)
sp_metrics = metrics.get_parse_metrics(object_type='Stored Procedure')
count = sp_metrics['confidence']['high']['count']
```

## See Also

- **Implementation:** `lineage_v3/metrics/metrics_service.py`
- **Usage in CLI:** `lineage_v3/main.py` (lines 353-367)
- **Usage in JSON:** `lineage_v3/output/summary_formatter.py` (lines 178-225)
- **Usage in Tests:** `test_isolated_objects.py` (Test 4)
- **Full Documentation:** `METRICS_SERVICE_IMPLEMENTATION_COMPLETE.md`

## Version History

- **v3.7.0** (2025-11-02): Initial implementation
  - Created MetricsService as single source of truth
  - Updated all consumers (CLI, JSON, tests)
  - Added explicit scope to all metrics
  - Fixed "160 vs 471" confusion

---

**Status:** ✅ Production Ready
**All consumers synchronized as of v3.7.0**
