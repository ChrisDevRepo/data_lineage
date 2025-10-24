CREATE TABLE [CONSUMPTION_FINANCE].[QuarterRanges]
(
    [QuarterRangeKey] [int] IDENTITY(1,1) NOT NULL,
    [YearQuarter] [varchar](25) NOT NULL,
    [Year] [int] NOT NULL,
    [QuarterOfTheYear] [int] NOT NULL,
    [FirstDayOfTheQuarter] [date] NOT NULL,
    [LastDayOfTheQuarter] [date] NOT NULL,
    [QuarterNumber] [int] NOT NULL,
    [FilterValue] [varchar](25) NOT NULL,
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
