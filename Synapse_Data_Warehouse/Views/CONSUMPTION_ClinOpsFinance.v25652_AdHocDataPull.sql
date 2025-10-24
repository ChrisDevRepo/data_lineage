CREATE VIEW [CONSUMPTION_ClinOpsFinance].[v25652_AdHocDataPull]
AS select
	  aa.[Project Code]
	, aa.[Project Name]
	, aa.[Year]
	, aa.[Month]
	, aa.[Department Name]							
	, aa.[Function]			
	, aa.[Currency]
	, sum(aa.[Earned Value])												as [Earned Value]
	, sum(aa.[Actual Cost])													as [Actual Cost]
	, isnull((sum(aa.[Earned Value])/nullif(sum(aa.[Actual Cost]),0)), 0)	as [aCPI]
from
(
	select 
		  ev.[Year]
		, ev.[Month]
		, ev.[Project Name] 	
		, ev.[PRIMA Project Id]												as [Project Code]
		, ev.[Service]									
		, ev.[Task]									
		, ev.[Task Country]							
		, ev.[Function]								
		, ev.[CadenceDepartmentName]										as [Department Name]						
		, ev.[Function Country]
		, ev.[RecordUpdateType]
		, ev.[Currency]
		, COALESCE(ev.[Earned Value (Total Allocated) Version-2], 0.00)		as [Earned Value]
		, COALESCE(ev.[Actual Cost of Work Performed], 0.00)				as [Actual Cost]
	from 
		[CONSUMPTION_ClinOpsFinance].[CadenceBudgetData] ev (nolock)
	where 
			ev.[Currency]				= 'USD'
		and ev.[CadenceDepartmentName]	= 'Process Improvement'
		and ev.[year]					>= 2024
) AA
group by
	  aa.[Project Code]
	, aa.[Project Name]
	, aa.[Year]
	, aa.[Month]
	, aa.[Function]								
	, aa.[Department Name]
	, aa.[Currency]
having 
	   sum(aa.[Earned Value])	<> 0 
	or sum(aa.[Actual Cost])	<> 0;
GO
