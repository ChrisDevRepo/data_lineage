CREATE PROC [CONSUMPTION_FINANCE].[spLoadSAPSalesDetailsMetrics] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadSAPSalesDetailsMetrics]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details_Metrics])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Details_Metrics];

begin transaction

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Details_Metrics]
select
Account,
AccountText,
Advances,
Assignment,
BusinessArea,
CompanyCode,
ContractDetails,
CostType,
Currency,
Customer,
CustomerName,
DatePaid,
DC,
DocumentDate,
DocumentNumber,
DueDate,
InternalInvoice,
InvoiceDetails,
Item,
NetAmountTC,
PaymentTerms,
PrimaID,
ProjectName,
TotalAmountTC,
ConversionRate,
CHFTotalAmountTC,
VatAmountTC,
Year

from(
select 
t.[Account],
        t.[AccountText],
        t.[Advances],
        t.[Assignment],
        t.[BusinessArea],
        t.[CompanyCode],
        t.[ContractDetails],
        t.[CostType],
        t.[Currency],
        t.[Customer],
        t.[CustomerName],
        t.[DatePaid],
        t.[DC],
        t.[DocumentDate],
        t.[DocumentNumber],
        t.[DueDate],
        t.[InternalInvoice],
        t.[InvoiceDetails],
        t.[Item],
        t.[NetAmountTC],
        t.[PaymentTerms],
        t.[PrimaID],
        s.[ProjectName],
        t.[TotalAmountTC],
        Case when t.TotalAmountTC = '0' then  Null
		     when t.Currency = 'CHF' then  Null         
         else r.UKURS
         END as ConversionRate,
        Case when t.TotalAmountTC = '0' then Null
		     when  t.Currency = 'CHF' then t.TotalAmountTC       
        else format(ROUND( t.TotalAmountTC * r.UKURS,2),'0.##')
        END as CHFTotalAmountTC,
        t.[VatAmountTC],
        t.[Year]

from (
SELECT
        [Account],
        [AccountText],
        [Advances],
        [Assignment],
        [BusinessArea],
        [CompanyCode],
        [ContractDetails],
        [CostType],
        [Currency],
        [Customer],
        [CustomerName],
        [DatePaid],
        [DC],
        [DocumentDate],
        [DocumentNumber],
        [DueDate],
        [InternalInvoice],
        [InvoiceDetails],
        [Item],
        [NetAmountTC],
        [PaymentTerms],
        [PrimaID],
        [ProjectName],
        [TotalAmountTC],
        [VatAmountTC],
        [Year]
    FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details_History]
   
    UNION ALL
   
    SELECT
        [Account],
        [AccountText],
        [Advances],
        [Assignment],
        [BusinessArea],
        [CompanyCode],
        [ContractDetails],
        [CostType],
        [Currency],
        [Customer],
        [CustomerName],
        [DatePaid],
        [DC],
        [DocumentDate],
        [DocumentNumber],
        [DueDate],
        [InternalInvoice],
        [InvoiceDetails],
        [Item],
        [NetAmountTC],
        [PaymentTerms],
        [PrimaID],
        [ProjectName],
        [TotalAmountTC],
        [VatAmountTC],
        [Year]
    FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details]

) as t

inner join [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics] s
on t.DocumentNumber = s.DocumentNumber AND t.DocumentDate = s.DocumentDate 
LEFT JOIN [CONSUMPTION_FINANCE].[SAP_Tcurr] r
ON t.Currency = r.FCURR
AND r.GDATU = Dateadd(month, Datediff(month, 0, t.documentdate),0)
WHERE t.DocumentDate >= '2015-01-01'
)r

	

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details_Metrics])
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
GO