CREATE PROC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_NoCountry] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadFinalCountryReallocateTS_NoCountry'
DECLARE @ProcName NVARCHAR(128) = '[STAGING_CADENCE].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'Cadence-ETL'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0
  ,@Count  BIGINT = 0
  ,@ProcessingTime DATETIME = GETDATE();

BEGIN TRY

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL




-- Fianlly inset remaining 'No Country' records after processing all other reallocations rules ([Task Country Name] = 'No Country')
INSERT INTO STAGING_CADENCE.FinalCountryReallocateTS
    SELECT
        NCT.[Period Year]
		, NCT.[Period Month]
		, NCT.[Project Name]
		, NCT.[Project Currency Code]
		, NCT.[Project Currency Name]			
		, NCT.[Service]		
		, NCT.[Task Code]
		, NCT.[Task Name]			
		, NCT.[Task Country Name]
		, NCT.[Unit type]
		, NCT.[Part Order Index]
		, NCT.[Segment Order Index]
		, NCT.[Function Code]
		, NCT.[Function Name]		
		, NCT.[Department]
		, NCT.[Function Country Name]
		, NCT.[Project Ref Id]
		, NCT.[Archived Project Ref Id]
		, NCT.[PRIMA Project Id]
		, NCT.[Project Status]
		, NCT.[Project Phase]
		, NCT.[Is Deleted Task]
		, NCT.[SUM Function Reconciliation Approved Units]
		, NCT.[Task Period CADENCE Earned Value]
		, NCT.[Task Reconciliation CADENCE Earned Value]
		, NCT.[Task CADENCE Earned Value]
		, NCT.[Task CADENCE Planned Unit Cost]
		, NCT.[SUM Function Period TimeSheet Actual Total Hours]
		, NCT.[SUM Task Period Approved Total Units]
		, NCT.[SUM Function Planned Total Cost Adjusted]
		, NCT.[SUM Function Planned Total Hours]
		, NCT.[Function CurrentRate Adjusted]
		, NCT.[SUM Task Planned Total Units]
		, NCT.[SUM Task Approved Total Units]
		, 0	AS [SUM Function TimeSheet Actual Total Hours CT]
		, NCT.[SUM Function Period TimeSheet Actual Total Hours]	AS [SUM Function TimeSheet Actual Total Hours NCT]
		, 'NC' AS [RecordUpdateType]
		, 0 AS [CountByRecordUpdateType] 
		, 0 AS [Actual Hours (re-allocated)]
		, NCT.[SUM Function Period TimeSheet Actual Total Hours] AS [Actual Total Hours (Allocated)]
		, NCT.[SUM Function Period Actual Cost]
		, NCT.[SUM Function Reconciliation Actual Cost]
		, NCT.[SUM Function Actual Cost]
		, 0										AS [SUM Function Actual Cost CT]
		, NCT.[SUM Function Period Actual Cost]		AS [SUM Function Actual Cost NCT]
		, 0										AS [Actual Cost (re-allocated)]
		, NCT.[SUM Function Period Actual Cost]		AS [Actual Cost (Allocated)]		
    FROM STAGING_CADENCE.NoCountryReallocateTS NCT with (nolock)





EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[FinalCountryReallocateTS] (NoCountry) in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG + ' (Record count: ' + CAST(@Count AS VARCHAR(10)) + ')' ;
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL


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