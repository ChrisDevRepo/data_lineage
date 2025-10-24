CREATE TABLE [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Nightly]
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
	[NetAmountTC] [money] NULL,
	[VatAmountTC] [money] NULL,
	[TotAmountTC] [money] NULL,
	[PaymentTerms] [varchar](10) NULL,
	[DueDate] [date] NULL,
	[DatePaid] [date] NULL,
	[ContractDetails] [nvarchar](4000) NULL,
	[PrimaID] [varchar](10) NULL,
	[SalesForceNumber] [varchar](25) NULL,
	[PostDate] [date] NULL,
	[NetAmountCHF] [money] NULL,
	[VatAmountCHF] [money] NULL,
	[TotAmountCHF] [money] NULL,
	[RteTcCHF] [decimal](38, 18) NULL,
	[NetAmountUSD] [money] NULL,
	[VatAmountUSD] [money] NULL,
	[TotAmountUSD] [money] NULL,
	[RteTcUSD] [decimal](38, 18) NULL,
	[NetAmountEUR] [money] NULL,
	[VatAmountEUR] [money] NULL,
	[TotAmountEUR] [money] NULL,
	[RteTcEUR] [decimal](38, 18) NULL,
	[NetAmountGBP] [money] NULL,
	[VatAmountGBP] [money] NULL,
	[TotAmountGBP] [money] NULL,
	[RteTcGBP] [decimal](38, 18) NULL,
	[AccountPreviousYear] [date] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO