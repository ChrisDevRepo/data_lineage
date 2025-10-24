CREATE TABLE [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post]
(
	[FactLaborCostForEarnedValue_PostKey] [bigint] IDENTITY(1,1) NOT NULL,
	[CadenceBudget_LaborCost_PrimaUtilization_JuncKey] [bigint] NULL,
	[Account] [varchar](13) NULL,
	[AccountName] [varchar](250) NULL,
	[SubAccountName] [varchar](250) NULL,
	[Company] [varchar](6) NULL,
	[Region] [varchar](50) NULL,
	[Country] [varchar](8000) NULL,
	[Office] [varchar](250) NULL,
	[CompanyDesc] [varchar](50) NULL,
	[DeptID] [varchar](4) NULL,
	[DeptNameLong] [varchar](250) NULL,
	[DeptNameShort] [varchar](25) NULL,
	[DeptNameMed] [varchar](100) NULL,
	[PrimaGlobalCountryId] [int] NULL,
	[PrimaGlobalCountryName] [varchar](100) NULL,
	[PrimaDepartmentId] [int] NULL,
	[PrimaDepartmentName] [varchar](250) NULL,
	[CadenceDepartmentId] [int] NULL,
	[CadenceDepartmentName] [varchar](250) NULL,
	[Year] [varchar](4) NULL,
	[Month] [varchar](2) NULL,
	[Currency] [varchar](3) NULL,
	[AmountYTD] [decimal](38, 6) NULL,
	[AmountPTD] [decimal](38, 6) NULL,
	[BillableFlag] [int] NOT NULL,
	[Vtyp] [varchar](1) NULL,
	[BomDateId] [int] NULL,
	[KEY] [nvarchar](255) NULL,
	[KEY_wo_Currency] [nvarchar](255) NULL
)
WITH
(
	DISTRIBUTION = HASH ( [PrimaGlobalCountryName],[PrimaDepartmentName],[Year],[Month],[Currency] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO


