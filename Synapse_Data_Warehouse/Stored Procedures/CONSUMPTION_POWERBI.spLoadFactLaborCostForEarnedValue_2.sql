CREATE PROC [CONSUMPTION_POWERBI].[spLoadFactLaborCostForEarnedValue_2] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_POWERBI].[spLoadFactLaborCostForEarnedValue_2]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )

BEGIN TRY

DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

begin transaction

insert into [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
select 
       t.[Account]
      ,t.[AccountName]
      ,t.[SubAccountName]
      ,t.[Company]
      ,t.[Region]
      ,t.[Country]
      ,t.[Office]
      ,t.[CompanyDesc]
      ,t.[DeptID]
      ,t.[DeptNameLong]
      ,t.[DeptNameShort]
      ,t.[DeptNameMed]
      ,t.[PrimaGlobalCountryId]
      ,t.[PrimaGlobalCountryName]
      ,t.[PrimaDepartmentId]
      ,t.[PrimaDepartmentName]
      ,t.[CadenceDepartmentId]
      ,t.[CadenceDepartmentName]
      ,t.[Year]
      ,t.[Month]
      ,r.ToCurrency as Currency
      ,(t.AmountYTD * r.Rate) as AmountYTD
      ,(t.AmountPTD * r.Rate) as AmountPTD
      ,t.[BillableFlag]
      ,t.[Vtyp]
from (select * from [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] where Currency = 'CHF') t
left join [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] r
on t.Year = r.Year and t.Month = r.Month and t.Currency = r.FromCurrency and r.ToCurrency = 'EUR';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
select 
       t.[Account]
      ,t.[AccountName]
      ,t.[SubAccountName]
      ,t.[Company]
      ,t.[Region]
      ,t.[Country]
      ,t.[Office]
      ,t.[CompanyDesc]
      ,t.[DeptID]
      ,t.[DeptNameLong]
      ,t.[DeptNameShort]
      ,t.[DeptNameMed]
      ,t.[PrimaGlobalCountryId]
      ,t.[PrimaGlobalCountryName]
      ,t.[PrimaDepartmentId]
      ,t.[PrimaDepartmentName]
      ,t.[CadenceDepartmentId]
      ,t.[CadenceDepartmentName]
      ,t.[Year]
      ,t.[Month]
      ,r.ToCurrency as Currency
      ,(t.AmountYTD * r.Rate) as AmountYTD
      ,(t.AmountPTD * r.Rate) as AmountPTD
      ,t.[BillableFlag]
      ,t.[Vtyp]
from (select * from [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] where Currency = 'CHF') t
left join [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] r
on t.Year = r.Year and t.Month = r.Month and t.Currency = r.FromCurrency and r.ToCurrency = 'GBP';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
select 
       t.[Account]
      ,t.[AccountName]
      ,t.[SubAccountName]
      ,t.[Company]
      ,t.[Region]
      ,t.[Country]
      ,t.[Office]
      ,t.[CompanyDesc]
      ,t.[DeptID]
      ,t.[DeptNameLong]
      ,t.[DeptNameShort]
      ,t.[DeptNameMed]
      ,t.[PrimaGlobalCountryId]
      ,t.[PrimaGlobalCountryName]
      ,t.[PrimaDepartmentId]
      ,t.[PrimaDepartmentName]
      ,t.[CadenceDepartmentId]
      ,t.[CadenceDepartmentName]
      ,t.[Year]
      ,t.[Month]
      ,r.ToCurrency as Currency
      ,(t.AmountYTD * r.Rate) as AmountYTD
      ,(t.AmountPTD * r.Rate) as AmountPTD
      ,t.[BillableFlag]
      ,t.[Vtyp]
from (select * from [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue] where Currency = 'CHF') t
left join [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] r
on t.Year = r.Year and t.Month = r.Month and t.Currency = r.FromCurrency and r.ToCurrency = 'USD';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

rollback transaction

DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048) 

--store all the error information for logging the error
SELECT @ErrorNum       = ERROR_NUMBER() 
      ,@ErrorLine      = 0
      ,@ErrorSeverity  = ERROR_SEVERITY()
      ,@ErrorState     = ERROR_STATE()
      ,@ErrorProcedure = ERROR_PROCEDURE()
      ,@ErrorMessage   = ERROR_MESSAGE()

SET @MSG = @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') 
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH

END