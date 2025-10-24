CREATE TABLE [CONSUMPTION_FINANCE].[DimCurrency]
(
	[CurrencyKey] [int] IDENTITY(1,1) NOT NULL,
	[Currency] [varchar](3) NOT NULL,
	[enhet] [decimal](14, 6) NULL,
	[IsActive] [varchar](1) NULL,
	[IsCurrent] [bit] NOT NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [Currency] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO
