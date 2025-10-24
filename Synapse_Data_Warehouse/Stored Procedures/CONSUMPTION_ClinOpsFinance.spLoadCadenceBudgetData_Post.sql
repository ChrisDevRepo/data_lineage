CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudgetData_Post] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCadenceBudgetData_Post'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY


truncate table [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post]


INSERT INTO [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData_Post]
           ([CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
           ,[Year]
           ,[Month]
           ,[Project Name]
           ,[Project Currency Code]
           ,[Project Currency Name]
           ,[Service]
           ,[Task Code]
           ,[Task]
           ,[Task Country]
           ,[Part Order Index]
           ,[Segment Order Index]
           ,[Function Code]
           ,[Function]
           ,[Function Country]
           ,[CadenceDepartmentId]
           ,[CadenceDepartmentName]
           ,[PrimaHrDepartmentId]
           ,[PrimaDepartmentName]
           ,[PrimaGlobalCountryId]
           ,[PrimaGlobalCountryName]
           ,[Unit type]
           ,[Currency]
           ,[RecordUpdateType]
           ,[SUM Function Planned Total Cost Adjusted]
           ,[SUM Function Planned Total Hours]
           ,[Function CurrentRate Adjusted]
           ,[SUM Task Planned Total Units]
           ,[SUM Task Approved Total Units]
           ,[SUM Function TimeSheet Actual Total Hours]
           ,[Total SUM Function TimeSheet Actual Total Hours]
           ,[Original Actual Total Hours (Allocated)]
           ,[Earned Value (Budget)]
           ,[Actual Total Hours (Allocated)]
           ,[Earned Value (50% Direct allocation)]
           ,[Non-allocated Earned Value]
           ,[Total Indirect Earned Value (Task)]
           ,[TS hours proportion]
           ,[Actual Cost Proportion]
           ,[Earned Value (Indirect allocation)]
           ,[Earned Value (Total Allocated)]
           ,[Actual Cost of Work Performed]
           ,[Billable Efficiency]
        -- New Version-2 columns
           ,[Earned Value (Direct allocation) Version-2]
           ,[Non-allocated Earned Value Version-2]
           ,[Total Indirect Earned Value (Task) Version-2]
           ,[Actual Cost (Allocated) Proportion]
           ,[Earned Value (Indirect allocation) Version-2]
           ,[Earned Value (Total Allocated) Version-2]
           ,[Billable Efficiency Version-2]

           ,[KEY]
           ,[KEY_wo_Currency]
           ,[Opportunity ID]
           ,[Department]
		   ,[BomDateId]
           ,[Archived Project Ref Id]

           ,[CREATED_AT]
           ,[UPDATED_AT])
SELECT 
	   ju.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
      ,cb.[Year]
      ,cb.[Month]
      ,cb.[Project Name]
      ,cb.[Project Currency Code]
      ,cb.[Project Currency Name]
      ,cb.[Service]
      ,cb.[Task Code]
      ,cb.[Task]
      ,cb.[Task Country]
      ,cb.[Part Order Index]
      ,cb.[Segment Order Index]
      ,cb.[Function Code]
      ,cb.[Function]
      ,cb.[Function Country]
      ,cb.[CadenceDepartmentId]
      ,cb.[CadenceDepartmentName]
      ,cb.[PrimaHrDepartmentId]
      ,cb.[PrimaDepartmentName]
      ,cb.[PrimaGlobalCountryId]
      ,cb.[PrimaGlobalCountryName]
      ,cb.[Unit type]
      ,cb.[Currency]
      ,cb.[RecordUpdateType]
      ,cb.[SUM Function Planned Total Cost Adjusted]
      ,cb.[SUM Function Planned Total Hours]
      ,cb.[Function CurrentRate Adjusted]
      ,cb.[SUM Task Planned Total Units]
      ,cb.[SUM Task Approved Total Units]
      ,cb.[SUM Function TimeSheet Actual Total Hours]
      ,cb.[Total SUM Function TimeSheet Actual Total Hours]
      ,cb.[Original Actual Total Hours (Allocated)]
      ,cb.[Earned Value (Budget)]
      ,cb.[Actual Total Hours (Allocated)]
      ,cb.[Earned Value (50% Direct allocation)]
      ,cb.[Non-allocated Earned Value]
      ,cb.[Total Indirect Earned Value (Task)]
      ,cb.[TS hours proportion]
      ,cb.[Actual Cost Proportion]
      ,cb.[Earned Value (Indirect allocation)]
      ,cb.[Earned Value (Total Allocated)]
      ,cb.[Actual Cost of Work Performed]
      ,cb.[Billable Efficiency]
   -- New Version-2 columns
      ,cb.[Earned Value (Direct allocation) Version-2]
      ,cb.[Non-allocated Earned Value Version-2]
      ,cb.[Total Indirect Earned Value (Task) Version-2]
      ,cb.[Actual Cost (Allocated) Proportion]
      ,cb.[Earned Value (Indirect allocation) Version-2]
      ,cb.[Earned Value (Total Allocated) Version-2]
      ,cb.[Billable Efficiency Version-2]

	  ,Concat(cb.[PrimaGlobalCountryName], cb.[PrimaDepartmentName], cb.[Year], FORMAT(cb.[Month], '00'), cb.[Currency]) as [KEY]
	  ,Concat(cb.[PrimaGlobalCountryName], cb.[PrimaDepartmentName], cb.[Year], FORMAT(cb.[Month], '00')) as [KEY_wo_Currency]
	  ,cb.[Project Name] as [Opportunity ID]
	  ,cb.[CadenceDepartmentName] as [Department]
	  ,[dbo].[udfDateToDateKey](DateFromParts(cb.[Year], cb.[Month], 1)) as [BomDateId]
      ,cb.[Archived Project Ref Id]
      ,cb.[CREATED_AT]
      ,cb.[UPDATED_AT]

from  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData] cb
inner join [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] ju on 
							cb.[PrimaGlobalCountryName] = ju.[PrimaGlobalCountryName]	
						and cb.[PrimaDepartmentName]    = ju.[Department]
						and cb.[Year]				    = ju.[Year]
						and cb.[Month]				    = ju.[Month]
						and cb.[Currency]			    = ju.[Currency]
						and ju.[TableName]				= 'CadenceBudgetData'




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


