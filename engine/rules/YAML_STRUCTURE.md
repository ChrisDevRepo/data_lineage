# YAML Rule Structure

## Required Fields Only (Minimal)

```yaml
name: remove_go
description: Remove GO batch separators
dialect: tsql
enabled: true
priority: 10
pattern: '^\s*GO\s*$'
replacement: ''
```

That's it! Just 7 lines for a working rule.

## Full Structure (All Fields)

```yaml
# Optional header comment explaining what this rule does

name: remove_go                    # REQUIRED: Unique identifier
description: Remove GO batch separators  # REQUIRED: Short explanation
dialect: tsql                      # REQUIRED: tsql, postgres, snowflake, etc.
category: batch_separator          # OPTIONAL: For organization
enabled: true                      # REQUIRED: true/false
priority: 10                       # OPTIONAL: Lower runs first (default: 50)

pattern_type: regex                # OPTIONAL: Always 'regex' (default)
pattern: '^\s*GO\s*$'              # REQUIRED: Regex pattern
replacement: ''                    # REQUIRED: What to replace with (can be empty)

# Optional test cases (for validation only, not used at runtime)
test_cases:
  - name: simple_go
    input: |
      SELECT * FROM Table1
      GO
    expected: |
      SELECT * FROM Table1

# Optional debug config (only for troubleshooting)
debug:
  log_matches: false              # Log when pattern matches
  log_replacements: false         # Log before/after
  show_context_lines: 0           # Show surrounding lines

# Optional metadata (documentation only, not used by engine)
metadata:
  author: your_name
  created: "2025-MM-DD"
```

## Field Reference

### Core Fields (Required)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | ✅ Yes | - | Unique identifier for this rule |
| `description` | string | ✅ Yes | - | What this rule does |
| `dialect` | string | ✅ Yes | - | `tsql`, `postgres`, `snowflake`, `bigquery`, `oracle`, `redshift`, `generic` |
| `enabled` | boolean | ✅ Yes | - | `true` to enable, `false` to disable |
| `pattern` | string | ✅ Yes | - | Regex pattern to match |
| `replacement` | string | ✅ Yes | - | What to replace matches with (empty string to remove) |

### Optional Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `priority` | integer | No | 50 | **Execution order** (lower runs first: 10 = early, 90 = late). This field controls when the rule runs, NOT the filename. |
| `category` | string | No | 'general' | For organization: `batch_separator`, `error_handling`, `transaction`, `table_mgmt` |
| `pattern_type` | string | No | 'regex' | Always 'regex' (only supported type) |

### Debug Fields (Optional, for troubleshooting only)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `debug.log_matches` | boolean | No | false | Log when pattern matches |
| `debug.log_replacements` | boolean | No | false | Log before/after SQL |
| `debug.show_context_lines` | integer | No | 0 | Show N surrounding lines in logs |

**Note:** Only enable debug fields when troubleshooting a specific rule.

### Metadata Fields (Optional, documentation only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metadata` | object | No | Documentation-only metadata (NOT used by engine) |
| `metadata.author` | string | No | Who created this rule |
| `metadata.created` | string | No | Creation date |
| `metadata.tested_with` | string | No | What was used to test this |
| `metadata.affects_lineage` | boolean | No | Does this remove SELECT/INSERT/UPDATE/DELETE? |
| `metadata.impact` | string | No | What this rule fixes |

## When to Use What

### Minimal Rule (7 lines)
Use for simple, obvious rules:
```yaml
name: remove_comments
description: Remove SQL comments
dialect: generic
enabled: true
priority: 90
pattern: '--.*$'
replacement: ''
```

### With All Fields (For GitHub/Sharing)
Include optional fields when sharing rules publicly:
```yaml
# ==============================================================================
# T-SQL Rule: Remove GO Batch Separators
# ==============================================================================
# GO is SSMS-only syntax and not valid T-SQL
# ==============================================================================

name: remove_go
description: Remove GO batch separators (SSMS-only syntax, not valid T-SQL)
dialect: tsql
category: batch_separator
enabled: true
priority: 10

pattern: '^\s*GO\s*$'
replacement: ''

# Optional: Enable debug logging when troubleshooting
debug:
  log_matches: false
  log_replacements: false

# Optional: Documentation metadata
metadata:
  author: vibecoding
  created: "2025-11-06"
  tested_with: "349 stored procedures"
  affects_lineage: false
  impact: "Critical - GO is not valid T-SQL and causes parser failure"
```

## Multi-Step Rules

For complex transformations requiring multiple steps:

```yaml
name: extract_try_content
description: Extract content from TRY/CATCH blocks
dialect: tsql
enabled: true
priority: 28
pattern:
  - 'BEGIN\s+TRY'
  - 'END\s+TRY'
  - 'BEGIN\s+CATCH.*?END\s+CATCH'
replacement:
  - ''
  - ''
  - ''
```

When `pattern` is a list, `replacement` must also be a list with the same number of items. Each pattern/replacement pair is applied in order.

## Regex Tips

All patterns use these flags automatically:
- **IGNORECASE** - Case-insensitive (`GO` matches `go` and `Go`)
- **MULTILINE** - `^` and `$` match line boundaries
- **DOTALL** - `.` matches newlines

Common patterns:
```yaml
# Remove entire line
pattern: '^\s*KEYWORD.*$'

# Remove keyword and preserve rest
pattern: 'KEYWORD\s+'
replacement: ''

# Remove keyword with argument
pattern: 'KEYWORD\s+\w+'

# Remove keyword with parentheses
pattern: 'KEYWORD\s*\([^)]*\)'
```
