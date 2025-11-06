# SQL Cleaning Engine - Action Plan

**Version:** 1.0.0
**Date:** 2025-11-06
**Status:** 🎯 Planning Phase
**Owner:** Data Lineage Team

---

## Executive Summary

This document outlines the multi-phase plan for integrating and iterating on the SQL Cleaning Rule Engine. The goal is to dramatically improve SQLGlot's success rate on complex T-SQL stored procedures through intelligent pre-processing.

**Current Status:**
- ✅ Rule engine architecture implemented (`sql_cleaning_rules.py`)
- ✅ 10 core rules defined and tested
- ✅ Proof of concept: 0% → 100% SQLGlot success on test SP
- ⏳ Production integration pending
- ⏳ Full evaluation suite pending

**Strategic Goals:**
1. Increase SQLGlot success rate from ~0% to 80%+ on complex SPs
2. Maintain/improve overall parsing accuracy (currently 95.5%)
3. Improve confidence scores by reducing method disagreement
4. Create extensible, maintainable cleaning system

---

## Phase 1: Foundation & Integration (Week 1-2)

### Objectives
- Integrate rule engine into production parser
- Establish baseline metrics
- Ensure backwards compatibility

### Tasks

#### 1.1 Integration into `quality_aware_parser.py`

**Location:** `lineage_v3/parsers/quality_aware_parser.py:237-295` (SQLGlot parsing section)

**Current Code:**
```python
def _parse_with_sqlglot(self, sql: str, obj_name: str) -> Dict[str, Set[str]]:
    """Use SQLGlot to parse SQL and extract table references"""
    try:
        parsed = sqlglot.parse_one(sql, read='tsql', error_level=None)
        # ... existing logic ...
```

**New Approach:**
```python
def _parse_with_sqlglot(self, sql: str, obj_name: str) -> Dict[str, Set[str]]:
    """Use SQLGlot to parse SQL and extract table references"""
    from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

    try:
        # NEW: Pre-process SQL with rule engine
        engine = RuleEngine()
        cleaned_sql = engine.apply_all(sql, verbose=False)

        # Try parsing cleaned SQL
        parsed = sqlglot.parse_one(cleaned_sql, read='tsql', error_level=None)

        # Store metadata about cleaning
        self._store_cleaning_metadata(obj_name, {
            'original_size': len(sql),
            'cleaned_size': len(cleaned_sql),
            'reduction_pct': (1 - len(cleaned_sql)/len(sql)) * 100,
            'sqlglot_success': True
        })

        # ... existing logic ...
```

**Backwards Compatibility Strategy:**
- If rule engine fails → fall back to original SQL
- If cleaned SQL fails to parse → try original SQL
- Log all failures for analysis

**Implementation Steps:**
1. Add `sql_cleaning_rules.py` import to parser
2. Modify `_parse_with_sqlglot()` with cleaning step
3. Add fallback logic (try cleaned, then original)
4. Add metadata tracking
5. Add feature flag `ENABLE_SQL_CLEANING` (default: True)

**Testing:**
- Run on single SP: `spLoadFactLaborCostForEarnedValue` ✅
- Run on 10 random SPs: Verify no regressions
- Run on known failing SPs: Measure improvement

**Success Criteria:**
- Zero regressions on existing passing cases
- At least 50% improvement on known SQLGlot failures

#### 1.2 Configuration & Feature Flags

**Add to `.env`:**
```bash
# SQL Cleaning Engine
ENABLE_SQL_CLEANING=true
SQL_CLEANING_LOG_LEVEL=INFO  # DEBUG for detailed rule execution
SQL_CLEANING_CACHE=true       # Cache cleaned SQL
```

**Add to `settings.py`:**
```python
class Settings(BaseSettings):
    # ... existing ...

    # SQL Cleaning Engine
    enable_sql_cleaning: bool = True
    sql_cleaning_log_level: str = "INFO"
    sql_cleaning_cache: bool = True
```

#### 1.3 Baseline Metrics Collection

**Run Full Evaluation:**
```bash
cd sandbox
source venv/bin/activate

# 1. Create baseline WITHOUT cleaning
python lineage_v3/parsers/quality_aware_parser.py disable_cleaning
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python lineage_v3/main.py export --format json --output evaluation_baselines/baseline_before_cleaning.json

# 2. Run WITH cleaning
python lineage_v3/parsers/quality_aware_parser.py enable_cleaning
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
python lineage_v3/main.py export --format json --output evaluation_baselines/baseline_after_cleaning.json

# 3. Compare
python scripts/compare_baselines.py \
    evaluation_baselines/baseline_before_cleaning.json \
    evaluation_baselines/baseline_after_cleaning.json \
    --output temp/cleaning_engine_impact_report.md
```

**Metrics to Track:**
- SQLGlot success rate (% of objects successfully parsed)
- Method agreement rate (regex vs SQLGlot)
- Average confidence scores
- Parsing time (performance impact)
- Table extraction accuracy (precision/recall)

