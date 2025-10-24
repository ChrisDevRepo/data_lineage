CREATE PROC [CONSUMPTION_FINANCE].[spLoadDimCompanyKoncern] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadDimCompanyKoncern]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimCompanyKoncern])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

-- Check for company koncern columns being unique identifier for [STAGING_FINANCE_COGNOS].[t_Company_filter] 
IF EXISTS (SELECT Company,koncern, Count(*) CountCompanyKoncern
			FROM [STAGING_FINANCE_COGNOS].[t_Company_filter]
			GROUP BY Company, koncern
			HAVING COUNT(*)> 1 )
BEGIN
  SET @MSG = 'Table:[STAGING_FINANCE_COGNOS].[t_Company_filter] - the combination of columns Company and koncern do not uniquely identify each row.' 
  RAISERROR (@MSG,16,1);
END

if object_id(N'tempdb..#Deduped_t_CompanyKoncern_filter') is not null
begin drop table #Deduped_t_CompanyKoncern_filter; end;

WITH PartitionedCompanyKoncern AS
(
SELECT company, koncern, activ, 
ROW_NUMBER() OVER (PARTITION BY company, koncern ORDER BY activ DESC) as RowNumber
FROM [STAGING_FINANCE_COGNOS].[t_Company_filter]
)
SELECT company, koncern, activ
INTO #Deduped_t_CompanyKoncern_filter
FROM PartitionedCompanyKoncern 
WHERE RowNumber = 1;

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

select 
       a.[company]
      ,a.[koncern]
      ,a.[activ]
      ,1 as IsCurrent
      ,'spLoadDimCompanyKoncern' as CreatedBy
      ,'spLoadDimCompanyKoncern' as UpdatedBy
      ,getdate() as CreatedAt
      ,getdate() as UpdatedAt
into #t
from #Deduped_t_CompanyKoncern_filter a
join [CONSUMPTION_FINANCE].[DimCompanyKoncern] b
on a.Company = b.Company AND a.koncern = b.koncern
where ISNULL(a.[activ],-1) <> ISNULL( b.[isActive],-1)
and b.IsCurrent = 1;

---
begin transaction

update d
set IsCurrent = 0, UpdatedAt = getdate()
FROM [CONSUMPTION_FINANCE].[DimCompanyKoncern] d
JOIN #t 
ON d.Company = #t.Company 
AND d.Koncern = #t.Koncern
WHERE d.IsCurrent = 1;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimCompanyKoncern]
(
      [Company]
      ,[Koncern]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select #t.[company]
      ,#t.[Koncern]
      ,#t.[activ]
      ,#t.[IsCurrent]
      ,#t.[CreatedBy]
      ,#t.[UpdatedBy]
      ,#t.[CreatedAt]
      ,#t.[UpdatedAt]
from #t
WHERE EXISTS (SELECT 1 FROM  [CONSUMPTION_FINANCE].[DimCompanyKoncern] dc 
				WHERE #t.Company = dc.Company AND  #t.Koncern = dc.Koncern);

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimCompanyKoncern]
(
      [Company]
      ,[Koncern]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
	  t.[company]
      ,t.[Koncern]
      ,t.[activ]
      ,1
      ,'spLoadDimCompanyKoncern'
      ,'spLoadDimCompanyKoncern'
      ,getdate()
      ,getdate()
from #Deduped_t_CompanyKoncern_filter t
left join [CONSUMPTION_FINANCE].[DimCompanyKoncern] dc 
on t.Company = dc.Company and t.Koncern = dc.Koncern
where NOT EXISTS (select 1 from [CONSUMPTION_FINANCE].[DimCompanyKoncern] D WHERE D.Company = t.Company and D.Koncern = t.Koncern);

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

update D
set IsActive = '0', UpdatedAt = getdate()
FROM [CONSUMPTION_FINANCE].[DimCompanyKoncern] D
where NOT EXISTS (select 1 from [STAGING_FINANCE_COGNOS].[t_Company_filter] DC WHERE D.Company = DC.Company and D.Koncern = DC.Koncern)
and IsActive = '1'
and Company <> 'df';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimCompanyKoncern])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
  rollback transaction
END

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