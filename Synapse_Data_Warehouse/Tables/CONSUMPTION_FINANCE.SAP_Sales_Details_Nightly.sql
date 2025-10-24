CREATE TABLE [CONSUMPTION_FINANCE].[SAP_Sales_Details_Nightly]
(
	[CompanyCode] [varchar](10) NULL,
	[DocumentNumber] [varchar](10) NULL,
	[Year] [char](4) NULL,
	[Item] [varchar](10) NULL,
	[DocumentDate] [date] NULL,
	[Customer] [varchar](10) NULL,
	[CustomerName] [nvarchar](250) NULL,
	[ProjectName] [nvarchar](100) NULL,
	[InvoiceDetails] [nvarchar](4000) NULL,
	[Assignment] [varchar](50) NULL,
	[Advances] [varchar](10) NULL,
	[CostType] [varchar](25) NULL,
	[BusinessArea] [varchar](10) NULL,
	[Currency] [char](3) NULL,
	[NetAmountTC] [money] NULL,
	[VatAmountTC] [money] NULL,
	[TotalAmountTC] [money] NULL,
	[Account] [varchar](10) NULL,
	[AccountText] [nvarchar](50) NULL,
	[PaymentTerms] [varchar](10) NULL,
	[DueDate] [date] NULL,
	[DatePaid] [date] NULL,
	[InternalInvoice] [nvarchar](25) NULL,
	[ContractDetails] [nvarchar](4000) NULL,
	[DC] [varchar](10) NULL,
	[PrimaID] [varchar](10) NULL,
	[SalesForceNumber] [varchar](25) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO