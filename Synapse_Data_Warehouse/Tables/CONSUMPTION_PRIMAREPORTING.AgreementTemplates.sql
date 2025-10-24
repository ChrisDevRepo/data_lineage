CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[AgreementTemplates]
(
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[System] [varchar](8) NULL,
	[country ID] [int] NULL,
	[Country] [varchar](100) NULL,
	[Template Type] [nvarchar](200) NULL,
	[Ownership] [nvarchar](200) NULL,
	[Site ID] [int] NULL,
	[Site Name] [varchar](1000) NULL,
	[Site Address] [varchar](500) NULL,
	[Party (primary)] [nvarchar](200) NULL,
	[Cost Center] [varchar](50) NULL,
	[Status] [nvarchar](200) NULL,
	[Comments] [nvarchar](max) NULL,
	[Review Cycle] [varchar](max) NULL,
	[Sent To client] [varchar](50) NULL,
	[Returned to PSI] [varchar](50) NULL,
	[PSI Template Reviewed by PSI] [varchar](50) NULL,
	[Received by PSI] [varchar](50) NULL,
	[Sponsor Template Reviewed by PSI] [varchar](50) NULL,
	[Returned to Client] [varchar](50) NULL,
	[Approved] [varchar](50) NULL,
	[Translated] [varchar](50) NULL,
	[Finalized] [varchar](50) NULL,
	[Review Comments] [nvarchar](max) NULL,
	[CTMS Agreement Details Last Updated Date] [varchar](50) NULL,
	[Document Type] [varchar](255) NULL,
	[Agreement Templates Record ID] [int] NULL,
	[Reporting Site ID] [varchar](255) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	HEAP
)
GO