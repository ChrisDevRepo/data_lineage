CREATE PROC [CONSUMPTION_PRIMA].[spLoadHumanResourcesObjects] AS
BEGIN

SET NOCOUNT ON


DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) );
DECLARE @procname               NVARCHAR(128) = '[CONSUMPTION_PRIMA].[spLoadHumanResourcesObjects]';
DECLARE @procid  VARCHAR(100) = ( SELECT OBJECT_ID(@procname));




/*-------------------------------------------------------------------------------*/
BEGIN TRY

-- ************** For Logging And Alerts  ************************
DECLARE @MSG								VARCHAR(max)  = 'Start Time:' ;
														  +  CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) 
														  + ' ' + @ProcName

DECLARE @MSG1								VARCHAR(max)  = '';
DECLARE @MSG2								VARCHAR(max)  = '';
DECLARE @MSG3								VARCHAR(max)  = '';
DECLARE @MSG4								VARCHAR(max)  = '';
DECLARE @MSG5								VARCHAR(max)  = '';
DECLARE @MSG6								VARCHAR(max)  = '';
DECLARE @MSG7								VARCHAR(max)  = '';
DECLARE @MSG8								VARCHAR(max)  = '';
DECLARE @MSG9								VARCHAR(max)  = '';
DECLARE @MSG10								VARCHAR(max)  = '';
DECLARE @MSG11								VARCHAR(max)  = '';
DECLARE @MSG12								VARCHAR(max)  = '';
DECLARE @MSG13								VARCHAR(max)  = '';
DECLARE @MSG14								VARCHAR(max)  = '';
DECLARE @MSG15								VARCHAR(max)  = '';

DECLARE @MSG16								VARCHAR(max)  = '';
DECLARE @MSG17								VARCHAR(max)  = '';
DECLARE @MSG18								VARCHAR(max)  = '';
DECLARE @MSG19								VARCHAR(max)  = '';
DECLARE @MSG20								VARCHAR(max)  = '';




DECLARE @AffectedRecordCount				BIGINT = 0;

DECLARE @AffectedHrContractsRecordCount		BIGINT = 0;
DECLARE @AffectedHrDepartmentsRecordCount	BIGINT = 0;
DECLARE @AffectedHrManningTableRecordCount	BIGINT = 0;
DECLARE @AffectedHrOfficesRecordCount		BIGINT = 0;
DECLARE @AffectedHrPositionsRecordCount		BIGINT = 0;
DECLARE @AffectedHrEmployeeTransfers BIGINT = 0;
DECLARE @AffectedHrEmployeeResignations BIGINT = 0;
DECLARE @AffectedHrEmployeeTrainings BIGINT = 0;


DECLARE @AffectedHrQuizMaster BIGINT = 0;
DECLARE @AffectedHrQuizSessions BIGINT = 0;
DECLARE @AffectedHrTrainingEmployees BIGINT = 0;
DECLARE @AffectedHrTrainingEmployeesTimesheet BIGINT = 0;
DECLARE @AffectedHrTrainingMatrix BIGINT = 0;
DECLARE @AffectedHrTrainingTitles BIGINT = 0;
DECLARE @AffectedHrTutorials BIGINT = 0;


DECLARE @AffectedHrEmployeeLeaveStatistics BIGINT = 0;
DECLARE @AffectedHrEmployeeWorkdays BIGINT = 0;
DECLARE @AffectedHrLeaveTracker BIGINT = 0;
DECLARE @AffectedHrManagement BIGINT = 0;
DECLARE @AffectedHrScormSessions BIGINT = 0;





DECLARE @ProcessId							BIGINT;

DECLARE @RowsInHrContractsTargetBegin		BIGINT;
DECLARE @RowsInHrDepartmentsTargetBegin		BIGINT;
DECLARE @RowsInHrManningTableTargetBegin	BIGINT;
DECLARE @RowsInHrOfficesTargetBegin			BIGINT;
DECLARE @RowsInHrPositionsTargetBegin		BIGINT;
DECLARE @RowsInHrEmployeeTransfersTargetBegin	 BIGINT;
DECLARE @RowsInHrEmployeeResignationsTargetBegin BIGINT;
DECLARE @RowsInHrEmployeeTrainingsTargetBegin	 BIGINT;


DECLARE @RowsInHrQuizMasterTargetBegin	 BIGINT;
DECLARE @RowsInHrQuizSessionsTargetBegin	 BIGINT;
DECLARE @RowsInHrTrainingEmployeesTargetBegin	 BIGINT;
DECLARE @RowsInHrTrainingEmployeesTimesheetTargetBegin	 BIGINT;
DECLARE @RowsInHrTrainingMatrixTargetBegin	 BIGINT;
DECLARE @RowsInHrTrainingTitlesTargetBegin	 BIGINT;
DECLARE @RowsInHrTutorialsTargetBegin	 BIGINT;


DECLARE @RowsInHrEmployeeLeaveStatisticsBegin BIGINT ;
DECLARE @RowsInHrEmployeeWorkdaysBegin BIGINT;
DECLARE @RowsInHrLeaveTrackerBegin BIGINT;
DECLARE @RowsInHrManagementBegin BIGINT;
DECLARE @RowsInHrScormSessionsBegin BIGINT ;




DECLARE @RowsInHrContractsTargetEnd			BIGINT;
DECLARE @RowsInHrDepartmentsTargetEnd		BIGINT;
DECLARE @RowsInHrManningTableTargetEnd		BIGINT;
DECLARE @RowsInHrOfficesTargetEnd			BIGINT;
DECLARE @RowsInHrPositionsTargetEnd			BIGINT;
DECLARE @RowsInHrEmployeeTransfersTargetEnd		BIGINT;
DECLARE @RowsInHrEmployeeResignationsTargetEnd	BIGINT ;
DECLARE @RowsInHrEmployeeTrainingsTargetEnd		BIGINT;


DECLARE @RowsInHrQuizMasterTargetEnd		BIGINT;
DECLARE @RowsInHrQuizSessionsTargetEnd		BIGINT;
DECLARE @RowsInHrTrainingEmployeesTargetEnd		BIGINT;
DECLARE @RowsInHrTrainingEmployeesTimesheetTargetEnd		BIGINT;
DECLARE @RowsInHrTrainingMatrixTargetEnd		BIGINT;
DECLARE @RowsInHrTrainingTitlesTargetEnd		BIGINT;
DECLARE @RowsInHrTutorialsTargetEnd		BIGINT;


DECLARE @RowsInHrEmployeeLeaveStatisticsEnd BIGINT ;
DECLARE @RowsInHrEmployeeWorkdaysEnd BIGINT;
DECLARE @RowsInHrLeaveTrackerEnd BIGINT;
DECLARE @RowsInHrManagementEnd BIGINT;
DECLARE @RowsInHrScormSessionsEnd BIGINT ;

DECLARE @StartTime							DATETIME ;
DECLARE @EndTime							DATETIME ;

SET @RowsInHrContractsTargetBegin			= (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrContracts);
SET @RowsInHrDepartmentsTargetBegin			= (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrDepartments);
SET @RowsInHrManningTableTargetBegin		= (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrManningTable);
SET @RowsInHrOfficesTargetBegin				= (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrOffices);
SET @RowsInHrPositionsTargetBegin			= (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrPositions);

SET @RowsInHrEmployeeTransfersTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrEmployeeTransfers);
SET @RowsInHrEmployeeTrainingsTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainings);
SET @RowsInHrEmployeeResignationsTargetBegin = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrResignations);

SET @RowsInHrQuizMasterTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrQuizMaster);
SET @RowsInHrQuizSessionsTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrQuizSessions);
SET @RowsInHrTrainingEmployeesTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingEmployees);
SET @RowsInHrTrainingEmployeesTimesheetTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingEmployeesTimesheet);
SET @RowsInHrTrainingMatrixTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingMatrix);
SET @RowsInHrTrainingTitlesTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingTitles);
SET @RowsInHrTutorialsTargetBegin	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTutorials);





