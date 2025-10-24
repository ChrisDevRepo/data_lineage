CREATE TABLE [STAGING_CADENCE].[FinalCountryReallocateTSAggregatedData]
(
	[Period Start Date] [date] NULL,
	[Period Year] [int] NULL,
	[Period Month] [int] NULL,
	[Project Name] [nvarchar](200) NULL,
	[Task Code] [nvarchar](50) NULL,
	[Task Country Name] [nvarchar](100) NULL,
	[Part Order Index] [int] NULL,
	[Segment Order Index] [int] NULL,
	[Function Code] [nvarchar](50) NULL,
	[Function Country Name] [nvarchar](100) NULL,
	[SUM Task Planned Total Units] [decimal](19,4) NULL,
	--[SUM Function Planned Total Hours] [decimal](19,4) NULL,
	[SUM Task Period Approved Total Units] [decimal](19,4) NULL,
	[Actual Total Hours (Allocated)] [decimal](19,4) NULL, 
	[Actual Cost (Allocated)] [decimal](19,4) NULL,
	[ROW_NUMBER] [int] NULL,
	[FromRecord] [int] NULL,
	[Calc Actual Total Hours (Allocated)] [decimal](19,4) NULL,
	[Calc Actual Cost (Allocated)] [decimal](19,4) NULL
)
WITH
(
	DISTRIBUTION = HASH ( [Period Year],[Period Month],[Project Name],[Task Code],[Task Country Name],[Part Order Index],[Segment Order Index],[Function Code] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO