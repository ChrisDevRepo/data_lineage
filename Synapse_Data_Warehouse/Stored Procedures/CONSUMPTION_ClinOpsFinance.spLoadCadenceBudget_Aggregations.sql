CREATE PROC [CONSUMPTION_ClinOpsFinance].spLoadCadenceBudget_Aggregations
AS

BEGIN

SET NOCOUNT ON

--EXEC [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudget_Aggregations]
-- Hours Expected Daily:
-- SELECT TOP (100) * FROM [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudget_Aggregations]'  order by CreateDateTimeUTC desc
-- delete from [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudget_Aggregations]'

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCadenceBudget_Aggregations'
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

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.CadenceBudgetData_EarnedValue') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_EarnedValue];


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
  WHERE TableName = 'CadenceBudgetData'
)
SELECT B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName,  BJD.Currency, BJD.[Rank], SUM(B.[Earned Value (Total Allocated)]) AS [Earned Value]
  , SUM(B.[Earned Value (Total Allocated) Version-2] ) AS [Earned Value Version-2]
INTO [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_EarnedValue]
FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post] B
JOIN BudgetJuncDates BJD 
  ON BJD.BomDateID = B.BomDateID
  AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = B.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName, BJD.Currency, BJD.[Rank]

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[CadenceBudgetData_EarnedValue] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.CadenceBudgetData_ActualCostOfWorkPerformed') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_ActualCostOfWorkPerformed];

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
  WHERE TableName = 'CadenceBudgetData'
)
SELECT B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName,  BJD.Currency, BJD.[Rank], SUM(B.[Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
INTO  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_ActualCostOfWorkPerformed]
FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post] B
JOIN BudgetJuncDates BJD 
  ON BJD.BomDateID = B.BomDateID
  AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = B.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName, BJD.Currency, BJD.[Rank]

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[CadenceBudgetData_ActualCostOfWorkPerformed] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.CadenceBudgetData_BillableEfficiency') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency];

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
  WHERE TableName = 'CadenceBudgetData'
)
SELECT B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName,  BJD.Currency, BJD.[Rank]
  , SUM(B.[Earned Value (Total Allocated)]) AS [Earned Value] 
  , SUM(B.[Earned Value (Total Allocated) Version-2] ) AS [Earned Value Version-2]
  , SUM(B.[Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
INTO  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency]
FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post] B
JOIN BudgetJuncDates BJD 
  ON BJD.BomDateID = B.BomDateID
  AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = B.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName, BJD.Currency, BJD.[Rank]

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[CadenceBudgetData_BillableEfficiency] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.CadenceBudgetData_BillableEfficiency_Task') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency_Task];

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
  WHERE TableName = 'CadenceBudgetData'
)
select 
      AA.[Project Name]
    , AA.[Function]
    , AA.[CadenceDepartmentName]
    , AA.[Service]
    , AA.[Task]
    , AA.[Task Country]
    , AA.[Unit Type]
    , AA.[Function Country]
    , AA.[PrimaGlobalCountryName]
    , AA.[Archived Project Ref Id]
    , AA.[Currency]
    , AA.[Rank] 
    , MAX(AA.[SUM Function Planned Total Hours])          as [SUM Function Planned Total Hours]
    , MAX(AA.[SUM Task Planned Total Units])              as [SUM Task Planned Total Units]
    , SUM(AA.[SUM Function TimeSheet Actual Total Hours]) as [SUM Function TimeSheet Actual Total Hours]
    , SUM(AA.[SUM Task Approved Total Units])             as [SUM Task Approved Total Units]
    , MAX(AA.[SUM Function Planned Total Cost Adjusted])  as [SUM Function Planned Total Cost Adjusted]
    , SUM(AA.[Earned Value])                              as [Earned Value]
    , SUM(AA.[Earned Value Version-2])                    as [Earned Value Version-2]
    , SUM(AA.[Actual Cost of Work Performed])             as [Actual Cost of Work Performed]
INTO  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency_Task]
FROM (
SELECT B.BomDateID, B.[Project Name], B.[Function], B.[CadenceDepartmentName]
  ,B.[Service],B.Task,B.[Task Country], B.[Unit Type]
  ,B.[Function Country], B.PrimaGlobalCountryName, B.[Archived Project Ref Id], BJD.Currency, BJD.[Rank]
,MAX([SUM Function Planned Total Hours]) AS [SUM Function Planned Total Hours]
,MAX([SUM Task Planned Total Units]) AS [SUM Task Planned Total Units]
,SUM([SUM Function TimeSheet Actual Total Hours]) AS [SUM Function TimeSheet Actual Total Hours]
,MAX([SUM Task Approved Total Units]) AS [SUM Task Approved Total Units]
,MAX([SUM Function Planned Total Cost Adjusted]) AS [SUM Function Planned Total Cost Adjusted]
  , SUM(B.[Earned Value (Total Allocated)]) AS [Earned Value] 
  , SUM(B.[Earned Value (Total Allocated) Version-2] ) AS [Earned Value Version-2]
  , SUM(B.[Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]

FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post] B
JOIN BudgetJuncDates BJD 
  ON BJD.BomDateID = B.BomDateID
  AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = B.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY B.BomDateID, B.[Project Name], B.[Function], B.[CadenceDepartmentName]
  ,B.[Service],B.Task,B.[Task Country], B.[Unit Type]
  ,B.[Function Country], B.PrimaGlobalCountryName, B.[Archived Project Ref Id], BJD.Currency, BJD.[Rank]
) AA
group by       
      AA.[Project Name]
    , AA.[Function]
    , AA.[CadenceDepartmentName]
    , AA.[Service]
    , AA.[Task]
    , AA.[Task Country]
    , AA.[Unit Type]
    , AA.[Function Country]
    , AA.[PrimaGlobalCountryName]
    , AA.[Archived Project Ref Id]
    , AA.[Currency]
    , AA.[Rank]

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[CadenceBudgetData_BillableEfficiency_Task] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.CadenceBudgetData_BillableEfficiency_RankDetail') IS NOT NULL
  DROP TABLE  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency_RankDetail];

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
  WHERE TableName = 'CadenceBudgetData'
)
SELECT B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName,  BJD.Currency, BJD.[Rank],BJD.[BomDateID]
  , CONVERT(DATE, SUBSTRING( CAST(BJD.[BomDateID] AS VARCHAR(20)),1,4) + '/' 
    + SUBSTRING( CAST(BJD.[BomDateID] AS VARCHAR(20)),5,2)+ '/' 
    + SUBSTRING( CAST(BJD.[BomDateID] AS VARCHAR(20)),7,2), 102) AS BomDate
  , SUM(B.[Earned Value (Total Allocated)]) AS [Earned Value] 
  , SUM(B.[Earned Value (Total Allocated) Version-2] ) AS [Earned Value Version-2]
  , SUM(B.[Actual Cost of Work Performed]) AS [Actual Cost of Work Performed]
INTO  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_BillableEfficiency_RankDetail]
FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post] B
JOIN BudgetJuncDates BJD 
  ON BJD.BomDateID = B.BomDateID
  AND BJD.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] = B.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
GROUP BY B.[Project Name], B.[Function], B.[CadenceDepartmentName],
  B.[Function Country], B.PrimaGlobalCountryName, BJD.Currency, BJD.[Rank],BJD.[BomDateID]
EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[CadenceBudgetData_BillableEfficiency_RankDetail] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

SELECT @MSG  = 'End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

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
GO
 