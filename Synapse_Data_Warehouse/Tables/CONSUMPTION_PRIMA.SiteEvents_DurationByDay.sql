CREATE TABLE [CONSUMPTION_PRIMA].[SiteEvents_DurationByDay] 
(
	SiteEventId			INT,
	PrimaryMonitorId	INT,
	DayNumber			NVARCHAR(254),
	EmployeeId			INT,
	SiteEventActualVisitDate DATETIME,
	DurationInMinutes	NVARCHAR(254),
	IsRemote			BIT,
	IsPrimaryMonitor	BIT, 
	FullJsonObject		NVARCHAR(MAX),
	NestedJsonObject	NVARCHAR(MAX),
	DurationByDay		Decimal(18,3)
)
WITH( 
 HEAP, 
 DISTRIBUTION = ROUND_ROBIN 
)