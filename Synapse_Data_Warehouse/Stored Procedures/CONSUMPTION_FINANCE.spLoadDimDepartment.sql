CREATE PROC [CONSUMPTION_FINANCE].[spLoadDimDepartment] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadDimDepartment]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimDepartment])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [STAGING_FINANCE_FILE].[Departments];

insert into [STAGING_FINANCE_FILE].[Departments]
select 
       cast([Dept ID] as varchar(6)) as [DeptID]
      ,cast([Dept Name Long] as varchar(250)) as DeptNameLong
      ,cast([Dept Name Short] as varchar(250)) as DeptNameShort
      ,cast([DeptNameMed] as varchar(100)) as DeptNameMed
from [STAGING_FINANCE_FILE].[Departments_Raw]
where [Dept ID] is not null and [Dept ID] <> '';

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

select 
       a.[DeptID]
      ,a.[DeptNameLong]
      ,a.[DeptNameShort]
      ,a.[DeptNameMed]
      ,'1' as IsActive
      ,1 as IsCurrent
      ,'spLoadDimDepartment' as CreatedBy
      ,'spLoadDimDepartment' as UpdatedBy
      ,getdate() as CreatedAt
      ,getdate() as UpdatedAt
into #t
from [STAGING_FINANCE_FILE].[Departments] a
join [CONSUMPTION_FINANCE].[DimDepartment] b
on a.DeptID = b.DeptID
where concat
(
       a.[DeptNameLong]
      ,'|'
      ,a.[DeptNameShort]
      ,'|'
      ,a.[DeptNameMed]
) <> concat
(
       b.[DeptNameLong]
      ,'|'
      ,b.[DeptNameShort]
      ,'|'
      ,b.[DeptNameMed]
)
and b.IsCurrent = 1;

begin transaction

update [CONSUMPTION_FINANCE].[DimDepartment]
set IsCurrent = 0, UpdatedAt = getdate()
where DeptID in (select distinct DeptID from #t)
and IsCurrent = 1;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimDepartment]
(
       [DeptID]
      ,[DeptNameLong]
      ,[DeptNameShort]
      ,[DeptNameMed]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       [DeptID]
      ,[DeptNameLong]
      ,[DeptNameShort]
      ,[DeptNameMed]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
from #t;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimDepartment]
(
       [DeptID]
      ,[DeptNameLong]
      ,[DeptNameShort]
      ,[DeptNameMed]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       [DeptID]
      ,[DeptNameLong]
      ,[DeptNameShort]
      ,[DeptNameMed]
      ,'1'
      ,1
      ,'spLoadDimDepartment'
      ,'spLoadDimDepartment'
      ,getdate()
      ,getdate()
from [STAGING_FINANCE_FILE].[Departments]
where DeptID not in (select distinct DeptID from [CONSUMPTION_FINANCE].[DimDepartment]);

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

update [CONSUMPTION_FINANCE].[DimDepartment]
set IsActive = '0', UpdatedAt = getdate()
where DeptID not in (select distinct DeptID from [STAGING_FINANCE_FILE].[Departments])
and IsActive = '1'
and DeptID <> 'df';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimDepartment])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

rollback transaction

DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048) 

-- store all the error information for logging the error
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