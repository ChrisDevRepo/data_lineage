CREATE PROCEDURE [CONSUMPTION_PRIMA].[spLoadEnrollmentPlanSitesHistory]
AS
BEGIN

SET NOCOUNT ON

/*-------------------------------------------------------------------------------*/
DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_PRIMA].[spLoadEnrollmentPlanSitesHistory]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[EnrollmentPlanSitesHistory])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 
-- ****************************************************************

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

select 
	a.[RECORD_ID], 
	a.[REGION_PLAN_RECORD_ID], 
	a.[SITE_ID], 
	a.[PLAN_1], 
	a.[PLAN_2], 
	a.[PLAN_3], 
	a.[ESTIMATED_PLAN], 
	a.[CREATED_BY], 
	a.[CREATED_AT], 
	a.[UPDATED_BY], 
	a.[UPDATED_AT], 
	a.[RECORD_STATUS],
	dateadd(day, 0, a.[UPDATED_AT]) as StartDate,
	'12/31/9999' as EndDAte,
	1 as IsCurrent
into #t
from CONSUMPTION_PRIMA.EnrollmentPlanSites a
join CONSUMPTION_PRIMA.EnrollmentPlanSitesHistory b
on (a.Record_ID = b.Record_ID and a.Site_id = b.Site_Id )
where 
(
isnull(a.[PLAN_1], -1) <> isnull(b.[PLAN_1], -1) or
isnull(a.[PLAN_2], -1) <> isnull(b.[PLAN_2], -1) or 
isnull(a.[PLAN_3], -1) <> isnull(b.[PLAN_3], -1) or
isnull(a.[ESTIMATED_PLAN], -1) <> isnull(b.[ESTIMATED_PLAN], -1) or
isnull(a.[RECORD_STATUS], -1) <> isnull(b.[RECORD_STATUS], -1) 
)
and b.IsCurrent = 1;

begin transaction

merge CONSUMPTION_PRIMA.EnrollmentPlanSitesHistory	as T -- Target
using CONSUMPTION_PRIMA.EnrollmentPlanSites     	as S -- Source
on (T.Record_ID = S.Record_ID and T.Site_id = S.Site_Id )
-- New Rows 
when not matched by target then 
insert 
(
		[RECORD_ID], 
		[REGION_PLAN_RECORD_ID], 
		[SITE_ID], 
		[PLAN_1], 
		[PLAN_2], 
		[PLAN_3], 
		[ESTIMATED_PLAN], 
		[CREATED_BY], 
		[CREATED_AT], 
		[UPDATED_BY], 
		[UPDATED_AT], 
		[RECORD_STATUS], 
		[StartDate], 
		[EndDate], 
		[IsCurrent]
)
values
(
	s.[RECORD_ID], 
	s.[REGION_PLAN_RECORD_ID], 
	s.[SITE_ID], 
	s.[PLAN_1], 
	s.[PLAN_2], 
	s.[PLAN_3], 
	s.[ESTIMATED_PLAN], 
	s.[CREATED_BY], 
	s.[CREATED_AT], 
	s.[UPDATED_BY], 
	s.[UPDATED_AT], 
	s.[RECORD_STATUS],
	isnull(s.[Updated_At], s.[CREATED_AT]), --StartDate
	'12/31/9999', --EndDate
	1 --IsCurrent	
)
when matched and T.iscurrent = 1 
and
( 
isnull(T.[PLAN_1], -1) <> isnull(S.[PLAN_1], -1) or
isnull(T.[PLAN_2], -1) <> isnull(S.[PLAN_2], -1) or 
isnull(T.[PLAN_3], -1) <> isnull(S.[PLAN_3], -1) or
isnull(T.[ESTIMATED_PLAN], -1) <> isnull(S.[ESTIMATED_PLAN], -1) or
isnull(T.[RECORD_STATUS], -1) <> isnull(S.[RECORD_STATUS], -1) 
)
then 
update set T.IsCurrent = 0, T.EndDate = dateadd(day, -1, S.[Updated_AT]);

insert into CONSUMPTION_PRIMA.EnrollmentPlanSitesHistory
(
		[RECORD_ID], 
		[REGION_PLAN_RECORD_ID], 
		[SITE_ID], 
		[PLAN_1], 
		[PLAN_2], 
		[PLAN_3], 
		[ESTIMATED_PLAN], 
		[CREATED_BY], 
		[CREATED_AT], 
		[UPDATED_BY], 
		[UPDATED_AT], 
		[RECORD_STATUS], 
		[StartDate], 
		[EndDate], 
		[IsCurrent]
)
select 
		[RECORD_ID], 
		[REGION_PLAN_RECORD_ID], 
		[SITE_ID], 
		[PLAN_1], 
		[PLAN_2], 
		[PLAN_3], 
		[ESTIMATED_PLAN], 
		[CREATED_BY], 
		[CREATED_AT], 
		[UPDATED_BY], 
		[UPDATED_AT], 
		[RECORD_STATUS], 
		[StartDate], 
		[EndDate], 
		[IsCurrent]
from #t;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[EnrollmentPlanSitesHistory])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY
/*----------------------------------------------------------------------*/
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
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH
 
END