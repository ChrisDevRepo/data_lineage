CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactGLCOGNOS] AS
BEGIN

SET NOCOUNT ON

DECLARE @DfAccountKey INT
DECLARE @DfCompanyKey INT
DECLARE @DfDepartmentKey INT
DECLARE @DfPositionKey INT
DECLARE @DfMonthFinanceKey INT
DECLARE @DfConsTypeKey INT
DECLARE @DfActualityKey INT
DECLARE @DfCurrencyKey INT
DECLARE @DfAccountDetailsCognosKey INT

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @ProcShortName NVARCHAR(128) = 'spLoadFactGLCOGNOS'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactGLCognos])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

-- Get the default FK key values
SET @DfAccountKey = (SELECT AccountKey 
                     FROM [CONSUMPTION_FINANCE].[DimAccount] 
                     WHERE [Account] = 'default')
IF @DfAccountKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimAccount] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

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

SET @DfPositionKey = (SELECT PositionKey 
                        FROM [CONSUMPTION_FINANCE].[DimPosition] 
                        WHERE PositionID = 'df')
IF @DfPositionKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimPosition] is required but not found.' 
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

SET @DfConsTypeKey = (SELECT ConsTypeKey 
                      FROM [CONSUMPTION_FINANCE].[DimConsType] 
                      WHERE ConsType = 'df')
IF @DfConsTypeKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimConsType] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

SET @DfActualityKey = (SELECT ActualityKey 
                       FROM [CONSUMPTION_FINANCE].[DimActuality] 
                       WHERE Actuality = 'df')
IF @DfActualityKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimActuality] is required but not found.' 
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

SET @DfAccountDetailsCognosKey = (SELECT AccountDetailsCognosKey 
                                  FROM [CONSUMPTION_FINANCE].[DimAccountDetailsCognos] 
                                  WHERE [Account] = 'default')
IF @DfAccountDetailsCognosKey IS NULL
BEGIN
  SET @MSG = 'Default row for [CONSUMPTION_FINANCE].[DimAccountDetailsCognos] is required but not found.' 
  RAISERROR (@MSG,16,1);
END

TRUNCATE TABLE [CONSUMPTION_FINANCE].[FactGLCognos];

SET @StatementTime = GETDATE();

BEGIN TRANSACTION

INSERT INTO [CONSUMPTION_FINANCE].[FactGLCognos]
(
   [AccountKey]
  ,[CompanyKey]
  ,[DepartmentKey]
  ,[PositionKey]
  ,[MonthFinanceKey]
  ,[ConsTypeKey]
  ,[ActualityKey]
  ,[CurrencyKey]
  ,[AccountDetailsCognosKey]
  ,[Perakt]
  ,[Periode]
  ,[Year]
  ,[Month]
  ,[Actuality]
  ,[Company]
  ,[LocalCurrency]
  ,[Account]
  ,[TransCurrency]
  ,[OriginCompany]
  ,[Partner]
  ,[PartnerDim]
  ,[Dim1]
  ,[Dim2]
  ,[Dim3]
  ,[Dim4]
  ,[Btyp]
  ,[Etyp]
  ,[Vtyp]
  ,[KonsType]
  ,[JournalNbr]
  ,[LocalAmountYTD]
  ,[TransAmountYTD]
  ,[LocalAmountPTD]
  ,[TransAmountPTD]
  ,[CreatedBy]
  ,[UpdatedBy]
  ,[CreatedAt]
  ,[UpdatedAt]
)
SELECT 
   COALESCE (DA.[AccountKey], @DfAccountKey)
  ,COALESCE (DC.[CompanyKey], @DfCompanyKey)
  ,COALESCE (DD.[DepartmentKey], @DfDepartmentKey)
  ,COALESCE (DP.[PositionKey], @DfPositionKey)
  ,COALESCE (DMF.[MonthFinanceKey], @DfMonthFinanceKey)
  ,COALESCE (DCT.[ConsTypeKey], @DfConsTypeKey)
  ,COALESCE (DAct.[ActualityKey], @DfActualityKey)
  ,COALESCE (DCur.[CurrencyKey], @DfCurrencyKey)
  ,COALESCE (DADC.[AccountDetailsCognosKey], @DfAccountDetailsCognosKey)
  ,S.[Perakt]
  ,S.[Periode]
  ,S.[Year]
  ,S.[Month]
  ,S.[Actuality]
  ,S.[Company]
  ,S.[Currency] LocalCurrency
  ,S.[Account]
  ,S.[TransCurrency]
  ,S.[OriginCompany]
  ,S.[Partner]
  ,S.[PartnerDim]
  ,S.[Dim1]
  ,S.[Dim2]
  ,S.[Dim3]
  ,S.[Dim4]
  ,S.[Btyp]
  ,S.[Etyp]
  ,S.[Vtyp]
  ,S.[KonsType]
  ,S.[JournalNbr]
  ,S.[LocalAmountYTD]
  ,S.[TransAmountYTD]
  ,S.[LocalAmountPTD]
  ,S.[TransAmountPTD]
  ,@ProcShortName [CreatedBy]
  ,@ProcShortName [UpdatedBy]
  ,@StatementTime [CreatedAt]
  ,@StatementTime [UpdatedAt]
FROM [CONSUMPTION_FINANCE].[GLCognosData] S
LEFT JOIN [CONSUMPTION_FINANCE].[DimAccount] DA
  ON DA.[Account] = S.[Account] 
    AND DA.[isCurrent] = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimCompany] DC
  ON DC.Company = S.Company 
    AND DC.isCurrent = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimDepartment] DD
  ON DD.DeptID = S.Dim1 
    AND DD.isCurrent = 1 
LEFT JOIN [CONSUMPTION_FINANCE].[DimPosition] DP
  ON DP.PositionID = S.Dim1 
    AND DP.isCurrent = 1 
LEFT JOIN [CONSUMPTION_FINANCE].[DimMonthFinance] DMF
  ON DMF.[YearMonth] = S.[YEAR] + '-' + S.[Month]
LEFT JOIN [CONSUMPTION_FINANCE].[DimConsType] DCT
  ON DCT.ConsType = S.KonsType 
    AND DCT.isCurrent = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimActuality] DAct
  ON DAct.Actuality = S.Actuality  
    AND DAct.isCurrent = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimCurrency] DCur
  ON DCur.[Currency] = S.[Currency] 
    AND DCur.isCurrent = 1
LEFT JOIN [CONSUMPTION_FINANCE].[DimAccountDetailsCognos] DADC
  ON DADC.[Account] = S.[Account] 
    AND DADC.isCurrent = 1;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactGLCognos])
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