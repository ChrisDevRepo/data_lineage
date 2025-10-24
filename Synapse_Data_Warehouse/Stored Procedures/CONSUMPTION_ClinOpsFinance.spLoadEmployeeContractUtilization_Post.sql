CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadEmployeeContractUtilization_Post] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadEmployeeContractUtilization_Post'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY


truncate table [CONSUMPTION_ClinOpsFinance].[EmployeeContractUtilization_Post]


INSERT INTO [CONSUMPTION_ClinOpsFinance].[EmployeeContractUtilization_Post]
	(
       [CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
      ,[EMPLOYEE_ID]
      ,[ContractId]
      ,[ContractHistoryStartDate]
      ,[ContractHistoryEndDate]      
      ,[FULL_NAME]
      ,[EmployeeCountryId]
      ,[OFFICE_COUNTRY_NAME]
      ,[DepartmentId]
      ,[DEPARTMENT]
      ,[POSITION_ID]
      ,[POSITION]
      ,[TIME_FRAME]
      ,[FTE]
      ,[BILLABLE_ID]
      ,[BILLABILITY]
      ,[ContractHoursPerWeek]
      ,[CountryHoursPerWeek]
      ,[TsProjectCode]
      ,[TsCountryId]
      ,[TsTitle]
      ,[TsPosition]
      ,[isBillable]
      ,[TitleOrPositionToUse]
      ,[DurationInHours]
      ,[DurationInMinutes]
      ,[NonBillableDurationInMinutes]
      ,[BillableDraftDurationInMinutes]
      ,[BillableSubmittedDurationInMinutes]
      ,[BillableApprovedDurationInMinutes]
      ,[IsHoliday]
      ,[IsVacation]
      ,[IsSickLeave]
      ,[IsDayOff]
      ,[IsBusinessTrip]
      ,[IsWeekend]
      ,[IsDismiss]
      ,[Attendance]
      ,[IsLongTermLeave]
      ,[Date]
      ,[Year]
      ,[Month]
      ,[StartofMonth_Date]
      ,[Date (Utilization)]
      ,[Currency]
      ,[IsAbsent]
      ,[Hours Billed]
      ,[CadenceDepartmentName]
      ,[ContractClassName]
      ,[ContractClassType]
      ,[Filter]
      ,[BomDateId]
      ,[UtilizationDateId]
      ,[Fridays]
      ,[Hours Expected, Daily]
	)

select AA.*
		,[dbo].[udfDateToDateKey](AA.[StartofMonth_Date]) as [BomDateId]
		,[dbo].[udfDateToDateKey](AA.[Date (Utilization)]) as [UtilizationDateId]
        ,d.[NumberOfFridays] as [Fridays]
		,Case When AA.[IsWeekend]=1 then 0 
			  Else Case When AA.[ContractHoursPerWeek] is null then AA.[CountryHoursPerWeek]/5*(1 - AA.[IsAbsent])
						Else AA.[ContractHoursPerWeek]/5*(1 - AA.[IsAbsent])
					End
		  End as [Hours Expected, Daily]
From																																																  
	(
		SELECT 
			   ju.[CadenceBudget_LaborCost_PrimaUtilization_JuncKey]
			  ,eu.[EMPLOYEE_ID]
              ,eu.[ContractId]
			  ,CONVERT(DATE, eu.[ContractHistoryStartDate], 101) as [ContractHistoryStartDate]
			  ,CONVERT(DATE, eu.[ContractHistoryEndDate], 101)  as [ContractHistoryEndDate]              
			  ,eu.[FULL_NAME]
			  ,eu.[EmployeeCountryId]
			  ,Trim(eu.[OFFICE_COUNTRY_NAME]) as [OFFICE_COUNTRY_NAME]
			  ,eu.[DepartmentId]
			  ,Trim(eu.[DEPARTMENT]) as [DEPARTMENT]
			  ,eu.[POSITION_ID]
			  ,Trim(eu.[POSITION]) as [POSITION]
			  ,eu.[TIME_FRAME]
			  ,eu.[FTE]
			  ,eu.[BILLABLE_ID]
              ,eu.[BILLABILITY]
			  ,eu.[ContractHoursPerWeek]
			  ,eu.[CountryHoursPerWeek]
			  ,eu.[TsProjectCode]
			  ,eu.[TsCountryId]				              
			  ,eu.[TsTitle]
			  ,eu.[TsPosition]
			  ,eu.[isBillable]
			  ,eu.[TitleOrPositionToUse]
			  ,eu.[DurationInHours]
			  ,eu.[DurationInMinutes]
			  ,eu.[NonBillableDurationInMinutes]
			  ,eu.[BillableDraftDurationInMinutes]
			  ,eu.[BillableSubmittedDurationInMinutes]
			  ,eu.[BillableApprovedDurationInMinutes]
			  ,eu.[IsHoliday]
			  ,eu.[IsVacation]
			  ,eu.[IsSickLeave]
			  ,eu.[IsDayOff]
			  ,eu.[IsBusinessTrip]
			  ,eu.[IsWeekend]
			  ,eu.[IsDismiss]
			  ,eu.[Attendance]
			  ,eu.[IsLongTermLeave]
			  ,eu.[Date]
			  ,Year(eu.[Date]) as [Year]
			  ,Month(eu.[Date]) as [Month]              
              ,CONVERT(DATE, [dbo].[udfDateToBomDate](eu.[Date]), 101) as [StartofMonth_Date]
              ,CONVERT(DATE, [dbo].[udfDateToBomDate](
      	      	              case when DATENAME(WEEKDAY, eu.[Date]) = 'Monday'		then DATEADD(Day, 4,  eu.[Date]) 
      	      	              	   when DATENAME(WEEKDAY, eu.[Date]) = 'Tuesday'	then DATEADD(Day, 3,  eu.[Date]) 
      	      	              	   when DATENAME(WEEKDAY, eu.[Date]) = 'Wednesday'	then DATEADD(Day, 2,  eu.[Date]) 
      	      	              	   when DATENAME(WEEKDAY, eu.[Date]) = 'Thursday'	then DATEADD(Day, 1,  eu.[Date]) 
      	      	              	   when DATENAME(WEEKDAY, eu.[Date]) = 'Friday'		then DATEADD(Day, 0,  eu.[Date]) 
      	      	              	   when DATENAME(WEEKDAY, eu.[Date]) = 'Saturday'	then DATEADD(Day, -1, eu.[Date]) 
      	      	              	   when DATENAME(WEEKDAY, eu.[Date]) = 'Sunday'		then DATEADD(Day, -2, eu.[Date]) 
      	      	              end	
      	                ), 101) AS [Date (Utilization)]	

			  ,'JUNC' as [Currency]	
			  ,case when eu.[IsWeekend] = 1 
                    then 0 
                    else (SELECT MAX(Holiday)
				            FROM (Select eu.[IsHoliday] Union All 
                                  Select eu.[IsVacation] Union All 
                                  Select eu.[IsSickLeave] Union All 
                                  Select eu.[IsDayOff] Union All 
                                  Select eu.[IsLongTermLeave]) AS AllHolidays(Holiday)) 
               end as [IsAbsent]
			  ,case when [isBillable]='Yes' then (Coalesce(eu.[BillableDraftDurationInMinutes], 0.0) + Coalesce(eu.[BillableSubmittedDurationInMinutes], 0.0) + Coalesce(eu.[BillableApprovedDurationInMinutes], 0.0))/60 else 0.0 end as [Hours Billed]
			  ,dp.[CadenceDepartmentName] as [CadenceDepartmentName]
			  ,eu.[ContractClassName] 
			  ,eu.[ContractClassType] 

			  ,Case when (eu.[ContractHistoryStartDate] <= eu.[Date] and eu.[Date] <= eu.[ContractHistoryEndDate]) then 'True' else 'False' end as [Filter]


		FROM [CONSUMPTION_ClinOpsFinance].[EmployeeContractUtilization] eu
			left join [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc] ju on 
										Coalesce(eu.[OFFICE_COUNTRY_NAME], '')	= Coalesce(ju.[PrimaGlobalCountryName], '')	
									and Coalesce(eu.[DEPARTMENT]		, '')	= Coalesce(ju.[Department]			  , '')
									and Year(eu.[Date])							= ju.[Year]
									and Month(eu.[Date])						= ju.[Month]
									and ju.[Currency]							= 'JUNC'
									and ju.[TableName]							= 'EmployeeUtilization'
			left join (select distinct [CadenceDepartmentName], [PrimaDepartmentName] 
						from [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]) dp on eu.[DEPARTMENT] = dp.[PrimaDepartmentName]
		Where 
			(eu.[ContractHistoryStartDate] <= eu.[Date] and eu.[Date] < eu.[ContractHistoryEndDate])
	) AA
	left join (select DateFromParts(Year([Date]), Month([Date]), 1) as [FirstDayOFTheMonth]
					, Count(1) as [NumberOfFridays]
				from [dbo].[dimDate] where [DayName] = 'Friday' 
				group by DateFromParts(Year([Date]), Month([Date]), 1)
			   ) d on d.FirstDayOFTheMonth = AA.[Date (Utilization)]



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