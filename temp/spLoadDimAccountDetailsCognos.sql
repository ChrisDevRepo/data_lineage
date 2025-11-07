CREATE PROC [Consumption_FinanceHub].[spLoadDimAccountDetailsCognos] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[Consumption_FinanceHub].[spLoadDimAccountDetailsCognos]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [Consumption_FinanceHub].[DimAccountDetailsCognos])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [STAGING_FINANCE_FILE].[COGNOS_Template_SubAccounts];

insert into [STAGING_FINANCE_FILE].[COGNOS_Template_SubAccounts]
select 
       [Account]
      ,[AccountName]
      ,[AccountSort]
      ,[SubAccountName]
      ,[SubAccountSort]
      ,[Companies]
      ,[Summary]
      ,[Category]
      ,[CategorySort]
      ,[Group]
      ,[GroupSort]
      ,[Template]
from
(
select 
       cast([Template] as varchar(100)) as Template
      ,cast([GroupSort] as tinyint) as GroupSort
      ,cast([Group] as varchar(250)) as [Group]
      ,cast([CategorySort] as tinyint) as CategorySort
      ,cast([Category] as varchar(250)) as Category
      ,cast([AccountSort] as smallint) as AccountSort
      ,cast([Account Name] as varchar(250)) as AccountName
      ,cast([SubAccount Sort] as smallint) as SubAccountSort
      ,cast([SubAccount Name] as varchar(250)) as SubAccountName
      ,cast([Companies] as varchar(50)) as Companies
      ,cast([Summary] as varchar(10)) as Summary
      ,cast([Account] as varchar(13)) as Account
	  ,rank() over (partition by cast([Account] as varchar(13)) order by cast([AccountSort] as smallint)) as rank
from [STAGING_FINANCE_FILE].[COGNOS_Template_SubAccounts_Raw]
where Account is not null and Account <> ''
) t
where rank = 1;

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

select 
       a.[Account]
      ,a.[AccountName]
      ,a.[AccountSort]
      ,a.[SubAccountName]
      ,a.[SubAccountSort]
      ,a.[Companies]
      ,a.[Summary]
      ,a.[Category]
      ,a.[CategorySort]
      ,a.[Group]
      ,a.[GroupSort]
      ,a.[Template]
      ,'1' as IsActive
      ,1 as IsCurrent
      ,'spLoadDimAccountDetailsCognos' as CreatedBy
      ,'spLoadDimAccountDetailsCognos' as UpdatedBy
      ,getdate() as CreatedAt
      ,getdate() as UpdatedAt
into #t
from [STAGING_FINANCE_FILE].[COGNOS_Template_SubAccounts] a
join [Consumption_FinanceHub].[DimAccountDetailsCognos] b
on a.Account = b.Account
where concat
(
       a.[AccountName]
      ,'|'
      ,a.[AccountSort]
      ,'|'
      ,a.[SubAccountName]
      ,'|'
      ,a.[SubAccountSort]
      ,'|'
      ,a.[Companies]
      ,'|'
      ,a.[Summary]
      ,'|'
      ,a.[Category]
      ,'|'
      ,a.[CategorySort]
      ,'|'
      ,a.[Group]
      ,'|'
      ,a.[GroupSort]
      ,'|'
      ,a.[Template]
) <> concat
(
       b.[AccountName]
      ,'|'
      ,b.[AccountSort]
      ,'|'
      ,b.[SubAccountName]
      ,'|'
      ,b.[SubAccountSort]
      ,'|'
      ,b.[Companies]
      ,'|'
      ,b.[Summary]
      ,'|'
      ,b.[Category]
      ,'|'
      ,b.[CategorySort]
      ,'|'
      ,b.[Group]
      ,'|'
      ,b.[GroupSort]
      ,'|'
      ,b.[Template]
)
and b.IsCurrent = 1;

begin transaction

update [Consumption_FinanceHub].[DimAccountDetailsCognos]
set IsCurrent = 0, UpdatedAt = getdate()
where Account in (select distinct Account from #t)
and IsCurrent = 1;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [Consumption_FinanceHub].[DimAccountDetailsCognos]
(
       [Account]
      ,[AccountName]
      ,[AccountSort]
      ,[SubAccountName]
      ,[SubAccountSort]
      ,[Companies]
      ,[Summary]
      ,[Category]
      ,[CategorySort]
      ,[Group]
      ,[GroupSort]
      ,[Template]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       [Account]
      ,[AccountName]
      ,[AccountSort]
      ,[SubAccountName]
      ,[SubAccountSort]
      ,[Companies]
      ,[Summary]
      ,[Category]
      ,[CategorySort]
      ,[Group]
      ,[GroupSort]
      ,[Template]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
from #t;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [Consumption_FinanceHub].[DimAccountDetailsCognos]
(
       [Account]
      ,[AccountName]
      ,[AccountSort]
      ,[SubAccountName]
      ,[SubAccountSort]
      ,[Companies]
      ,[Summary]
      ,[Category]
      ,[CategorySort]
      ,[Group]
      ,[GroupSort]
      ,[Template]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       [Account]
      ,[AccountName]
      ,[AccountSort]
      ,[SubAccountName]
      ,[SubAccountSort]
      ,[Companies]
      ,[Summary]
      ,[Category]
      ,[CategorySort]
      ,[Group]
      ,[GroupSort]
      ,[Template]
      ,'1'
      ,1
      ,'spLoadDimAccountDetailsCognos'
      ,'spLoadDimAccountDetailsCognos'
      ,getdate()
      ,getdate()
from [STAGING_FINANCE_FILE].[COGNOS_Template_SubAccounts]
where Account not in (select distinct Account from [Consumption_FinanceHub].[DimAccountDetailsCognos]);

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

update [Consumption_FinanceHub].[DimAccountDetailsCognos]
set IsActive = '0', UpdatedAt = getdate()
where Account not in (select distinct Account from [STAGING_FINANCE_FILE].[COGNOS_Template_SubAccounts])
and IsActive = '1'
and Account <> 'default';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [Consumption_FinanceHub].[DimAccountDetailsCognos])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'DWH FinanceHub ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

IF @@TRANCOUNT > 0
    rollback transaction;

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
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'DWH FinanceHub ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH

END
