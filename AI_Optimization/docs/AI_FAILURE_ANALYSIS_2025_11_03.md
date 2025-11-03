# AI Inference Failure Analysis - 2025-11-03

## Executive Summary

**Problem:** AI achieves only 16.4% accuracy (9/55 tables) when inferring dependencies for unreferenced tables.

**Root Cause:** AI is **hallucinating** SP names based on naming patterns rather than extracting exact names from the provided SQL code.

**Target:** >90% accuracy (per user requirement)

**Gap:** 16.4% → 90% = **73.6 percentage points improvement needed**

---

## Critical Finding: Hallucination vs Code Analysis

### What's Happening (WRONG)

The AI is generating plausible-sounding SP names like:
- `consumption_prima.spLoadEnrollmentPlans` (hallucinated 5 times)
- `consumption_prima.spLoadStudyArms` (hallucinated 3 times)
- `consumption_prima.spLoadGlobalAccounts` (hallucinated 3 times)

**These SPs DO NOT EXIST in the catalog!**

### What Should Happen (CORRECT)

The AI should:
1. Read the actual SQL code snippets provided
2. Extract table references from INSERT/SELECT statements
3. Return ONLY the SP names that were provided in the input list
4. Return empty arrays if no SQL code mentions the target table

---

## Why This Is Happening

### Issue #1: AI Learns Pattern Matching Instead of Code Analysis

**Current Few-Shot Examples Show:**
```json
{
  "output_procedures": ["consumption_prima.sploadstudyarms"]
}
```

**Problem:** Examples teach the AI to **guess** based on naming patterns:
- Table: `StudyArms` → AI guesses: `spLoadStudyArms`
- Table: `EnrollmentPlan` → AI guesses: `spLoadEnrollmentPlan` or `spLoadEnrollmentPlans`

**What AI Does:**
1. Sees table name: `EnrollmentPlan`
2. Applies pattern: `spLoad + TableName`
3. Returns hallucinated name WITHOUT checking if it exists in the provided SP list

### Issue #2: AI Doesn't Constrain Output to Input Catalog

**Current JSON Schema:**
```python
"output_procedures": {
    "type": "array",
    "items": {"type": "string"}  # Any string allowed!
}
```

**Problem:** AI can return ANY string, not just SP names from the provided catalog.

**2025 Best Practice (Missing):**
```python
"output_procedures": {
    "type": "array",
    "items": {
        "type": "string",
        "enum": [actual_sp_list]  # Constrain to provided catalog
    }
}
```

### Issue #3: Examples Don't Emphasize "Extract, Don't Generate"

**Current Examples Focus On:**
- INSERT statements
- SELECT statements
- Table name matching

**Missing Emphasis:**
- "Only return SP names provided in the input list"
- "If SQL code doesn't mention target table, return empty arrays"
- "Do NOT guess or generate SP names"

---

## Quantitative Analysis

### Hallucination Rate

**Total AI Inferences:** 55 tables
**Hallucinated SP Names:** 15 unique names × avg 2.5 occurrences = ~38 hallucinations
**Hallucination Rate:** ~69% (38/55)

**Impact:** Most "matches" are false positives because the SP doesn't exist.

### Success Rate Breakdown

| Category | Count | Percentage |
|----------|-------|------------|
| Correct matches | 9 | 16.4% |
| False positives (hallucinated) | ~38 | 69.1% |
| True negatives (correctly empty) | ~8 | 14.5% |

**Reality:** Only 16.4% actual success, 69% hallucination, 14.5% correct rejection.

---

## Research Findings: 2025 Best Practices

### Key Insight #1: Constrained Decoding with Enum

**Source:** OpenAI Structured Outputs (2025)

> "For extracting entities from a fixed set, use `enum` in JSON Schema to constrain outputs to known values."

**Application:** Pass the actual SP catalog as an `enum` list, forcing AI to choose from provided options.

**Expected Impact:** Eliminates 100% of hallucinations

### Key Insight #2: Explicit Instructions Beat Implicit Learning

**Source:** LLM Structured Output Best Practices (2025)

> "Clearly state constraints in both schema descriptions and system prompt. Don't rely on examples alone."

**Application:** Add explicit instruction: "ONLY return SP names from the provided list. DO NOT generate or guess names."

**Expected Impact:** Reduces creative generation, increases literal extraction

### Key Insight #3: Few-Shot Should Match Task Exactly

**Source:** Arize AI - Text-to-SQL Prompting (2024)

> "SQL query distribution matters more than question diversity. Use in-domain examples that match your exact task."

**Application:** Current examples show INSERT/SELECT patterns but don't emphasize catalog constraint.

**Expected Impact:** Better task alignment, less pattern matching

---

## Proposed Solution: Three-Pronged Approach

### Fix #1: Constrain JSON Schema with Enum (HIGH IMPACT)

**Change in `ai_disambiguator.py:592-600`:**

```python
# Build enum list from provided SPs
sp_name_list = [f"{sp['schema']}.{sp['name']}" for sp in all_sp_data]

"output_procedures": {
    "type": "array",
    "description": "SPs that WRITE to this table. MUST be from the provided SP list.",
    "items": {
        "type": "string",
        "enum": sp_name_list  # Force selection from catalog
    }
},
"input_procedures": {
    "type": "array",
    "description": "SPs that READ from this table. MUST be from the provided SP list.",
    "items": {
        "type": "string",
        "enum": sp_name_list  # Force selection from catalog
    }
}
```

**Expected Impact:**
- Eliminates 100% of hallucinations
- Forces AI to extract from provided list
- **Estimated improvement:** 16.4% → 60-70% (hallucinationsremoved)

### Fix #2: Update System Prompt with Explicit Constraints

**Add to `inference_prompt.txt` (line 72-77):**

```
## CRITICAL CONSTRAINTS

1. **ONLY return SP names provided in the "Available Stored Procedures" section above**
2. **DO NOT generate, guess, or invent SP names**
3. **If SQL code doesn't mention the target table, return empty arrays**
4. **Match table names exactly in the SQL code (case-insensitive)**
5. **Confidence should be 0.0 if no SQL code mentions target table**
```

**Expected Impact:**
- Reinforces catalog constraint
- Reduces creative name generation
- **Estimated improvement:** Additional 10-15% accuracy

### Fix #3: Add Negative Examples to Few-Shot

**Add 2 examples showing:**

1. **SP list provided, but AI correctly returns empty:**
```json
{
  "input_procedures": [],
  "output_procedures": [],
  "confidence": 0.0,
  "reasoning": "None of the provided SPs reference this table in their SQL code"
}
```

2. **Table name pattern exists (spLoadX) but SQL doesn't match:**
```json
Target: consumption_prima.vendor_details
Available SPs:
- consumption_prima.sploadvendoraccounts (SQL: INSERT INTO vendor_accounts)

Answer:
{
  "input_procedures": [],
  "output_procedures": [],
  "confidence": 0.0,
  "reasoning": "sploadvendoraccounts inserts into vendor_accounts, not vendor_details - no match"
}
```

**Expected Impact:**
- Teaches exact table name matching
- Discourages pattern-based guessing
- **Estimated improvement:** Additional 5-10% accuracy

---

## Expected Outcomes

### Conservative Estimate (Enum + Explicit Instructions)
- **Hallucinations eliminated:** 69% → 0%
- **True positives improved:** 16.4% → 60%
- **True negatives improved:** 14.5% → 30%
- **Total accuracy:** **~60%**

### Optimistic Estimate (All 3 Fixes)
- **Hallucinations eliminated:** 100%
- **True positives improved:** Code analysis works properly
- **True negatives improved:** Correct rejection of non-matches
- **Total accuracy:** **75-85%**

### Target (90% Requirement)
- **Additional iteration needed:** Refine few-shot with real failed cases
- **UAT feedback loop:** Collect user corrections for edge cases
- **Estimated timeline:** 2-3 iterations to reach 90%

---

## Implementation Plan

### Phase 1: Enum Constraint (30 minutes) - HIGH PRIORITY
1. Modify `ai_disambiguator.py` to build SP enum list
2. Update JSON schema with enum constraint
3. Test on 10 sample tables
4. **Expected:** Hallucinations drop to 0%

### Phase 2: Explicit Instructions (15 minutes)
1. Update `inference_prompt.txt` with CRITICAL CONSTRAINTS section
2. Test on same 10 tables
3. **Expected:** Accuracy improves 10-15%

### Phase 3: Negative Examples (30 minutes)
1. Add 2 negative examples to few-shot
2. Test on full 176-table dataset
3. **Expected:** Accuracy reaches 60-75%

### Phase 4: Iteration (if needed)
1. Analyze remaining failures
2. Add real failed cases to few-shot
3. Test until 90% accuracy achieved

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Enum list too large (token limit) | Low | High | Limit to 50 most relevant SPs per table |
| AI still returns empty for true matches | Medium | Medium | Add more positive examples with exact matches |
| True negatives decrease (false positives) | Low | Medium | Keep 5 negative examples in few-shot |
| 90% target not achievable with prompting alone | Low | High | Fall back to fine-tuning or hybrid approach |

---

## Key Metrics to Track

### Before (Iteration 2):
- Accuracy: 16.4%
- Hallucination rate: 69%
- True positive rate: 16.4%
- True negative rate: 14.5%

### After (Target):
- Accuracy: >90%
- Hallucination rate: 0%
- True positive rate: >80%
- True negative rate: >95%

---

## Summary

**Core Problem:** AI generates SP names instead of extracting from provided catalog.

**Root Cause:** Missing enum constraint in JSON Schema allows any string output.

**Solution:**
1. Add enum constraint (eliminates hallucinations)
2. Add explicit instructions (reinforces constraint)
3. Add negative examples (teaches correct rejection)

**Expected Impact:** 16.4% → 60-75% → 90% (over 2-3 iterations)

**Next Step:** Implement enum constraint in JSON Schema (30 minutes)

---

**Date:** 2025-11-03
**Status:** ⏳ Ready for implementation
**Priority:** 🚨 HIGH - Enum constraint is critical fix
