# Deprecated Implementation (Lineage v2)

**Date Deprecated:** 2025-10-26
**Reason:** Migration to new architecture (v3) with DuckDB, SQLGlot, and Microsoft Agent Framework

---

## What Was Moved

This folder contains the original autonomous lineage engine implementation (v2) that has been superseded by the new v3 implementation.

### Directory Structure

```
deprecated/
├── scripts/                    # Main entry point (autonomous_lineage.py)
├── ai_analyzer/               # AI-assisted SQL analysis
├── parsers/                   # SQL parsing modules
├── validators/                # Dependency validation
├── output/                    # JSON output formatters
└── README_DEPRECATED.md       # This file
```

---

## Key Differences: v2 vs v3

| Aspect | v2 (Deprecated) | v3 (New) |
|--------|----------------|----------|
| **Data Source** | File-based (`.sql` files) | DMV-based (Parquet snapshots) |
| **Primary Key** | String `"schema.object_name"` | Integer `object_id` |
| **Database** | None (in-memory Python dicts) | DuckDB persistent workspace |
| **SQL Parser** | Regex + AI hybrid | SQLGlot AST + AI fallback |
| **AI Framework** | Custom multi-source | Microsoft Agent Framework |
| **Output Format** | Frontend-only (string IDs) | Both internal (int) + frontend (string) |
| **Incremental Loads** | Not supported | Supported via `modify_date` tracking |
| **Provenance** | Verbose `sources[]` array | Simplified `primary_source` + `confidence` |

---

## Why v2 Was Deprecated

### Limitations of v2:

1. **File-Based Parsing Unreliable**
   - Regex parsing of `.sql` files prone to errors with complex SQL
   - No authoritative source of truth (files may be out of sync with deployed objects)
   - Temp table unwrapping logic fragile

2. **No Persistence**
   - Every run required full re-parsing of all objects
   - No incremental update capability
   - Performance degraded with large codebases (100+ objects)

3. **String-Based Object Tracking**
   - Normalization issues (`[schema].[table]` vs `schema.table`)
   - No reliable way to handle renamed objects
   - Cross-schema references ambiguous

4. **Limited AI Integration**
   - Custom AI logic without framework support
   - No agent orchestration or validation pipeline
   - Confidence scoring simplistic

---

## v2 Achievements (What Worked Well)

Despite these limitations, v2 successfully demonstrated:

✅ **Bidirectional Graph Construction** - Tables tracking both writers (inputs) and readers (outputs)
✅ **Circular Dependency Detection** - SPs that both read and write to same table
✅ **Frontend Compatibility** - JSON output format worked perfectly with React Flow
✅ **Logging Exclusion** - Automatically filtered out `ADMIN.Logs`, `dbo.LogMessage`, etc.
✅ **Confidence Scoring** - Multi-source confidence aggregation (DMV > Parser > AI)

These patterns have been **preserved and enhanced** in v3.

---

## Migration Notes

### Code Reuse from v2 → v3

The following components were **adapted** (not directly copied):

- **parsers/sql_parser_enhanced.py** → `lineage_v3/parsers/sqlglot_parser.py`
  - Migrated from regex to SQLGlot AST traversal
  - Object resolution now uses DuckDB instead of file search

- **output/json_formatter.py** → `lineage_v3/output/frontend_adapter.py`
  - Adapted to handle both internal (int) and frontend (string) formats
  - Added bidirectional graph population logic

- **ai_analyzer/** → `lineage_v3/ai_analyzer/`
  - Replaced custom AI logic with Microsoft Agent Framework
  - Added ValidatorAgent for cross-referencing against DuckDB

### Breaking Changes

⚠️ **v3 is NOT backward compatible with v2 output**

- Node IDs changed from `"schema.object"` to integer `object_id`
- Provenance structure simplified
- Requires Parquet snapshots instead of `.sql` files

### For Users Upgrading

If you have existing v2 lineage JSON files:

1. **Re-run lineage analysis** with v3 using Parquet snapshots
2. v3 will generate both internal and frontend JSON formats
3. Frontend format is compatible with existing React Flow visualizations

---

## Archival Status

**Status:** ARCHIVED - Read-only reference
**Support:** No bug fixes or enhancements
**Recommendation:** Use v3 for all new lineage analysis

This code remains available for:
- Historical reference
- Understanding evolution of the lineage engine
- Comparing v2 vs v3 approaches

---

## Questions?

For issues or questions about the new v3 implementation, see:
- [lineage_specs_v2.md](../lineage_specs_v2.md) - v3 specification
- [lineage_v3/](../lineage_v3/) - New codebase
- [docs/](../docs/) - Updated documentation
