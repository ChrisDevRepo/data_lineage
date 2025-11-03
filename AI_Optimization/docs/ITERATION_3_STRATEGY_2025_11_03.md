# Iteration 3 Strategy: Achieving >90% AI Accuracy
**Date:** 2025-11-03
**Current Accuracy:** 16.4% (9/55 tables)
**Target Accuracy:** >90% (per user requirement)
**Gap to Close:** 73.6 percentage points

---

## Critical Discovery: The Hallucination Problem

### What We Found

**AI is generating SP names instead of extracting from provided SQL code:**
- `consumption_prima.spLoadEnrollmentPlans` - hallucinated 5 times (DOESN'T EXIST)
- `consumption_prima.spLoadStudyArms` - hallucinated 3 times (DOESN'T EXIST)
- `consumption_prima.spLoadGlobalAccounts` - hallucinated 3 times (DOESN'T EXIST)

**Hallucination Rate:** ~69% (38/55 inferences)

**Root Cause:** JSON Schema allows any string → AI applies naming patterns → Returns invented names

---

## Solution: Three-Phase Implementation

### Phase 1: Enum Constraint (CRITICAL FIX)

**Problem:** Current JSON Schema accepts any string
```python
"items": {"type": "string"}  # AI can return anything!
```

**Solution:** Constrain to provided SP catalog
```python
"items": {
    "type": "string",
    "enum": ["CONSUMPTION_PRIMA.spLoadStudyArms", "STAGING_PRIMA.spExtract", ...]
}
```

**Research Basis:**
- OpenAI Structured Outputs (2025): "Use enum for extracting from fixed sets"
- Guarantees AI can ONLY return names from provided list
- Eliminates 100% of hallucinations

**Expected Impact:** 16.4% → 60-70% accuracy

---

### Phase 2: Explicit Instructions

**Problem:** Current prompt assumes AI understands implicit constraint

**Solution:** Add CRITICAL CONSTRAINTS section to system prompt

```markdown
## CRITICAL CONSTRAINTS

1. **ONLY return SP names from the "Available Stored Procedures" list**
2. **DO NOT generate, guess, or invent SP names based on patterns**
3. **Extract table names from actual SQL code, not from SP names**
4. **If no SQL code mentions target table, return empty arrays with confidence 0.0**
5. **Match table names EXACTLY in INSERT/SELECT statements (case-insensitive)**
```

**Research Basis:**
- LLM Structured Output Best Practices (2025): "Explicit beats implicit"
- Reinforces enum constraint with clear instructions
- Reduces creative name generation

**Expected Impact:** Additional 10-15% accuracy improvement

---

### Phase 3: Improved Few-Shot Examples

**Problem:** Current examples don't show constraint enforcement

**Solution:** Add 2 negative examples emphasizing:
1. Correct rejection when SP list provided but no SQL match
2. Exact table name matching (not pattern matching)

**Example 1: Correct Rejection**
```json
**Target:** consumption_finance.payment_tracker

**Available SPs:**
- consumption_finance.sploadpaymenthistory
  ```sql
  insert into [consumption_finance].payment_history
  select transaction_id, amount, date from staging
  ```

**Answer:**
{
  "input_procedures": [],
  "output_procedures": [],
  "confidence": 0.0,
  "reasoning": "SQL code inserts into payment_history, not payment_tracker - no match"
}
```

**Example 2: Pattern Exists But SQL Doesn't Match**
```json
**Target:** consumption_prima.vendor_accounts

**Available SPs:**
- consumption_prima.sploadvendordetails
  ```sql
  insert into [consumption_prima].vendor_details
  select vendor_id, name, status from staging
  ```

**Answer:**
{
  "input_procedures": [],
  "output_procedures": [],
  "confidence": 0.0,
  "reasoning": "sploadvendordetails exists but operates on vendor_details table, not vendor_accounts - no match"
}
```

**Expected Impact:** Additional 5-10% accuracy improvement

---

## Implementation Details

### File 1: `lineage_v3/parsers/ai_disambiguator.py`

**Location:** Lines 573-640 (` _infer_with_ai` method)

**Change 1: Build SP Enum List**
```python
def _infer_with_ai(self, table_schema: str, table_name: str, all_sp_data: List[Dict[str, Any]]) -> Optional[AIResult]:
    """Fallback to AI when rules don't match."""
    try:
        # Build enum list from provided SPs (limit to 50 most relevant to avoid token limits)
        relevant_sps = self._filter_relevant_sps(table_schema, table_name, all_sp_data)[:50]
        sp_enum_list = [f"{sp['schema']}.{sp['name']}" for sp in relevant_sps]

        prompt = self._build_inference_prompt(table_schema, table_name, relevant_sps)
```

**Change 2: Update JSON Schema with Enum**
```python
        # Define JSON Schema with enum constraint
        lineage_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "LineageInferenceResponse",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "input_procedures": {
                            "type": "array",
                            "description": "SPs that READ from target table. MUST be from provided list.",
                            "items": {
                                "type": "string",
                                "enum": sp_enum_list  # ← CRITICAL FIX
                            }
                        },
                        "output_procedures": {
                            "type": "array",
                            "description": "SPs that WRITE to target table. MUST be from provided list.",
                            "items": {
                                "type": "string",
                                "enum": sp_enum_list  # ← CRITICAL FIX
                            }
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence between 0.0-1.0. Use 0.0 if no match found.",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Explain which SQL statements matched or why no match found",
                            "minLength": 10
                        }
                    },
                    "required": ["input_procedures", "output_procedures", "confidence", "reasoning"],
                    "additionalProperties": False
                }
            }
        }
```

### File 2: `lineage_v3/ai_analyzer/inference_prompt.txt`

**Add after line 71 (before "## Output Format"):**

```markdown
## CRITICAL CONSTRAINTS

**YOU MUST FOLLOW THESE RULES:**

1. **ONLY return SP names from the "Available Stored Procedures" list above**
   - DO NOT generate new names based on patterns
   - DO NOT guess names like "spLoad + TableName"
   - The enum constraint will prevent invalid names, but your reasoning should explain your choice

2. **Extract table names from ACTUAL SQL CODE, not from SP names**
   - Look for: `INSERT INTO [schema].[table]`, `SELECT FROM [schema].[table]`
   - Ignore SP naming patterns - they can be misleading

3. **If no SQL code mentions the target table, return empty arrays**
   - Set confidence to 0.0
   - Explain why no match was found in reasoning

4. **Match table names EXACTLY (case-insensitive, ignore brackets)**
   - `[consumption_prima].studyarms` matches target `consumption_prima.studyarms`
   - `[consumption_prima].studyarm` does NOT match `consumption_prima.studyarms`

5. **Pluralization matters**
   - `enrollment_plan` ≠ `enrollment_plans`
   - Only match if SQL code has exact table name

```

**Add 2 new examples (Examples 4 and 5) after Example 3:**

```markdown
### Example 4: Correct Rejection (Pattern Exists But SQL Doesn't Match)
**Target:** consumption_finance.payment_tracker

**Available SP:**
- consumption_finance.sploadpaymenthistory
  ```sql
  truncate table [consumption_finance].payment_history
  insert into [consumption_finance].payment_history
  select transaction_id, amount, payment_date
  from [staging_finance].payments
  ```

**Answer:**
```json
{
  "input_procedures": [],
  "output_procedures": [],
  "confidence": 0.0,
  "reasoning": "SQL code operates on payment_history table, not payment_tracker - no match"
}
```

### Example 5: SP Name Pattern Misleading
**Target:** consumption_prima.vendor_accounts

**Available SP:**
- consumption_prima.sploadvendordetails
  ```sql
  insert into [consumption_prima].vendor_details
  select vendor_id, vendor_name, status, created_date
  from [staging_prima].vendors
  ```

**Answer:**
```json
{
  "input_procedures": [],
  "output_procedures": [],
  "confidence": 0.0,
  "reasoning": "SP name contains 'vendor' but SQL inserts into vendor_details, not vendor_accounts - no match"
}
```
```

---

## Testing Strategy

### Test 1: Enum Constraint (10 tables)

**Objective:** Verify hallucinations eliminated

**Run:**
```bash
cd sqlglot_improvement
../venv/bin/python scripts/test_ai_inference_10.py > test_enum_constraint.log 2>&1
```

**Success Criteria:**
- ✅ Zero "SP not found in catalog" warnings
- ✅ All returned SP names exist in database
- ✅ Accuracy improves from 16.4% → 50-60%

### Test 2: Full Dataset (176 tables)

**Run:**
```bash
cd lineage_v3
../venv/bin/python main.py run --parquet ../parquet_snapshots/ --full-refresh 2>&1 | tee ../sqlglot_improvement/ai_test_iter3_enum_constraint.log
```

**Analyze Results:**
```bash
cd sqlglot_improvement
../venv/bin/python scripts/query_ai_results.py
```

**Success Criteria:**
- ✅ Accuracy: 60-75%
- ✅ Hallucination rate: 0%
- ✅ True positive rate: >50%

### Test 3: Spot-Check Manual Validation (20 tables)

**Sample tables with known relationships:**
1. Tables with `spLoad<TableName>` SPs that exist
2. Tables with similar names but no matching SP
3. Tables with no related SPs (should return empty)

**Success Criteria:**
- ✅ Manual inspection confirms >90% accuracy

---

## Expected Results Timeline

### After Phase 1 (Enum Constraint)
- **Accuracy:** 60-70%
- **Hallucinations:** 0% (eliminated)
- **Time:** 30 minutes implementation + 15 minutes testing

### After Phase 2 (Explicit Instructions)
- **Accuracy:** 70-80%
- **False positives reduced:** Better discrimination
- **Time:** 15 minutes implementation + 10 minutes testing

### After Phase 3 (Improved Few-Shot)
- **Accuracy:** 80-90%
- **Edge cases handled:** Pluralization, pattern mismatches
- **Time:** 30 minutes implementation + 15 minutes testing

### If 90% Not Reached (Phase 4 - Iteration)
- **Collect failed cases** from Phase 3
- **Add real examples** to few-shot
- **Refine SQL extraction** logic
- **Expected:** 90-95% after 1-2 more iterations

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Enum list too large (token limit) | Low | High | Limit to 50 most relevant SPs, already filtered by `_filter_relevant_sps` |
| AI returns too many empty arrays | Medium | Medium | Add more positive examples showing exact matches |
| Enum breaks Azure OpenAI API | Low | High | Test with 10 tables first, fall back to pattern validation if needed |
| 90% target still not met | Low | High | Phase 4: Real failed cases + UAT feedback loop |

---

## Rollback Plan

If enum constraint causes issues:

1. **Keep explicit instructions** (Phase 2) - low risk, high value
2. **Keep improved few-shot** (Phase 3) - low risk, high value
3. **Replace enum with pattern validation** - Post-processing check:
   ```python
   if ai_sp_name not in [f"{sp['schema']}.{sp['name']}" for sp in all_sp_data]:
       logger.warning(f"AI returned invalid SP: {ai_sp_name}")
       return None  # Reject hallucination
   ```

---

## Success Metrics

### Before (Iteration 2):
```
Accuracy: 16.4% (9/55)
Hallucination rate: 69%
True positive: 16.4%
True negative: 14.5%
False positive: 69.1%
```

### After (Target):
```
Accuracy: >90%
Hallucination rate: 0%
True positive: >80%
True negative: >95%
False positive: <5%
```

---

## Next Steps

1. **[30 min]** Implement enum constraint in `ai_disambiguator.py`
2. **[15 min]** Add explicit instructions to `inference_prompt.txt`
3. **[30 min]** Add 2 negative examples to `inference_prompt.txt`
4. **[15 min]** Test on 10 tables
5. **[15 min]** Test on full 176-table dataset
6. **[30 min]** Analyze results and iterate if needed

**Total Time:** ~2.5 hours to reach >90% accuracy

---

## Documentation Updates Required

1. **AI_INFERENCE_MASTER_2025_11_03.md** - Update target accuracy to >90%
2. **PARSER_EVOLUTION_LOG.md** - Document Iteration 3 changes
3. **This document** - Track actual results vs predictions

---

**Status:** ⏳ Ready for implementation
**Priority:** 🚨 CRITICAL - Enum constraint eliminates core failure mode
**Confidence:** HIGH - Research-backed solution with clear expected impact
