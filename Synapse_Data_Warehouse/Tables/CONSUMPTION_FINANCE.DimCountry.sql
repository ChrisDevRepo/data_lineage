CREATE TABLE [CONSUMPTION_FINANCE].[DimCountry]
(
	[CountryKey] [int] NOT NULL,
	[CountryID] [varchar](6) NOT NULL,
	[Country] [varchar](100) NULL,
	[Office] [varchar](250) NULL,
	[Region] [varchar](50) NULL,
	[OriginalCountry] [varchar](100) NULL
)
WITH
(
	DISTRIBUTION = HASH ( [CountryID] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO