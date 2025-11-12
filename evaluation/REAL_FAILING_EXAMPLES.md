# Real Failing SQL Examples from Production

## Example 1: CONSUMPTION_FINANCE.spLoadDimCompanyKoncern

**Why it fails:** Temp table operations + IF EXISTS blocks + BEGIN/END nesting

```sql
-- Pattern 1: IF EXISTS with DROP TABLE
if object_id(N'tempdb..#Deduped_t_CompanyKoncern_filter') is not null
begin drop table #Deduped_t_CompanyKoncern_filter; end;

-- Pattern 2: SELECT INTO #temp (creates temp table)
WITH PartitionedCompanyKoncern AS
(
SELECT company, koncern, activ,
ROW_NUMBER() OVER (PARTITION BY company, koncern ORDER BY activ DESC) as RowNumber
FROM [STAGING_FINANCE_COGNOS].[t_Company_filter]
)
SELECT company, koncern, activ
INTO #Deduped_t_CompanyKoncern_filter  -- Creates temp table
FROM PartitionedCompanyKoncern
WHERE RowNumber = 1;

-- Pattern 3: Nested IF EXISTS with logic
IF EXISTS (SELECT Company,koncern, Count(*) CountCompanyKoncern
            FROM [STAGING_FINANCE_COGNOS].[t_Company_filter]
            GROUP BY Company, koncern
            HAVING COUNT(*)> 1 )
BEGIN
  SET @MSG = 'Error message'
  RAISERROR (@MSG,16,1);
END

-- Pattern 4: Temp table usage in DML
insert into [CONSUMPTION_FINANCE].[DimCompanyKoncern]
select #t.[company], #t.[Koncern], #t.[activ]  -- Uses #t
from #t
WHERE EXISTS (SELECT 1 FROM [CONSUMPTION_FINANCE].[DimCompanyKoncern] dc
              WHERE #t.Company = dc.Company);
```

**What we need:**
- Tables referenced: `STAGING_FINANCE_COGNOS.t_Company_filter`, `CONSUMPTION_FINANCE.DimCompanyKoncern`
- Temp tables: `#Deduped_t_CompanyKoncern_filter`, `#t` (should be ignored)

---

## Example 2: Pattern with WHILE Loop

```sql
DECLARE @Counter INT = 1
DECLARE @MaxCounter INT = 10

WHILE @Counter <= @MaxCounter
BEGIN
    INSERT INTO FactTable (ID, Value)
    SELECT @Counter, SomeValue
    FROM SourceTable
    WHERE Condition = @Counter

    SET @Counter = @Counter + 1
END
```

**Why it fails:** WHILE loop wrapper around INSERT statement

**What we need:**
- Extract: `INSERT INTO FactTable ... FROM SourceTable`
- Ignore: WHILE logic, @Counter variable

---

## Example 3: Complex IF/ELSE branches

```sql
IF @Mode = 1
BEGIN
    INSERT INTO TargetTable
    SELECT * FROM SourceA
END
ELSE IF @Mode = 2
BEGIN
    INSERT INTO TargetTable
    SELECT * FROM SourceB
END
ELSE
BEGIN
    INSERT INTO TargetTable
    SELECT * FROM SourceC
END
```

**Why it fails:** DML buried in IF/ELSE blocks

**What we need:**
- Extract all: `TargetTable`, `SourceA`, `SourceB`, `SourceC`
- Ignore: IF/ELSE control flow

---

## Simple, Smart Rules Needed

### Rule 1: Replace Temp Tables with Dummy Schema (USER'S BRILLIANT IDEA!)

**Before:**
```sql
SELECT * INTO #TempTable FROM RealTable
INSERT INTO #TempTable VALUES (1, 2)
SELECT * FROM #TempTable
```

**After:**
```sql
SELECT * INTO dummy.TempTable FROM RealTable
INSERT INTO dummy.TempTable VALUES (1, 2)
SELECT * FROM dummy.TempTable
```

**Why it works:**
- ✅ Valid SQL syntax - SQLGlot can parse it!
- ✅ Simple regex: `#(\w+)` → `dummy.$1`
- ✅ Filter out `dummy.*` objects later in catalog validation
- ✅ No need to remove CREATE TABLE / DROP TABLE

**Implementation:**
```python
class ReplaceTempTables(RegexRule):
    pattern = r'#(\w+)'
    replacement = r'dummy.\1'
    priority = 15  # Before DECLARE removal
```

---

### Rule 2: Remove IF EXISTS/IF NOT EXISTS Admin Checks

**Before:**
```sql
if object_id(N'tempdb..#temp') is not null
begin drop table #temp; end;

IF EXISTS (SELECT 1 FROM sys.objects WHERE name = 'Table')
    DROP TABLE Table
```

**After:**
```sql
-- Removed (not lineage-relevant)
```

**Why:** These are administrative checks, not data flow

**Implementation:**
```python
class RemoveIFObjectID(RegexRule):
    pattern = r'if\s+object_id\([^)]+\)\s+is\s+not\s+null\s+begin\s+drop\s+table[^;]+;?\s+end;?'
    replacement = ''
    priority = 25  # After temp table replacement
```

---

### Rule 3: Remove DROP TABLE Statements

**Before:**
```sql
DROP TABLE #temp
DROP TABLE IF EXISTS #staging
```

**After:**
```sql
-- Removed (not lineage-relevant)
```

**Why:** DROP doesn't show data flow, only cleanup

**Implementation:**
```python
class RemoveDropTable(RegexRule):
    pattern = r'drop\s+table\s+(?:if\s+exists\s+)?[#\w\.\[\]]+;?'
    replacement = ''
    priority = 26  # After IF EXISTS removal
```

---

### Rule 4: Flatten Simple BEGIN/END Blocks (Non-Control-Flow)

**Before:**
```sql
BEGIN
    INSERT INTO Table1 SELECT * FROM Table2
END

BEGIN
    UPDATE Table3 SET X = 1
END
```

**After:**
```sql
INSERT INTO Table1 SELECT * FROM Table2

UPDATE Table3 SET X = 1
```

**Why:** Standalone BEGIN/END adds nesting without value

**Implementation:**
```python
class FlattenSimpleBEGIN(RegexRule):
    # Only flatten BEGIN/END that don't follow IF/WHILE/TRY
    pattern = r'(?<!IF|WHILE|TRY)\s+BEGIN\s+(INSERT|UPDATE|DELETE|SELECT|WITH)[^;]+;?\s+END'
    replacement = r'\1...'  # Keep DML, remove BEGIN/END
    priority = 35  # After control flow handling
```

---

### Rule 5: Extract DML from IF Blocks (Simple Cases)

**Before:**
```sql
IF @condition = 1
BEGIN
    INSERT INTO Target SELECT * FROM Source
END
```

**After:**
```sql
INSERT INTO Target SELECT * FROM Source
```

**Why:** We want lineage even if condition not met at runtime

**Implementation:**
```python
class ExtractIFBlockDML(RegexRule):
    pattern = r'IF\s+[^B]+BEGIN\s+(INSERT|UPDATE|DELETE|MERGE)\s+([^;]+);?\s+END'
    replacement = r'\1 \2'  # Keep DML, remove IF wrapper
    priority = 40
```

---

## Summary: 5 Simple, Smart Rules

| Rule | Priority | What It Does | Impact |
|------|----------|--------------|--------|
| **ReplaceTempTables** | 15 | `#table` → `dummy.table` | ✅ Makes temp tables parseable |
| **RemoveIFObjectID** | 25 | Remove admin IF EXISTS checks | ✅ Removes noise |
| **RemoveDropTable** | 26 | Remove all DROP TABLE | ✅ Not lineage-relevant |
| **FlattenSimpleBEGIN** | 35 | Remove standalone BEGIN/END | ✅ Reduces nesting |
| **ExtractIFBlockDML** | 40 | Pull DML from IF branches | ✅ Captures conditional logic |

**Expected Impact:** 80.8% → ~90-93% (+10-12% improvement)

**Why This Approach is Better:**
- ✅ **Simple** - Each rule does ONE thing
- ✅ **Smart** - Temp table replacement is genius (valid SQL!)
- ✅ **Composable** - Rules work together naturally
- ✅ **Testable** - Each rule has clear before/after
- ✅ **No over-engineering** - Focuses on real problems

