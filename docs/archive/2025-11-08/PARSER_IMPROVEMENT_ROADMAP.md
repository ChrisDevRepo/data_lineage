# Parser Improvement Roadmap

**Based on Real Data Analysis - 2025-11-07**
**Status:** Ready for Implementation
**Priority:** HIGH

---

## Executive Summary

Based on comprehensive analysis of real production data (349 stored procedures, 137 views, 1,067 total objects), we have identified:

1. **✅ SQLGlot performs well** - 72.8% success rate, near target
2. **✅ Validation strategy validated** - Catalog validation + UAT feedback is correct approach
3. **✅ Ground truth available for views** - 137 views with 436 DMV dependencies
4. **⚠️ Ground truth missing for SPs** - DMV limitations require alternative validation
5. **✅ All Phase 1 & 2 work validated** - UAT feedback and comment hints are essential

**Key Finding:** DMV dependencies only track Views, not Stored Procedures. This clarifies our validation strategy.

---

## Implementation Phases

### Phase 3: View Evaluation Baseline (Week 1)
**Status:** ⏳ Ready to Start
**Priority:** HIGH
**Goal:** Establish true parser accuracy baseline using 137 views with DMV ground truth

#### Deliverables

1. **View Evaluation Script**
   - Location: `evaluation_baselines/view_evaluation.py`
   - Function: Evaluate parser on 137 views with DMV dependencies
   - Metrics: Precision, Recall, F1 Score per view
   - Output: `evaluation_baselines/view_results/`

2. **Baseline Results**
   - Location: `evaluation_baselines/view_baseline_20251107.json`
   - Content: Detailed precision/recall for each view
   - Purpose: Regression testing for future parser changes

3. **View Analysis Report**
   - Location: `evaluation_baselines/view_results/VIEW_ANALYSIS_REPORT.md`
   - Content: Detailed findings, accuracy metrics, failure analysis
   - Audience: Development team

#### Success Criteria
- [ ] View evaluation script created and tested
- [ ] Baseline results generated for all 137 views
- [ ] Average F1 score ≥ 80%
- [ ] Failure patterns documented
- [ ] Regression testing process established

#### Implementation Steps

```bash
# 1. Create view evaluation script
python evaluation_baselines/view_evaluation.py

# 2. Generate baseline
python evaluation_baselines/view_evaluation.py --create-baseline view_baseline_20251107

# 3. Review results
cat evaluation_baselines/view_results/VIEW_ANALYSIS_REPORT.md
```

#### Dependencies
- Real data parquet files (already available in temp/)
- Parser infrastructure (already implemented)
- DuckDB workspace (already configured)

---

### Phase 4: SQL Cleaning Engine Integration (Week 2-3)
**Status:** ⏳ Ready to Start (Engine Already Developed!)
**Priority:** HIGH
**Goal:** Improve SQLGlot success rate from 72.8% → 75-80%

#### Background

SQL Cleaning Engine was developed in Phase 2 (`lineage_v3/parsers/sql_cleaning_rules.py`) but not yet integrated into main parser.

**Test Results:**
- Test SP: `spLoadFactLaborCostForEarnedValue` (14,671 bytes)
- SQLGlot success (before cleaning): 0%
- SQLGlot success (after cleaning): 100%
- Processing time: <50ms
- Accuracy: 100% vs golden record

#### Deliverables

1. **Parser Integration**
   - File: `lineage_v3/parsers/quality_aware_parser.py`
   - Change: Add SQL cleaning step before SQLGlot parsing
   - Feature flag: `ENABLE_SQL_CLEANING` (default: True)

2. **Before/After Evaluation**
   - Run view evaluation BEFORE integration
   - Run view evaluation AFTER integration
   - Compare SQLGlot success rate
   - Compare F1 scores
   - Document impact

3. **Performance Testing**
   - Measure parsing time before/after
   - Ensure <100ms overhead per SP
   - Document performance impact

#### Success Criteria
- [ ] SQL Cleaning Engine integrated into parser
- [ ] SQLGlot success rate ≥ 75%
- [ ] Zero regressions on view evaluation
- [ ] Average confidence score increase ≥ 0.10
- [ ] Performance overhead <100ms per SP

#### Implementation Steps

```bash
# 1. Create feature branch
git checkout -b claude/integrate-sql-cleaning-engine

# 2. Integrate cleaning engine
# Edit: lineage_v3/parsers/quality_aware_parser.py
# Add: from lineage_v3.parsers.sql_cleaning_rules import RuleEngine, get_default_rules
# Modify: _sqlglot_parse() to clean SQL before parsing

# 3. Run before/after evaluation
python evaluation_baselines/view_evaluation.py --baseline view_baseline_20251107
# (Record results)

# 4. Commit and test
git add lineage_v3/parsers/quality_aware_parser.py
git commit -m "Integrate SQL Cleaning Engine for improved SQLGlot success rate"

# 5. Run full evaluation
python evaluation_baselines/view_evaluation.py --baseline view_baseline_20251107 --compare

# 6. Document results
# Update: temp/SQL_CLEANING_ENGINE_INTEGRATION_RESULTS.md
```

#### Dependencies
- Phase 3 complete (view baseline established)
- SQL Cleaning Engine (already implemented)
- View evaluation script (from Phase 3)

---

### Phase 5: Catalog Validation Analysis (Week 3-4)
**Status:** ⏳ Pending Phase 3 & 4
**Priority:** MEDIUM
**Goal:** Validate that catalog validation rate correlates with actual accuracy

#### Hypothesis

**High catalog validation rate (≥90%) should correlate with high F1 score (≥80%)**

Since we can measure true F1 scores on views, we can validate this hypothesis and then apply it to stored procedures.

#### Deliverables

1. **Correlation Analysis Script**
   - Location: `evaluation_baselines/catalog_correlation_analysis.py`
   - Function: Analyze catalog validation vs F1 score for views
   - Output: Correlation coefficient, scatter plot, regression line

2. **Analysis Report**
   - Location: `evaluation_baselines/CATALOG_VALIDATION_ANALYSIS.md`
   - Content: Correlation findings, confidence threshold validation
   - Recommendation: Adjust confidence model weights if needed

#### Success Criteria
- [ ] Correlation coefficient ≥ 0.7 (strong correlation)
- [ ] HIGH confidence (≥0.85) → ≥90% catalog validation
- [ ] MEDIUM confidence (0.75-0.84) → 75-90% catalog validation
- [ ] LOW confidence (<0.75) → <75% catalog validation

#### Implementation Steps

```python
# Pseudocode for correlation analysis
for view in views_with_ground_truth:
    parsed_tables = parser.parse(view.definition)
    catalog_rate = catalog_validation_rate(parsed_tables, catalog)
    f1_score = calculate_f1(parsed_tables, ground_truth)

    data.append((catalog_rate, f1_score))

correlation = calculate_pearson_correlation(data)
# Expected: correlation ≥ 0.7
```

---

### Phase 6: UAT Feedback System Deployment (Week 4-5)
**Status:** ⏳ Pending (System Ready, Not Deployed)
**Priority:** HIGH
**Goal:** Deploy UAT feedback system as primary SP validation method

#### Background

UAT feedback system was implemented in Phase 1 but not yet deployed to production environment.

**System Components:**
- JSON schema: `temp/uat_feedback/schema.json`
- Capture tool: `temp/uat_feedback/capture_feedback.py`
- Dashboard: `temp/uat_feedback/dashboard.py`
- User guide: `temp/uat_feedback/README.md`

#### Deliverables

1. **Production Deployment**
   - Move UAT feedback system from temp/ to production location
   - Set up automated feedback processing
   - Configure notifications for new feedback

2. **User Training**
   - Train 3-5 users on feedback capture tool
   - Provide examples of good feedback reports
   - Establish feedback review process

3. **Integration with Parser**
   - Implement UAT validation flag in confidence scoring
   - Track which SPs have been UAT validated
   - Boost confidence for validated SPs

4. **Monitoring Dashboard**
   - Weekly feedback summary
   - Bug fix turnaround time
   - Regression test generation status

#### Success Criteria
- [ ] ≥5 feedback reports submitted in first month
- [ ] ≥3 regression tests generated from feedback
- [ ] Bug fix turnaround time <48 hours
- [ ] User satisfaction ≥8/10

#### Implementation Steps

```bash
# 1. Move to production location
mv temp/uat_feedback/ lineage_v3/uat_feedback/

# 2. Update imports and paths
# Edit: lineage_v3/uat_feedback/*.py
# Update all temp/ references to lineage_v3/uat_feedback/

# 3. Integrate with parser
# Edit: lineage_v3/parsers/quality_aware_parser.py
# Add: Check for UAT validation flag in confidence calculation

# 4. Deploy to production
# Set up cron job for automated processing
# Configure email notifications

# 5. Train users
# Schedule training session
# Provide documentation and examples
```

---

### Phase 7: Continuous Improvement (Week 6+)
**Status:** ⏳ Ongoing
**Priority:** MEDIUM
**Goal:** Iterative refinement based on real-world usage

#### Activities

1. **Weekly UAT Review**
   - Review new feedback submissions
   - Prioritize bug fixes
   - Generate regression tests
   - Update parser rules

2. **Monthly Regression Testing**
   - Run view evaluation against baseline
   - Ensure zero regressions
   - Document improvements
   - Update baseline if needed

3. **Quarterly Confidence Calibration**
   - Analyze confidence score distribution
   - Calculate false confidence rate
   - Adjust multi-factor weights if needed
   - Document changes

4. **Documentation Updates**
   - Keep docs in sync with code
   - Add new examples
   - Update troubleshooting guide
   - Archive old versions

---

## Success Metrics Tracking

### Parser Performance

| Metric | Baseline | Current | Target | Status |
|--------|----------|---------|--------|--------|
| SQLGlot Success Rate | 72.8% | 72.8% | 75-80% | ⏳ Pending Phase 4 |
| View Average F1 Score | TBD | TBD | ≥80% | ⏳ Pending Phase 3 |
| SP Catalog Validation | TBD | TBD | ≥85% | ⏳ Pending Phase 5 |
| UAT Bug Rate (HIGH conf) | TBD | TBD | <5% | ⏳ Pending Phase 6 |

### Confidence Scoring

| Metric | Target | Status |
|--------|--------|--------|
| HIGH conf → catalog valid | ≥90% | ⏳ Pending Phase 5 |
| HIGH conf → UAT accurate | <5% bug rate | ⏳ Pending Phase 6 |
| View confidence calibration | F1≥80% when conf≥0.85 | ⏳ Pending Phase 3 |

---

## Risk Assessment

### High Risk

**Risk:** View evaluation reveals poor parser accuracy (<70% F1)
**Mitigation:**
- Already have SQL Cleaning Engine ready to deploy
- Can add targeted regex rules based on failure analysis
- Comment hints available for edge cases
**Likelihood:** Low (based on Phase 2 validation testing)

### Medium Risk

**Risk:** Catalog validation does not correlate with actual accuracy
**Mitigation:**
- Use UAT feedback as primary validation (already implemented)
- Adjust confidence model to rely more on UAT validation
- Document limitations in user guide
**Likelihood:** Low (catalog validation is strong signal)

### Low Risk

**Risk:** Users do not submit UAT feedback
**Mitigation:**
- Integrate feedback tool into workflow
- Provide incentives for feedback
- Make tool as easy as possible (<2 minutes)
**Likelihood:** Medium (requires user training and adoption)

---

## Timeline

```
Week 1: Phase 3 - View Evaluation Baseline
Week 2-3: Phase 4 - SQL Cleaning Engine Integration
Week 3-4: Phase 5 - Catalog Validation Analysis
Week 4-5: Phase 6 - UAT Feedback Deployment
Week 6+: Phase 7 - Continuous Improvement
```

**Total Duration:** 6 weeks to full deployment
**Critical Path:** Phase 3 → Phase 4 → Phase 5 → Phase 6

---

## Next Immediate Actions

### This Week

1. **Create view evaluation script** (`evaluation_baselines/view_evaluation.py`)
2. **Run baseline evaluation** on 137 views with DMV ground truth
3. **Document findings** in `VIEW_ANALYSIS_REPORT.md`
4. **Establish regression testing process** with `/sub_DL_OptimizeParsing`

### Next Week

1. **Integrate SQL Cleaning Engine** into `quality_aware_parser.py`
2. **Run before/after comparison** on view evaluation
3. **Measure SQLGlot success rate improvement**
4. **Document integration results**

---

## Questions for Review

1. **Should we prioritize catalog validation analysis before SQL Cleaning Engine integration?**
   - Recommendation: No - SQL Cleaning Engine integration is straightforward and high-impact

2. **Should we deploy UAT feedback system before completing technical validation?**
   - Recommendation: No - Establish view evaluation baseline first, then deploy UAT

3. **Should we create a separate confidence model for views vs SPs?**
   - Recommendation: No - Use same model, but validate calibration separately

---

**Last Updated:** 2025-11-07
**Next Review:** After Phase 3 completion
**Owner:** Development Team
**Status:** ✅ Ready for Implementation
