CREATE PROC [CONSUMPTION_FINANCE].[spLoadArAnalyticsMetrics] AS

BEGIN

SET NOCOUNT ON


DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadArAnalyticsMetrics'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_FINANCE].[' + @ProcShortName + ']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ArAnalyticsMetrics'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY



if object_id(N'tempdb..#TotalInvoiceLines') is not null
begin drop table #TotalInvoiceLines; end


   SELECT CONCAT(dod.Year, '-Q', dod.Quarter) AS YearQuarter,
          dod.Year,
          dod.Quarter AS QuarterOfTheYear,
          p.ProjectName,
          c.CustomerName,
          f.CostType,
          f.DocumentNumber,
          COUNT(1) AS InvoiceLineCount
   into #TotalInvoiceLines                       
   FROM [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Details] f
       LEFT JOIN [CONSUMPTION_FINANCE].[DimCustomersProjects] cp
           ON cp.[DimCustomerProjectKey] = f.[DimCustomerProjectKey]
       LEFT JOIN [CONSUMPTION_FINANCE].[DimProjects] p
           ON p.[DimProjectKey] = cp.[DimProjectKey]
       LEFT JOIN [CONSUMPTION_FINANCE].[DimCustomers] c
           ON c.[DimCustomerKey] = cp.[DimCustomerKey]
       LEFT JOIN [dbo].[DimDate] dod
           ON dod.[DimDateKey] = f.[DimDocumentDateKey]
   WHERE f.[DimDocumentDateKey] IS NOT NULL
         AND dod.LastDayOfQuarter < FORMAT(GetDate(), 'd', 'en-US')
		 AND f.Account not in (SELECT ColumnValue FROM [CONSUMPTION_FINANCE].[DataFilters] where Tablename = 'ArAnalyticsMetrics - Invoice Count' and IncludeExclude = 'Exclude')
   GROUP BY CONCAT(dod.Year, '-Q', dod.Quarter),
            dod.Year,
            dod.Quarter,
            p.ProjectName,
            c.CustomerName,
            f.CostType,
            f.DocumentNumber


truncate table [CONSUMPTION_FINANCE].[ArAnalyticsMetrics]

insert into [CONSUMPTION_FINANCE].[ArAnalyticsMetrics]
select  DD.[DimProjectKey], DD.[DimCustomerKey], DD.[DimCustomerProjectKey], DD.[YearQuarter], DD.[Year], DD.[QuarterOfTheYear], DD.[QuarterNumber], DD.[FilterValue],  DD.[ProjectName], DD.[CustomerName], DD.[CostType], 
    SUM(DD.[SumDaysToPay]) as [TotalDaysToPay],
    SUM(DD.[SumDaysToPayRecordCount]) as [TotalDaysToPayRecordCount], 
    SUM(DD.[SumDaysLate]) as [TotalDaysLate],
    SUM(DD.[SumDaysLateRecordCount]) as [TotalDaysLateRecordCount], 
    SUM(EE.[InvoiceCount]) as [TotalInvoices], SUM(EE.[InvoiceLineCount]) as [TotalInvoiceLines],
    'spLoadArAnalyticsMetrics' as [CreatedBy],
    'spLoadArAnalyticsMetrics' as [UpdatedBy],
    getdate() as [CreatedAt],
    getdate() as [UpdatedAt]
from
(
    select qt.[YearQuarter], qt.[Year], qt.[QuarterOfTheYear], qt.[QuarterNumber], qt.[FilterValue],
    ft.[ProjectName], ft.[CustomerName], ft.[CostType], ft.[DimProjectKey], ft.[DimCustomerKey], ft.[DimCustomerProjectKey], ft.[SumDaysToPay], ft.[SumDaysToPayRecordCount], ft.[SumDaysLate], ft.[SumDaysLateRecordCount]
    from 
    (
        select CONCAT(dod.Year, '-Q', dod.[Quarter]) as YearQuarter, dod.Year, dod.[Quarter] as QuarterOfTheYear, p.[ProjectName], c.[CustomerName], f.[CostType] 
            , p.[DimProjectKey], c.[DimCustomerKey], f.[DimCustomerProjectKey]
            , SUM(case when f.[DimDocumentDateKey] is not null and f.[DaysToPay] is not null then f.[DaysToPay] else 0 end) as [SumDaysToPay]
            , SUM(case when f.[DimDocumentDateKey] is not null and f.[DaysToPay] is not null then 1 else 0 end) as [SumDaysToPayRecordCount]
            , SUM(case when f.[DimDocumentDateKey] is not null and f.[DaysLate] is not null then f.[DaysLate] else 0 end) as [SumDaysLate]
            , SUM(case when f.[DimDocumentDateKey] is not null and f.[DaysLate] is not null then 1 else 0 end) as [SumDaysLateRecordCount]
        from [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Summary] f
            left join [CONSUMPTION_FINANCE].[DimCustomersProjects] cp on cp.[DimCustomerProjectKey] = f.[DimCustomerProjectKey]  
            left join [CONSUMPTION_FINANCE].[DimProjects] p on p.[DimProjectKey] = cp.[DimProjectKey]
            left join [CONSUMPTION_FINANCE].[DimCustomers]  c on c.[DimCustomerKey] = cp.[DimCustomerKey]    
            left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
        where 
            dod.LastDayOfQuarter < FORMAT(GetDate(), 'd', 'en-US') 
        group by CONCAT(dod.Year, '-Q', dod.[Quarter]), dod.Year, dod.[Quarter], p.[ProjectName], c.[CustomerName], f.[CostType]
            , p.[DimProjectKey], c.[DimCustomerKey], f.[DimCustomerProjectKey]
    ) ft

    left join [CONSUMPTION_FINANCE].[QuarterRanges] qt on ft.[YearQuarter] = qt.[YearQuarter]
      
) DD 

left join (
            SELECT YearQuarter,
                   Year,
                   QuarterOfTheYear,
                   ProjectName,
                   CustomerName,
                   CostType,
                   COUNT(DISTINCT DocumentNumber) AS InvoiceCount,
                   SUM(InvoiceLineCount) AS InvoiceLineCount
            FROM   #TotalInvoiceLines
            GROUP BY YearQuarter,
                     Year,
                     QuarterOfTheYear,
                     ProjectName,
                     CustomerName,
                     CostType
        ) EE ON DD.YearQuarter     = EE.YearQuarter
            AND DD.ProjectName     = EE.ProjectName
            AND DD.CustomerName    = EE.CustomerName
            AND DD.CostType        = EE.CostType

group by  DD.[DimProjectKey], DD.[DimCustomerKey], DD.[DimCustomerProjectKey], DD.[YearQuarter], DD.[Year], DD.[QuarterOfTheYear], DD.[QuarterNumber], DD.[FilterValue], DD.[ProjectName], DD.[CustomerName], DD.[CostType]



SELECT @MSG  = 'End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

END TRY

BEGIN CATCH

IF @@TRANCOUNT > 0
  rollback transaction;

DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048) ,@EndMsg varchar(200)

--store all the error information for logging the error
SELECT @ErrorNum       = ERROR_NUMBER() 
      ,@ErrorLine      = 0
      ,@ErrorSeverity  = ERROR_SEVERITY()
      ,@ErrorState     = ERROR_STATE()
      ,@ErrorProcedure = ERROR_PROCEDURE()
      ,@ErrorMessage   = ERROR_MESSAGE()

SET @MSG = @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') 
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState

SELECT @EndMsg  = 'End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @EndMsg, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH

END
GO
