CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactLaborCostForEarnedValue] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadFactLaborCostForEarnedValue]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactLaborCostForEarnedValue])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

if object_id(N'tempdb..#t1') is not null
begin drop table #t1; end

if object_id(N'tempdb..#t2') is not null
begin drop table #t2; end

truncate table [CONSUMPTION_FINANCE].[FactLaborCostForEarnedValue];

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
and Company <> 'FL0001';

select
m.[SalSysDepartment Id],
m.[HrDepartment Id],
t.Count
into #t2
from [CONSUMPTION_PRIMA].[HrDepartmentToFinanceSalSysMap] m
left join
(
select
[SalSysDepartment Id],
count(*) as Count
from [CONSUMPTION_PRIMA].[HrDepartmentToFinanceSalSysMap]
group by [SalSysDepartment Id]
) t
on m.[SalSysDepartment Id] = t.[SalSysDepartment Id];

begin transaction

insert into [CONSUMPTION_FINANCE].[FactLaborCostForEarnedValue]
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
      ,#t2.[HrDepartment Id] as [PrimaHrDepartmentId]
      ,h.[DEPARTMENT] as [PrimaHrDepartmentName]
      ,#t1.[Year]
      ,#t1.[Month]
      ,#t1.[LocalCurrency] as [Currency]
	  ,(#t1.[LocalAmountYTD] / [Count]) as [AmountYTD]
      ,((#t1.[LocalAmountPTD] / 3) / [Count]) as [AmountPTD]
      ,case when #t1.[AccountName] like '%- billable%' then 1 when #t1.[AccountName] like '%- non billable%' then 0 else -1 end as [BillableFlag]
      ,#t1.[Vtyp]
from #t1
left join #t2
on #t1.DeptID = #t2.[SalSysDepartment Id]
left join [CONSUMPTION_PRIMA].[HrDepartments] h
on #t2.[HrDepartment Id] = h.DEPARTMENT_ID;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[FactLaborCostForEarnedValue]
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
      ,#t2.[HrDepartment Id] as [PrimaHrDepartmentId]
      ,h.[DEPARTMENT] as [PrimaHrDepartmentName]
      ,#t1.[Year]
      ,case #t1.[Month] when '03' then '02' when '06' then '05' when '09' then '08' when '12' then '11' else '00' end as [Month]
      ,#t1.[LocalCurrency] as [Currency]
	  ,((#t1.[LocalAmountYTD] - #t1.[LocalAmountPTD] / 3) / [Count]) as [AmountYTD]
      ,((#t1.[LocalAmountPTD] / 3) / [Count]) as [AmountPTD]
      ,case when #t1.[AccountName] like '%- billable%' then 1 when #t1.[AccountName] like '%- non billable%' then 0 else -1 end as [BillableFlag]
      ,#t1.[Vtyp]
from #t1
left join #t2
on #t1.DeptID = #t2.[SalSysDepartment Id]
left join [CONSUMPTION_PRIMA].[HrDepartments] h
on #t2.[HrDepartment Id] = h.DEPARTMENT_ID;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[FactLaborCostForEarnedValue]
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
      ,#t2.[HrDepartment Id] as [PrimaHrDepartmentId]
      ,h.[DEPARTMENT] as [PrimaHrDepartmentName]
      ,#t1.[Year]
      ,case #t1.[Month] when '03' then '01' when '06' then '04' when '09' then '07' when '12' then '10' else '00' end as [Month]
      ,#t1.[LocalCurrency] as [Currency]
	  ,((#t1.[LocalAmountYTD] - #t1.[LocalAmountPTD] / 3 * 2) / [Count]) as [AmountYTD]
      ,((#t1.[LocalAmountPTD] / 3) / [Count]) as [AmountPTD]
      ,case when #t1.[AccountName] like '%- billable%' then 1 when #t1.[AccountName] like '%- non billable%' then 0 else -1 end as [BillableFlag]
      ,#t1.[Vtyp]
from #t1
left join #t2
on #t1.DeptID = #t2.[SalSysDepartment Id]
left join [CONSUMPTION_PRIMA].[HrDepartments] h
on #t2.[HrDepartment Id] = h.DEPARTMENT_ID;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t1') is not null
begin drop table #t1; end

if object_id(N'tempdb..#t2') is not null
begin drop table #t2; end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactLaborCostForEarnedValue])
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
