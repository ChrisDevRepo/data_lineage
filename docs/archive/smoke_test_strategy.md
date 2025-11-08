# Smoke Test Strategy: What Should Count?

## Current Problem

**Smoke Test (Raw DDL):** Counts EVERYTHING (4 table refs)
**Parser (Cleaned DDL):** Counts BUSINESS LOGIC only (2 table refs)
**Result:** 50% completeness → 75% confidence (false warning!)

## Key Insight

Smoke test should:
- ✅ Run on RAW DDL (to detect aggressive cleaning)
- ✅ Count only BUSINESS LOGIC dependencies (to match parser intent)

This is NOT the same as cleaning the DDL - we're being selective about COUNTING.

---

## Proposed Solution

**Smoke test pattern matching (on raw DDL):**

### COUNT as business logic:
```python
# DML operations (data transformation)
INSERT INTO Target          # ✅ Count
UPDATE Target SET          # ✅ Count
DELETE FROM Target         # ✅ Count
MERGE INTO Target          # ✅ Count

# Main query sources
SELECT ... FROM Source     # ✅ Count
JOIN Source2               # ✅ Count
```

### DO NOT COUNT (housekeeping/administrative):
```python
# DDL housekeeping
TRUNCATE TABLE Target      # ❌ Don't count (housekeeping, not transformation)

# Administrative queries in variables
SET @var = (SELECT COUNT(*) FROM Table)        # ❌ Don't count (admin)
DECLARE @var = (SELECT COUNT(*) FROM Table)    # ❌ Don't count (admin)

# Existence checks
IF EXISTS (SELECT 1 FROM Table)                # ❌ Don't count (control flow)
```

---

## Implementation

### Before (counts everything):
```python
target_patterns = [
    r'\bINSERT\s+(?:INTO\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',
    r'\bTRUNCATE\s+TABLE\s+\[?(\w+)\]?\.\[?(\w+)\]?',  # ← Counted
]
```

### After (counts business logic only):
```python
target_patterns = [
    r'\bINSERT\s+(?:INTO\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',
    # TRUNCATE removed from patterns - not counted as business dependency
]

# Also filter sources to exclude administrative queries
# Use negative lookbehind to skip SELECT in SET/DECLARE context
```

---

## Example: Your SP

### Raw DDL:
```sql
SET @count1 = (SELECT COUNT(*) FROM Target)
TRUNCATE TABLE Target
INSERT INTO Target SELECT FROM Source
SET @count2 = (SELECT COUNT(*) FROM Target)
```

### Old Smoke Test Count:
- Sources: 3 (2x SELECT COUNT + 1x SELECT FROM)
- Targets: 2 (TRUNCATE + INSERT)
- Total: 5 expected

### New Smoke Test Count:
- Sources: 1 (SELECT FROM only, admin queries excluded)
- Targets: 1 (INSERT only, TRUNCATE excluded)
- Total: 2 expected

### Parser Finds:
- Sources: 1 (SELECT FROM)
- Targets: 1 (INSERT)
- Total: 2 found

### Confidence:
- Old: 2/5 = 40% → 75% ⚠️
- New: 2/2 = 100% → 100% ✅

---

## Benefits

1. ✅ Smoke test still runs on raw DDL (detects aggressive cleaning)
2. ✅ Counts only business logic (aligns with parser intent)
3. ✅ Straightforward SPs get 100% instead of false 75% warnings
4. ✅ Can still detect problems (if parser misses actual business logic)

## Trade-offs

- Smoke test becomes slightly more complex (needs to identify administrative patterns)
- But more accurate "expected count" = better confidence scores

---

## Decision Needed

**Should smoke test exclude from COUNT:**
1. ✅ TRUNCATE TABLE? (housekeeping, not transformation)
2. ✅ SELECT in SET/DECLARE? (administrative queries)
3. ✅ IF EXISTS checks? (control flow, not data dependencies)

**My recommendation: YES to all three**

This makes smoke test count "business logic table dependencies" rather than "all table references."
