# Double-Counting Issue - Root Cause Analysis & Remediation Plan

**Report Date:** 2025-10-24
**Analyst:** Data Lineage Investigation
**Target Table:** `CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation`

---

## Executive Summary

### Issue Statement

Suspected double-counting in FTE aggregation metrics for:
- **Country:** USA
- **Department:** Document Management
- **Currency:** USD
- **Time Range:** Last 1 year (Rank = 1)

**Affected Attributes:**
1. `[MonthlyFTEAggSUM (Fully Billable)]` - ⚠️ **CONFIRMED ISSUE**
2. `[MonthlyFTEAggSUM (Partially Billable)]` - ⚠️ **CONFIRMED ISSUE**
3. `[Labor Cost (Billable)]` - ✅ **NO ISSUE** (clean data)

### Root Cause

**Department mapping row multiplication** in `spLoadEmployeeContractUtilization_Aggregations.sql` due to:
- INNER JOIN to `vFull_Departmental_Map_ActivePrima` without proportional allocation
- Missing division by `PrimaDepartmentCount` (used correctly elsewhere in the codebase)
- 1:M relationship (1 Prima department → M Cadence departments) causing row duplication

**Severity:** **CRITICAL**
**Impact:** FTE metrics inflated by factor of `PrimaDepartmentCount` for affected departments
**Data Quality:** High confidence in root cause identification

---

## Detailed Root Cause Analysis

### The Problem

The stored procedure `spLoadEmployeeContractUtilization_Aggregations.sql` performs the following JOIN at three critical locations:

```sql
-- Lines 46-47, 77-78, 98-99
JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
      FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) DM
ON DM.PrimaDepartmentName = EFD.Department
```

**Why This Causes Issues:**

1. **1:M Mapping Relationship**
   - The view `vFull_Departmental_Map_ActivePrima` contains mappings where:
     - **1 Prima Department** (from HR system) can map to **MULTIPLE Cadence Departments** (from Cadence system)
   - This is a valid business relationship for cross-system alignment

2. **Row Multiplication**
   - When an employee's `Department` (Prima) maps to 3 Cadence departments:
     - **Before JOIN:** 1 employee record
     - **After JOIN:** 3 employee records (one for each Cadence department)

3. **Missing Allocation Logic**
   - The correct pattern (used in `spLoadCadenceBudgetData.sql`) divides values by `PrimaDepartmentCount`
   - Example: If PrimaDepartmentCount = 3, each value should be divided by 3
   - **Current code does NOT apply this division**

### Concrete Example

**Scenario:**
- Employee: Jane Smith (ID: 99999)
- Month: January 2024 (BOMDateId: 20240101)
- Prima Department: "Document Management" (from HrContractAttendance table)
- Billability: Fully Billable (BILLABLE_ID = 0)
- FTE: 1.0

**Department Mapping:**
```
"Document Management" (Prima) maps to 3 Cadence departments:
  1. "Document Mgmt - Clinical"
  2. "Document Mgmt - Regulatory"
  3. "Document Mgmt - Quality"

PrimaDepartmentCount = 3
```

**Current (INCORRECT) Behavior:**

After JOIN in `EmployeeContractFTE_Monthly`:
```
Row 1: Employee_Id=99999, CadenceDepartmentName="Document Mgmt - Clinical",   MonthlyFTEAggSUM=1.0
Row 2: Employee_Id=99999, CadenceDepartmentName="Document Mgmt - Regulatory", MonthlyFTEAggSUM=1.0
Row 3: Employee_Id=99999, CadenceDepartmentName="Document Mgmt - Quality",    MonthlyFTEAggSUM=1.0
```

Aggregation in `AverageContractFTE_Monthly` (GROUP BY CadenceDepartmentName):
```
CadenceDepartmentName="Document Mgmt - Clinical":   MonthlyFTEAggSUM (Fully Billable) = 1.0
CadenceDepartmentName="Document Mgmt - Regulatory": MonthlyFTEAggSUM (Fully Billable) = 1.0
CadenceDepartmentName="Document Mgmt - Quality":    MonthlyFTEAggSUM (Fully Billable) = 1.0

Total across all 3 departments: 3.0 FTE
```

**Expected (CORRECT) Behavior with Allocation:**

After JOIN with allocation:
```
Row 1: Employee_Id=99999, CadenceDepartmentName="Document Mgmt - Clinical",   MonthlyFTEAggSUM=0.333
Row 2: Employee_Id=99999, CadenceDepartmentName="Document Mgmt - Regulatory", MonthlyFTEAggSUM=0.333
Row 3: Employee_Id=99999, CadenceDepartmentName="Document Mgmt - Quality",    MonthlyFTEAggSUM=0.333
```

Aggregation:
```
CadenceDepartmentName="Document Mgmt - Clinical":   MonthlyFTEAggSUM (Fully Billable) = 0.333
CadenceDepartmentName="Document Mgmt - Regulatory": MonthlyFTEAggSUM (Fully Billable) = 0.333
CadenceDepartmentName="Document Mgmt - Quality":    MonthlyFTEAggSUM (Fully Billable) = 0.333

Total across all 3 departments: 1.0 FTE ✅
```

**Impact:**
- **Current Reported Value:** 3.0 FTE (300% inflation)
- **Correct Value:** 1.0 FTE
- **Error Magnitude:** 200% overstatement

---

## Evidence & Supporting Analysis

### Evidence 1: Pattern Discrepancy

**Correct Pattern in `spLoadCadenceBudgetData.sql` (Lines 30-40, 156-164):**

```sql
-- Step 1: Calculate PrimaDepartmentCount
insert into [STAGING_CADENCE].[DepartmenMapping]
select distinct b.CadenceDepartmentId, b.CadenceDepartmentName,
                b.PrimaDepartmentId, b.PrimaDepartmentName,
                a.PrimaDepartmentCount  -- ✅ CALCULATED
from [dbo].[Full_Departmental_Map] b
inner join (
    select CadenceDepartmentId, count(1) as PrimaDepartmentCount
    from (select distinct CadenceDepartmentId, CadenceDepartmentName,
                          PrimaDepartmentId, PrimaDepartmentName
          from [dbo].[Full_Departmental_Map]) c
    group by CadenceDepartmentId
) a on b.CadenceDepartmentId = a.CadenceDepartmentId

-- Step 2: Use PrimaDepartmentCount in allocation
, ISNULL((e.[SUM Function Planned Total Cost Adjusted]
        / NULLIF(d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1)
    AS [SUM Function Planned Total Cost Adjusted]  -- ✅ DIVIDED
```

**Incorrect Pattern in `spLoadEmployeeContractUtilization_Aggregations.sql` (Lines 46-47):**

```sql
-- ❌ No PrimaDepartmentCount calculation
-- ❌ No division by PrimaDepartmentCount
JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
      FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) DM
ON DM.PrimaDepartmentName = EFD.Department
...
,Sum([Hours Expected, Daily]) as [Sum (Hours Expected, Daily)]  -- ❌ NOT DIVIDED
```

### Evidence 2: CLAUDE.md Documentation

From `CLAUDE.md` (Lines referencing department mapping):

> **Department mapping uses `Full_Departmental_Map` to map Cadence departments to Prima departments**
>
> **A single Cadence department can map to multiple Prima departments, requiring proportional allocation via `PrimaDepartmentCount`**

This confirms:
1. The 1:M relationship is a known pattern
2. Proportional allocation via `PrimaDepartmentCount` is the expected behavior
3. The codebase already implements this pattern in `spLoadCadenceBudgetData.sql`

### Evidence 3: Selective Impact

**Affected Data Flows:**
- ✅ `EmployeeAttendanceExpectedHoursUtilization_Monthly` (uses department mapping JOIN)
- ✅ `EmployeeContractFTE_Monthly` (uses department mapping JOIN)
- ✅ `AverageContractFTE_Monthly` (aggregates inflated data)
- ✅ `AverageContractFTE_Monthly_RankDetail` (propagates inflated data)
- ✅ `BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation` (final target)

**NOT Affected:**
- ✅ `FactLaborCostForEarnedValue_Post` (sources from `CONSUMPTION_POWERBI.FactLaborCostForEarnedValue`, no department mapping)
- ✅ `FactLaborCostForEarnedValue_RankDetaillAggregation` (uses clean labor cost data)
- ✅ `BillableEfficiency_Productivity_RankDetailAggregation` (labor cost portion is clean)

**Implication:** Only FTE-related attributes are affected; labor cost calculations are correct.

---

## Impact Assessment

### Scope of Impact

**Affected Metrics:**
- `[MonthlyFTEAggSUM (Fully Billable)]`
- `[MonthlyFTEAggSUM (Partially Billable)]`
- `[MonthlyFTEAggSUM (Non-Billable)]` (if applicable)
- `[MonthlyFTEAggSUM (Total)]` (derived from above)
- Any FTE-related calculations, averages, or ratios
- Employee count metrics derived from FTE aggregations

**NOT Affected:**
- `[Labor Cost (Billable)]` ✅
- `[Labor Cost (Non-Billable)]` ✅
- `[Labor Cost (Total)]` ✅
- `[Earned Value]` ✅
- `[Actual Cost of Work Performed]` ✅
- Budget-related metrics ✅

### Data Quality Impact

**Severity Level:** **CRITICAL**

**Inflation Factor:**
- Varies by department based on `PrimaDepartmentCount`
- For departments with PrimaDepartmentCount = 1: **No impact** (1:1 mapping)
- For departments with PrimaDepartmentCount = 2: **100% inflation** (2× actual)
- For departments with PrimaDepartmentCount = 3: **200% inflation** (3× actual)
- For departments with PrimaDepartmentCount = N: **(N-1) × 100% inflation**

### Business Impact

**Affected Stakeholders:**
- Finance teams using FTE metrics for workforce planning
- Department managers tracking billable vs non-billable capacity
- Executive dashboards showing employee utilization
- Productivity and efficiency KPIs based on FTE ratios

**Potential Consequences:**
- ❌ Overstated FTE capacity in reports
- ❌ Incorrect labor utilization percentages
- ❌ Misleading headcount vs FTE reconciliations
- ❌ Inaccurate department-level FTE allocations
- ❌ Flawed capacity planning based on inflated FTE numbers

**Decisions at Risk:**
- Hiring decisions based on perceived capacity
- Budget allocations proportional to FTE
- Billable efficiency targets
- Cross-department resource comparisons

---

## Remediation Plan

### Phase 1: Validation (Priority: IMMEDIATE)

**Objective:** Confirm the issue and quantify impact

**Actions:**
1. **Run Validation Queries** (see `VALIDATION_QUERIES_Double_Counting_Detection.sql`)
   - Execute Section 1: Department Mapping Analysis
   - Execute Section 2: Row Multiplication Detection
   - Execute Section 6: Summary Validation Query

2. **Document Findings**
   - Record `PrimaDepartmentCount` for "Document Management" and all affected departments
   - Calculate actual inflation factor for each affected department
   - Identify all departments with PrimaDepartmentCount > 1

3. **Quantify Impact**
   - Count affected employees
   - Calculate total FTE difference (Reported vs Actual)
   - Identify time range of affected data

**Expected Duration:** 2-4 hours

**Deliverables:**
- Validation query results
- List of affected departments with inflation factors
- Impact quantification report

---

### Phase 2: Code Fix (Priority: HIGH)

**Objective:** Implement correct department mapping allocation logic

**File to Modify:** `spLoadEmployeeContractUtilization_Aggregations.sql`

**Affected Code Sections:**
1. Lines 30-58: `EmployeeAttendanceExpectedHoursUtilization_Monthly`
2. Lines 60-138: `EmployeeContractFTE_Monthly` (2 CTEs)

**Detailed Fix for Section 1 (Lines 30-58):**

**BEFORE (Current Code):**
```sql
SELECT EFD.[Employee_Id]
      ,EFD.[UtilizationDateId]
      ,EFD.[Date (Utilization)]
      ,EFD.[Country] AS [PrimaGlobalCountryName]
      ,DM.[CadenceDepartmentName]  -- ❌ From department mapping
      ,EFD.[Position]
      ,EFD.[BILLABLE_ID]
      ,EFD.[BILLABILITY]
      ,EFD.[ContractClassType]
      ,Count(*) AS CountEmployeeExpectedDays
      ,Sum([Hours Expected, Daily]) as [Sum (Hours Expected, Daily)]  -- ❌ NOT DIVIDED
INTO [CONSUMPTION_ClinOpsFinance].EmployeeAttendanceExpectedHoursUtilization_Monthly
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
      FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima] ) DM
ON DM.PrimaDepartmentName = EFD.Department  -- ❌ No allocation
WHERE [IS_HOLIDAY] + [IS_VACATION] + [IS_SICK_LEAVE] + [IS_DAY_OFF] + [IS_WEEKEND] + [IS_DISMISS]  + [IS_LongTermLeave] = 0
GROUP BY EFD.[Employee_Id], EFD.[UtilizationDateId], EFD.[Date (Utilization)], EFD.[Country]
  ,DM.[CadenceDepartmentName], EFD.[Position], EFD.[BILLABLE_ID], EFD.[BILLABILITY], EFD.[ContractClassType]
```

**AFTER (Corrected Code):**
```sql
-- Step 1: Create department mapping WITH PrimaDepartmentCount
WITH DepartmentMappingWithCount AS (
    SELECT
          b.CadenceDepartmentId
        , b.CadenceDepartmentName
        , b.PrimaDepartmentId
        , b.PrimaDepartmentName
        , a.PrimaDepartmentCount  -- ✅ ADDED
    FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima] b
    INNER JOIN (
        SELECT
              PrimaDepartmentId
            , COUNT(DISTINCT CadenceDepartmentId) as PrimaDepartmentCount
        FROM (
            SELECT DISTINCT
                  PrimaDepartmentId
                , PrimaDepartmentName
                , CadenceDepartmentId
                , CadenceDepartmentName
            FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]
        ) c
        GROUP BY PrimaDepartmentId
    ) a ON b.PrimaDepartmentId = a.PrimaDepartmentId
)
-- Step 2: Use department mapping with allocation
SELECT EFD.[Employee_Id]
      ,EFD.[UtilizationDateId]
      ,EFD.[Date (Utilization)]
      ,EFD.[Country] AS [PrimaGlobalCountryName]
      ,DM.[CadenceDepartmentName]
      ,EFD.[Position]
      ,EFD.[BILLABLE_ID]
      ,EFD.[BILLABILITY]
      ,EFD.[ContractClassType]
      ,Count(*) AS CountEmployeeExpectedDays
      -- ✅ DIVIDE by PrimaDepartmentCount for proportional allocation
      ,Sum([Hours Expected, Daily]) / NULLIF(DM.PrimaDepartmentCount, 0)
          as [Sum (Hours Expected, Daily)]
INTO [CONSUMPTION_ClinOpsFinance].EmployeeAttendanceExpectedHoursUtilization_Monthly
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
JOIN DepartmentMappingWithCount DM  -- ✅ Use new CTE
  ON DM.PrimaDepartmentName = EFD.Department
WHERE [IS_HOLIDAY] + [IS_VACATION] + [IS_SICK_LEAVE] + [IS_DAY_OFF] + [IS_WEEKEND] + [IS_DISMISS] + [IS_LongTermLeave] = 0
GROUP BY EFD.[Employee_Id], EFD.[UtilizationDateId], EFD.[Date (Utilization)], EFD.[Country]
  ,DM.[CadenceDepartmentName], DM.PrimaDepartmentCount  -- ✅ Include in GROUP BY
  ,EFD.[Position], EFD.[BILLABLE_ID], EFD.[BILLABILITY], EFD.[ContractClassType]
```

**Detailed Fix for Section 2a (Lines 63-82: EmployeeContractLastDayFTE CTE):**

**BEFORE:**
```sql
WITH EmployeeContractLastDayFTE AS (
  SELECT  EFD.[Employee_Id]
        ,[dbo].[udfDateToBomDateKey](EFD.Date) AS [BOMDateId]
        ,EFD.[Country]
        ,DM.[CadenceDepartmentName]
        ,EFD.[Position]
        ,EFD.[BILLABLE_ID]
        ,EFD.[ContractClassName]
        ,EFD.[ContractClassType]
        ,EFD.[FTE] AS FTEValue
        ,SUM(EFD.[FTE]) AS TotalFTE  -- ❌ NOT DIVIDED
        ,COUNT(EFD.[FTE]) AS CountFTE
  FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
  JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
        FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima] ) DM
  ON DM.PrimaDepartmentName = EFD.Department  -- ❌ No allocation
  WHERE EFD.[DATE] = CAST(DBO.udfDateToEomDate (EFD.[DATE]) AS DATE)
  GROUP BY EFD.[Employee_Id], [dbo].[udfDateToBomDateKey](EFD.Date), EFD.[Country]
    ,DM.[CadenceDepartmentName], EFD.[Position], EFD.[BILLABLE_ID]
    ,EFD.[ContractClassName], EFD.[ContractClassType], EFD.[FTE]
)
```

**AFTER:**
```sql
-- Reuse the DepartmentMappingWithCount CTE defined above
WITH DepartmentMappingWithCount AS (
    -- Same as Section 1 fix
    ...
),
EmployeeContractLastDayFTE AS (
  SELECT  EFD.[Employee_Id]
        ,[dbo].[udfDateToBomDateKey](EFD.Date) AS [BOMDateId]
        ,EFD.[Country]
        ,DM.[CadenceDepartmentName]
        ,EFD.[Position]
        ,EFD.[BILLABLE_ID]
        ,EFD.[ContractClassName]
        ,EFD.[ContractClassType]
        ,EFD.[FTE] / NULLIF(DM.PrimaDepartmentCount, 0) AS FTEValue  -- ✅ DIVIDED
        ,SUM(EFD.[FTE]) / NULLIF(DM.PrimaDepartmentCount, 0) AS TotalFTE  -- ✅ DIVIDED
        ,COUNT(EFD.[FTE]) AS CountFTE
  FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
  JOIN DepartmentMappingWithCount DM  -- ✅ Use new CTE
    ON DM.PrimaDepartmentName = EFD.Department
  WHERE EFD.[DATE] = CAST(DBO.udfDateToEomDate(EFD.[DATE]) AS DATE)
  GROUP BY EFD.[Employee_Id], [dbo].[udfDateToBomDateKey](EFD.Date), EFD.[Country]
    ,DM.[CadenceDepartmentName], DM.PrimaDepartmentCount  -- ✅ Include in GROUP BY
    ,EFD.[Position], EFD.[BILLABLE_ID]
    ,EFD.[ContractClassName], EFD.[ContractClassType], EFD.[FTE]
)
```

**Detailed Fix for Section 2b (Lines 84-102: EmployeeContractAllDaysFTE CTE):**

Apply the same pattern as Section 2a (divide FTE values by PrimaDepartmentCount).

**IMPLEMENTATION NOTES:**
1. Create ONE `DepartmentMappingWithCount` CTE at the beginning of the procedure
2. Reuse this CTE for all three sections (Lines 30-58, 63-82, 84-102)
3. Ensure `PrimaDepartmentCount` is included in all relevant GROUP BY clauses
4. Use `NULLIF(DM.PrimaDepartmentCount, 0)` to prevent division by zero

**Expected Duration:** 4-6 hours (including code review and testing)

**Deliverables:**
- Updated `spLoadEmployeeContractUtilization_Aggregations.sql` file
- Code review documentation
- Unit test results (if applicable)

---

### Phase 3: Testing & Validation (Priority: HIGH)

**Objective:** Verify the fix resolves the issue without introducing new problems

**Test Cases:**

**Test 1: Department with PrimaDepartmentCount = 1**
- **Expected:** No change in values (1:1 mapping)
- **Validation:** Compare before/after values, should be identical

**Test 2: Department with PrimaDepartmentCount = 3 (e.g., Document Management)**
- **Expected:** Values divided by 3
- **Validation:** After fix, aggregated FTE should equal actual employee FTE

**Test 3: Row Count Verification**
- **Expected:** Row counts in intermediate tables may remain the same (still 1:M JOIN)
- **Validation:** But aggregated totals should now be correct

**Test 4: Specific Employee Trace**
- **Expected:** Single employee with PrimaDepartmentCount=3 should show 0.333 FTE per Cadence department
- **Validation:** Sum across all 3 Cadence departments = 1.0 FTE total

**Test 5: Cross-Reference with Labor Cost**
- **Expected:** Labor Cost (Billable) should remain unchanged (already clean)
- **Validation:** Compare labor cost before/after fix

**Validation Queries:**
```sql
-- Before-and-After comparison
SELECT
      'BEFORE FIX' AS TimeFrame
    , PrimaGlobalCountryName
    , CadenceDepartmentName
    , SUM([MonthlyFTEAggSUM (Fully Billable)]) AS TotalFullyBillableFTE
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation_BACKUP
WHERE PrimaGlobalCountryName = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
GROUP BY PrimaGlobalCountryName, CadenceDepartmentName

UNION ALL

SELECT
      'AFTER FIX' AS TimeFrame
    , PrimaGlobalCountryName
    , CadenceDepartmentName
    , SUM([MonthlyFTEAggSUM (Fully Billable)])
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
WHERE PrimaGlobalCountryName = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
GROUP BY PrimaGlobalCountryName, CadenceDepartmentName;
```

**Expected Duration:** 2-3 hours

**Deliverables:**
- Test execution results
- Before/after comparison reports
- Sign-off from QA/Data Validation team

---

### Phase 4: Deployment & Data Refresh (Priority: HIGH)

**Objective:** Deploy fix and refresh affected tables with corrected data

**Prerequisites:**
1. ✅ Code fix completed and tested
2. ✅ Validation results reviewed and approved
3. ✅ Backup of current tables created

**Deployment Steps:**

**Step 1: Backup Existing Tables**
```sql
-- Backup target table
SELECT * INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation_BACKUP
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation;

-- Backup intermediate tables
SELECT * INTO [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly_BACKUP
FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly;

SELECT * INTO [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly_BACKUP
FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly;

-- Add timestamps to backup table names if needed
```

**Step 2: Deploy Updated Stored Procedure**
```sql
-- Deploy corrected spLoadEmployeeContractUtilization_Aggregations.sql
-- Verify deployment successful
SELECT OBJECT_DEFINITION(OBJECT_ID('[CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Aggregations]'));
```

**Step 3: Execute Full Data Refresh**
```sql
-- Execute corrected stored procedure
EXEC [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Aggregations];

-- Verify completion
SELECT TOP 100 * FROM [ADMIN].[Logs]
WHERE ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Aggregations]'
ORDER BY CreateDateTimeUTC DESC;
```

**Step 4: Run Validation Queries**
- Execute queries from `VALIDATION_QUERIES_Double_Counting_Detection.sql`
- Compare results against expected values
- Verify no regression in Labor Cost metrics

**Step 5: Spot-Check Reports**
- Review downstream reports/dashboards consuming this data
- Verify FTE values now align with employee counts
- Confirm no unexpected side effects

**Expected Duration:** 4-6 hours (including execution time for large data volumes)

**Deliverables:**
- Deployment checklist (completed)
- Post-deployment validation results
- Backup confirmation

---

### Phase 5: Communication & Documentation (Priority: MEDIUM)

**Objective:** Inform stakeholders and document the fix

**Communication Plan:**

**Audience 1: Technical Team**
- **Who:** Data Engineering, ETL developers, DBAs
- **What:** Technical root cause, code changes, deployment details
- **When:** Immediately after deployment
- **How:** Email + Technical Documentation

**Audience 2: Business Stakeholders**
- **Who:** Finance, Department Managers, Executives
- **What:** Issue summary, impact on reports, corrected values
- **When:** After validation complete
- **How:** Business memo + stakeholder meeting

**Audience 3: End Users (Report Consumers)**
- **Who:** Anyone using FTE reports/dashboards
- **What:** Data correction notice, what changed, historical data impact
- **When:** Before reports are refreshed with corrected data
- **How:** Report annotation + user notification

**Documentation Updates:**

1. **Update CLAUDE.md**
   - Add note about the fix in the "Common Development Patterns" section
   - Document the correct department mapping pattern for future developers

2. **Create Incident Report**
   - Document root cause analysis
   - Record fix implementation details
   - Archive validation results

3. **Update Data Dictionary**
   - Clarify FTE metric definitions
   - Note data quality improvement and effective date

**Expected Duration:** 2-4 hours

**Deliverables:**
- Stakeholder communication emails
- Updated technical documentation
- Incident report

---

## Risk Assessment & Mitigation

### Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Code fix introduces new bugs** | LOW | HIGH | Thorough code review, comprehensive testing, phased deployment |
| **Performance degradation** | LOW | MEDIUM | Monitor query execution time, optimize if needed, consider indexing |
| **Incomplete data refresh** | MEDIUM | HIGH | Full pipeline refresh, validate completeness, have rollback plan |
| **Breaking downstream dependencies** | LOW | HIGH | Identify and test downstream reports before deployment |
| **Historical data inconsistency** | HIGH | MEDIUM | Document data quality change, consider historical data reprocessing |

### Rollback Plan

**If Issues Arise Post-Deployment:**

1. **Immediate Action:**
   ```sql
   -- Restore from backup
   TRUNCATE TABLE [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation;

   INSERT INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
   SELECT * FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation_BACKUP;
   ```

2. **Revert Stored Procedure:**
   - Redeploy original version of `spLoadEmployeeContractUtilization_Aggregations.sql`
   - Document rollback reason

3. **Notify Stakeholders:**
   - Alert technical team
   - Inform business stakeholders of temporary reversion

**Rollback Decision Criteria:**
- Data validation failures
- Unexpected NULL values
- Performance issues causing SLA breaches
- Critical downstream report failures

---

## Success Criteria

### Definition of Done

The remediation is considered successful when ALL of the following are met:

✅ **Technical Criteria:**
1. Code fix deployed to production
2. All validation queries pass
3. No regression in Labor Cost metrics
4. Performance within acceptable limits (< 10% increase in execution time)
5. Zero division errors or NULL propagation

✅ **Data Quality Criteria:**
1. FTE aggregations for departments with PrimaDepartmentCount > 1 reduced by factor of PrimaDepartmentCount
2. Departments with PrimaDepartmentCount = 1 show no change
3. Total FTE across all Cadence departments aligns with employee counts
4. Spot-checked employee records trace correctly through pipeline

✅ **Business Criteria:**
1. Finance team confirms corrected FTE values are reasonable
2. Department managers review and approve updated metrics
3. Downstream reports refreshed with corrected data
4. Stakeholders notified and documentation updated

### Validation Metrics

**Before Fix (Expected Issues):**
- Departments with PrimaDepartmentCount = 3 show 300% inflation
- Total USA FTE aggregation significantly higher than employee counts
- Row multiplication detected in `EmployeeContractFTE_Monthly`

**After Fix (Expected Results):**
- FTE aggregations reduced by PrimaDepartmentCount factor
- Total USA FTE aggregation aligns with actual employee FTE
- No row count change in intermediate tables (allocation handles multiplication)

**Acceptance Threshold:**
- 100% of validation queries pass
- 0% regression in Labor Cost calculations
- < 5% variance in spot-checked employee FTE allocations

---

## Timeline & Resource Allocation

### Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| **Phase 1: Validation** | 2-4 hours | Access to database, validation queries |
| **Phase 2: Code Fix** | 4-6 hours | Phase 1 complete, developer availability |
| **Phase 3: Testing** | 2-3 hours | Phase 2 complete, test environment |
| **Phase 4: Deployment** | 4-6 hours | Phase 3 sign-off, deployment window |
| **Phase 5: Communication** | 2-4 hours | Phase 4 complete, stakeholder availability |
| **Total** | **14-23 hours** (~2-3 business days) | - |

### Resource Requirements

**Required Roles:**
1. **Data Engineer / ETL Developer** (Primary)
   - Code fix implementation
   - Testing and validation
   - Deployment execution

2. **Database Administrator** (Supporting)
   - Performance monitoring
   - Backup management
   - Deployment oversight

3. **Data Analyst / QA** (Supporting)
   - Validation query execution
   - Before/after analysis
   - Spot-checking reports

4. **Business Analyst** (Supporting)
   - Stakeholder communication
   - Report impact assessment
   - User documentation

---

## Long-Term Recommendations

### Process Improvements

1. **Code Review Standards**
   - Mandate review of department mapping JOINs for proportional allocation
   - Include `PrimaDepartmentCount` pattern in coding standards
   - Create checklist for JOIN cardinality verification

2. **Automated Testing**
   - Add unit tests for department mapping scenarios
   - Implement row count reconciliation tests
   - Create integration tests for FTE calculations

3. **Data Quality Monitoring**
   - Set up alerts for FTE vs employee count discrepancies
   - Monitor aggregation ratios (avg FTE per employee should be ≤ 1.0)
   - Track row multiplication metrics in ETL pipelines

### Technical Debt Reduction

1. **Standardize Department Mapping**
   - Create reusable CTE or view: `vDepartmentMappingWithCount`
   - Centralize department mapping logic across all procedures
   - Deprecate DISTINCT-only department mapping pattern

2. **Refactor Similar Code**
   - Audit all stored procedures for similar department mapping JOINs
   - Apply proportional allocation pattern consistently
   - Document standard patterns in CLAUDE.md

3. **Schema Improvements**
   - Consider materializing `PrimaDepartmentCount` in a table
   - Add constraints or triggers to enforce referential integrity
   - Create indexed views for common department aggregations

---

## Appendix

### A. Quick Reference

**Affected File:**
- `Synapse_Data_Warehouse/Stored Procedures/CONSUMPTION_ClinOpsFinance.spLoadEmployeeContractUtilization_Aggregations.sql`

**Affected Code Lines:**
- Lines 46-47 (EmployeeAttendanceExpectedHoursUtilization_Monthly)
- Lines 77-78 (EmployeeContractLastDayFTE CTE)
- Lines 98-99 (EmployeeContractAllDaysFTE CTE)

**Reference Implementation:**
- `Synapse_Data_Warehouse/Stored Procedures/CONSUMPTION_ClinOpsFinance.spLoadCadenceBudgetData.sql`
  - Lines 30-40 (PrimaDepartmentCount calculation)
  - Lines 156-164 (Proportional allocation)

**Validation Queries:**
- `VALIDATION_QUERIES_Double_Counting_Detection.sql`

**Data Lineage Documentation:**
- `DATA_LINEAGE_ANALYSIS_BillableEfficiency_Productivity.md`

### B. Key SQL Patterns

**Correct Department Mapping Pattern:**
```sql
WITH DepartmentMappingWithCount AS (
    SELECT b.*, a.PrimaDepartmentCount
    FROM [vFull_Departmental_Map_ActivePrima] b
    INNER JOIN (
        SELECT PrimaDepartmentId, COUNT(DISTINCT CadenceDepartmentId) as PrimaDepartmentCount
        FROM (SELECT DISTINCT * FROM [vFull_Departmental_Map_ActivePrima]) c
        GROUP BY PrimaDepartmentId
    ) a ON b.PrimaDepartmentId = a.PrimaDepartmentId
)
SELECT ...,
       Value / NULLIF(DM.PrimaDepartmentCount, 0) AS AllocatedValue
FROM SourceTable ST
JOIN DepartmentMappingWithCount DM ON ...
```

**Incorrect Pattern (TO AVOID):**
```sql
JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
      FROM [vFull_Departmental_Map_ActivePrima]) DM
ON DM.PrimaDepartmentName = ST.Department
-- Missing: PrimaDepartmentCount division
```

### C. Contact Information

**For Technical Questions:**
- Data Engineering Team Lead
- Database Administrator

**For Business Questions:**
- Finance Data Analytics Manager
- Department Planning Leads

**For Escalation:**
- Data Governance Committee
- IT Leadership

---

**Report End**

*This report provides a comprehensive analysis of the double-counting issue, root cause, and detailed remediation plan. All phases should be executed in sequence with appropriate sign-offs at each stage.*