**Expected Results:**
- SQLGlot success: ~0-10% → ~60-80%
- Method agreement: ~50% → ~75%
- Confidence scores: Average increase of 0.10-0.15
- Parsing time: <10% slowdown (acceptable)

#### 1.4 Documentation Updates

**Files to Update:**

1. **`docs/PARSING_USER_GUIDE.md`**
   - Add section: "SQL Cleaning Engine"
   - Explain what it does and why
   - How to disable if needed

2. **`docs/PARSER_EVOLUTION_LOG.md`**
   - Add entry for SQL Cleaning Engine v1.0.0
   - Document baseline metrics
   - Link to this action plan

3. **`CLAUDE.md`**
   - Add SQL Cleaning Engine to parser features
   - Update parser version to v4.3.0

4. **`lineage_specs.md`**
   - Add technical specification for cleaning engine
   - Document rule priority system

**Deliverables:**
- [ ] Integration complete with feature flag
- [ ] Baseline metrics collected (before/after)
- [ ] Impact report generated
- [ ] Documentation updated
- [ ] Zero regressions confirmed

**Timeline:** Week 1-2 (10-15 hours)

---

## Phase 2: Rule Expansion - CURSOR Handling (Week 3)

### Objectives
- Handle CURSOR declarations and operations
- Improve parsing of SPs with CURSOR logic

### Background

**CURSOR Pattern in T-SQL:**
```sql
DECLARE cursor_name CURSOR FOR
    SELECT ... FROM ...
OPEN cursor_name
FETCH NEXT FROM cursor_name INTO @var1, @var2
WHILE @@FETCH_STATUS = 0
BEGIN
    -- Processing logic
    FETCH NEXT FROM cursor_name INTO @var1, @var2
END
CLOSE cursor_name
DEALLOCATE cursor_name
```

**Why It Breaks SQLGlot:**
- CURSOR syntax is T-SQL specific
- FETCH/OPEN/CLOSE are procedural, not SQL
- @@FETCH_STATUS system variable

**What We Need:**
- Extract the SELECT statement from CURSOR declaration
- Remove OPEN/FETCH/CLOSE/DEALLOCATE
- Keep the SELECT logic for table extraction

### New Rules to Add

#### Rule: ExtractCursorQueries
```python
@staticmethod
def extract_cursor_queries() -> CallbackRule:
    """
    Extract SELECT statements from CURSOR declarations.

    Before:
        DECLARE cur CURSOR FOR
            SELECT * FROM dbo.Table1 JOIN dbo.Table2
        OPEN cur
        FETCH NEXT FROM cur INTO @var
        CLOSE cur
        DEALLOCATE cur

    After:
        SELECT * FROM dbo.Table1 JOIN dbo.Table2
    """
    def extract_cursors(sql: str) -> str:
        # Find: DECLARE ... CURSOR FOR (SELECT ...)
        cursor_pattern = r'DECLARE\s+\w+\s+CURSOR\s+FOR\s+(SELECT\s+.*?)(?=\n\s*OPEN|\n\s*$)'

        selects = []
        for match in re.finditer(cursor_pattern, sql, re.DOTALL | re.IGNORECASE):
            selects.append(match.group(1))

        # Remove CURSOR operations
        sql = re.sub(r'DECLARE\s+\w+\s+CURSOR\s+FOR.*?(?=\n)', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'OPEN\s+\w+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'FETCH\s+NEXT\s+FROM\s+\w+\s+INTO\s+[^;]+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'CLOSE\s+\w+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'DEALLOCATE\s+\w+', '', sql, flags=re.IGNORECASE)

        # Append extracted SELECTs
        if selects:
            sql = sql + '\n\n' + '\n\n'.join(selects)

        return sql

    return CallbackRule(
        name="ExtractCursorQueries",
        category=RuleCategory.CURSOR_HANDLING,
        description="Extract SELECT from CURSOR declarations",
        callback=extract_cursors,
        priority=35,
        examples_before=[
            "DECLARE cur CURSOR FOR SELECT * FROM dbo.Table1\nOPEN cur\nFETCH NEXT FROM cur\nCLOSE cur"
        ],
        examples_after=[
            "\n\nSELECT * FROM dbo.Table1"
        ]
    )
```

#### Rule: RemoveFetchStatus
```python
@staticmethod
def remove_fetch_status() -> RegexRule:
    """Remove @@FETCH_STATUS system variable references"""
    return RegexRule(
        name="RemoveFetchStatus",
        category=RuleCategory.CURSOR_HANDLING,
        description="Remove @@FETCH_STATUS references",
        pattern=r'@@FETCH_STATUS\s*[=<>!]+\s*\d+',
        replacement='1=1',  # Replace with always-true condition
        priority=36
    )
```

### Testing Strategy

