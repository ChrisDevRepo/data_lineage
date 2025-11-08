# Simplified Confidence Model - 4 Values Only

**Status:** Proposed

---

## User Requirement

> "Simpler, no bonus in calc. Only four different percent values possible."
> "The calculation should not be complicated and not be a black box."

---

## New Model: 4 Discrete Values

**NO bonuses. NO complex calculations. Just reality.**

```
┌─────────────────────────────────────────────────────────────┐
│ CONFIDENCE = How complete is the dependency extraction?     │
└─────────────────────────────────────────────────────────────┘

IF parse_failed:
    → 0%     "Parse failed - add @LINEAGE hints"

ELSE IF all_dependencies_found AND all_validated:
    → 100%   "Perfect - all dependencies found and validated"

ELSE IF most_dependencies_found (>80%):
    → 85%    "Good - most dependencies found"

ELSE:
    → 75%    "Acceptable - partial dependencies"
```

---

## Simple Logic

### Step 1: Did Parsing Succeed?
```python
if parse_failed:
    return 0  # "Parse failed"
```

### Step 2: Compare Found vs Expected
```python
expected = count_tables_in_ddl_text()  # Smoke test regex
found = len(inputs) + len(outputs)

if found == 0 and is_orchestrator():  # Only calls other SPs
    completeness = 100  # Special case: orchestrators have no tables
else:
    completeness = (found / expected) * 100 if expected > 0 else 100
```

### Step 3: Map to 4 Values
```python
if completeness >= 90:
    confidence = 100
elif completeness >= 70:
    confidence = 85
elif completeness >= 50:
    confidence = 75
else:
    confidence = 0  # Too incomplete
```

---

## Examples

### Example 1: Perfect Match
```
SP: spLoadFactGL
Expected: 8 tables (from DDL text)
Found: 8 tables (from parser)
Completeness: 8/8 = 100%
→ Confidence: 100%
```

### Example 2: Good Match
```
SP: spLoadDimAccount
Expected: 10 tables
Found: 9 tables
Completeness: 9/10 = 90%
→ Confidence: 100%
```

### Example 3: Most Found
```
SP: spComplexProc
Expected: 10 tables
Found: 7 tables
Completeness: 7/10 = 70%
→ Confidence: 85%
```

### Example 4: Partial
```
SP: spPartialParse
Expected: 10 tables
Found: 5 tables
Completeness: 5/10 = 50%
→ Confidence: 75%
```

### Example 5: Too Incomplete
```
SP: spDynamicSQL
Expected: 10 tables
Found: 2 tables
Completeness: 2/10 = 20%
→ Confidence: 0%
Reason: "Only found 2/10 tables - add @LINEAGE hints"
```

### Example 6: Orchestrator (Special Case)
```
SP: spLoadDWH
Expected: 0 tables (only has EXEC statements)
Found: 0 tables
Type: Orchestrator (only calls other SPs)
→ Confidence: 100%
```

---

## Breakdown Format

**Simple, transparent JSON:**

```json
{
  "confidence": 85,
  "breakdown": {
    "parse_succeeded": true,
    "expected_tables": 10,
    "found_tables": 7,
    "completeness_pct": 70.0,
    "explanation": "Found 7 out of 10 expected tables (70%)",
    "to_improve": "Add @LINEAGE hints for 3 missing tables"
  }
}
```

**For parse failures:**
```json
{
  "confidence": 0,
  "breakdown": {
    "parse_succeeded": false,
    "expected_tables": 8,
    "found_tables": 1,
    "completeness_pct": 12.5,
    "failure_reason": "Dynamic SQL: sp_executesql @variable - table names unknown at parse time",
    "to_fix": "Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS comment hints"
  }
}
```

---

## Mapping Rules

| Completeness | Confidence | Meaning |
|--------------|------------|---------|
| ≥90% | 100% | Perfect or near-perfect |
| 70-89% | 85% | Good - most found |
| 50-69% | 75% | Acceptable - partial |
| <50% | 0% | Too incomplete - failed |

**Special Cases:**
- Orchestrators (only EXEC, no tables) → 100%
- Parse exceptions → 0%

---

## Benefits

1. **Simple Math** - Users can calculate: `found/expected = %`
2. **No Black Box** - Every value explained
3. **4 Discrete Values** - Easy to understand
4. **Reality-Based** - Uses actual smoke test comparison
5. **No Hidden Bonuses** - What you see is what you get

---

## Implementation

### Old Code (Complex - v2.0.0)
```python
# 5 factors, weighted contributions, hidden bonuses
parse_contribution = parse_score * 0.30
quality_contribution = quality_score * 0.25
catalog_contribution = catalog_score * 0.20
hints_contribution = hints_score * 0.10
uat_contribution = uat_score * 0.15
total_score = sum(all_contributions)

# Hidden orchestrator bonus
if is_orchestrator:
    total_score = max(total_score, 0.85)  # Magic!
```

### New Code (Simple - v2.1.0)
```python
def calculate_confidence_simple(
    parse_succeeded: bool,
    expected_tables: int,
    found_tables: int,
    is_orchestrator: bool = False
) -> dict:
    """
    Simple 4-value confidence model.

    Returns confidence in {0, 75, 85, 100}
    """

    # Failed parsing
    if not parse_succeeded:
        return {
            'confidence': 0,
            'explanation': 'Parse failed',
            'completeness_pct': 0
        }

    # Orchestrator special case
    if is_orchestrator:
        return {
            'confidence': 100,
            'explanation': 'Orchestrator SP (only calls other SPs)',
            'completeness_pct': 100
        }

    # Calculate completeness
    if expected_tables == 0:
        completeness_pct = 100.0
    else:
        completeness_pct = (found_tables / expected_tables) * 100

    # Map to 4 discrete values
    if completeness_pct >= 90:
        confidence = 100
    elif completeness_pct >= 70:
        confidence = 85
    elif completeness_pct >= 50:
        confidence = 75
    else:
        confidence = 0

    return {
        'confidence': confidence,
        'expected_tables': expected_tables,
        'found_tables': found_tables,
        'completeness_pct': round(completeness_pct, 1),
        'explanation': f'Found {found_tables}/{expected_tables} tables ({completeness_pct:.0f}%)'
    }
```

---

## Migration Plan

1. **Keep old model** for comparison (v2.0.0)
2. **Add new model** alongside (v2.1.0)
3. **Test both** on production data
4. **Compare results** - which makes more sense to users?
5. **Switch over** once validated

---

## Questions for User

1. **Thresholds OK?** 90%, 70%, 50% for 100/85/75?
2. **Orchestrator handling?** Should they get 100% or 85%?
3. **Missing tables penalty?** Should finding 0/10 be 0% or 75%?
