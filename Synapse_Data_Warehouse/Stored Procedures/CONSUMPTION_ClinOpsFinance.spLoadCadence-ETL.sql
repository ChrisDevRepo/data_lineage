CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadCadence-ETL]
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCadenceBudgetDataProcessing'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'Cadence-ETL'
  ,@ErrorMsg NVARCHAR(2048) = ''
  
DECLARE @MSG VARCHAR(max) = 'ETL Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0
  ,@Count  BIGINT = 0
  ,@ProcessingTime DATETIME = GETDATE();

BEGIN TRY

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

EXEC [STAGING_CADENCE].[spLoadCadenceExtractTaskCountry]
EXEC [STAGING_CADENCE].[spLoadCadenceExtractFunctionLocation]
EXEC [STAGING_CADENCE].[spLoadCadenceOutOfScopeRecords]
EXEC [STAGING_CADENCE].[spLoadTaskAndFunctionData]
EXEC [STAGING_CADENCE].[spLoadCountryReallocateTS]
EXEC [STAGING_CADENCE].[spLoadNoCountryReallocateTS]
EXEC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_Case1]
EXEC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_Case2]
EXEC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_Case3]
EXEC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_Case4]
EXEC [STAGING_CADENCE].[spLoadFinalCountryReallocateTS_NoCountry]
EXEC [STAGING_CADENCE].[spLoadCadenceCase0Data]
EXEC [STAGING_CADENCE].[spLoadMonthlyTaskTaskCountry]
EXEC [STAGING_CADENCE].[spLoadMonthlyTaskTaskCountryGlobalNoCountry]
EXEC [STAGING_CADENCE].[spLoadReconciliation_Case4.5]
EXEC [STAGING_CADENCE].[spLoadReconciliation_Case5-6]
EXEC [STAGING_CADENCE].[spLoadNoCountryReallocateTS]

-- To Populate final [CadenceBudgetData] table.
EXEC [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudgetData]

SELECT @ProcessingTime = GETDATE();

SELECT @MSG  = 'ETL End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
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
GO