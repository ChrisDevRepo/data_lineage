CREATE TABLE [STAGING_CADENCE].[AggregatedGlobalNoCountryTotals]
(
	[Period Year] [int] NULL,
	[Period Month] [int] NULL,
	[Project Name] [nvarchar](200) NULL,
	[Task Code] [nvarchar](50) NULL,
	[Task Country Name] [nvarchar](100) NULL,
	[Part Order Index] [int] NULL,
	[Segment Order Index] [int] NULL,
	[RecordCount] [int] NULL,
	[Calc Total SUM Function Planned Total Cost Adjusted] [decimal](19,4) NULL,
	[Calc Total SUM Task Planned Total Units] [decimal](19,4) NULL,
	[Calc Total SUM Function Planned Total Hours] [decimal](19,4) NULL,
	[Calc Total SUM Task Approved Total Units] [decimal](19,4) NULL,
	[Calc Total SUM Function TimeSheet Actual Total Hours CT] [decimal](19,4) NULL,
	[Calc Total SUM Function TimeSheet Actual Total Hours NCT] [decimal](19,4) NULL,
	[Calc Total Actual Total Hours (Allocated)] [decimal](19,4) NULL,
	[Calc Total Earned Value (Budget)] [decimal](19,4) NULL,
	[Calc Original Actual Total Hours (Allocated)] [decimal](19,4) NULL,
	[Calc SUM Function Actual Cost] [decimal](19,4) NULL,
	[Calc Actual Cost (Allocated) CT] [decimal](19,4) NULL,
	[Calc Actual Cost (Allocated) NCT] [decimal](19,4) NULL,
	[Calc Actual Cost (Allocated)] [decimal](19,4) NULL,
	[Calc Original Actual Cost (Allocated)] [decimal](19,4) NULL
)
WITH
(
	DISTRIBUTION = HASH ( [Period Year],[Period Month],[Project Name],[Task Code],[Task Country Name],[Part Order Index],[Segment Order Index] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO