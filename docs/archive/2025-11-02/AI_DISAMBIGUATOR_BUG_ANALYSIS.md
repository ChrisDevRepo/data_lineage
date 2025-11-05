# AI Disambiguator Not Triggered - Root Cause Analysis

**Date:** 2025-11-02
**Issue:** spLoadHumanResourcesObjects (0.50 confidence, 0 dependencies) was NOT passed to AI
**Reporter:** User question: "i do not understand why ai did not found it or why it was not passed to ai"

---

## TL;DR - The Bug

**Problem:** AI disambiguator only triggers for **unqualified table names**, not for **total parsing failures**

**Result:** SPs with 0 dependencies + qualified table names = AI never called

**Fix:** Add fallback: If confidence ≤ threshold AND no dependencies found → send full DDL to AI

---

## Current AI Trigger Logic

### Code Location: `quality_aware_parser.py:275-290`

```python
if confidence <= ai_threshold and ai_enabled:
    # Find ambiguous references (unqualified table names in DDL)
    ambiguous_refs = self._extract_ambiguous_references(ddl, regex_sources, regex_targets)

    logger.info(f"AI trigger: confidence {confidence:.2f} ≤ {ai_threshold}, found {len(ambiguous_refs)} ambiguous refs")

    # Attempt AI disambiguation for each ambiguous reference
    for ref_info in ambiguous_refs[:3]:  # Limit to top 3 to control cost
        # ... call AI ...
```

### What `_extract_ambiguous_references` Does (`quality_aware_parser.py:1070-1100`)

```python
def _extract_ambiguous_references(self, ddl, regex_sources, regex_targets):
    """
    Extract ambiguous table references (unqualified names) from DDL.

    An ambiguous reference is a table name WITHOUT SCHEMA QUALIFICATION
    that could refer to multiple tables in different schemas.
    """
    ambiguous = []

    # Pattern to find unqualified table references (single identifier, not schema.table)
    unqualified_pattern = r'\b(?:FROM|JOIN|INSERT\s+INTO|UPDATE|MERGE)\s+(\w+)\b'

    matches = re.findall(unqualified_pattern, ddl, re.IGNORECASE)

    for unqualified_name in set(matches):
        # Skip temp tables
        if unqualified_name.startswith('#') or unqualified_name.startswith('@'):
            continue

        # Find candidate schemas for this table name
        candidates = self._find_candidate_objects(unqualified_name)

        if len(candidates) > 1:  # Truly ambiguous
            ambiguous.append({
                'reference': unqualified_name,
                'candidates': candidates
            })

    return ambiguous
```

---

## Why spLoadHumanResourcesObjects Was NOT Sent to AI

### Confidence Trigger: ✅ PASSED
- SP confidence: 0.50
- AI threshold: 0.85
- 0.50 ≤ 0.85 → **Should trigger AI**

### Ambiguous References Check: ❌ FAILED
- Pattern looks for: `FROM Customers` (unqualified)
- Actual DDL has: `FROM CONSUMPTION_PRIMA.HrContracts` (qualified)
- Result: **0 ambiguous references found**
- AI loop never executes!

### Evidence from DDL

All table references in spLoadHumanResourcesObjects are **fully qualified**:

```sql
-- Qualified with schema
SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrContracts
SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrDepartments
INSERT INTO CONSUMPTION_PRIMA.[HrContracts] (...)
SELECT * FROM [STAGING_PRIMA].HREmployees

-- NOT unqualified like:
SELECT * FROM HrContracts  ← This would trigger AI
```

Regex pattern `\b(?:FROM|JOIN|INSERT\s+INTO)\s+(\w+)\b` matches:
- ✅ `FROM Customers` → captures "Customers"
- ❌ `FROM dbo.Customers` → no match (has schema prefix)
- ❌ `FROM [dbo].[Customers]` → no match (has brackets and schema)

---

## Design Flaw: AI Only for Disambiguation, Not Extraction

### Original Intent (Correct Use Case)

**Scenario:** Parser extracts unqualified table names but doesn't know which schema

```sql
CREATE PROC spExample AS
BEGIN
    SELECT * FROM Customers  -- Which schema?
    INSERT INTO Orders       -- Which schema?
END
```

**AI Disambiguator:**
1. Finds "Customers" (unqualified)
2. Queries catalog: `dbo.Customers`, `staging.Customers`, `archive.Customers`
3. Sends to AI: "Which schema does 'Customers' belong to in this context?"
4. AI analyzes DDL and picks correct schema

**Result:** ✅ Works great for schema disambiguation

### Current Problem (Wrong Use Case)

**Scenario:** Parser completely fails to extract any table names

```sql
CREATE PROC spLoadHumanResourcesObjects AS
BEGIN
    -- 667 lines of complex SQL
    INSERT INTO CONSUMPTION_PRIMA.[HrContracts] (...)  -- Parser misses this
    SELECT * FROM [STAGING_PRIMA].HREmployees           -- Parser misses this
    -- ... 18 more INSERT/SELECT statements all missed
END
```

