CREATE TABLE [STAGING_CADENCE].[CalcTotals]
(
	[Period Year] [int] NULL,
	[Period Month] [int] NULL,
	[Project Name] [nvarchar](200) NULL,
	[Task Code] [nvarchar](50) NULL,
	[Task Country Name] [nvarchar](100) NULL,
	[Part Order Index] [int] NULL,
	[Segment Order Index] [int] NULL,
	[RecordCount] [int] NULL,
	[Calc Total SUM Function Planned Total Cost Adjusted] [float] NULL,
	[Calc Total SUM Task Planned Total Units] [float] NULL,
	[Calc Total SUM Function Planned Total Hours] [float] NULL,
	[Calc Total SUM Task Approved Total Units] [float] NULL,
	[Calc Total SUM Function TimeSheet Actual Total Hours CT] [float] NULL,
	[Calc Total SUM Function TimeSheet Actual Total Hours NCT] [float] NULL,
	[Calc Total Actual Total Hours (Allocated)] [float] NULL,
	[Calc Total Earned Value (Budget)] [float] NULL,
	[Calc SUM Function Original TimeSheet Actual Total Hours] [float] NULL,
	[Calc SUM Function Actual Cost] [float] NULL
)
WITH
(
	DISTRIBUTION = HASH ( [Period Year],[Period Month],[Project Name],[Task Code],[Task Country Name],[Part Order Index],[Segment Order Index] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO
