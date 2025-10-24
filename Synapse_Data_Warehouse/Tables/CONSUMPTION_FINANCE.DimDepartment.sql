CREATE TABLE [CONSUMPTION_FINANCE].[DimDepartment]
(
	[DepartmentKey] [int] IDENTITY(1,1) NOT NULL,
	[DeptID] [varchar](6) NOT NULL,
	[DeptNameLong] [varchar](250) NULL,
	[DeptNameShort] [varchar](25) NULL,
	[DeptNameMed] [varchar](100) NULL,
	[IsActive] [varchar](1) NULL,
	[IsCurrent] [bit] NOT NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [DeptID] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO