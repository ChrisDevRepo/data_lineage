CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[ProjectRegions]
(
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[Project Status] [varchar](200) NULL,
	[Country ID] [int] NULL,
	[Country] [varchar](100) NULL,
	[Client ID] [int] NULL,
	[Client Name] [nvarchar](2000) NULL,
	[Region Phase] [nvarchar](230) NULL,
	[Region Completed] [varchar](3) NULL,
	[Therapeutic Area] [nvarchar](200) NULL,
	[Study Phase] [nvarchar](200) NULL,
	[Indication] [varchar](255) NULL,
	[Planned Sites (Identified)] [int] NULL,
	[Planned Sites (Evaluated)] [int] NULL,
	[Planned Sites (Selected)] [int] NULL,
	[Planned Sites (Initiated)] [int] NULL,
	[Planned Subjects (Screened)] [int] NULL,
	[Planned Subjects (Enrolled)] [int] NULL,
	[Planned Subjects (Complete)] [int] NULL,
	[Planned Subjects (Screened-Out)] [int] NULL,
	[Active Sites] [int] NULL,
	[Active Subjects] [varchar](3) NULL,
	[Country Start (PPT) Planned Date] [varchar](50) NULL,
	[Country Start (PPT) Actual] [varchar](50) NULL,
	[Planned Date] [varchar](50) NULL,
	[Start Date] [varchar](50) NULL,
	[End Date] [varchar](50) NULL,
	[Proposal Sent Date] [varchar](50) NULL,
	[Project Awarded Date] [varchar](50) NULL,
	[Suspension Lifted Date] [varchar](50) NULL,
	[Src Created Date] [varchar](50) NULL,
	[Active Region] [varchar](20) NULL,
	[Is Not Psi Managed] [bit] NULL,
	[Planned Enrollment (Months)] [int] NULL,
	[Expected Screening Rate] [decimal](38, 22) NULL,
	[Planned Screening Rate] [float] NULL,
	[Expected Days to First Screened (Site)] [float] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO