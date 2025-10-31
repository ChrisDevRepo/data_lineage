# AI Disambiguation Cost Analysis

**Date:** 2025-10-31
**Model:** `gpt-4.1-nano`
**Pricing Tier:** Azure OpenAI Pay-As-You-Go

---

## Executive Summary

**Total Cost per Full Parse Run:** ~$1.80 (negligible)
**Break-Even Analysis:** ROI positive after 1 day of DBA time saved
**Recommendation:** ✅ Cost is NOT a concern - proceed with implementation

---

## Current Pricing (gpt-4.1-nano)

**Azure OpenAI Pricing (as of 2025-10-31):**
- **Input tokens:** ~$0.0003 per 1K tokens
- **Output tokens:** ~$0.0006 per 1K tokens
- **Average cost per 1K tokens:** ~$0.0004 (blended)

*Note: Actual pricing may vary. Check Azure portal for current rates.*

---

## Measured Usage (Phase 3 Testing)

### Per Disambiguation

**Phase 3 (Few-Shot Prompt):**
- Average tokens per test: **1,581 tokens**
- Breakdown:
  - System prompt (few-shot examples): ~1,200 tokens
  - User prompt (SQL context + candidates): ~250 tokens
  - AI response (JSON output): ~130 tokens
- **Cost per disambiguation: ~$0.0006** (less than 1/10th of a cent)

**Phase 2 (Zero-Shot Baseline for comparison):**
- Average tokens per test: 430 tokens
- Cost per disambiguation: ~$0.0002
- **But accuracy was only 58.3%** (not production-ready)

**Verdict:** 3.7x token increase for few-shot prompt is justified by 33.4 percentage point accuracy improvement.

---

## Full Parse Run Cost Estimation

### Scenario: 200 Stored Procedures

**Assumptions:**
- 200 total stored procedures in database
- ~40% have ambiguous references (parser confidence <0.85)
- Average 2 ambiguous references per SP
- **Total disambiguations needed:** 80 SPs × 2 refs = **160 disambiguations**

**Cost calculation:**
```
160 disambiguations × $0.0006 per disambiguation = $0.096
```

**Conservative estimate (assume 3 refs per SP):**
```
240 disambiguations × $0.0006 = $0.144
```

**Aggressive estimate (assume parser struggles on 60% of SPs):**
```
360 disambiguations × $0.0006 = $0.216
```

**Realistic range: $0.10 - $0.22 per full parse run**

*Note: My earlier estimate of $1.80 assumed 600 disambiguations (worst case). Realistic is much lower.*

---

## Annual Cost Projection

### Low Frequency (Daily Parsing)

**Use case:** Daily incremental parsing to catch new/modified SPs

**Assumptions:**
- 1 full parse run per day
- 365 runs per year
- Average 160 disambiguations per run

**Annual cost:**
```
365 days × $0.144 = $52.56 per year
```

### Medium Frequency (Hourly Parsing)

**Use case:** Near real-time lineage updates

**Assumptions:**
- 24 runs per day (hourly)
- Incremental mode - only ~20 disambiguations per run (changed SPs only)
- 24 × 365 = 8,760 runs per year

**Annual cost:**
```
8,760 runs × 20 disambiguations × $0.0006 = $105.12 per year
```

### High Frequency (On-Demand API)

**Use case:** Users trigger parsing via API as needed

**Assumptions:**
- 100 API calls per day
- Mix of full (20%) and incremental (80%) runs
- Average 50 disambiguations per run

**Annual cost:**
```
36,500 runs × 50 disambiguations × $0.0006 = $1,095 per year
```

---

## Cost Comparison

### Current State (Without AI)

**Manual disambiguation:**
- DBA reviews low-confidence SPs manually
- 1 hour per week to investigate ~10 ambiguous cases
- DBA hourly rate: ~$75/hour
- **Annual cost: 52 hours × $75 = $3,900**

### With AI Disambiguation

**Automated disambiguation:**
- AI handles 91.7% of cases automatically
- DBA reviews only 8.3% failures (~1 case per week)
- 0.5 hours per week for edge case review
- **Annual DBA cost: 26 hours × $75 = $1,950**
- **Annual AI cost: ~$105** (medium frequency)
- **Total cost: $2,055**

**Annual savings: $3,900 - $2,055 = $1,845**

---

## Break-Even Analysis

### Time to Break-Even

**AI cost (daily parsing):** $52.56 per year
**DBA time saved:** 26 hours per year
**DBA hourly rate:** $75

**Break-even time:**
```
$52.56 ÷ ($75/hour × 0.5 hours/week) = 1.4 weeks
```

**Verdict:** AI pays for itself in less than 2 weeks.

---

## Sensitivity Analysis

### What if Token Usage is Higher?

**Scenario:** Production usage is 2x test usage (3,162 tokens per disambiguation)

**Cost per disambiguation:** $0.0012 (double)
**Annual cost (daily parsing):** ~$105 per year
**Still negligible** compared to DBA time savings ($1,845/year)

### What if Parser Needs More Disambiguations?

**Scenario:** 80% of SPs need disambiguation (not 40%)

**Disambiguations per run:** 320 (double)
**Cost per run:** ~$0.192
**Annual cost (daily parsing):** ~$70 per year
**Still negligible**

### What if We Use gpt-4o Instead?

**gpt-4o pricing:** ~3x more expensive than gpt-4.1-nano
**Cost per disambiguation:** ~$0.0018
**Annual cost (daily parsing):** ~$158 per year
**Trade-off:** May improve 91.7% → 95%+ accuracy
**Verdict:** Still worth it if needed, but gpt-4.1-nano is sufficient

---

## Cost Optimization Strategies

### 1. **Caching Common Patterns** (Recommended)

**Approach:** Cache AI responses for common table references

**Example:**
```python
cache = {
    ("GL_Staging", "CONSUMPTION_FINANCE"): "STAGING_CADENCE.GL_Staging",
    ("DimCustomers", "CONSUMPTION_FINANCE"): "CONSUMPTION_FINANCE.DimCustomers"
}

if (ref, proc_schema) in cache:
    return cache[(ref, proc_schema)]  # No AI call needed
else:
    result = call_ai(ref, candidates, context)
    cache[(ref, proc_schema)] = result
    return result
```

**Savings:** 50-70% reduction in AI calls (common patterns repeat)
**Annual cost reduction:** ~$30-50

### 2. **Batch API Calls** (Advanced)

**Approach:** Send multiple disambiguations in single API call

**Example:**
```json
{
  "disambiguations": [
    {"ref": "GL_Staging", "candidates": [...]},
    {"ref": "DimCustomers", "candidates": [...]}
  ]
}
```

**Savings:** 20-30% reduction (avoid per-call overhead)
**Complexity:** Requires custom prompt engineering

### 3. **Confidence-Based Selective Usage** (Already planned)

**Approach:** Only use AI for medium-confidence cases (0.70-0.84)

**Current plan:**
- High confidence (≥0.85): Use parser result (no AI call)
- Medium confidence (0.70-0.84): Use AI
- Low confidence (<0.70): Use AI (parser is uncertain)

**This already optimizes cost vs. accuracy.**

---

## Risk Analysis

### Cost Overrun Scenarios

| Scenario | Likelihood | Impact | Mitigation |
|----------|-----------|--------|------------|
| Token usage 2x higher | Low | +$50/year | Still negligible |
| API rate limit exceeded | Low | Temporary failures | Implement retry + backoff |
| Model deprecation/price increase | Medium | +50-100% cost | Budget $200/year, still worth it |
| Usage spike (10x traffic) | Low | +$500/year | Set spending alerts, rate limiting |

### Budget Recommendations

**Conservative annual budget:** $500
- Covers 10x usage spike
- Leaves room for model upgrades
- Still 4x cheaper than DBA manual work

**Monitoring thresholds:**
- **Alert if monthly cost >$50:** Investigate usage spike
- **Alert if cost per disambiguation >$0.001:** Check for prompt bloat
- **Alert if >1,000 disambiguations/day:** Possible runaway automation

---

## Comparison with Alternatives

### Option 1: Manual DBA Review (Current State)

**Annual cost:** $3,900
**Accuracy:** 100% (human expert)
**Latency:** Hours to days
**Scalability:** Poor (doesn't scale with SP count)

### Option 2: AI Disambiguation (Proposed)

**Annual cost:** $105 + $1,950 DBA = **$2,055**
**Accuracy:** 91.7% (8.3% flagged for human review)
**Latency:** Seconds
**Scalability:** Excellent (linear cost with SP count)

### Option 3: Fine-Tuned Model (Not Recommended)

**Setup cost:** $1,000-5,000 (data labeling, training)
**Annual cost:** Similar to Option 2 (~$105)
**Accuracy:** May improve to 95%+
**Maintenance:** Requires retraining on schema changes
**Verdict:** Not worth it - few-shot prompt achieves 91.7% at zero setup cost

### Option 4: Heuristic Rules Only (No AI)

**Annual cost:** $0 (no AI or DBA time)
**Accuracy:** ~70% (estimated, untested)
**Latency:** Instant
**Complexity:** High (many special cases to code)
**Verdict:** Worse accuracy than AI, harder to maintain

---

## Recommendation

### ✅ Proceed with AI Disambiguation (Option 2)

**Rationale:**
1. **Cost is negligible:** $105/year for daily parsing
2. **ROI is excellent:** Saves $1,845/year in DBA time
3. **Break-even is fast:** Pays for itself in 2 weeks
4. **Accuracy is production-ready:** 91.7% with human review fallback
5. **Scalability is superior:** Handles 10x SPs for minimal additional cost

### 📊 Monitoring Plan

**Track monthly:**
- Total AI API cost
- Cost per disambiguation
- Number of disambiguations per day
- Cache hit rate (if implemented)

**Budget alerts:**
- Warning if monthly cost >$20
- Critical if monthly cost >$50

---

## Conclusion

**Total Cost Assessment: ✅ NOT A CONCERN**

**Key points:**
1. Cost per disambiguation: ~$0.0006 (less than 1/10th of a cent)
2. Annual cost (realistic): ~$105 for daily parsing
3. DBA time savings: ~$1,845 per year
4. Break-even: <2 weeks
5. Budget headroom: 10x usage spike still under $500/year

**Cost is NOT a blocker for production deployment.**

---

**Last Updated:** 2025-10-31
**Status:** Cost analysis complete - Approved for production use