**AI Disambiguator:**
1. Looks for unqualified names → finds 0 (all tables are qualified)
2. `ambiguous_refs = []`
3. Loop doesn't execute
4. AI never called

**Result:** ❌ AI never gets a chance to help

---

## Why Parser Failed (Secondary Issues)

### 1. SQLGlot Parser Failure
- DDL too large (35KB, 667 lines)
- Complex nested IF/TRY/CATCH blocks
- Multi-line INSERT statements
- Result: Parser returns empty list

### 2. Regex Fallback Failure
- Should have extracted qualified names from INSERT/SELECT
- Somehow also returned empty list (needs investigation)
- Result: 0 sources, 0 targets

### 3. Confidence Calculation
- No sources + no targets = 0.50 confidence (minimum)
- Correctly flagged as low confidence ✅
- But AI trigger condition not met ❌

---

## The Fix: Add Zero-Dependency Fallback

### Current Logic (Insufficient)
```python
if confidence <= ai_threshold and ai_enabled:
    ambiguous_refs = self._extract_ambiguous_references(...)

    if len(ambiguous_refs) == 0:
        # No ambiguous refs → AI not called ❌
        pass
```

### Fixed Logic (Complete)
```python
if confidence <= ai_threshold and ai_enabled:
    ambiguous_refs = self._extract_ambiguous_references(...)

    if len(ambiguous_refs) > 0:
        # Normal path: Disambiguate unqualified names
        for ref_info in ambiguous_refs[:3]:
            ai_result = disambiguator.disambiguate(...)
            # ... merge results ...

    elif len(input_ids) == 0 and len(output_ids) == 0:
        # NEW: Fallback for total parsing failure
        # If no dependencies extracted AND low confidence → ask AI to extract everything
        logger.info(f"Zero dependencies extracted for low-confidence SP - invoking AI full extraction")

        ai_result = disambiguator.extract_full_lineage(
            ddl=ddl,
            object_id=object_id,
            sp_name=sp_name
        )

        if ai_result and ai_result.is_valid:
            input_ids = ai_result.sources
            output_ids = ai_result.targets
            confidence = ai_result.confidence  # Boost to 0.85-0.95

            logger.info(f"AI full extraction: {len(input_ids)} inputs, {len(output_ids)} outputs, confidence {confidence:.2f}")
```

---

## New Method Needed: `extract_full_lineage`

### Current: `disambiguate()` - For Single Table Resolution
```python
def disambiguate(
    self,
    reference: str,        # Single unqualified table name
    candidates: List[str], # Possible schemas
    sql_context: str,      # DDL for context
    parser_result: Dict,   # What parser found
    sp_name: str
) -> DisambiguationResult:
    """Pick which schema this table belongs to."""
```

### New: `extract_full_lineage()` - For Complete Parsing Failure
```python
def extract_full_lineage(
    self,
    ddl: str,              # Full DDL text
    object_id: int,        # SP object ID
    sp_name: str           # SP name for logging
) -> DisambiguationResult:
    """
    Extract ALL table dependencies when parser completely fails.

    Use case: Large/complex SPs where SQLGlot and regex both fail.

    Prompt:
    - "Extract ALL input tables (FROM, JOIN)"
    - "Extract ALL output tables (INSERT, UPDATE, MERGE, TRUNCATE)"
    - Return qualified names (schema.table)
    - Exclude temp tables, table variables, utility SPs

    Returns:
        DisambiguationResult with:
        - sources: List of input object_ids
        - targets: List of output object_ids
        - confidence: 0.85-0.95 based on validation
        - is_valid: True if passed validation
    """
```

---

## Implementation Steps

### 1. Add Zero-Dependency Check (`quality_aware_parser.py:290`)
```python
# After extracting ambiguous_refs
if len(ambiguous_refs) > 0:
    # Existing path: disambiguate specific tables
    for ref_info in ambiguous_refs[:3]:
        # ... existing code ...

elif len(input_ids) == 0 and len(output_ids) == 0:
    # NEW: Parser extracted nothing → full AI extraction
    logger.warning(f"Zero dependencies for {sp_name} with confidence {confidence:.2f} - invoking AI full extraction")

    ai_result = disambiguator.extract_full_lineage(
        ddl=ddl,
        object_id=object_id,
        sp_name=sp_name
    )

    if ai_result and ai_result.is_valid:
        input_ids = ai_result.sources
        output_ids = ai_result.targets
        confidence = ai_result.confidence

        logger.info(f"✅ AI extracted {len(input_ids)} inputs, {len(output_ids)} outputs")
```

### 2. Implement `extract_full_lineage()` (`ai_disambiguator.py`)
```python
def extract_full_lineage(
    self,
    ddl: str,
    object_id: int,
    sp_name: str
) -> Optional[DisambiguationResult]:
    """Extract complete lineage when parser fails."""

    # Build few-shot prompt with examples of large ETL SPs
    prompt = self._build_full_extraction_prompt(ddl, sp_name)

    # Call Azure OpenAI
    response = self._call_openai(prompt)

    # Parse JSON response
    extracted_tables = self._parse_ai_response(response)

    # Resolve table names to object_ids
    source_ids = self._resolve_to_object_ids(extracted_tables['inputs'])
    target_ids = self._resolve_to_object_ids(extracted_tables['outputs'])

    # Validate results (catalog check, schema consistency, query log)
    validation_result = self._validate_ai_result(source_ids, target_ids, sp_name)

    # Calculate confidence based on validation
    confidence = 0.85 if validation_result.is_valid else 0.70

    return DisambiguationResult(
        sources=source_ids,
        targets=target_ids,
        confidence=confidence,
        is_valid=validation_result.is_valid,
        validation_details=validation_result
    )
```

### 3. Add Prompt Template
```python
FULL_EXTRACTION_PROMPT = """
You are analyzing a SQL stored procedure to extract table-level data lineage.

Task: Extract ALL input tables and output tables from the DDL below.

Instructions:
1. Input Tables: Tables read via SELECT, FROM, JOIN
2. Output Tables: Tables written via INSERT, UPDATE, MERGE, TRUNCATE, DELETE
3. Return ONLY schema-qualified names (e.g., "dbo.Customers", not "Customers")
4. EXCLUDE:
   - Temp tables (#temp)
   - Table variables (@var)
   - System tables (sys.*)
   - Utility SPs (LogMessage, spLastRowCount, etc.)

Return JSON format:
{{
  "inputs": ["STAGING_PRIMA.HREmployees", "CONSUMPTION_PRIMA.HrContracts"],
  "outputs": ["CONSUMPTION_PRIMA.HrContracts", "CONSUMPTION_PRIMA.HrDepartments"]
}}

Stored Procedure DDL:
{ddl}

JSON Response:
"""
```

---

## Expected Impact

### Before Fix
- **spLoadHumanResourcesObjects:** 0 inputs, 0 outputs, 0.50 confidence ❌
- **Other large ETL SPs:** Likely same problem
- **AI usage:** Only for schema disambiguation (narrow use case)

### After Fix
- **spLoadHumanResourcesObjects:** 1+ inputs, 20 outputs, 0.85+ confidence ✅
- **Other large ETL SPs:** AI extraction as fallback
- **AI usage:** Full lineage extraction when parser fails (broad use case)

### Statistics Impact
- **Current:** 46/202 SPs at ≥0.85 confidence (22.8%)
- **Expected:** 160+/202 SPs at ≥0.85 confidence (79%+)
- **Improvement:** +114 SPs moved from low to high confidence

---

## Testing

### Test Case 1: spLoadHumanResourcesObjects
```python
def test_ai_full_extraction():
    # Setup
    sp_name = "CONSUMPTION_PRIMA.spLoadHumanResourcesObjects"
    object_id = 1235104157
    ddl = load_ddl(object_id)

    # Parse (should trigger AI fallback)
    result = parser.parse(object_id, ddl)

    # Assertions
    assert len(result['inputs']) > 0, "Should extract input tables"
    assert len(result['outputs']) >= 15, "Should extract ~20 output tables"
    assert result['confidence'] >= 0.85, "AI should boost confidence"
    assert object_id not in result['inputs'], "No self-reference"
```

### Test Case 2: Verify AI Log Entry
```bash
# Should see in logs:
# "Zero dependencies for CONSUMPTION_PRIMA.spLoadHumanResourcesObjects with confidence 0.50 - invoking AI full extraction"
# "✅ AI extracted 1 inputs, 20 outputs"
```

---

## Cost/Performance Considerations

### AI API Calls
- **Before:** ~40 calls (only for ambiguous refs)
- **After:** ~40 + ~156 = ~196 calls (ambiguous refs + zero-dep SPs)
- **Cost:** ~$0.20 per full extraction (gpt-4.1-nano)
- **Total:** ~$30 for full run (acceptable)

### Performance
- AI calls run sequentially (not parallel)
- Each call: ~2-5 seconds
- Total added time: ~10-15 minutes for 156 SPs
- **Acceptable:** Incremental mode only re-parses modified SPs

---

## Conclusion

### Root Cause
AI disambiguator designed for **schema disambiguation** (narrow use case), not **full lineage extraction** (broad use case).

### Why Bug Went Unnoticed
- Original design assumed parser would always extract SOME tables
- Didn't account for complete parsing failure (0 dependencies)
- Test cases only covered disambiguation scenarios, not extraction failures

### Simple Fix
Add fallback: If `confidence ≤ threshold AND no dependencies → call AI to extract everything`

### User-Visible Impact
- ✅ SPs with "no connection" will now show correct lineage
- ✅ High-confidence rate: 22.8% → 79%+
- ✅ No user action required (automatic fallback)

---

**Author:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-02
**Version:** v3.8.0
**Status:** 🐛 BUG IDENTIFIED - FIX PENDING
