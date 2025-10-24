CREATE TABLE [CONSUMPTION_FINANCE].[ArAnalyticsMetrics]
(
    [ArAnalyticsMetricsKey] [int] IDENTITY(1,1) NOT NULL,
    [DimProjectKey] [int] NULL,
    [DimCustomerKey] [int] NULL,
    [DimCustomerProjectKey] [int] NULL,
    [YearQuarter] [varchar](10) NULL,
    [Year] [int] NULL,
    [QuarterOfTheYear] [int] NULL,
    [QuarterNumber] [int] NULL,
    [FilterValue] [varchar](50) NULL,
    [ProjectName] [varchar](100) NOT NULL,
    [CustomerName] [varchar](255) NOT NULL,
    [CostType] [varchar](10) NULL,
    [TotalDaysToPay] [float] NULL,
    [TotalDaysToPayRecordCount] [float] NULL,
    [TotalDaysLate] [float] NULL,
    [TotalDaysLateRecordCount] [float] NULL,
    [TotalInvoices] [float] NULL,
    [TotalInvoiceLines] [float] NULL,
    [CreatedBy] [varchar](100) NOT NULL,
    [UpdatedBy] [varchar](100) NOT NULL,
    [CreatedAt] [datetime] NOT NULL,
    [UpdatedAt] [datetime] NOT NULL
)
WITH
(
    CLUSTERED COLUMNSTORE INDEX,
    DISTRIBUTION = HASH
( [YearQuarter], [FilterValue], [DimCustomerProjectKey], [CostType] )
)