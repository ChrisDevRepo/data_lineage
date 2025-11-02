# Preprocessing Approach Comparison

**Date:** 2025-11-02

---

## Three Approaches to Fix SQLGlot Delimiter Issue

### Root Cause (SQLGlot GitHub #3095)
> "SQLGlot doesn't understand that the newlines or GO keywords here are used as statement delimiters."

---

## Comparison Table

| | **Plan A (Current)** | **Plan A.5 (User's Insight)** | **Plan B (Alternative)** |
|---|---|---|---|
| **Method** | Remove DECLARE/SET | Add semicolons | Block extraction + merge |
| **DDL Size** | -9,567 chars (-27%) | +193 chars (+0.5%) | Unknown |
| **Statements** | 193 → 20 | 193 → 193 | 193 → ? |
| **Code Lines** | ~10 regex patterns | ~8 regex patterns | ~200+ lines |
| **Complexity** | Low | **Very Low** | Very High |
| **Implementation** | ✅ Complete | ⏭️ 30 minutes | ⏭️ 2-3 days |
| **Testing** | ✅ Tested (78 SPs) | ⏭️ Needs testing | ⏭️ Not started |
| **Preserves Code** | ❌ No (removed) | ✅ **Yes** | ✅ Yes |
| **Root Cause Fix** | Indirect (fewer statements) | **Direct (adds delimiters)** | Direct (separates blocks) |
| **User Directive** | ✅ Simple | ✅ **Simplest** | ❌ Overcomplicated |
| **Expected Result** | 78 SPs (38.6%) | 100+ SPs? | Unknown |

---

## Detailed Breakdown

### Plan A (Current - Statement Removal)

**Input:**
```sql
DECLARE @count INT
SET @count = (SELECT COUNT(*) FROM dbo.SourceTable)
INSERT INTO dbo.Target SELECT * FROM dbo.Source
```

**Output:**
```sql
-- DECLARE removed

INSERT INTO dbo.Target SELECT * FROM dbo.Source
```

**Result:** 78/202 SPs (38.6%) - Partial success

---

### Plan A.5 (User's Insight - Semicolon Addition) ⭐

**Input:**
```sql
DECLARE @count INT
SET @count = (SELECT COUNT(*) FROM dbo.SourceTable)
INSERT INTO dbo.Target SELECT * FROM dbo.Source
```

**Output:**
```sql
DECLARE @count INT;
SET @count = (SELECT COUNT(*) FROM dbo.SourceTable);
INSERT INTO dbo.Target SELECT * FROM dbo.Source;
```

**Result:** Unknown (needs testing) - Expected: 100+ SPs

**Why Better:**
- ✅ Directly addresses delimiter ambiguity
- ✅ Preserves all code (better debugging)
- ✅ Simpler than Plan A (just add semicolons)
- ✅ Zero double semicolons (validated)
- ✅ ANSI SQL compliant
- ✅ Minimal DDL changes (+0.5% vs -27%)

---

### Plan B (Alternative - Block Extraction)

**Input:**
```sql
BEGIN TRAN
  DECLARE @count INT
  SET @count = (SELECT COUNT(*) FROM dbo.SourceTable)
  INSERT INTO dbo.Target SELECT * FROM dbo.Source
END
```

**Output:**
```sql
# Extract blocks
block1 = "DECLARE @count INT; SET @count = 1; INSERT INTO ..."

# Parse each block
lineage1 = parse(block1)

# Merge results
final_lineage = merge([lineage1, ...])
```

**Why Deferred:**
- ❌ High complexity (block matching, nesting, merging)
- ❌ Many edge cases (nested blocks, malformed SQL)
- ❌ Unknown benefit
- ❌ Violates "do not overcomplicate" directive
- ❌ 2-3 days implementation vs 30 minutes for A.5

---

## Research Validation

### T-SQL Semicolons
✅ **ANSI SQL-92 standard** statement terminators
✅ **Microsoft recommended** practice
✅ **Required** for some T-SQL features (CTEs, MERGE, THROW)
✅ **Future-proof** (may become mandatory)
✅ **Double semicolons** valid but avoided by our pattern

### SQLGlot Support
✅ **Expects semicolons** as delimiters
✅ **`parse()` function** returns array for multiple statements
✅ **T-SQL dialect** has full support via `_parse_declare()`, `_parse_parameter()`
✅ **Should handle** properly delimited statements

---

## Testing Results

### Semicolon Addition Pattern (spLoadHumanResourcesObjects)
```
Original DDL: 35,609 characters, 193 statements
After semicolons: 35,802 characters (+193), 193 statements
Semicolons added: 193
Double semicolons: 0 ✅
```

### Sample Output
```sql
DECLARE @RowCount INT;
SET @RowCount = (SELECT COUNT(*) FROM STAGING_PRIMA.[HrContracts]);
INSERT INTO CONSUMPTION_PRIMA.[HrContracts]
    SELECT * FROM STAGING_PRIMA.[HrContracts];
```

Clean, properly delimited SQL that SQLGlot should parse correctly!

---

## Recommendation: Test Plan A.5 First

### Why Priority #1
1. **User's brilliant insight** directly addresses root cause
2. **Simpler than all alternatives** (30 min vs hours/days)
3. **Could achieve Phase 1 goal** (100 SPs) without complexity
4. **Low risk, high potential** (easy to revert if fails)
5. **Better developer experience** (preserved code)

### Testing Steps (1 hour)
1. ⏭️ Modify preprocessing patterns in `quality_aware_parser.py`
2. ⏭️ Run full parse on 202 SPs
3. ⏭️ Measure: Plan A.5 vs Plan A (? vs 78)
4. ⏭️ Decide:
   - If ≥100 SPs: ✅ Adopt A.5, proceed to Phase 2
   - If 78-99 SPs: ⚠️ Marginal, evaluate
   - If <78 SPs: ❌ Revert to Plan A

---

## Decision Matrix

```
                        Simplicity  Effectiveness  Risk  Time
Plan A (Current)        ████░░      ███░░░         ██░░  ✅ Done
Plan A.5 (Semicolons)   █████░      ████░?         ██░░  30 min
Plan B (Blocks)         ██░░░░      ???░?          ████  2-3 days
```

**Winner:** Plan A.5 (optimal simplicity/effectiveness ratio)

---

## Summary

**User's Question:** "Could we not just add a semicolon for each declare?"

**Answer:** 💡 **Brilliant!** This is likely the optimal solution.

**Why:**
- ✅ Addresses root cause (delimiter ambiguity)
- ✅ Simpler than removal or block extraction
- ✅ Preserves code structure
- ✅ ANSI SQL compliant
- ✅ Validated on test cases

**Status:** Ready for implementation and testing

**Next Action:** Test Plan A.5 on full dataset (202 SPs) to measure improvement over Plan A's 78 SPs

---

**Comparison Files:**
- `PLAN_A5_SEMICOLON_ADDITION.md` - Detailed analysis
- `test_semicolon_addition.py` - Pattern validation
- `spLoadHumanResourcesObjects_WITH_SEMICOLONS.sql` - Sample output
