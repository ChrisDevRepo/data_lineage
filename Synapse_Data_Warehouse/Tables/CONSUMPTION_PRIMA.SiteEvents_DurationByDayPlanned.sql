CREATE TABLE [CONSUMPTION_PRIMA].[SiteEvents_DurationByDayPlanned] 
(
	SiteEventId			INT,
	PrimaryMonitorId	INT,
	DayNumber nvarchar(254),
	EmployeeId INT,
	SiteEventForecastVisitDate DATE,
	IsRemote BIT,
	IsPrimaryMonitor BIT, 
	FullJsonObject NVARCHAR(MAX),
	NestedJsonObject NVARCHAR(MAX)
)
WITH( 
 HEAP, 
 DISTRIBUTION = ROUND_ROBIN 
)