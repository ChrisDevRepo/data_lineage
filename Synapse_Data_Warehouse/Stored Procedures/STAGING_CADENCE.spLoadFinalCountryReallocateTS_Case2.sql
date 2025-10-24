CREATE PROC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_Case2] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadFinalCountryReallocateTS_Case2'
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
-- ***** USE CASE 2 *******
-- ************************

--Insert Records matching on Department/Function Country
--Reallocate [SUM Function Timesheet Actual Total Hours] and [SUM Function Actual Cost] where Task Country = “No Country” to Country specific records.

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
		, NCT.[SUM Function Period TimeSheet Actual Total Hours]	AS [SUM Function TimeSheet Actual Total Hours NCT]
		, 'DFC' AS [RecordUpdateType]
		, FCT.[CountByDepartmentFunctionCountry] AS [CountByRecordUpdateType] 
		, [dbo].[udfDivide](NCT.[SUM Function Period TimeSheet Actual Total Hours], FCT.[CountByDepartmentFunctionCountry]) AS [Actual Hours (re-allocated)]
		, (CT.[SUM Function Period TimeSheet Actual Total Hours] 
			+ [dbo].[udfDivide](NCT.[SUM Function Period TimeSheet Actual Total Hours], FCT.[CountByDepartmentFunctionCountry])
		  )	AS [Actual Total Hours (Allocated)]
		, CT.[SUM Function Period Actual Cost]
		, CT.[SUM Function Reconciliation Actual Cost]
		, CT.[SUM Function Actual Cost]
		, CT.[SUM Function Period Actual Cost] as [SUM Function Actual Cost CT]
		, NCT.[SUM Function Period Actual Cost] as [SUM Function Actual Cost NCT]
		, [dbo].[udfDivide](NCT.[SUM Function Period Actual Cost], FCT.CountByDepartmentFunctionCountry) AS [Actual Cost (re-allocated)]
		, (CT.[SUM Function Period Actual Cost] 
			+  [dbo].[udfDivide](NCT.[SUM Function Period Actual Cost], FCT.CountByDepartmentFunctionCountry)
		  )	AS [Actual Cost (Allocated)]

    FROM (select *
        from STAGING_CADENCE.CountryReallocateTS CT with (nolock)
        where [SUM Task Period Approved Total Units] <> 0
            and NOT EXISTS ( SELECT *
            FROM STAGING_CADENCE.FinalCountryReallocateTS FTS with (nolock)
            WHERE 	CT.[Period Year]			= FTS.[Period Year]
                AND CT.[Period Month]			= FTS.[Period Month]
                AND CT.[Project Name]			= FTS.[Project Name]
                AND CT.[Task Code]				= FTS.[Task Code]
                AND CT.[Part Order Index]		= FTS.[Part Order Index]
                AND CT.[Segment Order Index]	= FTS.[Segment Order Index]
                AND CT.[Function Code]			= FTS.[Function Code]
                AND CT.[Function Country Name]	= FTS.[Function Country Name]
                AND FTS.[RecordUpdateType]		= 'FFC'
					)
	) CT
        INNER JOIN (select
            		  [Period Year]
					, [Period Month]
					, [Project Name]
					, [Task Code]
					, [Part Order Index]
					, [Segment Order Index]
					, [Department]
					, [Function Country Name]
					, sum([SUM Function Period TimeSheet Actual Total Hours]) as [SUM Function Period TimeSheet Actual Total Hours]
					, sum([SUM Function Period Actual Cost]) as [SUM Function Period Actual Cost]
        from STAGING_CADENCE.NoCountryReallocateTS  with (nolock)
        where ([SUM Function TimeSheet Actual Total Hours] <> 0  or [SUM Function Actual Cost] <> 0)
        group by 
					  [Period Year]
					, [Period Month]
					, [Project Name]
					, [Task Code]
					, [Part Order Index]
					, [Segment Order Index]
					, [Department]
					, [Function Country Name]
			) NCT ON	(		CT.[Period Year]			= NCT.[Period Year]
            AND CT.[Period Month]			= NCT.[Period Month]
            AND CT.[Project Name]			= NCT.[Project Name]
            AND CT.[Task Code]				= NCT.[Task Code]
            AND CT.[Part Order Index]		= NCT.[Part Order Index]
            AND CT.[Segment Order Index]	= NCT.[Segment Order Index]
            AND CT.[Department]				= NCT.[Department]
            AND CT.[Function Country Name]	= NCT.[Function Country Name]
						)
        INNER JOIN (select
            [Period Year]
					, [Period Month]
					, [Project Name]		
					, [Task Code]
					, [Part Order Index]
					, [Segment Order Index]
					, [Department]
					, [Function Country Name]
					, count(1) AS [CountByDepartmentFunctionCountry]
        from STAGING_CADENCE.CountryReallocateTS CT
        where [SUM Task Period Approved Total Units] <> 0
            and NOT EXISTS ( SELECT *
            FROM STAGING_CADENCE.FinalCountryReallocateTS FTS with (nolock)
            WHERE 	CT.[Period Year]			= FTS.[Period Year]
                AND CT.[Period Month]			= FTS.[Period Month]
                AND CT.[Project Name]			= FTS.[Project Name]
                AND CT.[Task Code]				= FTS.[Task Code]
                AND CT.[Part Order Index]		= FTS.[Part Order Index]
                AND CT.[Segment Order Index]	= FTS.[Segment Order Index]
                AND CT.[Function Code]			= FTS.[Function Code]
                AND CT.[Function Country Name]	= FTS.[Function Country Name]
                and FTS.[RecordUpdateType]		= 'FFC'
									 )
        group by 
					 [Period Year]
					,[Period Month]
					,[Project Name]		
					,[Task Code]
					,[Part Order Index]
					,[Segment Order Index]
					,[Department]
					,[Function Country Name]
			) FCT ON (		CT.[Period Year]				= FCT.[Period Year]
            AND CT.[Period Month]				= FCT.[Period Month]
            AND CT.[Project Name]				= FCT.[Project Name]
            AND CT.[Task Code]					= FCT.[Task Code]
            AND CT.[Part Order Index]			= FCT.[Part Order Index]
            AND CT.[Segment Order Index]		= FCT.[Segment Order Index]
            AND CT.[Department]					= FCT.[Department]
            AND CT.[Function Country Name]		= FCT.[Function Country Name]
					)


--Move reord for NoCountry where Department/FunctionCountry matches.
INSERT INTO STAGING_CADENCE.FinalCountryReallocateTS
    select distinct
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
		, 'NCD' AS [RecordUpdateType]
		, 1 AS [CountByRecord1UpdateType] 
		, (-1 * NCT.[SUM Function Period TimeSheet Actual Total Hours]) AS [Actual Hours (re-allocated)]
		, 0	AS [Actual Total Hours (Allocated)]
		, NCT.[SUM Function Period Actual Cost]
		, NCT.[SUM Function Reconciliation Actual Cost]
		, NCT.[SUM Function Actual Cost]
		, 0												AS [SUM Function Actual Cost CT]
		, NCT.[SUM Function Period Actual Cost]			AS [SUM Function Actual Cost NCT]
		, -1 * NCT.[SUM Function Period Actual Cost]	AS [Actual Cost (re-allocated)]
		, 0												AS [Actual Cost (Allocated)]		
    FROM STAGING_CADENCE.NoCountryReallocateTS NCT with (nolock)
        INNER JOIN STAGING_CADENCE.CountryReallocateTS CT with (nolock) ON 
												(		CT.[Period Year]			= NCT.[Period Year]
            AND CT.[Period Month]			= NCT.[Period Month]
            AND CT.[Project Name]			= NCT.[Project Name]
            AND CT.[Task Code]				= NCT.[Task Code]
            AND CT.[Part Order Index]		= NCT.[Part Order Index]
            AND CT.[Segment Order Index]	= NCT.[Segment Order Index]
            AND CT.[Department]				= NCT.[Department]
            AND CT.[Function Country Name]	= NCT.[Function Country Name]
            and CT.[SUM Task Period Approved Total Units] <> 0
												)
    WHERE (NCT.[SUM Function Period TimeSheet Actual Total Hours] <> 0 or NCT.[SUM Function Period Actual Cost] <> 0)


--After moving delete those records.
DELETE NCT
FROM STAGING_CADENCE.NoCountryReallocateTS NCT with (nolock)
        INNER JOIN STAGING_CADENCE.CountryReallocateTS CT with (nolock) ON (CT.[Period Year]		= NCT.[Period Year]
            AND CT.[Period Month]		= NCT.[Period Month]
            AND CT.[Project Name]		= NCT.[Project Name]
            AND CT.[Task Code]			= NCT.[Task Code]
            AND CT.[Part Order Index]	= NCT.[Part Order Index]
            AND CT.[Segment Order Index]= NCT.[Segment Order Index]
            AND CT.[Department]			= NCT.[Department]
            AND CT.[Function Country Name]= NCT.[Function Country Name]
            and CT.[SUM Task Period Approved Total Units] <> 0
											  )
WHERE (NCT.[SUM Function Period TimeSheet Actual Total Hours] <> 0 or NCT.[SUM Function Period Actual Cost] <> 0)



EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[FinalCountryReallocateTS] (Case-2) in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG  + ' (Record count: ' + CAST(@Count AS VARCHAR(10)) + ')' ;
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