CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[IpRedsReview]
(
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[Country ID] [int] NULL,
	[Country] [varchar](100) NULL,
	[Label] [varchar](397) NULL,
	[Category] [varchar](7) NULL,
	[Type] [varchar](7) NULL,
	[Site ID] [int] NULL,
	[Site Name] [varchar](500) NULL,
	[Site Name 2] [varchar](255) NULL,
	[Status] [nvarchar](200) NULL,
	[Project Team Review Completed By] [varchar](102) NULL,
	[Project Team Review Completed On] [varchar](50) NULL,
	[Regulatory Assessor Review Completed On] [varchar](50) NULL,
	[Regulatory Assessor Review Days Variance] [int] NULL,
	[Regulatory Assessor Review Completed By] [varchar](102) NULL,
	[Regulatory Assessor Review Outcome] [varchar](25) NULL,
	[Reporting Site ID] [varchar](255) NULL,
	[IpRedReviewRecordId] [int] NULL,
	[FirstSubmission] [bit] NULL,
	[FirstApproved] [bit] NULL,
	[FirstRejected] [bit] NULL,
	[NextSubmission] [bit] NULL,
	[NextApproved] [bit] NULL,
	[NextRejected] [bit] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO