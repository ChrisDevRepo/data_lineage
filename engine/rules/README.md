# SQL Cleaning Rules

**YAML-based rules to clean and normalize SQL dialects before parsing.**

**⚠️ IMPORTANT:** Execution order is controlled by the `priority` field in YAML, **NOT** by filename. Filename numbers (like `10_rule.yaml`) are just for organization.

**📖 Quick Links:**
- **[YAML Structure Reference](YAML_STRUCTURE.md)** - Field reference, minimal vs full templates
- **[Template File](TEMPLATE.yaml)** - Copy this to create new rules
- **[Quick Start](#-quick-start-adding-a-rule-for-your-database)** - Add rules for your database
- **[Examples](#-example-rules-by-database)** - Copy-paste templates for Snowflake, BigQuery, Oracle, etc.

## 📁 Directory Structure

```
rules/
├── README.md                   # This file
├── defaults/                   # ⭐ PRISTINE COPIES (for "Reset to Defaults")
│   └── tsql/                   # Battle-tested TSQL rules (17 files)
│       ├── 10_batch_separator.yaml
│       ├── 15_temp_tables.yaml
│       ├── 20_declare_variables.yaml
│       └── ... (all 17 rules)
├── generic/                    # Rules for ALL dialects
│   └── 01_whitespace.yaml      # Example: Normalize whitespace
├── tsql/                       # SQL Server / Azure Synapse (ACTIVE RULES)
│   ├── 10_batch_separator.yaml
│   ├── 15_temp_tables.yaml
│   ├── 20_declare_variables.yaml
│   ├── 21_set_variables.yaml
│   ├── 22_select_assignments.yaml
│   ├── 25_if_object_id.yaml
│   ├── 28_try_catch.yaml
│   ├── 30_raiserror.yaml
│   ├── 35_begin_end.yaml
│   ├── 38_if_blocks.yaml
│   ├── 40_transaction_control.yaml
│   ├── 41_empty_if.yaml
│   ├── 45_exec.yaml
│   ├── 50_truncate.yaml
│   ├── 60_drop_table.yaml
│   ├── 90_extract_dml.yaml
│   └── 99_whitespace.yaml
├── snowflake/                  # Snowflake Data Cloud
├── bigquery/                   # Google BigQuery
├── postgres/                   # PostgreSQL
├── oracle/                     # Oracle Database
└── redshift/                   # Amazon Redshift
```

## ✨ Minimal YAML Rule (Just 7 Lines!)

```yaml
name: remove_go
description: Remove GO batch separators
dialect: tsql
enabled: true
priority: 10
pattern: '^\s*GO\s*$'
replacement: ''
```

**That's it!** See [YAML_STRUCTURE.md](YAML_STRUCTURE.md) for all available fields and when to use them.

## 🔄 Default Rules & Reset Functionality (v0.9.0)

### Where Default Rules Are Stored

**Location:** `engine/rules/defaults/{dialect}/`

The `defaults` directory contains **pristine copies** of battle-tested rules:
- **Never modified** by the application
- Source of truth for factory default rules
- Use these to restore rules if you make a mistake

**Example:**
```
defaults/tsql/          # Pristine copies (17 files)
  ├── 10_batch_separator.yaml
  ├── 15_temp_tables.yaml
  └── ...

tsql/                   # Active rules (you can modify these)
  ├── 10_batch_separator.yaml
  ├── 15_temp_tables.yaml
  └── ...
```

### How to Reset Rules to Defaults (Manual)

If you modify rules and want to restore the factory defaults:

**Option 1: Reset All Rules for a Dialect**
```bash
# Backup your current rules first (optional)
cp -r engine/rules/tsql engine/rules/tsql.backup

# Copy default rules to active directory
cp engine/rules/defaults/tsql/* engine/rules/tsql/

# Restart application
./start-app.sh
```

**Option 2: Reset Single Rule**
```bash
# Restore one specific rule
cp engine/rules/defaults/tsql/10_batch_separator.yaml engine/rules/tsql/

# Restart application
./start-app.sh
```

**⚠️ Important:** Always backup your custom rules before resetting!

### Adding Your Own Default Rules

Want to ship custom default rules for your organization?

```bash
# Add your custom rule to defaults directory
cp custom_rule.yaml engine/rules/defaults/tsql/70_custom.yaml

# Now manual reset will include your custom rule
```

## 🚀 Quick Start: Adding a Rule for Your Database

### Step 1: Copy the Template

```bash
cp engine/rules/TEMPLATE.yaml engine/rules/your_dialect/10_your_rule.yaml
```

Edit the file and replace `YOUR_REGEX_PATTERN_HERE` with your pattern.

### Step 2: Enable DEBUG Mode to See Errors

```bash
# .env
RUN_MODE=debug
LOG_LEVEL=DEBUG
```

### Step 3: Upload a Stored Procedure

Upload your Snowflake/BigQuery/Oracle SP and watch Developer Panel → Logs.

### Step 4: See the parser error in the logs

### Step 5: Create a Rule to Fix It

Example for Snowflake JavaScript procedures:

```yaml
# rules/snowflake/10_javascript_procs.yaml
name: remove_javascript_language
description: Remove LANGUAGE JAVASCRIPT from Snowflake procedures
dialect: snowflake
enabled: true
priority: 10
pattern: 'LANGUAGE\s+JAVASCRIPT'
replacement: '-- LANGUAGE JAVASCRIPT (removed for parsing)'
```

Only 8 lines! See [YAML_STRUCTURE.md](YAML_STRUCTURE.md) for optional fields.

### Step 6: Restart & Test

```bash
./start-app.sh
```

Upload same SP → Check if parsing succeeds ✅

## 📝 File Naming Convention

**Numbered prefixes for organization (convention only):**

```
01-09   Generic rules (all dialects)
10-29   Dialect wrappers (CREATE PROCEDURE syntax)
30-49   Error handling (RAISERROR, RAISE_APPLICATION_ERROR, etc.)
50-69   DDL operations (TRUNCATE, DROP)
70-89   Control flow (IF/ELSE, WHILE, etc.)
90-99   Advanced transformations
```

**Important:** Execution order is controlled by the `priority` field in YAML, NOT the filename. Filename numbers are just convention to keep files organized.

**Examples:**
- `10_batch_separator.yaml` with `priority: 10` - Runs first
- `30_raiserror.yaml` with `priority: 30` - Runs after priority 10 rules
- `50_truncate.yaml` with `priority: 50` - Runs after priority 30 rules

**Best Practice:** Keep filename numbers matching priority values for clarity.

## 🎨 Rule Templates

### Minimal (7 lines)
```yaml
name: your_rule_name
description: What this rule does
dialect: tsql  # or postgres, snowflake, etc.
enabled: true
priority: 10   # Lower runs first (10=early, 90=late)
pattern: 'YOUR_REGEX_PATTERN'
replacement: ''  # What to replace with (empty = remove)
```


**For complete field reference, see [YAML_STRUCTURE.md](YAML_STRUCTURE.md)**

## 🔬 Testing Your Rule

### Manual Testing (Best Practice)

1. Enable DEBUG mode: `RUN_MODE=debug` and `LOG_LEVEL=DEBUG` in `.env`
2. Upload a stored procedure with the syntax your rule targets
3. Check Developer Panel → Logs to see if rule applied correctly
4. Look for log entries showing before/after SQL (if `debug.log_replacements: true`)

## 💡 Tips for Writing Rules

### 1. Start Simple
Copy a TSQL rule, change the pattern. Don't write regex from scratch!

### 2. Test Incrementally
```yaml
# Start with simple pattern
pattern: 'LANGUAGE\s+JAVASCRIPT'

# Then handle variations
pattern: 'LANGUAGE\s+(?:JAVASCRIPT|PYTHON|JAVA)'
```

### 3. Preserve Lineage!
**NEVER** remove `SELECT`, `INSERT`, `UPDATE`, `DELETE` unless absolutely necessary.

```yaml
# ❌ BAD - Removes lineage
pattern: 'INSERT.*'

# ✅ GOOD - Removes wrapper, keeps INSERT
pattern: 'EXECUTE\s+IMMEDIATE'
```

### 4. Use Comments for Removed Code
```yaml
replacement: '-- MERGE removed for parsing'
```

This helps debugging - you see what was removed in cleaned SQL.

## 🗂️ Example Rules by Database

### Snowflake

```yaml
# Remove LANGUAGE JAVASCRIPT
pattern: 'LANGUAGE\s+JAVASCRIPT'

# Remove WAREHOUSE specification
pattern: 'WAREHOUSE\s*=\s*\w+'

# Remove SNOWFLAKE metadata
pattern: 'COMMENT\s*=\s*''[^'']*'''
```

### BigQuery

```yaml
# Remove OPTIONS clause
pattern: 'OPTIONS\s*\([^)]+\)'

# Remove project.dataset prefix (simplify)
pattern: '`[^`]+\.[^`]+\.([^`]+)`'
replacement: '\1'  # Keep only table name
```

### Oracle

```yaml
# Remove AUTHID clause
pattern: 'AUTHID\s+(?:CURRENT_USER|DEFINER)'

# Remove PRAGMA AUTONOMOUS_TRANSACTION
pattern: 'PRAGMA\s+AUTONOMOUS_TRANSACTION'
```

### PostgreSQL

```yaml
# Remove LANGUAGE plpgsql
pattern: 'LANGUAGE\s+plpgsql'

# Remove dollar-quoted strings issues
pattern: '\$\$'
replacement: ''''  # Replace with single quotes
```

## 🔒 Security & Best Practices

### YAML Safe Loading
The rule loader uses `yaml.safe_load()` - no code execution risk.

### Validation
Rules are validated against JSON Schema before loading.

### Fail-Safe
If a rule fails, it logs error and **continues** with next rule - never crashes app.

### Test Thoroughly
Test your rules manually with real stored procedures before deploying!

## 🎓 Learning Resources

1. **Start with TSQL rules** - Battle-tested with 349 stored procedures (100% success)
2. **Copy & modify** - Don't write from scratch
3. **Enable DEBUG mode** - See what the parser is complaining about
4. **Test incrementally** - Add one rule at a time, validate results

## 📚 Advanced Topics

### Generic vs Dialect-Specific Rules

**Generic rules** (`rules/generic/`) apply to ALL databases:
- Whitespace normalization
- Comment removal
- Empty line cleanup

**Dialect rules** (`rules/tsql/`, etc.) are database-specific:
- T-SQL: GO statements, RAISERROR
- Snowflake: LANGUAGE JAVASCRIPT
- BigQuery: OPTIONS clauses

### Rule Priority (Execution Order)

Rules run in priority order (lower = earlier):

```yaml
priority: 10  # Runs first
priority: 50  # Runs in middle
priority: 90  # Runs last
```

**Best practice:** Use numbered filenames that match priorities:
- `10_*.yaml` → priority: 10
- `50_*.yaml` → priority: 50

### Regex Flags

All patterns use these flags automatically:
- `IGNORECASE` - Case-insensitive matching
- `MULTILINE` - `^` and `$` match line boundaries
- `DOTALL` - `.` matches newlines

### Callback Rules (Python Only)

For complex logic that can't be expressed as regex, use Python:

```python
# engine/parsers/sql_cleaning_rules.py
def extract_try_content() -> CallbackRule:
    def extract_try(sql: str) -> str:
        # Complex extraction logic here
        return processed_sql

    return CallbackRule(
        name="ExtractTryContent",
        callback=extract_try,
        priority=30
    )
```

YAML is for simple patterns. Python is for complex transformations.

## 🤝 Contributing Your Rules

Found rules that work for your database? **Share them!**

1. Test thoroughly with real stored procedures (100+ recommended)
2. Add clear description and comments explaining what the rule does
3. Document in `metadata` section (author, date, impact)
4. Submit PR with your dialect rules

**Your contribution helps the community!** 🎉

## 📞 Need Help?

1. Check TSQL rules in `engine/rules/tsql/` for working examples
2. Enable DEBUG mode (`RUN_MODE=debug`, `LOG_LEVEL=DEBUG`) to see parser errors
3. Use Developer Panel → Logs to debug rule application in real-time
4. Check [YAML_STRUCTURE.md](YAML_STRUCTURE.md) for complete field reference

---

**Remember:** The goal is to help the parser understand stored procedures, **not** to produce syntactically perfect SQL. Remove noise, preserve lineage! ✅
