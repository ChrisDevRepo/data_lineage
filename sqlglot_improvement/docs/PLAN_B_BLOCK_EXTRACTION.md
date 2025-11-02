# Plan B: Block-Based Extraction with Parameter Replacement

**Date:** 2025-11-02
**Status:** 📋 Proposed Alternative (Requires Analysis & Testing)
**User Request:** Document as optional alternative to Phase 1 preprocessing approach

---

## Overview

Alternative parsing strategy that combines:
1. SQL library comment removal
2. Block-based extraction (BEGIN TRAN/TRY blocks)
3. Parameter value replacement with dummy values
4. Individual block parsing
5. Result merging

---

## Proposed Workflow

### Step 1: Remove Comments
```python
# Use SQL library for proper comment removal
from sqlglot import parse, transpile

# Remove both -- and /* */ comments
cleaned_sql = remove_comments_using_sql_library(ddl)
```

**Why:** Comments can interfere with pattern matching and parsing.

### Step 2: Extract Transaction Blocks
```python
# Extract BEGIN TRAN...END blocks
# Extract BEGIN TRY...END TRY blocks

blocks = extract_blocks(cleaned_sql, patterns=[
    'BEGIN TRAN...END',
    'BEGIN TRY...END TRY'
])

# Ignore ROLLBACK and CATCH blocks (error handling, not lineage)
filtered_blocks = [b for b in blocks if not is_error_handling(b)]
```

**Why:**
- Focus on business logic only (ignore error handling)
- Smaller blocks → simpler parsing
- Can handle multiple transaction boundaries

### Step 3: Replace Parameter Values
```python
# For each block, replace complex parameter assignments with dummy values
# Example transformation:

# BEFORE:
DECLARE @RowCount INT
SET @RowCount = (SELECT COUNT(*) FROM dbo.SourceTable)
INSERT INTO dbo.Target WHERE count > @RowCount

# AFTER:
DECLARE @RowCount INT
SET @RowCount = 1
INSERT INTO dbo.Target WHERE count > 1
```

**Key replacements:**
```python
# Pattern 1: SET with subquery
r'SET\s+(@\w+)\s*=\s*\(SELECT[^\)]+\)'  →  'SET \\1 = 1'

# Pattern 2: DECLARE with initialization
r'DECLARE\s+(@\w+)\s+\w+\s*=\s*[^\n]+'  →  'DECLARE \\1 INT = 1'

# Pattern 3: Parameter references in WHERE/JOIN
# Keep as-is (parameters themselves work in SQLGlot)
```

### Step 4: Parse Each Block Individually
```python
block_results = []
for block in filtered_blocks:
    try:
        ast = sqlglot.parse(block, dialect='tsql')
        lineage = extract_lineage_from_ast(ast)
        block_results.append(lineage)
    except Exception as e:
        log_parse_failure(block, e)
```

**Why:**
- Fewer statements per parse attempt
- Easier to isolate failures
- Can handle complex SPs incrementally

### Step 5: Merge Results
```python
# Combine lineage from all blocks
merged_inputs = set()
merged_outputs = set()

for result in block_results:
    merged_inputs.update(result['inputs'])
    merged_outputs.update(result['outputs'])

return {
    'inputs': list(merged_inputs),
    'outputs': list(merged_outputs),
    'confidence': calculate_merged_confidence(block_results)
}
```

---

## Comparison with Current Approach (Plan A)

| Aspect | **Plan A (Current)** | **Plan B (Proposed)** |
|--------|---------------------|----------------------|
| **Complexity** | Low (simple removal) | **High** (5 steps, block matching, merging) |
| **Code Lines** | ~10 regex patterns | ~200+ lines (parsing, extraction, merging) |
| **Addresses Root Cause** | ✅ Yes (reduces statements) | ✅ Yes (separates statements by block) |
| **Handles Parameters** | N/A (removed) | ✅ Replaces complex values |
| **Edge Cases** | Few | **Many** (nested blocks, incomplete blocks, multiple TRAN) |
| **Testing Effort** | Low (regex validation) | **High** (block matching, edge cases, merging logic) |
| **Maintenance** | Low | **High** (complex logic) |
| **User Directive** | ✅ "Do not overcomplicate" | ⚠️ May violate simplicity requirement |

---

## Technical Challenges

### Challenge 1: Block Matching
**Problem:** Finding matching BEGIN/END pairs in nested structures
```sql
BEGIN TRAN
    BEGIN TRY
        INSERT INTO table1 SELECT * FROM table2

        IF @condition = 1
        BEGIN
            INSERT INTO table3 SELECT * FROM table4
        END
    END TRY
    BEGIN CATCH
        ROLLBACK
    END CATCH
END
```

**Questions:**
- How to match BEGIN TRAN with correct END?
- How to handle nested IF...BEGIN...END blocks?
- What if BEGIN/END pairs are malformed?

**Implementation:**
```python
def extract_blocks(sql: str) -> List[str]:
    """
    Extract BEGIN TRAN/TRY blocks using stack-based matching.
    Complexity: O(n) but requires careful state management.
    """
    stack = []
    blocks = []
    current_block = []

    for token in tokenize(sql):
        if token == 'BEGIN' and next_token in ['TRAN', 'TRY']:
            stack.append((token, next_token))
            current_block.append(token)
        elif token == 'END':
            if stack:
                block_type = stack.pop()
                current_block.append(token)
                if not stack:  # Complete block
                    blocks.append(''.join(current_block))
                    current_block = []

    return blocks
```

### Challenge 2: Parameter Value Replacement
**Problem:** Determining which parameter assignments need replacement

```sql
# Simple case (easy):
SET @count = 100  →  No change needed

# Complex case (need replacement):
SET @count = (SELECT COUNT(*) FROM table)  →  SET @count = 1

# Very complex case:
SET @date = (
    SELECT MAX(modified_date)
    FROM dbo.AuditLog
    WHERE status = 'Active'
)  →  SET @date = GETDATE()  # or SET @date = '2025-01-01'?
```

**Questions:**
- What dummy value for DATETIME parameters?
- What dummy value for VARCHAR parameters?
- Does data type matter for lineage extraction?

### Challenge 3: Merging Results
**Problem:** Combining lineage from multiple blocks

```sql
# Block 1:
INSERT INTO TableA SELECT * FROM TableB

# Block 2:
INSERT INTO TableA SELECT * FROM TableC
```

**Questions:**
- How to handle duplicate inputs (TableB and TableC)?
- How to calculate confidence for merged results?
- What if Block 1 succeeds but Block 2 fails?

**Proposed Logic:**
```python
def calculate_merged_confidence(block_results):
    """
    Options:
    1. Min confidence (pessimistic): min([r['confidence'] for r in block_results])
    2. Avg confidence (balanced): avg([r['confidence'] for r in block_results])
    3. Weighted by statements: sum(r['confidence'] * r['stmt_count']) / total_stmts
    """
    pass
```

---

## Testing Requirements

### Unit Tests Required
1. **Block Extraction**
   - Simple BEGIN TRAN...END
   - Nested BEGIN TRY inside BEGIN TRAN
   - Multiple TRAN blocks in same SP
   - Malformed blocks (missing END)
   - ROLLBACK blocks (should be ignored)

2. **Parameter Replacement**
   - SET with simple value (no change)
   - SET with subquery (replace)
   - DECLARE with initialization (replace)
   - Multiple parameters with same pattern

3. **Result Merging**
   - Two blocks, same input
   - Two blocks, different inputs
   - One block succeeds, one fails
   - Empty blocks

### Integration Tests Required
1. **Real SP Test Cases**
   - spLoadHumanResourcesObjects (667 lines, complex)
   - Simple SP (10 lines, 1 INSERT)
   - SP with multiple TRAN blocks
   - SP with no TRAN blocks

2. **Comparison with Plan A**
   - Run both approaches on 202 SPs
   - Compare confidence scores
   - Compare lineage accuracy
   - Measure performance difference

---

## Advantages vs. Plan A

✅ **Potential Benefits:**
1. **Preserves structure:** Keeps DECLARE/SET statements (debugging easier)
2. **Handles complex SPs:** Block-based extraction might handle very complex SPs better
3. **More granular control:** Can tune replacement patterns per data type
4. **Better error isolation:** Know which block failed vs. whole SP failing

---

## Disadvantages vs. Plan A

❌ **Significant Drawbacks:**
1. **Complexity:** ~20x more code than Plan A
2. **Edge cases:** Nested blocks, malformed SQL, multiple TRAN types
3. **Testing effort:** Requires extensive unit + integration tests
4. **Maintenance:** Complex regex + block matching logic
5. **User directive violation:** "Do not overcomplicate"
6. **Unknown benefit:** May not improve results vs. Plan A
7. **Performance:** More processing steps = slower

---

## SQLGlot Research Findings

**Key Discovery:** The root issue is **statement delimiters**, not parameters

From GitHub Discussion #3095:
> "SQLGlot doesn't understand that the newlines or GO keywords here are used as statement delimiters."

**Implications for Plan B:**
- Block extraction helps by separating statements
- Parameter replacement does **not** address root cause
- Plan A (statement removal) already addresses root cause
- Plan B adds complexity without addressing fundamentally different issue

---

## Recommendation

### Phase 1: Test Current Approach (Plan A) First
1. Run full parse with existing preprocessing
2. Measure improvement: 46 → ? high-confidence SPs
3. **If ≥100 SPs**: Plan A succeeded, no need for Plan B
4. **If <75 SPs**: Consider analyzing Plan B

### Phase 2: If Plan A Insufficient
1. **First:** Analyze why Plan A didn't reach target
   - Are there specific SP patterns that fail?
   - Is statement delimiter still the issue?
   - Or is there a different root cause?

2. **Then:** Design targeted fix
   - If nested blocks are the issue → implement block extraction
   - If parameter data types matter → implement parameter replacement
   - If delimiter mixing → add semicolon insertion

3. **Finally:** Implement and test Plan B incrementally
   - Start with block extraction only
   - Add parameter replacement if needed
   - Compare results at each step

---

## Open Questions (Requires Research)

1. **Block Extraction:**
   - Does SQLGlot provide a tokenizer we can use?
   - How to handle BEGIN...END for IF statements vs. transactions?
   - What about BEGIN DISTRIBUTED TRAN?

2. **Parameter Replacement:**
   - Do parameter data types affect lineage extraction?
   - Can SQLGlot handle parameters in all contexts after replacement?
   - Should we use typed dummy values (1 for INT, '1' for VARCHAR)?

3. **Performance:**
   - How much slower is block extraction vs. simple removal?
   - Does AI simplification (Phase 2) make Plan B unnecessary?

4. **Validation:**
   - How to validate merged lineage accuracy?
   - What's the ground truth for complex SPs with multiple blocks?

---

## Implementation Checklist (If Approved)

- [ ] 1. Research SQLGlot tokenizer for block matching
- [ ] 2. Prototype block extraction on spLoadHumanResourcesObjects
- [ ] 3. Validate block extraction on 10 sample SPs
- [ ] 4. Design parameter replacement patterns
- [ ] 5. Test parameter replacement on 10 sample SPs
- [ ] 6. Implement result merging logic
- [ ] 7. Define confidence calculation for merged results
- [ ] 8. Write unit tests (block extraction, replacement, merging)
- [ ] 9. Write integration tests (full workflow)
- [ ] 10. Run on all 202 SPs and compare with Plan A
- [ ] 11. Analyze improvement (if any)
- [ ] 12. Document results and update strategy

**Estimated Effort:** 2-3 days vs. <1 hour for Plan A

---

## Decision Framework

### Proceed with Plan B if:
✅ Plan A results show <75 high-confidence SPs
✅ Specific block-level patterns identified as failure cause
✅ Block extraction addresses those patterns
✅ User approves complexity increase
✅ Testing resources available

### Stay with Plan A if:
✅ Plan A results show ≥100 high-confidence SPs
✅ No clear benefit from block extraction
✅ Complexity increase not justified
✅ User prefers simpler approach
✅ AI simplification (Phase 2) can handle remaining cases

---

## Summary

**Plan B is a valid alternative** that addresses the root cause (statement delimiters) through block separation instead of statement removal. However, it adds significant complexity and requires extensive testing.

**Recommendation:** Test Plan A first. Only proceed with Plan B if Plan A shows insufficient improvement AND block-level patterns are identified as the root cause.

**Status:** 📋 Documented for future consideration

---

**Next Steps:**
1. Complete Phase 1 testing (Plan A)
2. Measure results
3. Decide if Plan B investigation warranted

---

**User Request Completed:** ✅ Plan B documented as optional alternative requiring detailed analysis and testing
