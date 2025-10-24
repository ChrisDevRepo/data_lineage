CREATE PROC [STAGING_CADENCE].[spLoadCountryReallocateTS] AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCountryReallocateTS'
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

IF OBJECT_ID('STAGING_CADENCE.CountryReallocateTS') IS NOT NULL
TRUNCATE TABLE  [STAGING_CADENCE].[CountryReallocateTS];


-- Filter and store all the records with Reallocate TC <> 'No Cuntry'

insert INTO STAGING_CADENCE.CountryReallocateTS
    SELECT --distinct
		[Period Year]
		, [Period Month]
		, [Project Name]
		, [Project Currency Code]
		, [Project Currency Name]
		, [Service]
		, [Task Code]
		, [Task Name]
		, [Task Country Name]
		, [Unit type]
		, [Part Order Index]
		, [Segment Order Index]
		, [Function Code]
		, [Function Name]
		, [Department]
		, [Function Country Name]
		, [Project Ref Id]
		, [Archived Project Ref Id]
		, [PRIMA Project Id]
		, [Project Status]
		, [Project Phase]
		, [Is Deleted Task]
		, [SUM Function Reconciliation Approved Units]
		, [Task Period CADENCE Earned Value]
		, [Task Reconciliation CADENCE Earned Value]
		, [Task CADENCE Earned Value]
		, [Task CADENCE Planned Unit Cost]
		, [SUM Function Planned Total Cost Adjusted]
		, [SUM Function Planned Total Hours]
		, [Function CurrentRate Adjusted]
		, [SUM Task Planned Total Units]
		, [SUM Task Period Approved Total Units]
		, [SUM Task Reconciliation Approved Total Units]
		, [SUM Task Approved Total Units]
		, [SUM Function Period TimeSheet Actual Total Hours]
		, [SUM Function Reconciliation TimeSheet Actual Total Hours]
		, [SUM Function Actual Hours]
		, [SUM Function Period Actual Cost]
		, [SUM Function Reconciliation Actual Cost]
		, [SUM Task Reconciliation Actual Cost]
		, [SUM Function Actual Cost]

    FROM [STAGING_CADENCE].[TaskAndFunctionData] with (nolock)
    WHERE [Task Country Name] <> 'No Country' 
	


EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[CountryReallocateTS] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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