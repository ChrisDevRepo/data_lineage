CREATE TABLE [CONSUMPTION_FINANCE].[DimCompanyKoncern]
(
	[CompanyKoncernKey] [int] IDENTITY(1,1) NOT NULL,
	[Company] [varchar](6) NOT NULL,
	[koncern] [varchar](6) NULL,
	[IsActive] [varchar](1) NULL,
	[IsCurrent] [bit] NOT NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(

DISTRIBUTION = REPLICATE,
CLUSTERED INDEX ([IsCurrent], [Company], [koncern], [CreatedAt])
)