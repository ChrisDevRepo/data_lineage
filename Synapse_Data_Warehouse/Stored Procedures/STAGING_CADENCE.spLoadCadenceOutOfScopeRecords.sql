CREATE PROC [STAGING_CADENCE].[spLoadCadenceOutOfScopeRecords] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCadenceOutOfScopeRecords'
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

IF OBJECT_ID('STAGING_CADENCE.CadenceOutOfScopeRecords') IS NOT NULL
TRUNCATE TABLE  [STAGING_CADENCE].[CadenceOutOfScopeRecords];


-- Filter records based on the [Layer] ='function-location' and [Service Code] = 'OOS_SERVICE'

INSERT INTO [STAGING_CADENCE].[CadenceOutOfScopeRecords]
        (
        [Project ref Id]
        ,[Project Name]
        ,[Opportunity Id]
        ,[Archived project ref Id]
        ,[PRIMA Project Id]
        ,[Project Status]
        ,[Project Phase]
        ,[Project Currency Code]
        ,[Project Currency Name]
        ,[CHF Contract Exchange Rate]
        ,[USD Contract Exchange Rate]
        ,[EUR Contract Exchange Rate]
        ,[GBP Contract Exchange Rate]
        ,[Period Name]
        ,[Period Year]
        ,[Period Month]
        ,[Is Closed Period]
        ,[Service code]
        ,[Service Name]
        ,[Department Id]
        ,[Department Name]
        ,[Task Code]
        ,[Task Name]
        ,[Tracking Task Code]
        ,[Tracking Task Name]
        ,[Is Deleted Task]
        ,[Part Name]
        ,[Part Order Index]
        ,[Segment Order Index]
        ,[Task Country Code]
        ,[Task Country Name]
        ,[Task Region Code]
        ,[Task Region Name]
        ,[Function Code]
        ,[Function Name]
        ,[Function Location Code]
        ,[Function Location Name]
        ,[Function Region Code]
        ,[Function Region Name]
        ,[Actual Hours]
        ,[Rate]
        ,[Planned Total Cost]
        ,[Planned Total Hours]
        ,[Reconciliation Actual Hours]
        ,[Reconciliation Actual Cost]
        ,[Period Actual Hours]
        ,[Period Actual Cost]
        ,[Actual Cost]
        ,[Reconciliation Approved Units]
	    ,[Period CADENCE Earned Value]
	    ,[Reconciliation CADENCE Earned Value]
	    ,[CADENCE Earned Value]
	    ,[CADENCE Planned Unit Cost]
        ,[Layer]
        ,[CREATED_AT]
        ,[UPDATED_AT]
        )
    SELECT
        pj.[Project ref Id]
      , pj.[Project Name]
      , [Opportunity Id]
      , [Archived project ref Id]
      , [PRIMA Project Id]
      , [Project Status]
      , [Project Phase]
      , [Project Currency Code]
      , [Project Currency Name]
      , [CHF Contract Exchange Rate]
      , [USD Contract Exchange Rate]
      , [EUR Contract Exchange Rate]
      , [GBP Contract Exchange Rate]
      , [Period Name]
      , [Period Year]
      , [Period Month]
      , [Is Closed Period]
      , [Service code]
      , [Service Name]
      , [Department Id]
      , [Department Name]
      , [Task Code]
      , [Task Name]
      , [Tracking Task Code]
      , [Tracking Task Name]
      , [Is Deleted Task]
      , [Part Name]
      , [Part Order Index]
      , [Segment Order Index]
      , [Task Country Code]
      , [Task Country Name]
      , [Task Region Code]
      , [Task Region Name]
      , [Function Code]
      , [Function Name]
      , [Function Location Code]
      , [Function Location Name]
      , [Function Region Code]
      , [Function Region Name]
      , [Actual Hours]
      --,[dbo].[udfDivide]([Actual Cost], [Actual Hours]) AS [Rate]
	  , [Rate]
      , [Planned Total Cost]
      , [Planned Total Hours]
      , [Reconciliation Actual Hours]
      , [Reconciliation Actual Cost]
      , [Period Actual Hours]
      , [Period Actual Cost]
      , [Actual Cost]
      ,[Reconciliation Approved Units]
	  ,[Period CADENCE Earned Value]
	  ,[Reconciliation CADENCE Earned Value]
	  , [CADENCE Earned Value]
	  , [CADENCE Planned Unit Cost]
      , [Layer]
      , [Date Created]
      , [Date Modified]
    from [STAGING_CADENCE].[CadenceExtract] e with (nolock)
    inner join (
                select * FROM
                (
                select *,
                RANK() OVER (PARTITION BY [Project Ref Id] ORDER BY [Project Ref Id], [LastPeriod] DESC) AS RankResult
                FROM
                    (
                        select 
                            [Project Ref Id],
                            [project name], 
                            min(datefromparts([Period Year], [Period Month], 1)) as FirstPeriod,
                            max(datefromparts([Period Year], [Period Month], 1)) as LastPeriod
                        from  [STAGING_CADENCE].[CadenceExtract]
                        group by [Project Ref Id],[project name]
                    ) CC 
                ) DD
                where RankResult = 1
    ) pj on e.[Project Ref Id] = pj.[Project Ref Id]		
    where [Layer] ='function-location'
        and [Service Code] = 'OOS_SERVICE'
        and [Is Closed Period] = 1



EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[CadenceOutOfScopeRecords] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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