CREATE VIEW [CONSUMPTION_PRIMAREPORTING].[vHrCRASupervisors]
AS select *  
from  
	( 
		select
			 e.FULL_NAME as [Employee Full Name]
			,e.OFFICE_COUNTRY_NAME as [Employee Location]
			,e.FULL_DEPARTMENT as [Department Name]
			,e.POSITION_SHORT as [Position Name (Short)]
			,e.EMPLOYEE_ID as [Employee ID]
			,coalesce(mts.EMPLOYEE_ID, MTE.EMPLOYEE_ID, HC.EMPLOYEE_ID) as [Line Manager ID]
			,isnull(oa.SUPERVISOR_FULL_NAME_MT, HC.FULL_NAME) as [Line Manager Name]
			,e.CONTRACT_CLASS_NAME as [Contract Class Name]
			,e.PHONE as [Phone Number]
			,e.PHONE_EXTENTION as [Phone Extention]
			,e.MOBILE_PHONE as [Mobile Phone Number]
			,e.EMAIL as [Email Address]
			,e.RECORD_STATUS_CONCEPTION as [Record Status Conception]
			,e.[START_DATE] as [Start Date]
			,e.[EXPIRY_DATE] as [Expiry Date]
		from        
			[CONSUMPTION_PRIMA].[HrEmployees] e
			inner join  [CONSUMPTION_PRIMA].[HrManningTable] MT on MT.RECORD_ID = e.MANNING_TABLE_ID
			left join   (   
							select   _MT.RECORD_ID
		                       , min(_E.EMPLOYEE_ID) as EMPLOYEE_ID
		                       , min(_E.FULL_NAME) as FULL_NAME
				            from     [CONSUMPTION_PRIMA].[HrManningTable] _MT
				            join     [CONSUMPTION_PRIMA].[HrEmployees] _E on _E.MANNING_TABLE_ID = _MT.RECORD_ID
				                                            and _E.RECORD_STATUS = 2
				            group by _MT.RECORD_ID
				            having   count(_E.EMPLOYEE_ID) = 1
						) mts on mts.RECORD_ID = MT.SUPERVISOR_ID
			left join   [CONSUMPTION_PRIMA].[HrEmployees] MTE on MTE.EMPLOYEE_ID = MT.SUPERVISOR_EMPLOYEE_ID and MTE.RECORD_STATUS = 2
			outer apply (
							--select iif(mts.EMPLOYEE_ID is not null, mts.FULL_NAME, MTE.FULL_NAME) as SUPERVISOR_FULL_NAME_MT
							select case when mts.EMPLOYEE_ID is not null then mts.FULL_NAME else MTE.FULL_NAME end as SUPERVISOR_FULL_NAME_MT
						) oa 
			left join   [CONSUMPTION_PRIMA].[HrContracts] C on C.CONTRACT_ID = e.last_contract_id
			left join   [CONSUMPTION_PRIMA].[HrEmployees] HC on HC.EMPLOYEE_ID = C.OFFICE_SUPERVISER_ID and HC.Record_status = 2
	) a
where [Position Name (Short)] in ('CRA','CRA I','CRA II','Senior CRA','Senior CRA I', 'Senior CRA II');
GO