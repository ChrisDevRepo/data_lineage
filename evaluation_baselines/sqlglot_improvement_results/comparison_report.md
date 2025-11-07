# SQLGlot Improvement Analysis Report

**Date:** 2025-11-07 13:46:22
**Total SPs Analyzed:** 349

---

## Executive Summary

| Metric | Baseline (No Cleaning) | Improved (With Cleaning) | Change |
|--------|------------------------|--------------------------|---------|
| **SQLGlot Success Rate** | 187/349 (53.6%) | 284/349 (81.4%) | **+27.8%** |
| **SQLGlot Failure Rate** | 162/349 (46.4%) | 65/349 (18.6%) | -27.8% |

### Key Findings

✅ **SUCCESS**: SQL Cleaning Engine improved SQLGlot success rate by **27.8%**

- **102 SPs** went from FAILURE → SUCCESS
- **5 SPs** went from SUCCESS → FAILURE (REGRESSIONS)

---

## Detailed Statistics

### SPs That Improved (102)

- **STAGING_CADENCE.spLoadReconciliation_Case4.5**: 0 → 1 tables
- **STAGING_CADENCE.spLoadCadenceExtractTaskCountry**: 0 → 2 tables
- **CONSUMPTION_STARTUP.spLoadIpRedsReview**: 0 → 3 tables
- **CONSUMPTION_PRIMA.spLoadSiteEvents_DurationByDayPlanned**: 0 → 3 tables
- **STAGING_CADENCE.TRIAL_spLoadFinalCountryReallocateTS_Case4**: 0 → 1 tables
- **STAGING_CADENCE.TRIAL_spLoadFinalCountryReallocateTS_NoCountry**: 0 → 1 tables
- **CONSUMPTION_STARTUP.spLoadSite**: 0 → 3 tables
- **CONSUMPTION_FINANCE.spLoadFact_SAP_Sales_Details**: 0 → 1 tables
- **CONSUMPTION_PRIMA_2.spLoadEnrollmentPlanSitesHistory**: 0 → 1 tables
- **CONSUMPTION_FINANCE.spLoadSAPSalesRetainerDetailsMetrics**: 0 → 3 tables
- ... and 92 more

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
| ❌ Fail | ✅ Success | 102 | 29.2% |
| ❌ Fail | ❌ Fail | 60 | 17.2% |

---

## Conclusion

✅ **RECOMMENDED**: Deploy SQL Cleaning Engine to production
- Improves SQLGlot success rate by 27.8%
- 102 SPs benefit from cleaning
- ⚠️ Review 5 regressions before deployment
