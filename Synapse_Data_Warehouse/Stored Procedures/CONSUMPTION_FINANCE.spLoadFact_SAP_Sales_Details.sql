CREATE PROC [CONSUMPTION_FINANCE].[spLoadFact_SAP_Sales_Details] AS

BEGIN

SET NOCOUNT ON


DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadFact_SAP_Sales_Details'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_FINANCE].[' + @ProcShortName + ']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'FinanceDaysToPay'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY


truncate table [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Details]

insert into [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Details]
select 
    cp.[DimCustomerProjectKey],
    dod.DimDateKey as [DimDocumentDateKey],
    dud.DimDateKey as [DimDueDateKey],
    pid.DimDateKey as [DimPaidDateKey],
	s.[Account],
	s.[DocumentNumber],
    s.[Item],
    s.[CostType],
    s.[Currency],
    s.[BusinessArea],
     s.[NetAmountTC],
	s.[PaymentTerms],
    s.[InternalInvoice],
	s.[TotalAmountTC] ,
	s.[ConversionRate],
	s.[CHFTotalAmountTC],
    'spLoadFact_SAP_Sales_Details' as [CreatedBy],
    'spLoadFact_SAP_Sales_Details' as [UpdatedBy],
    getdate() as [CreatedAt],
    getdate() as [UpdatedAt]
	
	
from  [CONSUMPTION_FINANCE].[SAP_Sales_Details_Metrics] s
    left join [CONSUMPTION_FINANCE].[DimProjects] p on p.[ProjectName] = s.[ProjectName]
    left join [CONSUMPTION_FINANCE].[DimCustomers]  c on c.[CustomerName] = s.[CustomerName]
    left join [CONSUMPTION_FINANCE].[DimCustomersProjects] cp on cp.[DimProjectKey] = p.[DimProjectKey] and cp.[DimCustomerKey] = c.[DimCustomerKey]
    left join [dbo].[DimDate] dod on dod.[Date] = s.[DocumentDate]
    left join [dbo].[DimDate] dud on dud.[Date] = s.[DueDate]
    left join [dbo].[DimDate] pid on pid.[Date] = s.[DatePaid]


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