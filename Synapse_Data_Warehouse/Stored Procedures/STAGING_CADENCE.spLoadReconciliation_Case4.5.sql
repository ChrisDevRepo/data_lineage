CREATE PROC [STAGING_CADENCE].[spLoadReconciliation_Case4.5] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadReconciliation_Case4.5'
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
-- ***** USE CASE 4.5******
-- ************************



if object_id(N'tempdb..#ChangeOrders') is not null
begin drop table #ChangeOrders; end

CREATE TABLE #ChangeOrders
WITH
(
	DISTRIBUTION = HASH ([Project Name], [period year], [period Month], [Task Code], [Part Order Index], [segment order index], [Task Country Name]),
	CLUSTERED COLUMNSTORE INDEX
)
AS
	select BB.*
	from
		(
			select aa.*, coalesce(lag([DatePeriod], 1)  OVER(PARTITION BY [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name] ORDER BY [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name], [Period Year], [Period Month]), [DatePeriod]) AS [FromRecord]
			from
				(
					select [Period Year], [Period Month], [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name] 
						, DATEFROMPARTS([Period Year], [Period Month], 1) as [DatePeriod]
						, MAX([Task Reconciliation CADENCE Earned Value]) as [Task Reconciliation CADENCE Earned Value]
						, row_number() OVER(PARTITION BY [Project Name] ORDER BY [Project Name], [Period Year], [Period Month]) AS [ROW_NUMBER]
					from [STAGING_CADENCE].[TaskAndFunctionData] with (nolock)
					where  ([SUM Task Reconciliation Actual Cost] <> 0 or [Task Reconciliation CADENCE Earned Value] <> 0)
					group by [Period Year], [Period Month], [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name]

					union

					select Year(min(DATEFROMPARTS([Period Year], [Period Month], 1))) as [Period Year], month(min(DATEFROMPARTS([Period Year], [Period Month], 1)))  as [Period Month], [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name] 
						, min(DATEFROMPARTS([Period Year], [Period Month], 1)) as [DatePeriod]
						, MAX([Task Reconciliation CADENCE Earned Value]) as [Task Reconciliation CADENCE Earned Value]
						, 0 as [ROW_NUMBER]
						
					from [STAGING_CADENCE].[TaskAndFunctionData] with (nolock)
					group by [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name] 
				) aa
		) BB
	where  BB.[ROW_NUMBER] > 0;


IF OBJECT_ID(N'STAGING_CADENCE.ReconciliationPopulation') IS NOT NULL
BEGIN
        TRUNCATE TABLE [STAGING_CADENCE].[ReconciliationPopulation]
    END

