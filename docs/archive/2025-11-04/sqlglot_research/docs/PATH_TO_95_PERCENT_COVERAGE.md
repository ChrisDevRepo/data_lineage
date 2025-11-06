# Path to 95% Coverage - Action Plan

**Date:** 2025-11-03
**Status:** READY TO IMPLEMENT
**Goal:** Achieve 95-99% coverage for trusted dependency analysis

---

## Executive Summary

**Current State:** 66.8% coverage (510/763 objects) with 33% fake placeholders
**Target:** 95%+ coverage (724/763 objects) with real dependencies
**Strategy:** 3-phase approach using SQLGlot fixes + AI-powered inference

---

## Problem Analysis

### Current Coverage Breakdown
```
Total objects: 763

Real coverage (no placeholders): 510 (66.8%)
├─ SPs (parser): 202 (26.5%)
├─ Views (DMV): 46 (6.0%)
└─ Tables (reverse lookup): 262 (34.3%)

Fake placeholders: 253 (33.2%)
├─ Parser bugs (missed references): 36 (4.7%)
└─ Truly unreferenced: 217 (28.4%)
```

### Root Cause
1. **SQLGlot parser missing references** - 36 tables ARE referenced but parser missed them
2. **No AI fallback currently active** - 217 tables could be resolved with AI
3. **Placeholder hack inflates metrics** - Shows 100% but 33% are fake

---

## Three-Phase Solution

### Phase 1: Fix SQLGlot Parser Bugs
**Target:** 71.6% coverage (546/763 objects)
**Effort:** 4-6 hours
**Priority:** CRITICAL

**Issues Found:**
1. **Dynamic SQL patterns** - `EXEC [sp_name]` not recognized
2. **Subquery contexts** - `IF ((SELECT COUNT(*) FROM [table])` missed
3. **Complex JOIN patterns** - Some table references in JONs not captured

**Implementation:**
- Enhance SQLGlot parser for known patterns
- Add regex fallback for common patterns
- Re-parse affected 36 tables

**Expected Result:** +36 objects with real dependencies

---

### Phase 2: Enable AI for Unreferenced Tables
**Target:** 91-95% coverage (696-724/763 objects)
**Effort:** 6-8 hours
**Priority:** HIGH

**AI Strategies:**

#### Strategy 1: Naming Pattern Inference (~60 tables)
**Pattern:**
```
SP: spLoadArAnalyticsDetailMetrics
Table: ArAnalyticsDetailMetrics
→ AI infers: SP writes to table
```

**Confidence:** 0.80-0.95

#### Strategy 2: Comment/Documentation Analysis (~25 tables)
**Pattern:**
```sql
-- This procedure loads data into TsDurationForAllEmployees
CREATE PROC spLoadEmployeeContractUtilization AS
...
```

**Confidence:** 0.75-0.85

#### Strategy 3: Context-Aware Pattern Matching (~40 tables)
**Pattern:**
```
Schema: CONSUMPTION_FINANCE
SP: spLoad* (ETL pattern)
Table: Same schema, fact/dim table
→ AI understands ETL conventions
```

**Confidence:** 0.70-0.85

#### Strategy 4: Cross-Schema Pipeline Inference (~25 tables)
**Pattern:**
```
STAGING_FINANCE → CONSUMPTION_FINANCE
SP references staging, likely writes to consumption
→ AI maps data pipeline
```

**Confidence:** 0.70-0.80

**Implementation:**
- Update `ai_disambiguator.py` to handle unreferenced tables
- Create new prompts for inference strategies
- Batch process 217 tables through AI
- Validate results with query logs where available

**Expected Result:** +150-178 objects with AI-inferred dependencies

---

### Phase 3: Aggressive AI for Final Push (Optional)
**Target:** 95-99% coverage (724-756/763 objects)
**Effort:** 2-4 hours
**Priority:** MEDIUM

**Strategy:**
- Lower confidence threshold to 0.60-0.70
- Accept uncertain matches for remaining ~67 tables
- Manual review of low-confidence matches

**Trade-off:**
- Higher coverage but some may be false positives
- Label these as "AI-inferred (low confidence)" for transparency

**Expected Result:** +28-60 objects (reaching 95-99%)

---

## Implementation Details

### Step 1: Fix SQLGlot Parser (Phase 1)

**File:** `lineage_v3/parsers/quality_aware_parser.py`

**Changes needed:**

1. **Add regex fallback for missed patterns:**
```python
def _extract_table_references_regex_fallback(self, ddl: str, schema: str) -> Set[str]:
    """
    Regex fallback for patterns SQLGlot misses.

    Patterns to catch:
    - EXEC [schema].[sp_name]
    - IF ((SELECT ... FROM [schema].[table])
    - Complex subqueries
    """
    patterns = [
        r'EXEC\s+\[?(\w+)\]?\.\[?(\w+)\]?',  # EXEC [schema].[sp]
        r'FROM\s+\[?(\w+)\]?\.\[?(\w+)\]?',   # FROM [schema].[table]
        r'JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',   # JOIN [schema].[table]
        r'INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?',   # INTO [schema].[table]
        r'UPDATE\s+\[?(\w+)\]?\.\[?(\w+)\]?', # UPDATE [schema].[table]
    ]
    # Implementation details...
```

2. **Enhance table name resolution:**
```python
def _resolve_exec_pattern(self, exec_statement: str) -> Optional[str]:
    """
    Resolve EXEC [sp_name] to target table.

    Convention: spLoadTableName → TableName
    """
    if 'EXEC' in exec_statement.upper():
        sp_name = extract_sp_name(exec_statement)
        if sp_name.startswith('spLoad'):
            table_name = sp_name.replace('spLoad', '')
            return table_name
    return None
```

**Testing:**
```bash
/sub_DL_OptimizeParsing init --name before_parser_fix
/sub_DL_OptimizeParsing run --mode full --baseline before_parser_fix
# Make changes
/sub_DL_OptimizeParsing run --mode full --baseline before_parser_fix
/sub_DL_OptimizeParsing compare --run1 RUN1 --run2 RUN2
```

**Success criteria:** 36 tables now have dependencies, zero regressions

---

### Step 2: Enable AI for Unreferenced Tables (Phase 2)

**File:** `lineage_v3/parsers/ai_disambiguator.py`

**New method:**
```python
def infer_dependencies_for_unreferenced_table(
    self,
    table_schema: str,
    table_name: str,
    all_sp_ddl: List[Dict[str, str]]
) -> AIResult:
    """
    Use AI to infer dependencies for tables not found in DDL.

    Strategies:
    1. Naming pattern matching (spLoadX → X)
    2. Comment/doc analysis
    3. Context-aware ETL patterns
    4. Cross-schema pipeline inference

    Returns AIResult with confidence 0.60-0.95
    """
    prompt = self._build_inference_prompt(
        table_schema=table_schema,
        table_name=table_name,
        sp_catalog=all_sp_ddl
    )

    # Call Azure OpenAI
    response = self.client.chat.completions.create(
        model=self.deployment,
        messages=[
            {"role": "system", "content": self.inference_system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )

    # Parse and validate
    result = self._parse_ai_response(response)
    validated = self._validate_inference(result, table_schema, table_name)

    return validated
```

**Prompt template:**
```
You are a data lineage expert analyzing SQL Server stored procedures.

Task: Infer which stored procedures interact with table {schema}.{table_name}

Available stored procedures:
{sp_catalog}

Analysis strategies:
1. Naming patterns: spLoad{TableName} likely writes to {TableName}
2. Comments: Look for mentions of {table_name} in comments
3. Schema context: CONSUMPTION tables typically loaded by spLoad* procedures
4. Pipeline flow: STAGING → CONSUMPTION ETL patterns

Return JSON:
{
  "input_procedures": ["schema.sp_name", ...],
  "output_procedures": ["schema.sp_name", ...],
  "confidence": 0.60-0.95,
  "reasoning": "Brief explanation"
}
```

**Integration point:**
```python
# In main.py after Step 4 (SP parsing)
if ai_available:
    unreferenced_tables = get_unreferenced_tables()

    for table in unreferenced_tables:
        ai_result = ai_disambiguator.infer_dependencies_for_unreferenced_table(
            table_schema=table.schema,
            table_name=table.name,
            all_sp_ddl=get_all_sp_ddl()
        )

        if ai_result.is_valid and ai_result.confidence >= 0.70:
            db.update_metadata(
                object_id=table.object_id,
                primary_source='ai',
                confidence=ai_result.confidence,
                inputs=ai_result.sources,
                outputs=ai_result.targets
            )
```

**Testing:**
```bash
# Test with sample unreferenced tables
python3 -c "from lineage_v3.parsers.ai_disambiguator import AIDisambiguator; ..."
```

**Success criteria:** 150+ tables resolved with confidence ≥ 0.70

---

### Step 3: Remove Placeholder Hack

**Files to modify:**
1. `lineage_v3/main.py` - Remove lines 495-523 (Step 7.5)
2. `api/background_tasks.py` - Remove lines 417-438 (Step 5.5)

**Result:** Only real dependencies remain

---

### Step 4: Update System Filters (Post-AI)

**After AI completes, remaining placeholders will be minimal (~7-67 objects)**

**System Filters dropdown:**
```
System Filters: ▼
  [ ] Logging/Admin Objects (ADMIN.*) - ~85 objects
  [ ] Unresolved Objects - ~7-67 objects (AI couldn't determine dependencies)
```

**Category rules:**
1. ADMIN schema → "Logging/Admin" (priority)
2. Remaining unreferenced → "Unresolved"

**Colors:**
- Admin: Light gray, dashed border
- Unresolved: Darker gray, dotted border

---

## Timeline & Effort

| Phase | Task | Effort | Priority |
|-------|------|--------|----------|
| 1 | Fix SQLGlot parser bugs | 4-6 hours | CRITICAL |
| 1 | Remove placeholder hack | 1 hour | HIGH |
| 1 | Testing & validation | 2 hours | HIGH |
| 2 | Implement AI inference | 4-6 hours | HIGH |
| 2 | Batch process 217 tables | 2 hours | HIGH |
| 2 | Validate AI results | 2 hours | MEDIUM |
| 3 | Aggressive AI (optional) | 2-4 hours | LOW |
| 4 | Update System Filters UI | 3-4 hours | MEDIUM |
| 4 | Documentation | 2 hours | MEDIUM |
| **Total** | | **22-31 hours** | |

---

## Expected Results

### After Phase 1 (SQLGlot fixes)
```
Coverage: 546/763 (71.6%)
├─ SPs: 202 (100%)
├─ Views: 60 (98.4%)
└─ Tables: 284 (56.8%)

Quality: All real dependencies, zero fake data
```

### After Phase 2 (AI inference)
```
Coverage: 696-724/763 (91.2-94.9%)
├─ SPs: 202 (100%)
├─ Views: 60 (98.4%)
└─ Tables: 434-462 (86.8-92.4%)

Quality: Mix of parsed + AI-inferred (confidence ≥ 0.70)
```

### After Phase 3 (Aggressive AI - Optional)
```
Coverage: 724-756/763 (94.9-99.1%)

Quality: Includes some low-confidence AI matches (≥ 0.60)
```

---

## Risk Mitigation

### Risk 1: AI False Positives
**Mitigation:**
- Set minimum confidence threshold (0.70)
- Validate against query logs
- Label AI-inferred dependencies clearly
- Allow manual review/override

### Risk 2: Azure OpenAI Costs
**Mitigation:**
- Batch API calls efficiently
- Cache results
- Estimated cost: ~$5-10 for 217 tables

### Risk 3: Performance Impact
**Mitigation:**
- Run AI processing async
- Show progress indicator
- Optional: skip AI for incremental updates

---

## Success Criteria

**Must Have:**
1. ✅ Coverage ≥ 95% (724/763 objects)
2. ✅ Zero fake placeholders (all dependencies are real or AI-inferred)
3. ✅ Clear confidence labeling (parser vs AI)
4. ✅ No regressions in existing coverage

**Should Have:**
1. ✅ Performance < 2 minutes for full refresh with AI
2. ✅ Confidence metrics visible in UI
3. ✅ System filters for admin/unresolved objects

**Nice to Have:**
1. ⭐ Coverage > 97%
2. ⭐ AI reasoning visible in detail view
3. ⭐ Manual dependency override capability

---

## Decision Points

### Decision 1: AI Confidence Threshold
**Options:**
- A) Conservative (≥ 0.80) → Higher quality, ~91% coverage
- B) Balanced (≥ 0.70) → Good quality, ~95% coverage
- C) Aggressive (≥ 0.60) → Some uncertainty, ~97% coverage

**Recommendation:** Start with B, optionally enable C per-user

### Decision 2: AI Processing Timing
**Options:**
- A) Always run AI (even for incremental updates)
- B) Run AI only on full refresh
- C) Run AI on-demand (user-triggered)

**Recommendation:** B - Only on full refresh

### Decision 3: Coverage Metric Display
**Options:**
- A) Show only total coverage (95%)
- B) Show breakdown (95% total, 72% parsed, 23% AI-inferred)
- C) Show confidence bands (High: 72%, Medium: 20%, Low: 3%)

**Recommendation:** A - Single number to avoid confusion (per your requirement)

---

## Next Steps

1. **Review this document** - Ensure alignment with requirements
2. **Approve approach** - Confirm 3-phase strategy
3. **Prioritize phases** - All 3 or stop at Phase 2?
4. **Start implementation** - Begin with Phase 1 (parser fixes)

---

## Documentation Updates Needed

**After implementation, update:**
1. `README.md` - Coverage expectations (95%+)
2. `docs/PARSING_USER_GUIDE.md` - AI inference explanation
3. `docs/AI_DISAMBIGUATION_SPEC.md` - New inference strategies
4. `docs/PARSER_EVOLUTION_LOG.md` - Record changes
5. `sqlglot_improvement/` - Archive as "RESOLVED"

---

**STARTING POINT FOR IMPLEMENTATION:**

📄 **This document (`docs/PATH_TO_95_PERCENT_COVERAGE.md`)**

This is the master plan. Implementation starts with:
1. Phase 1, Step 1: Fix SQLGlot parser
2. File: `lineage_v3/parsers/quality_aware_parser.py`
3. Method: `_extract_dependencies_sqlglot()` - add regex fallback

---

**Status:** ✅ Ready to begin
**Awaiting:** Your approval to start Phase 1
