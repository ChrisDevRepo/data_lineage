CREATE TABLE [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskInterestQuarterly]
(
	[FactSAPSalesSponsorRiskInterestQuarterlyKey] [int] IDENTITY(1,1) NOT NULL,
	[QuarterRangeKey] [int] NULL,
	[YearQuarter] [varchar](10) NULL,
	[FilterValue] [varchar](50) NULL,
	[DimCustomerKey] [int] NOT NULL,
	[Currency] [varchar](5) NOT NULL,
	[AggreratedNetAmountTC] [decimal](19, 4) NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [YearQuarter] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO