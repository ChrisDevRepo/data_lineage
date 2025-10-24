CREATE TABLE [CONSUMPTION_FINANCE].[SAP_Sales_Details_History]
(
	[Year] [char](4) NULL,
	[DocumentDate] [date] NULL,
	[DocumentNumber] [varchar](10) NULL,
	[Item] [varchar](10) NULL,
	[Customer] [varchar](10) NULL,
	[CustomerName] [nvarchar](250) NULL,
	[ProjectName] [nvarchar](100) NULL,
	[InvoiceDetails] [nvarchar](4000) NULL,
	[Assignment] [varchar](50) NULL,
	[Advances] [varchar](10) NULL,
	[CostType] [varchar](25) NULL,
	[BusinessArea] [varchar](10) NULL,
	[Currency] [char](3) NULL,
	[NetAmountTC] [decimal](19, 4) NULL,
	[VatAmountTC] [decimal](19, 4) NULL,
	[TotalAmountTC] [decimal](19, 4) NULL,
	[Account] [varchar](10) NULL,
	[AccountText] [nvarchar](50) NULL,
	[PaymentTerms] [varchar](10) NULL,
	[DueDate] [date] NULL,
	[DatePaid] [date] NULL,
	[InternalInvoice] [nvarchar](25) NULL,
	[ContractDetails] [nvarchar](4000) NULL,
	[CompanyCode] [varchar](10) NULL,
	[DC] [varchar](10) NULL,
	[PrimaID] [varchar](10) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO
