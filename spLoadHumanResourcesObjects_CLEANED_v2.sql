CREATE PROC [CONSUMPTION_PRIMA].[spLoadHumanResourcesObjects] AS
BEGIN




-- DECLARE removed
-- DECLARE removed
-- DECLARE removed




/*-------------------------------------------------------------------------------*/
BEGIN TRY

-- ************** For Logging And Alerts  ************************
-- DECLARE removed
														  +  CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) 
														  + ' ' + @ProcName

-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed

-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed




-- DECLARE removed

-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed


-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed


-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed





-- DECLARE removed

-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed


-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed


-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed




-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed


-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed


-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed
-- DECLARE removed

-- DECLARE removed
-- DECLARE removed








--SELECT * INTO Prima.HrEmployeeLeaveStatistics FROM [SRVZUGPRM13].[Prima_DWH].[dbo].[HrEmployeeLeaveStatistics]
--SELECT * INTO Prima.HrEmployeeWorkdays FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrEmployeeWorkdays
--SELECT * INTO Prima.HrLeaveTracker FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrLeaveTracker
--SELECT * INTO Prima.HrManagement FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrManagement
--SELECT * INTO Prima.HrScormSessions FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrScormSessions









RAISERROR (@MSG ,0,0) 
-- ****************************************************************

IF ((SELECT Count(1) FROM [STAGING_PRIMA].HREmployees) > 0 )
BEGIN

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrContracts]
	INSERT INTO CONSUMPTION_PRIMA.[HrContracts]
	SELECT 
		[CONTRACT_ID], [EMPLOYEE_ID], [CONTRACT_TYPE_ID], [START_DATE], [EXPIRY_DATE], [STOP_DATE], [CONTRACT_CLASS], [TERMINATE_REASON], [PSI_SUPERVISOR_ID], [OFFICE_SUPERVISER_ID], [COMMENT], [POSITION_ID], [TIME_FRAME_ID], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [SECONDARY_POSITION_ID], [HOURS_PER_WEEK], [HIDE_PREVIOUS_LEAVE_RECORDS_FLAG]
	--INTO Prima.[HrContracts]
	FROM 
		[STAGING_PRIMA].[HrContracts]

	-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrContractsRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrDepartments]
	INSERT INTO CONSUMPTION_PRIMA.[HrDepartments]
	SELECT
		[DEPARTMENT_ID], [DEPARTMENT], [DEPARTMENT_LOC], [DEPARTMENT_SHORT_NAME], [DEPARTMENT_SEQUENCE], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [IS_GROUP], [PARENT_ID], [ROWVERSION], [DIVISION_ID], [IS_OPERATIONS], [DIVISION_CODE], [SKILL_MATRIX_START_DATE]
	--INTO Prima.[HrDepartments]
	FROM
		[STAGING_PRIMA].[HrDepartments]

	-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrDepartmentsRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrManningTable]
	INSERT INTO CONSUMPTION_PRIMA.[HrManningTable]
	SELECT
		[RECORD_ID], [OFFICE_ID], [OFFICE_CODE], [DEPARTMENT_ID], [POSITION_ID], [START_DATE], [END_DATE], [SUPERVISOR_ID], [POSITION_NUMBER], [BILLABLE_ID], [ON_STAFF_ID], [SUPERVISOR_EMPLOYEE_ID], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_STATUS], [ROWVERSION]
	--INTO Prima.[HrManningTable]
	FROM
		[STAGING_PRIMA].[HrManningTable]

	-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrManningTableRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrOffices]
	INSERT INTO CONSUMPTION_PRIMA.[HrOffices]
	SELECT 
		[OFFICE_ID], [OFFICE_CODE], [OFFICE_NAME], [COUNTRY_ID], [COUNTRY_CODE], [CITY_ID], [CITY_CODE], [TIME_ZONE_ID], [OFFICE_HEAD_ID], [LOCATION_TYPE_ID], [ADDRESS], [ZIP_CODE], [PHONE], [FAX], [URL], CONVERT(VarBinary(1), [OFFICE_PICTURE]), [PHONE_LIST_DEPARTMENT], [PHONE_LIST_RUS], [IS_STOCK_EXISTS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [ROWVERSION], [COUNTRY_MANAGER_ID], [STREET], [HOUSE], [LOCAL_COMPANY_NAME], [FOUNDATION_DATE], [LOCATION_ID]
	--INTO Prima.[HrOffices]
	FROM
		[STAGING_PRIMA].[HrOffices]

	-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrOfficesRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrPositions]
	INSERT INTO CONSUMPTION_PRIMA.[HrPositions]
	SELECT
		[POSITION_ID], [POSITION_NAME], [POSITION_NAME_LOC], [IS_GROUP], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [ROWVERSION], [POSITION_SHORT_NAME]
	--INTO Prima.[HrPositions]
	FROM
		[STAGING_PRIMA].[HrPositions]

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrPositionsRecordCount output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrEmployeeTransfers]
	INSERT INTO CONSUMPTION_PRIMA.[HrEmployeeTransfers]
	SELECT
		[RECORD_ID], [EMPLOYEE_ID], [OLD_DEPARTMENT_ID], [OLD_POSITION_ID], [NEW_DEPARTMENT_ID], [NEW_POSITION_ID], [NEW_LINE_MANAGER_ID], [TRANSFER_DATE], [EDUCATION_REQUIREMENTS_CONDITION_ID], [TRAINING_COMPLETED_CONDITION_ID], [ADDITIONAL_REQUIREMENTS_CONDITION_ID], [INTERVIEW_PASSED_CONDITION_ID], [JOB_PERFORMANCE_ACCEPTANCE_FLAG], [QUALIFICATION_REQUIREMENTS_FLAG], [EDUCATION_REQUIREMENTS_COMMENTS], [TRAINING_COMPLETED_COMMENTS], [ADDITIONAL_REQUIREMENTS_COMMENTS], [INTERVIEW_PASSED_COMMENTS], [JOB_PERFORMANCE_ACCEPTANCE_COMMENTS], [DOCUMENT_OBJECT_ID], [COMMENTS], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [JOB_REQUISITION_ID]
	--INTO Prima.[HrEmployeeTransfers]
	FROM
		[STAGING_PRIMA].[HrEmployeeTransfers]

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeTransfers output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrResignations]
	INSERT INTO CONSUMPTION_PRIMA.[HrResignations]
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [CANCELLATION_TYPE_ID], [CANCELLATION_REASON_ID], [COMMENTS], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [CONTRACT_END_DATE], [ACTUAL_END_DATE]	
	--INTO Prima.[HrResignations]
	FROM
		[STAGING_PRIMA].[HrResignations]

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeResignations output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainings]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainings]
	SELECT
	[TRAINING_ID], [TRAINING_PROJECT_CODE], [TRAINING_TEMPLATE_ID], [TRAINING_ORIGINATOR_ID], [TRAINING_TITLE], [TRAINING_DATE], [TRAINING_DURATION], [TRAINING_GROUP_ID], [TRAINING_PROVIDER_TYPE_ID], [TRAINING_PROVIDER_NAME], [TRAINING_FORM_ID], [TRAINING_TEST_TYPE_ID], [TRAINING_PRIMACY_ID], [TRAINING_MODALITY_ID], [TRAINING_QSD_TYPE_ID], [TRAINING_QSD_ID], [TRAINING_QSD_NAME], [TRAINING_SCOPE], [TRAINING_ENCLOSURES], [TRAINING_STATUS_ID], [TRAINING_HARDCOPY_DATE], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [PARENT_TRAINING_ID], [APPROVED_BY], [APPROVED_AT], [DOCUMENTUM_OBJECT_ID], [SIGNED], [SIGNED_AT], [OUTCOME_ID], [SITE_EVENT_ID], [REJECT_REASON], [TRAINING_TYPE_ID], [TRAINING_DELAY_REASON_ID], [TRAINING_EXT_INSTRUCTORS], [FIELD_TRAINING_OBJECTIVE_ID], [SCORM_RESULT], [SCORM_ID], [FIELD_TRAINING_TEMPLATE_ID], [FIELD_TRAINING_VISIT_TYPES_LIST], [FIELD_TRAINING_AUTHORIZATION_DATE], [TRAINING_ORIGINATOR_USER_ID], [IS_DOCUMENT_REVIEWED], [REVIEWED_DOCUMENT_NAME], [REVIEWED_DOCUMENT_VERSION], [NQSD_VERSION_ID]
	--INTO Prima.[HrTrainings]
	FROM
		[STAGING_PRIMA].[HrTrainingsNew]

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeTrainings output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrQuizMaster]
	INSERT INTO CONSUMPTION_PRIMA.[HrQuizMaster]
	SELECT
	[RECORD_ID], [ORIGINAL_QUIZ_ID], [QUIZ_NAME], [VERSION_NUMBER], [VERSION_DATE], [QUESTIONS_TYPE_ID], [QUESTIONS_RANDOM_NUMBER], [PASS_SCORE], [PARENT_MASTER_ID], [PURPOSE_TEXT], [INTRODUCTION_TEXT], [COMPLETION_TIME], [DEVELOPER_ID], [GROUP_ID], [SKILL_ID], [SCORE_CALCULATION_TYPE_ID], [RECORD_STATUS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [ASSIGNMENT_TYPE_ID], [REPORT_TYPE_ID], [PROJECT_CODE]
	--INTO Prima.[HrQuizMaster]
	FROM
		[STAGING_PRIMA].HrQuizMaster

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrQuizMaster output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrQuizSessions]
	INSERT INTO CONSUMPTION_PRIMA.[HrQuizSessions]
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [QUIZ_MASTER_ID], [SESSION_NUMBER], [START_DATE], [END_DATE], [REASON_ID], [FINAL_SCORE], [PASS_SCORE], [PASSED_FLAG], [REVIEWED_BY], [REVIEWED_AT], [DOCUMENTUM_OBJECT_ID], [RECORD_STATUS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [ELAPSED_SECONDS], [RANDOMIZED_QUESTIONS_LIST]
	--INTO Prima.[HrQuizSessions]
	FROM
		[STAGING_PRIMA].HrQuizSessions

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrQuizSessions output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingEmployees]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingEmployees]
	SELECT
	[TRAINING_EMPLOYEE_ID], [EMPLOYEE_ID], [TRAINING_ID], [TRAINING_EMPLOYEE_TYPE_ID], [USER_ID]
	--INTO Prima.[HrTrainingEmployees]
	FROM
		[STAGING_PRIMA].HrTrainingEmployees

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingEmployees output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingEmployeesTimesheet]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingEmployeesTimesheet]
	SELECT
	[RecID], [TrainingID], [TrainingDate], [TrainerID], [TraineeID], [AddDate]
	--INTO Prima.[HrTrainingEmployeesTimesheet]
	FROM
		[STAGING_PRIMA].HrTrainingEmployeesTimesheet

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingEmployeesTimesheet output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingMatrix]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingMatrix]
	SELECT
	[RECORD_ID], [QSD_MASTER_ID], [DEPARTMENT_ID], [POSITIONS_LIST], [COUNTRIES_LIST], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_STATUS]
	--INTO Prima.[HrTrainingMatrix]
	FROM
		[STAGING_PRIMA].HrTrainingMatrix

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingMatrix output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingTitles]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingTitles]
	SELECT
	[RECORD_ID], [TRAINING_TITLE], [CATEGORY_ID], [VERSION_DATE], [VERSION_LABEL], [OBJECT_ID], [SCOPE], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [TRAINING_FORM_ID], [PROVIDER_TYPE_ID], [PROVIDER_NAME], [QSD_TYPE_ID], [QSD_MASTER_ID], [TRAINING_TITLE_TYPE_ID], [DEPARTMENTS_LIST], [SKILL_ID], [TRAINING_QSD_NAME], [PARENT_TITLE_ID], [ROOT_ID]
	--INTO Prima.[HrTrainingTitles]
	FROM
		[STAGING_PRIMA].HrTrainingTitles

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingTitles output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTutorials]
	INSERT INTO CONSUMPTION_PRIMA.[HrTutorials]
	SELECT
	[RECORD_ID], [TYPE_ID], [TITLE], [ORIGINATOR], [SCOPE], [TEST_TYPE_ID], [QSD_ID], [SECTION_ID], [DURATION], [PUBLISH_DATE], [PARAMS], [PARENT_ID], [RECORD_STATUS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [TESTERS_LIST], [ROOT_ID], [IS_INDUCTION], [COURSE_TYPE_ID], [QUIZ_TYPE_ID]
	--INTO Prima.[HrTutorials]
	FROM
		[STAGING_PRIMA].HrTutorials

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTutorials output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrEmployeeLeaveStatistics]
	INSERT INTO CONSUMPTION_PRIMA.[HrEmployeeLeaveStatistics]
	SELECT
	[EMPLOYEE_ID], [YEAR], [APPROVED_LEAVE_ENTITLEMENT], [CARRIED_OVER], [PREVIOUS_CARRIED_OVER], [LEAVE_DAYS], [LEFT_LEAVE_DAYS], [SICK_DAYS]
	--INTO Prima.[HrEmployeeLeaveStatistics]
	FROM
		[STAGING_PRIMA].HrEmployeeLeaveStatistics

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeLeaveStatistics output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrEmployeeWorkdays]
	INSERT INTO CONSUMPTION_PRIMA.[HrEmployeeWorkdays]
	SELECT
	[RECORD_ID], [YEAR], [MONTH], [EMPLOYEE_ID], [WORKDAYS], [LEAVEDAYS], [MAX_WORKDAYS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT]
	--INTO Prima.[HrEmployeeWorkdays]
	FROM
		[STAGING_PRIMA].HrEmployeeWorkdays

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeWorkdays output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrLeaveTracker]
	INSERT INTO CONSUMPTION_PRIMA.[HrLeaveTracker]
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [START_DATE], [END_DATE], [LEAVE_TYPE_ID], [LEAVE_TYPE_CUSTOM], [APPROVER_LIST], [APPROVED_DATE], [EMPLOYEES_TO_NOTIFY_LIST], [OLD_VACATION_ID], [COMMENTS], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [IS_HALF_DAY], [LEAVE_YEAR], [ENTERED_DURATION], [CALENDAR_DURATION], [WORK_DURATION], [CALCULATION_TYPE_ID], [DURATION], [IS_UNPAID], [HARDCOPY_AGREEMENT_DATE], [CALCULATION_SICK_TYPE_ID], [CITY_ID], [COUNTRY_ID]
	--INTO Prima.[HrLeaveTracker]
	FROM
		[STAGING_PRIMA].HrLeaveTracker

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrLeaveTracker output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrManagement]
	INSERT INTO CONSUMPTION_PRIMA.[HrManagement]
	SELECT
	[RECORD_ID], [MANAGER_ID], [COUNTRY_ID], [DEPARTMENT_ID], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_STATUS], [IS_DESIGNEE]
	--INTO Prima.[HrManagement]
	FROM
		[STAGING_PRIMA].HrManagement

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrManagement output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrScormSessions]
	INSERT INTO CONSUMPTION_PRIMA.[HrScormSessions]
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [COURSE_ID], [START_TIME], [END_TIME], [MIN_SCORE], [MAX_SCORE], [SCORE], [PASSING_SCORE], [PT_SCORE], [PT_MAX], [RESULT], [SESSION], [QUIZ_SESSION], [DURATION]
	--INTO Prima.[HrScormSessions]
	FROM
		[STAGING_PRIMA].HrScormSessions

		-- 	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrScormSessions output