insert into [STAGING_CADENCE].[ReconciliationPopulation]
    select
        CC.[Period Year],
        CC.[Period Month],
        CC.[Data Period Year],
        CC.[Data Period Month],
        CC.[Project Name],
        CC.[Project Currency Code],
        CC.[Project Currency Name],
        CC.[Service],
        CC.[Task Code],
        CC.[Task Name],
        CC.[Part Order Index],
        CC.[Segment Order Index],
        CC.[Original Task Country Name] as [Task Country Name],
        CC.[Function Code],
        CC.[Function Name],
        CC.[Function Country Name],
        CC.[Department],
        CC.[Unit type],
        'REC' as [RecordUpdateType],
	    CC.[Project Ref Id],
	    CC.[Archived Project Ref Id],
	    CC.[PRIMA Project Id],
	    CC.[Project Status],
	    CC.[Project Phase],
        CC.[Is Deleted Task],
        CC.[SUM Function Reconciliation Approved Units],
		CTC.[Task Period CADENCE Earned Value],
		CTC.[Task Reconciliation CADENCE Earned Value],
		CTC.[Task CADENCE Earned Value],
		CC.[Task CADENCE Planned Unit Cost],
        CC.[SUM Function Planned Total Cost Adjusted],
        CC.[Function CurrentRate Adjusted],
        CC.[SUM Task Planned Total Units] ,
        CC.[SUM Task Approved Total Units],
        CC.[SUM Function Reconciliation TimeSheet Actual Total Hours],
        sum(coalesce(cum.[SUM Function Actual Hours], 0)) as [SUM Function Actual Hours],
        SUM(coalesce(cum.[SUM Function Reconciliation Actual Cost], 0)) as [SUM Function Reconciliation Actual Cost],
        CTC.[SUM Task Reconciliation Actual Cost],
        sum(coalesce(cum.[SUM Function Actual Cost], 0)) as [SUM Function Actual Cost],
        CC.[SUM Function Planned Total Hours],
        case when isnull((sum(coalesce(cum.[SUM Function Actual Hours], 0)) / nullif(CC.[SUM Task Approved Total Units], 0)), 0) <= (isnull((CC.[SUM Function Planned Total Hours] / nullif(CC.[SUM Task Planned Total Units], 0)), 0) * 0.1)
			then 'yes'
			else 'no'
		end as [IsApprvedUnitLessThan10PercentPlannedUnits],
        CC.[From Period],
        CC.[To Period],
        GetUtcDate() as [CREATED_AT],
        GetUtcDate() as [UPDATED_AT]
    from
        (
			select 
			  co.[Period Year]
			, co.[Period Month]
			, tf.[Period Year] as [Data Period Year]
			, tf.[Period Month] as [Data Period Month]
			, tf.[Project Name]
			, tf.[Project Currency Code]
			, tf.[Project Currency Name]
			, tf.[Service]
			, tf.[Task Code]
			, tf.[Task Name]
			, tf.[Part Order Index]
			, tf.[Segment Order Index]
			, tf.[Task Country Name]
			, tf.[Function Code]
			, tf.[Function Name]
			, tf.[Function Country Name]
			, tf.[Department]
			, tf.[Unit type]
			, tf.[Project Ref Id]
			, tf.[Archived Project Ref Id]
			, tf.[PRIMA Project Id]
			, tf.[Project Status]
			, tf.[Project Phase]
			, tf.[Is Deleted Task]
			, tf.[SUM Function Reconciliation Approved Units]
			, tf.[Task Period CADENCE Earned Value]
			, tf.[Task CADENCE Earned Value]
			, tf.[Task CADENCE Planned Unit Cost]
			, tf.[SUM Function Planned Total Cost Adjusted]
			, tf.[Function CurrentRate Adjusted]
			, tf.[SUM Task Planned Total Units] 
			, tf.[SUM Task Approved Total Units]
			, tf.[SUM Function Reconciliation TimeSheet Actual Total Hours]
			, tf.[SUM Function Planned Total Hours]
			, co.[Task Country Name] as [Original Task Country Name]
			, co.[Task Reconciliation CADENCE Earned Value]
			, co.[FromRecord] as [From Period]
			, co.[DatePeriod] as [To Period]
			from #ChangeOrders co  with (nolock)
			inner join [STAGING_CADENCE].[TaskAndFunctionData] tf with (nolock) on tf.[Project Name]			= co.[Project Name]
				and tf.[Task Code]				= co.[Task Code]
				and tf.[Part Order Index]		= co.[Part Order Index]
				and tf.[Segment Order Index]	= co.[Segment Order Index]
				and tf.[Task Country Name]		= (
								case when (
											select count(1) as BudgetRecordCount
											from #ChangeOrders co1
											where not exists (
																select * 
																from [STAGING_CADENCE].[TaskAndFunctionData] tf1 with (nolock)
																where   tf1.[Project Name]				=	co1.[Project Name]
																	and tf1.[Task Code]					=	co1.[Task Code]
																	and tf1.[Task Country Name]			=	co1.[Task Country Name]
																	and tf1.[Part Order Index]			=	co1.[Part Order Index]
																	and tf1.[Segment Order Index]		=	co1.[Segment Order Index]
																	and tf1.[Period Year]				=	co1.[Period Year]	 
																	and tf1.[Period Month]				=	co1.[Period Month]
															)
										) = 0 and co.[Task Country Name] = 'No Country' 
									then 'Global'
									else co.[Task Country Name]
								end
							)
				and datefromparts(tf.[Period Year], tf.[Period Month], 1)	= format(dateadd(MONTH, -1, co.[DatePeriod]), 'MM/dd/yyyy')
		) CC
    	left join [STAGING_CADENCE].[TaskAndFunctionData] cum with (nolock) on
			(
					cum.[Project Name]				= CC.[Project Name]
    	        and cum.[Task Code]					= CC.[Task Code]
    	        and cum.[Task Country Name]			= CC.[Task Country Name]
    	        and cum.[Part Order Index]			= CC.[Part Order Index]
    	        and cum.[Segment Order Index]		= CC.[Segment Order Index]
    	        and cum.[Function Name]				= CC.[Function Name]
    	        and cum.[Function Country Name]		= CC.[Function Country Name]
    	        and cum.[Department]				= CC.[Department]
    	        and DATEFROMPARTS(cum.[Period Year], cum.[Period Month], 1) >= CC.[From Period]
    	        and DATEFROMPARTS(cum.[Period Year], cum.[Period Month], 1) < CC.[To Period]
			)
		inner join (
						select 
							[Project Name], [Period Year], [Period Month], [Task Code], [Part Order Index], 1 as [Segment Order Index], [Task Country Name]
							, SUM([SUM Task Reconciliation Actual Cost]) as [SUM Task Reconciliation Actual Cost]
							, SUM([Task Period CADENCE Earned Value]) as [Task Period CADENCE Earned Value]
							, SUM([Task Reconciliation CADENCE Earned Value]) as [Task Reconciliation CADENCE Earned Value]
							, SUM([Task CADENCE Earned Value]) as [Task CADENCE Earned Value]
						FROM
						(
							select distinct [Project Name], [Period Year], [Period Month], [Task Code], [Part Order Index], [Segment Order Index] 
								, case when [Task Country Name] = 'No Country' then 'Global' else [Task Country Name] end as [Task Country Name]
								, [SUM Task Reconciliation Actual Cost]			as [SUM Task Reconciliation Actual Cost]
								, [Task Period CADENCE Earned Value]			as [Task Period CADENCE Earned Value]
								, [Task Reconciliation CADENCE Earned Value]	as [Task Reconciliation CADENCE Earned Value]
								, [Task CADENCE Earned Value]					as [Task CADENCE Earned Value]
							from [STAGING_CADENCE].[TaskAndFunctionData] CTC with (nolock)
							WHERE [Task Reconciliation CADENCE Earned Value] <> 0
						) AA
						group by [Project Name], [Period Year], [Period Month], [Task Code], [Part Order Index], [Task Country Name]
					) CTC on
							(
									CTC.[Project Name]				= CC.[Project Name]
								and CTC.[Period Year]				= CC.[Period Year]
								and CTC.[Period Month]				= CC.[Period Month]
								and CTC.[Task Code]					= CC.[Task Code]
								and CTC.[Part Order Index]			= CC.[Part Order Index]
								and CTC.[Segment Order Index]		= CC.[Segment Order Index]
								and CTC.[Task Country Name]			= CC.[Task Country Name]
							)
    where 
		CC.[Period Year] IS NOT NULL
    group by 
 	CC.[Period Year],
	CC.[Period Month],
	CC.[Data Period Year],
	CC.[Data Period Month],
	CC.[Project Name],
	CC.[Project Currency Code],
	CC.[Project Currency Name],
	CC.[Service],
	CC.[Task Code],
	CC.[Task Name],
	CC.[Part Order Index],
	CC.[Segment Order Index],
	CC.[Task Country Name],
	CC.[Original Task Country Name],
	CC.[Function Code],
	CC.[Function Name],
	CC.[Function Country Name],
	CC.[Department],
	CC.[Unit type],
	CC.[SUM Function Planned Total Cost Adjusted],
	CC.[Function CurrentRate Adjusted],
	CC.[SUM Task Planned Total Units] ,
	CC.[SUM Task Approved Total Units],
	CC.[SUM Function Reconciliation TimeSheet Actual Total Hours],
	CTC.[SUM Task Reconciliation Actual Cost],
	CC.[From Period], 
	CC.[To Period],
	CC.[SUM Function Planned Total Hours],
	CC.[Project Ref Id],
	CC.[Archived Project Ref Id],
	CC.[PRIMA Project Id],
	CC.[Project Status],
	CC.[Project Phase],
    CC.[Is Deleted Task],
    CC.[SUM Function Reconciliation Approved Units],
	CTC.[Task Period CADENCE Earned Value],
	CTC.[Task Reconciliation CADENCE Earned Value],
	CTC.[Task CADENCE Earned Value],
	CC.[Task CADENCE Planned Unit Cost]



EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[ReconciliationPopulation] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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