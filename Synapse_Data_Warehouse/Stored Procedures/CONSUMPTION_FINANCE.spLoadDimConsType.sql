CREATE PROC [CONSUMPTION_FINANCE].[spLoadDimConsType] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadDimConsType]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimConsType])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

select 
       a.[ConsType]
      ,a.[desc]
      ,a.[activ]
      ,1 as IsCurrent
      ,'spLoadDimConsType' as CreatedBy
      ,'spLoadDimConsType' as UpdatedBy
      ,getdate() as CreatedAt
      ,getdate() as UpdatedAt
into #t
from [STAGING_FINANCE_COGNOS].[t_ConsType_filter] a
join [CONSUMPTION_FINANCE].[DimConsType] b
on a.ConsType = b.ConsType
where concat
(
       a.[desc]
      ,'|'
      ,a.[activ]
) <> concat
(
       b.[ConsTypeDesc]
      ,'|'
      ,b.[IsActive]
)
and b.IsCurrent = 1;

begin transaction

update [CONSUMPTION_FINANCE].[DimConsType]
set IsCurrent = 0, UpdatedAt = getdate()
where ConsType in (select distinct ConsType from #t)
and IsCurrent = 1;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimConsType]
(
       [ConsType]
      ,[ConsTypeDesc]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       [ConsType]
      ,[desc]
      ,[activ]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
from #t;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimConsType]
(
       [ConsType]
      ,[ConsTypeDesc]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       [ConsType]
      ,[desc]
      ,[activ]
      ,1
      ,'spLoadDimConsType'
      ,'spLoadDimConsType'
      ,getdate()
      ,getdate()
from [STAGING_FINANCE_COGNOS].[t_ConsType_filter]
where ConsType not in (select distinct ConsType from [CONSUMPTION_FINANCE].[DimConsType]);

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

update [CONSUMPTION_FINANCE].[DimConsType]
set IsActive = '0', UpdatedAt = getdate()
where ConsType not in (select distinct ConsType from [STAGING_FINANCE_COGNOS].[t_ConsType_filter])
and IsActive = '1'
and ConsType <> 'df';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimConsType])
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