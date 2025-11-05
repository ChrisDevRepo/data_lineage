# Documentation Archive

This directory contains archived project documentation organized by date.

## Purpose

Historical documentation is archived here to keep the root directory clean and focused on current, active documentation. These files provide valuable context for understanding the project evolution.

## Archive Structure

```
docs/archive/
├── 2025-11-03/          # Confidence Metrics Fix
├── 2025-11-04/          # SP-to-SP Lineage Direction Fix
└── 2025-11-05/          # Codebase Review & Misc Documentation
    ├── codebase-review/ # Comprehensive codebase review
    ├── QUICK_START.md   # Outdated quick start
    └── STARTUP.md       # Outdated startup guide
```

## What's Archived

### 2025-11-03: Confidence Metrics Fix
**Status:** ✅ Completed and deployed in v4.0.3

Fixed three critical bugs in confidence calculation:
1. Inconsistent formulas between backend and evaluation
2. Missing real-time stats during upload
3. Stale cache after new parquet uploads

**Impact:** Unified confidence calculator, 95.5% accuracy verified

**Files:** 2 files (CONFIDENCE_FIX_SUMMARY.md, CONFIDENCE_FIX_CHECKLIST.md)

---

### 2025-11-04: SP-to-SP Lineage Direction Fix
**Status:** ✅ Completed and deployed in v4.0.3

Fixed incorrect arrow direction for stored procedure calls in the GUI visualization.

**Impact:** All 151 SP-to-SP relationships now display correctly

**Files:** 2 files (SP_DIRECTION_FIX_COMPLETE.md, verify_sp_direction_fix.md)

---

### 2025-11-05: Codebase Review & Cleanup
**Status:** ✅ Completed and deployed

Comprehensive post-AI-removal codebase review and refactoring.

**Achievements:**
- Removed AI dependencies and configuration
- Standardized versions to v4.0.3
- Improved logging and error handling
- Updated branding consistency
- Archived 34 legacy AI files

**Files:** 8 files (6 review reports + 2 outdated guides)

---

## Active Documentation

For current documentation, see the root directory:
- **CLAUDE.md** - Developer guide and project instructions
- **README.md** - Main project overview
- **PROJECT_STATUS.md** - Current project status and metrics
- **lineage_specs.md** - Parser technical specification

## Archive Policy

Documentation is archived when:
1. Task/fix is completed and deployed
2. Content is superseded by newer documentation
3. File is outdated or redundant
4. Keeping it in root would cause confusion

Each archived directory includes a README explaining the context and contents.

---

**Last Updated:** 2025-11-05
**Maintained By:** Project team
