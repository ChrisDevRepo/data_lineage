CREATE TABLE [CONSUMPTION_FINANCE].[DimCustomers]
(
    [DimCustomerKey] [int] IDENTITY(1,1) NOT NULL,
	[CustomerName] [varchar](255) NOT NULL,
	[IsActive] [varchar](1) NOT NULL,
	[CreatedBy] [varchar](100) NOT NULL,
	[UpdatedBy] [varchar](100) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[UpdatedAt] [datetime] NOT NULL
)
WITH
(
    HEAP,  
    DISTRIBUTION = REPLICATE  
)
GO