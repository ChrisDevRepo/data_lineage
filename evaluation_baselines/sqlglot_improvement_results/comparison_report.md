# SQLGlot Improvement Analysis Report

**Date:** 2025-11-07 12:31:49
**Total SPs Analyzed:** 349

---

## Executive Summary

| Metric | Baseline (No Cleaning) | Improved (With Cleaning) | Change |
|--------|------------------------|--------------------------|---------|
| **SQLGlot Success Rate** | 187/349 (53.6%) | 282/349 (80.8%) | **+27.2%** |
| **SQLGlot Failure Rate** | 162/349 (46.4%) | 67/349 (19.2%) | -27.2% |

### Key Findings

✅ **SUCCESS**: SQL Cleaning Engine improved SQLGlot success rate by **27.2%**

- **100 SPs** went from FAILURE → SUCCESS
- **5 SPs** went from SUCCESS → FAILURE (REGRESSIONS)

---

## Detailed Statistics

### SPs That Improved (100)

- **STAGING_CADENCE.spLoadCadenceExtractTaskCountry**: 0 → 2 tables
- **CONSUMPTION_STARTUP.spLoadIpRedsReview**: 0 → 3 tables
- **CONSUMPTION_PRIMA.spLoadSiteEvents_DurationByDayPlanned**: 0 → 3 tables
- **STAGING_CADENCE.TRIAL_spLoadFinalCountryReallocateTS_Case4**: 0 → 1 tables
- **STAGING_CADENCE.TRIAL_spLoadFinalCountryReallocateTS_NoCountry**: 0 → 1 tables
- **CONSUMPTION_STARTUP.spLoadSite**: 0 → 3 tables
- **CONSUMPTION_FINANCE.spLoadFact_SAP_Sales_Details**: 0 → 1 tables
- **CONSUMPTION_PRIMA_2.spLoadEnrollmentPlanSitesHistory**: 0 → 1 tables
- **CONSUMPTION_FINANCE.spLoadSAPSalesRetainerDetailsMetrics**: 0 → 3 tables
- **Consumption_FinanceHub.spLoadFactGLCOGNOS**: 0 → 13 tables
- ... and 90 more

### SPs That Regressed (5)

- **CONSUMPTION_PRIMAREPORTING.spLoadPrimaReportingSiteEventsWithAllocations**: 1 → 0 tables
- **CONSUMPTION_PRIMADATAMART.LogMessage**: 1 → 0 tables
- **CONSUMPTION_PRIMAREPORTING_2.spLoadPrimaReportingSiteEventsWithAllocations**: 1 → 0 tables
- **CONSUMPTION_PRIMAREPORTING_2.spLoadPrimaReportingSubjectEvents**: 1 → 0 tables
- **CONSUMPTION_PRIMAREPORTING.spLoadPrimaReportingSubjectEvents**: 1 → 0 tables

---

## Success Matrix

| Baseline | Improved | Count | Percentage |
|----------|----------|-------|------------|
| ✅ Success | ✅ Success | 182 | 52.1% |
| ✅ Success | ❌ Fail | 5 | 1.4% |
| ❌ Fail | ✅ Success | 100 | 28.7% |
| ❌ Fail | ❌ Fail | 62 | 17.8% |

---

## Conclusion

✅ **RECOMMENDED**: Deploy SQL Cleaning Engine to production
- Improves SQLGlot success rate by 27.2%
- 100 SPs benefit from cleaning
- ⚠️ Review 5 regressions before deployment
