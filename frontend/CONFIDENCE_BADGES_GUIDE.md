# Confidence Badges Guide (v2.1.0)

## Overview

Visual confidence badges appear on **Stored Procedure nodes** to show parsing quality at a glance. The badges use simple symbols based on the v2.1.0 simplified confidence model.

---

## Badge Symbols

### ✅ High Confidence (100%)
**Symbol:** Green checkmark
**Confidence Score:** 1.0 (100%)
**Meaning:** Perfect or near-perfect parsing

**What it means:**
- Parser found ≥90% of expected tables
- All dependencies captured correctly
- High trust in the lineage data

**Example:**
- Expected 10 tables, found 9-10 tables (90-100%)
- Orchestrator SP (only calls other SPs, no tables)

---

### ⚠️ Good Confidence (85%)
**Symbol:** Yellow/Orange warning
**Confidence Score:** 0.85 (85%)
**Meaning:** Most dependencies found

**What it means:**
- Parser found 70-89% of expected tables
- Most dependencies captured
- May be missing a few tables

**Example:**
- Expected 10 tables, found 7-8 tables (70-89%)
- Suggestion: Add @LINEAGE hints for missing tables

---

### ⚠️ Medium Confidence (75%)
**Symbol:** Yellow warning
**Confidence Score:** 0.75 (75%)
**Meaning:** Partial dependencies found

**What it means:**
- Parser found 50-69% of expected tables
- Partial dependency extraction
- Several tables may be missing

**Example:**
- Expected 10 tables, found 5-6 tables (50-69%)
- Recommendation: Review and add @LINEAGE hints

---

### ❌ Low/Failed Confidence (0%)
**Symbol:** Red X
**Confidence Score:** 0.0 (0%)
**Meaning:** Parse failed or too incomplete

**What it means:**
- Parser found <50% of expected tables, OR
- Parsing failed completely
- Lineage data is unreliable

**Examples:**
- Expected 10 tables, found 0-4 tables (<50%)
- Dynamic SQL that can't be parsed statically
- Complex logic (WHILE loops, cursors, sp_executesql)

**Action Required:**
- Add @LINEAGE_INPUTS and @LINEAGE_OUTPUTS comment hints
- Review SP for dynamic SQL patterns

---

## v2.1.0 Simplified Model

The badges reflect the **v2.1.0 simplified confidence model**:

**Only 4 possible values:** 0%, 75%, 85%, 100%

**Simple logic:**
```
completeness = (tables_found / tables_expected) × 100

if completeness ≥ 90%:  → 100% confidence (✅)
if completeness ≥ 70%:  → 85% confidence (⚠️)
if completeness ≥ 50%:  → 75% confidence (⚠️)
if completeness < 50%:  → 0% confidence (❌)
```

**No hidden bonuses** - what you see is what you get!

---

## Visual Placement

Badges appear in the **top-right corner** of Stored Procedure nodes:

```
┌─────────────────────────┐
│                      ✅ │  ← Badge here
│   spLoadFactOrders      │
│                         │
└─────────────────────────┘
```

**Hover effects:**
- Hover over badge to see detailed tooltip
- Badge scales up on hover (1.3x)
- Tooltip shows exact confidence percentage

---

## Understanding the Symbols

### Your Question: "✅ Too incomplete (20% → 0%)"

This describes the **threshold mapping**:
- **Input:** 20% completeness (found 2 out of 10 tables)
- **Output:** 0% confidence (❌ symbol, not ✅)

**The arrow (→) means "maps to":**
- 20% completeness → 0% confidence (because <50%)
- 70% completeness → 85% confidence
- 90% completeness → 100% confidence

---

## Benefits

1. **Instant visual feedback** - See quality without hovering
2. **Easy prioritization** - Focus on ❌ and ⚠️ nodes first
3. **Transparent** - Simple % thresholds, no black box
4. **Actionable** - Clear what needs improvement

---

## Related Documentation

- [CONFIDENCE_MODEL_SIMPLIFIED.md](../CONFIDENCE_MODEL_SIMPLIFIED.md) - Full v2.1.0 spec
- [COMMENT_HINTS_DEVELOPER_GUIDE.md](../docs/COMMENT_HINTS_DEVELOPER_GUIDE.md) - How to add @LINEAGE hints
- [CustomNode.tsx](./components/CustomNode.tsx) - Badge implementation

---

**Last Updated:** 2025-11-08
**Version:** v2.1.0
