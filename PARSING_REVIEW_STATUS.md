# Parsing Review & Improvement Initiative

**Status:** ✅ Phase 1 & 2 Complete - Ready for Phase 3
**Started:** 2025-11-06
**Lead:** Claude Code Agent
**Objective:** Strengthen parsing pipeline and confidence scoring based on deep architecture review

---

## 📍 Quick Links

| Document | Purpose | Location |
|----------|---------|----------|
| **This Document** | Entry point, status, tasks | `/PARSING_REVIEW_STATUS.md` |
| **Detailed Action Plan** | Complete implementation plan | [`/temp/parsing_review/11_REVISED_ACTION_PLAN.md`](temp/parsing_review/11_REVISED_ACTION_PLAN.md) |
| **Analysis Reports** | Architecture review findings | [`/temp/parsing_review/`](temp/parsing_review/) |
| **UAT Feedback System** | Capture & test generation | [`/temp/uat_feedback/`](temp/uat_feedback/) |
| **Architecture Docs** | Production documentation | `/docs/PARSING_ARCHITECTURE.md` (coming Week 4) |

---

## 🎯 Scope & Objectives

### What We're Improving
1. **UAT Feedback Loop** - Structured bug capture → regression tests
2. **Comment Hints** - Developer-provided dependency hints for edge cases
3. **Confidence Scoring** - Multi-factor model (accuracy vs. agreement)
4. **Documentation** - Single source of truth, no black box

### What We're NOT Changing
- ✅ SQLGlot stays (best parser option)
- ✅ Query logs stay optional (security concerns)
- ✅ Current preprocessing approach (main block parsing works well)
- ✅ DMV baseline strategy (confidence 1.0 for views/functions)

---

## 📊 Current Status

### ✅ Completed (2025-11-06)
- [x] Deep architecture review
- [x] SQLGlot limitations analysis
- [x] Process flow analysis with failure modes
- [x] Confidence scoring model analysis
- [x] Revised action plan based on user decisions

**Analysis documents:** See [`/temp/parsing_review/`](temp/parsing_review/) for:
- `00_EXECUTIVE_SUMMARY.md` - Key findings
- `01_SQLGLOT_LIMITATIONS_ANALYSIS.md` - SQLGlot capability assessment
- `02_PROCESS_FLOW_ANALYSIS.md` - End-to-end flow with failure modes
- `11_REVISED_ACTION_PLAN.md` - 4-week implementation plan

### ✅ Completed (Phase 1 - Week 1 - 2025-11-06)
- [x] **Phase 1: UAT Feedback Capture System**
  - [x] JSON schema for feedback reports
  - [x] CLI capture tool (`temp/uat_feedback/capture_feedback.py`)
  - [x] Regression test generator
  - [x] Feedback dashboard
  - [x] User guide (`temp/uat_feedback/README.md`)

**Status:** All Phase 1 deliverables complete and tested

### ✅ Completed (Phase 2 - Week 2 - 2025-11-06)
- [x] **Phase 2: Comment Hints Parser**
  - [x] Created `lineage_v3/parsers/comment_hints_parser.py`
  - [x] Integrated into `quality_aware_parser.py`
  - [x] Added confidence boost logic (+0.10)
  - [x] Created user documentation (`docs/PARSING_USER_GUIDE.md`)
  - [x] Created developer guide (`docs/COMMENT_HINTS_DEVELOPER_GUIDE.md`)
  - [x] Added comprehensive tests (10/10 passing)

**Status:** All Phase 2 deliverables complete and tested

### ⏳ Planned (Weeks 3-4)
- [ ] **Week 3:** Multi-factor confidence scoring redesign
- [ ] **Week 4:** Consolidated architecture documentation

---

## 🔥 Key Findings from Review

### Critical Issues Identified
1. **Confidence measures agreement, not accuracy**
   - Current: High confidence (0.85) = regex and SQLGlot agree
   - Problem: Both could be wrong consistently
   - Fix: Multi-factor model with UAT validation

2. **No false confidence detection**
   - Can detect parse failures (confidence = 0)
   - Can't detect "confident but wrong" (confidence = 0.85 but incorrect)
   - Fix: UAT feedback loop to catch these cases

3. **SQLGlot T-SQL coverage untested**
   - Assumption: "SQLGlot handles most T-SQL" (never validated)
   - Reality: Unknown actual coverage %
   - Fix: Accept SQLGlot gaps, enhance regex + add comment hints

4. **No structured UAT feedback**
   - User bugs reported informally
   - No regression test generation
   - Fix: Structured capture system (Phase 1)

**Full analysis:** See [`/temp/parsing_review/00_EXECUTIVE_SUMMARY.md`](temp/parsing_review/00_EXECUTIVE_SUMMARY.md)

---

## 📅 4-Week Implementation Plan

### **Week 1: UAT Feedback Capture System** ⭐ HIGHEST PRIORITY
**Status:** 🚧 In Progress

**Objective:** Enable structured bug reporting from UAT users → auto-generate regression tests

**Deliverables:**
- `/temp/uat_feedback/schema.json` - Feedback JSON schema
- `/temp/uat_feedback/capture_feedback.py` - CLI capture tool
- `/temp/uat_feedback/dashboard.py` - Feedback summary dashboard
- `/temp/uat_feedback/README.md` - User guide

**Success criteria:**
- User can report bug in <2 minutes
- Regression test auto-generated from feedback
- Feedback dashboard shows status of all reports

---

### **Week 2: Special Comment Hints**
**Status:** ✅ Complete (2025-11-06)

**Objective:** Allow developers to hint dependencies for edge cases

**Syntax approved:**
```sql
-- @LINEAGE_INPUTS: dbo.Table1, dbo.Table2
-- @LINEAGE_OUTPUTS: dbo.OutputTable
```

**Deliverables:**
- ✅ `lineage_v3/parsers/comment_hints_parser.py` - Parser implementation
- ✅ Integration into `quality_aware_parser.py`
- ✅ `docs/COMMENT_HINTS_DEVELOPER_GUIDE.md` - Developer guide
- ✅ `docs/PARSING_USER_GUIDE.md` - User documentation with examples
- ✅ Comprehensive tests (10/10 passing)

**Success criteria:**
- ✅ Comment hints extracted and merged with parsed results
- ✅ Confidence score includes hint boost (+0.10, capped at 0.95)
- ✅ Documentation explains when/how to use (both user and developer guides)

---

### **Week 3: Confidence Scoring Redesign**
**Status:** ⏳ Pending

**Objective:** Multi-factor confidence model (accuracy vs. agreement)

**New formula:**
```
Confidence = Parse Success (30%)
           + Method Agreement (25%)
           + Catalog Validation (20%)
           + Comment Hints (10%)
           + UAT Validation (15%)
```

**Deliverables:**
- `lineage_v3/utils/confidence_calculator.py` - Updated with multi-factor
- Confidence breakdown in JSON output
- Frontend visualization of breakdown
- `docs/CONFIDENCE_SCORING_GUIDE.md`

**Success criteria:**
- Confidence score is explainable (user sees breakdown)
- 0.85+ means actually correct (validated by UAT)
- <5% false confidence rate

---

### **Week 4: Documentation Consolidation**
**Status:** ⏳ Pending

**Objective:** Single source of truth with clear references

**Deliverables:**
- `docs/PARSING_ARCHITECTURE.md` - Master document
- Updated cross-references in all docs
- Regex rule catalog (every pattern documented)
- Visual flow diagrams

**Success criteria:**
- No contradictions across docs
- Clear dataflow explanation (DML vs DDL filtering)
- Regex rule engine fully documented (no black box)
- User can understand system in 30 minutes

---

## 📂 Folder Organization

### `/temp/` - Temporary Work
```
temp/
├── parsing_review/          # Architecture review analysis (DONE)
│   ├── 00_EXECUTIVE_SUMMARY.md
│   ├── 01_SQLGLOT_LIMITATIONS_ANALYSIS.md
│   ├── 02_PROCESS_FLOW_ANALYSIS.md
│   └── 11_REVISED_ACTION_PLAN.md
│
└── uat_feedback/            # UAT capture system (IN PROGRESS)
    ├── schema.json          # Feedback JSON schema
    ├── capture_feedback.py  # CLI tool
    ├── dashboard.py         # Summary dashboard
    ├── README.md            # User guide
    ├── reports/             # JSON feedback reports
    └── test_cases/          # Auto-generated regression tests
```

### Production Code (Future Weeks)
```
lineage_v3/parsers/
└── comment_hints_parser.py  # Week 2

lineage_v3/utils/
└── confidence_calculator.py # Week 3 (update)

docs/
├── PARSING_ARCHITECTURE.md  # Week 4 (new master doc)
├── COMMENT_HINTS_GUIDE.md   # Week 2
└── CONFIDENCE_SCORING_GUIDE.md # Week 3
```

---

## 🎯 Success Metrics

### UAT Feedback System (Week 1)
- **Target:** 100% of user bugs captured in structured format
- **Target:** 80% converted to regression tests within 24 hours
- **Target:** Feedback dashboard updated daily

### Comment Hints (Week 2)
- **Target:** 10-15% of complex SPs use hints
- **Target:** Hints add 2-5% coverage
- **Target:** Clear documentation on when to use

### Confidence Scoring (Week 3)
- **Target:** 90%+ of HIGH confidence (≥0.85) are correct (UAT validated)
- **Target:** <5% false confidence rate
- **Target:** User understands confidence breakdown

### Documentation (Week 4)
- **Target:** Single source of truth
- **Target:** 100% of regex rules documented
- **Target:** No contradictions across docs

---

## 🚀 Quick Actions

### For Development Team
1. **This Week:** Test UAT capture tool when ready
2. **Week 2:** Start adding comment hints to complex SPs
3. **Week 3:** Validate new confidence scores make sense
4. **Week 4:** Review documentation for clarity

### For UAT Users
1. **Starting Week 1:** Report bugs using capture tool
2. **Ongoing:** Provide feedback on confidence accuracy
3. **Week 4:** Review documentation for understandability

---

## 📞 Questions or Concerns?

**Review analysis:** See [`/temp/parsing_review/00_EXECUTIVE_SUMMARY.md`](temp/parsing_review/00_EXECUTIVE_SUMMARY.md)
**Detailed plan:** See [`/temp/parsing_review/11_REVISED_ACTION_PLAN.md`](temp/parsing_review/11_REVISED_ACTION_PLAN.md)
**Current work:** See [`/temp/uat_feedback/`](temp/uat_feedback/)

---

## 📝 Change Log

| Date | Phase | Status | Notes |
|------|-------|--------|-------|
| 2025-11-06 | Analysis | ✅ Complete | Deep review, findings documented |
| 2025-11-06 | Planning | ✅ Complete | 4-week plan approved |
| 2025-11-06 | Phase 1 | 🚧 Started | UAT feedback system implementation |

---

**Last Updated:** 2025-11-06
**Next Milestone:** Phase 1 completion (2025-11-13)
**Overall Status:** On track ✅
