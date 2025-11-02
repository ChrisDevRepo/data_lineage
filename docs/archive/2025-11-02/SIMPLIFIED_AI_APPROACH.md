# Simplified AI Approach - No Overcomplication

**User Feedback:** "i do not want to overcomplicate it to have different approaches checks for the same goal"

---

## Current Overcomplicated Approach ❌

```python
# Parse with SQLGlot
parser_result = sqlglot_parse(ddl)

# Parse with regex as fallback
regex_result = regex_parse(ddl)

# Merge results
merged = merge(parser_result, regex_result)

# Calculate confidence
confidence = calculate_confidence(merged)

# IF low confidence:
if confidence <= 0.85 and ai_enabled:
    # 1. Find ambiguous references (only unqualified names)
    ambiguous_refs = extract_ambiguous_references(ddl)

    # 2. Loop through each ambiguous ref
    for ref in ambiguous_refs[:3]:
        # 3. Find candidates for this specific ref
        candidates = find_candidates(ref)

        # 4. Call AI to pick ONE table
        ai_result = disambiguator.disambiguate(
            reference=ref,
            candidates=candidates,
            sql_context=ddl
        )

        # 5. Merge AI result with parser result
        merged = merge(merged, ai_result)
```

**Problems:**
1. ❌ Multiple parsing approaches (SQLGlot + regex + AI)
2. ❌ Complex merging logic
3. ❌ AI only called for "ambiguous references" (unqualified names)
4. ❌ AI called per-table, not for full lineage
5. ❌ Doesn't work if parser extracted nothing (0 dependencies)

---

## Simplified Approach ✅

```python
# Try basic parsing first (SQLGlot + regex)
parser_result = parse(ddl)
confidence = calculate_confidence(parser_result)

# IF low confidence → just send to AI
if confidence <= 0.85 and ai_enabled:
    ai_result = disambiguator.extract_lineage(
        ddl=ddl,
        object_id=object_id
    )

    # Use AI result (don't merge, just replace)
    return ai_result
```

**Benefits:**
1. ✅ Single decision point: low confidence → AI
2. ✅ No merging logic
3. ✅ No special cases (ambiguous refs, zero deps, etc.)
4. ✅ AI handles ALL cases (unqualified names, complex SQL, parser bugs)
5. ✅ Simple and maintainable

---

## Why Current Approach Is Overcomplicated

### Multiple Code Paths for Same Goal

**Goal:** Extract table dependencies from SP

**Current paths:**
1. SQLGlot parser → extracts tables
2. Regex fallback → extracts tables
3. Merge logic → combines results
4. Ambiguous ref detection → finds specific problems
5. AI disambiguation → fixes specific problems
6. Merge AI results → combines again

**Simplified:**
1. Try parser (SQLGlot + regex)
2. If low confidence → AI extracts everything
3. Done

### Trying to Be "Smart" About AI Usage

**Current thinking:**
- "Only call AI for ambiguous references to save cost"
- "Try to merge AI results with parser results"
- "Call AI per-table to be more precise"

**Reality:**
- AI call costs ~$0.002 per SP (negligible)
- Merging adds complexity and bugs
- Parser bugs mean AI never called in many cases

**Better approach:**
- If confidence low → trust AI completely
- No partial fixes, just replace result

---

## What User Is Saying

> "i do not want to overcomplicate it to have different approaches checks for the same goal"

Translation:
- Don't have SQLGlot + regex + ambiguous ref detection + AI
- Just have: parser tries → if fails → AI
- One simple decision point

---

## Proposed Simple Implementation

### Step 1: Remove Ambiguous Reference Logic

**DELETE this entire section** (lines 286-328):
```python
# Find ambiguous references (unqualified table names in DDL)
ambiguous_refs = self._extract_ambiguous_references(ddl, regex_sources, regex_targets)

logger.info(f"AI trigger: confidence {confidence:.2f} ≤ {ai_threshold}, found {len(ambiguous_refs)} ambiguous refs")

# Attempt AI disambiguation for each ambiguous reference
for ref_info in ambiguous_refs[:3]:
    # ... 40 lines of complex logic ...
```

### Step 2: Replace with Simple AI Call

