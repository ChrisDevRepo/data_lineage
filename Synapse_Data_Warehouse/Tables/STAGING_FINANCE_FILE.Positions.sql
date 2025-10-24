CREATE TABLE [STAGING_FINANCE_FILE].[Positions]
(
	[DeptID] [varchar](6) NULL,
	[PositionID] [varchar](6) NULL,
	[Position] [varchar](250) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO

