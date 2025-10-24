CREATE TABLE [CONSUMPTION_FINANCE].[FactSAPSalesRetainerDetails]
(
	[FactSAPSalesRetainerDetailsKey] [int] IDENTITY(1,1) NOT NULL,
	[DimCustomerProjectKey] [int] NULL,
	[DimCustomerKey] [int] NULL,
	[DimProjectKey] [int] NULL,
	[DimDocumentDateKey] [int] NULL,
	[DimDueDateKey] [int] NULL,
	[DimPaidDateKey] [int] NULL,
	[Currency] [varchar](5) NULL,
	[NetAmountTC] [decimal](19, 4) NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
	DISTRIBUTION = HASH ( [DimCustomerProjectKey],[DimCustomerKey],[DimProjectKey],[DimDocumentDateKey],[Currency] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO