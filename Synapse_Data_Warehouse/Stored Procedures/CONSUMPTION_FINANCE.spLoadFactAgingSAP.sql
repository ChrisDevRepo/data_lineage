CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactAgingSAP] AS
BEGIN

SET NOCOUNT ON

DECLARE @DfCompanyKey INT
DECLARE @DfDateFinanceKey INT

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @ProcShortName NVARCHAR(128) = 'spLoadFactAgingSAP'
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].['+@ProcShortName+']'
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
DECLARE @StatementTime DATETIME

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactAgingSAP])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

-- Get the default FK key values

SET @DfCompanyKey = (SELECT CompanyKey 
                     FROM [CONSUMPTION_FINANCE].[DimCompany] 
                     WHERE Company = 'df')
IF @DfCompanyKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimCompany] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

SET @DfDateFinanceKey = (SELECT MonthFinanceKey 
                        FROM [CONSUMPTION_FINANCE].[DimDateFinance]
                        WHERE Date = '1900-01-01')
IF @DfDateFinanceKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimDateFinance] is required but not found.' 
  RAISERROR (@MSG,16,1);
END


TRUNCATE TABLE [CONSUMPTION_FINANCE].[FactAgingSAP];

SET @StatementTime = GETDATE();

BEGIN TRANSACTION

INSERT INTO [CONSUMPTION_FINANCE].[FactAgingSAP]
(
  [PostingDateKey]
  ,[NetDueDateKey]
  ,[CompanyKey]
  ,[CompanyCode]
  ,[FiscalYear]
  ,[DocuNumber]
  ,[LineItemNumber]
  ,[DocuType]
  ,[DocuStatus]
  ,[CurrencyKey]
  ,[LocalCurrencyKey]
  ,[SecondLocalCurrency]
  ,[DocuHeaderText]
  ,[PostingDate]
  ,[DocuDate]
  ,[PostingKey]
  ,[DebitCreditIndicator]
  ,[AccountType]
  ,[BusinessAreaName]
  ,[DocuAmount]
  ,[LocalAmount]
  ,[SecondLocalAmount]
  ,[AssignmentNumber]
  ,[ItemText]
  ,[OrderNumber]
  ,[GLAccount]
  ,[BaselineDate]
  ,[PaymentTermsKey]
  ,[TaxCode]
  ,[ValueDate]
  ,[SecondLocalAccount]
  ,[NetDueDate]
  ,[CustomerNumber]
  ,[CustomerCountryKey]
  ,[CustomerName]
  ,[CreatedBy]
  ,[UpdatedBy]
  ,[CreatedAt]
  ,[UpdatedAt]
)
SELECT COALESCE (DDFP.[DateFinanceKey], @DfDateFinanceKey)
  ,COALESCE (DDFN.[DateFinanceKey], @DfDateFinanceKey)
  ,COALESCE (DC.[CompanyKey], @DfCompanyKey)
  ,[BUKRS] [CompanyCode]
  ,[GJAHR] [FiscalYear]
  ,[BELNR] [DocuNumber]
  ,[BUZEI] [NumberOfLineItem]
  ,[BLART] [DocuType]
  ,[BSTAT] [DocuStatus]
  ,[WAERS] [CurrencyKey]
  ,[HWAER] [LocalCurrencyKey]
  ,[HWAE2] [SecondLocalCurrency]
  ,[BKTXT] [DocuHeaderText]
  ,[BUDAT] [PostingDate]
  ,[BLDAT] [DocuDate]
  ,[BSCHL] [PostingKey]
  ,[SHKZG] [DebitCreditIndicator]
  ,[KOART] [AccountType]
  ,[GSBER] [BusinessAreaName]
  ,[WRBTR] [DocuAmount]
  ,[DMBTR] [LocalAmount]
  ,[DMBE2] [SecondLocalAmount]
  ,[ZUONR] [AssignmentNumber]
  ,[SGTXT] [ItemText]
  ,[AUFNR] [OrderNumber]
  ,[HKONT] [GLAccount]
  ,[ZFBDT] [BaselineDate]
  ,[ZTERM] [PaymentTermsKey]
  ,[MWSKZ] [TaxCode]
  ,[VALUT] [ValueDate]
  ,[ALTKT] [SecondLocalAccount]
  ,[NETDT] [NetDueDate]
  ,[KUNNR] [CustomerNumber]
  ,[LAND1] [CustomerCountryKey]
  ,[NAME1] [CustomerName]
  ,@ProcShortName [CreatedBy]
  ,@ProcShortName [UpdatedBy]
  ,@StatementTime [CreatedAt]
  ,@StatementTime [UpdatedAt]
FROM [STAGING_FINANCE_SAP].[ZFIV_DWH_AGING] S
LEFT JOIN [CONSUMPTION_FINANCE].[DimCompany] DC
  ON DC.Company =S.BUKRS 
    AND DC.isCurrent = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimDateFinance] DDFP
  ON DDFP.[Date] = SUBSTRING(S.BUDAT,1,4) + '-' + SUBSTRING(S.BUDAT,5,2) + '-' + SUBSTRING(S.BUDAT,7,2)
LEFT JOIN [CONSUMPTION_FINANCE].[DimDateFinance] DDFN
  ON DDFN.[Date] = SUBSTRING(S.NETDT,1,4) + '-' + SUBSTRING(S.NETDT,5,2) + '-' + SUBSTRING(S.NETDT,7,2) ;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactAgingSAP])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

IF @@TRANCOUNT > 0
  rollback transaction;

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