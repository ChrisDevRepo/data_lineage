CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[SiteSubmissions]
(
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[Country ID] [int] NULL,
	[Country] [varchar](100) NULL,
	[Site ID] [int] NULL,
	[Site Name] [varchar](500) NULL,
	[Submission Description] [nvarchar](max) NULL,
	[Status] [nvarchar](200) NULL,
	[Type] [nvarchar](200) NULL,
	[Submission Planned] [datetime] NULL,
	[Submission Forecast] [datetime] NULL,
	[Submitted] [datetime] NULL,
	[Submission Variance] [int] NULL,
	[Approval Planned] [datetime] NULL,
	[Approval Forecast] [datetime] NULL,
	[Approval] [datetime] NULL,
	[Approval Variance] [int] NULL,
	[Expire] [date] NULL,
	[Responsible Monitor] [varchar](102) NULL,
	[Responsible Monitor Id] [int] NULL,
	[Responsible Id] [int] NULL,
	[IRB Type] [varchar](255) NULL,
	[Authority] [nvarchar](200) NULL,
	[Comments] [varchar](500) NULL,
	[Subject] [varchar](1000) NULL,
	[Sent To PI] [datetime] NULL,
	[Review] [varchar](9) NULL,
	[Is Non PSI Submission] [bit] NULL,
	[Is Request Complete] [bit] NULL,
	[Is Request Processed] [bit] NULL,
	[Created At Src] [datetime] NULL,
	[Created by Src] [varchar](50) NULL,
	[Updated At Src] [datetime] NULL,
	[Updated by Src] [varchar](50) NULL,
	[Initial Study Approval] [varchar](3) NULL,
	[Reporting Site ID] [varchar](255) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	HEAP
)
GO