```python
if confidence <= ai_threshold and ai_enabled:
    try:
        from lineage_v3.parsers.ai_disambiguator import AIDisambiguator

        # Get SP name for logging
        sp_info = self._get_object_info(object_id)
        sp_name = f"{sp_info['schema']}.{sp_info['name']}" if sp_info else f"object_{object_id}"

        # Initialize disambiguator
        disambiguator = AIDisambiguator(self.workspace)

        # Just send full DDL to AI - no overthinking
        logger.info(f"Low confidence ({confidence:.2f}) - sending to AI for full extraction")

        ai_result = disambiguator.extract_lineage(
            ddl=ddl,
            object_id=object_id,
            sp_name=sp_name
        )

        if ai_result and ai_result.is_valid:
            # Use AI result (replace, don't merge)
            input_ids = ai_result.sources
            output_ids = ai_result.targets
            confidence = ai_result.confidence

            logger.info(f"✅ AI extracted {len(input_ids)} inputs, {len(output_ids)} outputs (confidence: {confidence:.2f})")

    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
```

**That's it!** 40 lines of complex logic → 20 lines of simple logic

### Step 3: Simplify AI Disambiguator

**Current:** `disambiguate(reference, candidates, ...)`
- Takes single table name
- Returns single resolved table
- Called multiple times per SP

**New:** `extract_lineage(ddl, object_id, sp_name)`
- Takes full DDL
- Returns complete lineage (all inputs + outputs)
- Called once per SP

---

## AI Prompt (Simple)

```python
EXTRACTION_PROMPT = """
Extract table-level lineage from this SQL stored procedure.

Instructions:
1. List ALL input tables (FROM, JOIN)
2. List ALL output tables (INSERT, UPDATE, MERGE, TRUNCATE, DELETE)
3. Use qualified names: schema.table
4. Exclude:
   - Temp tables (#temp)
   - Table variables (@var)
   - System tables (sys.*, INFORMATION_SCHEMA.*)
   - Utility SPs (LogMessage, spLastRowCount)

Return JSON:
{{
  "inputs": ["STAGING_PRIMA.HREmployees", ...],
  "outputs": ["CONSUMPTION_PRIMA.HrContracts", ...]
}}

DDL:
{ddl}
"""
```

**That's the entire prompt!** No:
- No few-shot examples (AI models are smart enough)
- No complex instructions
- No edge case handling
- Just: "extract inputs and outputs"

---

## Comparison

### Current: Complicated ❌
```
Parse → Calculate confidence → Extract ambiguous refs →
Loop refs → Find candidates → Disambiguate each →
Merge results → Recalculate confidence
```

**Lines of code:** ~200
**Code paths:** 5+
**Special cases:** 3 (ambiguous refs, zero deps, parse errors)

### Proposed: Simple ✅
```
Parse → Calculate confidence → If low → AI extracts → Done
```

**Lines of code:** ~50
**Code paths:** 2 (parser or AI)
**Special cases:** 0

---

## Expected Results

### Before (Overcomplicated)
- spLoadHumanResourcesObjects: 0 inputs, 0 outputs ❌
  - Why: Ambiguous ref detection found 0 unqualified names → AI not called
- 156 low-confidence SPs with qualified names: AI not called ❌

### After (Simple)
- spLoadHumanResourcesObjects: 1 input, 20 outputs ✅
  - Why: Low confidence → AI called → extracted everything
- 156 low-confidence SPs: All sent to AI ✅
  - Expected: 80%+ move to high confidence

---

## User's Point

The current code is trying to be "clever":
- "Let's only call AI for specific cases"
- "Let's merge AI results with parser results"
- "Let's handle different scenarios differently"

**User says:** Stop being clever. Just use AI when confidence is low.

**He's right!** The simple approach:
1. Easier to understand
2. Easier to maintain
3. Fewer bugs
4. Better results

---

## Implementation Plan

### Phase 1: Simplify Parser (1 hour)
1. Remove `_extract_ambiguous_references()` method
2. Replace ambiguous ref loop with single AI call
3. Change AI call from `disambiguate()` to `extract_lineage()`

### Phase 2: Simplify AI Disambiguator (2 hours)
1. Rename `disambiguate()` to `extract_lineage()`
2. Simplify prompt (remove few-shot examples)
3. Return complete lineage, not single table

### Phase 3: Test (1 hour)
1. Test with spLoadHumanResourcesObjects
2. Verify 156 low-confidence SPs now processed by AI
3. Check confidence improvement

**Total time:** 4 hours

---

## Conclusion

**User is 100% correct:**
- Current approach is overcomplicated
- Multiple parsing strategies for same goal
- Special cases and edge case handling
- Complex merging logic

**Simple approach:**
- Parser tries first
- If low confidence → AI takes over
- No merging, no special cases
- Clean and maintainable

**The rule:** Don't try to be clever. Use the tool that works (AI) when the simple tool (parser) doesn't.

---

**Author:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-02
**Status:** ✅ ANALYSIS COMPLETE - READY TO SIMPLIFY
