# Comprehensive Dynamic SQL Patterns in SQL Server

**Date:** 2025-11-11
**Source:** Microsoft Learn, Stack Overflow, SQL Server documentation

---

## All Dynamic SQL Execution Patterns

### Pattern 1: EXEC with Variable
```sql
-- Most common pattern
DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM Sales.Orders WHERE OrderId = 123'
EXEC(@sql)

-- Or with EXECUTE (same thing)
EXECUTE(@sql)

-- With spaces (also valid)
EXEC (@sql)
EXECUTE (@sql)
```

**Query Log Signature:**
- `EXEC(@variableName)`
- `EXECUTE(@variableName)`
- `EXEC (@variableName)` (with space)

### Pattern 2: EXEC with Literal String (Direct)
```sql
-- Direct string execution WITHOUT variable
EXEC('SELECT * FROM Sales.Orders WHERE OrderId = 123')

-- Or EXECUTE
EXECUTE('SELECT * FROM Sales.Orders WHERE OrderId = 123')

-- Multi-line
EXEC('
    SELECT o.*, c.CustomerName
    FROM Sales.Orders o
    INNER JOIN Sales.Customers c ON o.CustomerId = c.CustomerId
')
```

**Query Log Signature:**
- `EXEC('SQL text')`
- `EXECUTE('SQL text')`
- `EXEC("SQL text")` (double quotes, less common)

**Key Point:** This pattern is DIRECTLY PARSEABLE because the SQL is right there in the string literal!

### Pattern 3: EXEC with Concatenated String
```sql
-- Building SQL dynamically
DECLARE @tableName NVARCHAR(100) = 'Orders'
DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM Sales.' + @tableName
EXEC(@sql)

-- More complex concatenation
DECLARE @sql NVARCHAR(MAX) =
    'SELECT * FROM Sales.Orders WHERE ' +
    'OrderDate >= ''' + @StartDate + ''' AND ' +
    'OrderDate <= ''' + @EndDate + ''''
EXEC(@sql)
```

**Query Log Signature:**
- May log the FINAL resolved SQL (depends on Query Store config)
- Or may log `EXEC(@sql)` placeholder

### Pattern 4: sp_executesql Basic
```sql
-- Standard parameterized pattern
DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM Sales.Orders WHERE OrderId = @p1'
EXEC sp_executesql @sql, N'@p1 INT', @p1 = 123

-- Without EXEC keyword (also valid)
sp_executesql @sql, N'@p1 INT', @p1 = 123

-- Fully qualified
EXEC sys.sp_executesql @sql, N'@p1 INT', @p1 = 123
```

**Query Log Signature:**
- `sp_executesql`
- `EXEC sp_executesql`
- `sys.sp_executesql`

### Pattern 5: sp_executesql with Multiple Parameters
```sql
-- Multiple parameters
DECLARE @sql NVARCHAR(MAX) = N'
    SELECT * FROM Sales.Orders
    WHERE OrderDate >= @StartDate
      AND OrderDate <= @EndDate
      AND CustomerId = @CustId
'
DECLARE @params NVARCHAR(MAX) = N'@StartDate DATE, @EndDate DATE, @CustId INT'

EXEC sp_executesql @sql, @params,
    @StartDate = '2024-01-01',
    @EndDate = '2024-12-31',
    @CustId = 100
```

### Pattern 6: sp_executesql with Output Parameters
```sql
-- With OUTPUT parameter
DECLARE @sql NVARCHAR(MAX) = N'SELECT @count = COUNT(*) FROM Sales.Orders'
DECLARE @params NVARCHAR(MAX) = N'@count INT OUTPUT'
DECLARE @OrderCount INT

EXEC sp_executesql @sql, @params, @count = @OrderCount OUTPUT
```

### Pattern 7: EXEC with Stored Procedure Name (NOT dynamic SQL)
```sql
-- This is NOT dynamic SQL - it's calling a stored procedure
EXEC dbo.MyStoredProcedure @param1, @param2

-- Or
EXECUTE dbo.MyStoredProcedure @param1, @param2
```

**Important:** This is NOT dynamic SQL! It's a direct SP call.

**Query Log Filter:** EXCLUDE this pattern

### Pattern 8: EXEC with String Variable + Concatenation
```sql
-- Multiple statements
DECLARE @sql1 NVARCHAR(MAX) = 'INSERT INTO dbo.Log VALUES (1, ''Start'')'
DECLARE @sql2 NVARCHAR(MAX) = 'UPDATE dbo.Config SET Value = ''Active'''
DECLARE @sql3 NVARCHAR(MAX) = 'INSERT INTO dbo.Log VALUES (2, ''End'')'

EXEC(@sql1 + '; ' + @sql2 + '; ' + @sql3)
```

