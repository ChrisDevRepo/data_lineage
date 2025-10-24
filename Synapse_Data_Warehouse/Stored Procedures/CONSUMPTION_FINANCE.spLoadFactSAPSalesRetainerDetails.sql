CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesRetainerDetails] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadFactSAPSalesRetainerDetails]'
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

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactSAPSalesRetainerDetails])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[FactSAPSalesRetainerDetails];

begin transaction

insert into [CONSUMPTION_FINANCE].[FactSAPSalesRetainerDetails]
(
       [DimCustomerProjectKey]
      ,[DimCustomerKey]
      ,[DimProjectKey]
      ,[DimDocumentDateKey]
      ,[DimDueDateKey]
      ,[DimPaidDateKey]
      ,[Currency]
      ,[NetAmountTC]
      ,[CreatedBy]
      ,[UpdatedBy]
      ,[CreatedAt]
      ,[UpdatedAt]
)
select
dcp.DimCustomerProjectKey,
dc.DimCustomerKey,
dp.DimProjectKey,
dd1.DimDateKey as [DimDocumentDateKey],
dd2.DimDateKey as [DimDueDateKey],
dd3.DimDateKey as [DimPaidDateKey],
r.Currency,
r.NetAmountTC,
'[CONSUMPTION_FINANCE].[spLoadFactSAPSalesRetainerDetails]' as CreatedBy,
'[CONSUMPTION_FINANCE].[spLoadFactSAPSalesRetainerDetails]' as UpdatedBy,
getdate() as CreatedAt,
getdate() as UpdatedAt
from [CONSUMPTION_FINANCE].[SAP_Sales_Retainer_Details_Metrics] r
left join [CONSUMPTION_FINANCE].[DimCustomers] dc
on r.CustomerName = dc.CustomerName
left join [CONSUMPTION_FINANCE].[DimProjects] dp
on r.ProjectName = dp.ProjectName
left join [CONSUMPTION_FINANCE].[DimCustomersProjects] dcp
on dc.DimCustomerKey = dcp.DimCustomerKey and dp.DimProjectKey = dcp.DimProjectKey
left join [dbo].[DimDate] dd1
on r.DocumentDate = dd1.Date
left join [dbo].[DimDate] dd2
on r.DueDate = dd2.Date
left join [dbo].[DimDate] dd3
on r.DatePaid = dd3.Date;

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[FactSAPSalesRetainerDetails])
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