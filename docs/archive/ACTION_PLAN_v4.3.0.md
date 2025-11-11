# Action Plan: UAT Readiness - Iterative Bug Fixing

**Date:** 2025-11-11 22:35 UTC
**Approach:** Deep research → Systematic bug fixing → Testing → Documentation

---

## Phase 1: Root Cause Analysis ✅

### Issue 1: DDL Storage ✅ CONFIRMED WORKING
**Status:** ✅ **WORKING AS DESIGNED**
- JSON file: 453 KB (NO ddl_text field)
- DDL fetched on-demand via `/api/ddl/{object_id}`
- Tested successfully for object_id 715842
- Performance optimization working correctly

---

## Phase 2: Critical Bug Fixes (In Progress)

### Issue 2: Phantom Objects Not Exported (P0 - CRITICAL)
**Problem:** 233 phantoms in DB, 0 in frontend JSON
**Root Cause:** Need to investigate `InternalFormatter._fetch_objects()`

**Action Items:**
1. ✅ Verify phantom_objects table has data (233 records confirmed)
2. ⏳ Debug InternalFormatter UNION query execution
3. ⏳ Check if phantoms are filtered during graph building
4. ⏳ Verify phantom_references table for dependency data
5. ⏳ Re-export and verify phantoms appear in JSON

**Hypothesis:** The `_build_lineage_graph()` method may filter out nodes without dependencies

---

### Issue 3: System Schema Filtering (P0 - CRITICAL)
**Problem:** sys, dummy, dbo CTEs included as phantoms
**Examples Found:**
- dbo.cte, dbo.cte_result, dbo.cte1 (CTEs)
- dbo.t, dbo.ParsedData (temp tables)
- INFORMATION_SCHEMA.COLUMNS (system table)

**Action Items:**
1. ⏳ Add exclusion patterns to phantom creation logic
2. ⏳ Define comprehensive exclusion list
3. ⏳ Test exclusion on existing data
4. ⏳ Re-process parquet files with filtering

**Exclusion Patterns:**
```python
EXCLUDED_SCHEMAS = ['sys', 'dummy', 'information_schema']
EXCLUDED_DBO_PATTERNS = [
    r'^cte',  # CTEs
    r'^CTE',
    r'^[a-z]$',  # Single letter tables
    r'^[#@]',  # Temp tables/variables
    r'ParsedData',
    r'PartitionedCompany',
]
```

---

### Issue 4: Frontend Performance (P0 - UAT BLOCKER)
**Problem:** Browser crashes with 1,300 nodes
**Error:** "Navigation failed because page crashed!"

**Research Findings:**

**React Flow Performance Limits:**
- Official stress test: 100-500 nodes recommended
- 1,000+ nodes: Performance degradation
- 10,000 nodes: Requires major optimization

**Alternative Libraries:**
- **Sigma.js:** Best for 10K+ nodes (WebGL rendering)
- **Cytoscape.js:** Good for 5K nodes (WebGL support)
- **Vis.js:** Worst performance (20-40x slower)

**Action Items - Quick Fix (UAT):**
1. ⏳ Add node count limit (500 visible nodes)
2. ⏳ Implement schema/type filtering UI
3. ⏳ Add "X nodes hidden" indicator
4. ⏳ Cache layout calculations
5. ⏳ Test with limited dataset

**Action Items - Long Term (Post-UAT):**
1. Evaluate Sigma.js migration (WebGL)
2. Implement graph clustering/grouping
3. Add virtualization
4. Progressive loading strategy

---

### Issue 5: Real Functions Missing
**Problem:** 0 Functions in objects table
**Finding:** All 78 "Functions" are phantoms (negative IDs)

**Action Items:**
1. ⏳ Verify parquet files contain Function metadata
2. ⏳ Check Function filtering in parquet loader
3. ⏳ Add Functions to objects table query
4. ⏳ Re-upload if Functions exist in source

---

## Phase 3: Testing Strategy

### Unit Tests
1. Test phantom export with known data
2. Test schema exclusion patterns
3. Test node count limiting
4. Test on-demand DDL fetching

### Integration Tests
1. Full pipeline: Upload → Process → Export
2. Verify phantom count matches expected
3. Verify no system schemas
4. Verify frontend renders without crash

### Playwright Tests
1. Run after fixes complete
2. Expected pass rate: 70-80% (63-72 tests)
3. Focus on: Legend, Node types, Data loading

---

## Phase 4: Documentation Updates

### Files to Update:
1. ✅ UAT_READINESS_REPORT.md (created)
2. ✅ ACTION_PLAN.md (this file)
3. ⏳ BUGS.md (add new issues)
4. ⏳ IMPLEMENTATION_SUMMARY.md (update status)
5. ⏳ PERFORMANCE_OPTIMIZATION.md (create)

---

## Execution Timeline

**Iteration 1: Investigation (30 min)**
- ✅ Verify DDL storage
- ⏳ Debug phantom export
- ⏳ Identify schema filtering location
- ⏳ Measure performance baseline

**Iteration 2: Core Fixes (60 min)**
- ⏳ Fix phantom export bug
- ⏳ Add schema filtering
- ⏳ Implement node limiting

**Iteration 3: Testing (30 min)**
- ⏳ Re-upload parquet files
- ⏳ Verify phantoms exported
- ⏳ Verify no system schemas
- ⏳ Test frontend performance

**Iteration 4: Validation (30 min)**
- ⏳ Run Playwright tests
- ⏳ Manual UAT scenario testing
- ⏳ Performance measurements
- ⏳ Documentation updates

**Total Estimated Time:** 2.5 hours

---

## Success Criteria

### Must Have (Go/No-Go):
- [ ] Phantoms exported to JSON (233 expected)
- [ ] System schemas filtered (0 sys/dummy/cte)
- [ ] Frontend renders without crash
- [ ] Question mark badges visible
- [ ] Diamond shapes for Functions
- [ ] Orange dotted phantom edges

### Should Have:
- [ ] Playwright tests 70%+ passing
- [ ] Performance under 5 seconds
- [ ] Real Functions loaded
- [ ] Node count indicator

---

## Current Status

**Phase:** 1 (Root Cause Analysis)
**Progress:** 20% complete
**Blockers:** None
**Next:** Debug phantom export in InternalFormatter

---

**Last Updated:** 2025-11-11 22:35 UTC
**Updated By:** Automated bug fixing process
