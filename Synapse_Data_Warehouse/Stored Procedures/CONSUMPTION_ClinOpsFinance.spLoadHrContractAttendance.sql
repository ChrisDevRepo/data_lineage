CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadHrContractAttendance] AS
BEGIN

SET NOCOUNT ON

BEGIN TRY

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadHrContractAttendance'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0


SET DATEFIRST 1  -- This is important. Setting Monday first day = Sat, Sun weekends

DECLARE @Employeeid int =  -1  
DECLARE @DaysInPast int = 2200

DECLARE  
	@FROM_DATE DATE = (SELECT getdate()-@daysInPast) , 
	@END_DATE DATE = getdate()- 1


   truncate table [CONSUMPTION_ClinOpsFinance].[HrContractAttendance]

   insert into [CONSUMPTION_ClinOpsFinance].[HrContractAttendance]
   select BB.*
        , CASE WHEN ISNULL(BB.IS_HOLIDAY,0) + 
                    ISNULL(BB.IS_VACATION,0) + 
                    ISNULL(BB.IS_SICK_LEAVE,0) + 
                    ISNULL(BB.IS_DAY_OFF,0) + 
                    ISNULL(BB.IS_WEEKEND,0) + 
                    ISNULL(BB.IS_LongTermLeave,0) = 0 
                THEN COALESCE(BB.ContractHoursPerWeek, BB.CountryHoursPerWeek,0.0)/5 
                ELSE 0.0 
            END AS [Hours Expected, Daily]

        , [dbo].[udfDateToDateKey](BB.[Date (Utilization)]) as [UtilizationDateId]

    --into [CONSUMPTION_ClinOpsFinance].[HrContractAttendance]
    from 
        (
            select 
                AA.[Employee_Id]
                ,AA.[ContractId]
                ,AA.[ContractHistoryStartDate]
                ,AA.[ContractHistoryEndDate]
                ,AA.[EmployeeFullName]
                ,AA.[OfficeCountryId]
                ,AA.[OfficeCountryCode]
                ,AA.[OfficeCountryName]
                ,AA.[DATE]
                ,AA.[Date (Utilization)]
                ,AA.[Country]
                ,AA.[PrimaGlobalCountryName]
                ,AA.[DepartmentId]
                ,AA.[Department]
                ,AA.[ContractPositionId]
                ,AA.[Position]
                ,AA.[ContractClassName]
                ,AA.[ContractClassType]
                ,AA.[BILLABLE_ID]
                ,AA.[BILLABILITY]

                ,sum(AA.[IS_HOLIDAY])         as [IS_HOLIDAY]
                ,sum(AA.[IS_VACATION])        as [IS_VACATION]
                ,sum(AA.[IS_SICK_LEAVE])      as [IS_SICK_LEAVE]
                ,sum(AA.[IS_DAY_OFF])         as [IS_DAY_OFF]
                ,sum(AA.[IS_BUSINESS_TRIP])   as [IS_BUSINESS_TRIP]
                ,sum(AA.[IS_WEEKEND])         as [IS_WEEKEND]
                ,sum(AA.[IS_DISMISS])         as [IS_DISMISS]
                ,max(AA.[ATTENDANCE])         as [ATTENDANCE]
                ,sum(AA.[IS_LongTermLeave])   as [IS_LongTermLeave]

                ,AA.[FTE]

                ,AA.[ContractTimeFrameId]
                ,AA.[ContractTimeFrameType]
                ,AA.[ContractHoursPerWeek]
                ,AA.[CountryHoursPerWeek]
                ,AA.[ContractRank]

            FROM
            (
                select  distinct 
                        e.[EmployeeId] as [Employee_Id]
                    , e.[ContractId]
                    , CONVERT(DATE, e.[ContractHistoryStartDate], 101) as [ContractHistoryStartDate]
                    , CONVERT(DATE, e.[ContractHistoryEndDate], 101) as [ContractHistoryEndDate]                    
                    , e.[EmployeeFullName]
                    , e.[OfficeCountryId]
                    , e.[OfficeCountryCode]
                    , e.[OfficeCountryName]
                    , d.[DATE]

                    ,CONVERT(DATE, [dbo].[udfDateToBomDate](
                                                            case when DATENAME(WEEKDAY, d.[Date]) = 'Monday'		then DATEADD(Day, 4,  d.[Date]) 
                                                                when DATENAME(WEEKDAY, d.[Date]) = 'Tuesday'		then DATEADD(Day, 3,  d.[Date]) 
                                                                when DATENAME(WEEKDAY, d.[Date]) = 'Wednesday'	    then DATEADD(Day, 2,  d.[Date]) 
                                                                when DATENAME(WEEKDAY, d.[Date]) = 'Thursday'	    then DATEADD(Day, 1,  d.[Date]) 
                                                                when DATENAME(WEEKDAY, d.[Date]) = 'Friday'		then DATEADD(Day, 0,  d.[Date]) 
                                                                when DATENAME(WEEKDAY, d.[Date]) = 'Saturday'	    then DATEADD(Day, -1, d.[Date]) 
                                                                when DATENAME(WEEKDAY, d.[Date]) = 'Sunday'		then DATEADD(Day, -2, d.[Date]) 
                                                            end	
                                            ), 101)	AS [Date (Utilization)]	    

                    , e.[OfficeCountryName] AS [Country]
                    , gc.[Country_name] as [PrimaGlobalCountryName]

                    , e.[DepartmentId]
                    , e.[DepartmentName] as [Department]

                    , e.[ContractPositionId]
                    , e.[PositionName] as [Position]

                    , e.[ContractClassName]
                    , e.[ContractClassType]

                    , e.[BillableId] as [BILLABLE_ID]

                    ,Replace(
                                Replace(Trim(e.[BILLABILITY])
                                        , 'Not billable', 'Non-billable')
                            , 'Billable (85-100%)', 'Fully Billable (85-100%)') as [BILLABILITY]

                    , case when h.RECORD_ID is not null then 1 else 0 end as [IS_HOLIDAY]
                    , case when lV.LEAVE_TYPE_ID = 0 and lv.RECORD_STATUS = 4 then 1 else 0 end as [IS_VACATION]
                    , case when lV.LEAVE_TYPE_ID = 2 then case when lv.CALENDAR_DURATION <=1 then lv.CALENDAR_DURATION else 1 end else 0 end as [IS_SICK_LEAVE] 
                    , case when lV.LEAVE_TYPE_ID not in (0, 2) then 1 else 0 end as [IS_DAY_OFF]
                    , case when coalesce(lB.RECORD_ID,site_v.RECORD_ID) is not null then 1 else 0 end as [IS_BUSINESS_TRIP] 
                    , case when datepart(weekday, d.DATE) in (6, 7) then 1 else 0 end as [IS_WEEKEND] 
                    , case when d.DATE >= e.ContractHistoryStartDate and d.DATE<= e.ContractHistoryEndDate then 0 else 1 end as [IS_DISMISS] 
                    , case when datepart(weekday, d.DATE) in (6, 7) then 'weekend, ' else  '' end + case when h.RECORD_ID is not null then 'holiday, ' else '' end
                            + case when lV.RECORD_ID is not null then 'leave, ' else '' end
                            + case when coalesce(site_v.RECORD_ID, lB.RECORD_ID) is not null then 'business trip' else '' end as [ATTENDANCE] 
                    , case when m.MATERNITY_ID is not null then 1 else 0 end as [IS_LongTermLeave]

                    , e.[FTE]

                    , e.[ContractTimeFrameId]
                    , e.[ContractTimeFrameName] as [ContractTimeFrameType]
                    , e.[ContractHoursPerWeek]
                    , e.[CountryHoursPerWeek]
                    , RANK() OVER (PARTITION BY e.EmployeeId, d.Date ORDER BY EmployeeId, d.Date, e.ContractHistoryStartDate DESC) as [ContractRank]

                from    [CONSUMPTION_PrimaReporting].[HrEmployeeContractHistory] e
                    cross apply (select DATE from dbo.DimDate d where DATE between @FROM_DATE and @END_DATE) d
                    left join CONSUMPTION_Prima.HrLeaveTracker lV on d.DATE between lV.START_DATE and lV.END_DATE  and lV.EMPLOYEE_ID = e.EmployeeId
                                    and lV.LEAVE_TYPE_ID not in (4, 6, 10, 11)	--all except Work at home (4), Business trips (6), Leave entitlement (10), Cary over (11)
                    left join CONSUMPTION_Prima.HrLeaveTracker lB on d.DATE between lB.START_DATE and lB.END_DATE and lB.EMPLOYEE_ID = e.EmployeeId and lB.LEAVE_TYPE_ID = 6
                    left join CONSUMPTION_Prima.GlobalHolidays h on d.DATE = h.HOLIDAY_DATE and h.COUNTRY_ID = e.OfficeCountryId
                    left join CONSUMPTION_Prima.GlobalCountries gc on gc.COUNTRY_CODE	= e.OfficeCountryCode
                    left join CONSUMPTION_Prima.HrMaternity m on d.DATE between m.START_DATE and m.END_DATE  and m.EMPLOYEE_ID = e.EmployeeId
                    left join (
                                select 
                                    e.Employee_Id,
                                    SITE_EVENT_ID as RECORD_ID,
                                    isnull(ACTUAL_DATE, PLANNED_DATE) as START_DATE,
                                    se.VISIT_END_DATE as END_DATE
                                from   CONSUMPTION_Prima.SiteEvents se
                                    join   CONSUMPTION_Prima.Sites s on s.SITE_ID = se.SITE_ID
                                    join   CONSUMPTION_PrimaReporting.Projects p on p.[project code] = s.project_code --remove test projects
                                    join   CONSUMPTION_Prima.HrEmployees e on PRIMARY_MONITOR_ID = e.Employee_Id or ',' + se.ATTENDEES + ',' like '%,' + cast(e.Employee_Id as varchar) + ',%'
                            ) site_v on site_v.Employee_Id = e.EmployeeId and d.DATE between site_v.START_DATE and site_v.END_DATE 
                where 
                    d.DATE >= e.ContractHistoryStartDate and 
                    d.DATE < e.ContractHistoryEndDate 
            ) AA
            group BY
                AA.[Employee_Id]
                ,AA.[ContractId]
                ,AA.[ContractHistoryStartDate]
                ,AA.[ContractHistoryEndDate]                
                ,AA.[EmployeeFullName]
                ,AA.[OfficeCountryId]
                ,AA.[OfficeCountryCode]
                ,AA.[OfficeCountryName]
                ,AA.[DATE]
                ,AA.[Date (Utilization)]
                ,AA.[Country]
                ,AA.[PrimaGlobalCountryName]
                ,AA.[DepartmentId]
                ,AA.[Department]
                ,AA.[ContractPositionId]
                ,AA.[Position]
                ,AA.[ContractClassName]
                ,AA.[ContractClassType]
                ,AA.[BILLABLE_ID]
                ,AA.[BILLABILITY]
                ,AA.[FTE]
                ,AA.[ContractTimeFrameId]
                ,AA.[ContractTimeFrameType]
                ,AA.[ContractHoursPerWeek]
                ,AA.[CountryHoursPerWeek]
                ,AA.[ContractRank]

                )  BB
    where BB.ContractRank = 1 




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
