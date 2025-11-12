# Updated DMV Queries for UDF Support and Dynamic SQL

**Date:** 2025-11-11
**Goal:** Extract UDFs from DMV and filter query logs for dynamic SQL patterns

---

## Part 1: Updated DMV Query for UDFs

### Current Issue

**Problem:** 25 UDF definitions exist in the database, but DMV query is NOT extracting them

**Current query filters:**
```sql
WHERE o.type IN ('P', 'V', 'U')  -- Only SPs, Views, Tables
```

**Missing:** Functions (Scalar UDFs, Table-Valued Functions, Inline Functions)

### SQL Server Object Types

| Type | Description | Include? |
|------|-------------|----------|
| **P** | Stored Procedure | ✅ Currently included |
| **V** | View | ✅ Currently included |
| **U** | User Table | ✅ Currently included |
| **FN** | Scalar Function | ⚠️ **MISSING** |
| **IF** | Inline Table-Valued Function | ⚠️ **MISSING** |
| **TF** | Table-Valued Function | ⚠️ **MISSING** |
| **AF** | Aggregate Function (CLR) | ❌ Exclude (CLR) |
| **FS** | Assembly Scalar Function (CLR) | ❌ Exclude (CLR) |
| **FT** | Assembly Table-Valued Function (CLR) | ❌ Exclude (CLR) |

### Updated Object Catalog Query

```sql
-- Extract objects WITH UDF support
SELECT
    o.object_id,
    SCHEMA_NAME(o.schema_id) AS schema_name,
    o.name AS object_name,
    CASE o.type
        WHEN 'P' THEN 'Stored Procedure'
        WHEN 'V' THEN 'View'
        WHEN 'U' THEN 'Table'
        WHEN 'FN' THEN 'Scalar Function'
        WHEN 'IF' THEN 'Inline Table-Valued Function'
        WHEN 'TF' THEN 'Table-Valued Function'
        ELSE 'Other'
    END AS object_type,
    o.create_date,
    o.modify_date
FROM sys.objects o
WHERE o.type IN ('P', 'V', 'U', 'FN', 'IF', 'TF')  -- Added FN, IF, TF
  AND o.is_ms_shipped = 0  -- Exclude system objects
  AND SCHEMA_NAME(o.schema_id) NOT IN ('sys', 'INFORMATION_SCHEMA')  -- Exclude system schemas
ORDER BY o.object_id;
```

**Changes:**
- Added `'FN'` (Scalar Function)
- Added `'IF'` (Inline Table-Valued Function)
- Added `'TF'` (Table-Valued Function)
- Updated CASE statement to include UDF types

**Expected result:** Extract 25 additional UDFs

### Updated Definitions Query

```sql
-- Extract definitions for SPs, Views, and UDFs
SELECT
    o.object_id,
    o.name AS object_name,
    SCHEMA_NAME(o.schema_id) AS schema_name,
    m.definition
FROM sys.objects o
INNER JOIN sys.sql_modules m ON o.object_id = m.object_id
WHERE o.type IN ('P', 'V', 'FN', 'IF', 'TF')  -- Added FN, IF, TF
  AND o.is_ms_shipped = 0
  AND SCHEMA_NAME(o.schema_id) NOT IN ('sys', 'INFORMATION_SCHEMA')
ORDER BY o.object_id;
```

**Changes:**
- Added `'FN', 'IF', 'TF'` to filter
- Will extract UDF definitions for parsing

### SQLGlot UDF Support

**Question:** Can SQLGlot parse UDF definitions?

**Answer:** YES! SQLGlot supports SQL function definitions

**Test:**
```python
import sqlglot

udf_sql = """
CREATE FUNCTION dbo.udfDateKeyToDate (@DateKey INT)
RETURNS DATE
AS
BEGIN
    DECLARE @ret DATE;
    SET @ret = CONVERT(DATE, SUBSTRING(CAST(@DateKey AS VARCHAR), 1, 8));
    RETURN @ret;
END
"""

# Parse with WARN mode
parsed = sqlglot.parse(udf_sql, dialect='tsql', error_level=ErrorLevel.WARN)

# SQLGlot will create a Create node with UserDefinedFunction
# Can extract:
# - Function name (udfDateKeyToDate)
# - Parameters (@DateKey INT)
# - Return type (DATE)
# - Function body (BEGIN...END)
```

**Lineage extraction from UDFs:**
- Extract table references in function body
- Functions can reference tables/views
- Functions can call other functions
- UDF → Table lineage is valuable!

**Example UDF with table reference:**
```sql
CREATE FUNCTION dbo.GetCustomerOrders(@CustomerId INT)
RETURNS TABLE
AS
RETURN
(
    SELECT *
    FROM Sales.Orders o
    INNER JOIN Sales.OrderDetails od ON o.OrderId = od.OrderId
    WHERE o.CustomerId = @CustomerId
)
```

**Lineage:**
- UDF: `dbo.GetCustomerOrders`
- Input tables: `Sales.Orders`, `Sales.OrderDetails`

---

## Part 2: Query Log Filter for Dynamic SQL

### Current Issue

**Problem:** Query logs contain all queries (metadata, ad-hoc, dynamic SQL)

**Current:** 297 queries total
- 260 SELECT (metadata queries, ad-hoc reads)
- 21 UPDATE (data changes)
- 16 INSERT (data changes)

**Value:** Mixed (some valuable, some noise)

### Dynamic SQL Patterns

**What we want:** Only dynamic SQL that static analysis cannot resolve

**Patterns to capture:**
1. **sp_executesql** - Parameterized dynamic SQL
2. **EXEC(@sql)** - String variable execution
3. **EXECUTE(@sql)** - Same as EXEC
4. **sys.sp_executesql** - Fully qualified

**Patterns to EXCLUDE:**
1. Ad-hoc queries (not in stored procedures)
2. Metadata queries (sys.objects, INFORMATION_SCHEMA)
3. Static queries (regular SELECT/INSERT/UPDATE)

### Updated Query Log Filter

```sql
-- Extract ONLY dynamic SQL queries from query store
-- Focus on sp_executesql and EXEC(@var) patterns
SELECT DISTINCT
    q.query_id,
    qt.query_sql_text AS command_text,
    q.object_id,
    o.name AS object_name,
    SCHEMA_NAME(o.schema_id) AS schema_name,
    qrs.count_executions,
    qrs.last_execution_time
FROM sys.query_store_query q
INNER JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
INNER JOIN sys.query_store_plan qp ON q.query_id = qp.query_id
INNER JOIN sys.query_store_runtime_stats qrs ON qp.plan_id = qrs.plan_id
LEFT JOIN sys.objects o ON q.object_id = o.object_id
WHERE
    -- Filter 1: Dynamic SQL patterns
    (
        qt.query_sql_text LIKE '%sp_executesql%'
        OR qt.query_sql_text LIKE '%EXEC(@%'
        OR qt.query_sql_text LIKE '%EXECUTE(@%'
        OR qt.query_sql_text LIKE '%EXEC %@%'
        OR qt.query_sql_text LIKE '%EXECUTE %@%'
    )
    -- Filter 2: Executed in last 30 days
    AND qrs.last_execution_time >= DATEADD(day, -30, GETUTCDATE())
    -- Filter 3: Exclude system queries
    AND qt.query_sql_text NOT LIKE '%sys.%'
    AND qt.query_sql_text NOT LIKE '%INFORMATION_SCHEMA%'
    -- Filter 4: Minimum execution count (not one-off queries)
    AND qrs.count_executions >= 10
ORDER BY qrs.count_executions DESC;
```

**Filters explained:**

1. **Dynamic SQL patterns:**
   - `sp_executesql` - Standard parameterized dynamic SQL
   - `EXEC(@var)` - Variable execution
   - `EXECUTE(@var)` - Same as EXEC

2. **Time-based:**
   - Last 30 days - Recent queries only
   - Configurable based on workload

3. **Exclude system:**
   - No `sys.` tables
   - No `INFORMATION_SCHEMA`

4. **Frequency filter:**
   - `count_executions >= 10` - Only frequently used dynamic SQL
   - Filters out one-off queries
   - Focuses on production patterns

**Expected result:**
- Fewer queries (10-50 instead of 297)
- Higher value (all dynamic SQL)
- Better ROI (solves static analysis limitation)

### Alternative: Extended Events

If Query Store is not enabled, use Extended Events:

```sql
-- Create Extended Events session for dynamic SQL
CREATE EVENT SESSION [DynamicSQLCapture] ON SERVER
ADD EVENT sqlserver.sp_statement_completed(
    ACTION(
        sqlserver.sql_text,
        sqlserver.database_name,
        sqlserver.session_id
    )
    WHERE (
        sqlserver.sql_text LIKE '%sp_executesql%'
        OR sqlserver.sql_text LIKE '%EXEC(@%'
        OR sqlserver.sql_text LIKE '%EXECUTE(@%'
    )
)
ADD TARGET package0.event_file(
    SET filename=N'DynamicSQLCapture.xel',
    max_file_size=(100)
)
WITH (
    MAX_MEMORY=4096 KB,
    EVENT_RETENTION_MODE=ALLOW_SINGLE_EVENT_LOSS,
    MAX_DISPATCH_LATENCY=30 SECONDS
);

-- Start session
ALTER EVENT SESSION [DynamicSQLCapture] ON SERVER STATE = START;
```

**Benefits:**
- Real-time capture
- Low overhead
- Configurable filters

---

## Part 3: Integration with Parser

### UDF Lineage Extraction

**Update SimplifiedParser to handle UDFs:**

```python
def parse_object(self, object_id: int) -> Dict[str, Any]:
    """Parse SP, View, or UDF"""

    # Check object type
    object_type = self._get_object_type(object_id)

    if object_type in ['Stored Procedure', 'Scalar Function',
                       'Inline Table-Valued Function', 'Table-Valued Function']:
        # Parse with WARN mode (works for UDFs too!)
        return self._parse_with_warn_best_effort(ddl)
    elif object_type == 'View':
        # Parse view definition
        return self._parse_view(ddl)
    else:
        # Unknown type
        return self._parse_error(object_id, 'Unsupported object type')
```

**UDF-specific considerations:**

1. **Scalar Functions:**
   - Parse function body
   - Extract table references
   - UDF → Table lineage

2. **Table-Valued Functions:**
   - Parse RETURN statement
   - Extract from SELECT statement
   - UDF → Table lineage

3. **Inline Table-Valued Functions:**
   - Parse RETURN SELECT
   - Direct table references
   - UDF → Table lineage

**Example UDF lineage:**
```python
# UDF definition
CREATE FUNCTION dbo.GetActiveCustomers()
RETURNS TABLE
AS
RETURN
(
    SELECT c.CustomerId, c.Name
    FROM Sales.Customers c
    WHERE c.IsActive = 1
)

# Parsed lineage
{
    'object_id': 12345,
    'object_name': 'dbo.GetActiveCustomers',
    'object_type': 'Inline Table-Valued Function',
    'inputs': ['Sales.Customers'],
    'outputs': [],  # Functions don't write data
    'confidence': 100
}
```

### Dynamic SQL Lineage Extraction

**Process dynamic SQL queries:**

```python
def parse_dynamic_sql_query(query_text: str) -> Dict[str, Any]:
    """
    Parse dynamic SQL from query logs

    Example:
        EXEC sp_executesql N'SELECT * FROM Sales.Orders WHERE OrderId = @p1'
    """

    # Extract SQL text from sp_executesql
    if 'sp_executesql' in query_text.lower():
        # Pattern: EXEC sp_executesql N'<SQL>'
        match = re.search(r"sp_executesql\s+N'([^']*)'", query_text, re.IGNORECASE)
        if match:
            sql_text = match.group(1)
            # Parse extracted SQL with WARN mode
            return self._parse_with_warn_best_effort(sql_text)

    # Extract SQL from EXEC(@var)
    elif 'exec(' in query_text.lower() or 'execute(' in query_text.lower():
        # Pattern: EXEC(@SqlString)
        # Cannot resolve without runtime variable value
        return {
            'parse_method': 'dynamic_unresolved',
            'reason': 'Variable content unknown',
            'confidence': 0
        }
```

**Value:**
- Captures lineage from dynamic SQL that static analysis misses
- Complements static analysis (fills the 5-10% gap)
- Real production patterns (from query logs)

---

## Summary

### 1. UDF Support ✅

**Status:** Can be extracted and parsed

**Action items:**
- [x] Update DMV query to include `'FN', 'IF', 'TF'`
- [ ] Test UDF parsing with SQLGlot WARN mode
- [ ] Extract UDF → Table lineage
- [ ] Add UDF support to SimplifiedParser

**Expected benefit:** +25 objects, complete function lineage

### 2. Dynamic SQL Filtering ✅

**Status:** Query log filter can focus on dynamic SQL only

**Action items:**
- [x] Create query log filter for sp_executesql patterns
- [ ] Test filter on production query store
- [ ] Extract dynamic SQL text
- [ ] Parse with WARN mode

**Expected benefit:**
- Higher quality query logs (10-50 dynamic SQL queries vs 297 mixed)
- Solves static analysis limitation
- Captures runtime lineage

### 3. Implementation Priority

**Phase B (Current):** Simplify rules 17 → 7
**Phase C (Next):** Add UDF support
**Phase D (Future):** Add dynamic SQL query log integration

---

**Status:** Ready for implementation
**Next step:** Continue with Option B (simplified 7-rule engine)
