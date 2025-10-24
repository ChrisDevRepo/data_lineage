CREATE TABLE [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskRetainerQuarterly]
(
	[FactSAPSalesSponsorRiskRetainerQuarterlyKey] [int] IDENTITY(1,1) NOT NULL,
	[DimCustomerProjectKey] [int] NULL,
	[DimCustomerKey] [int] NULL,
	[DimProjectKey] [int] NULL,
	[QuarterRangeKey] [int] NULL,
	[YearQuarter] [varchar](25) NULL,
	[FilterValue] [varchar](25) NULL,
	[Currency] [varchar](5) NULL,
	[AggregatedNetAmountTC] [money] NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [DimCustomerProjectKey] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO