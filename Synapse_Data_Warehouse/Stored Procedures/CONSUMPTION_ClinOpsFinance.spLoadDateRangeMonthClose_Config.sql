CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadDateRangeMonthClose_Config] @BaseYear SMALLINT AS
BEGIN

-- To run proc:

-- EXEC [CONSUMPTION_ClinOpsFinance].[spLoadDateRangeMonthClose_Config] @BaseYear = NULL

-- To Check Results
--SELECT * FROM [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config ORDER BY RowID
-- SELECT TOP (100) * FROM [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadDateRangeMonthClose_Config]'  order by CreateDateTimeUTC desc

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadDateRangeMonthClose_Config'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY

Declare @StartYear SMALLINT
,@ConfigMaxYear SMALLINT
,@TestStartYear SMALLINT
,@EndYear SMALLINT
,@LoopCountYear SMALLINT 
,@LoopCountMonth SMALLINT 
,@CloseDate DATE
,@RowID SMALLINT
,@MonthToClose DATETIME
,@CloseQtr SMALLINT
,@CurrentYear SMALLINT = DATEPART(YEAR,GETUTCDATE())

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

SELECT @MSG = '@BaseYear: ' +  ISNULL(CAST(@BaseYear AS VARCHAR(30)),'NULL');
SELECT @MSG = 'Parameter values: ' + @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL


SELECT @BaseYear = CASE WHEN @BaseYear IS NULL THEN DATEPART(YEAR, GETDATE()) ELSE @BaseYear END

SELECT @ConfigMaxYear = MAX(Year) , @RowID = MAX(RowID)
FROM [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config 

-- Handle [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config being empty
SELECT @ConfigMaxYear = ISNULL(@ConfigMaxYear, 2022), @RowID = ISNULL(@RowID, 0)

IF @ConfigMaxYear <= @BaseYear 
BEGIN

  SELECT @StartYear = @ConfigMaxYear + 1
    , @EndYear = CASE WHEN @BaseYear >= @CurrentYear THEN  @BaseYear + 1 ELSE @CurrentYear + 1 END
   
END
ELSE
BEGIN

  SELECT @MSG = 'There are already rows in [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config For Year: ' + CAST(@ConfigMaxYear AS VARCHAR(10)) +
      '. Modifications based on @BaseYear value: ' + ISNULL(CAST(@BaseYear AS VARCHAR(10)),'NULL') + ' will not be considered as user modifications might get overwritten';
  PRINT @MSG
  
  EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

  SELECT @StartYear = @ConfigMaxYear + 1
    , @EndYear = 0

END

SELECT @LoopCountYear = @StartYear, @RowID = @RowID + 1

WHILE @LoopCountYear <= @EndYear
BEGIN
  PRINT 'Year: ' + CAST (@LoopCountYear AS VARCHAR(10))

  SELECT @LoopCountMonth = 1

  WHILE @LoopCountMonth <= 12
  BEGIN
    PRINT 'Month: ' + CAST (@LoopCountMonth AS VARCHAR(10)) + ' in Year: ' + CAST (@LoopCountYear AS VARCHAR(10))

    -- Determine default close date which is the 25th of the next month for December and the 15th of the next month for all other months
    SELECT @CloseDate = DATEADD(MONTH, 1, CONVERT(DATE, CAST(@LoopCountYear AS VARCHAR(6)) +'/' + CAST(@LoopCountMonth  AS VARCHAR(4)) + '/' 
      + CASE WHEN @LoopCountMonth = 12 THEN '25' ELSE '15' END,120))
      ,@MonthToClose = CONVERT(DATE, CAST(@LoopCountYear AS VARCHAR(6)) +'/' + CAST(@LoopCountMonth  AS VARCHAR(4)) + '/' + '01',120)

    SELECT @CloseQtr = CASE WHEN @LoopCountMonth % 3 = 0 THEN @LoopCountMonth/3 ELSE NULL END

    Insert INTO [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config
    (RowID, [Year], [MonthNumber],[MonthToClose], CloseQtr, CloseDate,CreatedBy,UpdatedBy,CreatedAt,UpdatedAt)
    SELECT @RowID, @LoopCountYear , @LoopCountMonth,@MonthToClose, @CloseQtr, @CloseDate,SUSER_SNAME(),SUSER_SNAME(),GETUTCDATE(),GETUTCDATE() 

    SELECT @LoopCountMonth = @LoopCountMonth + 1, @RowID = @RowID + 1;
  END

  SELECT @LoopCountYear = @LoopCountYear + 1
END

--END


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