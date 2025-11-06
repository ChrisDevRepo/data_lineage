/*
 * Test Case: Comment Hints Feature Validation
 * Stored Procedure: spLoadFactLaborCostForEarnedValue
 *
 * Golden Record (Expected Dependencies):
 *
 * INPUTS (Sources - tables being read FROM):
 *   - Consumption_FinanceHub.FactGLCognos
 *   - CONSUMPTION_FINANCE.DimAccountDetailsCognos
 *   - dbo.Full_Departmental_Map
 *   - CONSUMPTION_PRIMA.MonthlyAverageCurrencyExchangeRate
 *   - CONSUMPTION_PRIMA.GlobalCountries
 *   - CONSUMPTION_FINANCE.DimCompany
 *   - CONSUMPTION_FINANCE.DimDepartment
 *   - CONSUMPTION_FINANCE.DimCountry
 *
 * OUTPUTS (Targets - tables being written TO):
 *   - Consumption_FinanceHub.FactLaborCostForEarnedValue
 */

CREATE PROC [Consumption_FinanceHub].[spLoadFactLaborCostForEarnedValue] AS
BEGIN
-- DESCRIPTION: Converts quarterly labor costs from FactGLCognos to monthly departmental costs in FactLaborCostForEarnedValue
--              Distributes costs evenly across quarters/departments with multi-currency and billable/non-billable classification

-- @LINEAGE_INPUTS: Consumption_FinanceHub.FactLaborCostForEarnedValue
-- @LINEAGE_OUTPUTS: Consumption_FinanceHub.FactGLCognos, CONSUMPTION_FINANCE.DimAccountDetailsCognos, dbo.Full_Departmental_Map, CONSUMPTION_PRIMA.MonthlyAverageCurrencyExchangeRate, CONSUMPTION_PRIMA.GlobalCountries, CONSUMPTION_FINANCE.DimCompany, CONSUMPTION_FINANCE.DimDepartment, CONSUMPTION_FINANCE.DimCountry
SET NOCOUNT ON

DECLARE @servername		VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @ProcShortName  NVARCHAR(128) = 'spLoadFactLaborCostForEarnedValue'
DECLARE @procname		NVARCHAR(128) = '[Consumption_FinanceHub].['+@ProcShortName+']'
DECLARE @procid			VARCHAR(100) = (SELECT OBJECT_ID(@procname))


/*-------------------------------------------------------------------------------*/
BEGIN TRY
-- ************** For Logging And Alerts  ************************
DECLARE @MSG					VARCHAR(max)  = 'Start Time:'
											  +  CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt'))
											  + ' ' + @ProcName
DECLARE @AffectedRecordCount	BIGINT = 0
DECLARE @ProcessId				BIGINT
DECLARE @RowsInTargetBegin		BIGINT
DECLARE @RowsInTargetEnd		BIGINT
DECLARE @StartTime              DATETIME
DECLARE @EndTime                DATETIME

SET @RowsInTargetBegin			= 0
SET @StartTime                  = GETDATE()

RAISERROR (@MSG ,0,0)
-- ****************************************************************

TRUNCATE TABLE Consumption_FinanceHub.FactLaborCostForEarnedValue;


WITH cte_base AS (
	select *
    FROM [Consumption_FinanceHub].[FactGLCognos]
    WHERE Account IN (
                        'IS400000',
                        --'IS400010',
                        'IS400020',
                        'IS400100',
                        'IS400110',
                        'IS400120',
                        'IS400130',
                        'IS400140',
                        'IS400150',
                        'IS400160',
                        'IS400220',
                        'IS400400',
                        'IS500000',
                        --'IS500010',
                        'IS500015',
                        'IS500020',
                        'IS500100',
                        'IS500110',
                        'IS500120',
                        'IS500130',
                        'IS500140',
                        'IS500150',
                        'IS500160',
                        'IS500220',
                        'IS500300',
                        'IS500400'
                        )
    AND Company NOT IN ('FL0001', 'LE100', 'LE200')
    AND Actuality = 'AC'
	AND LocalCurrency = 'CHF'
),
cte_base_enriched as
(
select
	    f.Account,
	    a.AccountName,
	    a.SubAccountName,
	    f.Company,
	    c.Region,
	    c.Country,
	    g.COUNTRY_ID as PrimaGlobalCountryId,
	    g.COUNTRY_NAME as PrimaGlobalCountryName,
	    c.Office,
	    c1.CompanyDesc as CompanyDesc,
	    c2.CompanyDesc as OriginCompanyDesc,
	    c3.CompanyDesc as PartnerCompanyDesc,
	    f.Dim1 as DeptID,
	    d.DeptNameLong,
	    d.DeptNameShort,
	    d.DeptNameMed,
	    f.Year,
	    f.Month,
	    f.LocalCurrency,
	    f.TransCurrency,
	    f.Vtyp,
	    f.LocalAmountYTD,
	    f.LocalAmountPTD,
	    f.TransAmountYTD,
	    f.TransAmountPTD
       ,CASE WHEN [AccountName] LIKE '%- billable%' THEN 1
            WHEN [AccountName] LIKE '%- non billable%' THEN 0
            ELSE -1
        END AS [BillableFlag]
from cte_base f
left join [CONSUMPTION_FINANCE].[DimAccountDetailsCognos] a
on f.AccountDetailsCognosKey = a.AccountDetailsCognosKey
left join [CONSUMPTION_FINANCE].[DimCountry] c
on f.Company = c.CountryID
left join [CONSUMPTION_PRIMA].[GlobalCountries] g
on trim(c.Country) = trim(g.COUNTRY_NAME)
left join (select * from [CONSUMPTION_FINANCE].[DimCompany] where IsCurrent = 1) c1
on f.CompanyKey = c1.CompanyKey
left join (select * from [CONSUMPTION_FINANCE].[DimCompany] where IsCurrent = 1) c2
on f.OriginCompany = c2.Company
left join (select * from [CONSUMPTION_FINANCE].[DimCompany] where IsCurrent = 1) c3
on f.Partner = c3.Company
left join [CONSUMPTION_FINANCE].[DimDepartment] d
on f.DepartmentKey = d.DepartmentKey
),

-- Count how many Prima departments are mapped to each Finance department
cte_dept_count AS (
    SELECT [FinanceDepartmentId]
          ,COUNT(DISTINCT PrimaDepartmentId) AS [Count]
    FROM [dbo].[Full_Departmental_Map]
    GROUP BY [FinanceDepartmentId]
),

-- Join department mapping with count, so costs can be distributed evenly across all Prima departments
cte_dept_map AS (
    SELECT DISTINCT
           m.[FinanceDepartmentId]
          ,m.[PrimaDepartmentId]
          ,m.[PrimaDepartmentName]
          ,m.[CadenceDepartmentId]
          ,m.[CadenceDepartmentName]
          ,c.[Count]
    FROM [dbo].[Full_Departmental_Map] m
    LEFT JOIN cte_dept_count c ON m.[FinanceDepartmentId] = c.[FinanceDepartmentId]
),

