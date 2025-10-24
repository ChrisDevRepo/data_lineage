CREATE TABLE [CONSUMPTION_FINANCE].[DataFilters]
(
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Tablename] [varchar](100) NOT NULL,
	[ColumnName] [varchar](100) NOT NULL,
	[ColumnValue] [varchar](50) NOT NULL,
	[IncludeExclude] [varchar](10) NOT NULL,
	[Condition] [varchar](20) NOT NULL
)
WITH
(
    HEAP,  
    DISTRIBUTION = REPLICATE 
)
GO 