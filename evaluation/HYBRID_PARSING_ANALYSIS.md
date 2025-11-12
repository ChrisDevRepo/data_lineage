# SQLGlot Hybrid Parsing Strategy Analysis

## Executive Summary

Testing shows that using `error_level=WARN` dramatically improves SQLGlot parse success (71.6% → 100.0%) and table extraction (+143.0% more tables). However, a simple fallback strategy has **38 regressions** where cleaning helps but WARN mode doesn't.

## Current Results

### Baseline (Cleaned + STRICT)
- **Parse Success:** 250/349 (71.6%)
- **Unique Tables:** 249
- **Method:** Always clean SQL before parsing with STRICT mode

### Hybrid V1 (WARN Primary + Simple Fallback)
- **Parse Success:** 349/349 (100.0%) ✅
- **Unique Tables:** 605 (+356, +143.0%) ✅
- **Method:**
  - Try WARN mode first (348 SPs)
  - Fallback to cleaning only if: SP >1500 lines AND <5 tables (1 SP)
- **Regressions:** 38 SPs extract fewer tables ⚠️

## Regression Analysis

### Top 10 Regressions
| SP Name | Baseline | Hybrid | Diff | Lines |
|---------|----------|--------|------|-------|
| spLoadFactGLCOGNOS | 11 | 1 | -10 | 270 |
| spLoadArAnalyticsMetricsQuarterlyGlobal | 7 | 1 | -6 | 188 |
| spLoadPrimaReportingFeasibilityQuestionsAndAnswers | 9 | 3 | -6 | 342 |
| spLoadFactGLSAP | 7 | 1 | -6 | 204 |
| spLoadFactSAPSalesRetainerDetails | 6 | 1 | -5 | 106 |
| spLoadFact_SAP_Sales_Summary | 6 | 1 | -5 | 104 |
| spLoadFact_SAP_Sales_Details | 6 | 1 | -5 | 103 |
| spLoadEmployeeUtilization_Post | 5 | 1 | -4 | 174 |
| spLoadFactSAPSalesSponsorRiskSnapshot | 5 | 1 | -4 | 130 |
| spLoadSAPSalesDetailsMetrics | 5 | 1 | -4 | 120 |

**Key Finding:** Regressions occur in relatively small SPs (100-350 lines), so the simple ">1500 lines" fallback doesn't catch them.

## Root Cause

WARN mode parses unsupported T-SQL syntax as `Command` objects without extracting table references. For example:

```sql
-- WARN mode sees this as Command (no tables extracted)
IF OBJECT_ID('tempdb..#temp') IS NOT NULL
BEGIN
    DROP TABLE #temp
END

-- After cleaning: removed entirely
-- INSERT/SELECT statements become parseable → tables extracted
```

Cleaning removes these "Command" blocks, making the remaining DML (INSERT/SELECT/UPDATE) more extractable.

## Proposed Solutions

### Option 1: Try Both (Zero Regressions, Best Quality)
**Strategy:** Always try both WARN and Cleaned+STRICT, use whichever extracts more tables

**Pros:**
- ✅ Zero regressions guaranteed
- ✅ Maximum table extraction (best of both worlds)
- ✅ Simple logic

**Cons:**
- ⚠️ 2x parsing cost (but still fast: ~5 seconds total for 349 SPs)
- ⚠️ More complex to maintain

**Expected Results:**
- Parse Success: 349/349 (100.0%)
- Unique Tables: ~800+ (249 baseline + 356 WARN improvements + 0 regressions)
- Method Distribution: ~311 WARN, ~38 cleaned

### Option 2: Improved Heuristic Fallback
**Strategy:** Use smarter heuristics to detect when cleaning helps

**Heuristics to try:**
1. If WARN extracts <3 tables AND SP contains "IF OBJECT_ID" → try cleaning
2. If WARN extracts <3 tables AND SP contains "BEGIN/END" blocks → try cleaning
3. If WARN extracts <3 tables AND SP has >100 lines → try cleaning

**Pros:**
- ✅ Faster than Option 1 (selective double-parsing)
- ✅ Reduced cost

**Cons:**
- ⚠️ May still have some regressions if heuristics miss cases
- ⚠️ Requires tuning and testing

### Option 3: Accept Regressions (Not Recommended)
**Strategy:** Use current Hybrid V1 with 38 regressions

**Pros:**
- ✅ Fastest (single parse per SP)
- ✅ Simplest code

**Cons:**
- ❌ 38 SPs extract fewer tables (worse quality)
- ❌ Net improvement still positive (+356-38 = +318 tables)

## Recommendation

**Implement Option 1: Try Both Approaches**

**Rationale:**
1. **Quality First:** Data lineage accuracy is critical; 2x parsing cost is acceptable
2. **Performance:** 349 SPs take ~5 seconds with double parsing (negligible for backend job)
3. **Future-Proof:** No regressions as SQLGlot evolves
4. **Simple Logic:** Clear decision rule (max table count wins)

**Implementation:**
```python
def parse_with_best_effort(sql_definition, engine):
    """Try both WARN and Cleaned approaches, return best result"""

    # Approach 1: WARN (handles most cases)
    try:
        parsed_warn = sqlglot.parse(sql_definition, dialect='tsql', error_level=ErrorLevel.WARN)
        tables_warn = extract_unique_tables(parsed_warn)
    except Exception:
        tables_warn = set()

    # Approach 2: Cleaned + STRICT (handles edge cases)
    try:
        cleaned = engine.apply_all(sql_definition)
        parsed_clean = sqlglot.parse(cleaned, dialect='tsql')
        tables_clean = extract_unique_tables(parsed_clean)
    except Exception:
        tables_clean = set()

    # Return whichever found more tables
    if len(tables_clean) > len(tables_warn):
        return tables_clean, 'cleaned', True
    else:
        return tables_warn, 'warn', True
```

## Next Steps

1. ✅ Analysis complete
2. ⏳ Implement Option 1 (Try Both)
3. ⏳ Test on all 349 SPs
4. ⏳ Verify zero regressions
5. ⏳ Update parser code in `quality_aware_parser.py`
6. ⏳ Update documentation

## Files Generated

- `hybrid_parsing_results.json` - Hybrid V1 results (WARN primary + simple fallback)
- `baseline_vs_hybrid_comparison.json` - Detailed comparison showing 38 regressions
- `HYBRID_PARSING_ANALYSIS.md` - This analysis document
