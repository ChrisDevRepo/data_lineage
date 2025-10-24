CREATE VIEW [CONSUMPTION_PRIMAREPORTING].[vTimeSheetDurationPerEmployeeAll]
AS

SELECT 
	p.[Project Code] as ProjectCode,
	p.[Project Name] as ProjectName,
	hr.EMPLOYEE_ID as EmployeeId,
	hr.FULL_NAME as EmployeeFullName,
	hr.OFFICE_COUNTRY_NAME OfficeCountryName,
	tsj.Title as [TsTitle],
	hr.Position as [Position],
	hr.DEPARTMENT as [Department],
	tst.TASK_FULL_NAME TaskFullName,
	tst.TASK_NAME as Task,  
	tc.CATEGORY_NAME Category,
	tsc.SUBCATEGORY_NAME SubCategory,
	--iif(tsm.Project_Code <> '0', 'Yes', 'No') as isBillable,
	case when tsm.Project_Code <> '0' then 'Yes' else 'No' end as isBillable,
	--iif(tsm.Project_Code <> '0', tsj.Title, hr.Position) as [Function],
	case when tsm.Project_Code <> '0' then tsj.Title else hr.Position end as [Function],
	sum(tstr.[DURATION]/60.0) as DurationInhours,
	sum(tstr.[DURATION]) as DurationInMinutes,
	cast(tstr.[DATE] as DATE) as TimeSheetTrackerDate
FROM 
	[CONSUMPTION_PRIMA].[PfmTsMaster] tsm
		left join [CONSUMPTION_PRIMA].[PfmTsTasks] tst on (tsm.TASK_ID = tst.RECORD_ID)
		left join [CONSUMPTION_PRIMA].[PfmJobs] tsj on (tsm.[JOB_ID] = tsj.JOB_ID)
		left join [CONSUMPTION_PRIMA].[PfmTsTracker] tstr on (tstr.TS_MASTER_ID = tsm.RECORD_ID)
		left join [CONSUMPTION_PRIMA].[HrEmployeeHistory] 	  hr on hr.[EMPLOYEE_ID] = tsm.EMPLOYEE_ID 
													and cast(tstr.[DATE] as DATE) >= hr.START_DATE
													and cast(tstr.[DATE] as DATE) <= COALESCE(hr.STOP_DATE_CONCEPTION , '9999-12-31')
	    
		left join [CONSUMPTION_PRIMAREPORTING].[Projects] p on tsm.PROJECT_CODE = p.[Project Code]
		left join [dbo].[DimDate] d on d.date = tstr.[DATE]
		left join [CONSUMPTION_PRIMA].[PfmTsCategories] TC on TC.RECORD_ID = tst.CATEGORY_ID
		left join [CONSUMPTION_PRIMA].[PfmTsSubCategories] TSC on TSC.RECORD_ID = tst.SUBCATEGORY_ID
WHERE 
	tsm.START_DATE is not null 
	--and year(tstr.[DATE]) > 201
	--and tsm.RECORD_STATUS <> 3  -- Rejected
	and 
		tstr.DURATION > 0
GROUP BY 
	p.[Project Code],
	p.[Project Name],
	hr.EMPLOYEE_ID,
	hr.FULL_NAME,
	hr.OFFICE_COUNTRY_NAME,
	tsj.Title,
	hr.Position,
	hr.DEPARTMENT,
	tst.TASK_FULL_NAME,
	tst.TASK_NAME,
	tc.CATEGORY_NAME,
	tsc.SUBCATEGORY_NAME,
	--iif(tsm.Project_Code <> '0', 'Yes', 'No'),
	case when tsm.Project_Code <> '0' then 'Yes' else 'No' end,
	--iif(tsm.Project_Code <> '0', tsj.Title, hr.Position),
	case when tsm.Project_Code <> '0' then tsj.Title else hr.Position end,
	cast(tstr.[DATE] as DATE);

GO