CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[SiteAgreements]
(
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[System] [varchar](8) NULL,
	[Country ID] [int] NULL,
	[Country] [varchar](100) NULL,
	[Site ID] [int] NULL,
	[Site Name] [varchar](500) NULL,
	[Site Address] [varchar](500) NULL,
	[Principal Investigator] [nvarchar](400) NULL,
	[Document Type] [nvarchar](400) NULL,
	[Template Type] [nvarchar](max) NULL,
	[Ownership] [nvarchar](400) NULL,
	[Party (primary)] [nvarchar](400) NULL,
	[Cost Center] [varchar](50) NULL,
	[Status] [nvarchar](400) NULL,
	[Comments] [nvarchar](max) NULL,
	[Review Cycle] [varchar](max) NULL,
	[Sent to Site] [varchar](50) NULL,
	[Site Comment] [varchar](50) NULL,
	[Comment Translated] [varchar](50) NULL,
	[Comment Reviewed by PSI] [varchar](50) NULL,
	[Sent to Client] [varchar](50) NULL,
	[Reviewed by Client] [varchar](50) NULL,
	[Finalized] [varchar](50) NULL,
	[Sent to Site for Signing] [varchar](50) NULL,
	[Signed by Site] [varchar](50) NULL,
	[Signed by PSI] [varchar](50) NULL,
	[Signed by Client] [varchar](50) NULL,
	[Executed] [varchar](50) NULL,
	[Review Comments] [nvarchar](max) NULL,
	[CTMS Site Agreement Details Last Updated At] [varchar](50) NULL,
	[Template Type Group] [varchar](50) NULL,
	[Site Agreements And Budgets Record ID] [int] NULL,
	[Reporting Site ID] [varchar](255) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	HEAP
)
GO


