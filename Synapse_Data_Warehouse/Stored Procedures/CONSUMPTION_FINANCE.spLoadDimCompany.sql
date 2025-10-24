CREATE PROC [CONSUMPTION_FINANCE].[spLoadDimCompany] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadDimCompany]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimCompany])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

-- Check for company being unique identifier for combination of columns boltyp, vkodlc and company_desc
IF EXISTS (SELECT Company, Count(*) CountCompany
			FROM (
				SELECT DISTINCT company, boltyp, vkodlc,company_desc
				FROM [STAGING_FINANCE_COGNOS].[t_Company_filter]
			) C
			GROUP BY Company
			HAVING COUNT(*)> 1 )
BEGIN
  SET @MSG = 'Table:[STAGING_FINANCE_COGNOS].[t_Company_filter] - column Company does not uniquely identify boltyp, vkodlc, and company_desc.' 
  RAISERROR (@MSG,16,1);
END

if object_id(N'tempdb..#Deduped_t_Company_filter') is not null
begin drop table #Deduped_t_Company_filter; end;

WITH PartitionedCompany AS
(
SELECT company, boltyp, vkodlc,company_desc, activ, 
ROW_NUMBER() OVER (PARTITION BY company, boltyp, vkodlc,company_desc ORDER BY activ DESC) as RowNumber
FROM [STAGING_FINANCE_COGNOS].[t_Company_filter]
)
SELECT company, boltyp, vkodlc,company_desc, activ
INTO #Deduped_t_Company_filter
FROM PartitionedCompany 
WHERE RowNumber = 1;


if object_id(N'tempdb..#t') is not null
begin drop table #t; end

select 
       a.[company]
      ,a.[company_desc]
      ,a.[boltyp]
      ,a.[vkodlc]
      ,a.[activ]
      ,1 as IsCurrent
      ,'spLoadDimCompany' as CreatedBy
      ,'spLoadDimCompany' as UpdatedBy
      ,getdate() as CreatedAt
      ,getdate() as UpdatedAt
into #t
from #Deduped_t_Company_filter a
join [CONSUMPTION_FINANCE].[DimCompany] b
on a.Company = b.Company
where concat
(
       a.[company_desc]
      ,'|'
      ,a.[boltyp]
      ,'|'
      ,a.[vkodlc]
      ,'|'
      ,a.[activ]
) <> concat
(
       b.[CompanyDesc]
      ,'|'
      ,b.[boltyp]
      ,'|'
      ,b.[vkodlc]
      ,'|'
      ,b.[IsActive]
)
and b.IsCurrent = 1;

begin transaction

update [CONSUMPTION_FINANCE].[DimCompany]
set IsCurrent = 0, UpdatedAt = getdate()
where Company in (select distinct Company from #t)
and IsCurrent = 1;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimCompany]
(
       [CountryKey]
      ,[Company]
      ,[CompanyDesc]
      ,[boltyp]
      ,[vkodlc]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       coalesce(dc.[CountryKey], 0) as [CountryKey]
      ,#t.[company]
      ,#t.[company_desc]
      ,#t.[boltyp]
      ,#t.[vkodlc]
      ,#t.[activ]
      ,#t.[IsCurrent]
      ,#t.[CreatedBy]
      ,#t.[UpdatedBy]
      ,#t.[CreatedAt]
      ,#t.[UpdatedAt]
from #t
left join [CONSUMPTION_FINANCE].[DimCountry] dc 
on #t.Company = dc.CountryID;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

insert into [CONSUMPTION_FINANCE].[DimCompany]
(
       [CountryKey]
      ,[Company]
      ,[CompanyDesc]
      ,[boltyp]
      ,[vkodlc]
      ,[IsActive]
      ,[IsCurrent]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select 
       coalesce(dc.[CountryKey], 0) as [CountryKey]
      ,t.[company]
      ,t.[company_desc]
      ,t.[boltyp]
      ,t.[vkodlc]
      ,t.[activ]
      ,1
      ,'spLoadDimCompany'
      ,'spLoadDimCompany'
      ,getdate()
      ,getdate()
from #Deduped_t_Company_filter t
left join [CONSUMPTION_FINANCE].[DimCountry] dc 
on t.Company = dc.CountryID
where t.Company not in (select distinct Company from [CONSUMPTION_FINANCE].[DimCompany]);

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

update [CONSUMPTION_FINANCE].[DimCompany]
set IsActive = '0', UpdatedAt = getdate()
where Company not in (select distinct Company from [STAGING_FINANCE_COGNOS].[t_Company_filter])
and IsActive = '1'
and Company <> 'df';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

if object_id(N'tempdb..#t') is not null
begin drop table #t; end

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[DimCompany])
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