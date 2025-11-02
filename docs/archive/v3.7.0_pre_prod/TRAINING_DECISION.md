# Fine-Tuning Decision Analysis

**Date:** 2025-10-31
**Model:** `gpt-4.1-nano`
**Current Accuracy:** 91.7% (few-shot, zero training)

---

## Executive Summary

**Recommendation:** ❌ **DO NOT FINE-TUNE** (at this time)

**Rationale:**
1. Few-shot prompt achieves 91.7% accuracy (exceeds 90% threshold)
2. Fine-tuning setup cost ($1,000-5,000) not justified for 8.3% remaining errors
3. Maintenance burden (retraining on schema changes) outweighs marginal benefit
4. Zero-shot → Few-shot improvement (+33.4%) already captured the low-hanging fruit

**Decision:** Use few-shot prompt in production. Revisit fine-tuning only if accuracy drops below 80% or new use cases emerge.

---

## What is Fine-Tuning?

**Fine-tuning** = Training a pre-trained model on your specific dataset to improve performance on your domain.

**Process:**
1. Collect labeled training data (100-1,000+ examples)
2. Submit to Azure OpenAI fine-tuning API
3. Wait for training (hours to days)
4. Deploy fine-tuned model
5. Pay for inference (usually same or higher cost as base model)

**When it helps:**
- Domain-specific jargon or patterns
- Repeated task structure that differs from general training data
- Need for subtle distinctions the base model misses

---

## Fine-Tuning Cost-Benefit Analysis

### Setup Costs (One-Time)

| Activity | Effort | Cost | Notes |
|----------|--------|------|-------|
| Data labeling | 40 hours | $3,000 | Label 500+ examples with correct resolutions |
| Training data preparation | 8 hours | $600 | Format as JSONL, quality check |
| Fine-tuning API cost | N/A | $50-200 | Azure charges per training token |
| Validation & testing | 8 hours | $600 | Test fine-tuned model vs few-shot |
| **Total Setup** | **56 hours** | **$4,250-4,400** | |

### Ongoing Costs (Annual)

| Activity | Frequency | Cost | Notes |
|----------|-----------|------|-------|
| Inference cost | Daily | ~$105/year | Same as few-shot (no savings) |
| Retraining on schema changes | Quarterly | $1,000/year | 4x per year as schemas evolve |
| Monitoring drift | Monthly | $600/year | Track when retraining needed |
| **Total Ongoing** | | **$1,705/year** | |

### Expected Benefits

**Optimistic scenario (95% accuracy):**
- Improvement: 91.7% → 95% (+3.3%)
- Errors reduced: 1/12 → 0.6/12 (~0.4 fewer errors)
- DBA time saved: Minimal (already at 91.7%)

**Value of 3.3% improvement:**
- Current: 8.3% errors flagged for DBA review
- After fine-tuning: 5% errors flagged
- DBA time savings: ~1 hour per month = $900/year

**ROI calculation:**
```
Setup cost: $4,400
Annual ongoing: $1,705
Annual benefit: $900

Payback period: Never (annual cost > annual benefit)
```

**Verdict:** ❌ Fine-tuning is NOT cost-effective

---

## Accuracy Ceiling Analysis

### What We've Achieved

| Approach | Accuracy | Improvement | Effort |
|----------|----------|-------------|--------|
| Zero-shot (Phase 2) | 58.3% | Baseline | 1 day |
| Few-shot (Phase 3) | 91.7% | +33.4% | 1 day |
| **Remaining gap** | **8.3%** | **1 error/12 tests** | |

### Remaining Error Analysis

**Failed case: BudgetData (Cadence vs Prima)**
- Expected: `STAGING_CADENCE.BudgetData`
- AI resolved: `CONSUMPTION_ClinOpsFinance.BudgetData`
- Root cause: **Genuinely ambiguous** - both are plausible

**Why this is hard:**
- ClinOpsFinance could have its own BudgetData table (materialized for performance)
- OR it could source from STAGING_CADENCE (typical ETL pattern)
- Even human DBAs would need additional context (table existence check, query logs)

**Can fine-tuning fix this?**
- Maybe - if we label 100+ similar ClinOpsFinance edge cases
- But: This is a genuinely ambiguous case even for humans
- Better solution: Add runtime table existence check (simple heuristic)

### Diminishing Returns

**Mathematical analysis:**
```
Zero-shot → Few-shot: 33.4% gain with 5 examples (6.7% gain per example)
Few-shot → Perfect: 8.3% remaining gap

To gain 8.3% through fine-tuning:
- Need ~100+ labeled examples (not 5)
- Marginal gain per example: ~0.08% (100x worse than few-shot)
- Effort: 40 hours labeling vs 1 day few-shot engineering
```

**Verdict:** We're on the steep part of diminishing returns curve. Few-shot captured most of the value.

---

## Fine-Tuning Maintenance Burden

### Schema Evolution Problem

**Your database schemas change:**
- New tables added (weekly/monthly)
- Schemas renamed or restructured (quarterly)
- New schema conventions introduced (annually)

**Impact on fine-tuned model:**
- Model learns specific table names, not general patterns
- When schemas change, model may hallucinate old table names
- Requires retraining every 3-6 months to stay current

**Example scenario:**
```
Fine-tuned model learns:
  "STAGING_CADENCE.BudgetData is the budget source"

Schema change (3 months later):
  Table renamed to STAGING_CADENCE.Budget_Data_v2

Fine-tuned model output:
  Still references old table name (hallucination risk!)

Few-shot prompt:
  Just update 1 line in prompt with new table name (5 min fix)
```

**Maintenance comparison:**

| Approach | Schema Change Response | Effort | Cost |
|----------|----------------------|--------|------|
| Few-shot | Edit prompt (5 min) | Negligible | $0 |
| Fine-tuned | Relabel 100+ examples, retrain (40 hours) | High | $3,000 |

**Verdict:** Few-shot is 100x more maintainable.

---

## Alternative Improvements (Better ROI)

### Option 1: Add 6th Few-Shot Example (1 hour effort)

**Target:** Fix the BudgetData edge case

**New example:**
```
"ClinOpsFinance cross-schema pattern: When in CONSUMPTION_ClinOpsFinance,
source budget data from STAGING_CADENCE (Cadence is primary budget source)"
```

**Expected improvement:** 91.7% → 95%+ (fix 1 error)
**Cost:** 1 hour of prompt engineering = $75
**Maintenance:** Edit 1 line when schemas change

**ROI:** Excellent (low effort, immediate gain)

### Option 2: Hybrid Approach (2-3 days effort)

**Strategy:** Use simple heuristics BEFORE calling AI

```python
def disambiguate_with_hybrid(reference, candidates, sql_context):
    # Step 1: Check if table exists in same schema as procedure
    same_schema_candidate = [c for c in candidates if c.startswith(proc_schema)]
    if len(same_schema_candidate) == 1:
        return same_schema_candidate[0], 0.90, "heuristic"

    # Step 2: Check for explicit context (TRUNCATE earlier in proc)
    truncate_match = find_truncate_reference(sql_context, candidates)
    if truncate_match:
        return truncate_match, 0.95, "context_clue"

    # Step 3: Fall back to AI only if truly ambiguous
    return call_ai(reference, candidates, sql_context)
```

**Expected improvement:**
- Reduce AI calls by 50-70% (lower cost)
- Accuracy: Maintain 91.7% or improve slightly
- Latency: Faster (heuristics are instant)

**ROI:** Excellent (reduces cost, maintains accuracy)

### Option 3: Query Log Validation (already in place)

**Current strategy:** Cross-validate AI resolution against runtime query logs

**If query logs show:**
```sql
-- Actual execution log
SELECT * FROM STAGING_CADENCE.BudgetData WHERE ...
```

**Then:** Override AI resolution if it differs
**Confidence boost:** 0.85 → 0.95 (runtime evidence)

**This is already implemented in parser** - no additional work needed.

---

## When to Revisit Fine-Tuning

### Trigger Conditions

Fine-tuning becomes worth it if:

1. **Accuracy drops below 80%** due to schema drift
   - Action: Try 6th few-shot example first
   - If still <80%: Consider fine-tuning

2. **New domain emerges** (e.g., 50+ SPs in new schema with unique patterns)
   - Example: New `STAGING_SALESFORCE` schema with different conventions
   - Action: Add domain-specific few-shot examples OR fine-tune

3. **High-volume production** (10,000+ disambiguations/day)
   - Current: ~160 disambiguations/day
   - Action: Fine-tuning may reduce cost at scale (lower token usage)

4. **Regulatory requirement** for auditability
   - If audit requires: "Prove model was trained on our data"
   - Action: Fine-tuning creates auditable training artifact

### Current Status: ✅ None of these triggers apply

---

## Comparison: Few-Shot vs Fine-Tuning

| Criterion | Few-Shot (Current) | Fine-Tuning |
|-----------|-------------------|-------------|
| **Accuracy** | 91.7% | ~95% (estimated) |
| **Setup cost** | $0 | $4,250 |
| **Setup time** | 1 day | 2-3 weeks |
| **Ongoing cost** | $105/year | $1,705/year |
| **Maintenance** | 5 min per schema change | 40 hours per schema change |
| **Flexibility** | Edit prompt instantly | Retrain model (days) |
| **Hallucination risk** | Low (grounded in few-shot examples) | Medium (may memorize old table names) |
| **Auditability** | Prompt is version-controlled | Training data + model versioning required |
| **Scalability** | Excellent | Good (but more complex) |

**Winner:** Few-shot prompt (better ROI, easier maintenance, sufficient accuracy)

---

## Decision Matrix

| Scenario | Recommendation | Effort | Timeline |
|----------|---------------|--------|----------|
| **Current state (91.7%)** | ✅ Use few-shot, NO fine-tuning | 0 hours | Immediate |
| **If accuracy drops to 80-90%** | Add 6th few-shot example | 1 hour | 1 day |
| **If accuracy drops to 70-80%** | Try hybrid approach | 16 hours | 1 week |
| **If accuracy drops below 70%** | Consider fine-tuning OR upgrade to gpt-4o | 56+ hours | 3 weeks |
| **If new domain emerges** | Add domain few-shot OR fine-tune if >100 cases | Varies | Varies |

---

## Recommendation Summary

### ❌ Do NOT Fine-Tune (Now)

**Reasons:**
1. ✅ 91.7% accuracy exceeds production threshold (80%)
2. ✅ Few-shot prompt is easier to maintain than fine-tuned model
3. ✅ Setup cost ($4,400) not justified for marginal 3.3% gain
4. ✅ Ongoing cost ($1,705/year) exceeds few-shot cost ($105/year)
5. ✅ Remaining errors are genuinely ambiguous (hard even for humans)

### ✅ Use Few-Shot Prompt in Production

**Benefits:**
- Zero setup cost (already developed)
- Instant updates (edit prompt, no retraining)
- Proven accuracy (91.7% in testing)
- Low maintenance (5 min per schema change)

### 📋 Future Options (If Needed)

**If accuracy becomes insufficient:**
1. **First:** Add 6th few-shot example (1 hour effort)
2. **Second:** Implement hybrid heuristics (1 week effort)
3. **Third:** Upgrade to gpt-4o (3x cost, may reach 95%+)
4. **Last resort:** Fine-tune (3 weeks effort, $4,400 setup, $1,700/year ongoing)

---

## Conclusion

**Fine-Tuning Decision: ❌ NOT RECOMMENDED**

**Key points:**
1. Few-shot achieves 91.7% accuracy (production-ready)
2. Fine-tuning cost ($4,400 setup + $1,705/year) not justified for 3.3% gain
3. Few-shot is 100x easier to maintain (5 min vs 40 hours per schema change)
4. Remaining 8.3% errors are genuinely ambiguous (not model limitation)
5. Better alternatives exist (6th few-shot example, hybrid approach)

**Final recommendation:** Proceed with Phase 4 using few-shot prompt. Monitor accuracy in production. Revisit fine-tuning only if accuracy drops below 80% or trigger conditions emerge.

---

**Last Updated:** 2025-10-31
**Status:** Training decision complete - Few-shot recommended, fine-tuning not justified
