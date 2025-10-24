CREATE TABLE [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Details]
(
	[Fact_SAP_Sales_DetailsKey] [int] IDENTITY(1,1) NOT NULL,
	[DimCustomerProjectKey] [int] NULL,
	[DimDocumentDateKey] [int] NULL,
	[DimDueDateKey] [int] NULL,
	[DimPaidDateKey] [int] NULL,
	[Account] [varchar](10) NULL,
	[DocumentNumber] [varchar](10) NULL,
	[Item] [int] NULL,
	[CostType] [varchar](10) NULL,
	[Currency] [varchar](5) NOT NULL,
	[BusinessArea] [int] NULL,
	[NetAmountTC] [decimal](19, 4) NULL,
	[PaymentTerms] [varchar](10) NULL,
	[InternalInvoice] [nvarchar](25) NULL,
	[TotalAmountTC] [decimal](19, 4) NULL,
	[ConversionRate] [decimal](38, 18) NULL,
	[CHFTotalAmountTC] [decimal](19, 4) NULL,
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