1. **Find CURSOR SPs:**
```sql
SELECT name
FROM objects
WHERE definition LIKE '%CURSOR%'
  AND object_type = 'stored_procedure'
LIMIT 20
```

2. **Test on 5 CURSOR SPs:**
- Measure SQLGlot success rate before/after
- Verify table extraction accuracy
- Check for regressions

3. **Add to Test Suite:**
```python
def test_cursor_extraction():
    """Test CURSOR query extraction"""
    sql = """
    DECLARE cur CURSOR FOR
        SELECT * FROM dbo.SourceTable
    OPEN cur
    FETCH NEXT FROM cur INTO @id
    CLOSE cur
    DEALLOCATE cur
    """

    engine = RuleEngine()
    cleaned = engine.apply_all(sql)

    # Should contain SELECT
    assert 'SELECT * FROM dbo.SourceTable' in cleaned
    # Should not contain CURSOR keywords
    assert 'CURSOR' not in cleaned
    assert 'OPEN' not in cleaned
    assert 'FETCH' not in cleaned
```

**Deliverables:**
- [ ] CURSOR rules implemented and tested
- [ ] Tested on 20 CURSOR-based SPs
- [ ] Impact report (accuracy improvement)
- [ ] Rules documented

**Timeline:** Week 3 (5-8 hours)

---

## Phase 3: Rule Expansion - WHILE Loops (Week 4)

### Objectives
- Handle WHILE loop constructs
- Extract SQL statements from within loops

### Background

**WHILE Pattern:**
```sql
DECLARE @counter INT = 1
WHILE @counter <= 10
BEGIN
    INSERT INTO dbo.Target
    SELECT * FROM dbo.Source
    WHERE id = @counter

    SET @counter = @counter + 1
END
```

**Strategy:**
- Extract SQL statements from WHILE body
- Remove loop control (@counter, conditions)
- Keep the core DML

### New Rules to Add

#### Rule: ExtractWhileContent
```python
@staticmethod
def extract_while_content() -> CallbackRule:
    """
    Extract SQL from WHILE loops.

    Keeps: DML statements inside loop
    Removes: WHILE condition, loop counter logic
    """
    def extract_while(sql: str) -> str:
        # Find WHILE ... BEGIN ... END blocks
        while_pattern = r'WHILE\s+.*?\s+BEGIN\s+(.*?)\s+END'

        # Extract content from WHILE blocks
        contents = []
        for match in re.finditer(while_pattern, sql, re.DOTALL | re.IGNORECASE):
            body = match.group(1)
            # Remove SET @counter statements
            body = re.sub(r'SET\s+@\w+\s*=\s*@\w+\s*[+\-*/]\s*\d+', '', body, flags=re.IGNORECASE)
            contents.append(body)

        # Replace WHILE blocks with their content
        result = sql
        for i, match in enumerate(re.finditer(while_pattern, sql, re.DOTALL | re.IGNORECASE)):
            result = result.replace(match.group(0), contents[i], 1)

        return result

    return CallbackRule(
        name="ExtractWhileContent",
        category=RuleCategory.WHILE_LOOP,
        description="Extract SQL from WHILE loops",
        callback=extract_while,
        priority=45
    )
```

**Deliverables:**
- [ ] WHILE loop rules implemented
- [ ] Tested on loop-heavy SPs
- [ ] Documentation updated

**Timeline:** Week 4 (5-8 hours)

---

## Phase 4: Rule Expansion - IF/ELSE Logic (Week 5)

### Objectives
- Handle conditional logic (IF/ELSE)
- Extract SQL from all branches

### Background

**IF/ELSE Pattern:**
```sql
IF @condition = 1
BEGIN
    INSERT INTO dbo.Target1 SELECT * FROM dbo.Source1
END
ELSE
BEGIN
    INSERT INTO dbo.Target2 SELECT * FROM dbo.Source2
END
```

**Strategy:**
- Extract SQL from both IF and ELSE branches
- Remove condition logic
- Keep all possible data flows

### New Rules to Add

#### Rule: ExtractIfElseContent
```python
@staticmethod
def extract_if_else_content() -> CallbackRule:
    """
    Extract SQL from IF/ELSE branches.

    Strategy: Keep SQL from ALL branches (union of possibilities)
    """
    def extract_if_else(sql: str) -> str:
        # Find IF ... ELSE blocks
        if_pattern = r'IF\s+.*?\s+BEGIN\s+(.*?)\s+END(?:\s+ELSE\s+BEGIN\s+(.*?)\s+END)?'

        contents = []
        for match in re.finditer(if_pattern, sql, re.DOTALL | re.IGNORECASE):
            if_body = match.group(1)
            else_body = match.group(2) if match.group(2) else ''

            # Combine both branches
            combined = f"{if_body}\n{else_body}"
            contents.append(combined)

        # Replace IF/ELSE with combined content
        result = sql
        for i, match in enumerate(re.finditer(if_pattern, sql, re.DOTALL | re.IGNORECASE)):
            result = result.replace(match.group(0), contents[i], 1)

        return result

    return CallbackRule(
        name="ExtractIfElseContent",
        category=RuleCategory.CONDITIONAL,
        description="Extract SQL from IF/ELSE branches",
        callback=extract_if_else,
        priority=46
    )
```

**Deliverables:**
- [ ] IF/ELSE rules implemented
- [ ] Tested on conditional SPs
- [ ] Documentation updated

**Timeline:** Week 5 (5-8 hours)

---

## Phase 5: Advanced Rules - Dynamic SQL (Week 6)

### Objectives
- Handle EXEC sp_executesql with dynamic SQL
- Extract table references from dynamic query strings

### Background

**Dynamic SQL Pattern:**
```sql
DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM dbo.TargetTable WHERE id = @id'
EXEC sp_executesql @sql, N'@id INT', @id = 123
```

**Challenge:**
- SQL is in a string variable
- Table names are inside quoted strings
- Parameters are passed separately

**Strategy:**
- Extract SQL string from @sql assignment
- Parse the string for table references
- Remove EXEC sp_executesql

### New Rules to Add

#### Rule: ExtractDynamicSQL
```python
@staticmethod
def extract_dynamic_sql() -> CallbackRule:
    """
    Extract SQL from dynamic SQL strings.

    Handles:
    - SET @sql = 'SELECT ...'
    - EXEC sp_executesql @sql
    """
    def extract_dynamic(sql: str) -> str:
        # Find SET @sql = '...'
        dynamic_pattern = r"SET\s+@\w+\s*=\s*N?'(.*?)'"

        extracted_queries = []
        for match in re.finditer(dynamic_pattern, sql, re.DOTALL | re.IGNORECASE):
            query = match.group(1)
            # Unescape single quotes
            query = query.replace("''", "'")
            extracted_queries.append(query)

        # Remove sp_executesql calls
        sql = re.sub(r'EXEC\s+sp_executesql\s+@\w+[^;]*;?', '', sql, flags=re.IGNORECASE)

        # Append extracted queries
        if extracted_queries:
            sql = sql + '\n\n-- Extracted from dynamic SQL:\n' + '\n\n'.join(extracted_queries)

        return sql

    return CallbackRule(
        name="ExtractDynamicSQL",
        category=RuleCategory.DYNAMIC_SQL,
        description="Extract SQL from dynamic query strings",
        callback=extract_dynamic,
        priority=55
    )
```

**Complexity:** High (string parsing, nested quotes, parameter handling)

**Deliverables:**
- [ ] Dynamic SQL rules implemented
- [ ] Tested on 10 dynamic SQL SPs
- [ ] Edge cases documented

**Timeline:** Week 6 (8-12 hours)

---

## Phase 6: Performance Optimization (Week 7-8)

### Objectives
- Minimize performance impact of cleaning
- Add caching layer
- Optimize rule execution

### 6.1 Caching Strategy

**Problem:** Cleaning same SP multiple times wastes CPU

**Solution:** Cache cleaned SQL by hash

```python
class RuleEngine:
    def __init__(self, rules=None, cache_enabled=True):
        self.rules = rules or self._load_default_rules()
        self.cache_enabled = cache_enabled
        self._cache = {}  # hash(sql) -> cleaned_sql

    def apply_all(self, sql: str, verbose: bool = False) -> str:
        if not self.cache_enabled:
            return self._apply_rules(sql, verbose)

        # Check cache
        sql_hash = hashlib.md5(sql.encode()).hexdigest()
        if sql_hash in self._cache:
            logger.debug(f"Cache hit for {sql_hash[:8]}")
            return self._cache[sql_hash]

        # Clean and cache
        cleaned = self._apply_rules(sql, verbose)
        self._cache[sql_hash] = cleaned
        return cleaned
```

**Benefits:**
- Incremental parsing: Cached results for unchanged SPs
- Full refresh: Still benefits from deduplication
- Memory efficient: LRU cache with max size

### 6.2 Rule Execution Optimization

**Current:** Sequential execution (rule 1 → rule 2 → ...)

**Optimization Ideas:**

1. **Early Exit:**
   ```python
   def apply_all(self, sql: str) -> str:
       # If no problematic patterns found, skip cleaning
       if not self._needs_cleaning(sql):
           return sql
       # ... apply rules ...

   def _needs_cleaning(self, sql: str) -> bool:
       # Quick check for T-SQL constructs
       patterns = ['BEGIN TRY', 'CURSOR', 'WHILE', 'EXEC sp_executesql']
       return any(p in sql.upper() for p in patterns)
   ```

2. **Parallel Rule Application (where safe):**
   - Some rules are independent (can run in parallel)
   - Example: RemoveGO and RemoveTRUNCATE don't interact
   - Use priority groups: Group 1 (parallel) → Group 2 (parallel) → ...

3. **Regex Compilation:**
   ```python
   class RegexRule:
       def __init__(self, name, pattern, ...):
           self.pattern = pattern
           self._compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)

       def apply(self, sql: str) -> str:
           return self._compiled.sub(self.replacement, sql)
   ```

### 6.3 Performance Metrics

**Add Monitoring:**
```python
class RuleEngine:
    def apply_all(self, sql: str, verbose: bool = False) -> str:
        start_time = time.time()

        # Apply rules
        result = self._apply_rules(sql, verbose)

        # Track metrics
        elapsed = time.time() - start_time
        self._record_metrics({
            'sql_size': len(sql),
            'cleaned_size': len(result),
            'duration_ms': elapsed * 1000,
            'rules_applied': len([r for r in self.rules if r.enabled])
        })

        return result
```

**Deliverables:**
- [ ] Caching implemented
- [ ] Early exit optimization
- [ ] Regex compilation
- [ ] Performance benchmarks (before/after)

**Timeline:** Week 7-8 (8-12 hours)

---

## Phase 7: Rule Statistics & Monitoring (Week 9)

### Objectives
- Track which rules fire most often
- Identify ineffective rules
- Monitor rule impact on accuracy

### 7.1 Rule Statistics

**Add to RuleEngine:**
```python
class RuleEngine:
    def __init__(self, rules=None):
        self.rules = rules or self._load_default_rules()
        self.stats = {
            'rules_fired': defaultdict(int),
            'rules_modified_sql': defaultdict(int),
            'rules_duration': defaultdict(float)
        }

    def apply_all(self, sql: str, verbose: bool = False) -> str:
        result = sql

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Time execution
            start = time.time()
            before_hash = hashlib.md5(result.encode()).hexdigest()

            result = rule.apply(result)

            after_hash = hashlib.md5(result.encode()).hexdigest()
            duration = time.time() - start

            # Track stats
            self.stats['rules_fired'][rule.name] += 1
            self.stats['rules_duration'][rule.name] += duration

            if before_hash != after_hash:
                self.stats['rules_modified_sql'][rule.name] += 1

        return result

    def get_statistics(self) -> Dict:
        """Get rule execution statistics"""
        return {
            'total_executions': sum(self.stats['rules_fired'].values()),
            'rules': [
                {
                    'name': name,
                    'fired': self.stats['rules_fired'][name],
                    'modified_sql': self.stats['rules_modified_sql'][name],
                    'avg_duration_ms': (self.stats['rules_duration'][name] / self.stats['rules_fired'][name]) * 1000,
                    'effectiveness': self.stats['rules_modified_sql'][name] / self.stats['rules_fired'][name]
                }
                for name in self.stats['rules_fired'].keys()
            ]
        }
```

### 7.2 Effectiveness Analysis

**Generate Report:**
```bash
python scripts/analyze_rule_effectiveness.py \
    --workspace lineage_workspace.duckdb \
    --output temp/rule_effectiveness_report.md
```

**Report Should Include:**
- Which rules fire most often (top 10)
- Which rules modify SQL most often (effectiveness)
- Which rules are slowest (performance)
- Correlation: Rule X → SQLGlot success rate

**Example Output:**
```
Rule Effectiveness Report
=========================

Top Rules by Frequency:
1. ExtractCoreDML: 763/763 (100%)
2. RemoveDECLARE: 542/763 (71%)
3. RemoveSET: 498/763 (65%)
4. ExtractTRY: 234/763 (31%)
5. RemoveEXEC: 187/763 (24%)

Top Rules by Impact (accuracy improvement):
1. ExtractCoreDML: +45% SQLGlot success
2. ExtractTRY: +18% SQLGlot success
3. RemoveDECLARE: +12% SQLGlot success

Least Effective Rules (consider removing):
1. RemoveTRUNCATE: 3/763 (0.4%) - rarely fires
```

**Deliverables:**
- [ ] Statistics tracking implemented
- [ ] Effectiveness report generated
- [ ] Ineffective rules identified
- [ ] Recommendations for rule refinement

**Timeline:** Week 9 (5-8 hours)

---

## Phase 8: Production Rollout (Week 10-12)

### Objectives
- Gradual rollout with monitoring
- A/B testing strategy
- Rollback plan if needed

### 8.1 Feature Flag Strategy

**Rollout Plan:**

1. **Week 10: Internal Testing (10% of objects)**
   ```python
   # In quality_aware_parser.py
   def should_use_cleaning(self, obj_name: str) -> bool:
       if not settings.enable_sql_cleaning:
           return False

       # Hash-based sampling (10%)
       obj_hash = int(hashlib.md5(obj_name.encode()).hexdigest(), 16)
       return (obj_hash % 100) < 10
   ```

2. **Week 11: Expanded Testing (50%)**
   - Increase to 50% of objects
   - Monitor confidence score changes
   - Check for unexpected regressions

3. **Week 12: Full Rollout (100%)**
   - Enable for all objects
   - Monitor for 1 week
   - Keep rollback ready

### 8.2 Monitoring Metrics

**Track in DuckDB:**
```sql
CREATE TABLE rule_engine_metrics (
    timestamp DATETIME,
    object_name VARCHAR,
    cleaning_enabled BOOLEAN,
    original_size INT,
    cleaned_size INT,
    reduction_pct FLOAT,
    sqlglot_success BOOLEAN,
    confidence_before FLOAT,
    confidence_after FLOAT,
    rules_applied INT,
    duration_ms FLOAT
)
```

**Daily Report:**
```bash
python scripts/daily_cleaning_report.py \
    --date $(date +%Y-%m-%d) \
    --output temp/daily_cleaning_report.md
```

### 8.3 Rollback Plan

**If problems occur:**

1. **Immediate Disable:**
   ```bash
   # Update .env
   ENABLE_SQL_CLEANING=false

   # Restart parser
   python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
   ```

2. **Identify Problem Objects:**
   ```sql
   SELECT object_name, confidence_before, confidence_after
   FROM rule_engine_metrics
   WHERE confidence_after < confidence_before - 0.10
   ORDER BY (confidence_before - confidence_after) DESC
   LIMIT 20
   ```

3. **Disable Specific Rules:**
   ```python
   # In quality_aware_parser.py
   engine = RuleEngine()
   engine.disable_rule("ExtractCoreDML")  # If this rule causes issues
   ```

4. **Revert to Previous Version:**
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

**Deliverables:**
- [ ] Gradual rollout complete (10% → 50% → 100%)
- [ ] Monitoring dashboards created
- [ ] No critical regressions detected
- [ ] Rollback procedures tested

**Timeline:** Week 10-12 (15-20 hours)

---

## Phase 9: Advanced Features (Future)

### 9.1 Rule Dependencies

**Problem:** Some rules must run before others

**Solution:** Explicit dependencies

```python
@dataclass
class CleaningRule(ABC):
    # ... existing fields ...
    depends_on: List[str] = field(default_factory=list)

# Example:
def extract_core_dml() -> CallbackRule:
    return CallbackRule(
        name="ExtractCoreDML",
        depends_on=["RemoveGO", "RemoveDECLARE"],  # Must run after these
        priority=90,
        # ...
    )
```

### 9.2 Conditional Rules

**Problem:** Some rules should only run if pattern detected

**Solution:** Conditional execution

```python
@dataclass
class CleaningRule(ABC):
    # ... existing fields ...
    condition: Optional[Callable[[str], bool]] = None

# Example:
def extract_cursor_queries() -> CallbackRule:
    def has_cursor(sql: str) -> bool:
        return 'CURSOR' in sql.upper()

    return CallbackRule(
        name="ExtractCursorQueries",
        condition=has_cursor,  # Only run if CURSOR detected
        # ...
    )
```

### 9.3 Rule Composition

**Problem:** Complex transformations need multiple steps

**Solution:** Composite rules

```python
class CompositeRule(CleaningRule):
    """Rule composed of multiple sub-rules"""
    def __init__(self, name: str, subrules: List[CleaningRule]):
        self.name = name
        self.subrules = subrules

    def apply(self, sql: str) -> str:
        result = sql
        for rule in self.subrules:
            result = rule.apply(result)
        return result

# Example:
def clean_error_handling() -> CompositeRule:
    """Composite rule for all error handling constructs"""
    return CompositeRule(
        name="CleanErrorHandling",
        subrules=[
            extract_try_content(),
            remove_raiserror(),
            remove_catch_blocks()
        ]
    )
```

### 9.4 Machine Learning-Assisted Rules

**Idea:** Use ML to identify patterns that break SQLGlot

**Approach:**
1. Collect failing SPs
2. Extract common patterns (n-grams, AST features)
3. Train classifier: Will SQLGlot succeed? (Y/N)
4. Generate rules for high-confidence failures

**Example:**
```python
def ml_suggested_rule() -> CallbackRule:
    """Rule suggested by ML analysis of SQLGlot failures"""
    def apply_ml_fix(sql: str) -> str:
        # Pattern identified by ML: FORMAT() calls with complex args
        pattern = r'FORMAT\s*\(\s*@\w+\s*,\s*[^)]+\)'
        return re.sub(pattern, 'CONVERT(VARCHAR, @var)', sql)

    return CallbackRule(
        name="MLSuggestedFormatFix",
        callback=apply_ml_fix,
        confidence=0.85  # ML confidence score
    )
```

---

## Testing Strategy

### Unit Tests

**Location:** `tests/test_sql_cleaning_rules.py`

