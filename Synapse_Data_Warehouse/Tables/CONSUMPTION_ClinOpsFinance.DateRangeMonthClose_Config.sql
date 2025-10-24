CREATE TABLE [CONSUMPTION_ClinOpsFinance].DateRangeMonthClose_Config
(
	RowID INT,
	[Year] SMALLINT NULL,
	MonthNumber SMALLINT,
	[MonthToClose] DATE NULL,
	[CloseQtr] SMALLINT NULL,
	CloseDate  DATE NULL,
	[CreatedBy] [varchar](100) NULL,
	[UpdatedBy] [varchar](100) NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = REPLICATE
)
GO