CREATE TABLE [CONSUMPTION_POWERBI].[FactAggregatedLaborCost] (
    [PrimaGlobalCountryId]   INT             NULL,
    [PrimaGlobalCountryName] VARCHAR (100)   NULL,
    [PrimaDepartmentId]      INT             NULL,
    [PrimaDepartmentName]    VARCHAR (250)   NULL,
    [BillableFlag]           INT             NULL,
    [Year]                   VARCHAR (4)     NULL,
    [Month]                  VARCHAR (2)     NULL,
    [Currency]               VARCHAR (3)     NULL,
    [AmountYTD]              DECIMAL (38, 6) NULL,
    [AmountPTD]              DECIMAL (38, 6) NULL
)
WITH (CLUSTERED COLUMNSTORE INDEX, DISTRIBUTION = ROUND_ROBIN);