### Pattern 9: EXEC AT (Linked Server - Distributed Query)
```sql
-- Execute on linked server
EXEC('SELECT * FROM Sales.Orders') AT LinkedServerName

-- Or
EXECUTE('SELECT * FROM Sales.Orders') AT LinkedServerName
```

**Query Log Signature:**
- `EXEC(...) AT`
- `EXECUTE(...) AT`

**Note:** These are distributed queries, not typical dynamic SQL

---

## Updated Query Log Filter (Comprehensive)

```sql
-- Extract ALL dynamic SQL patterns from Query Store
-- Updated: 2025-11-11 - Comprehensive pattern coverage
SELECT DISTINCT
    q.query_id,
    qt.query_sql_text AS sql_text,
    q.object_id,
    OBJECT_SCHEMA_NAME(q.object_id) AS schema_name,
    OBJECT_NAME(q.object_id) AS object_name,
    qrs.count_executions,
    qrs.last_execution_time,

    -- Pattern detection
    CASE
        WHEN qt.query_sql_text LIKE '%sp_executesql%' THEN 'sp_executesql'
        WHEN qt.query_sql_text LIKE '%EXEC(@%' OR qt.query_sql_text LIKE '%EXECUTE(@%' THEN 'EXEC(@var)'
        WHEN qt.query_sql_text LIKE "%EXEC('%" OR qt.query_sql_text LIKE '%EXEC("%' THEN 'EXEC(literal)'
        WHEN qt.query_sql_text LIKE '%EXEC %@%' OR qt.query_sql_text LIKE '%EXECUTE %@%' THEN 'EXEC @var'
        WHEN qt.query_sql_text LIKE '%EXEC%AT%' THEN 'EXEC AT (linked server)'
        ELSE 'other'
    END AS dynamic_sql_pattern

FROM sys.query_store_query q
INNER JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
INNER JOIN sys.query_store_plan qp ON q.query_id = qp.query_id
INNER JOIN sys.query_store_runtime_stats qrs ON qp.plan_id = qrs.plan_id

WHERE
    -- PATTERN GROUP 1: sp_executesql (all variations)
    (
        qt.query_sql_text LIKE '%sp_executesql%'
        OR qt.query_sql_text LIKE '%sys.sp_executesql%'
    )

    -- PATTERN GROUP 2: EXEC(@variable) / EXECUTE(@variable)
    OR (
        qt.query_sql_text LIKE '%EXEC(@%'
        OR qt.query_sql_text LIKE '%EXECUTE(@%'
        OR qt.query_sql_text LIKE '%EXEC %(@%'  -- With space: EXEC (@var)
        OR qt.query_sql_text LIKE '%EXECUTE %(@%'
    )

    -- PATTERN GROUP 3: EXEC('literal string') / EXECUTE('literal string')
    OR (
        (qt.query_sql_text LIKE "%EXEC('%" OR qt.query_sql_text LIKE '%EXEC("%')
        AND (
            qt.query_sql_text LIKE '%SELECT%'
            OR qt.query_sql_text LIKE '%INSERT%'
            OR qt.query_sql_text LIKE '%UPDATE%'
            OR qt.query_sql_text LIKE '%DELETE%'
            OR qt.query_sql_text LIKE '%MERGE%'
        )
    )

    -- PATTERN GROUP 4: EXEC @variable (no parentheses - less common but valid)
    OR (
        qt.query_sql_text LIKE '%EXEC %@%'
        OR qt.query_sql_text LIKE '%EXECUTE %@%'
    )

    -- PATTERN GROUP 5: EXEC AT (linked server)
    OR (
        qt.query_sql_text LIKE '%EXEC%AT%'
        OR qt.query_sql_text LIKE '%EXECUTE%AT%'
    )

    -- Time filter
    AND qrs.last_execution_time >= DATEADD(day, -30, GETUTCDATE())

    -- Exclude system queries
    AND qt.query_sql_text NOT LIKE '%sys.%'
    AND qt.query_sql_text NOT LIKE '%INFORMATION_SCHEMA%'
    AND qt.query_sql_text NOT LIKE '%sp_help%'
    AND qt.query_sql_text NOT LIKE '%sp_columns%'

    -- CRITICAL: Exclude direct SP calls (not dynamic SQL)
    -- Pattern: EXEC dbo.ProcedureName @param1, @param2
    AND NOT (
        qt.query_sql_text LIKE '%EXEC %dbo.%'
        AND qt.query_sql_text NOT LIKE '%EXEC(@%'
        AND qt.query_sql_text NOT LIKE "%EXEC('%"
        AND qt.query_sql_text NOT LIKE '%sp_executesql%'
    )

    -- Frequency filter (production patterns only)
    AND qrs.count_executions >= 10

    -- Length filter (exclude short queries)
    AND LEN(qt.query_sql_text) > 50

ORDER BY
    dynamic_sql_pattern,
    qrs.count_executions DESC;
```

---

## Extraction and Parsing Logic (Updated)

### Priority 1: EXEC('literal string') - DIRECTLY PARSEABLE ✅

```python
def extract_exec_literal_string(query_text):
    """
    Extract SQL from EXEC('literal string') pattern

    THIS IS THE EASIEST PATTERN - SQL is right there!

    Example:
        EXEC('SELECT * FROM Sales.Orders WHERE OrderId = 123')

    Returns:
        SELECT * FROM Sales.Orders WHERE OrderId = 123
    """
    import re

    # Pattern 1: EXEC('...') or EXECUTE('...')
    patterns = [
        r"EXEC\s*\(\s*'([^']*?)'\s*\)",  # EXEC('...')
        r"EXECUTE\s*\(\s*'([^']*?)'\s*\)",  # EXECUTE('...')
        r'EXEC\s*\(\s*"([^"]*?)"\s*\)',  # EXEC("...") - double quotes
        r'EXECUTE\s*\(\s*"([^"]*?)"\s*\)',  # EXECUTE("...")
    ]

    for pattern in patterns:
        match = re.search(pattern, query_text, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1)
            # Handle escaped quotes
            sql = sql.replace("''", "'")
            sql = sql.replace('""', '"')
            return sql

    return None


def extract_sp_executesql(query_text):
    """
    Extract SQL from sp_executesql pattern

    Example:
        EXEC sp_executesql N'SELECT * FROM Sales.Orders WHERE OrderId = @p1', N'@p1 INT', @p1 = 123

    Returns:
        SELECT * FROM Sales.Orders WHERE OrderId = @p1
    """
    import re

    # Patterns for sp_executesql
    patterns = [
        r"sp_executesql\s+N'([^']*)'",  # Basic
        r"sp_executesql\s+@\w+\s*=\s*N'([^']*)'",  # Named parameter
        r"sp_executesql\s+N\"([^\"]*?)\"",  # Double quotes (rare)
    ]

    for pattern in patterns:
        match = re.search(pattern, query_text, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1)
            sql = sql.replace("''", "'")
            return sql

    return None


def extract_exec_variable(query_text):
    """
    Extract from EXEC(@variable) pattern

    Example:
        EXEC(@SqlString)

    Returns:
        None (cannot resolve variable) OR actual SQL if Query Store logged it
    """
    # If query log contains EXEC(@...), we CANNOT resolve it
    if re.search(r'EXEC\s*\(@\w+\)', query_text, re.IGNORECASE):
        return None  # Unresolvable

    # If query log contains actual SQL (Query Store resolved it), return it
    # This happens when Query Store logs the executed SQL, not the EXEC statement
    return query_text


def parse_dynamic_sql_from_query_log(query_text, workspace):
    """
    Parse dynamic SQL from query logs - PRIORITY ORDER

    Priority:
    1. EXEC('literal') - Directly parseable ✅
    2. sp_executesql - Extract SQL from first parameter ✅
    3. EXEC(@var) - May be unresolvable ⚠️
    """
    from simplified_parser import SimplifiedParser
    import sqlglot
    from sqlglot.errors import ErrorLevel

    # Priority 1: EXEC('literal string') - EASIEST!
    sql = extract_exec_literal_string(query_text)
    if sql:
        # Parse extracted SQL
        parser = SimplifiedParser(workspace)
        try:
            parsed = sqlglot.parse(sql, dialect='tsql', error_level=ErrorLevel.WARN)
            sources, targets, sp_calls = parser._extract_from_parsed(parsed)

            # Validate
            sources_valid = parser._validate_against_catalog(sources)
            targets_valid = parser._validate_against_catalog(targets)

            return {
                'parse_method': 'dynamic_exec_literal',
                'confidence': 85,  # High confidence (runtime data)
                'inputs': list(sources_valid),
                'outputs': list(targets_valid),
                'source': 'query_log'
            }
        except Exception as e:
            return {'parse_method': 'failed', 'error': str(e)}

    # Priority 2: sp_executesql
    sql = extract_sp_executesql(query_text)
    if sql:
        # Parse extracted SQL (same as above)
        parser = SimplifiedParser(workspace)
        try:
            parsed = sqlglot.parse(sql, dialect='tsql', error_level=ErrorLevel.WARN)
            sources, targets, sp_calls = parser._extract_from_parsed(parsed)

            sources_valid = parser._validate_against_catalog(sources)
            targets_valid = parser._validate_against_catalog(targets)

            return {
                'parse_method': 'dynamic_sp_executesql',
                'confidence': 85,
                'inputs': list(sources_valid),
                'outputs': list(targets_valid),
                'source': 'query_log'
            }
        except Exception as e:
            return {'parse_method': 'failed', 'error': str(e)}

    # Priority 3: EXEC(@var) - May be unresolvable
    sql = extract_exec_variable(query_text)
    if sql is None:
        return {
            'parse_method': 'dynamic_unresolved',
            'confidence': 0,
            'reason': 'Variable content unknown (EXEC(@var))',
            'inputs': [],
            'outputs': []
        }

    # If Query Store logged the actual SQL, try parsing it
    parser = SimplifiedParser(workspace)
    try:
        parsed = sqlglot.parse(sql, dialect='tsql', error_level=ErrorLevel.WARN)
        sources, targets, sp_calls = parser._extract_from_parsed(parsed)

        sources_valid = parser._validate_against_catalog(sources)
        targets_valid = parser._validate_against_catalog(targets)

        return {
            'parse_method': 'dynamic_exec_resolved',
            'confidence': 75,  # Lower (may be Query Store interpretation)
            'inputs': list(sources_valid),
            'outputs': list(targets_valid),
            'source': 'query_log'
        }
    except Exception as e:
        return {'parse_method': 'failed', 'error': str(e)}
```

