CREATE TABLE [CONSUMPTION_FINANCE].[AccountFilter]
(
	[ID] [int] NOT NULL,
	[Area] [varchar](100) NOT NULL,
	[ColumnName] [varchar](100) NOT NULL,
	[ExcludeColumnValue] [varchar](10) NOT NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO


