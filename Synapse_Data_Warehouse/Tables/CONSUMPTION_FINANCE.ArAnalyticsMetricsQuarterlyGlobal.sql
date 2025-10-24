CREATE TABLE [CONSUMPTION_FINANCE].[ArAnalyticsMetricsQuarterlyGlobal]
(
	[ArAnalyticsMetricsQuarterlyGlobalKey] [int] IDENTITY(1,1) NOT NULL,
	[YearQuarter] [varchar](10) NOT NULL,
	[FilterValue] [varchar](50) NULL,
	[DaysInQuarter] [int] NULL,
	[EndingArChf] [decimal](19, 4) NULL,
	[RevenueChf] [decimal](19, 4) NULL,
	[ModifiedArBalance] [decimal](19, 4) NULL,
	[Dso] [decimal](38, 18) NULL,
	[DsoBestCase] [decimal](38, 18) NULL,
	[DsoVariance] [decimal](38, 18) NULL,
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