```python
import pytest
from lineage_v3.parsers.sql_cleaning_rules import RuleEngine, SQLCleaningRules

class TestSQLCleaningRules:
    def test_remove_go_statements(self):
        rule = SQLCleaningRules.remove_go_statements()
        sql = "SELECT 1\nGO\nSELECT 2"
        result = rule.apply(sql)
        assert "GO" not in result
        assert "SELECT 1" in result
        assert "SELECT 2" in result

    def test_extract_try_content(self):
        rule = SQLCleaningRules.extract_try_content()
        sql = """
        BEGIN TRY
            SELECT * FROM dbo.Table1
        END TRY
        BEGIN CATCH
            RAISERROR('Error', 16, 1)
        END CATCH
        """
        result = rule.apply(sql)
        assert "BEGIN TRY" not in result
        assert "BEGIN CATCH" not in result
        assert "SELECT * FROM dbo.Table1" in result

    def test_rule_engine_integration(self):
        engine = RuleEngine()
        sql = """
        CREATE PROC dbo.Test AS
        BEGIN
            DECLARE @var INT
            SET @var = 1
            GO
            SELECT * FROM dbo.Table1
        END
        """
        result = engine.apply_all(sql)
        assert "DECLARE" not in result
        assert "SET @var" not in result
        assert "GO" not in result
        assert "SELECT * FROM dbo.Table1" in result

    def test_all_rules_have_examples(self):
        engine = RuleEngine()
        for rule in engine.rules:
            assert len(rule.examples_before) > 0, f"Rule {rule.name} missing examples"
            assert len(rule.examples_after) > 0, f"Rule {rule.name} missing examples"

    def test_all_rules_pass_examples(self):
        engine = RuleEngine()
        for rule in engine.rules:
            assert rule.test(), f"Rule {rule.name} failed its own examples"
```

### Integration Tests

**Location:** `tests/test_cleaning_integration.py`

```python
import sqlglot
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser

class TestCleaningIntegration:
    def test_cleaning_improves_sqlglot_success(self):
        """Test that cleaning improves SQLGlot success rate"""
        parser = QualityAwareParser()

        # Known failing SP
        sql = """
        CREATE PROC dbo.Test AS
        BEGIN TRY
            SELECT * FROM dbo.Table1
        END TRY
        BEGIN CATCH
            RAISERROR('Error', 16, 1)
        END CATCH
        """

        # Without cleaning - should fail
        try:
            sqlglot.parse_one(sql, read='tsql')
            success_without = True
        except:
            success_without = False

        # With cleaning - should succeed
        result = parser._parse_with_sqlglot(sql, "dbo.Test")
        success_with = result['sources'] or result['targets']

        assert not success_without
        assert success_with

    def test_cleaning_maintains_accuracy(self):
        """Test that cleaning doesn't harm accuracy"""
        parser = QualityAwareParser()

        # SP with known tables
        sql = """
        CREATE PROC dbo.Test AS
        BEGIN
            INSERT INTO dbo.Target
            SELECT * FROM dbo.Source1
            JOIN dbo.Source2 ON ...
        END
        """

        result = parser._parse_with_sqlglot(sql, "dbo.Test")

        assert "dbo.Target" in result['targets']
        assert "dbo.Source1" in result['sources']
        assert "dbo.Source2" in result['sources']
```

### Performance Tests

**Location:** `tests/test_cleaning_performance.py`

```python
import time
from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

class TestCleaningPerformance:
    def test_cleaning_performance(self):
        """Test that cleaning completes in reasonable time"""
        engine = RuleEngine()

        # Large SQL (14KB like test SP)
        with open('temp/test_hint_validation_CORRECTED.sql', 'r') as f:
            sql = f.read()

        # Should complete in <50ms
        start = time.time()
        result = engine.apply_all(sql)
        duration = time.time() - start

        assert duration < 0.05, f"Cleaning too slow: {duration*1000:.0f}ms"
        assert len(result) < len(sql), "Should reduce SQL size"

    def test_cache_effectiveness(self):
        """Test that caching improves performance"""
        engine = RuleEngine(cache_enabled=True)

        sql = "SELECT * FROM dbo.Table1"

        # First run (cold)
        start = time.time()
        result1 = engine.apply_all(sql)
        duration_cold = time.time() - start

        # Second run (cached)
        start = time.time()
        result2 = engine.apply_all(sql)
        duration_cached = time.time() - start

        assert result1 == result2
        assert duration_cached < duration_cold * 0.5, "Cache should be 2x+ faster"
```

---

## Success Metrics

### Primary Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| SQLGlot Success Rate | ~5% | 80%+ | % of objects successfully parsed |
| Method Agreement | ~50% | 75%+ | % where regex & SQLGlot agree |
| Avg Confidence Score | 0.70 | 0.80+ | Mean confidence across all objects |
| Table Extraction Accuracy | 95.5% | 96%+ | Precision/recall vs golden records |

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cleaning Time | <50ms per SP | 95th percentile |
| Cache Hit Rate | >80% (incremental) | Cache hits / total |
| Memory Usage | <100MB | Rule engine overhead |
| Zero Regressions | 100% | Objects with lower confidence |

