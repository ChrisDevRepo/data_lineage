CREATE TABLE [dbo].[Full_Departmental_Map]
(
	[CadenceDepartmentId] [int] NULL,
	[CadenceDepartmentName] [varchar](250) NULL,
	[PrimaDepartmentId] [int] NULL,
	[PrimaDepartmentName] [varchar](250) NULL,
	[FinanceDepartmentId] [int] NULL,
	[FinanceDepartmentName] [varchar](250) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO
