CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadProductivityMetrics_Post]
AS

BEGIN

SET NOCOUNT ON

--EXEC [CONSUMPTION_ClinOpsFinance].[spLoadProductivity_Post]
-- 
-- SELECT TOP 100 * FROM [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' order by CreateDateTimeUTC desc


SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadProductivity_Post'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0
  ,@Count  BIGINT = 0
  ,@ProcessingTime DATETIME = GETDATE();
   
BEGIN TRY

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL


/******************************************************
-- To refresh date ranges based on the Today (Run date)
******************************************************/

EXEC [CONSUMPTION_ClinOpsFinance].[spLoadDateRange];

SELECT @MSG  = 'Completed Run of [CONSUMPTION_ClinOpsFinance].[spLoadDateRange] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();


/*********************************************************
-- To refresh Employee Contract Utilization related tables
*********************************************************/
EXEC [CONSUMPTION_ClinOpsFinance].[spLoadHrContractAttendance] ;

SELECT @MSG  = 'Completed Run of [CONSUMPTION_ClinOpsFinance].[spLoadHrContractAttendance] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds';
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();

EXEC [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization];

SELECT @MSG  = 'Completed Run of [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds';
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();


/**********************************************************************************
-- To refresh Cadence, Labor Cost , Employee Contract Utilization Junction  table
**********************************************************************************/

EXEC [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudget_LaborCost_PrimaContractUtilization_Junc];

SELECT @MSG  = 'Completed Run of [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudget_LaborCost_PrimaContractUtilization_Junc] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds';
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();



/**********************************************************************************
-- To refresh Cadence, Labor Cost , Employee Contract Utilization Post tables
**********************************************************************************/

EXEC [CONSUMPTION_ClinOpsFinance].[spLoadFactLaborCostForEarnedValue_Post];

SELECT @MSG  = 'Completed Run of [CONSUMPTION_ClinOpsFinance].[spLoadFactLaborCostForEarnedValue_Post] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds';
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();


EXEC [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Post];

SELECT @MSG  = 'Completed Run of [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Post] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds';
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();


EXEC [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudgetData_Post];

SELECT @MSG  = 'Completed Run of [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudgetData_Post] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds';
PRINT @MSG
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
SELECT @ProcessingTime = GETDATE();



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
 
