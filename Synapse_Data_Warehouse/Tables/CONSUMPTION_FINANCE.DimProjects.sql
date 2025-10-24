CREATE TABLE [CONSUMPTION_FINANCE].[DimProjects]
(
    [DimProjectKey] [int] IDENTITY(1,1) NOT NULL,
    [ProjectName] [varchar](100) NOT NULL,
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