CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadFactLaborCostForEarnedValue_Post] AS
BEGIN

SET NOCOUNT ON

BEGIN TRY

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadFactLaborCostForEarnedValue_Post'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0


DECLARE @Today Date =  CONVERT(Date,  GetDate(), 101) 
DECLARE @CutOffDayOfTheMonth int = COALESCE((select max(day(AA.[CloseDate])) 
                                                from [CONSUMPTION_ClinOpsFinance].[DateRangeMonthClose_Config] AA
                                                where year(AA.[CloseDate]) = year(@Today)
                                                and month(AA.[CloseDate]) = month(@Today))
                                            , 15) 

DECLARE @CurrentMonth int = (select Month(@Today))
DECLARE @CurrentYear int = (select Year(@Today))
DECLARE @CopyFromMonth int 

if object_id(N'tempdb..#ForecastingConfig') is not null
begin drop table #ForecastingConfig; end

    select 
        BB.Date as [CopyForTheDate], Year(BB.Date) as [CopyForTheYear], Month(BB.Date) as [CopyForTheMonth],
        DateFromParts((@CurrentYear + [CopyFromyearOffset]), [CopyFromMonth], 1) as [CopyFromTheDate], (@CurrentYear + [CopyFromyearOffset]) as [CopyFromYear], [CopyFromMonth], 
        @Today as [Today] 
    into #ForecastingConfig
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




 truncate table  [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post]
 INSERT into [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post]
 	(
        [CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
       ,[Account]
       ,[AccountName]
       ,[SubAccountName]
       ,[Company]
       ,[Region]
       ,[Country]
       ,[Office]
       ,[CompanyDesc]
       ,[DeptID]
       ,[DeptNameLong]
       ,[DeptNameShort]
       ,[DeptNameMed]
       ,[PrimaGlobalCountryId]
       ,[PrimaGlobalCountryName]
       ,[PrimaDepartmentId]
       ,[PrimaDepartmentName]
       ,[CadenceDepartmentId]
       ,[CadenceDepartmentName]
       ,[Year]
       ,[Month]
       ,[Currency]
       ,[AmountYTD]
       ,[AmountPTD]
       ,[BillableFlag]
       ,[Vtyp]
 	  ,[BomDateId]
       ,[KEY]
       ,[KEY_wo_Currency]
 	)

SELECT 
       ju.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
      ,lc.[Account]
      ,lc.[AccountName]
      ,lc.[SubAccountName]
      ,lc.[Company]
      ,lc.[Region]
      ,lc.[Country]
      ,lc.[Office]
      ,lc.[CompanyDesc]
      ,lc.[DeptID]
      ,lc.[DeptNameLong]
      ,lc.[DeptNameShort]
      ,lc.[DeptNameMed]
      ,lc.[PrimaGlobalCountryId]
      ,lc.[PrimaGlobalCountryName]
      ,lc.[PrimaDepartmentId]
      ,lc.[PrimaDepartmentName]
      ,lc.[CadenceDepartmentId]
      ,lc.[CadenceDepartmentName]
      ,lc.[Year]
      ,lc.[Month]
      ,lc.[Currency]
      ,-1*[AmountYTD] as [AmountYTD]
      ,-1*[AmountPTD] as [AmountPTD]
      ,lc.[BillableFlag]
      ,lc.[Vtyp]

	  ,[dbo].[udfDateToDateKey](DateFromParts(lc.[Year], lc.[Month], 1)) as [BomDateId]
	  ,Concat(lc.[PrimaGlobalCountryName], lc.[PrimaDepartmentName], lc.[Year], lc.[Month], lc.[Currency]) as [KEY]
	  ,Concat(lc.[PrimaGlobalCountryName], lc.[PrimaDepartmentName], lc.[Year], lc.[Month]) as [KEY_wo_Currency]
     
FROM [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] lc
left join [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] ju on 
							Coalesce(lc.[PrimaGlobalCountryName], '') = Coalesce(ju.[PrimaGlobalCountryName], '')	
						and Coalesce(lc.[PrimaDepartmentName]   , '') = Coalesce(ju.[Department]			, '')
						and lc.[Year]								  = ju.[Year]
						and lc.[Month]								  = ju.[Month]
						and lc.[Currency]							  = ju.[Currency]
						and ju.[TableName]							  = 'FactLaborCostForEarnedValue'
where DateFromParts(lc.[Year], lc.[Month], 1) <= COALESCE((select min(CopyFromTheDate) from #ForecastingConfig), CONVERT(date, dateadd(d,-(day(getdate())),getdate()),101))



UNION ALL
select
       ju.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey], DD.*
FROM
    (
    select
       lc.[Account]
      ,lc.[AccountName]
      ,lc.[SubAccountName]
      ,lc.[Company]
      ,lc.[Region]
      ,lc.[Country]
      ,lc.[Office]
      ,lc.[CompanyDesc]
      ,lc.[DeptID]
      ,lc.[DeptNameLong]
      ,lc.[DeptNameShort]
      ,lc.[DeptNameMed]
      ,lc.[PrimaGlobalCountryId]
      ,lc.[PrimaGlobalCountryName]
      ,lc.[PrimaDepartmentId]
      ,lc.[PrimaDepartmentName]
      ,lc.[CadenceDepartmentId]
      ,lc.[CadenceDepartmentName]
      ,[CC].[CopyForTheYear] as [Year]
      ,format([CC].[CopyForTheMonth], '00') as [Month]
      ,lc.[Currency]
      ,-1*[AmountYTD] as [AmountYTD]
      ,-1*[AmountPTD] as [AmountPTD]
      ,lc.[BillableFlag]
      ,lc.[Vtyp]

	  ,[dbo].[udfDateToDateKey](DateFromParts([CC].[CopyForTheYear], [CC].[CopyForTheMonth], 1)) as [BomDateId]
	  ,Concat(lc.[PrimaGlobalCountryName], lc.[PrimaDepartmentName], FORMAT([CC].[CopyForTheYear], '00'), FORMAT([CC].[CopyForTheMonth], '00'), lc.[Currency]) as [KEY]
	  ,Concat(lc.[PrimaGlobalCountryName], lc.[PrimaDepartmentName], FORMAT([CC].[CopyForTheYear], '00'), FORMAT([CC].[CopyForTheMonth], '00')) as [KEY_wo_Currency]
     
    from [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] lc
		inner join #ForecastingConfig CC  on lc.[Year] = [CC].[CopyFromYear] and lc.[Month] = [CC].[CopyFromMonth]
    ) DD
left join [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] ju on 
							Coalesce([DD].[PrimaGlobalCountryName], '') = Coalesce([ju].[PrimaGlobalCountryName], '')	
						and Coalesce([DD].[PrimaDepartmentName], '')    = Coalesce([ju].[Department], '')
						and [DD].[Year]									= [ju].[Year]
						and [DD].[Month]								= [ju].[Month]
						and [DD].[Currency]								= [ju].[Currency]
						and [ju].[TableName]							= 'FactLaborCostForEarnedValue'



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


