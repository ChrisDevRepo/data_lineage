CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization] AS
BEGIN

SET NOCOUNT ON

BEGIN TRY

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadEmployeeContractUtilization'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0


truncate table [CONSUMPTION_ClinOpsFinance].[EmployeeContractUtilization]

INSERT INTO [CONSUMPTION_ClinOpsFinance].[EmployeeContractUtilization]
    SELECT 
	isnull(t.EmployeeId, a.Employee_Id) as Employee_Id,
    a.[ContractId],
    a.[ContractHistoryStartDate],
    a.[ContractHistoryEndDate],     
	a.[EmployeeFullName] as [FULL_NAME],
	a.OfficeCountryId as [EmployeeCountryId],
    a.[OfficeCountryCode] as [EmployeeCountryCode],
	a.OfficeCountryName as [OFFICE_COUNTRY_NAME],
	a.DepartmentId,
	a.[Department] as [DEPARTMENT],
	a.ContractPositionId as [POSITION_ID],
	a.[Position] as [POSITION],
	a.ContractTimeFrameId as [TIME_FRAME_ID],
	a.[ContractTimeFrameType] as [TIME_FRAME],

  a.[FTE],
	a.[BILLABLE_ID],
	a.[BILLABILITY],
	a.[ContractHoursPerWeek],
	a.[CountryHoursPerWeek],  
	ProjectCode as TsProjectCode,
	CountryId as TsCountryId,
	isnull(cast(t.[TimeSheetTrackerDate] as date), cast(a.DATE as date)) as Date, 
	[TsTitle], 
	[TsPosition], 
	[isBillable], 
	[TitleOrPosition] TitleOrPositionToUse, 
	isnull([DurationInhours], 0) DurationInHours,
	isnull([DurationInMinutes],  0) DurationInMinutes,
	isnull([NonBillableDurationInMinutes], 0) [NonBillableDurationInMinutes],
	isnull([BillableDraftDurationInMinutes], 0) [BillableDraftDurationInMinutes],
	isnull([BillableSubmittedDurationInMinutes], 0) [BillableSubmittedDurationInMinutes],
	isnull([BillableApprovedDurationInMinutes], 0) [BillableApprovedDurationInMinutes],
	isnull([IS_HOLIDAY],  0) IsHoliday,
	isnull([IS_VACATION],  0) IsVacation,
	isnull([IS_SICK_LEAVE],  0) IsSickLeave,
	isnull([IS_DAY_OFF],  0) IsDayOff,
	isnull([IS_BUSINESS_TRIP],  0) IsBusinessTrip,
	isnull([IS_WEEKEND],  0) IsWeekend,
	isnull([IS_DISMISS],  0) IsDismiss,
	[ATTENDANCE] as Attendance,
	isnull([IS_LongTermLeave],  0) IsLongTermLeave,
	a.[ContractClassName],
	a.[ContractClassType]


FROM 
	CONSUMPTION_PRIMA.TsDurationForAllEmployees t
	full outer join [CONSUMPTION_ClinOpsFinance].[HrContractAttendance] a on a.Employee_Id = t.EmployeeId and t.TimeSheetTrackerDate = a.DATE
   



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


