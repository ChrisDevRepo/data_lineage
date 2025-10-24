CREATE TABLE [CONSUMPTION_FINANCE].[DimAccountDetailsCognos]
(
	[AccountDetailsCognosKey] [int] IDENTITY(1,1) NOT NULL,
	[Account] [varchar](13) NOT NULL,
	[AccountName] [varchar](250) NULL,
	[AccountSort] [smallint] NULL,
	[SubAccountName] [varchar](250) NULL,
	[SubAccountSort] [smallint] NULL,
	[Companies] [varchar](50) NULL,
	[Summary] [varchar](10) NULL,
	[Category] [varchar](250) NULL,
	[CategorySort] [tinyint] NULL,
	[Group] [varchar](250) NULL,
	[GroupSort] [tinyint] NULL,
	[Template] [varchar](100) NULL,
	[IsActive] [varchar](1) NOT NULL,
	[IsCurrent] [bit] NOT NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [Account] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO