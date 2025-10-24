CREATE PROC [STAGING_CADENCE].[spLoadCadenceCase0Data] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCadenceCase0Data'
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
-- ***** USE CASE 0 *******
-- ************************
-- Reallocate hours when Planned Units = 1 and Approved Total Units <> 0


if object_id(N'tempdb..#FinalCountryReallocateTS') is not null
begin drop table #FinalCountryReallocateTS; end

CREATE TABLE #FinalCountryReallocateTS
WITH
(
	DISTRIBUTION = HASH ([Project Name], [Task Code], [Task Country Name], [Part Order Index], [Function Code],[Function Country Name] ),
	CLUSTERED COLUMNSTORE INDEX
)
AS
select *
    , row_number() OVER(PARTITION BY d.[Project Name], d.[Task Code], d.[Task Country Name], d.[Part Order Index], d.[Segment Order Index], d.[Function Code], d.[Function Country Name] ORDER BY d.[Period Year], d.[Period Month]) AS [ROW_NUMBER]
from [STAGING_CADENCE].[FinalCountryReallocateTS] d with (nolock);



IF OBJECT_ID(N'STAGING_CADENCE.FinalCountryReallocateTSAggregatedData') IS NOT NULL
    TRUNCATE TABLE [STAGING_CADENCE].[FinalCountryReallocateTSAggregatedData];

insert into [STAGING_CADENCE].[FinalCountryReallocateTSAggregatedData]
    select p.*
    , sum(d.[Actual Total Hours (Allocated)]) as [Calc Actual Total Hours (Allocated)]
    , sum(d.[Actual Cost (Allocated)]) as [Calc Actual Cost (Allocated)]
    from
        (
		select datefromparts([Period Year], [Period Month], 1) as [Period Start Date]
			, [Period Year]
			, [Period Month]
			, [Project Name]
			, [Task Code]
			, [Task Country Name]
			, [Part Order Index]
			, [Segment Order Index]
			, [Function Code]
			, [Function Country Name]
			, [SUM Task Planned Total Units]
			--, [SUM Function Planned Total Hours]
			, [SUM Task Period Approved Total Units]
			, [Actual Total Hours (Allocated)]
			, [Actual Cost (Allocated)]
			, [ROW_NUMBER]
			, coalesce(lag([ROW_NUMBER], 1)  OVER(ORDER BY [Period Year], [Period Month]), 0) AS [FromRecord]
        from #FinalCountryReallocateTS d
        WHERE	[SUM Task Planned Total Units]	= 1
            and [SUM Task Period Approved Total Units] <> 0
	) p
        left join #FinalCountryReallocateTS d with (nolock) on
				d.[ROW_NUMBER]			   <= p.[ROW_NUMBER]
            and d.[Project Name]			= p.[Project Name]
            and d.[Task Code]				= p.[Task Code]
            and d.[Task Country Name]		= p.[Task Country Name]
            and d.[Part Order Index]		= p.[Part Order Index]
            and d.[Segment Order Index]		= p.[Segment Order Index]
            and d.[Function Code]			= p.[Function Code]
            and d.[Function Country Name]	= p.[Function Country Name]
    group by 
	 p.[Period Start Date]
	,p.[Project Name]			
	,p.[Period Year]				
	,p.[Period Month]
	,p.[Task Code]				
	,p.[Task Country Name]		
	,p.[Part Order Index]		
	,p.[Segment Order Index]		
	,p.[Function Code]			
	,p.[Function Country Name]	
	,p.[SUM Task Planned Total Units]
	--, p.[SUM Function Planned Total Hours]
	,p.[SUM Task Period Approved Total Units]
	,p.[Actual Total Hours (Allocated)]
    ,p.[Actual Cost (Allocated)]
	,p.[ROW_NUMBER]
	,p.[FromRecord]






IF OBJECT_ID(N'STAGING_CADENCE.CadenceCase0Data') IS NOT NULL
    TRUNCATE TABLE [STAGING_CADENCE].[CadenceCase0Data];

insert into [STAGING_CADENCE].[CadenceCase0Data]
select 
      AA.[Period Year]
    , AA.[Period Month]
    , AA.[Project Name]
    , AA.[Project Currency Code]
    , AA.[Project Currency Name]
    , AA.[Service]
    , AA.[Task Code]
    , AA.[Task Name]
    , AA.[Task Country Name]
    , AA.[Unit type]
    , AA.[Part Order Index]
    , AA.[Segment Order Index]
    , AA.[Function Code]
    , AA.[Function Name]
    , AA.[Department]
    , AA.[Function Country Name]
    , AA.[Project Ref Id]
    , AA.[Archived Project Ref Id]
    , AA.[PRIMA Project Id]
    , AA.[Project Status]
    , AA.[Project Phase]
    , AA.[Is Deleted Task]
    , AA.[SUM Function Reconciliation Approved Units]
	, AA.[Task Period CADENCE Earned Value]
	, AA.[Task Reconciliation CADENCE Earned Value]
	, AA.[Task CADENCE Earned Value]
	, AA.[Task CADENCE Planned Unit Cost]
	, AA.[SUM Function Period TimeSheet Actual Total Hours]
	--, AA.[SUM Function TimeSheet Actual Total Hours]
	, AA.[SUM Task Period Approved Total Units]
    , AA.[SUM Function Planned Total Cost Adjusted]
    , AA.[SUM Function Planned Total Hours]
    , AA.[Function CurrentRate Adjusted]
    , AA.[SUM Task Planned Total Units]
    , AA.[SUM Task Approved Total Units]
    , AA.[SUM Function TimeSheet Actual Total Hours CT]
    , AA.[SUM Function TimeSheet Actual Total Hours NCT]
    , AA.[RecordUpdateType]
    , AA.[CountByRecordUpdateType]
    , AA.[Actual Hours (re-allocated)]
    , AA.[Actual Total Hours (Allocated)] as [Original Actual Total Hours (Allocated)]
    , AA.[Updated Actual Total Hours (Allocated)] as [Actual Total Hours (Allocated)]
    , AA.[SUM Function Period Actual Cost]
    , AA.[SUM Function Reconciliation Actual Cost]
    , AA.[SUM Function Actual Cost]
    , AA.[SUM Function Actual Cost CT]
    , AA.[SUM Function Actual Cost NCT]
    , AA.[ROW_NUMBER]
	, AA.[SelRows]
    , AA.[Actual Cost (re-allocated)]
    , AA.[Actual Cost (Allocated)] as [Original Actual Cost (Allocated)]
    , AA.[Updated Actual Cost (Allocated)] as [Actual Cost (Allocated)]
	, AA.[Calculated Approved Units]
	, AA.[Calculated Planned Units]
	, AA.[Calculated Unit Cost]

from 
(    
  select 
      o.[Period Year]
    , o.[Period Month]
    , o.[Project Name]
    , o.[Project Currency Code]
    , o.[Project Currency Name]
    , o.[Service]
    , o.[Task Code]
    , o.[Task Name]
    , o.[Task Country Name]
    , o.[Unit type]
    , o.[Part Order Index]
    , o.[Segment Order Index]
    , o.[Function Code]
    , o.[Function Name]
    , o.[Department]
    , o.[Function Country Name]
    , o.[Project Ref Id]
    , o.[Archived Project Ref Id]
    , o.[PRIMA Project Id]
    , o.[Project Status]
    , o.[Project Phase]
    , o.[Is Deleted Task]
    , o.[SUM Function Reconciliation Approved Units]
	, o.[Task Period CADENCE Earned Value]
	, o.[Task Reconciliation CADENCE Earned Value]
	, o.[Task CADENCE Earned Value]
	, o.[Task CADENCE Planned Unit Cost]
	, o.[SUM Function Period TimeSheet Actual Total Hours]
	--, o.[SUM Function TimeSheet Actual Total Hours]
	, o.[SUM Task Period Approved Total Units]
    , o.[SUM Function Planned Total Cost Adjusted]
    , o.[SUM Function Planned Total Hours]
    , o.[Function CurrentRate Adjusted]
    , o.[SUM Task Planned Total Units]
    , o.[SUM Task Approved Total Units]
    , o.[SUM Function TimeSheet Actual Total Hours CT]
    , o.[SUM Function TimeSheet Actual Total Hours NCT]
    , o.[RecordUpdateType]
    , o.[CountByRecordUpdateType]
    , o.[Actual Hours (re-allocated)]
    , o.[Actual Total Hours (Allocated)]
    , o.[SUM Function Period Actual Cost]
    , o.[SUM Function Reconciliation Actual Cost]
    , o.[SUM Function Actual Cost]
    , o.[SUM Function Actual Cost CT]
    , o.[SUM Function Actual Cost NCT]
    , o.[ROW_NUMBER]
	, agg.[ROW_NUMBER] as [SelRows]
    , o.[Actual Cost (re-allocated)]
    , o.[Actual Cost (Allocated)]

	, case when (oc.[LastOccurance] = 0 or oc.[LastOccurance] is null)
		   then o.[Actual Total Hours (Allocated)]
		   else
				case  when o.[ROW_NUMBER] > oc.[LastOccurance]
					  then o.[Actual Total Hours (Allocated)]
					  else case when agg.[ROW_NUMBER] = o.[ROW_NUMBER]
								then agg.[Calc Actual Total Hours (Allocated)]
								else 0
						   end
				end 
	  end as [Updated Actual Total Hours (Allocated)]
	, case when (oc.[LastOccurance] = 0 or oc.[LastOccurance] is null)
		   then o.[Actual Cost (Allocated)]
		   else
				case  when o.[ROW_NUMBER] > oc.[LastOccurance]
					  then o.[Actual Cost (Allocated)]
					  else case when agg.[ROW_NUMBER] = o.[ROW_NUMBER]
								then agg.[Calc Actual Cost (Allocated)]
								else 0
						   end
				end 
	  end as [Updated Actual Cost (Allocated)]      
	      

	, ISNULL((o.[Actual Total Hours (Allocated)] / NULLIF(o.[SUM Task Period Approved Total Units], 0)), 0) as [Calculated Approved Units]
	, ISNULL((o.[SUM Function Planned Total Hours] / NULLIF(o.[SUM Task Planned Total Units], 0)), 0) as [Calculated Planned Units]

	, COALESCE(case when o.[Task Period CADENCE Earned Value] <> 0 and (o.[SUM Function Planned Total Cost Adjusted] = 0 or o.[SUM Task Planned Total Units] = 0)
			   		then o.[Task CADENCE Planned Unit Cost]
			   		else ISNULL((o.[SUM Function Planned Total Cost Adjusted] / NULLIF(o.[SUM Task Planned Total Units], 0)), 0)
			   end, 0) as [Calculated Unit Cost]   
      
    from #FinalCountryReallocateTS o with (nolock)
        left join [STAGING_CADENCE].[FinalCountryReallocateTSAggregatedData] agg  with (nolock)
        on	
			(	o.[Project Name]			= agg.[Project Name]
             and o.[Period Year]			= agg.[Period Year]
             and o.[Period Month]			= agg.[Period Month]
             and o.[Task Code]				= agg.[Task Code]
             and o.[Task Country Name]		= agg.[Task Country Name]
             and o.[Part Order Index]		= agg.[Part Order Index]
             and o.[Segment Order Index]	= agg.[Segment Order Index]
             and o.[Function Code]			= agg.[Function Code]
             and o.[Function Country Name]	= agg.[Function Country Name]
			)
        left join (select [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name], [Function Code], [Function Country Name], coalesce(max([ROW_NUMBER]), 0) as LastOccurance
        from [STAGING_CADENCE].[FinalCountryReallocateTSAggregatedData] oc with (nolock)
        group by [Project Name], [Task Code], [Part Order Index], [Segment Order Index], [Task Country Name], [Function Code], [Function Country Name]
		  ) oc
        on
		  (		o.[Project Name]		    = oc.[Project Name]
            and o.[Task Code]				= oc.[Task Code]
            and o.[Task Country Name]		= oc.[Task Country Name]
            and o.[Part Order Index]		= oc.[Part Order Index]
            and o.[Segment Order Index]		= oc.[Segment Order Index]
            and o.[Function Code]			= oc.[Function Code]
            and o.[Function Country Name]	= oc.[Function Country Name]
		  )
) AA




EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[CadenceCase0Data] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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
