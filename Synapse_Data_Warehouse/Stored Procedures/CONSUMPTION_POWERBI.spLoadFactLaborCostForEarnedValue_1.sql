CREATE PROC [CONSUMPTION_POWERBI].[spLoadFactLaborCostForEarnedValue_1] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_POWERBI].[spLoadFactLaborCostForEarnedValue_1]'
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

if object_id(N'tempdb..#t1') is not null
begin drop table #t1; end

if object_id(N'tempdb..#t2') is not null
begin drop table #t2; end

truncate table [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue];

select
*
into #t1
from [CONSUMPTION_FINANCE].[vFactLaborCost]
where Account in
(
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
and Company not in ('FL0001', 'LE100', 'LE200');

select
m.[FinanceDepartmentId],
m.[PrimaDepartmentId],
m.[PrimaDepartmentName],
m.[CadenceDepartmentId],
m.[CadenceDepartmentName],
t.Count
into #t2
from [dbo].[Full_Departmental_Map] m
left join
(
select
[FinanceDepartmentId],
count(distinct PrimaDepartmentId) as Count
from [dbo].[Full_Departmental_Map]
group by [FinanceDepartmentId]
) t
on m.[FinanceDepartmentId] = t.[FinanceDepartmentId];

begin transaction

insert into [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
select 
       #t1.[Account]
      ,#t1.[AccountName]
      ,#t1.[SubAccountName]
      ,#t1.[Company]
      ,#t1.[Region]
      ,#t1.[Country]
      ,#t1.[Office]
      ,#t1.[CompanyDesc]
      ,#t1.[DeptID]
      ,#t1.[DeptNameLong]
      ,#t1.[DeptNameShort]
      ,#t1.[DeptNameMed]
      ,#t1.[PrimaGlobalCountryId]
      ,#t1.[PrimaGlobalCountryName]
      ,#t2.[PrimaDepartmentId]
      ,#t2.[PrimaDepartmentName]
      ,#t2.[CadenceDepartmentId]
      ,#t2.[CadenceDepartmentName]
      ,#t1.[Year]
      ,#t1.[Month]
      ,#t1.[LocalCurrency] as [Currency]
	  ,(#t1.[LocalAmountYTD] / [Count]) as [AmountYTD]
      ,((#t1.[LocalAmountPTD] / 3) / [Count]) as [AmountPTD]
      ,case when #t1.[AccountName] like '%- billable%' then 1 when #t1.[AccountName] like '%- non billable%' then 0 else -1 end as [BillableFlag]
      ,#t1.[Vtyp]
from #t1
left join #t2
on #t1.DeptID = #t2.[FinanceDepartmentId];

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
select 
       #t1.[Account]
      ,#t1.[AccountName]
      ,#t1.[SubAccountName]
      ,#t1.[Company]
      ,#t1.[Region]
      ,#t1.[Country]
      ,#t1.[Office]
      ,#t1.[CompanyDesc]
      ,#t1.[DeptID]
      ,#t1.[DeptNameLong]
      ,#t1.[DeptNameShort]
      ,#t1.[DeptNameMed]
      ,#t1.[PrimaGlobalCountryId]
      ,#t1.[PrimaGlobalCountryName]
      ,#t2.[PrimaDepartmentId]
      ,#t2.[PrimaDepartmentName]
      ,#t2.[CadenceDepartmentId]
      ,#t2.[CadenceDepartmentName]
      ,#t1.[Year]
      ,case #t1.[Month] when '03' then '02' when '06' then '05' when '09' then '08' when '12' then '11' else '00' end as [Month]
      ,#t1.[LocalCurrency] as [Currency]
	  ,((#t1.[LocalAmountYTD] - #t1.[LocalAmountPTD] / 3) / [Count]) as [AmountYTD]
      ,((#t1.[LocalAmountPTD] / 3) / [Count]) as [AmountPTD]
      ,case when #t1.[AccountName] like '%- billable%' then 1 when #t1.[AccountName] like '%- non billable%' then 0 else -1 end as [BillableFlag]
      ,#t1.[Vtyp]
from #t1
left join #t2
on #t1.DeptID = #t2.[FinanceDepartmentId];

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
select 
       #t1.[Account]
      ,#t1.[AccountName]
      ,#t1.[SubAccountName]
      ,#t1.[Company]
      ,#t1.[Region]
      ,#t1.[Country]
      ,#t1.[Office]
      ,#t1.[CompanyDesc]
      ,#t1.[DeptID]
      ,#t1.[DeptNameLong]
      ,#t1.[DeptNameShort]
      ,#t1.[DeptNameMed]
      ,#t1.[PrimaGlobalCountryId]
      ,#t1.[PrimaGlobalCountryName]
      ,#t2.[PrimaDepartmentId]
      ,#t2.[PrimaDepartmentName]
      ,#t2.[CadenceDepartmentId]
      ,#t2.[CadenceDepartmentName]
      ,#t1.[Year]
      ,case #t1.[Month] when '03' then '01' when '06' then '04' when '09' then '07' when '12' then '10' else '00' end as [Month]
      ,#t1.[LocalCurrency] as [Currency]
	  ,((#t1.[LocalAmountYTD] - #t1.[LocalAmountPTD] / 3 * 2) / [Count]) as [AmountYTD]
      ,((#t1.[LocalAmountPTD] / 3) / [Count]) as [AmountPTD]
      ,case when #t1.[AccountName] like '%- billable%' then 1 when #t1.[AccountName] like '%- non billable%' then 0 else -1 end as [BillableFlag]
      ,#t1.[Vtyp]
from #t1
left join #t2
on #t1.DeptID = #t2.[FinanceDepartmentId];

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t1') is not null
begin drop table #t1; end

if object_id(N'tempdb..#t2') is not null
begin drop table #t2; end

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