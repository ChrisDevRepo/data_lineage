CREATE TABLE [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
(
	[CompanyCode] [varchar](10) NULL,
	[DocumentNumber] [varchar](10) NULL,
	[Year] [char](4) NULL,
	[DocumentDate] [date] NULL,
	[Customer] [varchar](10) NULL,
	[CustomerName] [nvarchar](250) NULL,
	[ProjectName] [nvarchar](100) NULL,
	[InvoiceDetails] [nvarchar](4000) NULL,
	[Advances] [char](1) NULL,
	[CostType] [varchar](25) NULL,
	[BusinessArea] [varchar](10) NULL,
	[Currency] [char](3) NULL,
	[NetAmountTC] [decimal](19, 4) NULL,
	[VatAmountTC] [decimal](19, 4) NULL,
	[TotAmountTC] [decimal](19, 4) NULL,
	[PaymentTerms] [varchar](10) NULL,
	[DueDate] [date] NULL,
	[DatePaid] [date] NULL,
	[ContractDetails] [nvarchar](4000) NULL,
	[PrimaID] [varchar](10) NULL,
	[SalesForceNumber] [varchar](25) NULL,
	[PostDate] [date] NULL,
	[NetAmountCHF] [decimal](19, 4) NULL,
	[VatAmountCHF] [decimal](19, 4) NULL,
	[TotAmountCHF] [decimal](19, 4) NULL,
	[RteTcCHF] [decimal](38, 18) NULL,
	[NetAmountUSD] [decimal](19, 4) NULL,
	[VatAmountUSD] [decimal](19, 4) NULL,
	[TotAmountUSD] [decimal](19, 4) NULL,
	[RteTcUSD] [decimal](38, 18) NULL,
	[NetAmountEUR] [decimal](19, 4) NULL,
	[VatAmountEUR] [decimal](19, 4) NULL,
	[TotAmountEUR] [decimal](19, 4) NULL,
	[RteTcEUR] [decimal](38, 18) NULL,
	[NetAmountGBP] [decimal](19, 4) NULL,
	[VatAmountGBP] [decimal](19, 4) NULL,
	[TotAmountGBP] [decimal](19, 4) NULL,
	[RteTcGBP] [decimal](38, 18) NULL,
	[AccountPreviousYear] [date] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO