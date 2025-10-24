CREATE TABLE [CONSUMPTION_FINANCE].[GLCognosData]
(
	[Perakt] [varchar](6) NULL,
	[Periode] [varchar](4) NULL,
	[Year] [varchar](4) NULL,
	[Month] [varchar](2) NULL,
	[Actuality] [varchar](2) NULL,
	[Company] [varchar](6) NULL,
	[Currency] [varchar](3) NULL,
	[Account] [varchar](13) NULL,
	[Dim1] [varchar](4) NULL,
	[Dim2] [varchar](4) NULL,
	[Dim3] [varchar](4) NULL,
	[Dim4] [varchar](4) NULL,
	[Btyp] [varchar](2) NULL,
	[Etyp] [varchar](2) NULL,
	[KonsType] [varchar](8) NULL,
	[JournalNbr] [int] NULL,
	[Partner] [varchar](6) NULL,
	[OriginCompany] [varchar](6) NULL,
	[TransCurrency] [varchar](3) NULL,
	[PartnerDim] [varchar](4) NULL,
	[LocalAmountYTD] [decimal](38, 6) NULL,
	[TransAmountYTD] [decimal](38, 6) NULL,
	[LocalAmountPTD] [decimal](38, 6) NULL,
	[TransAmountPTD] [decimal](38, 6) NULL,
	[Vtyp] [varchar](1) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO