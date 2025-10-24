-- =====================================================================================
-- SQL VALIDATION QUERY SUITE: Double-Counting Detection
-- =====================================================================================
-- Purpose: Detect and quantify suspected double-counting in FTE aggregations
--          due to department mapping row multiplication
--
-- Target Table: CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
-- Target Attributes:
--   1. [Labor Cost (Billable)]
--   2. [MonthlyFTEAggSUM (Fully Billable)]
--   3. [MonthlyFTEAggSUM (Partially Billable)]
--
-- Suspected Issue Scope:
--   PrimaGlobalCountryName = 'USA'
--   CadenceDepartmentName = 'Document Management'
--   Currency = 'USD'
--   RangeLabel = 'Last 1 year' (Rank = 1)
-- =====================================================================================

-- =====================================================================================
-- SECTION 1: DEPARTMENT MAPPING ANALYSIS
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- Query 1.1: Identify departments with 1:M mapping (PrimaDepartmentCount > 1)
-- -------------------------------------------------------------------------------------
-- Purpose: Find Prima departments that map to multiple Cadence departments
-- Expected: Document Management should appear if it has multiplicity
-- -------------------------------------------------------------------------------------

SELECT
      PrimaDepartmentId
    , PrimaDepartmentName
    , COUNT(DISTINCT CadenceDepartmentId) AS PrimaDepartmentCount
    , STRING_AGG(CAST(CadenceDepartmentName AS VARCHAR(MAX)), ', ') AS MappedCadenceDepartments
FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]
GROUP BY PrimaDepartmentId, PrimaDepartmentName
HAVING COUNT(DISTINCT CadenceDepartmentId) > 1
ORDER BY PrimaDepartmentCount DESC, PrimaDepartmentName;

-- Expected Result: List of Prima departments with multiple Cadence mappings
-- If 'Document Management' appears, note its PrimaDepartmentCount value


-- -------------------------------------------------------------------------------------
-- Query 1.2: Specific check for "Document Management" mapping
-- -------------------------------------------------------------------------------------
-- Purpose: Detailed view of Document Management department mapping
-- -------------------------------------------------------------------------------------

SELECT
      PrimaDepartmentId
    , PrimaDepartmentName
    , CadenceDepartmentId
    , CadenceDepartmentName
FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]
WHERE PrimaDepartmentName LIKE '%Document%Management%'
   OR CadenceDepartmentName LIKE '%Document%Management%'
ORDER BY PrimaDepartmentName, CadenceDepartmentName;

-- Expected Result: All Prima ↔ Cadence mappings for Document Management
-- Count the rows to determine the multiplicity factor


-- -------------------------------------------------------------------------------------
-- Query 1.3: Department mapping with count calculation
-- -------------------------------------------------------------------------------------
-- Purpose: Replicate the CORRECT pattern from spLoadCadenceBudgetData.sql
-- -------------------------------------------------------------------------------------

WITH DepartmentMappingWithCount AS (
    SELECT
          b.CadenceDepartmentId
        , b.CadenceDepartmentName
        , b.PrimaDepartmentId
        , b.PrimaDepartmentName
        , a.PrimaDepartmentCount
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
SELECT *
FROM DepartmentMappingWithCount
WHERE PrimaDepartmentName LIKE '%Document%Management%'
   OR CadenceDepartmentName LIKE '%Document%Management%'
ORDER BY PrimaDepartmentName, CadenceDepartmentName;

-- Expected Result: Document Management with PrimaDepartmentCount column
-- This is what SHOULD be used in the JOIN


-- =====================================================================================
-- SECTION 2: ROW MULTIPLICATION DETECTION IN FTE TABLES
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- Query 2.1: Detect duplicate employees in EmployeeContractFTE_Monthly
-- -------------------------------------------------------------------------------------
-- Purpose: Find employees with multiple rows for same BOMDateID (indicating row multiplication)
-- Issue: If an employee appears with same BOMDateID but different CadenceDepartmentName,
--        it indicates department mapping multiplication
-- -------------------------------------------------------------------------------------

SELECT
      Employee_Id
    , BOMDateId
    , PrimaGlobalCountryName
    , Position
    , BILLABLE_ID
    , ContractClassType
    , FTEValue
    , COUNT(*) AS RowCount
    , SUM(MonthlyFTEAggSUM) AS TotalMonthlyFTEAggSUM
    , STRING_AGG(CAST(CadenceDepartmentName AS VARCHAR(MAX)), ', ') AS AllCadenceDepartments
FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
WHERE PrimaGlobalCountryName = 'USA'
  AND BILLABLE_ID IN (0, 1)  -- Fully or Partially Billable
GROUP BY
      Employee_Id
    , BOMDateId
    , PrimaGlobalCountryName
    , Position
    , BILLABLE_ID
    , ContractClassType
    , FTEValue
HAVING COUNT(*) > 1
ORDER BY RowCount DESC, Employee_Id, BOMDateId;

-- Expected Result: Employees with duplicate rows due to department mapping
-- RowCount > 1 indicates row multiplication
-- TotalMonthlyFTEAggSUM should equal (MonthlyFTEAggSUM × RowCount) if inflated


-- -------------------------------------------------------------------------------------
-- Query 2.2: Quantify inflation in EmployeeContractFTE_Monthly for USA
-- -------------------------------------------------------------------------------------
-- Purpose: Compare expected vs actual aggregations for USA
-- -------------------------------------------------------------------------------------

WITH EmployeeAggregation AS (
    SELECT
          Employee_Id
        , BOMDateId
        , PrimaGlobalCountryName
        , BILLABLE_ID
        , ContractClassType
        , COUNT(DISTINCT CadenceDepartmentName) AS UniqueCadenceDepartments
        , COUNT(*) AS TotalRows
        , SUM(MonthlyFTEAggSUM) AS ActualAggregatedFTE
        , MAX(MonthlyFTEAggSUM) AS SingleEmployeeFTE  -- Assuming all rows have same FTE before multiplication
    FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
    WHERE PrimaGlobalCountryName = 'USA'
      AND BILLABLE_ID IN (0, 1)
    GROUP BY
          Employee_Id
        , BOMDateId
        , PrimaGlobalCountryName
        , BILLABLE_ID
        , ContractClassType
)
SELECT
      PrimaGlobalCountryName
    , BILLABLE_ID
    , CASE WHEN BILLABLE_ID = 0 THEN 'Fully Billable'
           WHEN BILLABLE_ID = 1 THEN 'Partially Billable'
           ELSE 'Other' END AS BillableCategory
    , COUNT(DISTINCT Employee_Id) AS UniqueEmployees
    , SUM(UniqueCadenceDepartments) AS TotalCadenceDepartmentRows
    , SUM(TotalRows) AS TotalRowsInTable
    , SUM(ActualAggregatedFTE) AS ActualAggregatedFTE_WithInflation
    , SUM(SingleEmployeeFTE) AS ExpectedFTE_WithoutInflation
    , SUM(ActualAggregatedFTE) - SUM(SingleEmployeeFTE) AS InflationAmount
    , CASE WHEN SUM(SingleEmployeeFTE) > 0
           THEN (SUM(ActualAggregatedFTE) / SUM(SingleEmployeeFTE)) - 1
           ELSE 0 END AS InflationFactor
FROM EmployeeAggregation
GROUP BY PrimaGlobalCountryName, BILLABLE_ID
ORDER BY BILLABLE_ID;

-- Expected Result:
-- - InflationFactor > 0 indicates inflation
-- - InflationFactor ≈ (PrimaDepartmentCount - 1) if department mapping is the issue


-- -------------------------------------------------------------------------------------
-- Query 2.3: Trace specific employee through the pipeline
-- -------------------------------------------------------------------------------------
-- Purpose: Follow a single employee's data through aggregation layers
-- Instructions: Replace <EMPLOYEE_ID> with an actual Employee_Id from Query 2.1
-- -------------------------------------------------------------------------------------

DECLARE @EmployeeId INT = <EMPLOYEE_ID>;  -- Replace with actual Employee_Id
DECLARE @BOMDateId INT = 20240101;        -- Replace with actual BOMDateId

-- Step 1: Source data from HrContractAttendance
SELECT
      'HrContractAttendance' AS SourceTable
    , Employee_Id
    , Date
    , Department AS PrimaDepartmentName
    , Country AS PrimaGlobalCountryName
    , Position
    , BILLABLE_ID
    , BILLABILITY
    , ContractClassType
    , FTE
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance]
WHERE Employee_Id = @EmployeeId
  AND [dbo].[udfDateToBomDateKey](Date) = @BOMDateId

UNION ALL

-- Step 2: After department mapping JOIN (EmployeeContractFTE_Monthly)
SELECT
      'EmployeeContractFTE_Monthly' AS SourceTable
    , CAST(Employee_Id AS VARCHAR(50))
    , CAST(BOMDateId AS VARCHAR(50))
    , CadenceDepartmentName  -- This is where multiplication happens
    , PrimaGlobalCountryName
    , Position
    , CAST(BILLABLE_ID AS VARCHAR(50))
    , CAST(BILLABLE_ID AS VARCHAR(50))
    , ContractClassType
    , CAST(MonthlyFTEAggSUM AS VARCHAR(50))
FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
WHERE Employee_Id = @EmployeeId
  AND BOMDateId = @BOMDateId;

-- Expected Result:
-- - Row 1: Original employee record from HrContractAttendance (1 row)
-- - Rows 2+: Multiple rows in EmployeeContractFTE_Monthly if department mapping causes multiplication


-- =====================================================================================
-- SECTION 3: AGGREGATED TABLE VALIDATION
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- Query 3.1: Validate AverageContractFTE_Monthly for USA/Document Management
-- -------------------------------------------------------------------------------------
-- Purpose: Check aggregated FTE values for the suspected problem area
-- -------------------------------------------------------------------------------------

SELECT
      BOMDateID
    , [dbo].[udfDateKeyToDate](BOMDateID) AS BOMDate
    , PrimaGlobalCountryName
    , CadenceDepartmentName
    , ContractClassType
    , [MonthlyFTEAggSUM (Fully Billable)]
    , [MonthlyFTEAggSUM (Partially Billable)]
    , [MonthlyFTEAggSUM (Non-Billable)]
    , [MonthlyFTEAggSUM (Total)]
FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly
WHERE PrimaGlobalCountryName = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
ORDER BY BOMDateID DESC;

-- Expected Result: Check if FTE values seem inflated compared to reasonable employee counts


-- -------------------------------------------------------------------------------------
-- Query 3.2: Compare FTE aggregations with employee counts
-- -------------------------------------------------------------------------------------
-- Purpose: Sanity check - FTE should align with employee counts
-- -------------------------------------------------------------------------------------

WITH EmployeeCounts AS (
    SELECT
          BOMDateId
        , PrimaGlobalCountryName
        , CadenceDepartmentName
        , BILLABLE_ID
        , COUNT(DISTINCT Employee_Id) AS UniqueEmployeeCount
        , SUM(MonthlyFTEAggSUM) AS TotalMonthlyFTEAggSUM
    FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
    WHERE PrimaGlobalCountryName = 'USA'
      AND CadenceDepartmentName LIKE '%Document%Management%'
    GROUP BY
          BOMDateId
        , PrimaGlobalCountryName
        , CadenceDepartmentName
        , BILLABLE_ID
)
SELECT
      BOMDateId
    , [dbo].[udfDateKeyToDate](BOMDateId) AS BOMDate
    , PrimaGlobalCountryName
    , CadenceDepartmentName
    , CASE WHEN BILLABLE_ID = 0 THEN 'Fully Billable'
           WHEN BILLABLE_ID = 1 THEN 'Partially Billable'
           WHEN BILLABLE_ID = 2 THEN 'Non-Billable'
           ELSE 'Other' END AS BillableCategory
    , UniqueEmployeeCount
    , TotalMonthlyFTEAggSUM
    , CASE WHEN UniqueEmployeeCount > 0
           THEN TotalMonthlyFTEAggSUM / UniqueEmployeeCount
           ELSE 0 END AS AvgFTEPerEmployee
FROM EmployeeCounts
ORDER BY BOMDateId DESC, BILLABLE_ID;

-- Expected Result:
-- - AvgFTEPerEmployee should be ≤ 1.0 for most cases
-- - If significantly > 1.0, indicates inflation


-- -------------------------------------------------------------------------------------
-- Query 3.3: Final target table validation for USA/Document Management/USD/Rank 1
-- -------------------------------------------------------------------------------------
-- Purpose: Check the final aggregated values in the target table
-- -------------------------------------------------------------------------------------

SELECT
      [Rank]
    , BOMDateID
    , BOMDate
    , PrimaGlobalCountryName
    , CadenceDepartmentName
    , Currency
    , [Earned Value]
    , [Earned Value Version-2]
    , [Actual Cost of Work Performed]
    , [Labor Cost (Billable)]  -- Should be CLEAN
    , [Labor Cost (Non-Billable)]
    , [Labor Cost (Total)]
    , [MonthlyFTEAggSUM (Fully Billable)]  -- Suspected INFLATED
    , [MonthlyFTEAggSUM (Partially Billable)]  -- Suspected INFLATED
    , [MonthlyFTEAggSUM (Non-Billable)]
    , [MonthlyFTEAggSUM (Total)]
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
WHERE PrimaGlobalCountryName = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
  AND Currency = 'USD'
  AND [Rank] = 1  -- Last 1 year
