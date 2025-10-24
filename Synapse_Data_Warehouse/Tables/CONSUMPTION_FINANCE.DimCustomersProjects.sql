CREATE TABLE [CONSUMPTION_FINANCE].[DimCustomersProjects]
  (
  	[DimCustomerProjectKey] [int] IDENTITY(1,1) NOT NULL,
    [DimCustomerKey] [int] NOT NULL,
  	[DimProjectKey] [int] NOT NULL,
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