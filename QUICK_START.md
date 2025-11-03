# Quick Start - v4.0.0 Slim Parser

**Read this first, then go to [PROJECT_STATUS.md](PROJECT_STATUS.md) for details.**

---

## 🎯 Where We Are

- **Version:** 4.0.0 (Slim - No AI)
- **Current:** 155/263 objects (58.94%) high confidence
- **Goal:** 250/263 objects (95.05%) high confidence
- **Gap:** Need to improve 95 objects

---

## 🔥 What to Do Next (Priority Order)

### 1️⃣ Fix DECLARE Bug (CRITICAL)
**File:** `lineage_v3/parsers/quality_aware_parser.py:119`
**Impact:** +10-20 objects
**Time:** 1 hour

Change this line:
```python
(r'\bDECLARE\s+@\w+\s+[^;]+;', '', 0),  # GREEDY - REMOVES BUSINESS LOGIC
```

To this:
```python
(r'\bDECLARE\s+@\w+\s+[^\n;]+(?:;|\n)', '', 0),  # STOPS AT LINE END
```

Then test:
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_2025_11_03_v4_slim_no_ai
```

### 2️⃣ Analyze 108 Low-Confidence Objects
**Time:** 2-3 hours

```bash
# Extract failing objects
jq '.objects[] | select(.regex.overall_f1 < 0.85) | {name: .object_name, f1: .regex.overall_f1}' \
   optimization_reports/latest.json > temp/low_conf_analysis.json

# Categorize by failure type (manual review)
# Find common patterns
# Prioritize fixes
```

### 3️⃣ Implement Top 3 Pattern Fixes
**Time:** 1-2 weeks

Based on analysis from step 2, fix most common patterns.

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| **PROJECT_STATUS.md** | 📋 **START HERE** - Master document with all details |
| `CLAUDE.md` | Development guide for working with repo |
| `lineage_v3/parsers/quality_aware_parser.py` | Parser code (line 119 needs fix) |
| `optimization_reports/latest.json` | Latest evaluation results |
| `docs/V4_SLIM_PARSER_BASELINE.md` | Baseline results and metrics |

---

## 🔧 Essential Commands

```bash
# Run evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_2025_11_03_v4_slim_no_ai

# Test frontend
/sub_DL_TestFrontend smoke

# View results
jq '.summary' optimization_reports/latest.json
```

---

## 📊 Progress Tracking

| Milestone | Objects | % | Status |
|-----------|---------|---|--------|
| Current | 155/263 | 58.94% | ✅ Done |
| Week 1: Fix DECLARE | 165-175 | 63-67% | 🔴 Next |
| Week 2-3: Regex | 185-205 | 70-78% | ⏳ Pending |
| Week 3-4: Rules | 195-225 | 74-86% | ⏳ Pending |
| Month 2-3: Goal | 250+ | 95%+ | 🎯 Target |

---

**For complete details:** See [PROJECT_STATUS.md](PROJECT_STATUS.md)
