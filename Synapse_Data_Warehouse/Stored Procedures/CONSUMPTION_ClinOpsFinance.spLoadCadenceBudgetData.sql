CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadCadenceBudgetData] 
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadCadenceBudgetData'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
    ,@CallSite VARCHAR(255) = 'Cadence-ETL'
    ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
    ,@AffectedRecordCount BIGINT = 0
    ,@Count  BIGINT = 0
    ,@ProcessingTime DATETIME = GETDATE();

BEGIN TRY

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL



IF OBJECT_ID('STAGING_CADENCE.DepartmenMapping') IS NOT NULL
BEGIN
        TRUNCATE TABLE [STAGING_CADENCE].[DepartmenMapping]
    END

	insert into [STAGING_CADENCE].[DepartmenMapping]
    select distinct b.CadenceDepartmentId, b.CadenceDepartmentName, b.PrimaDepartmentId, b.PrimaDepartmentName, a.PrimaDepartmentCount
    from [dbo].[Full_Departmental_Map] b
        inner join
        (
			select CadenceDepartmentId, count(1) as PrimaDepartmentCount
            from ( select distinct CadenceDepartmentId, CadenceDepartmentName, PrimaDepartmentId, PrimaDepartmentName
                    from [dbo].[Full_Departmental_Map] 
                 ) c
            group by CadenceDepartmentId
		) a on b.CadenceDepartmentId = a.CadenceDepartmentId


IF OBJECT_ID(N'CONSUMPTION_ClinOpsFinance.CadenceBudgetData') IS NOT NULL
BEGIN
        TRUNCATE TABLE [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData]
    END


INSERT INTO  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData]
    (
         [Year]
        ,[Month]
        ,[Project Name]
        ,[Project Currency Code]
        ,[Project Currency Name]
        ,[Service]
        ,[Task Code]
        ,[Task]
        ,[Task Country]
        ,[Part Order Index]
        ,[Segment Order Index]
        ,[Function Code]
        ,[Function]
        ,[Function Country]
        ,[CadenceDepartmentId]
        ,[CadenceDepartmentName]
        ,[PrimaHrDepartmentId]
        ,[PrimaDepartmentName]
        ,[PrimaGlobalCountryId]
        ,[PrimaGlobalCountryName]
        ,[Unit type]
        ,[Currency]
        ,[RecordUpdateType]
		,[Project Ref Id]
		,[Archived Project Ref Id]
		,[PRIMA Project Id]
		,[Project Status]
		,[Project Phase]
		,[Is Deleted Task]
		,[SUM Function Reconciliation Approved Units]
		,[Task Period CADENCE Earned Value]
		,[Task Reconciliation CADENCE Earned Value]
		,[Task CADENCE Earned Value]
		,[Task CADENCE Planned Unit Cost]
		--,[SUM Function Period TimeSheet Actual Total Hours]
		,[SUM Task Period Approved Total Units]
        ,[SUM Function Planned Total Cost Adjusted]
        ,[SUM Function Planned Total Hours]
        ,[Function CurrentRate Adjusted]
        ,[SUM Task Planned Total Units]
        ,[SUM Task Approved Total Units]
        ,[SUM Function TimeSheet Actual Total Hours]
        ,[Total SUM Function TimeSheet Actual Total Hours]
        ,[Original Actual Total Hours (Allocated)]
        ,[Earned Value (Budget)]
        ,[Actual Total Hours (Allocated)]
		,[Actual Cost (Allocated)]
        ,[Earned Value (50% Direct allocation)]
        ,[Earned Value (Direct allocation) Version-2]
        ,[Non-allocated Earned Value]
        ,[Non-allocated Earned Value Version-2]
        ,[Total Indirect Earned Value (Task)]
        ,[Total Indirect Earned Value (Task) Version-2]
        ,[TS hours proportion]
        ,[Actual Cost Proportion]
        ,[Actual Cost (Allocated) Proportion]
        ,[Earned Value (Indirect allocation)]
        ,[Earned Value (Indirect allocation) Version-2]
        ,[Earned Value (Total Allocated)]
        ,[Earned Value (Total Allocated) Version-2]
        ,[Actual Cost of Work Performed]
        ,[Billable Efficiency]
        ,[Billable Efficiency Version-2]
        ,[CREATED_AT]
        ,[UPDATED_AT]
    )
    SELECT
        e.[Period Year]
		, e.[Period Month]
		, e.[Project Name]	
		, e.[Project Currency Code]
		, e.[Project Currency Name]			
		, e.[Service]		
		, e.[Task Code]
		, e.[Task Name]			
		, e.[Task Country Name]
		, e.[Part Order Index]
		, e.[Segment Order Index]
		, e.[Function Code]
		, e.[Function Name]		
		, e.[Function Country Name]
		, d.[CadenceDepartmentId]
		, d.[CadenceDepartmentName]
		, d.[PrimaDepartmentId]
		, d.[PrimaDepartmentName]
		, c.[PrimaGlobalCountryId]
		, c.[PrimaGlobalCountryName]
		, e.[Unit type]																													
		, cur.[ToCurrency]						AS [Currency]
		, e.[RecordUpdateType]					AS [RecordUpdateType]

		, e.[Project Ref Id]
		, e.[Archived Project Ref Id]
		, e.[PRIMA Project Id]
		, e.[Project Status]
		, e.[Project Phase]
		, e.[Is Deleted Task]
		, e.[SUM Function Reconciliation Approved Units]
		, e.[Task Period CADENCE Earned Value]
		,  ISNULL(e.[Task Reconciliation CADENCE Earned Value], 0) * COALESCE(cur.[Rate], 1) 		AS [Task Reconciliation CADENCE Earned Value]
		, e.[Task CADENCE Earned Value]
		, e.[Task CADENCE Planned Unit Cost]
		--, e.[SUM Function TimeSheet Actual Total Hours]
		, e.[SUM Task Period Approved Total Units]
		--,  ISNULL(e.[Task Reconciliation CADENCE Earned Value], 0) * COALESCE(cur.[Rate], 1) 		AS [Task Reconciliation CADENCE Earned Value]
		, ISNULL((e.[SUM Function Planned Total Cost Adjusted] 
                / NULLIF(d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1)		            AS [SUM Function Planned Total Cost Adjusted] 
		, ISNULL((e.[SUM Function Planned Total Hours] 
                / NULLIF(d.PrimaDepartmentCount, 0)), 0) 											AS [SUM Function Planned Total Hours]
		, e.[Function CurrentRate Adjusted]	* COALESCE(cur.[Rate], 1)								AS [Function CurrentRate Adjusted]
		, ISNULL(e.[SUM Task Planned Total Units], 0) 												AS [SUM Task Planned Total Units]
		, ISNULL(e.[SUM Task Approved Total Units], 0) 												AS [SUM Task Approved Total Units]
		, ISNULL((e.[SUM Function TimeSheet Actual Total Hours] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) 											AS [SUM Function TimeSheet Actual Total Hours]
		, ISNULL((e.[Total SUM Function TimeSheet Actual Total Hours] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) 											AS [Total SUM Function TimeSheet Actual Total Hours]
		, ISNULL((e.[Original Actual Total Hours (Allocated)] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) 											AS [Original Actual Total Hours (Allocated)]

		, ISNULL((e.[Earned Value (Budget)] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [Earned Value (Budget)]
		, ISNULL((e.[Actual Total Hours (Allocated)] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) 											AS [Actual Total Hours (Allocated)]

		, ISNULL((e.[Actual Cost (Allocated)]
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 				AS [Actual Cost (Allocated)]

		--Calculated columns
		, ISNULL((e.[Earned Value (50% Direct allocation)] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [Earned Value (50% Direct allocation)]
        , ISNULL((e.[Earned Value (Direct allocation) Version-2] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 	            AS [Earned Value (Direct allocation) Version-2]

		, ISNULL((e.[Non-allocated Earned Value] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 				AS [Non-allocated Earned Value]

        , ISNULL((e.[Non-allocated Earned Value Version-2] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [Non-allocated Earned Value Version-2]

		, e.[Total Indirect Earned Value (Task)] * COALESCE(cur.[Rate], 1) 							AS [Total Indirect Earned Value (Task)]

        , e.[Total Indirect Earned Value (Task) Version-2] * COALESCE(cur.[Rate], 1) 				AS [Total Indirect Earned Value (Task) Version-2]        

		, e.[TS hours proportion] * 100 															AS [TS hours proportion]
		, e.[Actual Cost Proportion]* 100  															AS [Actual Cost Proportion]
        , e.[Actual Cost (Allocated) Proportion]* 100  												AS [Actual Cost (Allocated) Proportion]

		, ISNULL((e.[Earned Value (Indirect allocation)] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 	            AS [Earned Value (Indirect allocation)]

        , ISNULL((e.[Earned Value (Indirect allocation) Version-2] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1)					AS [Earned Value (Indirect allocation) Version-2]

		, ISNULL((e.[Earned Value (Total Allocated)] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 				AS [Earned Value (Total Allocated)]

        , ISNULL((e.[Earned Value (Total Allocated) Version-2] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 	            AS [Earned Value (Total Allocated) Version-2]

		, ISNULL((e.[Actual Cost of Work Performed] 
                / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 				AS [Actual Cost of Work Performed]
		, ISNULL((e.[Earned Value (Total Allocated)] 
                / NULLIF( e.[Actual Cost of Work Performed], 0)), 0) 								AS [Billable Efficiency]

        , ISNULL((e.[Earned Value (Total Allocated) Version-2] 
                / NULLIF( e.[Actual Cost of Work Performed], 0)), 0) 								AS [Billable Efficiency Version-2]

		, GetUtcDate() as [CREATED_AT]					 
		, GetUtcDate() as [UPDATED_AT]
       
    FROM
        (
    SELECT 
		  AA.[Period Year]
		, AA.[Period Month]
		, AA.[Project Name]	
		, AA.[Project Currency Code]
		, AA.[Project Currency Name]			
		, AA.[Service]		
		, AA.[Task Code]
		, AA.[Task Name]			
		, AA.[Task Country Name]
		, AA.[Part Order Index]
		, AA.[Segment Order Index]
		, AA.[Function Code]
		, AA.[Function Name]		
		, AA.[Function Country Name]
		, AA.[Department]
		, AA.[Unit type]													AS [Unit type]

		, AA.[Project Ref Id]
		, AA.[Archived Project Ref Id]
		, AA.[PRIMA Project Id]
		, AA.[Project Status]
		, AA.[Project Phase]
		, AA.[Is Deleted Task]
		, AA.[SUM Function Reconciliation Approved Units]			AS [SUM Function Reconciliation Approved Units]
		, AA.[Task Period CADENCE Earned Value]						AS [Task Period CADENCE Earned Value]
		, AA.[Task Reconciliation CADENCE Earned Value]				AS [Task Reconciliation CADENCE Earned Value]
		, AA.[Task CADENCE Earned Value]							AS [Task CADENCE Earned Value]
		, AA.[Task CADENCE Planned Unit Cost]						AS [Task CADENCE Planned Unit Cost]
		--, AA.[SUM Function Period TimeSheet Actual Total Hours]		AS [SUM Function Period TimeSheet Actual Total Hours]
		--,[SUM Function TimeSheet Actual Total Hours]				AS [SUM Function TimeSheet Actual Total Hours]
		, AA.[SUM Task Period Approved Total Units]					AS [SUM Task Period Approved Total Units]

		, AA.[SUM Function Planned Total Cost Adjusted]						AS [SUM Function Planned Total Cost Adjusted]
		, AA.[SUM Function Planned Total Hours]								AS [SUM Function Planned Total Hours]
		, AA.[Function CurrentRate Adjusted]								AS [Function CurrentRate Adjusted]
		, AA.[SUM Task Planned Total Units]									AS [SUM Task Planned Total Units]
		, AA.[SUM Task Approved Total Units]								AS [SUM Task Approved Total Units]
		, AA.[SUM Function Period TimeSheet Actual Total Hours]				AS [SUM Function TimeSheet Actual Total Hours]
		, AA.[Total SUM Function TimeSheet Period Actual Total Hours]		AS [Total SUM Function TimeSheet Actual Total Hours]
		, AA.[Original Actual Total Hours (Allocated)]			            AS [Original Actual Total Hours (Allocated)]
		, AA.[RecordUpdateType]												AS [RecordUpdateType]
		, AA.[Calc Earned Value (Budget)]									AS [Earned Value (Budget)]
		, AA.[Actual Total Hours (Allocated)]								AS [Actual Total Hours (Allocated)]
		, AA.[Actual Cost (Allocated)]                                      AS [Actual Cost (Allocated)]
		--Calculated columns

		, case when [Task Name] like '%Project Management%' 
			   then 0
			   else case when AA.[Calc Total Actual Total Hours (Allocated)] = 0
						 then 0
						 else CASE WHEN AA.[Actual Total Hours (Allocated)] = 0 
								   THEN 0 
								   ELSE AA.[Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end
							  END
					end
		  end                                                              AS [Earned Value (50% Direct allocation)]

		, case when [Task Name] like '%Project Management%' 
			   then 0
			   else case when AA.[Calc Actual Cost (Allocated)] = 0
						 then 0
						 else CASE WHEN AA.[Actual Cost (Allocated)] = 0 
								   THEN 0 
								   ELSE AA.[Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end
							  END
					end
		  end                                                              AS [Earned Value (Direct allocation) Version-2]


		, [Non-allocated Earned Value]                                      AS [Non-allocated Earned Value]

		, [Non-allocated Earned Value Version-2]                            AS [Non-allocated Earned Value Version-2]

		, [Calc Total Non-allocated Earned Value]			                AS [Total Indirect Earned Value (Task)]

		, [Calc Total Non-allocated Earned Value Version-2]			        AS [Total Indirect Earned Value (Task) Version-2]

		, [TS hours proportion]								                AS [TS hours proportion]
		, [Actual Cost Proportion]							                AS [Actual Cost Proportion]

		, [Actual Cost (Allocated) Proportion]                              AS [Actual Cost (Allocated) Proportion]

		, [Calc Total Non-allocated Earned Value] * case when [Task Name]	 like '%Project Management%' 
														 then [Actual Cost Proportion] 
														 else [TS hours proportion]	
													end		                AS [Earned Value (Indirect allocation)]
	
		, [Calc Total Non-allocated Earned Value Version-2] * [Actual Cost (Allocated) Proportion]	
																			AS [Earned Value (Indirect allocation) Version-2]

		, [Calc Total Non-allocated Earned Value] * case when [Task Name]	 like '%Project Management%' 
														  then [Actual Cost Proportion] 
														  else [TS hours proportion]	
													end

			+ case when ([Task Name] like '%Project Management%' and [Calc SUM Function Period Actual Cost]= 0) 
					then [Calc Earned Value (Budget)]
					else case  when ([Task Name] not like '%Project Management%' and [Calc Total Actual Total Hours (Allocated)] = 0)
							   then [Calc Earned Value (Budget)]
							   else 0
						 end
			  end

			+ case when [Task Name] like '%Project Management%' 
					then 0
					else case when AA.[Calc Total Actual Total Hours (Allocated)] = 0
						   then 0
						   else CASE WHEN AA.[Actual Total Hours (Allocated)] = 0 
									 THEN 0 
									 ELSE AA.[Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end 
								END
						  end
			  end							                                AS [Earned Value (Total Allocated)]

		, [Calc Total Non-allocated Earned Value Version-2] * [Actual Cost (Allocated) Proportion]
				+ case when ([Task Name] like '%Project Management%' and [Calc Actual Cost (Allocated)]= 0) 
				   then [Calc Earned Value (Budget)]
					   else case  when ([Task Name] not like '%Project Management%' and [Calc Actual Cost (Allocated)] = 0)
								  then [Calc Earned Value (Budget)]
                else 0
			  end
				  end
			+ case when [Task Name] like '%Project Management%' 
					then 0
					else case when AA.[Calc Actual Cost (Allocated)] = 0
							  then 0
							  else CASE WHEN AA.[Actual Cost (Allocated)] = 0 
										THEN 0 
									    ELSE AA.[Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end 
									END
						 end
			  end							                                AS [Earned Value (Total Allocated) Version-2]

		, (case when [RecordUPdateType] = 'BKF' then 0 else [SUM Function Period Actual Cost] end)	AS [Actual Cost of Work Performed]

		, ISNULL((
					([Calc Total Non-allocated Earned Value] * case when [Task Name]	 like '%Project Management%' 
																	then [Actual Cost Proportion] 
																	else [TS hours proportion]	
															   end
					 
					 + case when ([Task Name] like '%Project Management%' and [Calc SUM Function Period Actual Cost]= 0) 
							then [Calc Earned Value (Budget)]
							else case   when ([Task Name] not like '%Project Management%' and [Calc Total Actual Total Hours (Allocated)] = 0)
										then [Calc Earned Value (Budget)]
										else 0
								 end
					   end
					 
					 + case when [Task Name] like '%Project Management%' 
							then 0
							else case when AA.[Calc Total Actual Total Hours (Allocated)] = 0
									  then 0
									  else CASE WHEN AA.[Actual Total Hours (Allocated)] = 0 
												THEN 0 
												ELSE AA.[Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end 
											END
								  end
					   end
					)
				/ NULLIF((case when [RecordUPdateType] = 'BKF' then 0 else [SUM Function Period Actual Cost] end), 0)
				), 0)                                           			
				AS [Billable Efficiency]

		, ISNULL((
					([Calc Total Non-allocated Earned Value Version-2] * [Actual Cost (Allocated) Proportion]

						 + case when ([Task Name] like '%Project Management%' and [Calc SUM Function Period Actual Cost]= 0) 
							then [Calc Earned Value (Budget)]
								else case   when ([Task Name] not like '%Project Management%' and [Calc Actual Cost (Allocated)] = 0)
											then [Calc Earned Value (Budget)]
                            else 0
					   end
						   end

					 + case when [Task Name] like '%Project Management%' 
							then 0
							else case when AA.[Calc Actual Cost (Allocated)] = 0
								   then 0
								   else CASE WHEN AA.[Actual Cost (Allocated)] = 0 
											 THEN 0 
											 ELSE AA.[Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end 
										END
								  end
					   end
					)
				/ NULLIF((case when [RecordUPdateType] = 'BKF' then 0 else [SUM Function Period Actual Cost] end), 0)
				), 0)                                                   	
				AS [Billable Efficiency Version-2]            
       FROM STAGING_CADENCE.MonthlyTaskTaskCountry AA with (nolock)


    UNION

        -- Records WHERE [Task Country Name] IN ('Global', 'No Country')
       SELECT 
		  BB.[Period Year]
		, BB.[Period Month]
		, BB.[Project Name]	
		, BB.[Project Currency Code]
		, BB.[Project Currency Name]			
		, BB.[Service]		
		, BB.[Task Code]
		, BB.[Task Name]			
		, BB.[Task Country Name]
		, BB.[Part Order Index]
		, BB.[Segment Order Index]
		, BB.[Function Code]
		, BB.[Function Name]		
		, BB.[Function Country Name]
		, BB.[Department]
		, BB.[Unit type] AS [Unit type]

		, BB.[Project Ref Id]
		, BB.[Archived Project Ref Id]
		, BB.[PRIMA Project Id]
		, BB.[Project Status]
		, BB.[Project Phase]
		, BB.[Is Deleted Task]
		, BB.[SUM Function Reconciliation Approved Units]				AS [SUM Function Reconciliation Approved Units]
		, BB.[Task Period CADENCE Earned Value]							AS [Task Period CADENCE Earned Value]
		, BB.[Task Reconciliation CADENCE Earned Value]					AS [Task Reconciliation CADENCE Earned Value]
		, BB.[Task CADENCE Earned Value]								AS [Task CADENCE Earned Value]
		, BB.[Task CADENCE Planned Unit Cost]							AS [Task CADENCE Planned Unit Cost]
		--, BB.[SUM Function Period TimeSheet Actual Total Hours]			AS [SUM Function TimeSheet Actual Total Hours]
		--,[SUM Function TimeSheet Actual Total Hours]					AS [SUM Function TimeSheet Actual Total Hours]
		, BB.[SUM Task Period Approved Total Units]						AS [SUM Task Period Approved Total Units]

		, BB.[SUM Function Planned Total Cost Adjusted]					AS [SUM Function Planned Total Cost Adjusted]
		, BB.[SUM Function Planned Total Hours]							AS [SUM Function Planned Total Hours]
		, BB.[Function CurrentRate Adjusted]							AS [Function CurrentRate Adjusted]
		, BB.[SUM Task Planned Total Units]								AS [SUM Task Planned Total Units]
		, BB.[SUM Task Approved Total Units]							AS [SUM Task Approved Total Units]
		, BB.[SUM Function Period TimeSheet Actual Total Hours]			AS [SUM Function TimeSheet Actual Total Hours]
		, BB.[Total SUM Function TimeSheet Period Actual Total Hours]	AS [Total SUM Function TimeSheet Actual Total Hours]
		, BB.[Original Actual Total Hours (Allocated)]		            AS [Original Actual Total Hours (Allocated)]
		, BB.[RecordUpdateType]
		, BB.[Calc Earned Value (Budget)] 								AS [Earned Value (Budget)]
		, BB.[Actual Total Hours (Allocated)] 							AS [Actual Total Hours (Allocated)]
		, BB.[Actual Cost (Allocated)]                                  AS [Actual Cost (Allocated)]

		--Calculated columns
		, case when [Task Name] like '%Project Management%' 
			   then 0
			   else case when [Calc Total Actual Total Hours (Allocated)] = 0
						 then 0
						 else CASE WHEN [Actual Total Hours (Allocated)] = 0 
								   THEN 0 
								   ELSE [Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end 
							  END
					end
		  end													        AS [Earned Value (50% Direct allocation)]

		, case when [Task Name] like '%Project Management%' 
			   then 0
			  else case when [Calc Actual Cost (Allocated)] = 0
						 then 0
						 else CASE WHEN [Actual Cost (Allocated)] = 0 
								   THEN 0 
								   ELSE [Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end 
						   END
					end
		  end													        AS [Earned Value (Direct allocation) Version-2]

		, BB.[Non-allocated Earned Value]                               AS [Non-allocated Earned Value]

		, BB.[Non-allocated Earned Value Version-2]                     AS [Non-allocated Earned Value Version-2]

		, [Calc Total Non-allocated Earned Value]						AS [Total Indirect Earned Value (Task)]

		, [Calc Total Non-allocated Earned Value Version-2]				AS [Total Indirect Earned Value (Task) Version-2]

		, [TS hours proportion]											AS [TS hours proportion]
		, [Actual Cost Proportion]										AS [Actual Cost Proportion]

		, [Actual Cost (Allocated) Proportion]							AS [Actual Cost (Allocated) Proportion]        

		, [Calc Total Non-allocated Earned Value] * case when [Task Name]	 like '%Project Management%' 
														 then [Actual Cost Proportion] 
														 else [TS hours proportion]	
													end			
																		AS [Earned Value (Indirect allocation)]

		, [Calc Total Non-allocated Earned Value Version-2] * [Actual Cost (Allocated) Proportion]		
																		AS [Earned Value (Indirect allocation) Version-2]


		, [Calc Total Non-allocated Earned Value] * case when [Task Name] like '%Project Management%' 
														 then [Actual Cost Proportion] 
														 else [TS hours proportion]	
													end

			+ case when ([Task Name] like '%Project Management%' and [Calc SUM Function Period Actual Cost]= 0) 
				   then [Calc Earned Value (Budget)]
				   else case when ([Task Name] not like '%Project Management%' and [Calc Total Actual Total Hours (Allocated)] = 0)
							 then [Calc Earned Value (Budget)]
							 else 0
						 end
			  end

			+  case when [Task Name] like '%Project Management%' 
					then 0
					else case when [Calc Total Actual Total Hours (Allocated)] = 0
							  then 0
							  else CASE WHEN [Actual Total Hours (Allocated)] = 0 
										THEN 0 
										ELSE [Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end 
								   END
						 end
			   end                                             AS [Earned Value (Total Allocated)]

		, [Calc Total Non-allocated Earned Value Version-2] * [Actual Cost (Allocated) Proportion]
				+ case when ([Task Name] like '%Project Management%' and [Calc Actual Cost (Allocated)]= 0) 
					then [Calc Earned Value (Budget)]
						else case   when ([Task Name] not like '%Project Management%' and [Calc Actual Cost (Allocated)] = 0)
									then [Calc Earned Value (Budget)]
                    else 0
			  end
				  end
			+  case when [Task Name] like '%Project Management%' 
						 then 0
						 else case when [Calc Actual Cost (Allocated)] = 0
								   then 0
								   else CASE WHEN [Actual Cost (Allocated)] = 0 
										   THEN 0 
										   ELSE [Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end 
										END
							  end
				end                                             AS [Earned Value (Total Allocated) Version-2]


		, (case when [RecordUPdateType] = 'BKF' then 0 else [SUM Function Period Actual Cost] end)		
																		AS [Actual Cost of Work Performed]

		, ISNULL((
					(	[Calc Total Non-allocated Earned Value] * case when [Task Name] like '%Project Management%' 
															  then [Actual Cost Proportion] 
															  else [TS hours proportion]	
														  end

						+ case when ([Task Name] like '%Project Management%' and [Calc SUM Function Period Actual Cost]= 0) 
								then [Calc Earned Value (Budget)]
								else case   when ([Task Name] not like '%Project Management%' and [Calc Total Actual Total Hours (Allocated)] = 0)
											then [Calc Earned Value (Budget)]
											else 0
									 end
						  end

						+  case when [Task Name] like '%Project Management%' 
									 then 0
									 else case when [Calc Total Actual Total Hours (Allocated)] = 0
											   then 0
											   else CASE WHEN [Actual Total Hours (Allocated)] = 0 
														 THEN 0 
														 ELSE [Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end 
													END
										  end
							end
					)
					/ NULLIF((case when [RecordUPdateType] = 'BKF' then 0 else [SUM Function Period Actual Cost] end), 0)
				), 0)									
						AS [Billable Efficiency]

		, ISNULL((
					([Calc Total Non-allocated Earned Value Version-2] * [Actual Cost (Allocated) Proportion]

							+ case when ([Task Name] like '%Project Management%' and [Calc SUM Function Period Actual Cost]= 0) 
									then [Calc Earned Value (Budget)]
									else case   when ([Task Name] not like '%Project Management%' and [Calc Actual Cost (Allocated)] = 0)
								then [Calc Earned Value (Budget)]
                                else 0
						  end
							  end

						+  case when [Task Name] like '%Project Management%' 
									 then 0
									  else case when [Calc Actual Cost (Allocated)] = 0
											   then 0
											   else CASE WHEN [Actual Cost (Allocated)] = 0 
													     THEN 0 
    												     ELSE [Calc Earned Value (Budget)] * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end 
													END
										  end
							end
					)
					/ NULLIF((case when [RecordUPdateType] = 'BKF' then 0 else [SUM Function Period Actual Cost] end), 0)
				), 0)									
							AS [Billable Efficiency Version-2]
       FROM STAGING_CADENCE.MonthlyTaskTaskCountryGlobalNoCountry BB with (nolock)

        UNION

        -- Records WHERE [Service Code] = 'OOS_SERVICE'
        SELECT 
			  CC.[Period Year]
			, CC.[Period Month]
			, CC.[Project Name]	
			, CC.[Project Currency Code]
			, CC.[Project Currency Name]			
			, CC.[Service Name]		
			, CC.[Task Code]
			, CC.[Task Name]			
			, CC.[Task Country Name]
			, CC.[Part Order Index]
			, CC.[Segment Order Index]
			, CC.[Function Code]
			, CC.[Function Name]		
			, CC.[Function Location Name]									AS [Function Country Name]
			, CC.[Department Name]											AS [Department]
			, NULL															AS [Unit type]

			, CC.[Project Ref Id]
			, CC.[Archived Project Ref Id]
			, CC.[PRIMA Project Id]
			, CC.[Project Status]
			, CC.[Project Phase]
			, CC.[Is Deleted Task]
			, SUM(COALESCE(CC.[Reconciliation Approved Units], 0))			AS [SUM Function Reconciliation Approved Units]
			, MAX(COALESCE(CC.[Period CADENCE Earned Value], 0))			AS [Task Period CADENCE Earned Value]
			, MAX(COALESCE(CC.[Reconciliation CADENCE Earned Value], 0))	AS [Task Reconciliation CADENCE Earned Value]
			, MAX(COALESCE(CC.[CADENCE Earned Value], 0))					AS [Task CADENCE Earned Value]
			, MAX(COALESCE(CC.[CADENCE Planned Unit Cost], 0))				AS [Task CADENCE Planned Unit Cost]
			, 0					AS [SUM Task Period Approved Total Units]

			, SUM(COALESCE(CC.[Planned Total Cost], 0))						AS [SUM Function Planned Total Cost Adjusted]
			, SUM(COALESCE(CC.[Planned Total Hours], 0))					AS [SUM Function Planned Total Hours]
			, COALESCE(CC.[Rate], 0)										AS [Function CurrentRate Adjusted]
			, 0																AS [SUM Task Planned Total Units]
			, 0																AS [SUM Task Approved Total Units]
			, SUM(COALESCE(CC.[Actual Hours], 0))							AS [SUM Function TimeSheet Actual Total Hours]
			, 0																AS [Total SUM Function TimeSheet Actual Total Hours]
			, SUM(COALESCE(CC.[Actual Hours], 0))							AS [SUM Function Original TimeSheet Actual Total Hours]
			, 'OOS'															AS [RecordUpdateType]
			, 0																AS [Earned Value (Budget)]
			, 0																AS [Actual Total Hours (Allocated)]
			,  sum(CC.[Actual Cost])										AS [Actual Cost (Allocated)]
			, 0																AS [Earned Value (50% Direct allocation)]
			, 0																AS [Earned Value (Direct allocation) Version-2]
			, 0																AS [Non-allocated Earned Value]
			, 0																AS [Non-allocated Earned Value Version-2]
			, 0																AS [Total Indirect Earned Value (Task)]
			, 0																AS [Total Indirect Earned Value (Task) Version-2]
			, 0																AS [TS hours proportion]
			, 0																AS [Actual Cost Proportion]
			, 0																AS [Actual Cost (Allocated) Proportion]
			, 0																AS [Earned Value (Indirect allocation)]
			, 0																AS [Earned Value (Indirect allocation) Version-2]
			, 0																AS [Earned Value (Total Allocated)]
			, 0																AS [Earned Value (Total Allocated) Version-2]
			, sum(CC.[Actual Cost])											AS [Actual Cost of Work Performed]
			, 0																AS [Billable Efficiency]
			, 0																AS [Billable Efficiency Version-2]        
        FROM [STAGING_CADENCE].[CadenceOutOfScopeRecords] CC with (nolock)
        group by 
			  CC.[Period Year]
			, CC.[Period Month]
			, CC.[Project Name]	
			, CC.[Project Currency Code]
			, CC.[Project Currency Name]	
			, CC.[Service Name]		
			, CC.[Task Code]
			, CC.[Task Name]			
			, CC.[Task Country Name]
			, CC.[Part Order Index]
			, CC.[Segment Order Index]
			, CC.[Function Code]
			, CC.[Function Name]		
			, CC.[Function Location Name]
			, CC.[Department Name]
			, COALESCE(CC.[Rate], 0)
			, CC.[Project Ref Id]
			, CC.[Archived Project Ref Id]
			, CC.[PRIMA Project Id]
			, CC.[Project Status]
			, CC.[Project Phase]
			, CC.[Is Deleted Task]
	
         UNION

        -- Reconcilliation Data
        SELECT 
			  DD.[Period Year]
			, DD.[Period Month]
			, DD.[Project Name]	
			, DD.[Project Currency Code]
			, DD.[Project Currency Name]			
			, DD.[Service]		
			, DD.[Task Code]
			, DD.[Task Name]			
			, DD.[Task Country Name]
			, DD.[Part Order Index]
			, DD.[Segment Order Index]
			, DD.[Function Code]
			, DD.[Function Name]		
			, DD.[Function Country Name]											AS [Function Country Name]
			, DD.[Department]														AS [Department]
			, DD.[Unit type]														AS [Unit type]

			, DD.[Project Ref Id]
			, DD.[Archived Project Ref Id]
			, DD.[PRIMA Project Id]
			, DD.[Project Status]
			, DD.[Project Phase]
			, DD.[Is Deleted Task]
			, SUM(COALESCE(DD.[SUM Function Reconciliation Approved Units], 0))			AS [SUM Function Reconciliation Approved Units]			
			, MAX(COALESCE(DD.[Task Period CADENCE Earned Value], 0))			AS [Task Period CADENCE Earned Value]
			, MAX(COALESCE(DD.[Task Reconciliation CADENCE Earned Value], 0))	AS [Task Reconciliation CADENCE Earned Value]
			, MAX(COALESCE(DD.[Task CADENCE Earned Value], 0))					AS [Task CADENCE Earned Value]
			, MAX(COALESCE(DD.[Task CADENCE Planned Unit Cost], 0))				AS [Task CADENCE Planned Unit Cost]
			, SUM(COALESCE(DD.[SUM Task Approved Total Units], 0))					AS [SUM Task Period Approved Total Units]
			, SUM(COALESCE(DD.[SUM Function Planned Total Cost Adjusted], 0))					AS [SUM Function Planned Total Cost Adjusted]
			, 0																		AS [SUM Function Planned Total Hours]
			, COALESCE(DD.[Function CurrentRate Adjusted], 0)									AS [Function CurrentRate Adjusted]
			, sum(COALESCE(DD.[SUM Task Planned Total Units], 0)) 								AS [SUM Task Planned Total Units]
			, sum(COALESCE(DD.[SUM Task Approved Total Units], 0))								AS [SUM Task Approved Total Units]
			, SUM(COALESCE(DD.[SUM Function Reconciliation TimeSheet Actual Total Hours], 0))	AS [SUM Function TimeSheet Actual Total Hours]
			, sum(COALESCE(DD.[SUM Function Actual Hours], 0))										AS [Total SUM Function TimeSheet Actual Total Hours]
			, SUM(COALESCE(DD.[SUM Function Reconciliation TimeSheet Actual Total Hours], 0))	AS [SUM Function Original TimeSheet Actual Total Hours]
			, DD.[RecordUpdateType]													AS [RecordUpdateType]
			, sum(COALESCE([Earned Value (Budget)], 0))											AS [Earned Value (Budget)]
			, 0																		AS [Actual Total Hours (Allocated)]
			, 0																		AS [Actual Cost (Allocated)]
			, sum(COALESCE([Earned Value (50% Direct allocation)], 0))							AS [Earned Value (50% Direct allocation)]
			, sum(COALESCE([Earned Value (Direct allocation) Version-2], 0))						AS [Earned Value (Direct allocation) Version-2]
			, 0																		AS [Non-allocated Earned Value]
			, 0																		AS [Non-allocated Earned Value Version-2]        
			, sum(COALESCE([Total Indirect Earned Value (Task)], 0))								AS [Total Indirect Earned Value (Task)]
			, sum(COALESCE([Total Indirect Earned Value (Task) Version-2], 0))				    AS [Total Indirect Earned Value (Task) Version-2]
			, sum(COALESCE([TS hours proportion], 0))											AS [TS hours proportion]
			, sum(COALESCE([Actual Cost Proportion], 0))											AS [Actual Cost Proportion]
			, 0                                                                     AS [Actual Cost (Allocated) Proportion]
			, sum(COALESCE([Earned Value (Indirect allocation)], 0))								AS [Earned Value (Indirect allocation)]
			, sum(COALESCE([Earned Value (Indirect allocation) Version-2], 0))					AS [Earned Value (Indirect allocation) Version-2]
			, sum(COALESCE([Earned Value (Total Allocated)], 0))									AS [Earned Value (Total Allocated)]
			, sum(COALESCE([Earned Value (Total Allocated) Version-2], 0))						AS [Earned Value (Total Allocated) Version-2]
			, 0																		AS [Actual Cost of Work Performed]
			, 0																		AS [Billable Efficiency]
			, 0																		AS [Billable Efficiency Version-2]
        FROM [STAGING_CADENCE].[ReconciliationEV] DD with (nolock)

        group by 
			  DD.[Period Year]
			, DD.[Period Month]
			, DD.[Project Name]	
			, DD.[Project Currency Code]
			, DD.[Project Currency Name]	
			, DD.[Service]		
			, DD.[Task Code]
			, DD.[Task Name]			
			, DD.[Task Country Name]
			, DD.[Part Order Index]
			, DD.[Segment Order Index]
			, DD.[Function Code]
			, DD.[Function Name]		
			, DD.[Function Country Name]
			, DD.[Department]
			, DD.[Unit type]
			, DD.[Function CurrentRate Adjusted]
			, DD.[RecordUpdateType]
			, DD.[Project Ref Id]
			, DD.[Archived Project Ref Id]
			, DD.[PRIMA Project Id]
			, DD.[Project Status]
			, DD.[Project Phase]
			, DD.[Is Deleted Task]


				) e
        left join (select [Year], [Month], [FromCurrency], [ToCurrency], [Rate]
        from [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] with (nolock)
        where [ToCurrency] in ('CHF', 'GBP', 'USD', 'EUR')
		  ) cur on cur.[Year] = e.[Period Year] and
            cur.[Month] = e.[Period Month] and
            cur.[FromCurrency] = e.[Project Currency Code]
        left join [STAGING_CADENCE].[DepartmenMapping]  d with (nolock) on d.CadenceDepartmentName = e.[Department]
        left join(
			select [Function Country Code], [Function Country], gc.Country_id as [PrimaGlobalCountryId], gc.Country_name as [PrimaGlobalCountryName]
        from (select distinct [Function Location Code] as [Function Country Code], [Function Location Name] as [Function Country]
            from [STAGING_CADENCE].[CadenceExtract]  with (nolock)
            where [Layer] ='function-location' 
				  ) cc
            inner join [CONSUMPTION_PRIMA].[GlobalCountries] gc with (nolock) on gc.Country_code = cc.[Function Country Code]
 		) c on c.[Function Country] = e.[Function Country Name] 




		
/*************************** Country Specific (Currency/Departments)  ****************************/



if object_id(N'tempdb..#MonthlyTaskTaskCountry') is not null
begin drop table #MonthlyTaskTaskCountry; end

CREATE TABLE #MonthlyTaskTaskCountry
WITH
(
	DISTRIBUTION = HASH ([Project Name], [period year], [period Month], [Task Code], [Part Order Index], [segment order index], [Task Country Name], [CadenceDepartmentId] ),
	CLUSTERED COLUMNSTORE INDEX
)
AS


Select    
      e.[project name]
    , e.[period year]
    , e.[period Month]
    , e.[task code]
    , e.[segment order index]
    , e.[part order index]
    , e.[Task Country Name]
    , e.[Project Currency Code]
    , e.[Department]
    , e.[Function Country Name]
    , e.[RecordUpdateType]
    , d.[CadenceDepartmentId]
    , d.[PrimaDepartmentId]
    , c.[PrimaGlobalCountryId]
    , cur.[ToCurrency]	 AS [Currency]
    , e.[Actual Cost (Allocated) Proportion]
    , e.[RecordCount]
	, ISNULL((e.[Earned Value (Budget)] 
            / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [Original Earned Value (Budget)]
  	, ISNULL((e.[Task Period CADENCE Earned Value] 
            / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [Task Period CADENCE Earned Value]              
  	, ISNULL((e.[Calc Task Period CADENCE Earned Value]
            / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [New Task Period CADENCE Earned Value]  


FROM
    (
        select 
            BB.[project name],
            BB.[period year],
            BB.[period Month],
            BB.[task code],
            BB.[segment order index],
            BB.[part order index],
            BB.[Task Country Name],
            BB.[Project Currency Code],
            BB.[Department],
            BB.[Function Country Name],
            BB.[RecordUpdateType],
            AA.[RecordCount],
            AA.[Earned Value (Budget)], 
            AA.[Task Period CADENCE Earned Value], 
            AA.[Calc Task Period CADENCE Earned Value],
            BB.[Actual Cost (Allocated) Proportion]
        from [STAGING_CADENCE].[MonthlyTaskTaskCountry] BB with (nolock)
        inner join 
            (    
                select 
                    [project name],
                    [period Month],
                    [period year],
                    [task code],
                    [segment order index],
                    [part order index],
                    [Task Country Name],
                    Count(1) as [RecordCount],
                    MAX([Task Period CADENCE Earned Value])             as  [Task Period CADENCE Earned Value],
                    MAX([Task CADENCE Earned Value])                    as  [Task CADENCE Earned Value],
                    ISNULL(MAX([Task Period CADENCE Earned Value])/NULLIF(Count(1), 0), 0) as [Calc Task Period CADENCE Earned Value],
                    sum([SUM Task Planned Total Units]) as [SUM Task Planned Total Units],
                    sum([SUM Function Planned Total Cost Adjusted]) as [SUM Function Planned Total Cost Adjusted],
                    sum([Calc Earned Value (Budget)]) as [Earned Value (Budget)]
                from [STAGING_CADENCE].[MonthlyTaskTaskCountry] with (nolock) 
                where  [RecordUpdateType] not in ('OOS', 'REC')   --'NCF', 'NCD', 'NCB', 
                group by 		
                    [project name],
                    [period Month],
                    [period year],
                    [Task Country Name],
                    [task code],
                    [segment order index],
                    [part order index]
                Having MAX([Task Period CADENCE Earned Value]) <> 0
                    and (sum([SUM Task Planned Total Units]) = 0 or sum([SUM Function Planned Total Cost Adjusted]) = 0)  
            ) AA  ON
                        AA.[project name]           = BB.[project name]
                    and AA.[Period Month]           = BB.[period Month]
                    and AA.[Period year]            = BB.[period year]
                    and AA.[Task Country Name]      = BB.[Task Country Name]
                    and AA.[task code]              = BB.[task code]
                    and AA.[segment order index]    = BB.[segment order index]
                    and AA.[part order index]       = BB.[part order index]
            where   BB.[RecordUpdateType] not in ('OOS', 'REC')   --'NCF', 'NCD', 'NCB',
    ) e
    left join (select [Year], [Month], [FromCurrency], [ToCurrency], [Rate]
    from [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] with (nolock)
    where [ToCurrency] in ('CHF', 'GBP', 'USD', 'EUR')
	  ) cur on cur.[Year] = e.[Period Year] and
        cur.[Month] = e.[Period Month] and
        cur.[FromCurrency] = e.[Project Currency Code]
    left join [STAGING_CADENCE].[DepartmenMapping]  d with (nolock) on d.CadenceDepartmentName = e.[Department]
    left join(
		select [Function Country Code], [Function Country], gc.Country_id as [PrimaGlobalCountryId], gc.Country_name as [PrimaGlobalCountryName]
    from (select distinct [Function Location Code] as [Function Country Code], [Function Location Name] as [Function Country]
        from [STAGING_CADENCE].[CadenceExtract]  with (nolock)
        where [Layer] ='function-location' 
			  ) cc
        inner join [CONSUMPTION_PRIMA].[GlobalCountries] gc with (nolock) on gc.Country_code = cc.[Function Country Code]
 	) c on c.[Function Country] = e.[Function Country Name] 



	
/*************************** Global-NoCountry Specific (Currency/Departments)  ****************************/


if object_id(N'tempdb..#MonthlyTaskTaskCountryGlobalNoCountry') is not null
begin drop table #MonthlyTaskTaskCountryGlobalNoCountry; end

CREATE TABLE #MonthlyTaskTaskCountryGlobalNoCountry
WITH
(
	DISTRIBUTION = HASH ([Project Name], [period year], [period Month], [Task Code], [Part Order Index], [segment order index], [Task Country Name], [CadenceDepartmentId] ),
	CLUSTERED COLUMNSTORE INDEX
)
AS


Select    
      e.[project name]
    , e.[period year]
    , e.[period Month]
    , e.[task code]
    , e.[segment order index]
    , e.[part order index]
    , e.[Task Country Name]
    , e.[Project Currency Code]
    , e.[Department]
    , e.[Function Country Name]
    , e.[RecordUpdateType]
    , d.[CadenceDepartmentId]
    , d.[PrimaDepartmentId]
    , c.[PrimaGlobalCountryId]
    , cur.[ToCurrency]	 AS [Currency]
    , e.[Actual Cost (Allocated) Proportion]

    , e.[RecordCount]
	, ISNULL((e.[Earned Value (Budget)] 
            / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [Original Earned Value (Budget)]
  	, ISNULL((e.[Task Period CADENCE Earned Value] 
            / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [Task Period CADENCE Earned Value]              
  	, ISNULL((e.[Calc Task Period CADENCE Earned Value]
            / NULLIF( d.PrimaDepartmentCount, 0)), 0) * COALESCE(cur.[Rate], 1) 		        AS [New Task Period CADENCE Earned Value]  


FROM
    (
        select 
            BB.[project name],
            BB.[period year],
            BB.[period Month],
            BB.[task code],
            BB.[segment order index],
            BB.[part order index],
            BB.[Task Country Name],
            BB.[Project Currency Code],
            BB.[Department],
            BB.[Function Country Name],
            BB.[RecordUpdateType],
            AA.[RecordCount],
            AA.[Earned Value (Budget)], 
            AA.[Task Period CADENCE Earned Value], 
            AA.[Calc Task Period CADENCE Earned Value],
            BB.[Actual Cost (Allocated) Proportion]
        from [STAGING_CADENCE].[MonthlyTaskTaskCountryGlobalNoCountry] BB with (nolock)
        inner join 
            (    
                select 
                    [project name],
                    [period Month],
                    [period year],
                    [task code],
                    [segment order index],
                    [part order index],
                    [Task Country Name],
                    Count(1) as [RecordCount],
                    MAX([Task Period CADENCE Earned Value])             as  [Task Period CADENCE Earned Value],
                    MAX([Task CADENCE Earned Value])                    as  [Task CADENCE Earned Value],
                    ISNULL(MAX([Task Period CADENCE Earned Value])/NULLIF(Count(1), 0), 0) as [Calc Task Period CADENCE Earned Value],
                    sum([SUM Task Planned Total Units]) as [SUM Task Planned Total Units],
                    sum([SUM Function Planned Total Cost Adjusted]) as [SUM Function Planned Total Cost Adjusted],
                    sum([Calc Earned Value (Budget)]) as [Earned Value (Budget)]
                from [STAGING_CADENCE].[MonthlyTaskTaskCountryGlobalNoCountry] with (nolock) 
                where  [RecordUpdateType]  not in ('OOS', 'REC')   --'NCF', 'NCD', 'NCB',
                group by 		
                    [project name],
                    [period Month],
                    [period year],
                    [Task Country Name],
                    [task code],
                    [segment order index],
                    [part order index]
                Having MAX([Task Period CADENCE Earned Value]) <> 0
                    and (sum([SUM Task Planned Total Units]) = 0 or sum([SUM Function Planned Total Cost Adjusted]) = 0)  
            ) AA  ON
                        AA.[project name]           = BB.[project name]
                    and AA.[Period Month]           = BB.[period Month]
                    and AA.[Period year]            = BB.[period year]
                    and AA.[Task Country Name]      = BB.[Task Country Name]
                    and AA.[task code]              = BB.[task code]
                    and AA.[segment order index]    = BB.[segment order index]
                    and AA.[part order index]       = BB.[part order index]
            where   BB.[RecordUpdateType] not in ('OOS', 'REC')   --'NCF', 'NCD', 'NCB',
	) e
        left join (select [Year], [Month], [FromCurrency], [ToCurrency], [Rate]
        from [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate] with (nolock)
        where [ToCurrency] in ('CHF', 'GBP', 'USD', 'EUR')
		  ) cur on cur.[Year] = e.[Period Year] and
            cur.[Month] = e.[Period Month] and
            cur.[FromCurrency] = e.[Project Currency Code]
        left join [STAGING_CADENCE].[DepartmenMapping]  d with (nolock) on d.CadenceDepartmentName = e.[Department]
        left join(
			select [Function Country Code], [Function Country], gc.Country_id as [PrimaGlobalCountryId], gc.Country_name as [PrimaGlobalCountryName]
        from (select distinct [Function Location Code] as [Function Country Code], [Function Location Name] as [Function Country]
            from [STAGING_CADENCE].[CadenceExtract]  with (nolock)
            where [Layer] ='function-location' 
				  ) cc
            inner join [CONSUMPTION_PRIMA].[GlobalCountries] gc with (nolock) on gc.Country_code = cc.[Function Country Code]
 		) c on c.[Function Country] = e.[Function Country Name] 



/********************** Final Updates (Country) ***********************/

update CB
set [Earned Value (Budget)] = M.[New Task Period CADENCE Earned Value]
--, [Earned Value (Total Allocated)] = M.[New Task Period CADENCE Earned Value] 
, [Earned Value (Total Allocated) Version-2] = M.[New Task Period CADENCE Earned Value] 
from  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData]  CB
inner join #MonthlyTaskTaskCountry M
on 
        M.[project name]            =   CB.[project name]
   and  M.[period year]             =   CB.[year]
   and  M.[period Month]            =   CB.[Month]
   and  M.[task code]               =   CB.[task code]
   and  M.[segment order index]     =   CB.[segment order index]
   and  M.[part order index]        =   CB.[part order index]
   and  M.[Task Country Name]       =   CB.[Task Country]
   and  M.[Project Currency Code]   =   CB.[Project Currency Code]
   and  M.[Function Country Name]   =   CB.[Function Country]
   and  M.[CadenceDepartmentId]     =   CB.[CadenceDepartmentId]
   and  M.[PrimaDepartmentId]       =   CB.[PrimaHrDepartmentId]
   and  M.[PrimaGlobalCountryId]    =   CB.[PrimaGlobalCountryId]
   and  M.[Currency]                =   CB.[Currency]
   and M.[RecordUpdateType]         =   CB.[RecordUpdateType]
where    CB.[RecordUpdateType]  not in ('OOS', 'REC') 



/********************** Final Updates (Global-NoCountry) ***********************/

update CB
set [Earned Value (Budget)] = M.[New Task Period CADENCE Earned Value] 
--, [Earned Value (Total Allocated)] = M.[New Task Period CADENCE Earned Value] 
, [Earned Value (Total Allocated) Version-2] = M.[New Task Period CADENCE Earned Value] 
from  [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData]  CB
inner join #MonthlyTaskTaskCountryGlobalNoCountry M
on 
         M.[project name]            =   CB.[project name]
    and  M.[period year]             =   CB.[year]
    and  M.[period Month]            =   CB.[Month]
    and  M.[task code]               =   CB.[task code]
    and  M.[segment order index]     =   CB.[segment order index]
    and  M.[part order index]        =   CB.[part order index]
    and  M.[Task Country Name]       =   CB.[Task Country]
    and  M.[Project Currency Code]   =   CB.[Project Currency Code]
    and  M.[Function Country Name]   =   CB.[Function Country]
    and  M.[CadenceDepartmentId]     =   CB.[CadenceDepartmentId]
    and  M.[PrimaDepartmentId]       =   CB.[PrimaHrDepartmentId]
    and  M.[PrimaGlobalCountryId]    =   CB.[PrimaGlobalCountryId]
    and  M.[Currency]                =   CB.[Currency]
    and  M.[RecordUpdateType]         =   CB.[RecordUpdateType]
where    CB.[RecordUpdateType]  not in ('OOS', 'REC') 








EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [CONSUMPTION_ClinOpsFinance].[CadenceBudgetData] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
PRINT @MSG + ' (Record count: ' + CAST(@Count AS VARCHAR(10)) + ')' ;
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @Count, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

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