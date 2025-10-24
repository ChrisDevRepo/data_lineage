CREATE TABLE [CONSUMPTION_FINANCE].[COGNOS_Currency_Conversion]
(
	[perakt] [char](6) NULL,
	[vkod] [char](3) NULL,
	[kurstyp] [char](1) NULL,
	[enhet] [decimal](14, 6) NULL,
	[kurs] [decimal](12, 6) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO