CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskRetainerQuarterly] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskRetainerQuarterly]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )

BEGIN TRY

DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskRetainerQuarterly])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskRetainerQuarterly];

if object_id('tempdb..#t') is not null
begin drop table #t end

;with cte as
(
select 
       r.DimCustomerProjectKey
      ,r.DimCustomerKey
	  ,r.DimProjectKey
      ,r.DimDocumentDateKey
      ,r.Currency
      ,r.NetAmountTC
	  ,concat(dd.Year, '-Q', dd.Quarter) as YearQuarter
from [CONSUMPTION_FINANCE].[FactSAPSalesRetainerDetails] r
left join [dbo].[DimDate] dd
on r.DimDocumentDateKey = dd.DimDateKey
)
select
DimCustomerProjectKey,
DimCustomerKey,
DimProjectKey,
YearQuarter, 
Currency,
sum(NetAmountTC) as AggregatedNetAmountTC
into #t
from cte
group by DimCustomerProjectKey, DimCustomerKey, DimProjectKey, YearQuarter, Currency;

begin transaction

insert into [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskRetainerQuarterly]
(
       [DimCustomerProjectKey]
      ,[DimCustomerKey]
      ,[DimProjectKey]
      ,[QuarterRangeKey]
      ,[YearQuarter]
      ,[FilterValue]
      ,[Currency]
      ,[AggregatedNetAmountTC]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select
#t.DimCustomerProjectKey, 
#t.DimCustomerKey,
#t.DimProjectKey,
qr.QuarterRangeKey, 
#t.YearQuarter,
qr.FilterValue,
#t.Currency,
#t.AggregatedNetAmountTC,
'[CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskRetainerQuarterly]' as CreatedBy,
'[CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskRetainerQuarterly]' as UpdatedBy,
getdate() as CreatedAt,
getdate() as UpdatedAt
from #t



 left join [CONSUMPTION_FINANCE].[QuarterRanges] qr on qr.[YearQuarter] =  #t.YearQuarter
 and qr.[FilterValue] in ('All', 'Last 4 Quarters', NULL)

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id('tempdb..#t') is not null
begin drop table #t end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskRetainerQuarterly])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

rollback transaction

DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048) 

--store all the error information for logging the error
SELECT @ErrorNum       = ERROR_NUMBER() 
      ,@ErrorLine      = 0
      ,@ErrorSeverity  = ERROR_SEVERITY()
      ,@ErrorState     = ERROR_STATE()
      ,@ErrorProcedure = ERROR_PROCEDURE()
      ,@ErrorMessage   = ERROR_MESSAGE()

SET @MSG = @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') 
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH

END