CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudget_LaborCost_PrimaUtilization_Junc] AS
BEGIN

SET ANSI_NULLS ON

SET QUOTED_IDENTIFIER ON

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCadenceBudget_LaborCost_PrimaUtilization_Junc'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0


BEGIN TRY


truncate table [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaUtilization_Junc]


DECLARE @Today Date =  CONVERT(Date,  GetDate(), 101) 
DECLARE @CutOffDayOfTheMonth int = 15
DECLARE @CurrentMonth int = (select Month(@Today))
DECLARE @CurrentYear int = (select Year(@Today))
DECLARE @CopyFromMonth int 



insert into [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaUtilization_Junc]
	(
		 [KEY]
		,[KEY_wo_Currency]
		,[PrimaGlobalCountryName]
		,[Department]
		,[BomDateId]
		,[Date]
		,[Year]
		,[Month]
		,[Currency]
		,[TableName]
	)
select distinct
	 Concat(Coalesce(cb.[PrimaGlobalCountryName], ''), Coalesce(cb.[PrimaDepartmentName], ''), cb.[Year], FORMAT(cb.[Month], '00'), cb.[Currency]) as [KEY]
	,Concat(Coalesce(cb.[PrimaGlobalCountryName], ''), Coalesce(cb.[PrimaDepartmentName], ''), cb.[Year], FORMAT(cb.[Month], '00')) as [KEY_wo_Currency]
	,cb.[PrimaGlobalCountryName] as [Country]
	,cb.[PrimaDepartmentName] as [Department]
	,[dbo].[udfDateToDateKey](DateFromParts(cb.[Year], cb.[Month], 1)) as [BomDateId]
	,DateFromParts(cb.[Year], cb.[Month], 1) as [Date]
	,cb.[Year]
	,cb.[Month]
	,cb.[Currency]
	,'CadenceBudgetData' as [TableName]
from [CONSUMPTION_POWERBI].[CadenceBudgetData] cb

UNION
select distinct
	  Concat(Coalesce(eu.[OFFICE_COUNTRY_NAME], ''), Coalesce(eu.[DEPARTMENT], ''), Year(eu.[Date]), FORMAT(Month(eu.[Date]), '00'), 'JUNC') as [KEY]
	, Concat(Coalesce(eu.[OFFICE_COUNTRY_NAME], ''), Coalesce(eu.[DEPARTMENT], ''), Year(eu.[Date]), FORMAT(Month(eu.[Date]), '00')) as [KEY_wo_Currency]
	, eu.[OFFICE_COUNTRY_NAME] as [Country]
	, eu.[DEPARTMENT] as [Department]
	,[dbo].[udfDateToDateKey](DateFromParts(Year(eu.[Date]), Month(eu.[Date]), 1)) as [BomDateId]
	, DateFromParts(Year(eu.[Date]), Month(eu.[Date]), 1) as [Date]
	, Year(eu.[Date])
	, Month(eu.[Date])
	, 'JUNC' as [Currency]
	, 'EmployeeUtilization' as [TableName]
from  [CONSUMPTION_POWERBI].[EmployeeUtilization] eu

UNION
select distinct
	  Concat(Coalesce(lc.[PrimaGlobalCountryName], ''), Coalesce(lc.[PrimaDepartmentName], ''), lc.[Year],  lc.[Month], lc.[Currency]) as [KEY]
	, Concat(Coalesce(lc.[PrimaGlobalCountryName], ''), Coalesce(lc.[PrimaDepartmentName], ''), lc.[Year],  lc.[Month]) as [KEY_wo_Currency]
	, lc.[PrimaGlobalCountryName] as [Country]
	, lc.[PrimaDepartmentName] as [Department]
	, [dbo].[udfDateToDateKey](DateFromParts(lc.[Year], lc.[Month], 1)) as [BomDateId]
	, DateFromParts(lc.[Year], lc.[Month], 1) as [Date]
	, lc.[Year]
	, lc.[Month]
	, lc.[Currency]
	, 'FactLaborCostForEarnedValue' as [TableName]
from  [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] lc

UNION
select distinct
	  Concat(Coalesce(lc.[PrimaGlobalCountryName], ''), Coalesce(lc.[PrimaDepartmentName], ''), [CC].[CopyForTheYear], format([CC].[CopyForTheMonth], '00'), lc.[Currency]) as [KEY]
	, Concat(Coalesce(lc.[PrimaGlobalCountryName], ''), Coalesce(lc.[PrimaDepartmentName], ''), [CC].[CopyForTheYear], format([CC].[CopyForTheMonth], '00')) as [KEY_wo_Currency]
	, lc.[PrimaGlobalCountryName] as [Country]
	, lc.[PrimaDepartmentName] as [Department]
	,[dbo].[udfDateToDateKey](DateFromParts([CC].[CopyForTheYear], [CC].[CopyForTheMonth], 1)) as [BomDateId]
	, DateFromParts([CC].[CopyForTheYear], [CC].[CopyForTheMonth], 1) as [Date]
	, [CC].[CopyForTheYear]
	, [CC].[CopyForTheMonth]
	, lc.[Currency]
	, 'FactLaborCostForEarnedValue' as [TableName]
from  [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] lc
inner join     
    (
        select 
        BB.Date as [CopyForTheDate], Year(BB.Date) as [CopyForTheYear], Month(BB.Date) as [CopyForTheMonth],
        DateFromParts((@CurrentYear + [CopyFromyearOffset]), [CopyFromMonth], 1) as [CopyFromTheDate], (@CurrentYear + [CopyFromyearOffset]) as [CopyFromYear], [CopyFromMonth], 
        @Today as [Today] 
            from 
            (
                Select 1 as [SeqNumber], 1 as [CurrentMonth], 'January' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 9 as [CopyFromMonth], 'September' as [CopyFromMonthName], -1 as [CopyFromyearOffset] UNION
                Select 2 as [SeqNumber], 1 as [CurrentMonth], 'January' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], NULL as [CopyFromMonth], NULL as [CopyFromMonthName], -1 as [CopyFromyearOffset] UNION
                Select 3 as [SeqNumber], 2 as [CurrentMonth], 'February' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 12 as [CopyFromMonth], 'December' as [CopyFromMonthName], -1 as [CopyFromyearOffset] UNION
                Select 4 as [SeqNumber], 2 as [CurrentMonth], 'February' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 12 as [CopyFromMonth], 'December' as [CopyFromMonthName], -1 as [CopyFromyearOffset] UNION
                Select 5 as [SeqNumber], 3 as [CurrentMonth], 'March' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 12 as [CopyFromMonth], 'December' as [CopyFromMonthName], -1 as [CopyFromyearOffset] UNION
                Select 6 as [SeqNumber], 3 as [CurrentMonth], 'March' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 12 as [CopyFromMonth], 'December' as [CopyFromMonthName], -1 as [CopyFromyearOffset] UNION
                Select 7 as [SeqNumber], 4 as [CurrentMonth], 'April' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 12 as [CopyFromMonth], 'December' as [CopyFromMonthName], -1 as [CopyFromyearOffset] UNION
                Select 8 as [SeqNumber], 4 as [CurrentMonth], 'April' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], NULL as [CopyFromMonth], NULL as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 9 as [SeqNumber], 5 as [CurrentMonth], 'May' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 3 as [CopyFromMonth], 'March' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 10 as [SeqNumber], 5 as [CurrentMonth], 'May' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 3 as [CopyFromMonth], 'March' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 11 as [SeqNumber], 6 as [CurrentMonth], 'June' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 3 as [CopyFromMonth], 'March' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 12 as [SeqNumber], 6 as [CurrentMonth], 'June' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 3 as [CopyFromMonth], 'March' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 13 as [SeqNumber], 7 as [CurrentMonth], 'July' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 3 as [CopyFromMonth], 'March' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 14 as [SeqNumber], 7 as [CurrentMonth], 'July' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], NULL as [CopyFromMonth], NULL as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 15 as [SeqNumber], 8 as [CurrentMonth], 'August' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 6 as [CopyFromMonth], 'June' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 16 as [SeqNumber], 8 as [CurrentMonth], 'August' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 6 as [CopyFromMonth], 'June' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 17 as [SeqNumber], 9 as [CurrentMonth], 'September' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 6 as [CopyFromMonth], 'June' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 18 as [SeqNumber], 9 as [CurrentMonth], 'September' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 6 as [CopyFromMonth], 'June' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 19 as [SeqNumber], 10 as [CurrentMonth], 'October' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 6 as [CopyFromMonth], 'June' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 20 as [SeqNumber], 10 as [CurrentMonth], 'October' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], NULL as [CopyFromMonth], NULL as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 21 as [SeqNumber], 11 as [CurrentMonth], 'November' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 9 as [CopyFromMonth], 'September' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 22 as [SeqNumber], 11 as [CurrentMonth], 'November' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 9 as [CopyFromMonth], 'September' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 23 as [SeqNumber], 12 as [CurrentMonth], 'December' as [CurrentMonthName], 'Yes' as [IsBeforeCutOffDate], 9 as [CopyFromMonth], 'September' as [CopyFromMonthName], 0 as [CopyFromyearOffset] UNION
                Select 24 as [SeqNumber], 12 as [CurrentMonth], 'December' as [CurrentMonthName], 'No' as [IsBeforeCutOffDate], 9 as [CopyFromMonth], 'September' as [CopyFromMonthName], 0 as [CopyFromyearOffset]

            ) AA,
            (select * from [dbo].[DimDate] where DayOfMonth = 1 and Date >= dateadd(MONTH, -4, @Today) and Date < DATEADD(month, DATEDIFF(month, 0, @Today), 0)) BB 
        where [CurrentMonth] = @CurrentMonth
        and [IsBeforeCutOffDate] = case when day(@Today) <= @CutOffDayOfTheMonth then 'Yes' else 'No' END
        and AA.[CopyFromMonth] is not NULL
        and BB.Date > DATEFROMPARTS((@CurrentYear + [CopyFromyearOffset]), [CopyFromMonth], 1)
        and BB.Date <  @Today
    ) CC  on lc.Year = [CC].[CopyFromYear] and lc.[Month] = [CC].[CopyFromMonth]


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