--SELECT * INTO Prima.HrEmployeeLeaveStatistics FROM [SRVZUGPRM13].[Prima_DWH].[dbo].[HrEmployeeLeaveStatistics]
--SELECT * INTO Prima.HrEmployeeWorkdays FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrEmployeeWorkdays
--SELECT * INTO Prima.HrLeaveTracker FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrLeaveTracker
--SELECT * INTO Prima.HrManagement FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrManagement
--SELECT * INTO Prima.HrScormSessions FROM [SRVZUGPRM13].[Prima_DWH].[dbo].HrScormSessions




SET @RowsInHrEmployeeLeaveStatisticsBegin 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrEmployeeLeaveStatistics) ;
SET @RowsInHrEmployeeWorkdaysBegin 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrEmployeeWorkdays);
SET @RowsInHrLeaveTrackerBegin 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrLeaveTracker);
SET @RowsInHrManagementBegin 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrManagement);
SET @RowsInHrScormSessionsBegin 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrScormSessions) ;




SET @StartTime = GETDATE();

RAISERROR (@MSG ,0,0) 
-- ****************************************************************

IF ((SELECT Count(1) FROM [STAGING_PRIMA].HREmployees) > 0 )
BEGIN

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrContracts]
	INSERT INTO CONSUMPTION_PRIMA.[HrContracts];
	SELECT 
		[CONTRACT_ID], [EMPLOYEE_ID], [CONTRACT_TYPE_ID], [START_DATE], [EXPIRY_DATE], [STOP_DATE], [CONTRACT_CLASS], [TERMINATE_REASON], [PSI_SUPERVISOR_ID], [OFFICE_SUPERVISER_ID], [COMMENT], [POSITION_ID], [TIME_FRAME_ID], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [SECONDARY_POSITION_ID], [HOURS_PER_WEEK], [HIDE_PREVIOUS_LEAVE_RECORDS_FLAG]
	--INTO Prima.[HrContracts]
	FROM 
		[STAGING_PRIMA].[HrContracts]

	-- SET @AffectedHrContractsRecordCount = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrContractsRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrDepartments]
	INSERT INTO CONSUMPTION_PRIMA.[HrDepartments];
	SELECT
		[DEPARTMENT_ID], [DEPARTMENT], [DEPARTMENT_LOC], [DEPARTMENT_SHORT_NAME], [DEPARTMENT_SEQUENCE], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [IS_GROUP], [PARENT_ID], [ROWVERSION], [DIVISION_ID], [IS_OPERATIONS], [DIVISION_CODE], [SKILL_MATRIX_START_DATE]
	--INTO Prima.[HrDepartments]
	FROM
		[STAGING_PRIMA].[HrDepartments]

	-- SET @AffectedHrDepartmentsRecordCount = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrDepartmentsRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrManningTable]
	INSERT INTO CONSUMPTION_PRIMA.[HrManningTable];
	SELECT
		[RECORD_ID], [OFFICE_ID], [OFFICE_CODE], [DEPARTMENT_ID], [POSITION_ID], [START_DATE], [END_DATE], [SUPERVISOR_ID], [POSITION_NUMBER], [BILLABLE_ID], [ON_STAFF_ID], [SUPERVISOR_EMPLOYEE_ID], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_STATUS], [ROWVERSION]
	--INTO Prima.[HrManningTable]
	FROM
		[STAGING_PRIMA].[HrManningTable]

	-- SET @AffectedHrManningTableRecordCount = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrManningTableRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrOffices]
	INSERT INTO CONSUMPTION_PRIMA.[HrOffices];
	SELECT 
		[OFFICE_ID], [OFFICE_CODE], [OFFICE_NAME], [COUNTRY_ID], [COUNTRY_CODE], [CITY_ID], [CITY_CODE], [TIME_ZONE_ID], [OFFICE_HEAD_ID], [LOCATION_TYPE_ID], [ADDRESS], [ZIP_CODE], [PHONE], [FAX], [URL], CONVERT(VarBinary(1), [OFFICE_PICTURE]), [PHONE_LIST_DEPARTMENT], [PHONE_LIST_RUS], [IS_STOCK_EXISTS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [ROWVERSION], [COUNTRY_MANAGER_ID], [STREET], [HOUSE], [LOCAL_COMPANY_NAME], [FOUNDATION_DATE], [LOCATION_ID]
	--INTO Prima.[HrOffices]
	FROM
		[STAGING_PRIMA].[HrOffices]

	-- SET @AffectedHrOfficesRecordCount = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrOfficesRecordCount output

	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrPositions]
	INSERT INTO CONSUMPTION_PRIMA.[HrPositions];
	SELECT
		[POSITION_ID], [POSITION_NAME], [POSITION_NAME_LOC], [IS_GROUP], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_ACTIVE], [ROWVERSION], [POSITION_SHORT_NAME]
	--INTO Prima.[HrPositions]
	FROM
		[STAGING_PRIMA].[HrPositions]

		-- SET @AffectedHrPositionsRecordCount = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrPositionsRecordCount output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrEmployeeTransfers]
	INSERT INTO CONSUMPTION_PRIMA.[HrEmployeeTransfers];
	SELECT
		[RECORD_ID], [EMPLOYEE_ID], [OLD_DEPARTMENT_ID], [OLD_POSITION_ID], [NEW_DEPARTMENT_ID], [NEW_POSITION_ID], [NEW_LINE_MANAGER_ID], [TRANSFER_DATE], [EDUCATION_REQUIREMENTS_CONDITION_ID], [TRAINING_COMPLETED_CONDITION_ID], [ADDITIONAL_REQUIREMENTS_CONDITION_ID], [INTERVIEW_PASSED_CONDITION_ID], [JOB_PERFORMANCE_ACCEPTANCE_FLAG], [QUALIFICATION_REQUIREMENTS_FLAG], [EDUCATION_REQUIREMENTS_COMMENTS], [TRAINING_COMPLETED_COMMENTS], [ADDITIONAL_REQUIREMENTS_COMMENTS], [INTERVIEW_PASSED_COMMENTS], [JOB_PERFORMANCE_ACCEPTANCE_COMMENTS], [DOCUMENT_OBJECT_ID], [COMMENTS], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [JOB_REQUISITION_ID]
	--INTO Prima.[HrEmployeeTransfers]
	FROM
		[STAGING_PRIMA].[HrEmployeeTransfers]

		-- SET @AffectedHrEmployeeTransfers = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeTransfers output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrResignations]
	INSERT INTO CONSUMPTION_PRIMA.[HrResignations];
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [CANCELLATION_TYPE_ID], [CANCELLATION_REASON_ID], [COMMENTS], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [CONTRACT_END_DATE], [ACTUAL_END_DATE]	
	--INTO Prima.[HrResignations]
	FROM
		[STAGING_PRIMA].[HrResignations]

		-- SET @AffectedHrEmployeeResignations = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeResignations output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainings]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainings];
	SELECT
	[TRAINING_ID], [TRAINING_PROJECT_CODE], [TRAINING_TEMPLATE_ID], [TRAINING_ORIGINATOR_ID], [TRAINING_TITLE], [TRAINING_DATE], [TRAINING_DURATION], [TRAINING_GROUP_ID], [TRAINING_PROVIDER_TYPE_ID], [TRAINING_PROVIDER_NAME], [TRAINING_FORM_ID], [TRAINING_TEST_TYPE_ID], [TRAINING_PRIMACY_ID], [TRAINING_MODALITY_ID], [TRAINING_QSD_TYPE_ID], [TRAINING_QSD_ID], [TRAINING_QSD_NAME], [TRAINING_SCOPE], [TRAINING_ENCLOSURES], [TRAINING_STATUS_ID], [TRAINING_HARDCOPY_DATE], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [PARENT_TRAINING_ID], [APPROVED_BY], [APPROVED_AT], [DOCUMENTUM_OBJECT_ID], [SIGNED], [SIGNED_AT], [OUTCOME_ID], [SITE_EVENT_ID], [REJECT_REASON], [TRAINING_TYPE_ID], [TRAINING_DELAY_REASON_ID], [TRAINING_EXT_INSTRUCTORS], [FIELD_TRAINING_OBJECTIVE_ID], [SCORM_RESULT], [SCORM_ID], [FIELD_TRAINING_TEMPLATE_ID], [FIELD_TRAINING_VISIT_TYPES_LIST], [FIELD_TRAINING_AUTHORIZATION_DATE], [TRAINING_ORIGINATOR_USER_ID], [IS_DOCUMENT_REVIEWED], [REVIEWED_DOCUMENT_NAME], [REVIEWED_DOCUMENT_VERSION], [NQSD_VERSION_ID]
	--INTO Prima.[HrTrainings]
	FROM
		[STAGING_PRIMA].[HrTrainingsNew]

		-- SET @AffectedHrEmployeeTrainings = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeTrainings output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrQuizMaster]
	INSERT INTO CONSUMPTION_PRIMA.[HrQuizMaster];
	SELECT
	[RECORD_ID], [ORIGINAL_QUIZ_ID], [QUIZ_NAME], [VERSION_NUMBER], [VERSION_DATE], [QUESTIONS_TYPE_ID], [QUESTIONS_RANDOM_NUMBER], [PASS_SCORE], [PARENT_MASTER_ID], [PURPOSE_TEXT], [INTRODUCTION_TEXT], [COMPLETION_TIME], [DEVELOPER_ID], [GROUP_ID], [SKILL_ID], [SCORE_CALCULATION_TYPE_ID], [RECORD_STATUS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [ASSIGNMENT_TYPE_ID], [REPORT_TYPE_ID], [PROJECT_CODE]
	--INTO Prima.[HrQuizMaster]
	FROM
		[STAGING_PRIMA].HrQuizMaster

		-- SET @AffectedHrQuizMaster = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrQuizMaster output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrQuizSessions]
	INSERT INTO CONSUMPTION_PRIMA.[HrQuizSessions];
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [QUIZ_MASTER_ID], [SESSION_NUMBER], [START_DATE], [END_DATE], [REASON_ID], [FINAL_SCORE], [PASS_SCORE], [PASSED_FLAG], [REVIEWED_BY], [REVIEWED_AT], [DOCUMENTUM_OBJECT_ID], [RECORD_STATUS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [ELAPSED_SECONDS], [RANDOMIZED_QUESTIONS_LIST]
	--INTO Prima.[HrQuizSessions]
	FROM
		[STAGING_PRIMA].HrQuizSessions

		-- SET @AffectedHrQuizSessions = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrQuizSessions output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingEmployees]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingEmployees];
	SELECT
	[TRAINING_EMPLOYEE_ID], [EMPLOYEE_ID], [TRAINING_ID], [TRAINING_EMPLOYEE_TYPE_ID], [USER_ID]
	--INTO Prima.[HrTrainingEmployees]
	FROM
		[STAGING_PRIMA].HrTrainingEmployees

		-- SET @AffectedHrTrainingEmployees = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingEmployees output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingEmployeesTimesheet]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingEmployeesTimesheet];
	SELECT
	[RecID], [TrainingID], [TrainingDate], [TrainerID], [TraineeID], [AddDate]
	--INTO Prima.[HrTrainingEmployeesTimesheet]
	FROM
		[STAGING_PRIMA].HrTrainingEmployeesTimesheet

		-- SET @AffectedHrTrainingEmployeesTimesheet = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingEmployeesTimesheet output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingMatrix]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingMatrix];
	SELECT
	[RECORD_ID], [QSD_MASTER_ID], [DEPARTMENT_ID], [POSITIONS_LIST], [COUNTRIES_LIST], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_STATUS]
	--INTO Prima.[HrTrainingMatrix]
	FROM
		[STAGING_PRIMA].HrTrainingMatrix

		-- SET @AffectedHrTrainingMatrix = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingMatrix output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTrainingTitles]
	INSERT INTO CONSUMPTION_PRIMA.[HrTrainingTitles];
	SELECT
	[RECORD_ID], [TRAINING_TITLE], [CATEGORY_ID], [VERSION_DATE], [VERSION_LABEL], [OBJECT_ID], [SCOPE], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [TRAINING_FORM_ID], [PROVIDER_TYPE_ID], [PROVIDER_NAME], [QSD_TYPE_ID], [QSD_MASTER_ID], [TRAINING_TITLE_TYPE_ID], [DEPARTMENTS_LIST], [SKILL_ID], [TRAINING_QSD_NAME], [PARENT_TITLE_ID], [ROOT_ID]
	--INTO Prima.[HrTrainingTitles]
	FROM
		[STAGING_PRIMA].HrTrainingTitles

		-- SET @AffectedHrTrainingTitles = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTrainingTitles output



	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrTutorials]
	INSERT INTO CONSUMPTION_PRIMA.[HrTutorials];
	SELECT
	[RECORD_ID], [TYPE_ID], [TITLE], [ORIGINATOR], [SCOPE], [TEST_TYPE_ID], [QSD_ID], [SECTION_ID], [DURATION], [PUBLISH_DATE], [PARAMS], [PARENT_ID], [RECORD_STATUS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [TESTERS_LIST], [ROOT_ID], [IS_INDUCTION], [COURSE_TYPE_ID], [QUIZ_TYPE_ID]
	--INTO Prima.[HrTutorials]
	FROM
		[STAGING_PRIMA].HrTutorials

		-- SET @AffectedHrTutorials = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrTutorials output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrEmployeeLeaveStatistics]
	INSERT INTO CONSUMPTION_PRIMA.[HrEmployeeLeaveStatistics];
	SELECT
	[EMPLOYEE_ID], [YEAR], [APPROVED_LEAVE_ENTITLEMENT], [CARRIED_OVER], [PREVIOUS_CARRIED_OVER], [LEAVE_DAYS], [LEFT_LEAVE_DAYS], [SICK_DAYS]
	--INTO Prima.[HrEmployeeLeaveStatistics]
	FROM
		[STAGING_PRIMA].HrEmployeeLeaveStatistics

		-- SET @AffectedHrEmployeeLeaveStatistics = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeLeaveStatistics output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrEmployeeWorkdays]
	INSERT INTO CONSUMPTION_PRIMA.[HrEmployeeWorkdays];
	SELECT
	[RECORD_ID], [YEAR], [MONTH], [EMPLOYEE_ID], [WORKDAYS], [LEAVEDAYS], [MAX_WORKDAYS], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT]
	--INTO Prima.[HrEmployeeWorkdays]
	FROM
		[STAGING_PRIMA].HrEmployeeWorkdays

		-- SET @AffectedHrEmployeeWorkdays = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrEmployeeWorkdays output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrLeaveTracker]
	INSERT INTO CONSUMPTION_PRIMA.[HrLeaveTracker];
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [START_DATE], [END_DATE], [LEAVE_TYPE_ID], [LEAVE_TYPE_CUSTOM], [APPROVER_LIST], [APPROVED_DATE], [EMPLOYEES_TO_NOTIFY_LIST], [OLD_VACATION_ID], [COMMENTS], [CREATED_AT], [CREATED_BY], [UPDATED_AT], [UPDATED_BY], [RECORD_STATUS], [IS_HALF_DAY], [LEAVE_YEAR], [ENTERED_DURATION], [CALENDAR_DURATION], [WORK_DURATION], [CALCULATION_TYPE_ID], [DURATION], [IS_UNPAID], [HARDCOPY_AGREEMENT_DATE], [CALCULATION_SICK_TYPE_ID], [CITY_ID], [COUNTRY_ID]
	--INTO Prima.[HrLeaveTracker]
	FROM
		[STAGING_PRIMA].HrLeaveTracker

		-- SET @AffectedHrLeaveTracker = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrLeaveTracker output




	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrManagement]
	INSERT INTO CONSUMPTION_PRIMA.[HrManagement];
	SELECT
	[RECORD_ID], [MANAGER_ID], [COUNTRY_ID], [DEPARTMENT_ID], [CREATED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [RECORD_STATUS], [IS_DESIGNEE]
	--INTO Prima.[HrManagement]
	FROM
		[STAGING_PRIMA].HrManagement

		-- SET @AffectedHrManagement = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrManagement output


	TRUNCATE TABLE CONSUMPTION_PRIMA.[HrScormSessions]
	INSERT INTO CONSUMPTION_PRIMA.[HrScormSessions];
	SELECT
	[RECORD_ID], [EMPLOYEE_ID], [COURSE_ID], [START_TIME], [END_TIME], [MIN_SCORE], [MAX_SCORE], [SCORE], [PASSING_SCORE], [PT_SCORE], [PT_MAX], [RESULT], [SESSION], [QUIZ_SESSION], [DURATION]
	--INTO Prima.[HrScormSessions]
	FROM
		[STAGING_PRIMA].HrScormSessions

		-- SET @AffectedHrScormSessions = @@ROWCOUNT;
	EXEC  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrScormSessions output





END



SET @RowsInHrContractsTargetEnd			= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrContracts);
SET @RowsInHrDepartmentsTargetEnd		= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrDepartments);
SET @RowsInHrManningTableTargetEnd		= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrManningTable);
SET @RowsInHrOfficesTargetEnd			= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrOffices);
SET @RowsInHrPositionsTargetEnd			= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrPositions);
SET @RowsInHrEmployeeTransfersTargetEnd		= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrEmployeeTransfers);
SET @RowsInHrEmployeeResignationsTargetEnd	= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrResignations);
SET @RowsInHrEmployeeTrainingsTargetEnd		= (SELECT COUNT(*) FROM CONSUMPTION_PRIMA.HrTrainings);


SET @RowsInHrQuizMasterTargetEnd	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrQuizMaster);
SET @RowsInHrQuizSessionsTargetEnd	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrQuizSessions);
SET @RowsInHrTrainingEmployeesTargetEnd	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingEmployees);
SET @RowsInHrTrainingEmployeesTimesheetTargetEnd	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingEmployeesTimesheet);
SET @RowsInHrTrainingMatrixTargetEnd	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingMatrix);
SET @RowsInHrTrainingTitlesTargetEnd	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTrainingTitles);
SET @RowsInHrTutorialsTargetEnd	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrTutorials);

SET @RowsInHrEmployeeLeaveStatisticsEnd 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrEmployeeLeaveStatistics) ;
SET @RowsInHrEmployeeWorkdaysEnd 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrEmployeeWorkdays);
SET @RowsInHrLeaveTrackerEnd 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrLeaveTracker);
SET @RowsInHrManagementEnd 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrManagement);
SET @RowsInHrScormSessionsEnd 	 = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrScormSessions) ;








SET @EndTime                = GETDATE();
SET	@MSG1                    = @MSG + ' (CONSUMPTION_PRIMA.HrContracts): New Rows Processed = ' ;
							+ CAST((@RowsInHrContractsTargetEnd - @RowsInHrContractsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG2                    = @MSG + ' (CONSUMPTION_PRIMA.HrDepartments): New Rows Processed = ' ;
							+ CAST((@RowsInHrDepartmentsTargetEnd - @RowsInHrDepartmentsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG3                    = @MSG + ' (CONSUMPTION_PRIMA.HrManningTable): New Rows Processed = ' ;
							+ CAST((@RowsInHrManningTableTargetEnd - @RowsInHrManningTableTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG4                    = @MSG + ' (CONSUMPTION_PRIMA.HrOffices): New Rows Processed = ' ;
							+ CAST((@RowsInHrOfficesTargetEnd - @RowsInHrOfficesTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG5                    = @MSG + ' (CONSUMPTION_PRIMA.HrPositions): New Rows Processed = ' ;
							+ CAST((@RowsInHrPositionsTargetEnd - @RowsInHrPositionsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'


SET	@MSG6                    = @MSG + ' (CONSUMPTION_PRIMA.HrEmployeeTransfters): New Rows Processed = ' ;
							+ CAST((@RowsInHrEmployeeTransfersTargetEnd - @RowsInHrEmployeeTransfersTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'


SET	@MSG7                    = @MSG + ' (CONSUMPTION_PRIMA.HrEmployeeResignations): New Rows Processed = ' ;
							+ CAST((@RowsInHrEmployeeResignationsTargetEnd - @RowsInHrEmployeeResignationsTargetBegin ) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG8                    = @MSG + ' (CONSUMPTION_PRIMA.HrEmployeeTraninings): New Rows Processed = ' ;
							+ CAST((@RowsInHrEmployeeTrainingsTargetEnd - @RowsInHrEmployeeTrainingsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG9                    = @MSG + ' (CONSUMPTION_PRIMA.HrQuizMaster): New Rows Processed = ' ;
							+ CAST((@RowsInHrQuizMasterTargetEnd - @RowsInHrQuizMasterTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG10                    = @MSG + ' (CONSUMPTION_PRIMA.HrQuizSessions): New Rows Processed = ' ;
							+ CAST((@RowsInHrQuizSessionsTargetEnd - @RowsInHrQuizSessionsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG11                    = @MSG + ' (CONSUMPTION_PRIMA.HrTrainingEmployeess): New Rows Processed = ' ;
							+ CAST((@RowsInHrTrainingEmployeesTargetEnd - @RowsInHrTrainingEmployeesTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG12                    = @MSG + ' (CONSUMPTION_PRIMA.HrTrainingEmployeesTimesheets): New Rows Processed = ' ;
							+ CAST((@RowsInHrTrainingEmployeesTimesheetTargetEnd - @RowsInHrTrainingEmployeesTimesheetTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG13                    = @MSG + ' (CONSUMPTION_PRIMA.HrTrainingMatrix): New Rows Processed = ' ;
							+ CAST((@RowsInHrTrainingMatrixTargetEnd - @RowsInHrTrainingMatrixTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG14                    = @MSG + ' (CONSUMPTION_PRIMA.HrTrainingTitles): New Rows Processed = ' ;
							+ CAST((@RowsInHrTrainingTitlesTargetEnd - @RowsInHrTrainingTitlesTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG15                    = @MSG + ' (CONSUMPTION_PRIMA.HrTutorials): New Rows Processed = ' ;
							+ CAST((@RowsInHrTutorialsTargetEnd - @RowsInHrTutorialsTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'



SET	@MSG16                    = @MSG + ' (CONSUMPTION_PRIMA.HrEmployeeLeaveStatistics): New Rows Processed = ' ;
							+ CAST((@RowsInHrEmployeeLeaveStatisticsEnd - @RowsInHrEmployeeLeaveStatisticsBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG17                    = @MSG + ' (CONSUMPTION_PRIMA.HrEmployeeWorkdays): New Rows Processed = ' ;
							+ CAST((@RowsInHrEmployeeWorkdaysEnd - @RowsInHrEmployeeWorkdaysBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG18                    = @MSG + ' (CONSUMPTION_PRIMA.HrLeaveTracker): New Rows Processed = ' ;
							+ CAST((@RowsInHrLeaveTrackerEnd - @RowsInHrLeaveTrackerBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG19                    = @MSG + ' (CONSUMPTION_PRIMA.HrManagement): New Rows Processed = ' ;
							+ CAST((@RowsInHrManagementEnd - @RowsInHrManagementBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

SET	@MSG20                    = @MSG + ' (CONSUMPTION_PRIMA.HrScormSessions): New Rows Processed = ' ;
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

DECLARE @ErrorNum int, @ErrorLine int  ,@ErrorSeverity int ,@ErrorState int;
DECLARE @ErrorProcedure nvarchar(126) ,@ErrorMessage nvarchar(2048) ;


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

	SET	@MSG	= @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') ;
	EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
	RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 


END CATCH
 

END
