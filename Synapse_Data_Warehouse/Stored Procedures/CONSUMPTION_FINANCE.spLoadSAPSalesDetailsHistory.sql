CREATE PROC [CONSUMPTION_FINANCE].[spLoadSAPSalesDetailsHistory] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadSAPSalesDetailsHistory]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details_History])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Details_History];

begin transaction

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Details_History]
(
       [Year]
      ,[DocumentDate]
      ,[DocumentNumber]
      ,[Item]
      ,[Customer]
      ,[CustomerName]
      ,[ProjectName]
      ,[InvoiceDetails]
      ,[Assignment]
      ,[Advances]
      ,[CostType]
      ,[BusinessArea]
      ,[Currency]
      ,[NetAmountTC]
      ,[VatAmountTC]
      ,[TotalAmountTC]
      ,[Account]
      ,[AccountText]
      ,[PaymentTerms]
      ,[DueDate]
      ,[DatePaid]
      ,[InternalInvoice]
      ,[ContractDetails]
      ,[CompanyCode]
      ,[DC]
      ,[PrimaID]
)
select 
cast([Year] as char(4)) as [Year],
cast([DocDate] as date) as [DocumentDate],
cast([DocNumber] as varchar(10)) as [DocumentNumber],
cast([Item] as varchar(10)) as [Item],
cast([Customer] as varchar(10)) as [Customer],
cast([CustName] as nvarchar(250)) as [CustomerName],
case when left([Proj (Ord)], 1) = '''' then cast(substring([Proj (Ord)], 2, len([Proj (Ord)])) as nvarchar(100))
     else cast([Proj (Ord)] as nvarchar(100))
end as [ProjectName],
cast([InvoiceDet] as nvarchar(4000)) as [InvoiceDetails],
cast([Assignment] as varchar(50)) as [Assignment],
cast([Advances] as varchar(10)) as [Advances],
cast([CostTypeBA] as varchar(25)) as [CostType],
cast([BusArea] as varchar(10)) as [BusinessArea],
cast([Curr] as char(3)) as [Currency],
cast([Net TC] as decimal(19, 4)) as [NetAmountTC],
cast([Vat TC] as decimal(19, 4)) as [VatAmountTC],
cast([Tot TC] as decimal(19, 4)) as [TotalAmountTC],
cast([Account] as varchar(10)) as [Account],
cast([AcctText] as nvarchar(50)) as [AccountText],
cast([PayTerms] as varchar(10)) as [PaymentTerms],
cast([DueDate] as date) as [DueDate],
cast([DatePaid] as date) as [DatePaid],
cast([InternlInv] as nvarchar(25)) as [InternalInvoice],
cast([ContrctDet] as nvarchar(4000)) as [ContractDetails],
cast([CompCode] as varchar(10)) as [CompanyCode],
cast([D/C] as varchar(10)) as [DC],
cast([PrimaID] as varchar(10)) as [PrimaID]
from [STAGING_FINANCE_FILE].[SAP_Sales_Details_History];

update [CONSUMPTION_FINANCE].[SAP_Sales_details_History]
set CustomerName = 'Melinta Therapeutics, LLC'
where Customer = '100197';

update [CONSUMPTION_FINANCE].[SAP_Sales_Details_History]
set CustomerName = 'Merck Sharp & Dohme'
where CustomerName = 'Merck Sharp & Dome';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details_History])
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