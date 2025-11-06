# Open Tasks - Production Readiness Checklist

**Last Updated:** 2025-11-06
**Status:** Post-Cleanup Review
**Priority:** Medium (Non-Blocking for Production)

---

## Overview

This document tracks remaining tasks identified during the repository cleanup and production readiness preparation. All **critical** items have been completed. The items below are **quality improvements** and **nice-to-haves** that can be addressed post-deployment.

**Cleanup Status:** ✅ **Complete**
- Outdated documents archived
- Experimental directories removed
- Production documentation created
- Repository structure optimized

---

## Category 1: Documentation Consistency

### Task 1.1: Standardize Version Numbers

**Priority:** 🟡 Medium
**Effort:** 1 hour
**Status:** ⏳ Pending

**Issue:**
Version numbers are inconsistent across documentation files:
- README.md: Parser v4.1.3, Frontend v2.9.1
- CLAUDE.md: Frontend v2.9.2
- frontend/README.md: v2.9.4
- api/README.md: API v3.0.1 vs v4.0.3

**Actual Code Versions:**
- Frontend package.json: 1.0.0 (semver)
- API main.py: 4.0.3
- Parser __init__.py: 3.0.0

**Action Required:**
1. Decide on versioning strategy:
   - Option A: Use semver from code everywhere (1.0.0, 4.0.3, 3.0.0)
   - Option B: Use feature versions in docs (v2.9.x, v4.1.3) and map to semver in code
2. Update all documentation to use consistent version numbers
3. Add version mapping table to README if using dual system

**Files to Update:**
- README.md (lines 83-84, 187, 279)
- CLAUDE.md (line 14, 167)
- frontend/README.md (line 4)
- api/README.md (line 3)

---

### Task 1.2: Verify Internal Links

**Priority:** 🟢 Low
**Effort:** 30 minutes
**Status:** ⏳ Pending

**Issue:**
Some internal links may reference archived or removed files.

**Action Required:**
```bash
# Find all markdown files
find . -name "*.md" -exec grep -l "\[.*\](.*\.md)" {} \;

# Check for broken links (manual verification)
# - docs/QUERY_LOGS_ANALYSIS.md referenced in CLAUDE.md but not found
# - Verify all cross-references work
```

**Files to Check:**
- All new docs: SYSTEM_OVERVIEW, SETUP_AND_DEPLOYMENT, MAINTENANCE_GUIDE
- README.md
- CLAUDE.md
- Component READMEs (api/, frontend/, extractor/)

---

## Category 2: Code Quality Improvements

### Task 2.1: Remove AI Type Literals from Code

**Priority:** 🟢 Low (Informational Only)
**Effort:** 15 minutes
**Status:** ⏳ Pending

**Issue:**
Type hints in `lineage_v3/models/lineage_result.py` include 'ai' literal that's never used:
```python
step_name: Literal['regex', 'sqlglot', 'ai']  # 'ai' never actually used
primary_source: Literal['regex', 'sqlglot', 'ai', 'hybrid']
```

**Impact:** No functional impact (AI step never called), but confusing for developers

**Action Required:**
```python
# Update to:
step_name: Literal['regex', 'sqlglot']
primary_source: Literal['regex', 'sqlglot', 'hybrid']
```

**Files to Update:**
- `lineage_v3/models/lineage_result.py` (lines 20, 60, 92)

---

## Category 3: Testing & Quality Assurance

### Task 3.1: End-to-End Testing

**Priority:** 🟡 Medium
**Effort:** 2-3 hours
**Status:** ⏳ Pending

**Recommended Tests:**
1. **Upload Flow** - Test with sample Parquet files
2. **Incremental vs Full Refresh** - Verify both modes work
3. **Frontend Loading** - Test with various dataset sizes (100, 500, 1000, 5000 nodes)
4. **Search Functionality** - Test DDL search across all objects
5. **Trace Mode** - Verify upstream/downstream exploration

**Test Data:**
- Use test_baselines/ for frontend visual regression
- Create sample Parquet files for backend testing
- Document test procedures in a new docs/TESTING_GUIDE.md (optional)

---

### Task 3.2: Browser Compatibility Testing

**Priority:** 🟢 Low
**Effort:** 1 hour
**Status:** ⏳ Pending

**Browsers to Test:**
- ✅ Chrome/Edge (primary development browser)
- ⏳ Firefox
- ⏳ Safari (macOS)

**Test Cases:**
- Graph visualization rendering
- Monaco Editor (SQL viewer) functionality
- Toolbar interactions
- Performance with 1,000+ nodes

---

## Category 4: Deployment Preparation

### Task 4.1: Create Azure Deployment Scripts

**Priority:** 🟡 Medium
**Effort:** 2-3 hours
**Status:** ⏳ Pending

**Scripts to Create:**
1. `deploy-backend.sh` - Azure App Service deployment
2. `deploy-frontend.sh` - Azure Static Web Apps deployment
3. `setup-azure-resources.sh` - Resource group, app service plan, etc.

**Location:** Create `deployment/` folder with scripts

**Reference:** See [SETUP_AND_DEPLOYMENT.md](SETUP_AND_DEPLOYMENT.md) for commands

---

### Task 4.2: Configure GitHub Actions

**Priority:** 🟡 Medium
**Effort:** 1-2 hours
**Status:** ⏳ Pending

**Workflows to Create:**
1. `.github/workflows/deploy-backend.yml` - Backend deployment on push to main
2. `.github/workflows/deploy-frontend.yml` - Frontend deployment on push to main
3. `.github/workflows/test.yml` - Run tests on PR (future)

**Benefits:**
- Automated deployment on merge
- Consistent deployment process
- Rollback capability via GitHub

---

## Category 5: Optional Enhancements

### Task 5.1: Create Deployment Troubleshooting Guide

**Priority:** 🟢 Low
**Effort:** 1 hour
**Status:** ⏳ Pending

**Content:**
- Common Azure deployment errors
- CORS troubleshooting specific to Azure
- Application Insights setup
- Performance monitoring setup

**Location:** Could be added to MAINTENANCE_GUIDE.md or separate doc

---

### Task 5.2: Add Health Check Monitoring Script

**Priority:** 🟢 Low
**Effort:** 30 minutes
**Status:** ⏳ Pending

**Script Purpose:**
- Automated health checks (backend, frontend, API endpoints)
- Email/Slack alerts on failures
- Uptime monitoring

**Location:** `monitoring/health_check.sh`

**Example:**
```bash
#!/bin/bash
# Check backend health every 5 minutes
while true; do
  curl -s http://localhost:8000/health || echo "⚠️ Backend down!"
  sleep 300
done
```

---

### Task 5.3: Create Quick Reference Card

**Priority:** 🟢 Low (Nice-to-Have)
**Effort:** 1 hour
**Status:** ⏳ Pending

**Content:**
- Common commands (start, stop, restart)
- Port numbers
- Key file locations
- Troubleshooting quick fixes

**Format:** One-page PDF or markdown cheat sheet
**Audience:** New developers, support engineers

---

## Category 6: Known Issues (Non-Blocking)

### Issue 6.1: Duplicate extractor/README.md

**Priority:** 🟢 Low
**Effort:** 5 minutes
**Status:** ⏳ Pending

**Observation:**
```bash
find . -name "README.md" | grep extractor
# Found:
# ./extractor/README.md
# ./lineage_v3/extractor/README.md
```

**Action Required:**
- Verify both files have same content
- If duplicate, remove one and update links
- If different purposes, rename to clarify (e.g., EXTRACTOR_SETUP.md, EXTRACTOR_API.md)

---

### Issue 6.2: Missing docs/QUERY_LOGS_ANALYSIS.md

**Priority:** 🟢 Low
**Effort:** N/A
**Status:** ⏳ Pending Investigation

**Observation:**
- Referenced in CLAUDE.md line 129 (now removed from latest version)
- File may have been archived previously or never created

**Action Required:**
- Search git history: `git log --all --full-history -- "**/QUERY_LOGS_ANALYSIS.md"`
- If found in history and still relevant, restore
- If never existed, ignore (reference removed from CLAUDE.md)

---

## Summary

### By Priority

| Priority | Tasks | Effort |
|----------|-------|--------|
| 🔴 Critical | 0 | - |
| 🟡 Medium | 5 | ~7-10 hours |
| 🟢 Low | 7 | ~5-6 hours |
| **Total** | **12** | **~12-16 hours** |

### Quick Wins (< 1 hour each)

1. ✅ Verify internal links (30 min)
2. ✅ Remove AI type literals from code (15 min)
3. ✅ Check duplicate extractor/README.md (5 min)
4. ✅ Add health check monitoring script (30 min)

### Recommended Next Steps

**Pre-Deployment:**
1. ✅ Standardize version numbers (Task 1.1)
2. ✅ End-to-end testing (Task 3.1)

**Post-Deployment:**
4. ✅ Configure GitHub Actions (Task 4.2)
5. ✅ Browser compatibility testing (Task 3.2)
6. ✅ Create deployment scripts (Task 4.1)

**Nice-to-Have:**
7. ✅ Optional enhancements (Category 5)

---

## Tracking

**Started:** 2025-11-06
**Target Completion:** TBD (based on priority)
**Owner:** Development Team

**Update This Document:**
- Mark tasks as ✅ Complete when finished
- Add new tasks as discovered
- Update effort estimates based on actual time

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Status:** 📋 Active Tracking
