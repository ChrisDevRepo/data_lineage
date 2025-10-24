CREATE TABLE [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] (
    [Year]         INT         NULL,
    [Month]        INT         NULL,
    [FromCurrency] VARCHAR (3) NULL,
    [ToCurrency]   VARCHAR (3) NULL,
    [Rate]         DECIMAL(19, 8)  NULL,
    [CREATED_AT]   DATETIME    NOT NULL,
    [UPDATED_AT]   DATETIME    NOT NULL
)
WITH (CLUSTERED COLUMNSTORE INDEX, DISTRIBUTION = ROUND_ROBIN);

