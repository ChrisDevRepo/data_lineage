# Synapse DMV Query Log Filtering Research

## Problem with Current Approach
Excluding all queries starting with "SELECT %" will also exclude:
- Stored procedures that run SELECT statements
- Valid ETL queries that are SELECT-based
- Queries wrapped in EXEC that internally run SELECT

## Proper Ad-Hoc Detection in Synapse

In sys.dm_pdw_exec_requests, there's NO dedicated "is_adhoc" flag.

However, we can distinguish ad-hoc queries by:

1. **Session Context Columns:**
   - `session_id` - Interactive sessions have different patterns
   - `login_name` - User logins vs service accounts
   - `app_name` - SSMS/Azure Data Studio vs application name

2. **Command Characteristics:**
   - Ad-hoc queries typically DON'T have labels
   - Ad-hoc queries are direct SELECT/WITH statements
   - Stored procedure executions show as "EXEC" or "EXECUTE"

3. **Best Practice Filter:**
```sql
-- Include ONLY these query types:
WHERE (
    -- Stored procedure executions
    r.command LIKE 'EXEC %' OR
    r.command LIKE 'EXECUTE %' OR
    
    -- DML operations (INSERT/UPDATE/DELETE/MERGE)
    r.command LIKE 'INSERT %' OR
    r.command LIKE 'UPDATE %' OR
    r.command LIKE 'DELETE %' OR
    r.command LIKE 'MERGE %' OR
    r.command LIKE 'TRUNCATE %' OR
    
    -- Has a label (ETL process marker)
    r.[label] IS NOT NULL
)
-- Exclude system queries
AND r.command NOT LIKE '%sys.dm_pdw%'

-- NOTE: This excludes:
-- - Direct SELECT queries (ad-hoc)
-- - Direct WITH/CTE queries (ad-hoc)
-- - DDL operations (CREATE/ALTER/DROP) - not needed for lineage
```

## Why DDL is Not Helpful
DDL operations (CREATE/ALTER/DROP) don't provide lineage information:
- They modify schema structure, not data flow
- Parser already gets DDL from sys.sql_modules
- Including them adds noise without value

## Recommendation
Remove DDL from filter (CREATE/ALTER/DROP) and keep only:
- EXEC/EXECUTE (stored procedures)
- DML operations (INSERT/UPDATE/DELETE/MERGE/TRUNCATE)
- Labeled queries (if used)