END














							+ CAST((@RowsInHrContractsTargetEnd - @RowsInHrContractsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrDepartmentsTargetEnd - @RowsInHrDepartmentsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrManningTableTargetEnd - @RowsInHrManningTableTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrOfficesTargetEnd - @RowsInHrOfficesTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrPositionsTargetEnd - @RowsInHrPositionsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'


							+ CAST((@RowsInHrEmployeeTransfersTargetEnd - @RowsInHrEmployeeTransfersTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'


							+ CAST((@RowsInHrEmployeeResignationsTargetEnd - @RowsInHrEmployeeResignationsTargetBegin ) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrEmployeeTrainingsTargetEnd - @RowsInHrEmployeeTrainingsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrQuizMasterTargetEnd - @RowsInHrQuizMasterTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrQuizSessionsTargetEnd - @RowsInHrQuizSessionsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrTrainingEmployeesTargetEnd - @RowsInHrTrainingEmployeesTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrTrainingEmployeesTimesheetTargetEnd - @RowsInHrTrainingEmployeesTimesheetTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrTrainingMatrixTargetEnd - @RowsInHrTrainingMatrixTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrTrainingTitlesTargetEnd - @RowsInHrTrainingTitlesTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrTutorialsTargetEnd - @RowsInHrTutorialsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'



							+ CAST((@RowsInHrEmployeeLeaveStatisticsEnd - @RowsInHrEmployeeLeaveStatisticsBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrEmployeeWorkdaysEnd - @RowsInHrEmployeeWorkdaysBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrLeaveTrackerEnd - @RowsInHrLeaveTrackerBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrManagementEnd - @RowsInHrManagementBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

							+ CAST((@RowsInHrScormSessionsEnd - @RowsInHrScormSessionsBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'













EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG1, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG1 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG2, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG2 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG3, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG3 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG4, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG4 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG5, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG5 ,0,0) 


EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName =@servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG6, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG6 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG7, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG7 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG8, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG8 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG9, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG9 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG10, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG10 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG11, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG11 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG12, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG12 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG13, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG13 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG14, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG14 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG15, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG15 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG15, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG16 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG15, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG17 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG15, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG18 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG15, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG19 ,0,0) 

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG15, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG20 ,0,0) 









END TRY
/*----------------------------------------------------------------------*/
BEGIN CATCH

-- DECLARE removed
-- DECLARE removed


    -- store all the error information for logging the error
    SELECT @ErrorNum       = ERROR_NUMBER() 
          ,@ErrorLine      = 0
          ,@ErrorSeverity  = ERROR_SEVERITY()
          ,@ErrorState     = ERROR_STATE()
          ,@ErrorProcedure = ERROR_PROCEDURE()
          ,@ErrorMessage   = ERROR_MESSAGE()

    -- if there is a pending transation roll it back
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION

		EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
	RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 


END CATCH
 

END
