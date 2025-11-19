# YAML Rules - Error Handling Examples

This document shows what happens when YAML rules have errors.

**KEY PRINCIPLE:** The app **NEVER crashes** due to invalid rules. Rules are skipped and clearly reported.

---

## Example 1: Invalid YAML Syntax

**File:** `rules/snowflake/10_bad_syntax.yaml`

```yaml
name: remove_javascript
description: "Remove LANGUAGE JAVASCRIPT"
dialect: snowflake
pattern: 'LANGUAGE\s+JAVASCRIPT
# Missing closing quote ↑
replacement: ''
```

**What you see in logs:**

```
❌ YAML syntax error in 10_bad_syntax.yaml: while scanning a quoted scalar
   File: /app/engine/rules/snowflake/10_bad_syntax.yaml
   Fix the YAML syntax and restart. Rule skipped.

✅ Successfully loaded 5 rules for dialect 'snowflake'
⚠️  Failed to load 1 rule file(s):
   - 10_bad_syntax.yaml: YAML syntax error
   Fix the errors above and restart to enable these rules.
```

**Result:** App continues, other 5 rules work fine ✅

---

## Example 2: Invalid Regex Pattern

**File:** `rules/bigquery/10_bad_regex.yaml`

```yaml
name: remove_options
description: "Remove OPTIONS clause"
dialect: bigquery
enabled: true
priority: 10
pattern_type: regex
pattern: 'OPTIONS\s+\([^)]+\))'  # Extra closing paren - invalid!
replacement: ''
```

**What you see in logs:**

```
❌ Invalid regex pattern in 10_bad_regex.yaml: unbalanced parenthesis at position 20
   File: /app/engine/rules/bigquery/10_bad_regex.yaml
   Fix the 'pattern' field. Rule skipped.

✅ Successfully loaded 3 rules for dialect 'bigquery'
⚠️  Failed to load 1 rule file(s):
   - 10_bad_regex.yaml: Invalid regex
      Details: Pattern is invalid: unbalanced parenthesis at position 20
   Fix the errors above and restart to enable these rules.
```

**Result:** App continues, parsing works with 3 remaining rules ✅

---

## Example 3: Missing Required Fields

**File:** `rules/oracle/10_incomplete.yaml`

```yaml
name: remove_pragma
# Missing: description, dialect, pattern, replacement
enabled: true
priority: 10
```

**What you see in logs:**

```
❌ Invalid rule configuration in 10_incomplete.yaml: Missing required fields: description, dialect, pattern, replacement
   File: /app/engine/rules/oracle/10_incomplete.yaml
   Check README.md for required fields. Rule skipped.

✅ Successfully loaded 0 rules for dialect 'oracle'
⚠️  Failed to load 1 rule file(s):
   - 10_incomplete.yaml: Invalid configuration
      Details: Missing required fields: description, dialect, pattern, replacement
   Fix the errors above and restart to enable these rules.
```

**Result:** App continues with no Oracle rules (falls back to Python rules if any) ✅

---

## Example 4: Pattern/Replacement Mismatch (Multi-Step)

**File:** `rules/tsql/99_mismatched.yaml`

```yaml
name: multi_step_broken
description: "Multi-step with wrong counts"
dialect: tsql
enabled: true
priority: 99
pattern_type: regex
pattern:
  - 'DECLARE\s+@\w+'
  - 'SET\s+@\w+'
  - 'BEGIN\s+TRAN'
replacement:
  - ''
  - ''
# Only 2 replacements for 3 patterns - ERROR!
```

**What you see in logs:**

```
❌ Invalid rule configuration in 99_mismatched.yaml: Pattern list has 3 items but replacement list has 2 items. They must have the same length for multi-step rules.
   File: /app/engine/rules/tsql/99_mismatched.yaml
   Check README.md for required fields. Rule skipped.

✅ Successfully loaded 6 rules for dialect 'tsql'
⚠️  Failed to load 1 rule file(s):
   - 99_mismatched.yaml: Invalid configuration
      Details: Pattern list has 3 items but replacement list has 2 items...
   Fix the errors above and restart to enable these rules.
```

**Result:** App continues with 6 working TSQL rules ✅

---

## Example 5: Runtime Error (Pattern Matching Fails)

**File:** `rules/postgres/10_works_loads_fails_runtime.yaml`

```yaml
name: catastrophic_backtracking
description: "Pattern causes catastrophic backtracking"
dialect: postgres
enabled: true
priority: 10
pattern_type: regex
# This pattern can cause catastrophic backtracking on certain inputs
pattern: '(a+)+b'
replacement: ''
```

**What you see during SP parsing:**

```
❌ Rule 'catastrophic_backtracking' failed during pattern matching: timeout exceeded
   SQL might contain unexpected characters. Rule skipped.

Continuing with remaining rules...
```

**Result:** SP parsing continues, other rules still apply ✅

---

## Example 6: All Rules Valid (Success Case)

**What you see in INFO mode:**

```
Loading rules from: /app/engine/rules/generic
Loaded rule 'normalize_whitespace' from 01_whitespace.yaml
Loading rules from: /app/engine/rules/tsql
Loaded rule 'remove_go' from 10_batch_separator.yaml
Loaded rule 'remove_declare' from 20_declare_variables.yaml
Loaded rule 'remove_raiserror' from 30_raiserror.yaml

✅ Successfully loaded 6 rules for dialect 'tsql'
✅ All rule files loaded successfully (no errors)

Rule execution order (by priority):
   10 - remove_go (batch_separator)
   20 - remove_declare (variable_decl)
   30 - remove_raiserror (error_handling)
   40 - remove_transaction_control (transaction)
   50 - remove_truncate (table_mgmt)
   60 - remove_drop_table (table_mgmt)
```

**Result:** Perfect! All rules working ✅

---

## Example 7: What You See in DEBUG Mode

**Enable DEBUG:**
```bash
# .env
RUN_MODE=debug
LOG_LEVEL=DEBUG
```

**Additional details for errors:**

```
❌ Invalid regex pattern in 10_bad_regex.yaml: unbalanced parenthesis
   File: /app/engine/rules/bigquery/10_bad_regex.yaml
   Fix the 'pattern' field. Rule skipped.

DEBUG: Regex error details:
  Traceback (most recent call last):
    File "/app/engine/rules/rule_loader.py", line 298, in _validate_regex_patterns
      re.compile(p, re.IGNORECASE | re.MULTILINE | re.DOTALL)
  re.error: unbalanced parenthesis at position 20
  Pattern: 'OPTIONS\s+\([^)]+\))'
                           ↑ Extra paren here
```

**Result:** DEBUG mode shows EXACTLY what's wrong and where ✅

---

## Error Handling Philosophy

### ✅ What We Do

1. **Validate early** - Check YAML syntax, required fields, regex patterns at load time
2. **Fail gracefully** - Skip bad rules, continue with good ones
3. **Report clearly** - Show filename, error type, and how to fix
4. **Never crash** - App always starts, even with 100% broken rules
5. **Help users** - Point to README, show context, suggest fixes

### ❌ What We DON'T Do

1. **Don't crash the app** - Invalid rules = warning, not fatal error
2. **Don't silently fail** - Every error is logged with context
3. **Don't hide details** - DEBUG mode shows full stack traces
4. **Don't give up** - One broken rule doesn't stop others from loading

---

## Testing Your Rules

### Quick Test (Before Restarting App)

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('rules/mydb/10_myrule.yaml'))"

# Test regex pattern
python -c "import re; re.compile('YOUR_PATTERN_HERE')"
```

### Full Validation Tool

```bash
python tools/validate_rules.py --dialect snowflake
```

Shows:
- ✅ Valid rules (with test case results)
- ❌ Invalid rules (with specific errors)
- ⚠️ Rules without test cases

---

## Common Mistakes & Fixes

### Mistake 1: Forgot quotes around pattern

```yaml
# ❌ WRONG
pattern: LANGUAGE\s+JAVASCRIPT

# ✅ CORRECT
pattern: 'LANGUAGE\s+JAVASCRIPT'
```

### Mistake 2: Wrong indentation (YAML is strict!)

```yaml
# ❌ WRONG (test_cases not indented)
test_cases:
- name: test1
  input: "SELECT 1"

# ✅ CORRECT
test_cases:
  - name: test1
    input: "SELECT 1"
```

### Mistake 3: Multi-line strings without pipe

```yaml
# ❌ WRONG
description: This is a very long description
that spans multiple lines

# ✅ CORRECT
description: |
  This is a very long description
  that spans multiple lines
```

### Mistake 4: Unescaped backslashes in regex

```yaml
# ❌ WRONG (in YAML, \ needs escaping in some cases)
pattern: "\s+SELECT"

# ✅ CORRECT (use single quotes, no escaping needed)
pattern: '\s+SELECT'
```

---

## Summary

**The Golden Rule:** If your YAML rule has errors, the app:
1. Logs the error clearly ❌
2. Skips that rule ⏭️
3. Continues with other rules ✅
4. Tells you how to fix it 📝
5. **Never crashes** 🛡️

**In DEBUG mode, you get even more details to fix issues fast!**

✅ This makes the app production-ready for open-source release!
