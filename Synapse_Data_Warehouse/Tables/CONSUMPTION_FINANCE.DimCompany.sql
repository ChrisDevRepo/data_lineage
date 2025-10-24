CREATE TABLE [CONSUMPTION_FINANCE].[DimCompany]
(
[CompanyKey] [int] IDENTITY(1,1) NOT NULL,
[CountryKey] [int] NOT NULL,
[Company] [varchar](6) NOT NULL,
[CompanyDesc] [varchar](50) NULL,
[boltyp] [varchar](1) NULL,
[vkodlc] [varchar](3) NULL,
[IsActive] [varchar](1) NULL,
[IsCurrent] [bit] NOT NULL,
[CreatedBy] [varchar](100) NOT NULL,
[UpdatedBy] [varchar](100) NOT NULL,
[CreatedAt] [datetime] NOT NULL,
[UpdatedAt] [datetime] NOT NULL
)
WITH
(
DISTRIBUTION = REPLICATE,
CLUSTERED INDEX (IsCurrent,Company,CreatedBy)
)