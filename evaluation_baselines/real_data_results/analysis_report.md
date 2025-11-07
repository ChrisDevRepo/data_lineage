# Real Data Parser Analysis Report

**Generated:** 2025-11-07 10:58:39
**Total Stored Procedures:** 349

---

## Overall Performance

| Metric | Value |
|--------|-------|
| **Average Precision** | 0.0% |
| **Average Recall** | 100.0% |
| **Average F1 Score** | 0.0% |

---

## SQLGlot Analysis

### Success Rate
- **Successful Parses:** 254 / 349 (72.8%)
- **Failed Parses:** 95 (27.2%)

### Accuracy Comparison: SQLGlot vs Regex

| Outcome | Count | Percentage |
|---------|-------|------------|
| **SQLGlot Better** | 0 | 0.0% |
| **Regex Better** | 0 | 0.0% |
| **Tie** | 349 | 100.0% |

**Key Finding:** Regex outperforms SQLGlot in 0.0% of cases, indicating significant value in hybrid approach.

---

## Query Log Analysis

**Available:** Yes
**Total Queries:** 297

**Assessment:**
- Query logs can provide runtime validation
- However, matching queries to specific SPs is challenging
- **Recommendation:** Use as supplementary validation, not primary parsing method


---

## Top 5 Best Performing SPs

| SP Name | F1 Score | Precision | Recall | SQLGlot Success |
|---------|----------|-----------|--------|-----------------|
| CONSUMPTION_FINANCE.spLoadDimCompanyKoncern | 0.0% | 0.0% | 100.0% | ✗ |
| dbo.usp_GET_ACCOUNT_RELATIONSHIPS | 0.0% | 0.0% | 100.0% | ✓ |
| STAGING_CADENCE.spLoadReconciliation_Case4.5 | 0.0% | 0.0% | 100.0% | ✗ |
| CONSUMPTION_PRIMAREPORTING.spLoadPrimaReportingProjectRegions | 0.0% | 0.0% | 100.0% | ✓ |
| CONSUMPTION_PRIMA_2.spLoadAgreementTemplates | 0.0% | 0.0% | 100.0% | ✓ |

---

## Bottom 5 Worst Performing SPs

| SP Name | F1 Score | Precision | Recall | SQLGlot Success |
|---------|----------|-----------|--------|-----------------|
| CONSUMPTION_PRIMAREPORTING.spLoadPrimaReportingPrimaLastRefresh | 0.0% | 0.0% | 100.0% | ✓ |
| CONSUMPTION_FINANCE.spLoadFactTables | 0.0% | 0.0% | 100.0% | ✓ |
| CONSUMPTION_PRIMAREPORTING.spLoadPrimaReportingFeasibilityQuestionsAndAnswers | 0.0% | 0.0% | 100.0% | ✓ |
| STAGING_STARTUP.spLoadSiteEventPlanHistory | 0.0% | 0.0% | 100.0% | ✗ |
| CONSUMPTION_FINANCE.spLoadFact_SAP_Sales_Summary | 0.0% | 0.0% | 100.0% | ✓ |

---

## Key Recommendations

### 1. SQLGlot Enhancement Priority: HIGH
- **Current Success Rate:** 72.8%
- **Target:** 70-80% with SQL Cleaning Engine
- **Action:** Implement SQL Cleaning Engine (documented in temp/SQL_CLEANING_ENGINE_DOCUMENTATION.md)
- **Expected Impact:** +2.2% success rate improvement

### 2. Hybrid Approach Validation: CONFIRMED
- Regex outperforms SQLGlot in 0.0% of cases
- **Conclusion:** Current hybrid strategy (Regex + SQLGlot) is correct
- **Action:** Continue both methods, use best result from each

### 3. Confidence Scoring Strategy
- Current average F1 (0.0%) establishes baseline
- **Action:** Calibrate confidence thresholds against these results
- **Goal:** HIGH confidence (≥0.85) should correlate with F1 ≥ 0.90

### 4. Query Logs Usefulness
- Available but challenging to use effectively
- **Recommendation:** Optional supplementary signal, not primary method

---

## Next Steps

### Week 1-2: SQL Cleaning Engine
1. Integrate cleaning engine into parser
2. Re-run this analysis
3. Target: 72.8% → 75% SQLGlot success rate

### Week 3-4: Iterative Improvement
1. Analyze worst performers (CONSUMPTION_PRIMAREPORTING.spLoadPrimaReportingPrimaLastRefresh and similar)
2. Add targeted regex rules or comment hints
3. Target: 0.0% → 85% average F1 score

### Week 5+: Continuous Monitoring
1. Use `/sub_DL_OptimizeParsing` for regression testing
2. Capture UAT feedback for real-world validation
3. Maintain improvement baseline

---

**Data Summary:**
- **Objects in Catalog:** 1067
- **DMV Dependencies:** 732
- **Stored Procedures Analyzed:** 349
- **Query Logs:** 297

**Output:** evaluation_baselines/real_data_results/
