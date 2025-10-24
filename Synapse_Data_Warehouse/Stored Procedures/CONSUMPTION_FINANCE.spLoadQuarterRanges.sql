CREATE PROC [CONSUMPTION_FINANCE].[spLoadQuarterRanges] AS

BEGIN

SET NOCOUNT ON


DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadQuarterRanges'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_FINANCE].[' + @ProcShortName + ']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'FinanceDaysToPay'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY


truncate table [CONSUMPTION_FINANCE].[QuarterRanges]

insert into [CONSUMPTION_FINANCE].[QuarterRanges]

--Adding data for Last 4 Quarters
select *, 'Last 4 Quarters' as [FilterValue],
    'spLoadQuarterRanges' as [CreatedBy],
    'spLoadQuarterRanges' as [UpdatedBy],
    getdate() as [CreatedAt],
    getdate() as [UpdatedAt]
FROM
(
    select  
        YearQuarter, Year, QuarterOfTheYear, FirstDayOfQuarter, LastDayOfQuarter, 
        ROW_NUMBER() OVER(ORDER BY AA.[Year] desc, AA.[QuarterOfTheYear] desc) as QuarterNumber
    FROM
    (
        select CONCAT(dod.Year, '-Q', dod.[Quarter]) as YearQuarter, dod.Year, dod.[Quarter] as QuarterOfTheYear, dod.FirstDayOfQuarter, dod.LastDayOfQuarter 
        from [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Summary] f
            left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
        where f.[DimDocumentDateKey] is not null and f.DaysToPay is not null
        and dod.LastDayOfQuarter < FORMAT(GetDate(), 'd', 'en-US') 
) AA

group by  AA.yearQuarter, AA.Year, AA.QuarterOfTheYear, AA.FirstDayOfQuarter, AA.LastDayOfQuarter 
) DD
where DD.QuarterNumber <= 4
--order by DD.[Year] desc, DD.[QuarterOfTheYear] desc


UNION

--Adding data for Last 8 Quarters
select *, 'Last 8 Quarters' as [FilterValue],
    'spLoadQuarterRanges' as [CreatedBy],
    'spLoadQuarterRanges' as [UpdatedBy],
    getdate() as [CreatedAt],
    getdate() as [UpdatedAt]
FROM
(
    select  
        YearQuarter, Year, QuarterOfTheYear, FirstDayOfQuarter, LastDayOfQuarter, 
        ROW_NUMBER() OVER(ORDER BY AA.[Year] desc, AA.[QuarterOfTheYear] desc) as QuarterNumber
    FROM
    (
        select CONCAT(dod.Year, '-Q', dod.[Quarter]) as YearQuarter, dod.Year, dod.[Quarter] as QuarterOfTheYear, dod.FirstDayOfQuarter, dod.LastDayOfQuarter 
        from [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Summary] f
            left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
        where f.[DimDocumentDateKey] is not null and f.DaysToPay is not null
        and dod.LastDayOfQuarter < FORMAT(GetDate(), 'd', 'en-US') 
) AA

group by  AA.yearQuarter, AA.Year, AA.QuarterOfTheYear, AA.FirstDayOfQuarter, AA.LastDayOfQuarter 
) DD
where DD.QuarterNumber <= 8
--order by DD.[Year] desc, DD.[QuarterOfTheYear] desc


UNION

--Adding data for All Quarters
select *, 'All' as [FilterValue],
    'spLoadQuarterRanges' as [CreatedBy],
    'spLoadQuarterRanges' as [UpdatedBy],
    getdate() as [CreatedAt],
    getdate() as [UpdatedAt]
FROM
(
    select  
        YearQuarter, Year, QuarterOfTheYear, FirstDayOfQuarter, LastDayOfQuarter, 
        ROW_NUMBER() OVER(ORDER BY AA.[Year] desc, AA.[QuarterOfTheYear] desc) as QuarterNumber
    FROM
    (
        select CONCAT(dod.Year, '-Q', dod.[Quarter]) as YearQuarter, dod.Year, dod.[Quarter] as QuarterOfTheYear, dod.FirstDayOfQuarter, dod.LastDayOfQuarter 
        from [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Summary] f
            left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
        where f.[DimDocumentDateKey] is not null and f.DaysToPay is not null
        and dod.LastDayOfQuarter < FORMAT(GetDate(), 'd', 'en-US') 
    ) AA

    group by  AA.yearQuarter, AA.Year, AA.QuarterOfTheYear, AA.FirstDayOfQuarter, AA.LastDayOfQuarter 
) DD


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
