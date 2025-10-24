CREATE PROC [CONSUMPTION_PRIMAREPORTING_PARALLEL].[spGetEventDates] AS

BEGIN
SET NOCOUNT ON

-- declare @project_Dates table ([Project_Code] int, [Handed_Over_To_Operations_Date] datetimeoffset);


If object_id('tempdb.dbo.#project_Dates') is not null DROP TABLE #project_Dates
CREATE TABLE #project_Dates
(
[Project_Code] int,
[Handed_Over_To_Operations_Date] datetimeoffset
)

insert into #project_Dates
	select 
		p.[Project_Code], 
		min (handed_over_to_operations.[Actual Date]) as Handed_Over_To_Operations_Date
	from [CONSUMPTION_PRIMA_PARALLEL].Sites p 
	LEFT JOIN [CONSUMPTION_PRIMAREPORTING_PARALLEL].[projectevents] handed_over_to_operations on (handed_over_to_operations.[Project Code] = p.[Project_Code] and handed_over_to_operations.[event] =  'Handed over to Operations (Start date)')
group by p.[Project_Code]


-- declare @dates table (	project_code int,

If object_id('tempdb.dbo.#dates') is not null DROP TABLE #dates
CREATE TABLE #dates
(
project_code int,
						site_id int, 
						CDA_Sent_Date datetimeoffset, 
						CDA_Executed_Date datetimeoffset, 
						FQ_SIQ_Sent_Date datetimeoffset, 
						FQ_SIQ_Received_Date datetimeoffset,
						Selection_Visit_Date datetimeoffset,
						Site_Selected_Date datetimeoffset,
						Initiation_Visit_Date datetimeoffset,
						Site_Activation_Event_Date datetimeoffset,
						Screening_Date datetimeoffset,
						Randomization_Date datetimeoffset,
						Enrollment_Date datetimeoffset
					 );
insert into #dates
	select Sites.project_code,
	Sites.site_id, 
	cda_sent_date, 
	cda_executed_date,
	fq_siq_sent_date,
	fiq_received_date,
	selection_visit_date,
	site_selected_date,
	initiation_visit_date,
	site_activation_event_date,
	screening_date,
	randomization_date,
	enrollment_date

	from [CONSUMPTION_PRIMA_PARALLEL].Sites
	Left Join
	(
		select SiteEvents.[Site Id], min ([Actual Date]) as cda_sent_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where [Event Name] = 'CDA Sent'
		group by SiteEvents.[Site Id]
	) cda_sent on cda_sent.[Site Id] = Sites.Site_Id
	Left Join
	(
		select SiteEvents.[Site Id], max ([Actual Date]) as cda_executed_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where [Event Name] = 'Executed CDA received'
		group by SiteEvents.[Site Id]
	) cda_received on cda_received.[Site Id] = Sites.Site_Id
	Left Join
	(
		select SiteEvents.[Site Id], min ([Actual Date]) as fq_siq_sent_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where [Event Name] = 'FQ/SIQ sent'
		group by SiteEvents.[Site Id]
	) fiq_sent on fiq_sent.[Site Id] = Sites.Site_Id
	Left Join
	(
		select SiteEvents.[Site Id], max ([Actual Date]) as fiq_received_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where [Event Name] = 'FQ/SIQ received'
		group by SiteEvents.[Site Id]
	) fiq_received on fiq_received.[Site Id] = Sites.Site_Id
	Left Join
	(
		select SiteEvents.[Site Id], max ([Forecast Date]) as selection_visit_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where [Event Name] = 'Selection Visit'
		group by SiteEvents.[Site Id]
	) selection_visit on selection_visit.[Site Id] = Sites.Site_Id
	Left Join
	(
		select SiteEvents.[Site Id], max ([Actual Date]) as site_selected_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where 
			[event name] in ('Selected by Sponsor/another CRO', 'Site selection waiver', 'Clinical site approval by Sponsor/CRO')
		group by SiteEvents.[Site Id]
	) site_selected on site_selected.[Site Id] = Sites.Site_Id
	Left Join
	(
		select SiteEvents.[Site Id], max ([Actual Date]) as initiation_visit_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where [Event Name] = 'Initiation Visit'
		group by SiteEvents.[Site Id]
	) initiation_visit on initiation_visit.[Site Id] = Sites.Site_Id
	Left Join
	(
		select SiteEvents.[Site Id], max ([Actual Date]) as site_activation_event_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SiteEvents where [Event Name] = 'Site activation'
		group by SiteEvents.[Site Id]
	) site_activation on site_activation.[Site Id] = Sites.Site_Id
	LEFT JOIN 
	(
		select SubjectEvents.[Site Id], min ([Actual Date]) as screening_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].SubjectEvents where [Event Type Name Conception] =  'screening'
		group by SubjectEvents.[Site Id]
	) screening on screening.[Site Id] = Sites.Site_Id

	Left join
	(
		select  [site id], min ([actual date]) as randomization_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].subjectevents where [randomization flag] = 1 
		group by [site id]
	) randomization on randomization.[site id] = Sites.Site_Id
	Left join
	(
		select  [site id], min ([actual date]) as enrollment_date from [CONSUMPTION_PRIMAREPORTING_PARALLEL].subjectevents where [enrollment flag] = 1 group by [site id]
	) enrollment on enrollment.[site id] = Sites.Site_Id


	