ORDER BY BOMDateID DESC;

-- Expected Result: Suspected inflated values in MonthlyFTEAggSUM columns


-- =====================================================================================
-- SECTION 4: ROW COUNT RECONCILIATION
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- Query 4.1: Row count comparison across pipeline stages
-- -------------------------------------------------------------------------------------
-- Purpose: Track row counts through the pipeline to identify multiplication points
-- -------------------------------------------------------------------------------------

SELECT
    'HrContractAttendance' AS TableName,
    COUNT(*) AS RowCount,
    COUNT(DISTINCT Employee_Id) AS UniqueEmployees,
    COUNT(DISTINCT Department) AS UniquePrimaDepartments
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance]
WHERE Country = 'USA'
  AND BILLABLE_ID IN (0, 1)

UNION ALL

SELECT
    'EmployeeContractFTE_Monthly' AS TableName,
    COUNT(*) AS RowCount,
    COUNT(DISTINCT Employee_Id) AS UniqueEmployees,
    COUNT(DISTINCT CadenceDepartmentName) AS UniqueCadenceDepartments
FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
WHERE PrimaGlobalCountryName = 'USA'
  AND BILLABLE_ID IN (0, 1)

UNION ALL

SELECT
    'AverageContractFTE_Monthly' AS TableName,
    COUNT(*) AS RowCount,
    0 AS UniqueEmployees,
    COUNT(DISTINCT CadenceDepartmentName) AS UniqueDepartments
FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly
WHERE PrimaGlobalCountryName = 'USA'

UNION ALL

SELECT
    'AverageContractFTE_Monthly_RankDetail' AS TableName,
    COUNT(*) AS RowCount,
    0 AS UniqueEmployees,
    COUNT(DISTINCT CadenceDepartmentName) AS UniqueDepartments
FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly_RankDetail
WHERE PrimaGlobalCountryName = 'USA'

UNION ALL

SELECT
    'BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation' AS TableName,
    COUNT(*) AS RowCount,
    0 AS UniqueEmployees,
    COUNT(DISTINCT CadenceDepartmentName) AS UniqueDepartments
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
WHERE PrimaGlobalCountryName = 'USA';

-- Expected Result:
-- - Row counts should increase proportionally
-- - Sharp increase in EmployeeContractFTE_Monthly indicates department mapping multiplication


-- -------------------------------------------------------------------------------------
-- Query 4.2: JOIN cardinality test - HrContractAttendance to Department Mapping
-- -------------------------------------------------------------------------------------
-- Purpose: Simulate the JOIN to see the multiplication effect
-- -------------------------------------------------------------------------------------

WITH SourceData AS (
    SELECT
          Employee_Id
        , Date
        , Department AS PrimaDepartmentName
        , Country
        , Position
        , BILLABLE_ID
        , BILLABILITY
        , ContractClassType
        , FTE
    FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance]
    WHERE Country = 'USA'
      AND BILLABLE_ID IN (0, 1)
      AND [dbo].[udfDateToBomDateKey](Date) = 20240101  -- Example date
),
JoinedData AS (
    SELECT
          SD.Employee_Id
        , SD.Date
        , SD.PrimaDepartmentName
        , DM.CadenceDepartmentName
        , SD.Country
        , SD.Position
        , SD.BILLABLE_ID
        , SD.FTE
    FROM SourceData SD
    INNER JOIN (
        SELECT DISTINCT PrimaDepartmentName, CadenceDepartmentName
        FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]
    ) DM ON DM.PrimaDepartmentName = SD.PrimaDepartmentName
)
SELECT
      'Before JOIN' AS Stage
    , COUNT(*) AS RowCount
    , COUNT(DISTINCT Employee_Id) AS UniqueEmployees
    , COUNT(DISTINCT PrimaDepartmentName) AS UniqueDepartments
FROM SourceData

UNION ALL

SELECT
      'After JOIN' AS Stage
    , COUNT(*) AS RowCount
    , COUNT(DISTINCT Employee_Id) AS UniqueEmployees
    , COUNT(DISTINCT CadenceDepartmentName) AS UniqueDepartments
FROM JoinedData;

-- Expected Result:
-- - Row count "After JOIN" > "Before JOIN" indicates multiplication
-- - Multiplication factor = (After JOIN RowCount) / (Before JOIN RowCount)


-- =====================================================================================
-- SECTION 5: LABOR COST VALIDATION (Should be CLEAN)
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- Query 5.1: Verify Labor Cost does NOT have department mapping issues
-- -------------------------------------------------------------------------------------
-- Purpose: Confirm that Labor Cost (Billable) is calculated correctly
-- -------------------------------------------------------------------------------------

SELECT
      PrimaGlobalCountryName
    , CadenceDepartmentName
    , Currency
    , [Rank]
    , BomDateID
    , [dbo].[udfDateKeyToDate](BomDateID) AS BomDate
    , BillableFlag
    , SUM(AmountPTD) AS TotalAmountPTD
    , COUNT(*) AS RowCount
FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post]
WHERE PrimaGlobalCountryName = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
  AND Currency = 'USD'
GROUP BY
      PrimaGlobalCountryName
    , CadenceDepartmentName
    , Currency
    , [Rank]
    , BomDateID
    , BillableFlag
ORDER BY BomDateID DESC, BillableFlag;

-- Expected Result: Clean aggregations without department mapping multiplication
-- Labor Cost should NOT show inflation


-- -------------------------------------------------------------------------------------
-- Query 5.2: Compare Labor Cost aggregation across layers
-- -------------------------------------------------------------------------------------

SELECT
      'FactLaborCostForEarnedValue_RankDetaillAggregation' AS SourceTable
    , PrimaGlobalCountryName
    , CadenceDepartmentName
    , Currency
    , [Rank]
    , BomDateID
    , SUM(CASE WHEN BillableFlag = 1 THEN AmountPTD ELSE 0 END) AS LaborCostBillable
FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankDetaillAggregation]
WHERE PrimaGlobalCountryName = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
  AND Currency = 'USD'
  AND [Rank] = 1
GROUP BY
      PrimaGlobalCountryName, CadenceDepartmentName, Currency, [Rank], BomDateID

UNION ALL

SELECT
      'BillableEfficiency_Productivity_RankDetailAggregation' AS SourceTable
    , COUNTRY AS PrimaGlobalCountryName
    , CadenceDepartmentName
    , Currency
    , [Rank]
    , BomDateID
    , [Labor Cost (Billable)]
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankDetailAggregation
WHERE COUNTRY = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
  AND Currency = 'USD'
  AND [Rank] = 1

UNION ALL

SELECT
      'BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation' AS SourceTable
    , PrimaGlobalCountryName
    , CadenceDepartmentName
    , Currency
    , [Rank]
    , BOMDateID AS BomDateID
    , [Labor Cost (Billable)]
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
WHERE PrimaGlobalCountryName = 'USA'
  AND CadenceDepartmentName LIKE '%Document%Management%'
  AND Currency = 'USD'
  AND [Rank] = 1
ORDER BY BomDateID DESC, SourceTable;

-- Expected Result: Labor Cost (Billable) should be IDENTICAL across all 3 tables
-- Confirms that Labor Cost is NOT affected by department mapping issue


-- =====================================================================================
-- SECTION 6: SUMMARY VALIDATION QUERY
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- Query 6.1: Comprehensive validation summary for USA/Document Management/USD/Rank 1
-- -------------------------------------------------------------------------------------
-- Purpose: Single query to show all key metrics for investigation
-- -------------------------------------------------------------------------------------

WITH DepartmentMapping AS (
    SELECT
          PrimaDepartmentName
        , COUNT(DISTINCT CadenceDepartmentName) AS PrimaDepartmentCount
    FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]
    WHERE PrimaDepartmentName LIKE '%Document%Management%'
       OR CadenceDepartmentName LIKE '%Document%Management%'
    GROUP BY PrimaDepartmentName
),
EmployeeData AS (
    SELECT
          COUNT(DISTINCT Employee_Id) AS UniqueEmployees
        , COUNT(*) AS TotalRowsInFTEMonthly
        , SUM(CASE WHEN BILLABLE_ID = 0 THEN MonthlyFTEAggSUM ELSE 0 END) AS SumFullyBillableFTE
        , SUM(CASE WHEN BILLABLE_ID = 1 THEN MonthlyFTEAggSUM ELSE 0 END) AS SumPartiallyBillableFTE
    FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
    WHERE PrimaGlobalCountryName = 'USA'
      AND CadenceDepartmentName LIKE '%Document%Management%'
      AND BOMDateId >= 20240101  -- Adjust date range as needed
),
FinalTarget AS (
    SELECT
          SUM([Labor Cost (Billable)]) AS TotalLaborCostBillable
        , SUM([MonthlyFTEAggSUM (Fully Billable)]) AS TotalMonthlyFTEAggSUM_FullyBillable
        , SUM([MonthlyFTEAggSUM (Partially Billable)]) AS TotalMonthlyFTEAggSUM_PartiallyBillable
        , COUNT(*) AS RowCountInFinalTable
    FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
    WHERE PrimaGlobalCountryName = 'USA'
      AND CadenceDepartmentName LIKE '%Document%Management%'
      AND Currency = 'USD'
      AND [Rank] = 1
)
SELECT
      'Department Mapping Multiplicity' AS MetricCategory
    , CAST(DM.PrimaDepartmentCount AS VARCHAR(50)) AS Value
    , 'Expected inflation factor if not allocated' AS Description
FROM DepartmentMapping DM

UNION ALL

SELECT
      'Unique Employees in EmployeeContractFTE_Monthly'
    , CAST(ED.UniqueEmployees AS VARCHAR(50))
    , 'Number of unique employees'
FROM EmployeeData ED

UNION ALL

SELECT
      'Total Rows in EmployeeContractFTE_Monthly'
    , CAST(ED.TotalRowsInFTEMonthly AS VARCHAR(50))
    , 'Should be close to UniqueEmployees if no multiplication'
FROM EmployeeData ED

UNION ALL

SELECT
      'SUM(MonthlyFTEAggSUM) Fully Billable in EmployeeContractFTE_Monthly'
    , CAST(ED.SumFullyBillableFTE AS VARCHAR(50))
    , 'Intermediate aggregation - may be inflated'
FROM EmployeeData ED

UNION ALL

SELECT
      'SUM(MonthlyFTEAggSUM) Partially Billable in EmployeeContractFTE_Monthly'
    , CAST(ED.SumPartiallyBillableFTE AS VARCHAR(50))
    , 'Intermediate aggregation - may be inflated'
FROM EmployeeData ED

UNION ALL

SELECT
      'Final MonthlyFTEAggSUM (Fully Billable)'
    , CAST(FT.TotalMonthlyFTEAggSUM_FullyBillable AS VARCHAR(50))
    , 'Target attribute - suspected inflated'
FROM FinalTarget FT

UNION ALL

SELECT
      'Final MonthlyFTEAggSUM (Partially Billable)'
    , CAST(FT.TotalMonthlyFTEAggSUM_PartiallyBillable AS VARCHAR(50))
    , 'Target attribute - suspected inflated'
FROM FinalTarget FT

UNION ALL

SELECT
      'Final Labor Cost (Billable)'
    , CAST(FT.TotalLaborCostBillable AS VARCHAR(50))
    , 'Should be CLEAN - no department mapping issue'
FROM FinalTarget FT

UNION ALL

SELECT
      'Rows in Final Target Table'
    , CAST(FT.RowCountInFinalTable AS VARCHAR(50))
    , 'Number of rows in final aggregation'
FROM FinalTarget FT;

-- Expected Result: Summary showing:
-- 1. Department mapping multiplicity
-- 2. Employee counts and row counts
-- 3. FTE aggregations (inflated vs expected)
-- 4. Labor Cost (should be clean)


-- =====================================================================================
-- END OF VALIDATION QUERIES
-- =====================================================================================
--
-- USAGE INSTRUCTIONS:
-- 1. Run queries in sequence (Section 1 → Section 6)
-- 2. Start with Section 1 to identify department mapping multiplicity
-- 3. Use Section 2 to detect row multiplication in FTE tables
-- 4. Section 3 validates aggregated tables
-- 5. Section 4 provides row count reconciliation
-- 6. Section 5 confirms Labor Cost is clean
-- 7. Section 6 provides comprehensive summary
--
-- EXPECTED FINDINGS:
-- - Query 1.1-1.3: Confirm "Document Management" has PrimaDepartmentCount > 1
-- - Query 2.1-2.3: Show employee row multiplication in EmployeeContractFTE_Monthly
-- - Query 3.1-3.3: Demonstrate inflated FTE aggregations
-- - Query 4.1-4.2: Quantify multiplication factor through pipeline stages
-- - Query 5.1-5.2: Verify Labor Cost (Billable) is NOT affected
-- - Query 6.1: Summary showing inflation in FTE but not Labor Cost
--
-- =====================================================================================
