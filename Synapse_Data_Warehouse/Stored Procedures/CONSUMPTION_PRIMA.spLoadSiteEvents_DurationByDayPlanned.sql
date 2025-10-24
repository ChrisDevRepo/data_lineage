CREATE PROC [CONSUMPTION_PRIMA].[spLoadSiteEvents_DurationByDayPlanned] AS
BEGIN

SET NOCOUNT ON

BEGIN TRY

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_MPS].[spLoadSiteEvents_DurationByDayPlanned]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )


DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[SiteEvents_DurationByDayPlanned])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

                          
IF ((SELECT Count(1) FROM [CONSUMPTION_PRIMA].[SiteEvents_DurationByDayPlanned]) > 0 )
BEGIN
	TRUNCATE TABLE [CONSUMPTION_PRIMA].[SiteEvents_DurationByDayPlanned]
END

-- Requirements: This feature was released on 18-11-24. 
DECLARE @PrimaImplementationReleaseDay DATE = '18-Nov-2024' 


;WITH ParsedData AS (
    SELECT
        Site_Event_Id as SiteEventId,
        Primary_Monitor_Id as PrimaryMonitorId,
        CAST(json_value(item.value, '$.daynum') AS NVARCHAR(254)) AS DayNumber,
        CAST(json_value(employee.value, '$.employeeId') AS INT) AS EmployeeId,
        DATEADD(day,  CAST(CAST(json_value(item.value, '$.daynum') AS NVARCHAR(254)) as INT)- 1, se.Forecast_Date) SiteEventForecastVisitDate,
        CASE 
            WHEN json_value(employee.value, '$.visitType') = 'remote' THEN 1 
            ELSE 0 
        END AS IsRemote,
        CASE 
            WHEN se.Primary_Monitor_Id = json_value(employee.value, '$.employeeId') THEN 1 
            ELSE 0 
        END AS IsPrimaryMonitor,
        se.duration_by_day_planned as FullJsonObject,
        item.value AS NestedJsonObject
    FROM [CONSUMPTION_PRIMA].[SiteEvents] AS se
    CROSS APPLY OPENJSON(duration_by_day_planned) AS item
    CROSS APPLY OPENJSON(item.value, '$.employees') AS employee
	WHERE
		se.Forecast_date>= @PrimaImplementationReleaseDay
		and ISJSON(duration_by_day_planned) = 1
)
INSERT INTO [CONSUMPTION_PRIMA].[SiteEvents_DurationByDayPlanned]
(
    SiteEventId,
    PrimaryMonitorId,
    DayNumber,
    EmployeeId,
    SiteEventForecastVisitDate,
    IsRemote,
    IsPrimaryMonitor,
    FullJsonObject,
    NestedJsonObject
)
SELECT
    SiteEventId,
    PrimaryMonitorId,
    DayNumber,
    EmployeeId,
    SiteEventForecastVisitDate,
    IsRemote,
    IsPrimaryMonitor,
    FullJsonObject,
    NestedJsonObject
FROM ParsedData;
	



exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount
 
 
SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[SiteEvents_DurationByDayPlanned])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'
 
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'Consumption Prima ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0)
 
END TRY
/*----------------------------------------------------------------------*/
BEGIN CATCH
 
IF @@TRANCOUNT > 0
BEGIN
  rollback transaction
END
 
DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048)
 
-- store all the error information for logging the error
SELECT @ErrorNum       = ERROR_NUMBER()
      ,@ErrorLine      = 0
      ,@ErrorSeverity  = ERROR_SEVERITY()
      ,@ErrorState     = ERROR_STATE()
      ,@ErrorProcedure = ERROR_PROCEDURE()
      ,@ErrorMessage   = ERROR_MESSAGE()
 
SET @MSG = @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ')
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'Consumption Prima ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
RAISERROR (@MSG ,@ErrorSeverity,@ErrorState)
 
END CATCH
 
END
