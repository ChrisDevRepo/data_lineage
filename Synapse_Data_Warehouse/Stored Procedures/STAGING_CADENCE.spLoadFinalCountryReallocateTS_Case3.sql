CREATE PROC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_Case3] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadFinalCountryReallocateTS_Case3'
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



-- ************************
-- ***** USE CASE 3 *******
-- ************************
--Insert remaining Country Records for NO MATCH on Function/Function Country, Department/Function Country

INSERT INTO STAGING_CADENCE.FinalCountryReallocateTS
    SELECT
        CT.[Period Year]
		, CT.[Period Month]
		, CT.[Project Name]		
		, CT.[Project Currency Code]
		, CT.[Project Currency Name]	
		, CT.[Service]	
		, CT.[Task Code]
		, CT.[Task Name]			
		, CT.[Task Country Name]
		, CT.[Unit type]
		, CT.[Part Order Index]
		, CT.[Segment Order Index]
		, CT.[Function Code]
		, CT.[Function Name]		
		, CT.[Department]
		, CT.[Function Country Name]
		, CT.[Project Ref Id]
		, CT.[Archived Project Ref Id]
		, CT.[PRIMA Project Id]
		, CT.[Project Status]
		, CT.[Project Phase]
		, CT.[Is Deleted Task]
		, CT.[SUM Function Reconciliation Approved Units]
		,CT.[Task Period CADENCE Earned Value]
		,CT.[Task Reconciliation CADENCE Earned Value]
		,CT.[Task CADENCE Earned Value]
		,CT.[Task CADENCE Planned Unit Cost]
		, CT.[SUM Function Period TimeSheet Actual Total Hours]
		, CT.[SUM Task Period Approved Total Units]
		, CT.[SUM Function Planned Total Cost Adjusted]
		, CT.[SUM Function Planned Total Hours]
		, CT.[Function CurrentRate Adjusted]
		, CT.[SUM Task Planned Total Units]
		, CT.[SUM Task Approved Total Units]
		, CT.[SUM Function Period TimeSheet Actual Total Hours]	AS [SUM Function TimeSheet Actual Total Hours CT]
		, 0	AS [SUM Function TimeSheet Actual Total Hours NCT]
		, 'NOM' AS [RecordUpdateType]
		, 0 AS [CountByRecordUpdateType] 
		, 0 AS [Actual Hours (re-allocated)]
		, CT.[SUM Function Period TimeSheet Actual Total Hours] AS [Actual Total Hours (Allocated)]
		, CT.[SUM Function Period Actual Cost]
		, CT.[SUM Function Reconciliation Actual Cost]
		, CT.[SUM Function Actual Cost]
		, CT.[SUM Function Period Actual Cost] as [SUM Function Actual Cost CT]
		, 0 as [SUM Function Actual Cost NCT]
		, 0 AS [Actual Cost (re-allocated)]
		, CT.[SUM Function Period Actual Cost] 	AS [Actual Cost (Allocated)]
    FROM STAGING_CADENCE.CountryReallocateTS CT with (nolock)
    WHERE  NOT EXISTS ( 
						SELECT distinct *
        FROM STAGING_CADENCE.FinalCountryReallocateTS FTS with (nolock)
        WHERE 	CT.[Period Year]		= FTS.[Period Year]
            AND CT.[Period Month]		= FTS.[Period Month]
            AND CT.[Project Name]		= FTS.[Project Name]
            AND CT.[Task Code]			= FTS.[Task Code]
            AND CT.[Part Order Index]	= FTS.[Part Order Index]
            AND CT.[Segment Order Index]= FTS.[Segment Order Index]
            AND CT.[Function Code]		= FTS.[Function Code]
            AND CT.[Function Country Name]= FTS.[Function Country Name]
            AND FTS.[RecordUpdateType]	= 'FFC'
					  )
        and NOT EXISTS ( 
						SELECT distinct *
        FROM STAGING_CADENCE.FinalCountryReallocateTS FTS with (nolock)
        WHERE 	CT.[Period Year]		= FTS.[Period Year]
            AND CT.[Period Month]		= FTS.[Period Month]
            AND CT.[Project Name]		= FTS.[Project Name]
            AND CT.[Task Code]			= FTS.[Task Code]
            AND CT.[Part Order Index]	= FTS.[Part Order Index]
            AND CT.[Segment Order Index]= FTS.[Segment Order Index]
            AND CT.[Department]			= FTS.[Department]
            AND CT.[Function Country Name]= FTS.[Function Country Name]
            AND FTS.[RecordUpdateType]	= 'DFC'
					  )




EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[FinalCountryReallocateTS] (Case-3) in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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