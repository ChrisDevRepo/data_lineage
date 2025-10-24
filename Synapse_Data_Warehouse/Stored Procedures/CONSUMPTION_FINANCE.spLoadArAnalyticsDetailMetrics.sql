CREATE PROC [CONSUMPTION_FINANCE].[spLoadArAnalyticsDetailMetrics] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadArAnalyticsDetailMetrics]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )

BEGIN TRY

DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[ArAnalyticsDetailMetrics])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[ArAnalyticsDetailMetrics];

begin transaction

insert into [CONSUMPTION_FINANCE].[ArAnalyticsDetailMetrics]
(      [ArAnalyticsMetricsKey]
      ,[DimCustomerProjectKey]
      ,[DimCustomerKey]
      ,[DimProjectKey]
      ,[DimDocumentDateKey]
      ,[DimDueDateKey]
      ,[DimPaidDateKey]
      ,[DimPostDateKey]
      ,[DocumentDate]
      ,[DueDate]
      ,[PaidDate]
      ,[PostDate]
      ,[FilterValue]
      ,[YearQuarter]
      ,[DocumentNumber]
      ,[ProjectName]
      ,[CustomerName]
      ,[CostType]
      ,[Currency]
      ,[BusinessArea]
      ,[NetAmountTC]
	  ,[ConversionRate]	  
      ,[CHFNetAmountTC]
      ,[InvoiceDetails]
      ,[Advances]
      ,[VatAmountTC]
      ,[TotAmountTC]
      ,[PaymentTerms]
      ,[ContractDetails]
      ,[SalesForceNumber]
      ,[DaysToPay]
      ,[DaysLate]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]

)
select 
       a.[ArAnalyticsMetricsKey]
      ,a.[DimCustomerProjectKey]
      ,a.[DimCustomerKey]
      ,a.[DimProjectKey]
      ,b.[DimDocumentDateKey]
      ,b.[DimDueDateKey]
      ,b.[DimPaidDateKey]
      ,b.[DimPostDateKey]
      ,b.[DocumentDate]
      ,b.[DueDate]
      ,b.[PaidDate]
      ,b.[PostDate]
      ,a.[FilterValue]
      ,a.[YearQuarter]
      ,b.[DocumentNumber]
      ,a.[ProjectName]
      ,a.[CustomerName]
      ,a.[CostType]
      ,b.[Currency]
      ,b.[BusinessArea]
      ,b.[NetAmountTC]
	  ,b.[ConversionRate]	  
      ,b.[CHFNetAmountTC]
      ,b.[InvoiceDetails]
      ,b.[Advances]
      ,b.[VatAmountTC]
      ,b.[TotAmountTC]
      ,b.[PaymentTerms]
      ,b.[ContractDetails]
      ,b.[SalesForceNumber]
      ,b.[DaysToPay]
      ,b.[DaysLate],
    'spLoadFact_SAP_Sales_Summary' as [CreatedBy],
    'spLoadFact_SAP_Sales_Summary' as [UpdatedBy],
    getdate() as [CreatedAt],
    getdate() as [UpdatedAt]
from  [CONSUMPTION_FINANCE].[ArAnalyticsMetrics] a
inner join (select CONCAT(dod.Year, '-Q', dod.Quarter) as YearQuarter
                , dod.Date as [DocumentDate]
                , dud.Date as [DueDate]
                , pid.Date as [PaidDate]
                , pod.Date as [PostDate]
                ,f.[DimCustomerProjectKey]
                ,f.[DimDocumentDateKey]
                ,f.[DimDueDateKey]
                ,f.[DimPaidDateKey]
                ,f.[DimPostDateKey]
                ,f.[DocumentNumber]
                ,f.[CostType]
                ,f.[Currency]
                ,f.[BusinessArea]
                ,f.[NetAmountTC]
				,f.[ConversionRate]	  
	            ,f.[CHFNetAmountTC]
                ,f.[InvoiceDetails]
                ,f.[Advances]
                ,f.[VatAmountTC]
                ,f.[TotAmountTC]
                ,f.[PaymentTerms]
                ,f.[ContractDetails]
                ,f.[SalesForceNumber]
                ,f.[DaysToPay]
                ,f.[DaysLate]
            from [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Summary] f
                left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
                left join [dbo].[DimDate] dud on dud.[DimDateKey] = f.[DimDueDateKey]
                left join [dbo].[DimDate] pid on pid.[DimDateKey] = f.[DimPaidDateKey]
                left join [dbo].[DimDate] pod on pod.[DimDateKey] = f.[DimPostDateKey]
            ) b on a.YearQuarter = b.YearQuarter and a.[DimCustomerProjectKey]= b.[DimCustomerProjectKey] and a.CostType = b.CostType


	

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details_Metrics])
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
GO