# Documentation Directory

**Last Updated:** 2025-11-06
**Organization:** Guides | Reference | Development | Archive

---

## 📚 Quick Navigation

| Category | Purpose | Audience |
|----------|---------|----------|
| **[guides/](#guides)** | How-to guides and tutorials | Users & Developers |
| **[reference/](#reference)** | Technical specifications | Developers & Architects |
| **[development/](#development)** | Active development projects | Development Team |
| **[archive/](#archive)** | Historical documents | Reference Only |

---

## 📖 Guides

**User-facing documentation for setup, configuration, and usage**

### Getting Started
- **[SETUP_AND_DEPLOYMENT.md](guides/SETUP_AND_DEPLOYMENT.md)** - Installation and deployment guide
- **[CONFIGURATION_GUIDE.md](guides/CONFIGURATION_GUIDE.md)** - Complete configuration reference
- **[MAINTENANCE_GUIDE.md](guides/MAINTENANCE_GUIDE.md)** - Operations and troubleshooting

### Usage
- **[PARSING_USER_GUIDE.md](guides/PARSING_USER_GUIDE.md)** - SQL parsing guide with examples
- **[COMMENT_HINTS_DEVELOPER_GUIDE.md](guides/COMMENT_HINTS_DEVELOPER_GUIDE.md)** - Using @LINEAGE hints in SQL

---

## 📋 Reference

**Technical specifications and reference documentation**

- **[SYSTEM_OVERVIEW.md](reference/SYSTEM_OVERVIEW.md)** - Architecture and components
- **[PARSER_EVOLUTION_LOG.md](reference/PARSER_EVOLUTION_LOG.md)** - Parser version history and changes
- **[DUCKDB_SCHEMA.md](reference/DUCKDB_SCHEMA.md)** - Database schema documentation
- **[SUB_DL_OPTIMIZE_PARSING_SPEC.md](reference/SUB_DL_OPTIMIZE_PARSING_SPEC.md)** - Parser evaluation framework

---

## 🚀 Development

**Active development projects and specifications**

### SQL Cleaning Engine (v1.0.0)
**Status:** ✅ Implementation Complete | ⏳ Integration Pending

Rule-based SQL pre-processing engine that increases SQLGlot success rate from ~5% to ~70-80% on complex T-SQL.

**Documents:**
- **[sql_cleaning_engine/README.md](development/sql_cleaning_engine/README.md)** - Project overview
- **[SQL_CLEANING_ENGINE_SUMMARY.md](development/sql_cleaning_engine/SQL_CLEANING_ENGINE_SUMMARY.md)** - Executive summary (8.9 KB)
- **[SQL_CLEANING_ENGINE_DOCUMENTATION.md](development/sql_cleaning_engine/SQL_CLEANING_ENGINE_DOCUMENTATION.md)** - Technical reference (12 KB)
- **[SQL_CLEANING_ENGINE_ACTION_PLAN.md](development/sql_cleaning_engine/SQL_CLEANING_ENGINE_ACTION_PLAN.md)** - 9-phase implementation plan (37 KB)

**Key Achievement:** 100% SQLGlot success on test SP (was 0%)

---

## 📦 Archive

**Historical documents organized by date**

### Recent Archives

#### 2025-11-06
- **phase2_validation/** - Phase 2 validation testing results and artifacts
- **confidence_analysis/** - Confidence model v2.0.0 → v2.1.0 analysis and fix
- **PRODUCTION_CODE_REVIEW.md** - Production readiness review
- **REPOSITORY_CLEANUP_ANALYSIS.md** - Repository cleanup analysis
- **OPEN_TASKS.md** - Post-cleanup task tracking

#### 2025-11-05
- Codebase refactor and review reports

#### 2025-11-04
- UI simplification (v2.9.2)
- Performance optimizations
- SQLGlot research experiments

#### 2025-11-03
- Cache mechanism audit
- Lineage metadata fixes

#### 2025-11-02
- SP dependency implementation
- AI disambiguator work
- Parser bug fixes

**See [archive/README.md](archive/README.md) for complete archive index**

---

## 🗺️ Document Relationships

```
Getting Started:
  SETUP_AND_DEPLOYMENT.md → CONFIGURATION_GUIDE.md → SYSTEM_OVERVIEW.md

Parser Work:
  PARSING_USER_GUIDE.md → COMMENT_HINTS_DEVELOPER_GUIDE.md → PARSER_EVOLUTION_LOG.md

Current Development:
  development/sql_cleaning_engine/ → PARSER_EVOLUTION_LOG.md (v1.0.0 entry)

Database:
  DUCKDB_SCHEMA.md (schema reference)

Operations:
  MAINTENANCE_GUIDE.md (troubleshooting)
```

---

## 📝 Documentation Standards

### File Naming
- Use SCREAMING_SNAKE_CASE for main docs
- Include purpose in filename (SETUP, GUIDE, REFERENCE, etc.)
- Add version or date to time-sensitive docs

### Structure
```markdown
# Document Title

**Last Updated:** YYYY-MM-DD
**Status:** Current | In Progress | Archived
**Version:** X.Y.Z (if applicable)

## Quick Links / TOC

## Main Content
```

### When to Archive
Archive documents when:
- Feature is fully implemented and stable
- Analysis/review is completed
- Superseded by newer version
- No longer relevant to current work

**Move to:** `archive/YYYY-MM-DD/document_name.md`

---

## 🔍 Finding Documentation

### By Task

| Task | Start Here |
|------|------------|
| **Install the system** | [guides/SETUP_AND_DEPLOYMENT.md](guides/SETUP_AND_DEPLOYMENT.md) |
| **Configure settings** | [guides/CONFIGURATION_GUIDE.md](guides/CONFIGURATION_GUIDE.md) |
| **Understand architecture** | [reference/SYSTEM_OVERVIEW.md](reference/SYSTEM_OVERVIEW.md) |
| **Fix parsing issues** | [guides/PARSING_USER_GUIDE.md](guides/PARSING_USER_GUIDE.md) |
| **Add @LINEAGE hints** | [guides/COMMENT_HINTS_DEVELOPER_GUIDE.md](guides/COMMENT_HINTS_DEVELOPER_GUIDE.md) |
| **Troubleshoot errors** | [guides/MAINTENANCE_GUIDE.md](guides/MAINTENANCE_GUIDE.md) |
| **Check parser versions** | [reference/PARSER_EVOLUTION_LOG.md](reference/PARSER_EVOLUTION_LOG.md) |
| **Query DuckDB directly** | [reference/DUCKDB_SCHEMA.md](reference/DUCKDB_SCHEMA.md) |
| **Work on SQL Cleaning Engine** | [development/sql_cleaning_engine/](development/sql_cleaning_engine/) |

### By Role

**End Users:**
- Start: [guides/SETUP_AND_DEPLOYMENT.md](guides/SETUP_AND_DEPLOYMENT.md)
- Configuration: [guides/CONFIGURATION_GUIDE.md](guides/CONFIGURATION_GUIDE.md)
- Usage: [guides/PARSING_USER_GUIDE.md](guides/PARSING_USER_GUIDE.md)

**Developers:**
- Architecture: [reference/SYSTEM_OVERVIEW.md](reference/SYSTEM_OVERVIEW.md)
- Parser: [guides/PARSING_USER_GUIDE.md](guides/PARSING_USER_GUIDE.md)
- Comment Hints: [guides/COMMENT_HINTS_DEVELOPER_GUIDE.md](guides/COMMENT_HINTS_DEVELOPER_GUIDE.md)
- Database: [reference/DUCKDB_SCHEMA.md](reference/DUCKDB_SCHEMA.md)

**DevOps:**
- Deployment: [guides/SETUP_AND_DEPLOYMENT.md](guides/SETUP_AND_DEPLOYMENT.md)
- Maintenance: [guides/MAINTENANCE_GUIDE.md](guides/MAINTENANCE_GUIDE.md)
- Configuration: [guides/CONFIGURATION_GUIDE.md](guides/CONFIGURATION_GUIDE.md)

**Architects:**
- System Design: [reference/SYSTEM_OVERVIEW.md](reference/SYSTEM_OVERVIEW.md)
- Database Schema: [reference/DUCKDB_SCHEMA.md](reference/DUCKDB_SCHEMA.md)
- Parser Architecture: [reference/PARSER_EVOLUTION_LOG.md](reference/PARSER_EVOLUTION_LOG.md)

---

## 📊 Documentation Stats

| Category | Files | Total Size |
|----------|-------|------------|
| **guides/** | 5 | ~84 KB |
| **reference/** | 4 | ~126 KB |
| **development/** | 1 project (4 files) | ~58 KB |
| **archive/** | Many (dated) | Historical |

**Total Active Documentation:** ~268 KB across 13 files

---

## 💡 Tips

1. **Start with guides/SETUP_AND_DEPLOYMENT.md** if you're new
2. **Check reference/PARSER_EVOLUTION_LOG.md** for version history
3. **Look in development/** for active projects
4. **Search archive/** only for historical context
5. **Update this README** when adding new major documentation

---

**Questions?** Check the main project [README.md](../README.md) or [CLAUDE.md](../CLAUDE.md)
