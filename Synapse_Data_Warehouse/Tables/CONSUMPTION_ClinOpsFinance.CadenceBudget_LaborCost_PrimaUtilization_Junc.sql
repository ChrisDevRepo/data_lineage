CREATE TABLE [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaUtilization_Junc]
(
	[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] [bigint] IDENTITY(1,1) NOT NULL,
	[KEY] [nvarchar](255) NULL,
	[KEY_wo_Currency] [nvarchar](255) NULL,
	[PrimaGlobalCountryName] [varchar](100) NULL,
	[Department] [varchar](250) NULL,
	[BomDateId] [int] NULL,
	[Date] [date] NULL,
	[Year] [int] NULL,
	[Month] [int] NULL,
	[Currency] [varchar](4) NULL,
	[TableName] [varchar](100) NULL
)
WITH
(
	DISTRIBUTION = HASH ( [PrimaGlobalCountryName],[Department],[Year],[Month],[Currency] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO


