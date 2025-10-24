CREATE PROC [CONSUMPTION_ClinOpsFinance].spLoadDateRange
AS
BEGIN

-- EXEC [CONSUMPTION_ClinOpsFinance].[spLoadDateRange] 
-- SELECT TOP (100) * FROM [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadDateRange]'  order by CreateDateTimeUTC desc

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadDateRange'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY

DECLARE @MonthToClose DATETIME
  ,@CloseDate DATETIME 
  ,@Today DATETIME  
  ,@YearsToGoBack SMALLINT   
  ,@RangeCloseType VARCHAR(10) 
  ,@BaseYear SMALLINT 

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

SELECT @Today = GETUTCDATE(), @YearsToGoBack = 5, @RangeCloseType = 'Month'

-- if config table is empty - run with @BaseYear = NULL to initialize it
IF NOT EXISTS(SELECT TOP 1 1 FROM [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config )
BEGIN
  EXEC [CONSUMPTION_ClinOpsFinance].[spLoadDateRangeMonthClose_Config] @BaseYear = NULL
END
ELSE
BEGIN
-- run with year from today's date
  SELECT @BaseYear = DATEPART(YEAR, @Today)
  EXEC [CONSUMPTION_ClinOpsFinance].[spLoadDateRangeMonthClose_Config] @BaseYear = @BaseYear
END

-- Get the Configuration Month Close  and Close Date for the latest closed month that is <= today's date
SELECT @MonthToClose = MonthToClose, @CloseDate=CloseDate
FROM [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config 
WHERE RowId = (SELECT MAX(RowID) 
               FROM [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config 
               WHERE CloseDate <= @Today);

IF @MonthToClose IS NULL OR @CloseDate IS NULL
BEGIN
  SELECT @ErrorMsg = 'Based on Today: ' + CAST(@Today AS VARCHAR(20)) 
    + ' there is no valid [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config row';

  PRINT @ErrorMsg;

  THROW 200000, @ErrorMsg, 1;
END

EXEC [CONSUMPTION_ClinOpsFinance].[spLoadDateRangeDetails]
   @MonthToClose = @MonthToClose
  ,@CloseDate =  @CloseDate
  ,@Today = @Today  
  ,@YearsToGoBack = @YearsToGoBack  
  ,@RangeCloseType = @RangeCloseType
  
SELECT @MSG  = 'End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

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
