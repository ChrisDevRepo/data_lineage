CREATE PROC [CONSUMPTION_FINANCE].[spLoadSAPSalesSummary] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadSAPSalesSummary]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Summary];

begin transaction

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
(
       [CompanyCode]
      ,[DocumentNumber]
	  ,[Year]
      ,[DocumentDate]
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
)
select
cast([BUKRS] as varchar(10)) as [CompanyCode],
cast([BELNR] as varchar(10)) as [DocumentNumber],
cast([GJAHR] as char(4)) as [Year],
try_cast([BLDAT] as date) as [DocumentDate],
cast([KUNNR] as varchar(10)) as [Customer],
cast([CUST_NAME] as nvarchar(250)) as [CustomerName],
cast([KTEXT] as nvarchar(100)) as [ProjectName],
cast([INVDETTX] as nvarchar(4000)) as [InvoiceDetails],
cast([FL_ADV_ACCT] as char(1)) as [Advances],
cast([GTEXT] as varchar(25)) as [CostType],
cast([GSBER] as varchar(10)) as [BusinessArea],
cast([WAERS] as char(3)) as [Currency],
cast([WRBTR] as decimal(19,4)) as [NetAmountTC],
cast([VATBTR] as decimal(19,4)) as [VatAmountTC],
cast([DEBBTR] as decimal(19,4)) as [TotAmountTC],
cast([ZTERM] as varchar(10)) as [PaymentTerms],
try_cast([DUEDT] as date) as [DueDate],
try_cast([AUGDT] as date) as [DatePaid],
cast([ZKTXT] as nvarchar(4000)) as [ContractDetails],
cast([PRIMA_ID] as varchar(10)) as [PrimaID],
cast([SF_NBR] as varchar(25)) as [SalesForceNumber],
try_cast([BUDAT] as date) as [PostDate],
cast([NETCHF] as decimal(19,4)) as [NetAmountCHF],
cast([VATCHF] as decimal(19,4)) as [VatAmountCHF],
cast([TOTCHF] as decimal(19,4)) as [TotAmountCHF],
cast([RTCCHF] as decimal(38,18)) as [RteTcCHF],
cast([NETUSD] as decimal(19,4)) as [NetAmountUSD],
cast([VATUSD] as decimal(19,4)) as [VatAmountUSD],
cast([TOTUSD] as decimal(19,4)) as [TotAmountUSD],
cast([RTCUSD] as decimal(38,18)) as [RteTcUSD],
cast([NETEUR] as decimal(19,4)) as [NetAmountEUR],
cast([VATEUR] as decimal(19,4)) as [VatAmountEUR],
cast([TOTEUR] as decimal(19,4)) as [TotAmountEUR],
cast([RTCEUR] as decimal(38,18)) as [RteTcEUR],
cast([NETGBP] as decimal(19,4)) as [NetAmountGBP],
cast([VATGBP] as decimal(19,4)) as [VatAmountGBP],
cast([TOTGBP] as decimal(19,4)) as [TotAmountGBP],
cast([RTCGBP] as decimal(38,18)) as [RteTcGBP],
try_cast([ACCPYR] as date) as [AccountPreviousYear]
from [STAGING_FINANCE_SAP].[SAP_Sales_Summary];

/***
truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Summary];

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
(
       [DocumentNumber]
      ,[Year]
      ,[DocumentDate]
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
)
select
cast([DocNumber] as varchar(10)) as [DocumentNumber],
cast([Year] as char(4)) as [Year],
convert(date, [DocDate], 104) as [DocumentDate],
cast([Customer] as varchar(10)) as [Customer],
cast([CustName] as nvarchar(250)) as [CustomerName],
case when left([Proj (Ord)], 1) = '''' then cast(substring([Proj (Ord)], 2, len([Proj (Ord)])) as nvarchar(100))
     else cast([Proj (Ord)] as nvarchar(100))
end as [ProjectName],
cast([InvoiceDet] as nvarchar(4000)) as [InvoiceDetails],
cast([Advances] as char(1)) as [Advances],
cast([CostTypeBA] as varchar(25)) as [CostType],
cast([BusArea] as varchar(10)) as [BusinessArea],
cast([Curr] as char(3)) as [Currency],
cast([Net TC] as decimal(19,4)) as [NetAmountTC],
cast([Vat TC] as decimal(19,4)) as [VatAmountTC],
cast([Tot TC] as decimal(19,4)) as [TotAmountTC],
cast([PayTerms] as varchar(10)) as [PaymentTerms],
convert(date, [DueDate], 104) as [DueDate],
convert(date, [DatePaid], 104) as [DatePaid],
cast([ContrctDet] as nvarchar(4000)) as [ContractDetails],
cast([PrimaID] as varchar(10)) as [PrimaID],
cast([SalesForceNbr] as varchar(25)) as [SalesForceNumber],
convert(date, [PstDate], 104) as [PostDate],
cast([Net CHF] as decimal(19,4)) as [NetAmountCHF],
cast([Vat CHF] as decimal(19,4)) as [VatAmountCHF],
cast([Tot CHF] as decimal(19,4)) as [TotAmountCHF],
cast([Rte TC/CHF] as decimal(38,18)) as [RteTcCHF],
cast([Net USD] as decimal(19,4)) as [NetAmountUSD],
cast([Vat USD] as decimal(19,4)) as [VatAmountUSD],
cast([Tot USD] as decimal(19,4)) as [TotAmountUSD],
cast([Rte TC/USD] as decimal(38,18)) as [RteTcUSD],
cast([Net EUR] as decimal(19,4)) as [NetAmountEUR],
cast([Vat EUR] as decimal(19,4)) as [VatAmountEUR],
cast([Tot EUR] as decimal(19,4)) as [TotAmountEUR],
cast([Rte TC/EUR] as decimal(38,18)) as [RteTcEUR],
cast([Net GBP] as decimal(19,4)) as [NetAmountGBP],
cast([Vat GBP] as decimal(19,4)) as [VatAmountGBP],
cast([Tot GBP] as decimal(19,4)) as [TotAmountGBP],
cast([Rte TC/GBP] as decimal(38,18)) as [RteTcGBP],
convert(date, [AccPrevYr], 104) as [AccountPreviousYear]
from [STAGING_FINANCE_FILE].[SAP_Sales_Summary];

update [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
set DocumentDate = '2017-04-20'
where documentnumber ='226854';

update [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
set DocumentDate = '2023-05-30'
where documentnumber in ('256683','802030');
***/

update [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
set DocumentDate = '2017-04-20'
where documentnumber ='0000226854';

update [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
set DocumentDate = '2023-05-30'
where documentnumber in ('0000256683','0000802030');

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary])
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