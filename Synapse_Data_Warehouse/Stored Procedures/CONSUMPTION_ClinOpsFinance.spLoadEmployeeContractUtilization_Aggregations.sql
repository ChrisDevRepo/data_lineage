CREATE PROC [CONSUMPTION_ClinOpsFinance].spLoadEmployeeContractUtilization_Aggregations

AS

BEGIN

SET NOCOUNT ON

--EXEC [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Aggregations]
--  
-- SELECT TOP (100) * FROM [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Aggregations]'  order by CreateDateTimeUTC desc
-- delete from [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Aggregations]'
SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadEmployeeContractUtilization_Aggregations'
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

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.EmployeeAttendanceExpectedHoursUtilization_Monthly') IS NOT NULL
DROP TABLE  [CONSUMPTION_ClinOpsFinance].EmployeeAttendanceExpectedHoursUtilization_Monthly;

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
      ,Sum([Hours Expected, Daily]) as [Sum (Hours Expected, Daily)]
INTO [CONSUMPTION_ClinOpsFinance].EmployeeAttendanceExpectedHoursUtilization_Monthly
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
JOIN (SELECT DISTINCT PrimaDepartmentName,  CadenceDepartmentName FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima] ) DM
ON DM.PrimaDepartmentName = EFD.Department
WHERE [IS_HOLIDAY] + [IS_VACATION] + [IS_SICK_LEAVE] + [IS_DAY_OFF] + [IS_WEEKEND] + [IS_DISMISS]  + [IS_LongTermLeave] = 0 
GROUP BY EFD.[Employee_Id], EFD.[UtilizationDateId] ,EFD.[Date (Utilization)] ,EFD.[Country]   
  ,DM.[CadenceDepartmentName] ,EFD.[Position] ,EFD.[BILLABLE_ID] ,EFD.[BILLABILITY] ,EFD.[ContractClassType]

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[EmployeeAttendanceExpectedUtilizationHours_Monthly] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.EmployeeContractFTE_Monthly') IS NOT NULL
DROP TABLE  [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly;

WITH EmployeeContractLastDayFTE
AS (
SELECT  EFD.[Employee_Id]
      ,[dbo].[udfDateToBomDateKey](EFD.Date) AS [BOMDateId]
      ,EFD.[Country]
      ,DM.[CadenceDepartmentName]
      ,EFD.[Position]
      ,EFD.[BILLABLE_ID]
      ,EFD.[ContractClassName]
      ,EFD.[ContractClassType]
      ,EFD.[FTE] AS FTEValue
      ,SUM(EFD.[FTE]) AS TotalFTE
      ,COUNT(EFD.[FTE]) AS CountFTE
FROM [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] EFD
JOIN (SELECT DISTINCT PrimaDepartmentName,  CadenceDepartmentName FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima] ) DM
ON DM.PrimaDepartmentName = EFD.Department
WHERE EFD.[DATE] = CAST(DBO.udfDateToEomDate (EFD.[DATE]) AS DATE)
GROUP BY EFD.[Employee_Id], [dbo].[udfDateToBomDateKey](EFD.Date) ,EFD.[Country]
  ,DM.[CadenceDepartmentName],EFD.[Position],EFD.[BILLABLE_ID]
  ,EFD.[ContractClassName],EFD.[ContractClassType],EFD.[FTE]
)
, EmployeeContractAllDaysFTE
AS (
SELECT EFD.[Employee_Id]
      ,[dbo].[udfDateToBomDateKey](EFD.Date) AS [BOMDateId]
      ,EFD.[Country]
      ,DM.[CadenceDepartmentName]
      ,EFD.[Position]
      ,EFD.[BILLABLE_ID]
      ,EFD.[ContractClassName]
      ,EFD.[ContractClassType]
      ,EFD.[FTE] AS FTEValue
      ,SUM(EFD.[FTE]) AS TotalFTE
      ,COUNT(EFD.[FTE]) AS CountFTE
FROM [CONSUMPTION_ClinOpsFinance].HrContractAttendance EFD
JOIN  (SELECT DISTINCT PrimaDepartmentName,  CadenceDepartmentName FROM [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima] ) DM 
ON DM.PrimaDepartmentName = EFD.Department
GROUP BY EFD.[Employee_Id], [dbo].[udfDateToBomDateKey](EFD.Date),EFD.[Country]
  ,DM.[CadenceDepartmentName],EFD.[Position],EFD.[BILLABLE_ID]
  ,EFD.[ContractClassName],EFD.[ContractClassType],EFD.[FTE]
)
SELECT EAFD.[Employee_Id]
      ,EAFD.[BOMDateId]
      ,EAFD.[Country] AS [PrimaGlobalCountryName]
      ,EAFD.[CadenceDepartmentName]
      ,EAFD.[Position]
      ,EAFD.[BILLABLE_ID]
      ,EAFD.[ContractClassName]
      ,EAFD.[ContractClassType]
      ,EAFD.FTEValue
      ,EAFD.TotalFTE As MonthlyFTEAggSUM
      ,EAFD.CountFTE As MonthlyFTEAggCount
      ,EAFD.TotalFTE / CASE WHEN EAFD.CountFTE = 0 THEN CAST(NULL AS FLOAT) ELSE EAFD.CountFTE END AS [Monthly Average FTE]
      ,ELFD.TotalFTE As LastDayDailyFTEAggSUM
      ,ELFD.CountFTE As LastDayFTEAggCount
      ,ELFD.TotalFTE / CASE WHEN ELFD.CountFTE = 0 THEN CAST(NULL AS FLOAT) ELSE ELFD.CountFTE END  AS [Monthly Average FTE, Last Day]
INTO [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
FROM EmployeeContractAllDaysFTE EAFD
LEFT JOIN EmployeeContractLastDayFTE ELFD
ON EAFD.[Employee_Id] = ELFD.[Employee_Id]
   AND EAFD.[BOMDateId] = ELFD.[BOMDateId]
   AND EAFD.[Country] = ELFD.[Country]
   AND EAFD.[CadenceDepartmentName] = ELFD.[CadenceDepartmentName]
   AND EAFD.[Position] = ELFD.[Position]
   AND EAFD.[BILLABLE_ID] = ELFD.[BILLABLE_ID]
   AND EAFD.[ContractClassName] = ELFD.[ContractClassName]
   AND EAFD.[ContractClassType] = ELFD.[ContractClassType]
   AND EAFD.FTEValue = ELFD.FTEValue ; 

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[EmployeeContractFTE_Monthly] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.AverageContractFTE_Monthly') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly;

With FullBillable 
AS
(
SELECT
   [BOMDateID]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[ContractClassType]
  ,COUNT(*) AS EmployeeCount
  ,SUM(MonthlyFTEAggCount) As MonthlyFTEAggCount
  ,SUM(MonthlyFTEAggSUM) As MonthlyFTEAggSUM
  ,SUM(LastDayFTEAggCount) As MonthlyLastDayFTEAggCount
  ,SUM(LastDayDailyFTEAggSUM) As MonthlyLastDayDailyFTEAggSUM
FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly 
WHERE [BILLABLE_ID] IN (0)
GROUP BY [BOMDateID]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[ContractClassType]
)
,PartialBillable 
AS
(
SELECT
   [BOMDateID]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[ContractClassType]
  ,COUNT(*) AS EmployeeCount
  ,SUM(MonthlyFTEAggCount) As MonthlyFTEAggCount
  ,SUM(MonthlyFTEAggSUM) As MonthlyFTEAggSUM
  ,SUM(LastDayFTEAggCount) As MonthlyLastDayFTEAggCount
  ,SUM(LastDayDailyFTEAggSUM) As MonthlyLastDayDailyFTEAggSUM
FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly 
WHERE [BILLABLE_ID] IN (1)
GROUP BY [BOMDateID]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[ContractClassType]
)
,NonBillable
AS
(
SELECT
   [BOMDateID]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[ContractClassType]
  ,COUNT(*) AS EmployeeCount
  ,SUM(MonthlyFTEAggCount) As MonthlyFTEAggCount
  ,SUM(MonthlyFTEAggSUM) As MonthlyFTEAggSUM
  ,SUM(LastDayFTEAggCount) As MonthlyLastDayFTEAggCount
  ,SUM(LastDayDailyFTEAggSUM) As MonthlyLastDayDailyFTEAggSUM
FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly 
WHERE [BILLABLE_ID] IN (2)
GROUP BY [BOMDateID]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[ContractClassType]
)
,AllBillable
AS
(
SELECT COALESCE(B.[BOMDateID],N.[BOMDateID]) AS [BOMDateID],  COALESCE(B.[PrimaGlobalCountryName],N.[PrimaGlobalCountryName]) AS [PrimaGlobalCountryName]
  ,COALESCE(B.[CadenceDepartmentName], N.[CadenceDepartmentName]) AS [CadenceDepartmentName], COALESCE(B.[ContractClassType], N.[ContractClassType]) AS [ContractClassType]
  , B.EmployeeCount AS [FTE EmployeeCount (Fully Billable)], B.MonthlyFTEAggCount AS [MonthlyFTEAggCount (Fully Billable)]
  , B.MonthlyFTEAggSUM AS [MonthlyFTEAggSUM (Fully Billable)]  
  , B.MonthlyLastDayFTEAggCount AS [MonthlyLastDayFTEAggCount (Fully Billable)]
  , B.MonthlyLastDayDailyFTEAggSUM AS [MonthlyLastDayDailyFTEAggSUM (Fully Billable)]  
  , N.EmployeeCount AS [FTE EmployeeCount (Partially Billable)], N.MonthlyFTEAggCount AS [MonthlyFTEAggCount (Partially Billable)]
  , N.MonthlyFTEAggSUM AS [MonthlyFTEAggSUM (Partially Billable)]  
  , N.MonthlyLastDayFTEAggCount AS [MonthlyLastDayFTEAggCount (Partially Billable)]
  , N.MonthlyLastDayDailyFTEAggSUM AS [MonthlyLastDayDailyFTEAggSUM (Partially Billable)]  
FROM FullBillable  B
FULL OUTER JOIN PartialBillable N
  ON  B.[BOMDateID] = N.[BOMDateID] 
  AND B.[PrimaGlobalCountryName] = N.[PrimaGlobalCountryName]
  AND B.[CadenceDepartmentName] = N.[CadenceDepartmentName]
  AND B.[ContractClassType] = N.[ContractClassType]
)
SELECT COALESCE(B.[BOMDateID],N.[BOMDateID]) AS [BOMDateID],  COALESCE(B.[PrimaGlobalCountryName],N.[PrimaGlobalCountryName]) AS [PrimaGlobalCountryName]
  ,COALESCE(B.[CadenceDepartmentName], N.[CadenceDepartmentName]) AS [CadenceDepartmentName], COALESCE(B.[ContractClassType], N.[ContractClassType]) AS [ContractClassType]
  , B.[FTE EmployeeCount (Fully Billable)]
  , B.[MonthlyFTEAggCount (Fully Billable)]
  , B.[MonthlyFTEAggSUM (Fully Billable)]  
  , B.[MonthlyLastDayFTEAggCount (Fully Billable)]
  , B.[MonthlyLastDayDailyFTEAggSUM (Fully Billable)]  
  , B.[FTE EmployeeCount (Partially Billable)]
  , B.[MonthlyFTEAggCount (Partially Billable)]
  , B.[MonthlyFTEAggSUM (Partially Billable)]  
  , B.[MonthlyLastDayFTEAggCount (Partially Billable)]
  , B.[MonthlyLastDayDailyFTEAggSUM (Partially Billable)]  
  , N.EmployeeCount AS [FTE EmployeeCount (Non-Billable)], N.MonthlyFTEAggCount AS [MonthlyFTEAggCount (Non-Billable)], N.MonthlyFTEAggSUM AS [MonthlyFTEAggSUM (Non-Billable)]  
  , N.MonthlyLastDayFTEAggCount AS [MonthlyLastDayFTEAggCount (Non-Billable)], N.MonthlyLastDayDailyFTEAggSUM AS [MonthlyLastDayDailyFTEAggSUM (Non-Billable)]  
INTO [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly
FROM AllBillable  B
FULL OUTER JOIN NonBillable N
  ON  B.[BOMDateID] = N.[BOMDateID] 
  AND B.[PrimaGlobalCountryName] = N.[PrimaGlobalCountryName]
  AND B.[CadenceDepartmentName] = N.[CadenceDepartmentName]
  AND B.[ContractClassType] = N.[ContractClassType] ;

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[AverageContractFTE_Monthly] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.AverageContractFTE_Monthly_RankDetail') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly_RankDetail

SELECT [Rank]
  ,[BOMDateID]
  ,dbo.udfDateKeyToDate([BOMDateID]) AS [BOMDate]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[ContractClassType]  
  ,[FTE EmployeeCount (Fully Billable)]
  ,[MonthlyFTEAggCount (Fully Billable)]
  ,[MonthlyFTEAggSUM (Fully Billable)]
  ,[MonthlyLastDayFTEAggCount (Fully Billable)]
  ,[MonthlyLastDayDailyFTEAggSUM (Fully Billable)]
  ,[FTE EmployeeCount (Partially Billable)]
  ,[MonthlyFTEAggCount (Partially Billable)]
  ,[MonthlyFTEAggSUM (Partially Billable)]
  ,[MonthlyLastDayFTEAggCount (Partially Billable)]
  ,[MonthlyLastDayDailyFTEAggSUM (Partially Billable)]
  ,[FTE EmployeeCount (Non-Billable)]
  ,[MonthlyFTEAggCount (Non-Billable)]
  ,[MonthlyFTEAggSUM (Non-Billable)]
  ,[MonthlyLastDayFTEAggCount (Non-Billable)]
  ,[MonthlyLastDayDailyFTEAggSUM (Non-Billable)]
  ,ISNULL([FTE EmployeeCount (Fully Billable)],0.0) + ISNULL([FTE EmployeeCount (Partially Billable)],0.0) + ISNULL([FTE EmployeeCount (Non-Billable)],0.0) AS  [FTE EmployeeCount (Total)]
  ,ISNULL([MonthlyFTEAggCount (Fully Billable)],0.0) + ISNULL([MonthlyFTEAggCount (Partially Billable)],0.0) + ISNULL([MonthlyFTEAggCount (Non-Billable)],0.0) AS  [MonthlyFTEAggCount (Total)]
  ,ISNULL([MonthlyFTEAggSUM (Fully Billable)],0.0) + ISNULL([MonthlyFTEAggSUM (Partially Billable)],0.0) + ISNULL([MonthlyFTEAggSUM (Non-Billable)],0.0) AS [MonthlyFTEAggSUM (Total)]
  ,ISNULL([MonthlyLastDayFTEAggCount (Fully Billable)],0.0) + ISNULL([MonthlyLastDayFTEAggCount (Partially Billable)],0.0) + ISNULL([MonthlyLastDayFTEAggCount (Non-Billable)],0.0) AS [MonthlyLastDayFTEAggCount (Total)]
  ,ISNULL([MonthlyLastDayDailyFTEAggSUM (Fully Billable)],0.0) + ISNULL([MonthlyLastDayDailyFTEAggSUM (Partially Billable)],0.0) + ISNULL([MonthlyLastDayDailyFTEAggSUM (Non-Billable)],0.0) AS [MonthlyLastDayDailyFTEAggSUM (Total)]
INTO [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly_RankDetail
FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly AF
JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
  ON AF.[BOMDateID] = DR.DateID 

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[AverageContractFTE_Monthly_RankDetail] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation;

WITH AverageFTE_Monthly_RankDetail_Currency
AS
(
SELECT U.* , C.Currency
FROM [CONSUMPTION_ClinOpsFinance].AverageContractFTE_Monthly_RankDetail U
CROSS JOIN  [CONSUMPTION_ClinOpsFinance].CURRENCY C
WHERE U.[ContractClassType] = 'EMPLOYEE'
)
SELECT COALESCE(BP.[Rank],U.[Rank] ) AS [Rank], COALESCE(BP.[BOMDateID],U.[BOMDateID]) AS [BOMDateID], COALESCE(BP.[BOMDate],U.[BOMDate]) AS [BOMDate]
  , COALESCE(BP.COUNTRY,U.[PrimaGlobalCountryName]) as [PrimaGlobalCountryName], COALESCE(BP.[CadenceDepartmentName],U.[CadenceDepartmentName]) AS [CadenceDepartmentName],
     COALESCE(BP.Currency,U.Currency) Currency --,
  ,BP.[Earned Value],BP.[Earned Value Version-2], BP.[Actual Cost of Work Performed], BP.[Labor Cost (Billable)]
  ,BP.[Labor Cost (Non-Billable)], BP.[Labor Cost (Total)]
  ,U.[FTE EmployeeCount (Fully Billable)]
  ,U.[MonthlyFTEAggCount (Fully Billable)]
  ,U.[MonthlyFTEAggSUM (Fully Billable)]
  ,U.[MonthlyLastDayFTEAggCount (Fully Billable)]
  ,U.[MonthlyLastDayDailyFTEAggSUM (Fully Billable)]
  ,U.[FTE EmployeeCount (Partially Billable)]
  ,U.[MonthlyFTEAggCount (Partially Billable)]
  ,U.[MonthlyFTEAggSUM (Partially Billable)]
  ,U.[MonthlyLastDayFTEAggCount (Partially Billable)]
  ,U.[MonthlyLastDayDailyFTEAggSUM (Partially Billable)]
  ,U.[FTE EmployeeCount (Non-Billable)]
  ,U.[MonthlyFTEAggCount (Non-Billable)]
  ,U.[MonthlyFTEAggSUM (Non-Billable)]
  ,U.[MonthlyLastDayFTEAggCount (Non-Billable)]
  ,U.[MonthlyLastDayDailyFTEAggSUM (Non-Billable)]
  ,U.[FTE EmployeeCount (Total)]
  ,U.[MonthlyFTEAggCount (Total)]
  ,U.[MonthlyFTEAggSUM (Total)]
  ,U.[MonthlyLastDayFTEAggCount (Total)]
  ,U.[MonthlyLastDayDailyFTEAggSUM (Total)]
INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankDetailAggregation BP
FULL OUTER JOIN AverageFTE_Monthly_RankDetail_Currency U
ON BP.Rank = U.Rank
  AND BP.BOMDateID = U.BomDateID
  AND BP.COUNTRY = U.PrimaGlobalCountryName
  AND BP.CadenceDepartmentName = U.CadenceDepartmentName
  AND BP.Currency = U.Currency

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

---- Tables needed for Billed Hours and Expected hours from Timesheets

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.Employee_Day_Hours') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].[Employee_Day_Hours]

SELECT  EMPLOYEE_ID
  ,DATE
  ,[UtilizationDateId]
  ,[Date (Utilization)]
  ,Office_Country_name
  ,[CadenceDepartmentName]
  ,Position
  ,CAST(CASE WHEN [isBillable] = 'Yes'  THEN 1 ELSE 0 END AS TINYINT) AS BillableFlag
  ,BILLABLE_ID
  ,[BILLABILITY]
  ,[ContractClassType]
  ,SUM([Hours Billed]) [Day Hours Billed]
INTO [CONSUMPTION_ClinOpsFinance].[Employee_Day_Hours]  
FROM [CONSUMPTION_ClinOpsFinance].[EmployeeContractUtilization_Post]  
GROUP BY EMPLOYEE_ID, DATE, [UtilizationDateId], [Date (Utilization)], Office_Country_name, [CadenceDepartmentName], Position, [isBillable] ,BILLABLE_ID, [BILLABILITY], [ContractClassType]

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[Employee_Day_Hours] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.EmployeeTimeSheetHours_Utilization') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].[EmployeeTimeSheetHours_Utilization];

SELECT  EMPLOYEE_ID 
  ,[UtilizationDateId]
  ,[Date (Utilization)]
  ,Office_Country_name
  ,[CadenceDepartmentName]
  ,Position
  ,BillableFlag
  ,[BILLABLE_ID]
  ,[BILLABILITY]
  ,[ContractClassType]
  , SUM([Day Hours Billed]) [Hours Billed SUM]
  , COUNT(*) AS [Hours Billed Day Count]
INTO [CONSUMPTION_ClinOpsFinance].[EmployeeTimeSheetHours_Utilization]
FROM [CONSUMPTION_ClinOpsFinance].[Employee_Day_Hours] 
GROUP BY EMPLOYEE_ID, [UtilizationDateId], [Date (Utilization)], Office_Country_name
  , [CadenceDepartmentName], Position, BillableFlag,[BILLABLE_ID], [BILLABILITY], [ContractClassType]

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[EmployeeTimeSheetHours_Utilization] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.Employee_Utilization_Hours') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].[Employee_Utilization_Hours];

WITH EmployeeAttendanceExpectedHours
AS
(
SELECT 
  [Employee_Id]
  ,[UtilizationDateId]
  ,[Date (Utilization)]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,[Position]
  ,[BILLABLE_ID]
  ,[BILLABILITY]
  ,[ContractClassType]
  ,CountEmployeeExpectedDays
  ,[Sum (Hours Expected, Daily)]
FROM [CONSUMPTION_ClinOpsFinance].[EmployeeAttendanceExpectedHoursUtilization_Monthly]
)
, EmployeeTimeSheetHours
AS
(
SELECT  EMPLOYEE_ID 
,[UtilizationDateId]
,[Date (Utilization)]
,Office_Country_name
,[CadenceDepartmentName]
,Position
,BillableFlag
,[BILLABLE_ID]
,[BILLABILITY]
,[ContractClassType]
,[Hours Billed SUM]
,[Hours Billed Day Count]
FROM [CONSUMPTION_ClinOpsFinance].[EmployeeTimeSheetHours_Utilization] 
WHERE BillableFlag = 1
)
SELECT COALESCE(TS.EMPLOYEE_ID, AEH.EMPLOYEE_ID) EMPLOYEE_ID
  ,COALESCE(TS.[UtilizationDateId], AEH.[UtilizationDateId]) [UtilizationDateId]
  ,COALESCE(TS.[Date (Utilization)], AEH.[Date (Utilization)]) [Date (Utilization)]
  ,COALESCE(TS.Office_Country_name, AEH.[PrimaGlobalCountryName]) [PrimaGlobalCountryName]
  ,COALESCE(TS.[CadenceDepartmentName], AEH.[CadenceDepartmentName]) [CadenceDepartmentName]
  ,COALESCE(TS.Position, AEH.Position) Position
  ,COALESCE(TS.[BILLABLE_ID], AEH.[BILLABLE_ID]) [BILLABLE_ID]
  ,COALESCE(TS.[BILLABILITY], AEH.[BILLABILITY]) [BILLABILITY]
  ,COALESCE(TS.[ContractClassType], AEH.[ContractClassType]) [ContractClassType]
  ,TS.[Hours Billed SUM]
  ,TS.[Hours Billed Day Count]
  ,AEH.[CountEmployeeExpectedDays] 
  ,AEH.[Sum (Hours Expected, Daily)] AS [Hours Expected SUM]
INTO [CONSUMPTION_ClinOpsFinance].[Employee_Utilization_Hours]
FROM EmployeeTimeSheetHours TS
FULL OUTER JOIN EmployeeAttendanceExpectedHours AEH
ON TS.EMPLOYEE_ID = AEH.EMPLOYEE_ID
  AND TS.[UtilizationDateId] = AEH.[UtilizationDateId]
  AND TS.[Date (Utilization)] = AEH.[Date (Utilization)]
  AND TS.Office_Country_name = AEH.[PrimaGlobalCountryName]
  AND TS.[CadenceDepartmentName] = AEH.[CadenceDepartmentName]
  AND TS.Position = AEH.Position
  AND TS.[BILLABLE_ID] = AEH.[BILLABLE_ID]
  AND TS.[ContractClassType] = AEH.[ContractClassType]

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[Employee_Utilization_Hours] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.[EmployeeAverageFTE_Monthly_Utilization_Hours]') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].EmployeeAverageFTE_Monthly_Utilization_Hours;

WITH FTE_Contract
AS
(
SELECT EMPLOYEE_ID
  ,[BOMDateID]
  ,[PrimaGlobalCountryName]
  ,[CadenceDepartmentName]
  ,Position
  ,[BILLABLE_ID]
  ,[ContractClassType]
  ,COUNT(*) AS EmployeeCount
  ,SUM(MonthlyFTEAggCount) As MonthlyFTEAggCount
  ,SUM(MonthlyFTEAggSUM) As MonthlyFTEAggSUM
  ,SUM(MonthlyFTEAggSUM) / CASE WHEN SUM(MonthlyFTEAggCount) = 0 THEN CAST(NULL AS FLOAT) ELSE SUM(MonthlyFTEAggCount) END AS [Monthly Average FTE]
  ,SUM(LastDayFTEAggCount) As LastDayFTEAggCount
  ,SUM(LastDayDailyFTEAggSUM) As LastDayDailyFTEAggSUM
  ,SUM(LastDayDailyFTEAggSUM)/ CASE WHEN SUM(LastDayFTEAggCount)  = 0 THEN CAST(NULL AS FLOAT) ELSE SUM(LastDayFTEAggCount) END AS [Monthly Average FTE, Last Day]
 FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
 GROUP BY EMPLOYEE_ID, [BOMDateID], [PrimaGlobalCountryName]
  ,[CadenceDepartmentName], Position, [BILLABLE_ID], [ContractClassType]
)
SELECT COALESCE(H.EMPLOYEE_ID, FTE.EMPLOYEE_ID) EMPLOYEE_ID
  ,COALESCE(H.[UtilizationDateId], FTE.[BOMDateId]) [BOMDateId]
  ,COALESCE(H.[PrimaGlobalCountryName], FTE.[PrimaGlobalCountryName]) [PrimaGlobalCountryName]
  ,COALESCE(H.[CadenceDepartmentName], FTE.[CadenceDepartmentName]) [CadenceDepartmentName]
  ,COALESCE(H.Position, FTE.Position) Position
  ,COALESCE(H.[BILLABLE_ID], FTE.[BILLABLE_ID]) [BILLABLE_ID]
  ,COALESCE(H.[ContractClassType], FTE.[ContractClassType]) [ContractClassType]
  ,H.[Hours Billed SUM]
  ,H.[Hours Billed Day Count]
  ,H.[CountEmployeeExpectedDays] 
  ,H.[Hours Expected SUM]
  ,FTE.[MonthlyFTEAggSUM]
  ,FTE.[MonthlyFTEAggCount]
  ,FTE.[Monthly Average FTE]
  ,FTE.[LastDayDailyFTEAggSUM]
  ,FTE.[LastDayFTEAggCount]
  ,FTE.[Monthly Average FTE, Last Day]
INTO [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours]
FROM [CONSUMPTION_ClinOpsFinance].[Employee_Utilization_Hours] H
FULL OUTER JOIN FTE_Contract FTE
ON H.EMPLOYEE_ID = FTE.EMPLOYEE_ID
  AND H.[UtilizationDateId] = FTE.[BOMDateId]
  AND H.[PrimaGlobalCountryName] = FTE.[PrimaGlobalCountryName]
  AND H.[CadenceDepartmentName] = FTE.[CadenceDepartmentName]
  AND H.Position = FTE.Position
  AND H.[BILLABLE_ID] = FTE.[BILLABLE_ID]
  AND H.[ContractClassType] = FTE.[ContractClassType]


SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[EmployeeAverageFTE_Monthly_Utilization_Hours] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

IF OBJECT_ID('CONSUMPTION_ClinOpsFinance.EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail]

SELECT EFUH.[EMPLOYEE_ID]
      ,DR.Rank
      ,EFUH.[BOMDateId]
      ,[dbo].[udfDateKeyToDate]([BOMDateId]) BOMDate
      ,EFUH.[PrimaGlobalCountryName]
      ,EFUH.[CadenceDepartmentName]
      ,EFUH.[Position]
      ,EFUH.[BILLABLE_ID]
      ,B.[BILLABILITY]
      ,EFUH.[ContractClassType]
      ,EFUH.[Hours Billed SUM]
      ,EFUH.[Hours Billed Day Count]
      ,EFUH.[CountEmployeeExpectedDays]
      ,EFUH.[Hours Expected SUM]
      ,EFUH.[MonthlyFTEAggSUM]
      ,EFUH.[MonthlyFTEAggCount]
      ,EFUH.[Monthly Average FTE]
      ,EFUH.[LastDayDailyFTEAggSUM]
      ,EFUH.[LastDayFTEAggCount]
      ,EFUH.[Monthly Average FTE, Last Day]
INTO [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail] 
FROM [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours] EFUH
JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
ON EFUH.[BOMDateID] = DR.DateID 
JOIN [CONSUMPTION_ClinOpsFinance].[Billability] B
ON EFUH.[BILLABLE_ID] = B.[BILLABLE_ID]

SELECT @MSG  = 'Completed load of CONSUMPTION_ClinOpsFinance.[EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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
 