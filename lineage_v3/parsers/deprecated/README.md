# Deprecated Parser Implementations

These parser implementations have been superseded by `quality_aware_parser.py` (used via `dual_parser.py`).

## Files

- **enhanced_sqlglot_parser.py** (639 lines) - Enhanced SQLGlot implementation with preprocessing
- **sqlglot_parser.py** (460 lines) - Initial SQLGlot wrapper implementation

**Total:** 1,099 lines of deprecated code

## Current Implementation

**Active parser:** `quality_aware_parser.py` (v3.6.0)
**Wrapper:** `dual_parser.py` (provides dual validation)

## Why These Were Replaced

The current `quality_aware_parser.py` provides:

1. **Better Confidence Scoring** - Regex baseline validation against SQLGlot results
2. **Enhanced Preprocessing** - Improved T-SQL compatibility (removes CATCH blocks, EXEC, logging)
3. **Quality Metrics** - Compares parsed tables against regex-found tables
4. **Query Log Validation** - Cross-validates with runtime execution evidence
5. **Self-Referencing Support** - Handles complex INSERT → SELECT → INSERT patterns

## Migration History

- **v3.0-v3.3:** Used `enhanced_sqlglot_parser.py`
- **v3.4.0:** Introduced `quality_aware_parser.py` with confidence scoring
- **v3.5.0:** Added TRUNCATE statement support
- **v3.6.0:** Added self-referencing pattern support, simplified source extraction
- **v3.7.0:** Archived old implementations (this cleanup)

## Performance Comparison

| Metric | Old (enhanced_sqlglot) | Current (quality_aware) |
|--------|------------------------|-------------------------|
| High Confidence (≥0.85) | ~40-50% | 80.7% |
| Average Confidence | ~0.65 | 0.800 |
| Baseline Validation | No | Yes |
| Query Log Integration | No | Yes |

## Restoration

If needed, these parsers can be restored from git history:
```bash
git log --all --full-history -- lineage_v3/parsers/deprecated/enhanced_sqlglot_parser.py
```

## Archived Date

2025-10-31
