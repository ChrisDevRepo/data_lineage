CREATE TABLE [CONSUMPTION_FINANCE].[FactGLCognos]
(
	[FactGLCognosKey] [bigint] IDENTITY(1,1) NOT NULL,
	[AccountKey] [int] NULL,
	[CompanyKey] [int] NULL,
	[DepartmentKey] [int] NULL,
	[PositionKey] [int] NULL,
	[MonthFinanceKey] [int] NULL,
	[ConsTypeKey] [int] NULL,
	[ActualityKey] [int] NULL,
	[CurrencyKey] [int] NULL,
	[AccountDetailsCognosKey] [int] NULL,
	[Perakt] [varchar](6) NULL,
	[Periode] [varchar](4) NULL,
	[Year] [varchar](4) NULL,
	[Month] [varchar](2) NULL,
	[Actuality] [varchar](2) NULL,
	[Company] [varchar](6) NULL,
	[LocalCurrency] [varchar](3) NULL,
	[Account] [varchar](13) NULL,
	[TransCurrency] [varchar](3) NULL,
	[OriginCompany] [varchar](6) NULL,
	[Partner] [varchar](6) NULL,
	[PartnerDim] [varchar](4) NULL,
	[Dim1] [varchar](4) NULL,
	[Dim2] [varchar](4) NULL,
	[Dim3] [varchar](4) NULL,
	[Dim4] [varchar](4) NULL,
	[Btyp] [varchar](2) NULL,
	[Etyp] [varchar](2) NULL,
	[Vtyp] [varchar](1) NULL,
	[KonsType] [varchar](8) NULL,
	[JournalNbr] [int] NULL,
	[LocalAmountYTD] [decimal](38, 6) NULL,
	[TransAmountYTD] [decimal](38, 6) NULL,
	[LocalAmountPTD] [decimal](38, 6) NULL,
	[TransAmountPTD] [decimal](38, 6) NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO

