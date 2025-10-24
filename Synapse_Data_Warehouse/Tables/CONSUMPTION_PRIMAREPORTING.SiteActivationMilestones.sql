CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[SiteActivationMilestones]
(
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[Country Code] [varchar](2) NULL,
	[Country] [varchar](100) NULL,
	[Milestone Group] [varchar](30) NULL,
	[Milestone Name] [varchar](302) NULL,
	[N/a Flag] [varchar](3) NULL,
	[Template ID] [int] NULL,
	[Forecast Date] [date] NULL,
	[Planned Date] [date] NULL,
	[Actual Date] [date] NULL,
	[Planned Total] [int] NULL,
	[Planned to Date] [int] NULL,
	[Activated] [int] NULL,
	[Template Name] [varchar](200) NULL,
	[Active Region] [varchar](20) NULL,
	[Country ID] [int] NULL,
	[Last Site Activated in Country Flag] [bit] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO