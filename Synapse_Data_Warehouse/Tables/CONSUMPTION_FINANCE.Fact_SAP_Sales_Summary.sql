CREATE TABLE [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Summary]
(
	[Fact_SAP_Sales_SummaryKey] [int] IDENTITY(1,1) NOT NULL,
	[DimCustomerProjectKey] [int] NOT NULL,
	[DimDocumentDateKey] [int] NULL,
	[DimDueDateKey] [int] NULL,
	[DimPaidDateKey] [int] NULL,
	[DimPostDateKey] [int] NOT NULL,
	[DocumentNumber] [bigint] NULL,
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
	DISTRIBUTION = HASH ( [DimCustomerProjectKey],[CostType] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO