# SQL Cleaning Rule Development Guide

**Version**: 1.0.0
**Date**: 2025-11-11
**Author**: vibecoding

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Rule File Structure](#rule-file-structure)
3. [Writing Your First Rule](#writing-your-first-rule)
4. [Testing Rules](#testing-rules)
5. [Debugging Rules](#debugging-rules)
6. [Best Practices](#best-practices)
7. [Advanced Topics](#advanced-topics)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Choose Rule Directory

Rules are organized by dialect:

```
lineage_v3/rules/
├── generic/     # Universal rules (all databases)
├── tsql/        # Microsoft SQL Server / Synapse
├── postgres/    # PostgreSQL
└── ...
```

**Guidelines:**
- **Generic rules**: Use for whitespace, comments, common SQL syntax
- **Dialect-specific rules**: Use for database-specific syntax (RAISERROR, NOTICE, etc.)

### 2. Create Rule File

File naming convention: `{priority}_{descriptive_name}.yaml`

Examples:
- `01_whitespace.yaml` - Runs first (priority 1)
- `10_remove_raiserror.yaml` - Runs early (priority 10)
- `50_cleanup_temps.yaml` - Runs mid-way (priority 50)

### 3. Rule Template

```yaml
name: my_custom_rule
description: |
  What does this rule do?
  Why is it needed?

dialect: tsql  # or 'generic', 'postgres', etc.
category: noise_reduction
enabled: true
priority: 50

pattern_type: regex
pattern: 'PRINT\s+.*'
replacement: ''

test_cases:
  - name: simple_test
    description: "Basic PRINT statement"
    input: "PRINT 'hello'"
    expected: ""

debug:
  log_matches: true
  log_replacements: true
  show_context_lines: 2

metadata:
  author: your_name
  created: "2025-11-11"
  jira_ticket: "DL-123"
  impact: "Removes debug PRINT statements"
  risk: low
```

### 4. Test Your Rule

```bash
# Test all rules for a dialect
python -m lineage_v3.rules.test_rules tsql

# Test specific rule
python -m lineage_v3.rules.test_rules tsql --rule 10_remove_raiserror.yaml

# Show verbose output
python -m lineage_v3.rules.test_rules tsql --verbose
```

---

## Rule File Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier (use snake_case) |
| `description` | string | What the rule does (supports multiline) |
| `dialect` | string | Target dialect or "generic" |
| `enabled` | boolean | Enable/disable without deleting file |
| `pattern` | string | Regex pattern to match |
| `replacement` | string | Replacement text (empty = delete) |

### Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `category` | `general` | Rule category (noise_reduction, preprocessing, etc.) |
| `priority` | `50` | Execution order (lower = earlier) |
| `pattern_type` | `regex` | Pattern type (currently only regex supported) |
| `test_cases` | `[]` | Embedded test cases |
| `debug` | `{}` | Debug logging configuration |
| `metadata` | `{}` | Author, ticket, impact, risk, etc. |

---

## Writing Your First Rule

### Example 1: Remove T-SQL PRINT Statements

**Goal**: Remove `PRINT` statements that don't affect lineage.

**File**: `lineage_v3/rules/tsql/15_remove_print.yaml`

```yaml
name: remove_print
description: |
  Remove T-SQL PRINT statements used for debugging and logging.
  These don't affect data lineage and add noise to the graph.

dialect: tsql
category: noise_reduction
enabled: true
priority: 15

pattern_type: regex

# Pattern explanation:
# - PRINT\s* : Match "PRINT" followed by optional whitespace
# - .* : Match any characters until end of line
pattern: 'PRINT\s+.*'

replacement: ''

test_cases:
  - name: simple_print
    description: "Basic PRINT with string literal"
    input: "PRINT 'Debug message'"
    expected: ""

  - name: print_with_variable
    description: "PRINT with variable"
    input: "PRINT @debug_msg"
    expected: ""

  - name: preserve_other_code
    description: "Only remove PRINT, keep other statements"
    input: |
      INSERT INTO table VALUES (1)
      PRINT 'Debug'
      SELECT * FROM table
    expected: |
      INSERT INTO table VALUES (1)

      SELECT * FROM table

debug:
  log_matches: true
  log_replacements: true
  show_context_lines: 1

metadata:
  author: vibecoding
  created: "2025-11-11"
  impact: "Removes ~150 PRINT statements in production SPs"
  risk: low
  affects_lineage: false
```

### Example 2: Normalize Comments (Generic)

**Goal**: Remove SQL comments to simplify parsing.

**File**: `lineage_v3/rules/generic/05_remove_comments.yaml`

```yaml
name: remove_comments
description: |
  Remove SQL comments (both line and block comments).
  This is a preprocessing step that helps SQLGlot parsing.

dialect: generic  # Applies to ALL dialects
category: preprocessing
enabled: true
priority: 5

pattern_type: regex

# Match both line comments (--) and block comments (/* ... */)
pattern: '(--[^\n]*|/\*[\s\S]*?\*/)'

replacement: ''

test_cases:
  - name: line_comment
    description: "Remove line comment"
    input: "SELECT * FROM table -- This is a comment"
    expected: "SELECT * FROM table "

  - name: block_comment
    description: "Remove block comment"
    input: "SELECT /* comment */ * FROM table"
    expected: "SELECT  * FROM table"

  - name: multiline_block_comment
    description: "Remove multi-line block comment"
    input: |
      SELECT *
      /*
       * Multi-line comment
       * with details
       */
      FROM table
    expected: |
      SELECT *

      FROM table

debug:
  log_matches: false  # Too noisy
  log_replacements: false

metadata:
  author: system
  created: "2025-11-11"
  impact: "Preprocessing for better SQLGlot parsing"
  risk: low
```

---

## Testing Rules

### Embedded Test Cases

Test cases are defined directly in the YAML file:

```yaml
test_cases:
  - name: descriptive_name
    description: "What this test validates"
    input: "SQL code before rule"
    expected: "SQL code after rule"
```

**Best practices:**
- Test edge cases (empty strings, nested constructs)
- Test that other code is preserved
- Test multi-line statements
- Test with special characters

### Running Tests

```bash
# Test all rules for T-SQL
python -m lineage_v3.rules.test_rules tsql

# Test specific rule
python -m lineage_v3.rules.test_rules tsql --rule 15_remove_print.yaml

# Verbose output
python -m lineage_v3.rules.test_rules tsql --verbose

# Show diff for failed tests
python -m lineage_v3.rules.test_rules tsql --show-diff
```

### Expected Output

```
====================================================================
Testing Rules for Dialect: tsql
====================================================================

Rule: normalize_whitespace
  ✅ multiple_spaces PASSED
  ✅ tabs_and_newlines PASSED
  ✅ mixed_whitespace PASSED

Rule: remove_raiserror
  ✅ simple_raiserror PASSED
  ✅ raiserror_with_variables PASSED
  ❌ multiline_raiserror FAILED
     Expected: ""
     Got:      "RAISERROR(\n'Long message',\n16,\n1\n)"
     Diff: Pattern didn't match multi-line statement

Rule: remove_print
  ✅ simple_print PASSED
  ✅ print_with_variable PASSED

====================================================================
Summary: 7 passed, 1 failed
====================================================================
```

---

## Debugging Rules

### Enable Debug Logging

```yaml
debug:
  log_matches: true          # Log when pattern matches
  log_replacements: true     # Log before/after SQL
  show_context_lines: 2      # Show N lines around match
```

### Debug Output

When enabled, you'll see:

```
[DEBUG] Rule 'remove_raiserror' matched:
  Pattern: RAISERROR\s*\([^)]*\)
  Matches: 3 occurrence(s)
  Match 1: RAISERROR('Error', 16, 1)
  Match 2: RAISERROR(@msg, 0, 1) WITH NOWAIT
  Match 3: RAISERROR('Done', 0, 1)

[DEBUG] Rule 'remove_raiserror' applied:
  SQL size: 2847 → 2691 bytes (-5.5%)
  Replacements: 3
```

### Testing Individual Rules in Python

```python
from lineage_v3.rules import load_rules
from lineage_v3.config.dialect_config import SQLDialect

# Load rules
rules = load_rules(SQLDialect.TSQL)

# Test specific rule
for rule in rules:
    if rule.name == 'remove_raiserror':
        test_sql = "RAISERROR('Error', 16, 1)"
        result = rule.apply(test_sql, verbose=True)
        print(f"Input:  {test_sql}")
        print(f"Output: {result}")
        break
```

### Common Issues

#### Pattern Doesn't Match

**Problem**: Regex pattern doesn't match expected input.

**Solution**: Test pattern on [regex101.com](https://regex101.com)

```yaml
# Add test case that currently fails
test_cases:
  - name: debug_failing_case
    input: "RAISERROR('Test', 16, 1)"
    expected: ""  # What you expect
```

#### Pattern Matches Too Much

**Problem**: Pattern removes code it shouldn't.

**Solution**: Make pattern more specific.

```yaml
# Too greedy (matches everything)
pattern: 'PRINT.*'

# Better (matches until end of line)
pattern: 'PRINT\s+[^\n]*'

# Even better (matches PRINT with specific syntax)
pattern: 'PRINT\s+(?:''[^'']*''|@\w+|\d+)'
```

#### Rule Order Issues

**Problem**: Rules interfere with each other.

**Solution**: Adjust `priority` values.

```yaml
# Preprocessing rules (1-10): Run first
priority: 5

# Noise reduction (11-50): Run second
priority: 20

# Transformations (51-90): Run third
priority: 60

# Cleanup (91-100): Run last
priority: 95
```

---

## Best Practices

### 1. One Rule, One Purpose

❌ **Bad**: Single rule that removes PRINT, RAISERROR, and comments
```yaml
pattern: '(PRINT.*|RAISERROR.*|--.*)'
```

✅ **Good**: Separate rules for each statement type
```yaml
# File: 15_remove_print.yaml
pattern: 'PRINT\s+.*'

# File: 10_remove_raiserror.yaml
pattern: 'RAISERROR\s*\([^)]*\)'

# File: 05_remove_comments.yaml
pattern: '--[^\n]*'
```

### 2. Test Edge Cases

Always test:
- Empty strings
- Multi-line statements
- Nested constructs
- Special characters
- Code before/after match

```yaml
test_cases:
  - name: empty_string
    input: ""
    expected: ""

  - name: nested_parens
    description: "Nested parentheses in RAISERROR"
    input: "RAISERROR('Error: (code %d)', 16, 1, @code)"
    expected: ""

  - name: preserve_surrounding
    description: "Don't remove adjacent code"
    input: |
      INSERT INTO logs VALUES (1)
      PRINT 'Debug'
      SELECT * FROM table
    expected: |
      INSERT INTO logs VALUES (1)

      SELECT * FROM table
```

### 3. Use Descriptive Names

❌ **Bad**: `rule1.yaml`, `fix.yaml`, `temp_fix.yaml`

✅ **Good**: `10_remove_raiserror.yaml`, `15_remove_print.yaml`

### 4. Document Impact

```yaml
metadata:
  impact: |
    Based on smoke test analysis:
    - Reduces false positives by 15%
    - Improves SQLGlot parse success by 2.3%
    - Affects 327 stored procedures
    - Baseline improvement: +2.3% parse success
  risk: low
  affects_lineage: false
  baseline_tables: 729  # Before this rule
  improved_tables: 743  # After this rule
```

### 5. Priority Guidelines

```
1-10:    Preprocessing (whitespace, comments)
11-30:   Noise reduction (PRINT, RAISERROR, NOCOUNT)
31-50:   Simplification (DECLARE, temp variables)
51-70:   Transformations (temp tables, CTEs)
71-90:   Cleanup (trailing whitespace, empty lines)
91-100:  Final polish (semicolons, formatting)
```

---

## Advanced Topics

### Custom Rule Directories

Add custom rules via environment variable:

```bash
export LINEAGE_CUSTOM_RULES_DIR="/opt/company/sql_rules"
```

Or programmatically:

```python
from pathlib import Path
from lineage_v3.rules import load_rules
from lineage_v3.config.dialect_config import SQLDialect

custom_dirs = [Path("/opt/company/sql_rules")]
rules = load_rules(SQLDialect.TSQL, custom_dirs=custom_dirs)
```

### Regex Performance

For complex patterns, use non-capturing groups:

```yaml
# Slower (capturing group)
pattern: '(PRINT\s+.*)'

# Faster (non-capturing group)
pattern: '(?:PRINT\s+.*)'
```

### Multi-Line Patterns

Use `(?s)` flag or `[\s\S]*` for multi-line:

```yaml
# Match multi-line block comments
pattern: '/\*[\s\S]*?\*/'

# Match multi-line statements
pattern: 'BEGIN\s+TRANSACTION[\s\S]*?END\s+TRANSACTION'
```

---

## Troubleshooting

### Rule Not Loading

**Check:**
1. File is in correct directory (`generic/`, `tsql/`, etc.)
2. File has `.yaml` extension
3. `enabled: true` in YAML
4. YAML syntax is valid (`yamllint your_rule.yaml`)

**Backend log will show:**
```
[WARNING] Failed to load rule from 15_remove_print.yaml: Missing required field 'pattern'
```

### Tests Failing

**Check:**
1. `expected` exactly matches output (including whitespace)
2. Pattern matches the input
3. Replacement is correct

**Run with verbose:**
```bash
python -m lineage_v3.rules.test_rules tsql --rule your_rule.yaml --verbose
```

### Pattern Not Matching

**Debug:**
1. Test on [regex101.com](https://regex101.com)
2. Add `debug.log_matches: true`
3. Check for case sensitivity
4. Check for multi-line requirements

---

## Example: Complete Rule File

```yaml
# =============================================================================
# T-SQL Rule: Remove SET NOCOUNT Statements
# =============================================================================
# SET NOCOUNT ON/OFF controls whether row count messages are returned.
# This doesn't affect data lineage and can be safely removed for parsing.
# =============================================================================

name: remove_set_nocount
description: |
  Remove T-SQL SET NOCOUNT ON/OFF statements.
  These control message output but don't affect data transformations.

dialect: tsql
category: noise_reduction
enabled: true
priority: 12

# -----------------------------------------------------------------------------
# Pattern Configuration
# -----------------------------------------------------------------------------
pattern_type: regex

# Match: SET NOCOUNT ON/OFF (case-insensitive)
pattern: 'SET\s+NOCOUNT\s+(?:ON|OFF)'

replacement: ''

# -----------------------------------------------------------------------------
# Test Cases
# -----------------------------------------------------------------------------
test_cases:
  - name: nocount_on
    description: "SET NOCOUNT ON"
    input: "SET NOCOUNT ON"
    expected: ""

  - name: nocount_off
    description: "SET NOCOUNT OFF"
    input: "SET NOCOUNT OFF"
    expected: ""

  - name: with_surrounding_code
    description: "Preserve other statements"
    input: |
      CREATE PROCEDURE test AS
      SET NOCOUNT ON
      SELECT * FROM table
      SET NOCOUNT OFF
    expected: |
      CREATE PROCEDURE test AS

      SELECT * FROM table


  - name: case_insensitive
    description: "Handle different casing"
    input: "set nocount on"
    expected: ""

# -----------------------------------------------------------------------------
# Debug Configuration
# -----------------------------------------------------------------------------
debug:
  log_matches: true
  log_replacements: true
  show_context_lines: 1

# -----------------------------------------------------------------------------
# Metadata
# -----------------------------------------------------------------------------
metadata:
  author: vibecoding
  created: "2025-11-11"
  updated: "2025-11-11"
  jira_ticket: "DL-789"
  impact: |
    Removes SET NOCOUNT statements that appear in ~95% of stored procedures.
    No impact on lineage detection, purely noise reduction.
  risk: low
  affects_lineage: false
  baseline_improvement: "+0.5% parse success"
```

---

## Summary

### Key Takeaways

1. **Rules are YAML files** - No Python coding required
2. **Organized by dialect** - `generic/`, `tsql/`, `postgres/`, etc.
3. **Priority-based execution** - Lower priority runs first
4. **Embedded test cases** - Test right in the YAML file
5. **Invalid rules warn** - Backend logs warnings, doesn't crash
6. **Debug-friendly** - Enable logging per-rule

### Quick Reference

```bash
# Create new rule
cp lineage_v3/rules/generic/01_whitespace.yaml \
   lineage_v3/rules/tsql/50_my_rule.yaml

# Test rules
python -m lineage_v3.rules.test_rules tsql

# Enable debug logging
# Edit rule YAML:
debug:
  log_matches: true
  log_replacements: true
```

---

**Questions?** Check the backend logs or file an issue!
