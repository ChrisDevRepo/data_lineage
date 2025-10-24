Create PROC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskSnapshot] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskSnapshot]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskSnapshot])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskSnapshot];

begin transaction

insert into [CONSUMPTION_FINANCE].[FactSAPSalesSponsorRiskSnapshot]

select 
 f.[DimCustomerProjectKey]  as [DimCustomerProjectKey]
,cp.[DimProjectKey] as [DimProjectKey]
,cp.[DimCustomerKey] as [DimCustomerKey]
,f.[Currency] as [Currency]
,f.[CostType] as [CostType]
 ,SUM(CASE WHEN f.[NetAmountTC] NOT LIKE '-%' AND (f.[PaymentTerms] IS NOT NULL AND f.[PaymentTerms] <> '') AND (f.[DimDueDateKey] IS NOT NULL AND f.[DimDueDateKey] <> '') THEN f.[NetAmountTC] ELSE 0 END)
as [TotalAdvanceInvoiced]

,SUM(CASE WHEN f.[NetAmountTC] LIKE '-%' AND (f.[PaymentTerms] IS NULL OR f.[PaymentTerms] = '' OR f.[PaymentTerms] = 'N000') AND (f.[DimDueDateKey] IS NOT NULL AND f.[DimDueDateKey] <> '') THEN f.[NetAmountTC] ELSE 0 END)
as [TotalCreditsInvoices]
,SUM(CASE WHEN ((f.[NetAmountTC] LIKE '%-%' AND (f.[PaymentTerms] IS NULL OR f.[PaymentTerms] = '') AND (f.[DimDueDateKey] IS NULL OR f.[DimDueDateKey] = '') )
            OR
                (f.[NetAmountTC] LIKE '%-%' AND (f.[PaymentTerms] IS NOT NULL AND f.[PaymentTerms] <> '' AND f.[PaymentTerms] <> 'N000') AND (f.[DimDueDateKey] IS NOT NULL AND f.[DimDueDateKey] <> '') )
            OR
                (f.[NetAmountTC] NOT LIKE '%-%' AND (f.[PaymentTerms] IS NULL OR f.[PaymentTerms] = '') ) ) THEN f.[NetAmountTC] ELSE 0 END) AS [TotalAdvancewithdrawn]
, SUM(f.[NetAmountTC]) as [AdvanceBalance]
,SUM(CASE WHEN f.[NetAmountTC] > 0 AND  pid.[Date] IS NULL    AND  f.[InternalInvoice] = '' THEN  f.[NetAmountTC] Else 0  END ) AS [UnpaidAdvanceRisk]
, SUM(f.[NetAmountTC]) - SUM(CASE WHEN f.[NetAmountTC] > 0 AND  pid.[Date] IS NULL    AND  f.[InternalInvoice] = '' THEN  f.[NetAmountTC] Else 0  END )AS [AvailableFunds]

,Getdate() as ProcessDate,
'spLoadFactSAPSalesSponsorRiskSnapshot' as [CreatedBy],
'spLoadFactSAPSalesSponsorRiskSnapshot' as [UpdatedBy],
getdate() as [CreatedAt],
getdate() as [UpdatedAt]

from  [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Details] f
left join [CONSUMPTION_FINANCE].[DimCustomersProjects] cp on cp.[DimCustomerProjectKey] = f.[DimCustomerProjectKey]
left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
left join [dbo].[DimDate] dud on dud.[DimDateKey] = f.[DimDueDateKey]
left join [dbo].[DimDate] pid on pid.[DimDateKey] = f.[DimPaidDateKey]

 where  

 (f.Account in (select distinct ColumnValue from [CONSUMPTION_FINANCE].[DataFilters] where [Tablename] = 'FactSAPSalesSponsorRiskSnapshot-OOP' and ColumnName = 'Account' )
 and f.CostType = 'OOP')
 or
 (f.Account in (select distinct ColumnValue from [CONSUMPTION_FINANCE].[DataFilters] where [Tablename] = 'FactSAPSalesSponsorRiskSnapshot-GRANTS' and ColumnName = 'Account' )
 and f.CostType = 'GRANTS') 
 group by  f.[DimCustomerProjectKey],cp.[DimProjectKey] ,cp.[DimCustomerKey], f.[Currency], f.[CostType]
                                      
                                      

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


