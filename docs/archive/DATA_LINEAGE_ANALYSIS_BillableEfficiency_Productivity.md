# Data Lineage Analysis: BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation

**Analysis Date:** 2025-10-24
**Target Table:** `CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation`
**Issue:** Suspected double-counting for USA/Document Management/USD/Last 1 year

## Target Attributes Under Investigation

1. **[Labor Cost (Billable)]**
2. **[MonthlyFTEAggSUM (Fully Billable)]**
3. **[MonthlyFTEAggSUM (Partially Billable)]**

---

## Executive Summary

### Key Findings

**CRITICAL ISSUE IDENTIFIED:** Row multiplication due to department mapping JOINs without proper allocation.

The `vFull_Departmental_Map_ActivePrima` view enables **1:M** relationships (1 Prima department → M Cadence departments), but the aggregation procedure in `spLoadEmployeeContractUtilization_Aggregations` performs JOINs using `DISTINCT` on this mapping **WITHOUT** applying the `PrimaDepartmentCount` divisor used elsewhere in the codebase.

**Expected Behavior:** When a Cadence department maps to multiple Prima departments, values should be divided by `PrimaDepartmentCount`.

**Actual Behavior:** Values are duplicated across all mapped Prima departments, causing inflated aggregations.

### Impact Zones

1. **MonthlyFTEAggSUM (Fully Billable)** - Lines 143-162, 209
2. **MonthlyFTEAggSUM (Partially Billable)** - Lines 163-181, 213
3. **Labor Cost (Billable)** - Upstream from FactLaborCostForEarnedValue (no direct impact from this JOIN)

---

## Complete Data Lineage Map

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 0: Source Tables                                              │
├─────────────────────────────────────────────────────────────────────┤
│ • CONSUMPTION_ClinOpsFinance.HrContractAttendance                   │
│ • CONSUMPTION_ClinOpsFinance.vFull_Departmental_Map_ActivePrima  ⚠️ │
│ • CONSUMPTION_ClinOpsFinance.DateRanges_PM                          │
│ • CONSUMPTION_ClinOpsFinance.CURRENCY                               │
│ • CONSUMPTION_POWERBI.FactLaborCostForEarnedValue                   │
│ • CONSUMPTION_ClinOpsFinance.CadenceBudgetData_Post                 │
│ • CONSUMPTION_PRIMA.MonthlyAverageCurrencyExchangeRate              │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 1: spLoadEmployeeContractUtilization_Aggregations         ⚠️ │
│ (File: spLoadEmployeeContractUtilization_Aggregations.sql)         │
├─────────────────────────────────────────────────────────────────────┤
│ Creates:                                                            │
│ 1. EmployeeAttendanceExpectedHoursUtilization_Monthly (L30-58)     │
│ 2. EmployeeContractFTE_Monthly (L60-138)                           │
│ 3. AverageContractFTE_Monthly (L140-251)                           │
│ 4. AverageContractFTE_Monthly_RankDetail (L253-290)                │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 2: spLoadFactLaborCostForEarnedValue_Post                    │
│ (File: spLoadFactLaborCostForEarnedValue_Post.sql)                 │
├─────────────────────────────────────────────────────────────────────┤
│ Creates:                                                            │
│ • FactLaborCostForEarnedValue_Post (L76-200)                       │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 3: spLoadCadenceBudget_Aggregations                          │
│ (File: spLoadCadenceBudget_Aggregations.sql)                       │
├─────────────────────────────────────────────────────────────────────┤
│ Creates:                                                            │
│ • CadenceBudgetData_BillableEfficiency (L104-138)                  │
│ • CadenceBudgetData_BillableEfficiency_RankDetail (L223-262)       │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 4: spLoadFactLaborCostForEarnedValue_Aggregations            │
│ (File: spLoadFactLaborCostForEarnedValue_Aggregations.sql)         │
├─────────────────────────────────────────────────────────────────────┤
│ Creates:                                                            │
│ • FactLaborCostForEarnedValue_RankDetaillAggregation (L129-165)    │
│ • BillableEfficiency_Productivity_RankDetailAggregation (L167-233) │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 5: FINAL TARGET (spLoadEmployeeContractUtilization_Agg)      │
│ (File: spLoadEmployeeContractUtilization_Aggregations.sql)         │
├─────────────────────────────────────────────────────────────────────┤
│ • BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetail    │
│   Aggregation (L292-340)                                           │
│                                                                     │
│ FULL OUTER JOIN:                                                   │
│   BillableEfficiency_Productivity_RankDetailAggregation            │
│   ⋈ AverageFTE_Monthly_RankDetail_Currency                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Lineage Analysis by Layer

---

## LAYER 0: Source Tables

### 0.1 HrContractAttendance
**Purpose:** Employee contract and attendance data
**Grain:** Employee × Date × Department
**Key Columns:**
- `Employee_Id`, `Date`, `Department`, `Country`, `Position`
- `BILLABLE_ID`, `BILLABILITY`, `ContractClassType`
- `FTE`, `Hours Expected, Daily`

**Relevance:** Source for FTE calculations and attendance tracking.

---

### 0.2 vFull_Departmental_Map_ActivePrima ⚠️ CRITICAL

**File:** `vFull_Departmental_Map_ActivePrima.sql`

```sql
CREATE VIEW [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]
AS
SELECT FDM.*
FROM DBO.Full_Departmental_Map FDM
LEFT JOIN CONSUMPTION_PRIMA.HrDepartments HrD
ON FDM.PrimaDepartmentID = Hrd.Department_ID
WHERE HrD.Record_Active = 1
UNION
SELECT * FROM DBO.Full_Departmental_Map
WHERE PrimaDepartmentName = 'Marketing & Events Management';
```

**Purpose:** Maps Cadence departments to Prima departments
**Grain:** CadenceDepartmentId × PrimaDepartmentId
**Key Columns:**
- `CadenceDepartmentId`, `CadenceDepartmentName`
- `PrimaDepartmentId`, `PrimaDepartmentName`

**CRITICAL BEHAVIOR:**
- **1:M Relationship:** One Cadence department can map to MULTIPLE Prima departments
- **Requires Allocation:** Per CLAUDE.md, should use `PrimaDepartmentCount` for proportional allocation
- **Current Issue:** JOINs use this view with DISTINCT but WITHOUT division by `PrimaDepartmentCount`

**Example Multiplicity:**
```
CadenceDepartmentId: 123, CadenceDepartmentName: "Document Management"
→ Maps to 3 Prima departments:
  - PrimaDepartmentId: 456, PrimaDepartmentName: "Doc Mgmt A"
  - PrimaDepartmentId: 457, PrimaDepartmentName: "Doc Mgmt B"
  - PrimaDepartmentId: 458, PrimaDepartmentName: "Doc Mgmt C"

PrimaDepartmentCount = 3
```

---

### 0.3 DateRanges_PM
**Purpose:** Date dimension with rank-based date ranges
**Grain:** DateID × Rank
**Key Columns:**
- `DateID`, `Date`, `Rank`, `RangeLabel`

**Ranks:**
- `Rank = 1`: Last 1 year (suspected issue scope)
- `Rank = 2`: Last 2 years
- etc.

---

### 0.4 CURRENCY
**Purpose:** Currency dimension for cross joins
**Grain:** Currency
**Key Columns:**
- `Currency` (CHF, GBP, USD, EUR)

---

## LAYER 1: spLoadEmployeeContractUtilization_Aggregations ⚠️

**File:** `spLoadEmployeeContractUtilization_Aggregations.sql`

---

### 1.1 EmployeeAttendanceExpectedHoursUtilization_Monthly

**Lines:** 30-58
**Pattern:** Truncate-and-load into temp table

**Business Logic:**
```sql
SELECT EFD.[Employee_Id], EFD.[UtilizationDateId], EFD.[Date (Utilization)]
      ,EFD.[Country] AS [PrimaGlobalCountryName]
      ,DM.[CadenceDepartmentName]  -- ⚠️ From department mapping
      ,EFD.[Position], EFD.[BILLABLE_ID], EFD.[BILLABILITY], EFD.[ContractClassType]
      ,Count(*) AS CountEmployeeExpectedDays
      ,Sum([Hours Expected, Daily]) as [Sum (Hours Expected, Daily)]
INTO [CONSUMPTION_ClinOpsFinance].EmployeeAttendanceExpectedHoursUtilization_Monthly
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
      FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) DM
ON DM.PrimaDepartmentName = EFD.Department  -- ⚠️ MULTIPLICATION POINT
WHERE [IS_HOLIDAY] + [IS_VACATION] + ... = 0
GROUP BY EFD.[Employee_Id], EFD.[UtilizationDateId], ... DM.[CadenceDepartmentName]
```

**⚠️ DOUBLE-COUNTING RISK:**
- **JOIN Type:** INNER JOIN on department mapping
- **Cardinality:** 1:M (1 Prima department → M Cadence departments)
- **Effect:** If "Document Management" Prima department maps to 3 Cadence departments, each employee record is **DUPLICATED 3 TIMES**
- **Missing Logic:** No division by `PrimaDepartmentCount`

**Target Attribute Impact:**
- Does NOT directly calculate target attributes but creates inflated base data

---

### 1.2 EmployeeContractFTE_Monthly ⚠️

**Lines:** 60-138
**Pattern:** CTEs + SELECT INTO

**Business Logic:**

```sql
WITH EmployeeContractLastDayFTE AS (
  SELECT EFD.[Employee_Id], [dbo].[udfDateToBomDateKey](EFD.Date) AS [BOMDateId]
      ,EFD.[Country], DM.[CadenceDepartmentName]  -- ⚠️ From mapping
      ,EFD.[Position], EFD.[BILLABLE_ID], EFD.[ContractClassName], EFD.[ContractClassType]
      ,EFD.[FTE] AS FTEValue
      ,SUM(EFD.[FTE]) AS TotalFTE
      ,COUNT(EFD.[FTE]) AS CountFTE
  FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
  JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
        FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) DM
  ON DM.PrimaDepartmentName = EFD.Department  -- ⚠️ MULTIPLICATION POINT
  WHERE EFD.[DATE] = CAST(DBO.udfDateToEomDate(EFD.[DATE]) AS DATE)
  GROUP BY EFD.[Employee_Id], [BOMDateId], EFD.[Country], DM.[CadenceDepartmentName], ...
),
EmployeeContractAllDaysFTE AS (
  -- Similar pattern, aggregates ALL days in month
  ...
)
SELECT EAFD.[Employee_Id], EAFD.[BOMDateId], EAFD.[Country] AS [PrimaGlobalCountryName]
      ,EAFD.[CadenceDepartmentName], EAFD.[Position], EAFD.[BILLABLE_ID]
      ,EAFD.[ContractClassName], EAFD.[ContractClassType]
      ,EAFD.FTEValue
      ,EAFD.TotalFTE As MonthlyFTEAggSUM  -- ⚠️ TARGET ATTRIBUTE
      ,EAFD.CountFTE As MonthlyFTEAggCount
      ,EAFD.TotalFTE / CASE WHEN EAFD.CountFTE = 0 THEN NULL ELSE EAFD.CountFTE END
          AS [Monthly Average FTE]
      ,ELFD.TotalFTE As LastDayDailyFTEAggSUM
      ,ELFD.CountFTE As LastDayFTEAggCount
      ,ELFD.TotalFTE / CASE WHEN ELFD.CountFTE = 0 THEN NULL ELSE ELFD.CountFTE END
          AS [Monthly Average FTE, Last Day]
INTO [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
FROM EmployeeContractAllDaysFTE EAFD
LEFT JOIN EmployeeContractLastDayFTE ELFD ON ...
```

**⚠️ DOUBLE-COUNTING MECHANISM:**

**Example Scenario:**
- Employee: John Doe (ID: 12345)
- Month: 2024-01
- Prima Department: "Document Management" (from HrContractAttendance)
- This Prima department maps to 3 Cadence departments:
  1. "Doc Mgmt A"
  2. "Doc Mgmt B"
  3. "Doc Mgmt C"

**Without PrimaDepartmentCount Division:**
```
Result rows in EmployeeContractFTE_Monthly:
1. Employee_Id: 12345, CadenceDepartmentName: "Doc Mgmt A", MonthlyFTEAggSUM: 1.0
2. Employee_Id: 12345, CadenceDepartmentName: "Doc Mgmt B", MonthlyFTEAggSUM: 1.0
3. Employee_Id: 12345, CadenceDepartmentName: "Doc Mgmt C", MonthlyFTEAggSUM: 1.0
```

**With Proper Allocation (Expected):**
```
Result rows:
1. Employee_Id: 12345, CadenceDepartmentName: "Doc Mgmt A", MonthlyFTEAggSUM: 0.333
2. Employee_Id: 12345, CadenceDepartmentName: "Doc Mgmt B", MonthlyFTEAggSUM: 0.333
3. Employee_Id: 12345, CadenceDepartmentName: "Doc Mgmt C", MonthlyFTEAggSUM: 0.333
```

**Target Attribute Impact:**
- **MonthlyFTEAggSUM:** INFLATED by factor of `PrimaDepartmentCount`

---

### 1.3 AverageContractFTE_Monthly

**Lines:** 140-251
**Pattern:** CTEs with FULL OUTER JOINs

**Business Logic:**

```sql
With FullBillable AS (
  SELECT [BOMDateID], [PrimaGlobalCountryName], [CadenceDepartmentName], [ContractClassType]
        ,COUNT(*) AS EmployeeCount
        ,SUM(MonthlyFTEAggCount) As MonthlyFTEAggCount
        ,SUM(MonthlyFTEAggSUM) As MonthlyFTEAggSUM  -- ⚠️ TARGET ATTRIBUTE
        ,SUM(LastDayFTEAggCount) As MonthlyLastDayFTEAggCount
        ,SUM(LastDayDailyFTEAggSUM) As MonthlyLastDayDailyFTEAggSUM
  FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
  WHERE [BILLABLE_ID] IN (0)  -- Fully Billable
  GROUP BY [BOMDateID], [PrimaGlobalCountryName], [CadenceDepartmentName], [ContractClassType]
),
PartialBillable AS (
  -- Same pattern for BILLABLE_ID = 1
),
NonBillable AS (
  -- Same pattern for BILLABLE_ID = 2
),
AllBillable AS (
  SELECT COALESCE(B.[BOMDateID], N.[BOMDateID]) AS [BOMDateID]
        ,COALESCE(B.[PrimaGlobalCountryName], N.[PrimaGlobalCountryName]) AS [PrimaGlobalCountryName]
        ,COALESCE(B.[CadenceDepartmentName], N.[CadenceDepartmentName]) AS [CadenceDepartmentName]
        ,COALESCE(B.[ContractClassType], N.[ContractClassType]) AS [ContractClassType]
        ,B.EmployeeCount AS [FTE EmployeeCount (Fully Billable)]
        ,B.MonthlyFTEAggCount AS [MonthlyFTEAggCount (Fully Billable)]
        ,B.MonthlyFTEAggSUM AS [MonthlyFTEAggSUM (Fully Billable)]  -- ⚠️
        ,B.MonthlyLastDayFTEAggCount AS [MonthlyLastDayFTEAggCount (Fully Billable)]
        ,B.MonthlyLastDayDailyFTEAggSUM AS [MonthlyLastDayDailyFTEAggSUM (Fully Billable)]
        ,N.EmployeeCount AS [FTE EmployeeCount (Partially Billable)]
        ,N.MonthlyFTEAggCount AS [MonthlyFTEAggCount (Partially Billable)]
        ,N.MonthlyFTEAggSUM AS [MonthlyFTEAggSUM (Partially Billable)]  -- ⚠️
        ,N.MonthlyLastDayFTEAggCount AS [MonthlyLastDayFTEAggCount (Partially Billable)]
        ,N.MonthlyLastDayDailyFTEAggSUM AS [MonthlyLastDayDailyFTEAggSUM (Partially Billable)]
  FROM FullBillable B
  FULL OUTER JOIN PartialBillable N ON ...
)
SELECT COALESCE(B.[BOMDateID], N.[BOMDateID]) AS [BOMDateID], ...
      ,B.[MonthlyFTEAggSUM (Fully Billable)]  -- ⚠️ Carries inflated values
      ,B.[MonthlyFTEAggSUM (Partially Billable)]  -- ⚠️ Carries inflated values
      ,N.[MonthlyFTEAggSUM (Non-Billable)]
INTO [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly
FROM AllBillable B
FULL OUTER JOIN NonBillable N ON ...
```

**Aggregation Logic:**
- **SUM(MonthlyFTEAggSUM):** Aggregates the already-inflated values from `EmployeeContractFTE_Monthly`
- **GROUP BY:** `[BOMDateID], [PrimaGlobalCountryName], [CadenceDepartmentName], [ContractClassType]`

**Target Attribute Impact:**
- **MonthlyFTEAggSUM (Fully Billable):** Propagates inflation from Layer 1.2
- **MonthlyFTEAggSUM (Partially Billable):** Propagates inflation from Layer 1.2

**JOIN Risk:**
- FULL OUTER JOINs between Billable types: **No multiplication** (proper use)

---

### 1.4 AverageContractFTE_Monthly_RankDetail

**Lines:** 253-290
**Pattern:** SELECT INTO with JOIN to DateRanges_PM

```sql
SELECT [Rank], [BOMDateID], dbo.udfDateKeyToDate([BOMDateID]) AS [BOMDate]
      ,[PrimaGlobalCountryName], [CadenceDepartmentName], [ContractClassType]
      ,[MonthlyFTEAggSUM (Fully Billable)]  -- ⚠️ Inflated
      ,[MonthlyFTEAggSUM (Partially Billable)]  -- ⚠️ Inflated
      ,[MonthlyFTEAggSUM (Non-Billable)]
      ,ISNULL([MonthlyFTEAggSUM (Fully Billable)], 0.0)
        + ISNULL([MonthlyFTEAggSUM (Partially Billable)], 0.0)
        + ISNULL([MonthlyFTEAggSUM (Non-Billable)], 0.0)
       AS [MonthlyFTEAggSUM (Total)]
INTO [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly_RankDetail
FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly AF
JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
  ON AF.[BOMDateID] = DR.DateID
```

**JOIN Analysis:**
- **JOIN Type:** INNER JOIN
- **Cardinality:** M:1 (Multiple BOMDateIDs can match 1 Rank)
- **Risk:** **NO MULTIPLICATION** - One BOMDateID maps to exactly one Rank record
- **Purpose:** Adds Rank dimension for date range filtering

**Target Attribute Impact:**
- **MonthlyFTEAggSUM (Fully Billable):** Carries forward inflated values
- **MonthlyFTEAggSUM (Partially Billable):** Carries forward inflated values

---

## LAYER 2: spLoadFactLaborCostForEarnedValue_Post

**File:** `spLoadFactLaborCostForEarnedValue_Post.sql`
**Lines:** 76-200

**Business Logic:**

```sql
SELECT
       ju.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
      ,lc.[Account], lc.[AccountName], lc.[SubAccountName]
      ,lc.[PrimaGlobalCountryName], lc.[PrimaDepartmentName], lc.[CadenceDepartmentName]
      ,lc.[BillableFlag], lc.[Vtyp], lc.[Currency]
      ,-1*[AmountYTD] as [AmountYTD]
      ,-1*[AmountPTD] as [AmountPTD]  -- ⚠️ Labor cost value
      ,[dbo].[udfDateToDateKey](DateFromParts(lc.[Year], lc.[Month], 1)) as [BomDateId]
FROM [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] lc
LEFT JOIN [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] ju
  ON lc.[PrimaGlobalCountryName] = ju.[PrimaGlobalCountryName]
 AND lc.[PrimaDepartmentName] = ju.[Department]
 AND lc.[Year] = ju.[Year]
 AND lc.[Month] = ju.[Month]
 AND lc.[Currency] = ju.[Currency]
 AND ju.[TableName] = 'FactLaborCostForEarnedValue'
WHERE DateFromParts(lc.[Year], lc.[Month], 1) <= ...

UNION ALL

-- Future months (forecasting logic)
...
```

**Source Table:** `CONSUMPTION_POWERBI.FactLaborCostForEarnedValue`

**JOIN Analysis:**
- **JOIN Type:** LEFT JOIN to junction table
- **Cardinality:** 1:1 (based on composite key)
- **Risk:** **NO MULTIPLICATION** (junction table should have unique keys per TableName)

**Target Attribute Impact:**
- **Labor Cost (Billable):** Sourced from `AmountPTD` field
- **Note:** This layer does NOT use `vFull_Departmental_Map_ActivePrima`, so **NO double-counting from department mapping**

---

## LAYER 3: spLoadCadenceBudget_Aggregations

**File:** `spLoadCadenceBudget_Aggregations.sql`

---

### 3.1 CadenceBudgetData_BillableEfficiency

**Lines:** 104-138

```sql
WITH BudgetJuncDates AS (
  SELECT [CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
        ,[PrimaGlobalCountryName], Department, Currency, BomDateID, [Rank]
  FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] J
  JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
    ON J.BomDateID = DR.DateID
  WHERE TableName = 'CadenceBudgetData'
)
SELECT B.[Project Name], B.[Function], B.[CadenceDepartmentName],
      B.[Function Country], B.PrimaGlobalCountryName, BJD.Currency, BJD.[Rank]
      ,SUM(B.[Earned Value (Total Allocated)]) AS [Earned Value]
      ,SUM(B.[Earned Value (Total Allocated) Version-2]) AS [Earned Value Version-2]
      ,SUM(B.[Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
INTO [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency]
FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post] B
JOIN BudgetJuncDates BJD
  ON BJD.BomDateID = B.BomDateID
 AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = B.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY B.[Project Name], B.[Function], B.[CadenceDepartmentName],
         B.[Function Country], B.PrimaGlobalCountryName, BJD.Currency, BJD.[Rank]
```

**JOIN Analysis:**
- **JOIN Type:** INNER JOIN to BudgetJuncDates CTE
- **Cardinality:** 1:1 (composite key match on JuncKey + BomDateID)
- **Risk:** **NO MULTIPLICATION**

**Target Attribute Impact:**
- Does NOT directly impact target attributes (budget data, not labor cost or FTE)

---

### 3.2 CadenceBudgetData_BillableEfficiency_RankDetail

**Lines:** 223-262
**Similar pattern to 3.1 but includes BomDateID in GROUP BY**

---

## LAYER 4: spLoadFactLaborCostForEarnedValue_Aggregations

**File:** `spLoadFactLaborCostForEarnedValue_Aggregations.sql`

---

### 4.1 FactLaborCostForEarnedValue_RankDetaillAggregation

**Lines:** 129-165

```sql
WITH BudgetJuncDates AS (
  SELECT [CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
        ,[PrimaGlobalCountryName], Department, Currency, BomDateID, [Rank]
  FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] J
  JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
    ON J.BomDateID = DR.DateID
  WHERE TableName = 'FactLaborCostForEarnedValue'
)
SELECT
  LC.[PrimaGlobalCountryName], LC.[CadenceDepartmentName]
  ,LC.[BillableFlag], BJD.Currency, BJD.[Rank], BJD.[BomDateID]
  ,SUM(AmountPTD) AmountPTD  -- ⚠️ Aggregates labor cost
INTO [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankDetaillAggregation]
FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post] LC
JOIN BudgetJuncDates BJD
  ON BJD.BomDateID = LC.BomDateID
 AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = LC.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY LC.[PrimaGlobalCountryName], LC.[CadenceDepartmentName]
        ,LC.[BillableFlag], BJD.Currency, BJD.[Rank], BJD.BomDateID
```

**JOIN Analysis:**
- **JOIN Type:** INNER JOIN to BudgetJuncDates
- **Cardinality:** 1:1 (composite key)
- **Risk:** **NO MULTIPLICATION**

**Aggregation:**
- **SUM(AmountPTD):** Sums labor cost by Country/Department/BillableFlag/Currency/Rank/Date
- **GROUP BY Grain:** `[PrimaGlobalCountryName], [CadenceDepartmentName], [BillableFlag], Currency, [Rank], BomDateID`

**Target Attribute Impact:**
- **Labor Cost (Billable):** Calculated here from `AmountPTD` where `BillableFlag = 1`

---

### 4.2 BillableEfficiency_Productivity_RankDetailAggregation

**Lines:** 167-233

```sql
WITH LaborCostAgg_Billable AS (
  SELECT [PrimaGlobalCountryName], [CadenceDepartmentName], Currency, [Rank], BomDateID, [BillableFlag]
        ,SUM(AmountPTD) BillableAmountPTD
  FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankDetaillAggregation]
  WHERE [BillableFlag] = 1
  GROUP BY [PrimaGlobalCountryName], [CadenceDepartmentName], Currency, [Rank], BomDateID, [BillableFlag]
),
LaborCostAgg_NonBillable AS (
  -- Same for BillableFlag = 0
),
LaborCost AS (
  SELECT COALESCE(B.[PrimaGlobalCountryName], NB.[PrimaGlobalCountryName]) as [PrimaGlobalCountryName]
        ,COALESCE(B.[CadenceDepartmentName], NB.[CadenceDepartmentName]) as [CadenceDepartmentName]
        ,COALESCE(B.Currency, NB.Currency) as Currency
        ,COALESCE(B.[Rank], NB.[Rank]) as [Rank]
        ,COALESCE(B.BomDateID, NB.BomDateID) as BomDateID
        ,BillableAmountPTD, NonBillableAmountPTD
  FROM LaborCostAgg_Billable B
  FULL OUTER JOIN LaborCostAgg_NonBillable NB ON ...
),
Budget_BF_Agg AS (
  SELECT [PrimaGlobalCountryName], [CadenceDepartmentName], Currency, [Rank], [BomDateID]
        ,SUM([Earned Value]) AS [Earned Value]
        ,SUM([Earned Value Version-2]) AS [Earned Value Version-2]
        ,SUM([Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
  FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency_RankDetail]
  GROUP BY [PrimaGlobalCountryName], [CadenceDepartmentName], Currency, [Rank], [BomDateID]
)
SELECT COALESCE(B.[PrimaGlobalCountryName], LC.[PrimaGlobalCountryName]) AS COUNTRY
      ,COALESCE(B.[CadenceDepartmentName], LC.[CadenceDepartmentName]) as [CadenceDepartmentName]
      ,COALESCE(B.Currency, LC.Currency) as Currency
      ,COALESCE(B.[Rank], LC.[Rank]) as [Rank]
      ,COALESCE(B.BomDateID, LC.BomDateID) as BomDateID
      ,CONVERT(DATE, SUBSTRING(...), 102) AS BomDate
      ,B.[Earned Value], B.[Earned Value Version-2], B.[Actual Cost of Work Performed]
      ,ISNULL(LC.BillableAmountPTD, 0.0) AS [Labor Cost (Billable)]  -- ⚠️ TARGET ATTRIBUTE
      ,ISNULL(LC.NonBillableAmountPTD, 0.0) AS [Labor Cost (Non-Billable)]
      ,ISNULL(LC.BillableAmountPTD, 0.0) + ISNULL(LC.NonBillableAmountPTD, 0.0) AS [Labor Cost (Total)]
INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankDetailAggregation
FROM Budget_BF_Agg B
FULL OUTER JOIN LaborCost LC ON ...
```

**JOIN Analysis:**
- **FULL OUTER JOIN:** Budget data ⋈ Labor Cost data
- **Cardinality:** 1:1 (matching on Country/Department/Currency/Rank/BomDateID)
- **Risk:** **NO MULTIPLICATION** (proper use of FULL OUTER JOIN with COALESCE)

**Target Attribute Calculation:**
- **[Labor Cost (Billable)] = ISNULL(LC.BillableAmountPTD, 0.0)**
  - Source: `LaborCostAgg_Billable.BillableAmountPTD`
  - Aggregated from `FactLaborCostForEarnedValue_RankDetaillAggregation`

**Target Attribute Impact:**
- **Labor Cost (Billable):** Calculated cleanly WITHOUT department mapping double-counting

---

## LAYER 5: FINAL TARGET - BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation

**File:** `spLoadEmployeeContractUtilization_Aggregations.sql`
**Lines:** 292-340

```sql
WITH AverageFTE_Monthly_RankDetail_Currency AS (
  SELECT U.*, C.Currency
  FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly_RankDetail U
  CROSS JOIN [CONSUMPTION_ClinOpsFinance].CURRENCY C  -- ⚠️ CROSS JOIN
  WHERE U.[ContractClassType] = 'EMPLOYEE'
)
SELECT COALESCE(BP.[Rank], U.[Rank]) AS [Rank]
      ,COALESCE(BP.[BOMDateID], U.[BOMDateID]) AS [BOMDateID]
      ,COALESCE(BP.[BOMDate], U.[BOMDate]) AS [BOMDate]
      ,COALESCE(BP.COUNTRY, U.[PrimaGlobalCountryName]) as [PrimaGlobalCountryName]
      ,COALESCE(BP.[CadenceDepartmentName], U.[CadenceDepartmentName]) AS [CadenceDepartmentName]
      ,COALESCE(BP.Currency, U.Currency) Currency
      ,BP.[Earned Value], BP.[Earned Value Version-2], BP.[Actual Cost of Work Performed]
      ,BP.[Labor Cost (Billable)]  -- ⚠️ From BillableEfficiency_Productivity_RankDetailAggregation
      ,BP.[Labor Cost (Non-Billable)], BP.[Labor Cost (Total)]
      ,U.[MonthlyFTEAggSUM (Fully Billable)]  -- ⚠️ FROM INFLATED SOURCE
      ,U.[MonthlyFTEAggSUM (Partially Billable)]  -- ⚠️ FROM INFLATED SOURCE
      ,U.[MonthlyFTEAggSUM (Non-Billable)]
      ,U.[MonthlyFTEAggSUM (Total)]
INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankDetailAggregation BP
FULL OUTER JOIN AverageFTE_Monthly_RankDetail_Currency U
  ON BP.Rank = U.Rank
 AND BP.BOMDateID = U.BomDateID
 AND BP.COUNTRY = U.PrimaGlobalCountryName
 AND BP.CadenceDepartmentName = U.CadenceDepartmentName
 AND BP.Currency = U.Currency
```

**CROSS JOIN Analysis:**
- **Purpose:** Create combinations of FTE data × Currency
- **Source Cardinality:** `AverageFTE_Monthly_RankDetail` × `CURRENCY` (4 currencies)
- **Effect:** Each FTE record is duplicated 4 times (CHF, GBP, USD, EUR)
- **Risk:** **INTENTIONAL MULTIPLICATION** for currency dimension (not a bug)

**FULL OUTER JOIN Analysis:**
- **Left:** `BillableEfficiency_Productivity_RankDetailAggregation` (labor cost + budget)
- **Right:** `AverageFTE_Monthly_RankDetail_Currency` (FTE data × currency)
- **JOIN Keys:** Rank, BOMDateID, PrimaGlobalCountryName, CadenceDepartmentName, Currency
- **Cardinality:** 1:1 (matching on composite key)
- **Risk:** **NO MULTIPLICATION** from this JOIN

**Final Attribute Sources:**

| Attribute | Source | Double-Counting Risk |
|-----------|--------|---------------------|
| **Labor Cost (Billable)** | BP.[Labor Cost (Billable)] from Layer 4.2 | ✅ CLEAN (no dept mapping) |
| **MonthlyFTEAggSUM (Fully Billable)** | U.[MonthlyFTEAggSUM (Fully Billable)] from Layer 1.3 | ❌ INFLATED (dept mapping issue) |
| **MonthlyFTEAggSUM (Partially Billable)** | U.[MonthlyFTEAggSUM (Partially Billable)] from Layer 1.3 | ❌ INFLATED (dept mapping issue) |

---

## Root Cause Analysis

### Double-Counting Mechanism

**Location:** `spLoadEmployeeContractUtilization_Aggregations.sql` Lines 46-47, 77-78, 98-99

**Problematic Code Pattern:**
```sql
JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
      FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) DM
ON DM.PrimaDepartmentName = EFD.Department
```

**Expected Code Pattern (from spLoadCadenceBudgetData.sql Lines 156-158):**
```sql
-- Currency conversion with PrimaDepartmentCount allocation
ISNULL((e.[SUM Function Planned Total Cost Adjusted]
        / NULLIF(d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1)
```

### Why It Happens

1. **Mapping Table Structure:**
   - `vFull_Departmental_Map_ActivePrima` contains 1:M relationships
   - One Prima department (from `HrContractAttendance.Department`) can map to multiple Cadence departments

2. **JOIN Without Allocation:**
   - The DISTINCT prevents duplicate mapping rows but does NOT prevent row multiplication
   - If "Document Management" (Prima) maps to 3 Cadence departments, the JOIN creates 3 rows per employee

3. **Missing Division Logic:**
   - The code does NOT apply `/ NULLIF(d.PrimaDepartmentCount, 0)` to allocate FTE proportionally
   - Compare with Lines 156-164 in `spLoadCadenceBudgetData.sql` which correctly divides by `PrimaDepartmentCount`

### Impact Quantification

**Multiplier = PrimaDepartmentCount** for affected department mappings

**Example:**
- If "Document Management" (Prima) maps to 3 Cadence departments:
  - Actual MonthlyFTEAggSUM (Fully Billable): 10.0
  - Reported value: 30.0 (inflated by 3×)

---

## Comparison with Correct Pattern

### Correct Implementation: spLoadCadenceBudgetData.sql

**Lines 30-40:**
```sql
insert into [STAGING_CADENCE].[DepartmenMapping]
select distinct b.CadenceDepartmentId, b.CadenceDepartmentName,
                b.PrimaDepartmentId, b.PrimaDepartmentName,
                a.PrimaDepartmentCount  -- ⚠️ CALCULATED HERE
from [dbo].[Full_Departmental_Map] b
inner join (
    select CadenceDepartmentId, count(1) as PrimaDepartmentCount
    from (select distinct CadenceDepartmentId, CadenceDepartmentName,
                          PrimaDepartmentId, PrimaDepartmentName
          from [dbo].[Full_Departmental_Map]) c
    group by CadenceDepartmentId
) a on b.CadenceDepartmentId = a.CadenceDepartmentId
```

**Lines 156-164:**
```sql
-- Division by PrimaDepartmentCount for proportional allocation
, ISNULL((e.[SUM Function Planned Total Cost Adjusted]
        / NULLIF(d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1)
    AS [SUM Function Planned Total Cost Adjusted]
, ISNULL((e.[SUM Function Planned Total Hours]
        / NULLIF(d.PrimaDepartmentCount, 0)), 0)
    AS [SUM Function Planned Total Hours]
```

### Incorrect Implementation: spLoadEmployeeContractUtilization_Aggregations.sql

**Lines 46-47:**
```sql
-- NO PrimaDepartmentCount calculation or division
JOIN (SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
      FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) DM
ON DM.PrimaDepartmentName = EFD.Department
```

**Missing Logic:**
- No `PrimaDepartmentCount` calculation
- No division by `PrimaDepartmentCount` in aggregations

---

## Recommendations

### Priority 1: Fix Department Mapping JOIN

**Affected Locations:**
1. `spLoadEmployeeContractUtilization_Aggregations.sql:46-47` (EmployeeAttendanceExpectedHours)
2. `spLoadEmployeeContractUtilization_Aggregations.sql:77-78` (EmployeeContractLastDayFTE)
3. `spLoadEmployeeContractUtilization_Aggregations.sql:98-99` (EmployeeContractAllDaysFTE)

**Recommended Fix:**

```sql
-- Step 1: Create department mapping with count (similar to spLoadCadenceBudgetData)
WITH DepartmentMappingWithCount AS (
  SELECT b.CadenceDepartmentId, b.CadenceDepartmentName,
         b.PrimaDepartmentId, b.PrimaDepartmentName,
         a.PrimaDepartmentCount
  FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima] b
  INNER JOIN (
    SELECT PrimaDepartmentId, COUNT(1) as PrimaDepartmentCount
    FROM (SELECT DISTINCT PrimaDepartmentId, PrimaDepartmentName,
                          CadenceDepartmentId, CadenceDepartmentName
          FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) c
    GROUP BY PrimaDepartmentId
  ) a ON b.PrimaDepartmentId = a.PrimaDepartmentId
)
SELECT EFD.[Employee_Id], ...
      ,DM.[CadenceDepartmentName]
      ,DM.PrimaDepartmentCount  -- Include in SELECT
      ,Count(*) AS CountEmployeeExpectedDays
      -- Divide aggregations by PrimaDepartmentCount
      ,Sum([Hours Expected, Daily]) / NULLIF(DM.PrimaDepartmentCount, 0)
          as [Sum (Hours Expected, Daily)]
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
JOIN DepartmentMappingWithCount DM
  ON DM.PrimaDepartmentName = EFD.Department
WHERE ...
GROUP BY EFD.[Employee_Id], ..., DM.[CadenceDepartmentName], DM.PrimaDepartmentCount
```

**Apply similar fix to:**
- Lines 77-82 (EmployeeContractLastDayFTE CTE)
- Lines 98-102 (EmployeeContractAllDaysFTE CTE)

### Priority 2: Data Validation

Run validation queries (see separate SQL file) to:
1. Identify which departments have `PrimaDepartmentCount > 1`
2. Quantify the inflation factor for affected departments
3. Compare expected vs actual aggregations

### Priority 3: Impact Assessment

**Affected Tables:**
1. `EmployeeAttendanceExpectedHoursUtilization_Monthly`
2. `EmployeeContractFTE_Monthly`
3. `AverageContractFTE_Monthly`
4. `AverageContractFTE_Monthly_RankDetail`
5. `BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation` (final target)

**NOT Affected:**
- `BillableEfficiency_Productivity_RankDetailAggregation` (uses different data source)
- `FactLaborCostForEarnedValue_*` (no department mapping issue)

---

## Summary

### Confirmed Issues

| Issue | Location | Impact | Severity |
|-------|----------|--------|----------|
| Department mapping row multiplication | spLoadEmployeeContractUtilization_Aggregations.sql Lines 46-47, 77-78, 98-99 | MonthlyFTEAggSUM attributes inflated by PrimaDepartmentCount factor | **CRITICAL** |

### Clean Data Flows

| Attribute | Clean? | Reason |
|-----------|--------|--------|
| Labor Cost (Billable) | ✅ YES | Sources from FactLaborCostForEarnedValue without department mapping |
| MonthlyFTEAggSUM (Fully Billable) | ❌ NO | Affected by department mapping multiplication |
| MonthlyFTEAggSUM (Partially Billable) | ❌ NO | Affected by department mapping multiplication |

### Next Actions

1. **Run validation queries** to quantify the issue (see `VALIDATION_QUERIES.sql`)
2. **Implement fix** for department mapping JOINs
3. **Re-run aggregation procedures** after fix
4. **Validate results** using reconciliation queries
5. **Document fix** in change log

---

## Appendix: Key File References

| File | Purpose | Key Lines |
|------|---------|-----------|
| `spLoadEmployeeContractUtilization_Aggregations.sql` | FTE aggregations (ISSUE HERE) | 30-340 |
| `spLoadFactLaborCostForEarnedValue_Post.sql` | Labor cost staging | 76-200 |
| `spLoadFactLaborCostForEarnedValue_Aggregations.sql` | Labor cost aggregations | 129-233 |
| `spLoadCadenceBudgetData.sql` | Budget data (CORRECT PATTERN) | 30-40, 156-164 |
| `spLoadCadenceBudget_Aggregations.sql` | Budget aggregations | 104-262 |
| `vFull_Departmental_Map_ActivePrima.sql` | Department mapping view | 1-13 |

---

**End of Data Lineage Analysis**
