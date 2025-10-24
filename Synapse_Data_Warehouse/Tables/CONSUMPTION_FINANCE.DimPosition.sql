CREATE TABLE [CONSUMPTION_FINANCE].[DimPosition]
(
	[PositionKey] [int] IDENTITY(1,1) NOT NULL,
	[PositionID] [varchar](6) NOT NULL,
	[Position] [varchar](250) NULL,
	[DeptID] [varchar](6) NULL,
	[IsActive] [varchar](1) NULL,
	[IsCurrent] [bit] NOT NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [PositionID] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO