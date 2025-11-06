# Documentation Archive

**Last Updated:** 2025-11-06
**Organization:** Chronological by completion date

---

## Purpose

Historical documentation is archived here to keep the root directory clean and focused on current, active documentation. These files provide valuable context for understanding project evolution.

---

## Archive Structure

```
docs/archive/
├── README.md (this file)
├── 2025-11-02/ (26 files) - SP Dependency Implementation
├── 2025-11-03/ (9 files)  - Cache & Metrics Fixes
├── 2025-11-04/ (16 files) - UI Simplification & Performance
├── 2025-11-05/ (10 files) - Codebase Review & Refactoring
└── 2025-11-06/ (26 files) - Production Readiness & Doc Reorganization
```

---

## What's Archived

### 2025-11-02: SP Dependency Implementation (26 files)
**Status:** ✅ Deployed in v3.8.0

**Major Achievement:** SP-to-SP dependency tracking via EXEC statement detection

**Key Files:**
- `SP_DEPENDENCY_IMPLEMENTATION_SUMMARY.md` - Complete implementation
- `SP_DEPENDENCY_COMPLETE_SUMMARY.md` - Validation results
- `code-review-summary.md` - Codebase review v3.7.0
- `PHASE1_RESULTS_SUMMARY.md` - Testing results
- `AI_DISAMBIGUATOR_BUG_ANALYSIS.md` - AI-related fixes

**Impact:**
- Regex pattern extraction for EXEC statements
- Selective merge strategy (SQLGlot for tables, regex for SPs)
- Utility SP filtering (LogMessage, spLastRowCount excluded)

---

### 2025-11-03: Cache & Metrics Fixes (9 files)
**Status:** ✅ Deployed in v4.0.2

**Fixed:** Three critical confidence calculation bugs

**Key Files:**
- `LINEAGE_METADATA_ERROR_FIX.md` - Metadata cache fix
- `CACHE_MECHANISMS_AUDIT.md` - Cache analysis
- `V4_0_2_RELEASE_NOTES.md` - Release documentation

**Impact:**
- Unified confidence calculator
- Fixed stale cache after parquet uploads
- 95.5% accuracy verified

---

### 2025-11-04: UI Simplification & Performance (16 files)
**Status:** ✅ Deployed in v2.9.2

**Focus:** Frontend performance and UX improvements

**Key Files:**
- `UI_SIMPLIFICATION_V2.9.2.md` - UI streamlining
- `PERFORMANCE_OPTIMIZATION_COMPLETE.md` - 100x faster schema toggling
- `GLOBAL_EXCLUSION_PATTERNS_FEATURE.md` - Global filters
- `SP_DIRECTION_FIX_COMPLETE.md` - Arrow direction fix
- `sqlglot_research/` - SQLGlot improvement experiments

**Impact:**
- React.memo optimization (5,000+ nodes)
- Simplified filter UI
- Global exclusion patterns
- 151 SP-to-SP relationships corrected

---

### 2025-11-05: Codebase Review & Refactoring (10 files)
**Status:** ✅ Deployed in v4.0.3

**Focus:** Post-AI-removal cleanup and production readiness

**Key Files:**
- `codebase-review/CODEBASE_REVIEW_REPORT.md` - Comprehensive review
- `codebase-review/CODEBASE_REFACTOR_REPORT.md` - Refactoring plan
- `QUICK_START.md`, `STARTUP.md` - Outdated guides (superseded)

**Impact:**
- Removed AI dependencies and configuration
- Standardized versions to v4.0.3
- Improved logging and error handling
- Archived 34 legacy AI files

---

### 2025-11-06: Production Readiness & Doc Reorganization (26 files)
**Status:** ✅ Documentation reorganization complete

**Focus:** Production readiness review, documentation organization, parser improvements

**Key Subdirectories:**
- `phase2_validation/` - Comment hints validation testing
- `confidence_analysis/` - Confidence model v2.0.0 → v2.1.0 analysis
- One-time analyses and reviews

**Key Files:**
- `PRODUCTION_CODE_REVIEW.md` - Production readiness assessment
- `REPOSITORY_CLEANUP_ANALYSIS.md` - Cleanup plan
- `OPEN_TASKS.md` - Post-cleanup task tracking
- `CODEBASE_REVIEW_FINDINGS.md` - Code review findings
- `PROJECT_STATUS.md` - Status snapshot (97% SP confidence achieved)

**phase2_validation/** (7 files):
- `COMMENT_HINTS_VALIDATION_REPORT.md` - Real-world SP validation
- `PHASE2_VALIDATION_EXECUTIVE_SUMMARY.md` - High-level summary
- `test_hint_validation.sql` - Original test SP (swapped hints)
- `test_hint_validation_CORRECTED.sql` - Corrected golden record
- `test_comment_hints_validation.py` - Automated validation suite

**confidence_analysis/** (4 files):
- `CRITICAL_CONFIDENCE_MODEL_FLAW.md` - Problem analysis (agreement vs quality)
- `CONFIDENCE_MODEL_FIX_SUMMARY.md` - v2.1.0 fix
- `SQLGLOT_FAILURE_DEEP_ANALYSIS.md` - Why SQLGlot fails on T-SQL
- Led to SQL Cleaning Engine development

**Impact:**
- ✅ Phase 2 feature complete (Comment Hints)
- ✅ Confidence model fixed (v2.1.0)
- ✅ Documentation reorganized (guides/, reference/, development/)
- ✅ SQL Cleaning Engine implemented (integration pending)

---

## Archive Organization Principles

### When to Archive

Documents are archived when:
1. ✅ Task/feature is completed and deployed
2. ✅ Analysis/review is finished and decisions made
3. ✅ Content is superseded by newer documentation
4. ✅ File is outdated or would cause confusion in active docs

### Folder Naming

- **Date Format:** `YYYY-MM-DD` (completion date, not start date)
- **Grouped by:** Date completed/deployed, not by topic
- **README:** Each dated folder includes README with context

### What Stays Active

Documentation stays in root/docs when:
- ❌ Still being actively developed
- ❌ Required for current operations
- ❌ Frequently referenced by users/developers
- ❌ Part of official documentation set

---

## Current Active Documentation

**Root Documentation:**
- `README.md` - Project overview
- `CLAUDE.md` - Developer guide and instructions

**docs/ (Organized):**
- `docs/README.md` - Documentation navigation
- `docs/guides/` - How-to guides (5 files)
- `docs/reference/` - Technical specs (5 files)
- `docs/development/` - Active projects
  - `sql_cleaning_engine/` - SQL pre-processing (v1.0.0)
  - `PARSING_REVIEW_STATUS.md` - Parser improvement tracking

**See:** [docs/README.md](../README.md) for complete documentation index

---

## Archive Statistics

| Date | Files | Size | Key Topics |
|------|-------|------|------------|
| **2025-11-02** | 26 | ~500 KB | SP dependencies, AI fixes |
| **2025-11-03** | 9 | ~150 KB | Cache fixes, metrics |
| **2025-11-04** | 16 | ~300 KB | UI optimization, performance |
| **2025-11-05** | 10 | ~200 KB | Codebase review, cleanup |
| **2025-11-06** | 26 | ~350 KB | Production readiness, validation |
| **Total** | **87** | **~1.5 MB** | - |

---

## Quick Navigation

**By Topic:**
- **Parser Evolution:** 2025-11-02 (SP dependencies) → 2025-11-06 (Comment Hints, Confidence v2.1.0)
- **Frontend:** 2025-11-04 (UI simplification, performance)
- **Confidence Model:** 2025-11-03 (metrics fix) → 2025-11-06 (v2.1.0 quality fix)
- **Production Readiness:** 2025-11-05 (codebase review) → 2025-11-06 (final review)
- **Code Quality:** 2025-11-02 (code review) → 2025-11-05 (refactoring)

**By Version:**
- v3.7.0-3.8.0: 2025-11-02
- v4.0.2-4.0.3: 2025-11-03 through 2025-11-05
- v4.2.0: 2025-11-06 (Comment Hints, Confidence v2.1.0)

---

**Maintained By:** Data Lineage Team
**Next Archive:** When new features/analyses are completed
