CREATE PROC [STAGING_CADENCE].[spLoadTaskAndFunctionData] AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadTaskAndFunctionData'
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

IF OBJECT_ID('STAGING_CADENCE.TaskAndFunctionData') IS NOT NULL
TRUNCATE TABLE  [STAGING_CADENCE].[TaskAndFunctionData];


insert INTO STAGING_CADENCE.TaskAndFunctionData
	SELECT
           fl.[Period Year]										AS [Period Year]
		, fl.[Period Month]										AS [Period Month]
		, fl.[Project Name]										AS [Project Name]
		, fl.[Project Currency Code]							AS [Project Currency Code]
		, fl.[Project Currency Name]							AS [Project Currency Name]
		, fl.[Service Name]										AS [Service]
		, tc.[Unit type]										AS [Unit type]
		, fl.[Task Code]										AS [Task Code]
		, fl.[Task Name]										AS [Task Name]
		, case when (fl.[Task Country Name] = 'Global' AND MAX(COALESCE(tc.[Planned Total Cost], 0)) = 0) 
			   then 'No Country' 
			   else fl.[Task Country Name] 
		  end as [Task Country Name]
		, fl.[Part Order Index]									AS [Part Order Index]
		, fl.[Segment Order Index] 								AS [Segment Order Index] 
		, fl.[Task Region Name]									AS [Task Region]
		, fl.[Function Code]									AS [Function Code]
		, fl.[Function Name]									AS [Function Name]
		, fl.[Department Name]									AS [Department]
		, fl.[Function Location Name]							AS [Function Country Name]
		, fl.[Function Region Name]								AS [Function Region]
		, fl.[Project Ref Id]
		, fl.[Archived Project Ref Id]
		, fl.[PRIMA Project Id]
		, fl.[Project Status]
		, fl.[Project Phase]
		, fl.[Is Deleted Task]
		, SUM(fl.[Reconciliation Approved Units])			AS [SUM Function Reconciliation Approved Units]	
		
		, MAX(tc.[Period CADENCE Earned Value])				AS [Task Period CADENCE Earned Value]
		, MAX(tc.[Reconciliation CADENCE Earned Value])		AS [Task Reconciliation CADENCE Earned Value]
		, MAX(tc.[CADENCE Earned Value])					AS [Task CADENCE Earned Value]
		, MAX(tc.[CADENCE Planned Unit Cost])				AS [Task CADENCE Planned Unit Cost]

		, SUM(COALESCE(fl.[Planned Total Cost], 0))				AS [SUM Function Planned Total Cost Adjusted]
		, SUM(COALESCE(fl.[Planned Total Hours], 0))			AS [SUM Function Planned Total Hours]
		, COALESCE(fl.[Rate], 0)								AS [Function CurrentRate Adjusted]
		, SUM(COALESCE(tc.[Planned Total Units], 0))			AS [SUM Task Planned Total Units]
		, SUM(COALESCE(tc.[Period Approved Units], 0))			AS [SUM Task Period Approved Total Units]
		, SUM(COALESCE(tc.[Reconciliation Approved Units], 0))	AS [SUM Task Reconciliation Approved Total Units]
		, SUM(COALESCE(tc.[Approved Units], 0))					AS [SUM Task Approved Total Units]
		, SUM(COALESCE(fl.[Period Actual Hours], 0))			AS [SUM Function Period TimeSheet Actual Total Hours]
		, SUM(COALESCE(fl.[Reconciliation Actual Hours], 0))	AS [SUM Function Reconciliation TimeSheet Actual Total Hours]
		, SUM(COALESCE(fl.[Actual Hours], 0))					AS [SUM Function Actual Hours]
		, SUM(COALESCE(fl.[Period Actual Cost], 0))				AS [SUM Function Period Actual Cost]
		, SUM(COALESCE(fl.[Reconciliation Actual Cost], 0))		AS [SUM Function Reconciliation Actual Cost]
		, sum(COALESCE(tc.[Reconciliation Actual Cost], 0))		AS [SUM Task Reconciliation Actual Cost]
		, SUM(COALESCE(fl.[Actual Cost], 0))					AS [SUM Function Actual Cost]
       FROM
           [STAGING_CADENCE].[CadenceExtractFunctionLocation] fl  with (nolock)
           LEFT JOIN [STAGING_CADENCE].[CadenceExtractTaskCountry] tc  with (nolock)
									ON (	 	tc.[Project Name]			= fl.[Project Name]
											and tc.[Period Year]			= fl.[Period Year]
											and tc.[Period Month]			= fl.[Period Month]
											and tc.[Task Code]				= fl.[Task Code]
											and tc.[Task Country Code]		= fl.[Task Country Code]
											and tc.[Part Order Index]		= fl.[Part Order Index]
											and tc.[Segment Order Index]	= fl.[Segment Order Index]
										)
       GROUP BY
		  fl.[Period Year]				
		, fl.[Period Month]				
		, fl.[Project Name]	
		, fl.[Project Currency Code]
		, fl.[Project Currency Name]	
		, fl.[Service Name]	
		, fl.[Task Code]
		, fl.[Part Order Index]
		, fl.[Segment Order Index]
		, fl.[Task Name]				
		, tc.[Unit type]				
		, fl.[Task Country Name]		
		, fl.[Task Region Name]	
		, fl.[Function Code]
		, fl.[Function Name]			
		, fl.[Department Name]			
		, fl.[Function Location Name]	
		, fl.[Function Region Name]	
		, COALESCE(fl.[Rate], 0)
		, fl.[Project Ref Id]
		, fl.[Archived Project Ref Id]
		, fl.[PRIMA Project Id]
		, fl.[Project Status]
		, fl.[Project Phase]
		, fl.[Is Deleted Task]



UPDATE tc
SET [Task Reconciliation CADENCE Earned Value] = 0
FROM [STAGING_CADENCE].[TaskAndFunctionData] tc  
	INNER JOIN 
			(
				SELECT *
				FROM 
				(
					SELECT   
						AA.[Period Year]			
						, AA.[Period Month]			
						, AA.[Project Name]			
						, AA.[Task Code]			
						, AA.[Task Name]			
						, AA.[Part Order Index]		
						, AA.[Segment Order Index] 	
						, AA.[Task Country Name]
						, row_number() OVER(PARTITION BY AA.[Period Year], AA.[Period Month], AA.[Project Name], AA.[Task Code], AA.[Task Name], AA.[Part Order Index], AA.[Segment Order Index]  ORDER BY AA.[Task Country Name]) AS [ROW_NUMBER]
					FROM
					(
						SELECT distinct
							  [Period Year]											AS [Period Year]
							, [Period Month]										AS [Period Month]
							, [Project Name]										AS [Project Name]
							, [Task Code]											AS [Task Code]
							, [Task Name]											AS [Task Name]
							, [Part Order Index]									AS [Part Order Index]
							, [Segment Order Index] 								AS [Segment Order Index] 
							,	case	when ([Task Country Name] = 'Global' AND COALESCE([Planned Total Cost], 0) = 0) 
									then 'No Country' 
									else [Task Country Name] 
								end													AS [Task Country Name]
						FROM
							[STAGING_CADENCE].[CadenceExtractTaskCountry] with (nolock)
						WHERE [Task Country Name] = 'Global'
					) AA 
				)BB
				where BB.[ROW_NUMBER] = 2				
			) DD	ON (	 	DD.[Project Name]			= tc.[Project Name]
							and DD.[Period Year]			= tc.[Period Year]
							and DD.[Period Month]			= tc.[Period Month]
							and DD.[Task Code]				= tc.[Task Code]
							and DD.[Task Country Name]		= tc.[Task Country Name]
							and DD.[Part Order Index]		= tc.[Part Order Index]
							and DD.[Segment Order Index]	= tc.[Segment Order Index]
						)

EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[TaskAndFunctionData] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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