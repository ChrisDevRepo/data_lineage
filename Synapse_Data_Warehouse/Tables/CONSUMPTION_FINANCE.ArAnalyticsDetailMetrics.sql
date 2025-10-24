CREATE TABLE [CONSUMPTION_FINANCE].[ArAnalyticsDetailMetrics]
(
	[ArAnalyticsDetailMetricsKey] [int] IDENTITY(1,1) NOT NULL,
	[ArAnalyticsMetricsKey] [int] NOT NULL,
	[DimCustomerProjectKey] [int] NOT NULL,
	[DimCustomerKey] [int] NOT NULL,
	[DimProjectKey] [int] NOT NULL,
	[DimDocumentDateKey] [int] NULL,
	[DimDueDateKey] [int] NULL,
	[DimPaidDateKey] [int] NULL,
	[DimPostDateKey] [int] NULL,
	[DocumentDate] [date] NULL,
	[DueDate] [date] NULL,
	[PaidDate] [date] NULL,
	[PostDate] [date] NULL,
	[FilterValue] [varchar](50) NULL,
	[YearQuarter] [varchar](10) NULL,
	[DocumentNumber] [bigint] NULL,
	[ProjectName] [varchar](100) NOT NULL,
	[CustomerName] [varchar](255) NOT NULL,
	[CostType] [varchar](10) NULL,
	[Currency] [varchar](5) NOT NULL,
	[BusinessArea] [int] NULL,
	[NetAmountTC] [decimal](19, 4) NULL,
	[ConversionRate] [decimal](38, 18) NULL,
	[CHFNetAmountTC] [decimal](19, 4) NULL,
	[InvoiceDetails] [nvarchar](4000) NULL,
	[Advances] [char](1) NULL,
	[VatAmountTC] [decimal](19, 4) NULL,
	[TotAmountTC] [decimal](19, 4) NULL,
	[PaymentTerms] [varchar](10) NULL,
	[ContractDetails] [nvarchar](4000) NULL,
	[SalesForceNumber] [varchar](25) NULL,
	[DaysToPay] [float] NULL,
	[DaysLate] [float] NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [DimCustomerProjectKey],[FilterValue],[CostType] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO