# Quick Start Guide - SQLGlot Optimization

**Current Status:** 86/202 SPs (42.6%) high confidence
**Goal:** 100-140 SPs (50-70%) in Phase 1

---

## TL;DR

**Problem:** Leading semicolons approach broke CREATE PROC structure (181 validation failures)

**Solution:** Test 5 simple regex iterations to find optimal preprocessing

**Time:** ~1 hour for all 5 iterations

**Next:** Proceed to AI fallback (Phase 2) for 85-90% total

---

## Phase 1: Run 5 Iterations (~1 hour)

### Setup
```bash
cd /home/chris/sandbox
```

### Iteration 1: No Preprocessing (10 min)

**Edit:** `lineage_v3/parsers/quality_aware_parser.py` line 131
```python
def _preprocess_ddl(self, ddl: str) -> str:
    return ddl  # No preprocessing
```

**Test:**
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python sqlglot_improvement/scripts/test_iteration.py "Iteration 1: No preprocessing"
```

**Expected:** 70-80 SPs (worse than 86, but validates baseline)

**Decision:** If ≤ 86 → Revert and proceed to Iteration 2

---

### Iteration 2: GO Replacement Only (10 min)

**Edit:** `lineage_v3/parsers/quality_aware_parser.py` line 131
```python
def _get_preprocessing_patterns(self) -> List[Tuple[Pattern, str, int]]:
    patterns = [
        (r'\bGO\b', ';', re.IGNORECASE),
    ]
    return patterns
```

**Test:**
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python sqlglot_improvement/scripts/test_iteration.py "Iteration 2: GO replacement"
```

**Expected:** 80-90 SPs

**Decision:** If > best → Keep, else → Revert

---

### Iteration 3: GO + Comments (10 min)

**Edit:** `lineage_v3/parsers/quality_aware_parser.py` line 131
```python
def _get_preprocessing_patterns(self) -> List[Tuple[Pattern, str, int]]:
    patterns = [
        (r'--[^\n]*', '', 0),
        (r'/\*.*?\*/', '', re.DOTALL),
        (r'\bGO\b', ';', re.IGNORECASE),
    ]
    return patterns
```

**Test:**
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python sqlglot_improvement/scripts/test_iteration.py "Iteration 3: GO + comments"
```

**Expected:** 85-95 SPs

**Decision:** If > best → Keep, else → Revert

---

### Iteration 4: GO + Comments + Session Options (10 min)

**Edit:** `lineage_v3/parsers/quality_aware_parser.py` line 131
```python
def _get_preprocessing_patterns(self) -> List[Tuple[Pattern, str, int]]:
    patterns = [
        (r'--[^\n]*', '', 0),
        (r'/\*.*?\*/', '', re.DOTALL),
        (r'\bSET\s+NOCOUNT\s+(ON|OFF)\b', '', re.IGNORECASE),
        (r'\bSET\s+ANSI_NULLS\s+(ON|OFF)\b', '', re.IGNORECASE),
        (r'\bSET\s+QUOTED_IDENTIFIER\s+(ON|OFF)\b', '', re.IGNORECASE),
        (r'\bGO\b', ';', re.IGNORECASE),
    ]
    return patterns
```

**Test:**
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python sqlglot_improvement/scripts/test_iteration.py "Iteration 4: GO + comments + session"
```

**Expected:** 90-100 SPs

**Decision:** If > best → Keep, else → Revert

---

### Iteration 5: GO + Comments + Session + Utility (10 min)

**Edit:** `lineage_v3/parsers/quality_aware_parser.py` line 131
```python
def _get_preprocessing_patterns(self) -> List[Tuple[Pattern, str, int]]:
    patterns = [
        (r'--[^\n]*', '', 0),
        (r'/\*.*?\*/', '', re.DOTALL),
        (r'\bSET\s+NOCOUNT\s+(ON|OFF)\b', '', re.IGNORECASE),
        (r'\bSET\s+ANSI_NULLS\s+(ON|OFF)\b', '', re.IGNORECASE),
        (r'\bSET\s+QUOTED_IDENTIFIER\s+(ON|OFF)\b', '', re.IGNORECASE),
        (r'\bEXEC(?:UTE)?\s+\[?[^\]]+\]?\.\[?(LogMessage|LogError|spLastRowCount)\]?[^\n;]*;?',
         '', re.IGNORECASE),
        (r'\bGO\b', ';', re.IGNORECASE),
    ]
    return patterns
```

**Test:**
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python sqlglot_improvement/scripts/test_iteration.py "Iteration 5: Full cleanup"
```

**Expected:** 95-110 SPs

**Decision:** If ≥ 100 (50%) → SUCCESS! Proceed to Phase 2

---

## After Phase 1

### If Result ≥ 100 SPs (50%)
✅ **SUCCESS!** Document final patterns and proceed to Phase 2 (AI fallback)

### If Result < 100 SPs
⚠️ Accept best result from 5 iterations, proceed to Phase 2 anyway
- Phase 2 will add 60-80 SPs via AI
- Total expected: 160-180 SPs (80-90%)

---

## Phase 2 Preview (AI Fallback)

**Complexity Detection Logic:**
```python
if has_complexity_red_flags(ddl):
    use_ai()
elif complexity_score(ddl) >= 10000:
    use_ai()
elif sqlglot_confidence < 0.85:
    use_ai()
else:
    use_sqlglot()
```

**Red Flags:**
- `sp_executesql` (dynamic SQL)
- `DECLARE CURSOR` (cursor logic)
- `CREATE TABLE #` (temp tables)
- `BEGIN TRY` (error handling)
- `BEGIN TRANSACTION` (transaction mgmt)

**Expected:** +60-80 SPs via AI → Total: 160-180 SPs (80-90%)

**Cost:** ~$0.03 per full parse

See `MASTER_PLAN.md` Phase 2 for complete implementation.

---

## Troubleshooting

### "No stored procedures found"
```bash
# Run full parse first
cd /home/chris/sandbox
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

### "Preprocessing validation failed"
Check `/tmp/parse_output.log` for warnings:
```bash
grep "Preprocessing validation failed" /tmp/parse_output.log | wc -l
```

### Regression from baseline
Revert changes and proceed to next iteration

---

## Files

| File | Purpose |
|------|---------|
| `MASTER_PLAN.md` | Complete 3-phase strategy |
| `README.md` | Detailed documentation |
| `QUICK_START.md` | This file (quick reference) |
| `docs/` | Supporting analysis documents |
| `scripts/test_iteration.py` | Test and measure results |
| `scripts/analyze_sqlglot_failures.py` | Analyze parse log |

---

**Time to Complete Phase 1:** ~1 hour (5 iterations × 10-15 min each)

**Start Now:**
```bash
cd /home/chris/sandbox
# Edit lineage_v3/parsers/quality_aware_parser.py
# Run Iteration 1
```

Good luck!