---

## Comparison: EXEC vs sp_executesql

### EXEC('literal') - Best for Query Logs!

**Advantages:**
✅ SQL is RIGHT THERE in the string literal - directly parseable!
✅ No variable resolution needed
✅ High confidence extraction
✅ Common in older code

**Example:**
```sql
EXEC('SELECT * FROM Sales.Orders WHERE OrderId = 123')
```

**Extraction:** Easy! Regex extract the string between `EXEC('...')`

### EXEC(@variable)

**Disadvantages:**
❌ Cannot resolve variable content from query log
❌ Need runtime value of `@variable`
❌ May log as `EXEC(@SqlString)` placeholder

**Workaround:** Query Store MAY log the actual executed SQL (depends on config)

### sp_executesql

**Advantages:**
✅ SQL string is first parameter - extractable
✅ Parameterized (secure)
✅ Plan reuse

**Example:**
```sql
EXEC sp_executesql N'SELECT * FROM Sales.Orders WHERE OrderId = @p1', N'@p1 INT', @p1 = 123
```

**Extraction:** Regex extract first N'...' parameter

**Disadvantage:**
⚠️ Parameters like `@p1` may need resolution (but table names are usually literal)

---

## Summary: Pattern Coverage

| Pattern | Example | Parseable? | Priority |
|---------|---------|------------|----------|
| **EXEC('literal')** | `EXEC('SELECT * FROM...')` | ✅ YES - Directly | **HIGH** |
| **sp_executesql** | `EXEC sp_executesql N'SELECT...'` | ✅ YES - Extract | **HIGH** |
| **EXEC(@var)** | `EXEC(@SqlString)` | ⚠️ MAYBE - Depends on log | **MEDIUM** |
| **EXEC AT** | `EXEC('SELECT...') AT Server` | ✅ YES - Extract | **LOW** |
| **EXEC SP_Name** | `EXEC dbo.MyProc @p1` | ❌ NO - Not dynamic SQL | **EXCLUDE** |

---

## Key Takeaway

**You were absolutely right!**

EXEC with literal strings like `EXEC('SELECT * FROM...')` is a CRITICAL pattern we need to capture. It's actually the **EASIEST pattern** to parse because the SQL is right there in the string literal!

**Updated filter priorities:**
1. ✅ **EXEC('literal string')** - Highest value (directly parseable)
2. ✅ **sp_executesql** - High value (extractable)
3. ⚠️ **EXEC(@variable)** - Medium value (may be unresolvable)

---

**Date:** 2025-11-11
**Status:** Comprehensive pattern coverage documented ✅
