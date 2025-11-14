# Python SQL Cleaning Rules (Active System)

**Version:** v4.3.3
**Status:** ✅ Production (17 rules)
**Location:** `lineage_v3/parsers/sql_cleaning_rules.py`

---

## ⚠️ CRITICAL: This is the ACTIVE system

> **Current Status:** This document describes the SQL cleaning rules that are **CURRENTLY ACTIVE** in v4.3.3.
>
> **NOT YAML:** The YAML rule system documented in [RULE_DEVELOPMENT.md](RULE_DEVELOPMENT.md) is implemented but NOT integrated with the parser.
>
> **To modify rules:** Edit `lineage_v3/parsers/sql_cleaning_rules.py` directly.

## 🚨 MANDATORY: Check Journal Before Making Changes

**⚠️ CRITICAL: ALWAYS check change journal BEFORE modifying rules!**

```bash
# STEP 1: Check journal (MANDATORY)
cat docs/PARSER_CHANGE_JOURNAL.md | grep -A 10 "DO NOT"
cat docs/PARSER_CHANGE_JOURNAL.md | grep -E "rule|cleaning|preprocessing"

# Review:
# - Past rule issues and root causes
# - What NOT to change (defensive patterns)
# - Patterns that caused regressions
# - User-verified corrections
```

**Why this is mandatory:**
- Rule changes affect ALL 349 stored procedures
- One bad pattern can break 100% success rate
- Past issues documented: WARN mode, IF EXISTS, DECLARE/SET conflicts
- "Never change a running system" - validate heavily before changing

---

## Overview

The SQL cleaning rule engine preprocesses T-SQL stored procedures before SQLGlot parsing. It removes T-SQL-specific constructs that SQLGlot can't handle and extracts the core DML (Data Manipulation Language) for table dependency analysis.

**Architecture:**
- **RuleEngine:** Orchestrates rule execution
- **CleaningRule:** Base class for all rules
- **RegexRule:** Simple pattern → replacement rules
- **CallbackRule:** Complex logic rules with custom functions

**Execution:** Rules execute in priority order (lower number = higher priority)

---

## Rule Categories (8)

1. **BATCH_SEPARATOR** - GO statements
2. **VARIABLE_DECLARATION** - DECLARE, SET, SELECT assignments
3. **ERROR_HANDLING** - TRY/CATCH, RAISERROR
4. **EXECUTION** - EXEC, dynamic SQL
5. **TRANSACTION** - BEGIN TRAN, COMMIT, ROLLBACK
6. **TABLE_MANAGEMENT** - TRUNCATE, temp tables, DROP
7. **WRAPPER** - CREATE PROC, BEGIN/END, IF blocks
8. **EXTRACTION** - Extract core DML from wrappers

---

## Active Rules (17)

### Priority 10: RemoveGO
**Category:** BATCH_SEPARATOR
**Type:** RegexRule
**Purpose:** Remove GO batch separators (SQL Server Management Studio specific)

**Pattern:** `^\s*GO\s*$` (multiline)
**Replacement:** Empty string

**Example:**
```sql
-- Before
SELECT * FROM Table1
GO
SELECT * FROM Table2
GO

-- After
SELECT * FROM Table1

SELECT * FROM Table2
```

**Why:** GO is not valid SQL - SQLGlot will fail if it sees it

---

### Priority 15: ReplaceTempTables ✨ NEW
**Category:** TABLE_MANAGEMENT
**Type:** RegexRule
**Purpose:** Replace temp table references (#table) with dummy schema (dummy.table)

**Pattern:** `#(\w+)`
**Replacement:** `dummy.\1`

**Example:**
```sql
-- Before
SELECT * INTO #TempData FROM SourceTable
INSERT INTO #TempData VALUES (1, 2)
SELECT * FROM #TempData

-- After
SELECT * INTO dummy.TempData FROM SourceTable
INSERT INTO dummy.TempData VALUES (1, 2)
SELECT * FROM dummy.TempData
```

**Why:** Brilliant simple solution! Makes temp tables parseable by SQLGlot. Valid SQL syntax, filter out dummy.* objects in post-processing.

---

### Priority 20: RemoveDECLARE
**Category:** VARIABLE_DECLARATION
**Type:** CallbackRule
**Purpose:** Remove DECLARE variable declarations

**Logic:**
1. Match DECLARE until semicolon or blank line
2. Handle comma-separated multi-variable declarations
3. Remove multi-line declarations with subqueries

**Example:**
```sql
-- Before
DECLARE @var VARCHAR(100);
DECLARE @count INT = (SELECT COUNT(*) FROM Table1);
SELECT * FROM Table2

-- After


SELECT * FROM Table2
```

**Critical Fix (2025-11-11):** Handles multi-line DECLARE with subqueries (previously left dangling FROM clauses)

**Why:** Variables don't affect table dependencies. SQLGlot has limited DECLARE support.

---

### Priority 21: RemoveSET
**Category:** VARIABLE_DECLARATION
**Type:** CallbackRule
**Purpose:** Remove SET variable assignments and session settings

**Logic:**
1. Pass 0: Remove session SET (NOCOUNT, ANSI_NULLS, etc.)
2. Pass 1: Remove SET with SELECT...FROM (admin queries)
3. Pass 2: Remove simple SET without SELECT (pure assignments)

**Example:**
```sql
-- Before
SET NOCOUNT ON
SET @var = 'test';
SET @count = (SELECT COUNT(*) FROM Table1);
SELECT * FROM Table2

-- After



SELECT * FROM Table2
```

**Critical Fix (2025-11-11):** More specific pattern - only removes SET with SELECT...FROM or simple assignments. Preserves scalar SELECT (no FROM).

**Why:** Variable assignments and session settings don't affect lineage.

---

### Priority 22: RemoveSELECTAssignment ✨ NEW
**Category:** VARIABLE_DECLARATION
**Type:** RegexRule
**Purpose:** Remove SELECT statements that assign to variables (T-SQL specific)

**Pattern:** `SELECT\s+@\w+\s*=.*?(?=\n(?:INSERT|UPDATE|DELETE|MERGE|SELECT(?!\s+@)|EXEC|$))`
**Replacement:** Empty string

**Example:**
```sql
-- Before
SELECT @MSG = 'End Time:' + CONVERT(VARCHAR(30), GETDATE())
INSERT INTO Table1 SELECT * FROM Table2

-- After

INSERT INTO Table1 SELECT * FROM Table2
```

**Why:** SELECT @var = value doesn't return data, it's an assignment (not data retrieval).

---

### Priority 25: RemoveIFObjectID ✨ NEW
**Category:** TABLE_MANAGEMENT
**Type:** RegexRule
**Purpose:** Remove IF object_id(...) administrative checks

**Pattern:** `if\s+object_id\s*\(\s*N?['"]tempdb\.\.[#\w]+['"]\s*\)\s+is\s+not\s+null\s+begin\s+drop\s+table\s+[#\w\.]+\s*;?\s*end\s*;?`
**Replacement:** Empty string

**Example:**
```sql
-- Before
if object_id(N'tempdb..#temp') is not null
begin drop table #temp; end;

-- After
(removed)
```

**Why:** Administrative existence checks before drops, not data lineage.

---

### Priority 26: RemoveDropTable ✨ NEW
**Category:** TABLE_MANAGEMENT
**Type:** RegexRule
**Purpose:** Remove DROP TABLE statements

**Pattern:** `drop\s+table\s+(?:if\s+exists\s+)?[#\w\.\[\]]+\s*;?`
**Replacement:** Empty string

**Example:**
```sql
-- Before
DROP TABLE #temp
DROP TABLE IF EXISTS staging.temp_data
drop table [dbo].[TempStaging];

-- After
(all removed)
```

**Why:** Cleanup operations don't show data flow.

---

### Priority 30: ExtractTRY
**Category:** ERROR_HANDLING
**Type:** CallbackRule
**Purpose:** Extract content from BEGIN TRY...END TRY blocks, remove CATCH blocks

**Logic:**
1. Remove all BEGIN CATCH...END CATCH blocks
2. Extract content from BEGIN TRY...END TRY blocks

**Example:**
```sql
-- Before
BEGIN TRY
    INSERT INTO Table1 SELECT * FROM Table2
END TRY
BEGIN CATCH
    RAISERROR('Error', 16, 1)
END CATCH

-- After
INSERT INTO Table1 SELECT * FROM Table2
```

**Why:** TRY/CATCH is error handling, not supported by SQLGlot. Keep business logic (TRY content), discard error handling (CATCH).

---

### Priority 31: RemoveRAISERROR
**Category:** ERROR_HANDLING
**Type:** RegexRule
**Purpose:** Remove RAISERROR statements

**Pattern:** `RAISERROR\s*\([^)]*\)`
**Replacement:** Empty string

**Example:**
```sql
-- Before
RAISERROR('Error message', 16, 1)
RAISERROR(@msg, @severity, @state)
SELECT 1

-- After


SELECT 1
```

**Why:** Error throwing, not relevant for table dependencies.

---

### Priority 35: FlattenSimpleBEGIN ✨ NEW
**Category:** WRAPPER
**Type:** RegexRule
**Purpose:** Remove standalone BEGIN/END wrappers (non-control-flow)

**Pattern:** `\n\s*BEGIN\s*\n\s*((?:INSERT|UPDATE|DELETE|MERGE|SELECT|WITH)[\s\S]*?)\n\s*END\s*;?`
**Replacement:** `\n\1\n`

**Example:**
```sql
-- Before

BEGIN
    INSERT INTO Target SELECT * FROM Source
END

-- After

    INSERT INTO Target SELECT * FROM Source
```

**Why:** Standalone BEGIN/END adds complexity without value. Preserves control flow BEGIN/END (handled by other rules).

---

### Priority 40: ExtractIFBlockDML ✨ NEW
**Category:** EXTRACTION
**Type:** RegexRule
**Purpose:** Extract DML from simple IF blocks

**Pattern:** `IF\s+[^B]+?\s+BEGIN\s+(INSERT|UPDATE|DELETE|MERGE)\s+([^;]+?)\s*;?\s*END`
**Replacement:** `\1 \2`

**Example:**
```sql
-- Before
IF @condition = 1
BEGIN
    INSERT INTO Target SELECT * FROM Source
END

-- After
INSERT INTO Target SELECT * FROM Source
```

**Why:** We want lineage regardless of runtime condition. Captures conditional lineage.

---

### Priority 41: RemoveEmptyIF ✨ NEW
**Category:** WRAPPER
**Type:** RegexRule
**Purpose:** Remove empty IF blocks (typically from DROP TABLE removal)

**Pattern:** `if\s+[^\n]+\s+begin\s+end`
**Replacement:** Empty string

**Example:**
```sql
-- Before
if object_id(N'tempdb..dummy.Table') is not null
begin  end

-- After
(removed)
```

**Bug Fix (2025-11-11):** Clean up empty IF blocks left after DROP removal.

**Why:** After DROP TABLE is removed, we're left with empty IF blocks.

---

### Priority 40: RemoveEXEC
**Category:** EXECUTION
**Type:** RegexRule
**Purpose:** Remove EXEC statements (dynamic SQL execution)

**Pattern:** `EXEC(?:UTE)?\s+\[?[a-zA-Z_\[\]\.]+\]?\s+[^;]*;?`
**Replacement:** Empty string

**Example:**
```sql
-- Before
EXEC dbo.LogMessage @Param1 = 'value', @Param2 = 123
EXEC sp_executesql @sql
SELECT 1

-- After


SELECT 1
```

**Why:** Can't extract table dependencies from dynamic SQL or procedure calls at parse time.

---

### Priority 50: RemoveTransactionControl
**Category:** TRANSACTION
**Type:** RegexRule
**Purpose:** Remove BEGIN TRAN, COMMIT, ROLLBACK statements

**Pattern:** `(?:BEGIN|COMMIT|ROLLBACK)\s+TRAN(?:SACTION)?\s*;?`
**Replacement:** Empty string

**Example:**
```sql
-- Before
BEGIN TRANSACTION
INSERT INTO Table1 VALUES (1)
COMMIT TRANSACTION

-- After

INSERT INTO Table1 VALUES (1)
```

**Why:** Transaction management, not relevant for table dependencies.

---

### Priority 60: RemoveTRUNCATE
**Category:** TABLE_MANAGEMENT
**Type:** RegexRule
**Purpose:** Remove TRUNCATE TABLE statements

**Pattern:** `TRUNCATE\s+TABLE\s+\[?\w+\]?(?:\.\[?\w+\]?(?:\.\[?\w+\]?)?)?`
**Replacement:** Empty string

**Example:**
```sql
-- Before
TRUNCATE TABLE dbo.Test;
SELECT 1

-- After

SELECT 1
```

**Critical Fix (2025-11-11):** Pattern was TOO GREEDY. Changed from `[^;]+` to `[\w\.\[\]]+` to match only table name components, not arbitrary text.

**Bug:** Old pattern would eat entire INSERT if no semicolon after TRUNCATE.

**Why:** TRUNCATE is DDL for emptying tables. The table reference is the target, not a dependency.

---

### Priority 90: ExtractCoreDML
**Category:** EXTRACTION
**Type:** CallbackRule
**Purpose:** Extract core DML from CREATE PROC...AS BEGIN...END wrapper

**Logic:**
1. Find `CREATE PROC...AS BEGIN`
2. Match closing END using depth counting
3. Skip string literals when counting BEGIN/END
4. Skip CASE...END blocks (don't count as BEGIN/END)
5. Extract body between outer BEGIN...END

**Example:**
```sql
-- Before
CREATE PROC dbo.Test AS
BEGIN
    WITH cte AS (SELECT * FROM Source)
    INSERT INTO Target SELECT * FROM cte
END

-- After
WITH cte AS (SELECT * FROM Source)
INSERT INTO Target SELECT * FROM cte
```

**Critical Fix (2025-11-11):** Handle nested BEGIN/END with depth counting. Skip string literals like 'End Time:'. Skip CASE...END blocks.

**Why:** This is the KEY transformation that makes SQLGlot work! Removes wrapper, keeps business logic.

---

### Priority 99: CleanupWhitespace
**Category:** COMMENT
**Type:** RegexRule
**Purpose:** Clean up excessive blank lines

**Pattern:** `\n\s*\n\s*\n+`
**Replacement:** `\n\n`

**Example:**
```sql
-- Before
SELECT 1



SELECT 2

-- After
SELECT 1

SELECT 2
```

**Why:** After removing T-SQL constructs, we have multiple blank lines. Clean up for readability.

---

## Rule Execution Flow

**Order (by priority):**
1. **[10]** Remove GO statements
2. **[15]** Replace #temp → dummy.temp
3. **[20]** Remove DECLARE
4. **[21]** Remove SET
5. **[22]** Remove SELECT @var assignments
6. **[25]** Remove IF object_id(...) checks
7. **[26]** Remove DROP TABLE
8. **[30]** Extract TRY content
9. **[31]** Remove RAISERROR
10. **[35]** Flatten standalone BEGIN/END
11. **[40]** Extract IF block DML
12. **[40]** Remove EXEC (same priority)
13. **[41]** Remove empty IF blocks
14. **[50]** Remove transaction control
15. **[60]** Remove TRUNCATE
16. **[90]** Extract core DML from CREATE PROC
17. **[99]** Cleanup whitespace

**Strategy:**
- Early: Remove T-SQL specifics (GO, temp tables, variables)
- Middle: Handle control flow (TRY/CATCH, IF blocks)
- Late: Extract core DML from wrapper
- Last: Clean up whitespace

---

## Usage

### Apply All Rules

```python
from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

# Create engine with default rules
engine = RuleEngine()

# Clean SQL
cleaned_sql = engine.apply_all(raw_sql, verbose=True)
```

### Test Rules

```python
# Test all rules with built-in examples
engine = RuleEngine()
all_passed = engine.test_all_rules()

if all_passed:
    print("✓ All rules passed")
else:
    print("✗ Some rules failed")
```

### List Rules

```python
engine = RuleEngine()
engine.list_rules()

# Output:
# ==========================================
# SQL CLEANING RULES
# ==========================================
#
# BATCH_SEPARATOR
# ------------------------------------------
#   ✓ [ 10] RemoveGO
#       Remove GO batch separators
# ...
```

### Disable/Enable Rules

```python
engine = RuleEngine()

# Disable a rule
engine.disable_rule("RemoveEXEC")

# Enable a rule
engine.enable_rule("RemoveEXEC")
```

### Get Rules by Category

```python
from lineage_v3.parsers.sql_cleaning_rules import RuleCategory

engine = RuleEngine()
var_rules = engine.get_rules_by_category(RuleCategory.VARIABLE_DECLARATION)

# Returns: [RemoveDECLARE, RemoveSET, RemoveSELECTAssignment]
```

---

## Adding New Rules

### Step 1: Create Rule Class

**Simple Regex Rule:**
```python
@staticmethod
def your_new_rule() -> RegexRule:
    """
    Remove your construct.

    Example:
        Your example before

    Becomes:
        Your example after
    """
    return RegexRule(
        name="YourRuleName",
        category=RuleCategory.YOUR_CATEGORY,
        description="Brief description",
        pattern=r'your_regex_pattern',
        replacement='',
        flags=re.IGNORECASE,
        priority=25,  # Choose appropriate priority
        examples_before=["Example input"],
        examples_after=["Expected output"]
    )
```

**Complex Callback Rule:**
```python
@staticmethod
def your_complex_rule() -> CallbackRule:
    """Your documentation"""

    def your_callback(sql: str) -> str:
        # Your custom logic here
        return modified_sql

    return CallbackRule(
        name="YourRuleName",
        category=RuleCategory.YOUR_CATEGORY,
        description="Brief description",
        callback=your_callback,
        priority=35,
        examples_before=["Example"],
        examples_after=["Expected"]
    )
```

### Step 2: Register in RuleEngine

Add to `_load_default_rules()`:
```python
@staticmethod
def _load_default_rules() -> List[CleaningRule]:
    return [
        # ... existing rules ...
        SQLCleaningRules.your_new_rule(),  # Add here
        # ... rest of rules ...
    ]
```

### Step 3: Test Your Rule

```python
from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

engine = RuleEngine()
engine.test_all_rules()  # Should pass for your new rule
```

### Step 4: Document in Change Journal

Update [PARSER_CHANGE_JOURNAL.md](PARSER_CHANGE_JOURNAL.md) with:
- What was added
- Why it was needed
- Example cases

---

## Design Principles

1. **Self-documenting:** Each rule has name, description, examples
2. **Testable:** Built-in test cases with expected outputs
3. **Enable/disable:** Rules can be toggled without code changes
4. **Clear execution order:** Priority determines sequence
5. **Comprehensive logging:** Debug rule application easily
6. **Extensible:** Easy to add new rules

---

## History & Critical Fixes

### 2025-11-11: Critical Pattern Fixes

**RemoveTRUNCATE (Priority 60):**
- **Bug:** Pattern `[^;]+` was too greedy, ate entire INSERT if no semicolon
- **Fix:** Changed to `[\w\.\[\]]+` to match only table name components
- **Impact:** Prevented loss of downstream SQL statements

**RemoveDECLARE (Priority 20):**
- **Bug:** Pattern removed ALL DECLARE including scalar SELECT without FROM
- **Example Broken:** `DECLARE @month INT = (SELECT Month(@Today))` → removed entire line
- **Fix:** Handle multi-line DECLARE with subqueries properly
- **Impact:** Preserved calculations while removing admin queries

**RemoveSET (Priority 21):**
- **Bug:** Same as DECLARE - removed scalar SELECT calculations
- **Fix:** Three-pass approach (session settings, SELECT...FROM, simple assignments)
- **Impact:** Preserved scalar calculations

**ExtractCoreDML (Priority 90):**
- **Bug:** Depth counter matched 'END' inside string literals like 'End Time:'
- **Fix:** Skip string literals and CASE...END blocks when counting depth
- **Impact:** Prevented premature END matching in nested structures

### 2025-11-07: New Smarter Rules (7 added)

Added 7 new rules (Priority 15-41):
- ReplaceTempTables - #temp → dummy.temp (brilliant!)
- RemoveSELECTAssignment - SELECT @var = value
- RemoveIFObjectID - IF object_id(...) checks
- RemoveDropTable - DROP TABLE statements
- FlattenSimpleBEGIN - Standalone BEGIN/END
- ExtractIFBlockDML - Pull DML from IF blocks
- RemoveEmptyIF - Clean empty IF blocks

**Impact:** Simplified SQL, better SQLGlot parsing success rate

---

## Warnings & Best Practices

### ⚠️ DO NOT Change These Patterns

**ExtractCoreDML (Priority 90):**
- DO NOT remove depth counting logic (regression: nested BEGIN/END broken)
- DO NOT remove string literal skipping (regression: 'End Time:' breaks parser)
- DO NOT remove CASE...END tracking (regression: CASE statements break depth)

**RemoveTRUNCATE (Priority 60):**
- DO NOT change to greedy pattern like `[^;]+` (regression: eats following SQL)
- KEEP pattern specific to table name components only

**RemoveDECLARE/SET (Priority 20-21):**
- DO NOT simplify to single regex (regression: removes scalar calculations)
- KEEP multi-pass callback approach

**Rule Priority Order:**
- DO NOT change priority without testing full suite
- Rules depend on execution order (e.g., temp table replacement BEFORE DECLARE removal)

### ✅ Best Practices

1. **Always add test cases:** `examples_before` and `examples_after`
2. **Document fixes in code:** Comment critical fixes with date and reason
3. **Test with user-verified cases:** Run `pytest tests/unit/test_parser_golden_cases.py`
4. **Update change journal:** Document what changed and why
5. **Baseline validation:** Use `scripts/testing/run_baseline_validation.sh`

---

## Testing

### Unit Tests

```bash
# Test rule engine
pytest tests/unit/test_rule_engine.py -v

# Test specific rule
pytest tests/unit/test_rule_engine.py::test_remove_go -v
```

### Integration Tests

```bash
# User-verified cases (regression detection)
pytest tests/unit/test_parser_golden_cases.py -v

# User-reported cases
pytest tests/unit/test_user_verified_cases.py -v

# Full parser validation
python3 scripts/testing/check_parsing_results.py
```

### Baseline Validation

```bash
# Capture baseline before changes
./scripts/testing/run_baseline_validation.sh before

# Make rule changes

# Validate after changes
./scripts/testing/run_baseline_validation.sh after

# Review diff
./scripts/testing/run_baseline_validation.sh diff
```

---

## Performance

**Metrics (349 stored procedures):**
- Total rule applications: ~5,900 (17 rules × 349 SPs)
- Average time per SP: ~2-5ms (rule application only)
- Regex compilation: Cached (happens once per rule)
- Success rate: 100% (349/349 SPs)

**Optimization:**
- Rules execute in priority order (efficient early exits)
- Regex patterns compiled once and reused
- Simple rules use RegexRule (faster)
- Complex rules use CallbackRule (more flexible)

---

## Future: YAML Rule System

**Status:** Implemented but NOT integrated (see [RULE_DEVELOPMENT.md](RULE_DEVELOPMENT.md))

**Decision Pending:**
- Option A: Integrate YAML system (replace Python rules)
- Option B: Delete YAML system (keep Python rules)
- Option C: Hybrid (YAML for simple rules, Python for complex)

**Current:** Python rules are production, YAML is experimental

---

**Last Updated:** 2025-11-14
**Version:** v4.3.3
**Total Rules:** 17 (10 original + 7 new)

**See Also:**
- [Parser Critical Reference](PARSER_CRITICAL_REFERENCE.md) - What NOT to change
- [Parser Technical Guide](PARSER_TECHNICAL_GUIDE.md) - Complete architecture
- [Parser Change Journal](PARSER_CHANGE_JOURNAL.md) - Change history & regression prevention
- [Rule Development (YAML)](RULE_DEVELOPMENT.md) - Future YAML system ⚠️ Not integrated
