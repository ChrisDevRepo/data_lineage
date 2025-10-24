CREATE VIEW [CONSUMPTION_PRIMAREPORTING].[vRegionEnrollmentPlans]
AS SELECT [Project Code] AS ProjectCode
      ,[Project Name] AS ProjectName
      ,[Region ID] AS RegionID
      ,[Country ID] AS CountryID
      ,[Country] 
      ,[Year] 
      ,[Month Number] AS MonthNumber
      ,[Month] 
      ,[Plan Date] AS PlanDate
      ,[Planned Screened Subjects] AS PlannedScreenedSubjects
      ,[Planned Enrolled Subjects] AS PlannedEnrolledSubjects
      ,[Planned Screened To Date] AS PlannedScreenedToDate
      ,[Planned Enrolled To Date] AS PlannedEnrolledToDate
      ,[Planned Screened Cumulative] AS PlannedScreenedCumulative
      ,[Planned Enrolled Cumulative] AS PlannedEnrolledCumulative
      ,[Src Created Date] AS SrcCreatedDate
      ,[Src Updated Date] AS SrcUpdatedDate
FROM [CONSUMPTION_PRIMAREPORTING].[RegionEnrollmentPlans];
GO