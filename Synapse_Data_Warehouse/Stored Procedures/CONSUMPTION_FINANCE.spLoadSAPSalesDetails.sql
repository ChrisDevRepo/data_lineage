CREATE PROC [CONSUMPTION_FINANCE].[spLoadSAPSalesDetails] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadSAPSalesDetails]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Details];

begin transaction

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Details]
(
       [CompanyCode]
      ,[DocumentNumber]
      ,[Year]
	  ,[Item]
      ,[DocumentDate]
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
      ,[DC]
      ,[PrimaID]
	  ,[SalesForceNumber]
)
select
cast([BUKRS] as varchar(10)) as [CompanyCode],
cast([BELNR] as varchar(10)) as [DocumentNumber],
cast([GJAHR] as char(4)) as [Year],
cast([BUZEI] as varchar(10)) as [Item],
try_cast([BLDAT] as date) as [DocumentDate],
cast([KUNNR] as varchar(10)) as [Customer],
cast([CUST_NAME] as nvarchar(250)) as [CustomerName],
cast([KTEXT] as nvarchar(100)) as [ProjectName],
cast([INVDETTX] as nvarchar(4000)) as [InvoiceDetails],
cast([ZUONR] as varchar(50)) as [Assignment],
cast([FL_ADV_ACCT] as varchar(10)) as [Advances],
cast([GTEXT] as varchar(25)) as [CostType],
cast([GSBER] as varchar(10)) as [BusinessArea],
cast([WAERS] as char(3)) as [Currency],
cast([WRBTR] as decimal(19,4)) as [NetAmountTC],
cast([VATBTR] as decimal(19,4)) as [VatAmountTC],
cast([DEBBTR] as decimal(19,4)) as [TotalAmountTC],
cast([HKONT] as varchar(10)) as [Account],
cast([TXT20] as nvarchar(50)) as [AccountText],
cast([ZTERM] as varchar(10)) as [PaymentTerms],
try_cast([DUEDT] as date) as [DueDate],
try_cast([AUGDT] as date) as [DatePaid],
cast([Z_PAID_ADV] as nvarchar(25)) as [InternalInvoice],
cast([ZKTXT] as nvarchar(4000)) as [ContractDetails],
cast([SHKZG] as varchar(10)) as [DC],
cast([PRIMA_ID] as varchar(10)) as [PrimaID],
cast([SF_NBR] as varchar(25)) as [SalesForceNumber]
from [STAGING_FINANCE_SAP].[SAP_Sales_Details];

/***
truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Details];

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Details]
(
       [CompanyCode]
      ,[DocumentNumber]
      ,[Year]
	  ,[Item]
      ,[DocumentDate]
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
      ,[DC]
      ,[PrimaID]
)
select
cast([CompCode] as varchar(10)) as [CompanyCode],
cast([DocNumber] as varchar(10)) as [DocumentNumber],
cast([Year] as char(4)) as [Year],
cast([Item] as varchar(10)) as [Item],
convert(date, [DocDate], 104) as [DocumentDate],
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
cast([Net TC] as decimal(19,4)) as [NetAmountTC],
cast([Vat TC] as decimal(19,4)) as [VatAmountTC],
cast([Tot TC] as decimal(19,4)) as [TotalAmountTC],
cast([Account] as varchar(10)) as [Account],
cast([AcctText] as nvarchar(50)) as [AccountText],
cast([PayTerms] as varchar(10)) as [PaymentTerms],
convert(date, [DueDate], 104) as [DueDate],
convert(date, [DatePaid], 104) as [DatePaid],
cast([InternlInv] as nvarchar(25)) as [InternalInvoice],
cast([ContrctDet] as nvarchar(4000)) as [ContractDetails],
cast([D/C] as varchar(10)) as [DC],
cast([PrimaID] as varchar(10)) as [PrimaID]
from [STAGING_FINANCE_FILE].[SAP_Sales_Details];

update [CONSUMPTION_FINANCE].[SAP_Sales_Details]
set DocumentDate = '2017-04-20'
where DocumentNumber ='226854';

update [CONSUMPTION_FINANCE].[SAP_Sales_Details]
set DocumentDate = '2023-05-30'
where documentnumber in ('256683','802030');
***/

update [CONSUMPTION_FINANCE].[SAP_Sales_Details]
set DocumentDate = '2017-04-20'
where DocumentNumber ='0000226854';

update [CONSUMPTION_FINANCE].[SAP_Sales_Details]
set DocumentDate = '2023-05-30'
where documentnumber in ('0000256683','0000802030');

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details])
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