CREATE PROC [CONSUMPTION_FINANCE].[spLoadSAPSalesSummaryMetrics] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadSAPSalesSummaryMetrics]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )

BEGIN TRY

DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics];

begin transaction

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics]
select [Year]
      ,[DocumentDate]
      ,[DocumentNumber]
      ,[Customer]
      ,[CustomerName]
      ,[ProjectName]
      ,[InvoiceDetails]
      ,[Advances]
      ,[CostType]
      ,[BusinessArea]
      ,[Currency]
      ,[NetAmountTC]
	  ,[ConversionRate]	  
	  ,[CHFNetAmountTC]
      ,[VatAmountTC]
      ,[TotAmountTC]
      ,[PaymentTerms]
      ,[DueDate]
      ,[DatePaid]
      ,[ContractDetails]
      ,[PrimaID]
      ,[SalesForceNumber]
      ,[PostDate]
      ,[NetAmountCHF]
      ,[VatAmountCHF]
      ,[TotAmountCHF]
      ,[RteTcCHF]
      ,[NetAmountUSD]
      ,[VatAmountUSD]
      ,[TotAmountUSD]
      ,[RteTcUSD]
      ,[NetAmountEUR]
      ,[VatAmountEUR]
      ,[TotAmountEUR]
      ,[RteTcEUR]
      ,[NetAmountGBP]
      ,[VatAmountGBP]
      ,[TotAmountGBP]
      ,[RteTcGBP]
      ,[AccountPreviousYear],
	  [DaysToPay],
	  [DaysLate]

	  from 
(
select 
*,
CASE
    WHEN [ToTAmountTC] = 0 THEN NULL
    WHEN [DatePaid] IS NULL THEN NULL
    ELSE DATEDIFF(day, [DocumentDate], [DatePaid])
END AS DaysToPay,

CASE
    WHEN [ToTAmountTC] = 0 THEN NULL
    WHEN [DueDate] > FORMAT(getdate(), 'yyyy-MM-dd') AND [DatePaid] IS NULL THEN NULL
    WHEN [DueDate] IS NULL THEN NULL
    WHEN [DatePaid] IS NULL AND [DueDate] = FORMAT(getdate(), 'yyyy-MM-dd') THEN NULL
    WHEN [DatePaid] IS NULL AND [DueDate] < FORMAT(getdate(), 'yyyy-MM-dd') THEN DATEDIFF(day, [DueDate], getdate())
    ELSE DATEDIFF(day, [DueDate], [DatePaid])
END AS DaysLate,

Case when  [NetAmountTC] <= '0' then  Null
     when Currency = 'CHF' then  Null
     else r.UKURS  END as [ConversionRate],

Case 
     when [NetAmountTC] <= '0' then NULL 
	 when  Currency = 'CHF' then [NetAmountTC] else format(ROUND( [NetAmountTC]* r.UKURS,2),'0.##') END as [CHFNetAmountTC]

from 
(
select 
       [Year]
      ,[DocumentDate]
      ,[DocumentNumber]
      ,[Customer]
      ,[CustomerName]
      ,[ProjectName]
      ,[InvoiceDetails]
      ,[Advances]
      ,[CostType]
      ,[BusinessArea]
      ,[Currency]
      ,[NetAmountTC]
      ,[VatAmountTC]
      ,[TotAmountTC]
      ,[PaymentTerms]
      ,[DueDate]
      ,[DatePaid]
      ,[ContractDetails]
      ,[PrimaID]
      ,NULL as [SalesForceNumber]
      ,[PostDate]
      ,[NetAmountCHF]
      ,[VatAmountCHF]
      ,[TotAmountCHF]
      ,[RteTcCHF]
      ,[NetAmountUSD]
      ,[VatAmountUSD]
      ,[TotAmountUSD]
      ,[RteTcUSD]
      ,[NetAmountEUR]
      ,[VatAmountEUR]
      ,[TotAmountEUR]
      ,[RteTcEUR]
      ,[NetAmountGBP]
      ,[VatAmountGBP]
      ,[TotAmountGBP]
      ,[RteTcGBP]
      ,[AccountPreviousYear]
from [CONSUMPTION_FINANCE].[SAP_Sales_Summary_History]
union all
select 
       [Year]
      ,[DocumentDate]
      ,[DocumentNumber]
      ,[Customer]
      ,[CustomerName]
      ,[ProjectName]
      ,[InvoiceDetails]
      ,[Advances]
      ,[CostType]
      ,[BusinessArea]
      ,[Currency]
      ,[NetAmountTC]
      ,[VatAmountTC]
      ,[TotAmountTC]
      ,[PaymentTerms]
      ,[DueDate]
      ,[DatePaid]
      ,[ContractDetails]
      ,[PrimaID]
      ,[SalesForceNumber]
      ,[PostDate]
      ,[NetAmountCHF]
      ,[VatAmountCHF]
      ,[TotAmountCHF]
      ,[RteTcCHF]
      ,[NetAmountUSD]
      ,[VatAmountUSD]
      ,[TotAmountUSD]
      ,[RteTcUSD]
      ,[NetAmountEUR]
      ,[VatAmountEUR]
      ,[TotAmountEUR]
      ,[RteTcEUR]
      ,[NetAmountGBP]
      ,[VatAmountGBP]
      ,[TotAmountGBP]
      ,[RteTcGBP]
      ,[AccountPreviousYear]
from [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
) t

left join  [CONSUMPTION_FINANCE].[SAP_Tcurr] r on t.currency = r.fcurr
and r.GDATU = Dateadd(month, Datediff(month, 0, t.documentdate),0)
 
) M
where  DocumentDate >= '2015-01-01'  
and [DocumentNumber] not in
  (
    select [DocumentNumber]
      from [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
      where [DocumentNumber] >= (select ColumnValue from [CONSUMPTION_FINANCE].[udfGetDataFilterColumnValue]('SAP_Sales_Summary_Metrics', 'DocumentNumber', 'Exclude', 'GtEq'))
      and [DocumentNumber] < (select ColumnValue from [CONSUMPTION_FINANCE].[udfGetDataFilterColumnValue]('SAP_Sales_Summary_Metrics', 'DocumentNumber', 'Exclude', 'Lt'))
  ) 

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics])
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