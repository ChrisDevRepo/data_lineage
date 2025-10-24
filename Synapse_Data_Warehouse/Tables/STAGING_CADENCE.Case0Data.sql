CREATE TABLE [STAGING_CADENCE].[Case0Data]
(
	[Period Year] [int] NULL,
	[Period Month] [int] NULL,
	[Project Name] [nvarchar](200) NULL,
	[Project Currency Code] [nvarchar](3) NULL,
	[Project Currency Name] [nvarchar](3) NULL,
	[Service] [nvarchar](200) NULL,
	[Unit type] [nvarchar](200) NULL,
	[Task Code] [nvarchar](50) NULL,
	[Task Name] [nvarchar](200) NULL,
	[Task Country Name] [nvarchar](100) NULL,
	[Part Order Index] [int] NULL,
	[Segment Order Index] [int] NULL,
	[Task Region] [nvarchar](100) NULL,
	[Function Code] [nvarchar](50) NULL,
	[Function Name] [nvarchar](200) NULL,
	[Department] [nvarchar](200) NULL,
	[Function Country Name] [nvarchar](100) NULL,
	[Function Region] [nvarchar](100) NULL,
	[SUM Function Planned Total Cost Adjusted] [float] NULL,
	[SUM Function Planned Total Hours] [float] NULL,
	[Function CurrentRate Adjusted] [float] NULL,
	[SUM Task Planned Total Units] [float] NULL,
	[SUM Task Approved Total Units] [float] NULL,
	[SUM Function TimeSheet Actual Total Hours] [float] NULL,
	[SUM Function Reconciliation TimeSheet Actual Total Hours] [float] NULL,
	[SUM Function Actual Hours] [float] NULL,
	[SUM Function Period Actual Cost] [float] NULL,
	[SUM Function Reconciliation Actual Cost] [float] NULL,
	[SUM Task Reconciliation Actual Cost] [float] NULL,
	[SUM Function Actual Cost] [float] NULL,
	[ROW_NUMBER] [int] NULL,
	[SelRows] [int] NULL,
	[Updated SUM Function TimeSheet Actual Total Hours] [float] NULL
)
WITH
(
	DISTRIBUTION = HASH ( [Period Year],[Period Month],[Project Name],[Task Code],[Task Country Name],[Part Order Index],[Segment Order Index],[Function Code] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO
