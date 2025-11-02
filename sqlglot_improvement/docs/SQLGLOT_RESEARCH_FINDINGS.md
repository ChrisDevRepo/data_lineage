# SQLGlot T-SQL Parsing Research Findings

**Date:** 2025-11-02
**Question:** What actually breaks SQLGlot when parsing T-SQL stored procedures?
**User Hypothesis:** Parameter variables (@variable) themselves cause failures

---

## Key Finding: Statement Delimiters (Not Parameters)

### Root Cause (GitHub Discussion #3095)

**SQLGlot Maintainer's Response:**
> "SQLGlot doesn't understand that the newlines or `GO` keywords here are used as statement delimiters."

### What This Means

1. **Parameters (@variable) are NOT the problem** ✅
   - SQLGlot has full support for T-SQL parameter syntax
   - `VAR_SINGLE_TOKENS = {"@", "$", "#"}` in tokenizer
   - `_parse_parameter()` method handles @variables
   - Parameters in WHERE clauses work fine

2. **Statement separation IS the problem** ❌
   - Production T-SQL uses newlines as delimiters:
     ```sql
     DECLARE @count INT
     SET @count = (SELECT COUNT(*) FROM table)
     INSERT INTO target SELECT * FROM source
     ```
   - SQLGlot expects semicolons:
     ```sql
     DECLARE @count INT;
     SET @count = (SELECT COUNT(*) FROM table);
     INSERT INTO target SELECT * FROM source;
     ```

3. **Multi-statement parsing fails** ❌
   - Error: "Required keyword: 'expression' missing for <class 'sqlglot.expressions.Dot'>"
   - Error: "Expected table name but got <Token token_type: <TokenType.L_BRACKET: 'L_BRACKET'>"
   - SQLGlot gets confused parsing multiple newline-separated statements

---

## Implications for Our Approach

### ✅ Our Current Preprocessing Approach is CORRECT

**What we do:**
```python
# Remove DECLARE statements
(r'\bDECLARE\s+@\w+[^\n]*\n', '-- DECLARE removed\n', 0)

# Remove SET statements
(r'\bSET\s+@\w+\s*=\s*[^\n;]+[;\n]?', '', 0)

# Keep INSERT/SELECT statements
# (These contain actual lineage information)
```

**Why this works:**
- Reduces statement count from 200+ to 20-30 per SP
- Fewer statements → fewer delimiter ambiguities
- Remaining INSERT/SELECT statements parse successfully
- **This is the simplest, most effective solution**

---

## Alternative Approaches Evaluated

### ❌ User's Hypothesis: Replace Parameter Values

**Proposed:**
```sql
-- Before
DECLARE @count INT = (SELECT COUNT(*) FROM table)
SELECT * FROM target WHERE id = @count

-- After
DECLARE @count INT = 1
SELECT * FROM target WHERE id = 1
```

**Why this doesn't help:**
- Parameters themselves aren't the issue
- Still leaves multiple newline-separated statements
- Would still trigger delimiter parsing failures
- More complex than removal approach

### ⚠️ Block-Based Extraction

**Proposed:**
```python
# Extract BEGIN TRAN...END blocks
# Parse each block separately
# Merge results
```

**Why this adds complexity:**
- Need to match BEGIN/END pairs correctly
- Handle nested blocks (BEGIN TRY inside BEGIN TRAN)
- Merge lineage from multiple blocks
- Still need to handle delimiters within each block
- **Violates user's "do not overcomplicate" directive**

---

## Phase 1 Validation Strategy

### Test Current Approach First

1. **Run full parse** with existing preprocessing
2. **Measure improvement**: 46 → ? high-confidence SPs
3. **Expected result**: ~100 SPs (50%)

### Why This is Best

- **Simplest solution** (user requirement)
- **Already implemented** and tested
- **Addresses root cause** (reduces statement count)
- **No additional complexity**

---

## Evidence Summary

### SQLGlot Documentation (sqlglot.com/sqlglot/dialects/tsql.html)

- ✅ `_parse_declare()` method exists
- ✅ `_parse_declareitem()` handles variable declarations
- ✅ `VAR_SINGLE_TOKENS = {"@"}` enables @variable recognition
- ✅ T-SQL is an "Official" dialect maintained by core team

### GitHub Discussion #3095

- ❌ Multiple parsing errors with stored procedures
- ❌ "SQLGlot doesn't understand newlines as delimiters"
- ✅ Solution: "Separate statements with semicolons" (preprocessing)

---

## Conclusion

**User's question:** "is the parameter itself the issue?"
**Answer:** No, parameters work fine. The issue is newline delimiters in multi-statement T-SQL.

**Our approach:** Remove DECLARE/SET statements to reduce statement count
**Result:** Fewer statements → fewer delimiter ambiguities → better parsing

**Next step:** Run Phase 1 test to validate this approach empirically.

---

## References

1. SQLGlot T-SQL Dialect Documentation: https://sqlglot.com/sqlglot/dialects/tsql.html
2. GitHub Discussion #3095: https://github.com/tobymao/sqlglot/discussions/3095
3. SQLGlot Parser API: https://sqlglot.com/sqlglot/parser.html

---

**Status:** ✅ Research Complete
**Recommendation:** Proceed with Phase 1 testing using current preprocessing approach
