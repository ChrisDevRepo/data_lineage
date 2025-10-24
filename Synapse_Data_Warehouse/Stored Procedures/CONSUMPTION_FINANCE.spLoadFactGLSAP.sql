CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactGLSAP] AS
BEGIN

SET NOCOUNT ON

DECLARE @DfCompanyKey INT
DECLARE @DfDepartmentKey INT
DECLARE @DfMonthFinanceKey INT
DECLARE @DfCurrencyKey INT
DECLARE @DfAccountDetailsSAPKey INT

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @ProcShortName NVARCHAR(128) = 'spLoadFactGLSAP'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactGLSAP])
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

SET @DfDepartmentKey = (SELECT DepartmentKey 
                        FROM [CONSUMPTION_FINANCE].[DimDepartment] 
                        WHERE DeptID = 'df')
IF @DfDepartmentKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimDepartment] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

SET @DfMonthFinanceKey = (SELECT MonthFinanceKey 
                        FROM [CONSUMPTION_FINANCE].[DimMonthFinance]
                        WHERE YearMonth = '1900-01')
IF @DfMonthFinanceKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimMonthFinance] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

SET @DfCurrencyKey = (SELECT CurrencyKey 
                       FROM [CONSUMPTION_FINANCE].[DimCurrency]
                       WHERE [Currency] = 'df')
IF @DfCurrencyKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimCurrency] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

SET @DfAccountDetailsSAPKey = (SELECT AccountDetailsSAPKey 
                                  FROM [CONSUMPTION_FINANCE].[DimAccountDetailsSAP] 
                                  WHERE [Account] = 'default')
IF @DfAccountDetailsSAPKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimAccountDetailsSAP] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

TRUNCATE TABLE [CONSUMPTION_FINANCE].[FactGLSAP];

SET @StatementTime = GETDATE();

BEGIN TRANSACTION

INSERT INTO [CONSUMPTION_FINANCE].[FactGLSAP]
(
  [CompanyKey]
  ,[DepartmentKey]
  ,[MonthFinanceKey]
  ,[CurrencyKey]
  ,[AccountDetailsSAPKey]
  ,[Client]
  ,[Type]
  ,[Periode]
  ,[PeriodName]
  ,[PeriodDescription]
  ,[Year]
  ,[Month]
  ,[CompanyCode]
  ,[GLAccountNumber]
  ,[GLAccountNumberShort]
  ,[GroupAccountNumber]
  ,[BusinessArea]
  ,[CompanyIDofTradingPartner]
  ,[CostCenter]
  ,[Department]
  ,[DIM3CurrForCognos]
  ,[Currency]
  ,[Amount]
  ,[CreatedBy]
  ,[UpdatedBy]
  ,[CreatedAt]
  ,[UpdatedAt]
)
SELECT COALESCE (DC.[CompanyKey], @DfCompanyKey)
  ,COALESCE (DD.[DepartmentKey] ,@DfDepartmentKey)
  ,COALESCE (DMF.[MonthFinanceKey], @DfMonthFinanceKey)
  ,COALESCE (DCur.[CurrencyKey], @DfCurrencyKey)
  ,COALESCE ( DADS.[AccountDetailsSAPKey], @DfAccountDetailsSAPKey)
  ,S.[MANDT]
  ,S.[Type]
  ,S.[Periode]
  ,S.[PeriodName]
  ,S.[PeriodDescription]
  ,S.[Year]
  ,S.[Month]
  ,S.[CompanyCode]
  ,S.[GLAccountNumber]
  ,S.[GLAccountNumberShort]
  ,S.[GroupAccountNumber]
  ,S.[BusinessArea]
  ,S.[CompanyIDofTradingPartner]
  ,S.[CostCenter]
  ,S.[Department]
  ,S.[DIM3CurrForCognos]
  ,S.[Currency]
  ,S.[Amount]
  ,@ProcShortName [CreatedBy]
  ,@ProcShortName [UpdatedBy]
  ,@StatementTime [CreatedAt]
  ,@StatementTime [UpdatedAt]
FROM [CONSUMPTION_FINANCE].[SAP_PowerBI_FACT] S
LEFT JOIN [CONSUMPTION_FINANCE].[DimCompany] DC
  ON DC.Company =S.CompanyCode 
    AND DC.isCurrent = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimDepartment] DD
  ON DD.DeptID =S.Department 
    AND DD.isCurrent = 1 
LEFT JOIN [CONSUMPTION_FINANCE].[DimMonthFinance] DMF
  ON DMF.[YearMonth] =S.[YEAR] + '-' + S.[Month]
LEFT JOIN [CONSUMPTION_FINANCE].[DimCurrency] DCur
  ON DCur.[Currency] = S.[Currency] 
    AND DCur.isCurrent = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimAccountDetailsSAP] DADS
  ON  DADS.[Account] = S.[GLAccountNumber] 
    AND  DADS.isCurrent = 1;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactGLSAP])
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
