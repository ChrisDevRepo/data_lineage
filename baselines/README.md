# Parser Baselines Directory

This directory contains baseline snapshots of parser performance, used for regression testing.

## What is a Baseline?

A baseline is a JSON snapshot of all stored procedure parsing results at a specific point in time. It captures:
- Object ID and name
- Schema
- Confidence score
- Input/output counts
- Full input/output dependencies

## Naming Convention

```
baseline_YYYYMMDD_description.json
```

**Examples**:
- `baseline_20251028_before_truncate_fix.json` - Snapshot before implementing TRUNCATE support
- `baseline_20251029_after_truncate_fix.json` - Snapshot after implementing TRUNCATE support

## Current Baselines

### baseline_20251028_before_truncate_fix.json
**Captured**: 2025-10-28
**Purpose**: Baseline before implementing TRUNCATE statement support
**Metrics**:
- Total SPs: 16
- High Confidence (≥0.85): 8 (50%)
- Average Confidence: 0.681

**Known Issues**:
- spLoadGLCognosData: 0.50 confidence (missing TRUNCATE outputs)
- spLoadFactGLCOGNOS: May be affected by TRUNCATE issue

## How to Use

### Capture a New Baseline

```bash
# Before making parser changes
python tests/parser_regression_test.py --capture-baseline baselines/baseline_$(date +%Y%m%d)_description.json
```

### Compare Against Baseline

```bash
# After making parser changes
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python tests/parser_regression_test.py --compare baselines/baseline_YYYYMMDD_description.json
```

## Baseline Lifecycle

1. **Capture** - Before any parser code change
2. **Compare** - After making changes, to detect regressions
3. **Archive** - Keep for historical reference
4. **Supersede** - When a new baseline becomes the standard

## Retention Policy

- **Keep forever**: Major version baselines (e.g., v3.0.0, v3.5.0, v4.0.0)
- **Keep 6 months**: Minor change baselines
- **Keep 1 month**: Experimental baselines (if change rejected)

## File Structure

Each baseline JSON contains:

```json
{
  "metadata": {
    "captured_at": "2025-10-28T12:34:56",
    "frontend_lineage_path": "lineage_output/frontend_lineage.json",
    "total_stored_procedures": 16,
    "avg_confidence": 0.681,
    "high_confidence_count": 8,
    "high_confidence_pct": 50.0
  },
  "objects": {
    "510624862": {
      "object_id": "510624862",
      "object_name": "spLoadGLCognosData",
      "schema_name": "CONSUMPTION_FINANCE",
      "confidence": 0.50,
      "inputs_count": 0,
      "outputs_count": 0,
      "inputs": [],
      "outputs": []
    },
    ...
  }
}
```

## See Also

- **Change Management**: [docs/PARSER_CHANGE_MANAGEMENT.md](../docs/PARSER_CHANGE_MANAGEMENT.md)
- **Evolution Log**: [docs/PARSER_EVOLUTION_LOG.md](../docs/PARSER_EVOLUTION_LOG.md)
- **Regression Test**: [tests/parser_regression_test.py](../tests/parser_regression_test.py)