select	
	s.project_code, 
	s.site_id, 
	p.Handed_Over_To_Operations_Date,
	datediff (day, p.Handed_Over_To_Operations_Date, d.CDA_Sent_Date) as Number_Days_Site_ID_Project_Preparations,
	d.cda_executed_date, 
	d.CDA_Sent_Date,
	datediff (day, d.CDA_Sent_Date, d.cda_executed_date) as Number_Days_CDA_Timelines,
	d.fq_siq_sent_date,
	d.fq_siq_received_date,
	datediff (day, d.fq_siq_sent_date, d.fq_siq_received_date) as Number_Days_SIQ_Timelines,
	datediff (day, d.CDA_Sent_Date, d.fq_siq_received_date) as Number_Days_Site_Identified_Timelines_Combine_CDASIQ_Timelines,
	d.Selection_Visit_Date,
	datediff (day, d.CDA_Sent_Date, d.Selection_Visit_Date) as Number_Days_SSV_Scheduled_Timelines,
	d.Site_Selected_Date,
	datediff (day, CDA_Sent_Date, d.Site_Selected_Date) as Number_Days_Site_Selected_Timelines,
	d.Initiation_Visit_Date,
	datediff (day, CDA_Sent_Date, d.Initiation_Visit_Date) as Number_Days_Initiation_Visit_Timelines,
	d.Site_Activation_Event_Date,
	datediff (day, CDA_Sent_Date, d.Site_Activation_Event_Date) as Number_Days_Site_Activation_Timelines,
	d.Screening_Date,
	datediff (day, d.Site_Activation_Event_Date, d.Screening_Date) as Number_Days_First_Patient_Screened_Timelines,
	d.Randomization_Date,
	d.Enrollment_Date,
	-- datediff (day, Site_Activation_Event_Date, (select min (first_patient_enrollment_date) from (values (d.Randomization_Date), (d.Enrollment_Date)) as value (first_patient_enrollment_date))) as Number_Days_First_Patient_Enrolled_Timelines,
	datediff (day, Site_Activation_Event_Date, (select LEAST (d.Randomization_Date, d.Enrollment_Date) as Number_Days_First_Patient_Enrolled_Timelines)),
	datediff (day, d.Site_Selected_Date, Site_Activation_Event_Date) as Number_Days_Selection_To_Activation

	from [CONSUMPTION_PRIMA_PARALLEL].Sites s
	left join #dates d on d.[site_id] = s.site_id
	left join #project_Dates p on p.[Project_Code] = convert (int, s.[Project_Code])

	order by convert (int, s.[project_code]), s.site_id


END
