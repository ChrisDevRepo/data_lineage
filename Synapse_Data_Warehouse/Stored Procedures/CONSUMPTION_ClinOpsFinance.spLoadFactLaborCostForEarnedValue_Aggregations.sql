CREATE PROC [CONSUMPTION_ClinOpsFinance].spLoadFactLaborCostForEarnedValue_Aggregations AS

BEGIN

SET NOCOUNT ON

--EXEC [CONSUMPTION_ClinOpsFinance].[spLoadFactLaborCostForEarnedValue_Aggregations]
-- Hours Expected Daily:
-- SELECT TOP (100) * FROM [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadFactLaborCostForEarnedValue_Aggregations]'  order by CreateDateTimeUTC desc
-- delete from [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadFactLaborCostForEarnedValue_Aggregations]'

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadFactLaborCostForEarnedValue_Aggregations'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0
  ,@Count  BIGINT = 0
  ,@ProcessingTime DATETIME = GETDATE();

BEGIN TRY

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.FactLaborCostForEarnedValue_RankAggregation') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankAggregation];
 
WITH BudgetJuncDates
AS
(
  SELECT [CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
    ,[KEY]
    ,[PrimaGlobalCountryName]
    ,Department
    ,Currency
    ,BomDateID
    ,[Rank]
  FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] J
  JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
  ON J.BomDateID = DR.DateID
  WHERE TableName = 'FactLaborCostForEarnedValue'
)
SELECT LC.[AccountName], LC.[SubAccountName], LC.[Country]
  , LC.[PrimaGlobalCountryName], LC.[PrimaDepartmentName], LC.[CadenceDepartmentName]
  , LC.[BillableFlag], LC.[Vtyp], BJD.Currency, BJD.[Rank]
  ,SUM(AmountPTD) AmountPTD
INTO  [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankAggregation]
FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post] LC
JOIN BudgetJuncDates BJD 
  ON BJD.BomDateID = LC.BomDateID
  AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = LC.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY LC.[AccountName], LC.[SubAccountName], LC.[Country]
  , LC.[PrimaGlobalCountryName], LC.[PrimaDepartmentName], LC.[CadenceDepartmentName]
  , LC.[BillableFlag], LC.[Vtyp], BJD.Currency, BJD.[Rank]

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[FactLaborCostForEarnedValue_RankAggregation] ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_Aggregation') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_Aggregation;
  
WITH LaborCostAgg_Billable AS (
  SELECT [PrimaGlobalCountryName],[CadenceDepartmentName], Currency, [Rank], [BillableFlag] ,SUM(AmountPTD) BillableAmountPTD
  FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankAggregation]
  WHERE [BillableFlag] = 1
  GROUP BY [PrimaGlobalCountryName],[CadenceDepartmentName],Currency, [Rank], [BillableFlag] 
 )
 ,LaborCostAgg_NonBillable AS (
  SELECT [PrimaGlobalCountryName],[CadenceDepartmentName], Currency, [Rank], [BillableFlag] ,SUM(AmountPTD) NonBillableAmountPTD
  FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankAggregation]
  WHERE [BillableFlag] = 0
  GROUP BY [PrimaGlobalCountryName],[CadenceDepartmentName],Currency, [Rank], [BillableFlag] 
 )
 ,LaborCost AS (
 SELECT COALESCE(B.[PrimaGlobalCountryName], NB.[PrimaGlobalCountryName]) as [PrimaGlobalCountryName] 
 ,COALESCE(B.[CadenceDepartmentName], NB.[CadenceDepartmentName]) as [CadenceDepartmentName]
 ,COALESCE(B.Currency, NB.Currency) as Currency
 ,COALESCE(B.[Rank], NB.[Rank]) as [Rank]
 ,BillableAmountPTD, NonBillableAmountPTD
 FROM LaborCostAgg_Billable B
 FULL OUTER JOIN LaborCostAgg_NonBillable NB
 ON B.[PrimaGlobalCountryName] = NB.[PrimaGlobalCountryName] 
 AND B.[CadenceDepartmentName] = NB.[CadenceDepartmentName]
 AND B.Currency = NB.Currency
 AND B.[Rank] = NB.[Rank]
 )
,Budget_BF_Agg AS
 (
 SELECT [PrimaGlobalCountryName], [CadenceDepartmentName], Currency,[Rank] 
  , SUM( [Earned Value]) AS [Earned Value] 
  , SUM([Earned Value Version-2]) AS [Earned Value Version-2]
  , SUM([Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
 FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency]
 GROUP BY [PrimaGlobalCountryName], [CadenceDepartmentName], Currency,[Rank] 
 )
 SELECT COALESCE(B.[PrimaGlobalCountryName],LC.[PrimaGlobalCountryName])  AS COUNTRY
 , COALESCE(B.[CadenceDepartmentName],LC.[CadenceDepartmentName]) AS [CadenceDepartmentName]
 , COALESCE(B.Currency,LC.Currency)  AS Currency
 , COALESCE(B.[Rank],LC.[Rank])  AS [Rank]
 ,B.[Earned Value], B.[Earned Value Version-2], B.[Actual Cost of Work Performed]
 ,ISNULL(LC.BillableAmountPTD,0.0) AS [Labor Cost (Billable)]
 ,ISNULL(LC.NonBillableAmountPTD,0.0) AS [Labor Cost (Non-Billable)]
 ,ISNULL(LC.BillableAmountPTD,0.0) + ISNULL(LC.NonBillableAmountPTD,0.0) AS [Labor Cost (Total)]
 INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_Aggregation
 FROM Budget_BF_Agg B 
 FULL OUTER JOIN LaborCost LC
 ON LC.[PrimaGlobalCountryName] = B.[PrimaGlobalCountryName]
  AND LC.[CadenceDepartmentName] = B.[CadenceDepartmentName]
  AND LC.Currency = B.Currency
  AND LC.[Rank] = B.[Rank];

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[BillableEfficiency_Productivity_Aggregation] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.FactLaborCostForEarnedValue_RankDetaillAggregation') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].FactLaborCostForEarnedValue_RankDetaillAggregation;

WITH BudgetJuncDates
AS
(
  SELECT [CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
    ,[KEY]
    ,[PrimaGlobalCountryName]
    ,Department
    ,Currency
    ,BomDateID
    ,[Rank]
  FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] J
  JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
  ON J.BomDateID = DR.DateID
  WHERE TableName = 'FactLaborCostForEarnedValue'
)
SELECT 
  LC.[PrimaGlobalCountryName], LC.[CadenceDepartmentName]
  , LC.[BillableFlag],  BJD.Currency, BJD.[Rank],BJD.[BomDateID]
  ,SUM(AmountPTD) AmountPTD
INTO  [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankDetaillAggregation]
FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post] LC
JOIN BudgetJuncDates BJD 
  ON BJD.BomDateID = LC.BomDateID
  AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = LC.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY LC.[PrimaGlobalCountryName], LC.[CadenceDepartmentName]
  , LC.[BillableFlag], BJD.Currency, BJD.[Rank],BJD.BomDateID

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[FactLaborCostForEarnedValue_RankDetaillAggregation] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_RankDetailAggregation') IS NOT NULL
  DROP TABLE [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankDetailAggregation;
 
WITH LaborCostAgg_Billable AS (
  SELECT [PrimaGlobalCountryName],[CadenceDepartmentName], Currency, [Rank], BomDateID, [BillableFlag] ,SUM(AmountPTD) BillableAmountPTD
  FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankDetaillAggregation]
  WHERE [BillableFlag] = 1
  GROUP BY [PrimaGlobalCountryName],[CadenceDepartmentName],Currency, [Rank], BomDateID, [BillableFlag] 
 )
 ,LaborCostAgg_NonBillable AS (
  SELECT [PrimaGlobalCountryName],[CadenceDepartmentName], Currency, [Rank], BomDateID, [BillableFlag] ,SUM(AmountPTD) NonBillableAmountPTD
  FROM [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_RankDetaillAggregation]
  WHERE [BillableFlag] = 0
  GROUP BY [PrimaGlobalCountryName],[CadenceDepartmentName],Currency, [Rank], BomDateID, [BillableFlag] 
 )
 ,LaborCost AS (
 SELECT COALESCE(B.[PrimaGlobalCountryName], NB.[PrimaGlobalCountryName]) as [PrimaGlobalCountryName] 
 ,COALESCE(B.[CadenceDepartmentName], NB.[CadenceDepartmentName]) as [CadenceDepartmentName]
 ,COALESCE(B.Currency, NB.Currency) as Currency
 ,COALESCE(B.[Rank], NB.[Rank]) as [Rank]
 ,COALESCE(B.BomDateID, NB.BomDateID) as  BomDateID
 ,BillableAmountPTD, NonBillableAmountPTD
 FROM LaborCostAgg_Billable B
 FULL OUTER JOIN LaborCostAgg_NonBillable NB
 ON B.[PrimaGlobalCountryName] = NB.[PrimaGlobalCountryName] 
 AND B.[CadenceDepartmentName] = NB.[CadenceDepartmentName]
 AND B.Currency = NB.Currency
 AND B.[Rank] = NB.[Rank]
 AND B.BomDateID = NB.BomDateID
 )
,Budget_BF_Agg AS
 (
 SELECT [PrimaGlobalCountryName], [CadenceDepartmentName], Currency,[Rank],[BomDateID]
  , SUM( [Earned Value]) AS [Earned Value] 
  , SUM([Earned Value Version-2]) AS [Earned Value Version-2]
  , SUM([Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
 FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency_RankDetail]
 GROUP BY [PrimaGlobalCountryName], [CadenceDepartmentName], Currency,[Rank], [BomDateID] 
 )
SELECT COALESCE(B.[PrimaGlobalCountryName], LC.[PrimaGlobalCountryName]) AS COUNTRY
,COALESCE(B.[CadenceDepartmentName], LC.[CadenceDepartmentName]) as [CadenceDepartmentName]
,COALESCE(B.Currency, LC.Currency) as Currency
,COALESCE(B.[Rank], LC.[Rank]) as [Rank]
,COALESCE(B.BomDateID, LC.BomDateID) as  BomDateID
  ,CONVERT(DATE, SUBSTRING( CAST(COALESCE(B.BomDateID, LC.BomDateID) AS VARCHAR(20)),1,4) + '/' 
    + SUBSTRING( CAST(COALESCE(B.BomDateID, LC.BomDateID) AS VARCHAR(20)),5,2)+ '/' 
    + SUBSTRING( CAST(COALESCE(B.BomDateID, LC.BomDateID) AS VARCHAR(20)),7,2), 102) AS BomDate
 ,B.[Earned Value], B.[Earned Value Version-2], B.[Actual Cost of Work Performed]
  ,ISNULL(LC.BillableAmountPTD,0.0) AS [Labor Cost (Billable)]
 ,ISNULL(LC.NonBillableAmountPTD,0.0) AS [Labor Cost (Non-Billable)]
 ,ISNULL(LC.BillableAmountPTD,0.0) + ISNULL(LC.NonBillableAmountPTD,0.0) AS [Labor Cost (Total)]
INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankDetailAggregation
FROM Budget_BF_Agg B 
FULL OUTER JOIN LaborCost LC
ON LC.[PrimaGlobalCountryName] = B.[PrimaGlobalCountryName]
  AND LC.[CadenceDepartmentName] = B.[CadenceDepartmentName]
  AND LC.Currency = B.Currency
  AND LC.[Rank] = B.[Rank] 
  AND LC.[BomDateID] = B.[BomDateID] ;

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[BillableEfficiency_Productivity_RankDetailAggregation] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

SELECT @MSG  = 'End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_RankGlobalAggregation') IS NOT NULL
  DROP TABLE [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankGlobalAggregation;
 
SELECT  [Currency]
      ,[Rank]
      ,[BomDateID]
      ,[BomDate]
      ,SUM([Earned Value]) AS [Earned Value]
      ,SUM([Earned Value Version-2]) AS [Earned Value Version-2]
      ,SUM([Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
      ,SUM([Labor Cost (Billable)]) AS [Labor Cost (Billable)]
      ,SUM([Labor Cost (Non-Billable)]) AS [Labor Cost (Non-Billable)]
      ,SUM([Labor Cost (Total)]) AS [Labor Cost (Total)]
INTO [CONSUMPTION_ClinOpsFinance].[BillableEfficiency_Productivity_RankGlobalAggregation]
  FROM [CONSUMPTION_ClinOpsFinance].[BillableEfficiency_Productivity_RankDetailAggregation]
  GROUP BY [Currency],[Rank],[BomDateID],[BomDate];

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[BillableEfficiency_Productivity_RankGlobalAggregation] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

END TRY

BEGIN CATCH

IF @@TRANCOUNT > 0
  rollback transaction;

DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048) ,@EndMsg varchar(200)

--store all the error information for logging the error
SELECT @ErrorNum       = ERROR_NUMBER() 
      ,@ErrorLine      = 0
      ,@ErrorSeverity  = ERROR_SEVERITY()
      ,@ErrorState     = ERROR_STATE()
      ,@ErrorProcedure = ERROR_PROCEDURE()
      ,@ErrorMessage   = ERROR_MESSAGE()

SET @MSG = @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') 
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState

SELECT @EndMsg  = 'End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @EndMsg, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH

END
 