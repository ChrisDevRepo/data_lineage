CREATE TABLE [CONSUMPTION_FINANCE].[SAP_Sales_Retainer_Details_Metrics]
(
	[Account] [varchar](10) NULL,
	[AccountText] [nvarchar](50) NULL,
	[Advances] [varchar](10) NULL,
	[Assignment] [varchar](50) NULL,
	[BusinessArea] [varchar](10) NULL,
	[CompanyCode] [varchar](10) NULL,
	[ContractDetails] [nvarchar](4000) NULL,
	[CostType] [varchar](25) NULL,
	[Currency] [char](3) NULL,
	[Customer] [varchar](10) NULL,
	[CustomerName] [nvarchar](250) NULL,
	[DatePaid] [date] NULL,
	[DC] [varchar](10) NULL,
	[DocumentDate] [date] NULL,
	[DocumentNumber] [varchar](10) NULL,
	[DueDate] [date] NULL,
	[InternalInvoice] [nvarchar](25) NULL,
	[InvoiceDetails] [nvarchar](4000) NULL,
	[Item] [varchar](10) NULL,
	[NetAmountTC] [decimal](19, 4) NULL,
	[PaymentTerms] [varchar](10) NULL,
	[PrimaID] [varchar](10) NULL,
	[ProjectName] [nvarchar](100) NULL,
	[TotalAmountTC] [decimal](19, 4) NULL,
	[VatAmountTC] [decimal](19, 4) NULL,
	[Year] [char](4) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO





