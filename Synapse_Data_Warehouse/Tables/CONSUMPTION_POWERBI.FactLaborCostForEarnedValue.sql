CREATE TABLE [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] (
    [Account]                VARCHAR (13)    NULL,
    [AccountName]            VARCHAR (250)   NULL,
    [SubAccountName]         VARCHAR (250)   NULL,
    [Company]                VARCHAR (6)     NULL,
    [Region]                 VARCHAR (50)    NULL,
    [Country]                VARCHAR (8000)  NULL,
    [Office]                 VARCHAR (250)   NULL,
    [CompanyDesc]            VARCHAR (50)    NULL,
    [DeptID]                 VARCHAR (4)     NULL,
    [DeptNameLong]           VARCHAR (250)   NULL,
    [DeptNameShort]          VARCHAR (25)    NULL,
    [DeptNameMed]            VARCHAR (100)   NULL,
    [PrimaGlobalCountryId]   INT             NULL,
    [PrimaGlobalCountryName] VARCHAR (100)   NULL,
    [PrimaDepartmentId]      INT             NULL,
    [PrimaDepartmentName]    VARCHAR (250)   NULL,
    [CadenceDepartmentId]    INT             NULL,
    [CadenceDepartmentName]  VARCHAR (250)   NULL,
    [Year]                   VARCHAR (4)     NULL,
    [Month]                  VARCHAR (2)     NULL,
    [Currency]               VARCHAR (3)     NULL,
    [AmountYTD]              DECIMAL (38, 6) NULL,
    [AmountPTD]              DECIMAL (38, 6) NULL,
    [BillableFlag]           INT             NOT NULL,
    [Vtyp]                   VARCHAR (1)     NULL
)
WITH (CLUSTERED COLUMNSTORE INDEX, DISTRIBUTION = ROUND_ROBIN);

