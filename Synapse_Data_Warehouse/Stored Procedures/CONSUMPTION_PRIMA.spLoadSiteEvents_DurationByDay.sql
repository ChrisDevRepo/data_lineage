CREATE PROC [CONSUMPTION_PRIMA].[spLoadSiteEvents_DurationByDay] AS
BEGIN

SET NOCOUNT ON

BEGIN TRY

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_MPS].[spLoadSiteEvents_DurationByDay]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )


DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[SiteEvents_DurationByDay])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 


IF ((SELECT Count(1) FROM [CONSUMPTION_PRIMA].[SiteEvents_DurationByDay]) > 0 )
BEGIN
	TRUNCATE TABLE [CONSUMPTION_PRIMA].[SiteEvents_DurationByDay]
END

---- Requirements: This feature was released on 18-11-24. 
DECLARE @PrimaImplementationReleaseDay DATE = '18-Nov-2024' 


;WITH ParsedData AS (
    SELECT
        Site_Event_Id as SiteEventId,
        Primary_Monitor_Id as PrimaryMonitorId,
        CAST(json_value(item.value, '$.daynum') AS NVARCHAR(254)) AS DayNumber,
        CAST(json_value(employee.value, '$.employeeId') AS INT) AS EmployeeId,
        DATEADD(day,  CAST(CAST(json_value(item.value, '$.daynum') AS NVARCHAR(254)) as INT)- 1, se.actual_Date) SiteEventActualVisitDate,
		json_value(employee.value, '$.duration') AS DurationInMinutes,
        json_value(employee.value, '$.isRemote') AS IsRemote,
        CASE 
            WHEN se.Primary_Monitor_Id = json_value(employee.value, '$.employeeId') THEN 1 
            ELSE 0 
        END AS IsPrimaryMonitor,
        se.duration_by_day as FullJsonObject,
        item.value AS NestedJsonObject
    FROM [CONSUMPTION_PRIMA].[SiteEvents] AS se
    CROSS APPLY OPENJSON(duration_by_day) AS item
    CROSS APPLY OPENJSON(item.value, '$.employees') AS employee
	WHERE
		se.actual_Date>= @PrimaImplementationReleaseDay
		and ISJSON(duration_by_day) = 1
)
INSERT INTO [CONSUMPTION_PRIMA].[SiteEvents_DurationByDay]
(
    SiteEventId,
    PrimaryMonitorId,
    DayNumber,
    EmployeeId,
    SiteEventActualVisitDate,
	DurationInMinutes,
    IsRemote,
    IsPrimaryMonitor,
    FullJsonObject,
    NestedJsonObject,
	DurationByDay
)
SELECT
    SiteEventId,
    PrimaryMonitorId,
    DayNumber,
    EmployeeId,
    SiteEventActualVisitDate,
	DurationInMinutes,
    IsRemote,
    IsPrimaryMonitor,
    FullJsonObject,
    NestedJsonObject,
	CASE 
		WHEN DurationInMinutes = 0 THEN 0.0  -- special case: there should not be any zeros, yet they exist
		WHEN DurationInMinutes > 240 THEN 1 ELSE 0.5 END as DurationInDay
FROM ParsedData

---
--- New Adding Primary Monitor Id and Attendees where new Duration_by_day is not provided 
---
UNION

SELECT
	distinct 
	e.Site_Event_Id as SiteEventId,
	PRIMARY_MONITOR_ID as PrimaryMonitorId,
	1 as DayNumber,
	nullif(ss.Value, '') /*ss.Value*/ as EmployeeId, 
	e.[Actual Date] as ActualDate,
	e.DURATION_TOTAL as DurationInMinutes,
	CASE WHEN e.[Remote Visit] = 'Yes' THEN 1 ELSE 0 END as IsRemote, 
	CASE WHEN PRIMARY_MONITOR_ID =  ss.Value THEN 1 ELSE 0 END as IsPrimaryMonitor,
	e.duration_by_day FullJsonObject,
	e.duration_by_day NestedJsonObject,
CASE 
	WHEN e.DURATION_TOTAL = 0 THEN 0.0  -- special case: there should not be any zeros, yet they exist
	WHEN e.DURATION_TOTAL > 240 THEN 1 ELSE 0.5 END as DurationByDay

from [consumption_PrimaReporting].[SiteEvents] e
cross apply STRING_SPLIT ([Attendees Id], ',') ss
WHERE
	e.[ACTUAL DATE] >= @PrimaImplementationReleaseDay
    and 
	e.PRIMARY_MONITOR_ID is not null 
	and
	e.duration_by_day is null 
	and
	isnull(e.[Attendees Id], '') <> ''

UNION


SELECT
	distinct 
	e.Site_Event_Id as SiteEventId,
	PRIMARY_MONITOR_ID as PrimaryMonitorId,
	1 as DayNumber,
	PRIMARY_MONITOR_ID as EmployeeId, 
	e.[Actual Date] as ActualDate,
	e.DURATION_TOTAL as DurationInMinutes,
	CASE WHEN e.[Remote Visit] = 'Yes' THEN 1 ELSE 0 END as IsRemote, 
	1 IsPrimaryMonitor,
	e.duration_by_day FullJsonObject,
	e.duration_by_day NestedJsonObject,
CASE 
	WHEN e.DURATION_TOTAL = 0 THEN 0.0  -- special case: there should not be any zeros, yet they exist
	WHEN e.DURATION_TOTAL > 240 THEN 1 ELSE 0.5 END as DurationByDay
from [consumption_PrimaReporting].[SiteEvents] e

WHERE
	e.[ACTUAL DATE] >= @PrimaImplementationReleaseDay
    and 
	e.PRIMARY_MONITOR_ID is not null 
	and
	e.duration_by_day is null;
	   	 






exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount
 
 
SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[SiteEvents_DurationByDay])
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