### Operational Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Rule Effectiveness | >50% | % of rules that modify SQL |
| False Positive Rate | <5% | % cleaning makes parsing worse |
| Documentation Coverage | 100% | All rules documented with examples |
| Test Coverage | >90% | Line coverage in sql_cleaning_rules.py |

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cleaning breaks valid SQL | Medium | High | Extensive testing, fallback to original SQL |
| Performance degradation | Low | Medium | Caching, optimization, benchmarking |
| New T-SQL construct not handled | High | Low | Rule engine extensible, monitor failures |
| Rule conflicts (order matters) | Medium | Medium | Priority system, dependency tracking |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Confidence scores change unexpectedly | Medium | Medium | Gradual rollout, monitoring, rollback plan |
| User confusion about new results | Low | Low | Documentation, release notes |
| Maintenance burden (many rules) | Medium | Low | Self-documenting rules, effectiveness analysis |

### Rollback Triggers

**Immediately disable cleaning if:**
- More than 5% of objects show confidence regression >0.10
- Average confidence drops >0.05
- Critical SP accuracy drops below 90%
- Performance impact >20% (p95 parsing time)

---

## Documentation Plan

### Developer Documentation

1. **`temp/SQL_CLEANING_ENGINE_DOCUMENTATION.md`** ✅ Complete
   - Architecture overview
   - Usage guide
   - Rule reference
   - Testing guide

2. **`docs/PARSING_USER_GUIDE.md`** (Update)
   - Add section: "How SQL Cleaning Works"
   - Troubleshooting section
   - When to disable cleaning

3. **`docs/PARSER_EVOLUTION_LOG.md`** (Update)
   - Add entry for SQL Cleaning Engine v1.0.0
   - Document performance improvements
   - Link to this action plan

### User Documentation

4. **Release Notes**
   - Summary of changes
   - Expected improvements
   - How to disable if needed

5. **Training Materials**
   - Presentation: "Understanding SQL Cleaning"
   - Video walkthrough
   - FAQ document

---

## Timeline Summary

| Phase | Duration | Description | Deliverable |
|-------|----------|-------------|-------------|
| **Phase 1** | Week 1-2 | Integration & baseline | Production integration complete |
| **Phase 2** | Week 3 | CURSOR handling | CURSOR rules implemented |
| **Phase 3** | Week 4 | WHILE loops | WHILE rules implemented |
| **Phase 4** | Week 5 | IF/ELSE logic | IF/ELSE rules implemented |
| **Phase 5** | Week 6 | Dynamic SQL | Dynamic SQL rules implemented |
| **Phase 6** | Week 7-8 | Performance optimization | Caching & optimization complete |
| **Phase 7** | Week 9 | Statistics & monitoring | Effectiveness report |
| **Phase 8** | Week 10-12 | Production rollout | Full rollout (100%) |
| **Phase 9** | Future | Advanced features | ML-assisted rules, dependencies |

**Total Estimated Effort:** 60-80 hours over 12 weeks

---

## Open Questions

1. **Should we clean SQL before or after extracting comment hints?**
   - **Before:** Hints in original SQL, clean for SQLGlot
   - **After:** Clean might remove hint comments
   - **Recommendation:** Before cleaning (hints are in comments, won't be removed)

2. **How aggressive should we be with extraction?**
   - **Conservative:** Only remove clearly problematic constructs
   - **Aggressive:** Extract all DML, even from complex control flow
   - **Recommendation:** Start conservative, measure impact, increase gradually

3. **Should we store both original and cleaned SQL?**
   - **Pros:** Debugging, auditing, comparison
   - **Cons:** 2x storage, complexity
   - **Recommendation:** Store metadata only (size, reduction %, rules applied)

4. **How to handle edge cases (nested WHILE, dynamic CURSOR)?**
   - **Option 1:** Skip cleaning for edge cases
   - **Option 2:** Best-effort cleaning with fallback
   - **Recommendation:** Best-effort with fallback to original

---

## Next Steps (Immediate)

1. **Review this action plan** with team
2. **Prioritize phases** based on business needs
3. **Set up development environment** for rule testing
4. **Create baseline metrics** (run full evaluation without cleaning)
5. **Begin Phase 1** integration work

---

## References

- **Implementation:** `lineage_v3/parsers/sql_cleaning_rules.py`
- **Documentation:** `temp/SQL_CLEANING_ENGINE_DOCUMENTATION.md`
- **Test SP:** `temp/test_hint_validation_CORRECTED.sql`
- **Confidence Model:** `lineage_v3/utils/confidence_calculator.py`
- **Quality Parser:** `lineage_v3/parsers/quality_aware_parser.py`

---

**Document Owner:** Data Lineage Team
**Last Updated:** 2025-11-06
**Status:** 📋 Planning Complete - Ready for Phase 1
**Next Review:** After Phase 1 completion (Week 2)
