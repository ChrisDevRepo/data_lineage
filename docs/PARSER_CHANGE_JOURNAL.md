# Rule Change Journal

**Purpose:** Track rule engine changes to maintain parsing quality and prevent regressions

**Branch:** v4.3.5-regex-only-parsing

## Overview

This journal documents changes to the YAML rule engine that powers the regex-only SQL parser. The parser uses a simplified architecture with pattern-based extraction rules.

## 🚨 CRITICAL: Check This Journal BEFORE Making Rule Changes

**⚠️ MANDATORY REQUIREMENT:**
- **Adding new rules** → Check for conflicts with existing patterns
- **Modifying rule priority** → Verify execution order dependencies
- **Changing regex patterns** → Test against edge cases documented here
- **Removing rules** → Confirm no downstream dependencies

## Rule Structure

### Current Rule Organization

```
engine/rules/
├── generic/          # Standard SQL rules (all dialects)
├── tsql/            # T-SQL specific rules
├── postgres/        # PostgreSQL specific rules
└── defaults/        # Pristine copies for reset
```

### Multi-Dialect Support

The rule engine supports multiple SQL dialects:
- **Generic rules** apply to all dialects (TRUNCATE, DROP, COMMIT, etc.)
- **Dialect-specific rules** handle syntax variations (GO, RAISERROR, etc.)
- Rules load in priority order: generic first, then dialect-specific

---

## Rule Change Log

### 2025-11-19 - Regex-Only Parsing: Fresh Start

**Status:** 🎯 Clean slate for regex-only architecture

**Context:**
Starting new branch `v4.3.5-regex-only-parsing` with simplified architecture:
- Pure regex-based extraction via YAML rules
- Pattern-based cleaning and normalization
- Simplified rule engine

**Current Rule Inventory:**
- **T-SQL:** 13 dialect-specific rules
- **Generic:** 4 standard SQL rules
- **Total active:** 17 rules

**Architecture Principles:**
1. **Pattern-based extraction** - Regex patterns match SQL keywords and capture object references
2. **Priority-based execution** - Rules run in order (10, 15, 20, ... 99)
3. **Cleaning rules** - Remove noise (comments, GO statements, temp tables, etc.)
4. **Extraction rules** - Capture FROM/JOIN/INSERT INTO/UPDATE/MERGE targets
5. **Catalog validation** - Filter extracted objects against metadata catalog

**DO NOT:**
- ❌ Re-introduce AST parsing (defeats purpose of regex-only approach)
- ❌ Create overly complex regex patterns (maintainability over perfection)
- ❌ Skip catalog validation (prevents false positives from comments/strings)

**Next Steps:**
- Document rule changes in this journal
- Track regex pattern improvements
- Record edge cases and solutions
- Maintain parsing quality metrics

---

## Journal Entry Format

When adding rule changes, use this format:

```markdown
### YYYY-MM-DD - Brief Description of Change

**Rule Modified:** `XX_rule_name.yaml`
**Type:** [Addition/Modification/Removal/Bug Fix]

**Issue:**
What problem was being solved?

**Change:**
What was modified in the rule?
- Pattern before: `...`
- Pattern after: `...`
- Priority changed from X to Y (if applicable)

**Impact:**
- Test cases affected: X
- Parsing improvement: Y
- Edge cases handled: Z

**DO NOT:**
- Specific patterns or behaviors to preserve
- Regression risks to avoid

**Validation:**
✅ Test results confirming no regressions
```

---

## Common Patterns

### Cleaning Rules (Priorities 10-49)

**Purpose:** Remove syntax that interferes with extraction
- Comments (single-line, multi-line)
- Batch separators (GO statements)
- Temp tables (#temp syntax)
- Variable declarations
- Control flow blocks

### Extraction Rules (Priorities 50-99)

**Purpose:** Capture table/view references for lineage
- FROM clauses
- JOIN clauses  
- INSERT INTO targets
- UPDATE targets
- MERGE targets
- DELETE FROM targets

### Rule Priority Guidelines

- **10-29:** Remove dialect-specific noise (GO, temp tables, variables)
- **30-49:** Remove standard SQL noise (transactions, control flow)
- **50-69:** Extract DML operations (TRUNCATE, DROP)
- **70-89:** Reserved for future extraction patterns
- **90-99:** Final extraction and cleanup (DML extraction, whitespace)

---

## Regression Prevention

### Protected Patterns

*Patterns to preserve will be documented here as issues arise*

### Known Edge Cases

*Edge cases and solutions will be documented here*

---

## Metrics Tracking

**Baseline (v4.3.5-regex-only-parsing):**
- Parser: Simplified regex-only architecture
- Rules: 17 active (13 T-SQL + 4 generic)
- Dialects supported: T-SQL, PostgreSQL (proof of concept)

*Future metrics will track parsing success rates and quality*

---

**Last Updated:** 2025-11-19
**Branch:** v4.3.5-regex-only-parsing
**Maintained By:** Manual updates as rules change
