CREATE TABLE [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskSnapshot]
(
	[FactSAPSalesSponsorRiskSnapshotKey] [int] IDENTITY(1,1) NOT NULL,
	[DimCustomerProjectKey] [int] NOT NULL,
	[DimProjectKey] [int] NULL,
	[DimCustomerKey] [int] NULL,
	[Currency] [varchar](5) NULL,
	[CostType] [varchar](10) NULL,
	[TotalAdvanceInvoiced] [decimal](19, 4) NULL,
	[TotalCreditsInvoices] [decimal](19, 4) NULL,
	[TotalAdvanceWithdrawn] [decimal](19, 4) NULL,
	[AdvanceBalance] [decimal](19, 4) NULL,
	[UnpaidAdvanceRisk] [decimal](19, 4) NULL,
	[AvailableFunds] [decimal](19, 4) NULL,
	[ProcessDate] [datetime] NOT NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [DimCustomerProjectKey],[CostType] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO


