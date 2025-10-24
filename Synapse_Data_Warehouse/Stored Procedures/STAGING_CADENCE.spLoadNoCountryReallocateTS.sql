CREATE PROC [STAGING_CADENCE].[spLoadNoCountryReallocateTS] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadNoCountryReallocateTS'
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

IF OBJECT_ID('STAGING_CADENCE.NoCountryReallocateTS') IS NOT NULL
TRUNCATE TABLE  [STAGING_CADENCE].[NoCountryReallocateTS];



-- Filter and store all the records with Reallocate TC = 'No Cuntry' and SUM Function TimeSheet Actual Total Hours more than 0


insert 	INTO STAGING_CADENCE.NoCountryReallocateTS
    SELECT 
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
		, SUM( [SUM Function Reconciliation Approved Units]) AS  [SUM Function Reconciliation Approved Units]
		, SUM([Task Period CADENCE Earned Value]) AS  [Task Period CADENCE Earned Value]
		, SUM([Task Reconciliation CADENCE Earned Value]) AS  [Task Reconciliation CADENCE Earned Value]
		, SUM([Task CADENCE Earned Value]) AS  [Task CADENCE Earned Value]
		, SUM([Task CADENCE Planned Unit Cost]) AS  [Task CADENCE Planned Unit Cost]
		, SUM([SUM Function Planned Total Cost Adjusted]) AS  [SUM Function Planned Total Cost Adjusted]
		, SUM([SUM Function Planned Total Hours]) AS  [SUM Function Planned Total Hours]
		, SUM([Function CurrentRate Adjusted]) AS  [Function CurrentRate Adjusted]
		, SUM([SUM Task Planned Total Units]) AS  [SUM Task Planned Total Units]
		, SUM([SUM Task Period Approved Total Units]) AS  [SUM Task Period Approved Total Units]
		, SUM([SUM Task Reconciliation Approved Total Units]) AS  [SUM Task Reconciliation Approved Total Units]
		, SUM([SUM Task Approved Total Units]) AS  [SUM Task Approved Total Units]
		, SUM([SUM Function Period TimeSheet Actual Total Hours]) AS  [SUM Function Period TimeSheet Actual Total Hours]
		, SUM([SUM Function Reconciliation TimeSheet Actual Total Hours]) AS  [SUM Function Reconciliation TimeSheet Actual Total Hours]
		, SUM([SUM Function Actual Hours]) AS  [SUM Function TimeSheet Actual Total Hours]
		, SUM([SUM Function Period Actual Cost]) AS  [SUM Function Period Actual Cost]
		, SUM([SUM Function Reconciliation Actual Cost]) AS  [SUM Function Reconciliation Actual Cost]
		, SUM([SUM Task Reconciliation Actual Cost]) AS  [SUM Task Reconciliation Actual Cost]
		, SUM([SUM Function Actual Cost]) AS  [SUM Function Actual Cost]


    FROM [STAGING_CADENCE].[TaskAndFunctionData] with (nolock)
    WHERE [Task Country Name] = 'No Country'
    GROUP BY 
		 [Period Year]
		,[Period Month]
		,[Project Name]
		,[Project Currency Code]
		,[Project Currency Name]	
		,[Service]
		,[Task Code]
		,[Task Name]
		,[Task Country Name]
		,[Unit type]
		,[Part Order Index]
		,[Segment Order Index]
		,[Function Code]
		,[Function Name]
		,[Department]
		,[Function Country Name]
		,[Project Ref Id]
		,[Archived Project Ref Id]
		,[PRIMA Project Id]
		,[Project Status]
		,[Project Phase]
		,[Is Deleted Task]
	


EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[NoCountryReallocateTS] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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