-- Break quarterly period costs into 3 equal monthly amounts and distribute evenly across all Prima departments
cte_distribute_amount AS (
    -- Original quarter-end month (03/06/09/12) with 1/3 of quarterly cost
    SELECT base.[Account]
          ,base.[AccountName]
          ,base.[SubAccountName]
          ,base.[Company]
          ,base.[Region]
          ,base.[Country]
          ,base.[Office]
          ,base.[CompanyDesc]
          ,base.[DeptID]
          ,base.[DeptNameLong]
          ,base.[DeptNameShort]
          ,base.[DeptNameMed]
          ,base.[PrimaGlobalCountryId]
          ,base.[PrimaGlobalCountryName]
          ,dept.[PrimaDepartmentId]
          ,dept.[PrimaDepartmentName]
          ,dept.[CadenceDepartmentId]
          ,dept.[CadenceDepartmentName]
          ,base.[Year]
          ,base.[Month]
          ,base.[LocalCurrency]
          ,(base.[LocalAmountYTD] / dept.[Count]) AS [AmountYTD]
          ,((base.[LocalAmountPTD] / 3) / dept.[Count]) AS [AmountPTD]
          ,base.[BillableFlag]
          ,base.[Vtyp]
    FROM cte_base_enriched base
    LEFT JOIN cte_dept_map dept ON base.DeptID = dept.[FinanceDepartmentId]

    UNION ALL

    -- Month 2 of quarter: middle month (02/05/08/11) with 1/3 of quarterly cost, YTD adjusted
    SELECT base.[Account]
          ,base.[AccountName]
          ,base.[SubAccountName]
          ,base.[Company]
          ,base.[Region]
          ,base.[Country]
          ,base.[Office]
          ,base.[CompanyDesc]
          ,base.[DeptID]
          ,base.[DeptNameLong]
          ,base.[DeptNameShort]
          ,base.[DeptNameMed]
          ,base.[PrimaGlobalCountryId]
          ,base.[PrimaGlobalCountryName]
          ,dept.[PrimaDepartmentId]
          ,dept.[PrimaDepartmentName]
          ,dept.[CadenceDepartmentId]
          ,dept.[CadenceDepartmentName]
          ,base.[Year]
          ,CASE base.[Month]
               WHEN '03' THEN '02'
               WHEN '06' THEN '05'
               WHEN '09' THEN '08'
               WHEN '12' THEN '11'
               ELSE '00'
           END AS [Month]
          ,base.[LocalCurrency]
          ,((base.[LocalAmountYTD] - base.[LocalAmountPTD] / 3) / dept.[Count]) AS [AmountYTD]
          ,((base.[LocalAmountPTD] / 3) / dept.[Count]) AS [AmountPTD]
          ,base.[BillableFlag]
          ,base.[Vtyp]
    FROM cte_base_enriched base
    LEFT JOIN cte_dept_map dept ON base.DeptID = dept.[FinanceDepartmentId]

    UNION ALL

    -- Month 1 of quarter: first month (01/04/07/10) with 1/3 of quarterly cost, YTD adjusted
    SELECT base.[Account]
          ,base.[AccountName]
          ,base.[SubAccountName]
          ,base.[Company]
          ,base.[Region]
          ,base.[Country]
          ,base.[Office]
          ,base.[CompanyDesc]
          ,base.[DeptID]
          ,base.[DeptNameLong]
          ,base.[DeptNameShort]
          ,base.[DeptNameMed]
          ,base.[PrimaGlobalCountryId]
          ,base.[PrimaGlobalCountryName]
          ,dept.[PrimaDepartmentId]
          ,dept.[PrimaDepartmentName]
          ,dept.[CadenceDepartmentId]
          ,dept.[CadenceDepartmentName]
          ,base.[Year]
          ,CASE base.[Month]
               WHEN '03' THEN '01'
               WHEN '06' THEN '04'
               WHEN '09' THEN '07'
               WHEN '12' THEN '10'
               ELSE '00'
           END AS [Month]
          ,base.[LocalCurrency]
          ,((base.[LocalAmountYTD] - base.[LocalAmountPTD] / 3 * 2) / dept.[Count]) AS [AmountYTD]
          ,((base.[LocalAmountPTD] / 3) / dept.[Count]) AS [AmountPTD]
          ,base.[BillableFlag]
          ,base.[Vtyp]
    FROM cte_base_enriched base
    LEFT JOIN cte_dept_map dept
    ON base.DeptID = dept.[FinanceDepartmentId]
),
cte_result as
(    SELECT
        [Account],
        [AccountName],
        [SubAccountName],
        [Company],
        [Region],
        [Country],
        [Office],
        [CompanyDesc],
        [DeptID],
        [DeptNameLong],
        [DeptNameShort],
        [DeptNameMed],
        [PrimaGlobalCountryId],
        [PrimaGlobalCountryName],
        [PrimaDepartmentId],
        [PrimaDepartmentName],
        [CadenceDepartmentId],
        [CadenceDepartmentName],
        [Year],
        [Month],
        LocalCurrency AS Currency,  -- CHF
        AmountYTD,
        AmountPTD,
        [BillableFlag],
        [Vtyp]
    FROM cte_distribute_amount

    UNION ALL

    -- Convert CHF records to EUR, GBP, USD using monthly exchange rates (multiplication of records)
    SELECT
        t.[Account],
        t.[AccountName],
        t.[SubAccountName],
        t.[Company],
        t.[Region],
        t.[Country],
        t.[Office],
        t.[CompanyDesc],
        t.[DeptID],
        t.[DeptNameLong],
        t.[DeptNameShort],
        t.[DeptNameMed],
        t.[PrimaGlobalCountryId],
        t.[PrimaGlobalCountryName],
        t.[PrimaDepartmentId],
        t.[PrimaDepartmentName],
        t.[CadenceDepartmentId],
        t.[CadenceDepartmentName],
        t.[Year],
        t.[Month],
        r.ToCurrency AS Currency,
        (t.AmountYTD * r.Rate) AS AmountYTD,
        (t.AmountPTD * r.Rate) AS AmountPTD,
        t.[BillableFlag],
        t.[Vtyp]
    FROM cte_distribute_amount t
    CROSS JOIN (SELECT 'EUR' AS Currency UNION ALL
                SELECT 'GBP' AS Currency UNION ALL
                SELECT 'USD' AS Currency) c
    LEFT JOIN [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] r
        ON t.Year = r.Year
        AND t.Month = r.Month
        AND t.LocalCurrency = r.FromCurrency
        AND r.ToCurrency = c.Currency
)
INSERT INTO [Consumption_FinanceHub].[FactLaborCostForEarnedValue]
(
       [Account]
      ,[AccountName]
      ,[SubAccountName]
      ,[Company]
      ,[Region]
      ,[Country]
      ,[Office]
      ,[CompanyDesc]
      ,[DeptID]
      ,[DeptNameLong]
      ,[DeptNameShort]
      ,[DeptNameMed]
      ,[PrimaGlobalCountryId]
      ,[PrimaGlobalCountryName]
      ,[PrimaDepartmentId]
      ,[PrimaDepartmentName]
      ,[CadenceDepartmentId]
      ,[CadenceDepartmentName]
      ,[Year]
      ,[Month]
      ,[Currency]
      ,[AmountYTD]
      ,[AmountPTD]
      ,[BillableFlag]
      ,[Vtyp]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
SELECT
       [Account]
      ,[AccountName]
      ,[SubAccountName]
      ,[Company]
      ,[Region]
      ,[Country]
      ,[Office]
      ,[CompanyDesc]
      ,[DeptID]
      ,[DeptNameLong]
      ,[DeptNameShort]
      ,[DeptNameMed]
      ,[PrimaGlobalCountryId]
      ,[PrimaGlobalCountryName]
      ,[PrimaDepartmentId]
      ,[PrimaDepartmentName]
      ,[CadenceDepartmentId]
      ,[CadenceDepartmentName]
      ,[Year]
      ,[Month]
      ,[Currency]
      ,[AmountYTD]
      ,[AmountPTD]
      ,[BillableFlag]
      ,[Vtyp]
      ,@ProcShortName [CreatedBy]
      ,NULL [UpdatedBy]
      ,@StartTime [CreatedAt]
      ,NULL [UpdatedAt]
FROM cte_result S;


SET @RowsInTargetEnd        = (SELECT COUNT(*) FROM Consumption_FinanceHub.FactLaborCostForEarnedValue)
SET @AffectedRecordCount	= @RowsInTargetEnd - @RowsInTargetBegin
SET @EndTime                = GETDATE()
SET	@MSG                    = @MSG + ': New Rows Processed = '
							+ CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: '
							+ CAST(DATEDIFF(SECOND, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH FinanceHub ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0)



END TRY
/*----------------------------------------------------------------------*/
BEGIN CATCH

DECLARE @ErrorNum INT, @ErrorLine INT  ,@ErrorSeverity INT ,@ErrorState INT
DECLARE @ErrorProcedure NVARCHAR(126) ,@ErrorMessage NVARCHAR(2048)


    -- store all the error information for logging the error
    SELECT @ErrorNum       = ERROR_NUMBER()
          ,@ErrorLine      = 0
          ,@ErrorSeverity  = ERROR_SEVERITY()
          ,@ErrorState     = ERROR_STATE()
          ,@ErrorProcedure = ERROR_PROCEDURE()
          ,@ErrorMessage   = ERROR_MESSAGE()

	SET	@MSG	= @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ')
	EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'DWH FinanceHub ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
	RAISERROR (@MSG ,@ErrorSeverity,@ErrorState)


END CATCH


END
