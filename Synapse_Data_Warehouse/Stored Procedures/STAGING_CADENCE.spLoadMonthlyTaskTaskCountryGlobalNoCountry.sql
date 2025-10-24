CREATE PROC [STAGING_CADENCE].[spLoadMonthlyTaskTaskCountryGlobalNoCountry] AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadMonthlyTaskTaskCountryGlobalNoCountry'
DECLARE @ProcName NVARCHAR(128) = '[STAGING_CADENCE].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
    ,@CallSite VARCHAR(255) = 'Cadence-ETL'
    ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
    ,@AffectedRecordCount BIGINT = 0
    ,@Count  BIGINT = 0
    ,@ProcessingTime DATETIME = GETDATE();

BEGIN TRY

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL





-- EV Allocation 
-- Calculate aggregate totals WHERE [Task Country Name] IN ('Global', 'No Country')


IF OBJECT_ID(N'STAGING_CADENCE.AggregatedCountryTotals') IS NOT NULL
    TRUNCATE TABLE [STAGING_CADENCE].[AggregatedCountryTotals]


insert 	INTO [STAGING_CADENCE].[AggregatedCountryTotals]
    SELECT
        FTS.[Period Year]
		, FTS.[Period Month]
		, FTS.[Project Name]	
		, FTS.[Task Code]
        , FTS.[Task Country Name]
		, FTS.[Part Order Index]
		, FTS.[Segment Order Index]
		, COUNT(1) RecordCount

		, SUM(COALESCE(FTS.[SUM Function Planned Total Cost Adjusted], 0)) AS [Calc Total SUM Function Planned Total Cost Adjusted]
		, SUM(COALESCE(FTS.[SUM Task Planned Total Units], 0)) AS [Calc Total SUM Task Planned Total Units]
		, SUM(COALESCE(FTS.[SUM Function Planned Total Hours], 0)) AS [Calc Total SUM Function Planned Total Hours]
		, SUM(COALESCE(FTS.[SUM Task Period Approved Total Units], 0))	AS [Calc Total SUM Task Period Approved Total Units]
		, SUM(COALESCE(FTS.[SUM Task Approved Total Units], 0))	AS [Calc Total SUM Task Approved Total Units]

		, SUM(COALESCE(FTS.[SUM Function TimeSheet Actual Total Hours CT], 0)) AS [Calc Total SUM Function TimeSheet Actual Total Hours CT]
		, SUM(COALESCE(FTS.[SUM Function TimeSheet Actual Total Hours NCT], 0)) AS [Calc Total SUM Function TimeSheet Actual Total Hours NCT]

		, SUM(COALESCE(case when FTS.[Actual Total Hours (Allocated)] <= 0 then 0 else FTS.[Actual Total Hours (Allocated)] end, 0)) AS [Calc Total Actual Total Hours (Allocated)]

		, SUM(COALESCE(FTS.[SUM Task Period Approved Total Units], 0)) --  * FTS.[Calculated Unit Cost]) AS [Calc Total Earned Value (Budget)]
					* [dbo].[udfDivide](SUM(COALESCE(FTS.[SUM Function Planned Total Cost Adjusted], 0)), SUM(COALESCE(FTS.[SUM Task Planned Total Units], 0))) AS [Calc Total Earned Value (Budget)]
		--, sum([SUM Function Original TimeSheet Actual Total Hours]) as [Calc SUM Function Original TimeSheet Actual Total Hours]
        , sum([Original Actual Total Hours (Allocated)]) as [Calc Original Actual Total Hours (Allocated)]
		, sum(COALESCE(case when FTS.[SUM Function Period Actual Cost] <= 0 then 0 else FTS.[SUM Function Period Actual Cost] end, 0)) as [Calc SUM Function Period Actual Cost]
		, sum(COALESCE(case when FTS.[SUM Function Actual Cost] <= 0 then 0 else FTS.[SUM Function Actual Cost] end, 0)) as [Calc SUM Function Actual Cost]

		, SUM(COALESCE(FTS.[SUM Function Actual Cost CT], 0))  AS [Calc Actual Cost (Allocated) CT]
		, SUM(COALESCE(FTS.[SUM Function Actual Cost NCT], 0)) AS [Calc Actual Cost (Allocated) NCT]

		, sum(COALESCE(case when FTS.[Actual Cost (Allocated)] <= 0 then 0 else FTS.[Actual Cost (Allocated)] end, 0)) as [Calc Actual Cost (Allocated)]
		, sum([Original Actual Cost (Allocated)]) as [Calc Original Actual Cost (Allocated)]

    FROM [STAGING_CADENCE].[CadenceCase0Data] FTS with (nolock)
    WHERE FTS.[Task Country Name] IN ('Global', 'No Country')
    GROUP BY 
		  FTS.[Period Year]
		, FTS.[Period Month]
		, FTS.[Project Name]	
		, FTS.[Task Code]
		, FTS.[Part Order Index]
		, FTS.[Segment Order Index]
		, FTS.[Task Country Name]

			
   
	
					
-- Create table with reacords aligned with aggregate total colunns  WHERE [Task Country Name] IN ('Global', 'No Country')
 IF OBJECT_ID(N'STAGING_CADENCE.MonthlyTaskTaskCountryGlobalNoCountry') IS NOT NULL
     TRUNCATE TABLE STAGING_CADENCE.MonthlyTaskTaskCountryGlobalNoCountry
    
insert 	INTO STAGING_CADENCE.MonthlyTaskTaskCountryGlobalNoCountry
    SELECT 
        CT.[Period Year]
		, CT.[Period Month]
		, CT.[Project Name]	
		, CT.[Project Currency Code]
		, CT.[Project Currency Name]	
		, CT.[Service]		
		, CT.[Task Code]
		, CT.[Task Name]			
		, CT.[Task Country Name]
		, CT.[Unit type]
		, CT.[Part Order Index]
		, CT.[Segment Order Index]
		, CT.[Function Code]
		, CT.[Function Name]		
		, CT.[Department]
		, CT.[Function Country Name]

		, CT.[Project Ref Id]
		, CT.[Archived Project Ref Id]
		, CT.[PRIMA Project Id]
		, CT.[Project Status]
		, CT.[Project Phase]
		, CT.[Is Deleted Task]
		, CT.[SUM Function Reconciliation Approved Units]
		, CT.[Task Period CADENCE Earned Value]
		, CT.[Task Reconciliation CADENCE Earned Value]
		, CT.[Task CADENCE Earned Value]
		, CT.[Task CADENCE Planned Unit Cost]
		, CASE WHEN CT.[RecordUpdateType] in ('NC', 'NCF', 'NCD', 'NCB')
					THEN  CT.[SUM Function TimeSheet Actual Total Hours NCT] 
					ELSE  CT.[SUM Function TimeSheet Actual Total Hours CT] 
		  END AS [SUM Function TimeSheet Period Actual Total Hours]
		, CT.[SUM Task Period Approved Total Units]
		--, CT.[SUM Function TimeSheet Actual Total Hours]

		, CT.[SUM Function Planned Total Cost Adjusted]
		, CT.[SUM Function Planned Total Hours]
		, CT.[Function CurrentRate Adjusted]
		, CT.[SUM Task Planned Total Units]
		, CT.[SUM Task Approved Total Units]

		, CT.[RecordUpdateType]
		, FTS.[RecordCount]

		, CASE WHEN CT.[RecordUpdateType] in ('NC', 'NCF', 'NCD', 'NCB')
					THEN FTS.[Calc Total SUM Function TimeSheet Actual Total Hours NCT] 
					ELSE FTS.[Calc Total SUM Function TimeSheet Actual Total Hours CT] 
		  END AS [Total SUM Function Period TimeSheet Actual Total Hours]
		--, FTS.[Total SUM Function TimeSheet Actual Total Hours]

		, FTS.[Calc Total SUM Function Planned Total Cost Adjusted] AS [Total SUM Function Planned Total Cost Adjusted]
		, FTS.[Calc Total SUM Task Planned Total Units] AS [Total SUM Task Planned Total Units]
		, FTS.[Calc Total SUM Function Planned Total Hours] AS [Total SUM Function Planned Total Hours]
		, FTS.[Calc Total SUM Task Period Approved Total Units]AS [Total SUM Task Approved Total Units]
		, FTS.[Calc Total Actual Total Hours (Allocated)]
		, CT.[Actual Total Hours (Allocated)]


		, COALESCE(CT.[SUM Task Period Approved Total Units], 0)-- * CT.[Calculated Unit Cost]
			* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0)) AS [Calc Earned Value (Budget)]
		, FTS.[Calc Total Earned Value (Budget)]

		--Calculated columns
		, case when CT.[Task Name] like '%Project Management%' 
				 	 then 0
				 	 else case when FTS.[Calc Total Actual Total Hours (Allocated)] = 0
							   then 0
							   else CASE WHEN CT.[Actual Total Hours (Allocated)] = 0 
										 THEN 0 
										 ELSE (COALESCE(CT.[SUM Task Period Approved Total Units], 0)  --* CT.[Calculated Unit Cost])
												* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
											-- * case when [dbo].[udfDivide](CT.[Actual Total Hours (Allocated)], CT.[SUM Task Period Approved Total Units]) <= ([dbo].[udfDivide](CT.[SUM Function Planned Total Hours], CT.[SUM Task Planned Total Units]) * 0.1) 
											* case when CT.[Calculated Approved Units] <= (CT.[Calculated Planned Units] * 0.1)
											 	    then 0 
											 	    else 0.5 
											   end 
									END
						  end
			end AS [Earned Value (50% Direct allocation)]

-- , [Earned Value (Direct allocation) Version-2]
, case when CT.[Task Name] like '%Project Management%' 
		 	 then 0
		 	 else case when FTS.[Calc Actual Cost (Allocated)] = 0
					   then 0
					   else CASE WHEN CT.[Actual Cost (Allocated)] = 0 
								 THEN 0 
								 ELSE (COALESCE(CT.[SUM Task Period Approved Total Units], 0)  --* CT.[Calculated Unit Cost])
										* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
									-- * case when [dbo].[udfDivide](CT.[Actual Total Hours (Allocated)], CT.[SUM Task Period Approved Total Units]) <= ([dbo].[udfDivide](CT.[SUM Function Planned Total Hours], CT.[SUM Task Planned Total Units]) * 0.1) 
									* case when CT.[Calculated Approved Units] <= (CT.[Calculated Planned Units] * 0.1)
									 	    then 0 
									 	    else 0.25 
									   end 
							END
				  end
	end AS [Earned Value (Direct allocation) Version-2]

		, (COALESCE(CT.[SUM Task Period Approved Total Units], 0) -- * CT.[Calculated Unit Cost])
			* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
		 - (case when CT.[Task Name] like '%Project Management%' 
				 	 then 0
				 	 else case when FTS.[Calc Total Actual Total Hours (Allocated)] = 0
							   then 0
							   else  CASE WHEN CT.[Actual Total Hours (Allocated)] = 0 
										  THEN 0 
										  ELSE (COALESCE(CT.[SUM Task Period Approved Total Units], 0)  --* CT.[Calculated Unit Cost])
												* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
											--	* case when [dbo].[udfDivide](CT.[Actual Total Hours (Allocated)], CT.[SUM Task Period Approved Total Units]) <= ([dbo].[udfDivide](CT.[SUM Function Planned Total Hours], CT.[SUM Task Planned Total Units]) * 0.1) 
											* case when CT.[Calculated Approved Units] <= (CT.[Calculated Planned Units] * 0.1)
											 	    then 0 
											 	    else 0.5 
											   end  
									 END
						  end
			end) AS [Non-allocated Earned Value]

-- , [Non-allocated Earned Value Version-2]
, (COALESCE(CT.[SUM Task Period Approved Total Units], 0) --* CT.[Calculated Unit Cost])
	* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
 - (case when CT.[Task Name] like '%Project Management%' 
		 	 then 0
		 	 else case when FTS.[Calc Actual Cost (Allocated)] = 0
					   then 0
					   else  CASE WHEN CT.[Actual Cost (Allocated)] = 0 
								  THEN 0 
								  ELSE (COALESCE(CT.[SUM Task Period Approved Total Units], 0)  --* CT.[Calculated Unit Cost])
										  * [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
										--* case when [dbo].[udfDivide](CT.[Actual Total Hours (Allocated)], CT.[SUM Task Period Approved Total Units]) <= ([dbo].[udfDivide](CT.[SUM Function Planned Total Hours], CT.[SUM Task Planned Total Units]) * 0.1) 
										* case when CT.[Calculated Approved Units] <= (CT.[Calculated Planned Units] * 0.1)
									 	    then 0 
									 	    else 0.25 
									   end  
							 END
				  end
	end) AS [Non-allocated Earned Value Version-2]


, Agg.[Calc Total Non-allocated Earned Value] AS [Calc Total Non-allocated Earned Value]
, Agg.[Calc Total Non-allocated Earned Value Version-2] AS [Calc Total Non-allocated Earned Value Version-2]        
		, CT.[SUM Function Period Actual Cost]
		, CT.[SUM Function Reconciliation Actual Cost]
		, CT.[SUM Function Actual Cost]
		--, CT.[SUM Function Original TimeSheet Actual Total Hours]
, CT.[Original Actual Total Hours (Allocated)]
	, FTS.[Calc SUM Function Period Actual Cost]
		, FTS.[Calc SUM Function Actual Cost]

, CT.[Actual Cost (Allocated)]
, CASE WHEN CT.[RecordUpdateType] in ('NC', 'NCF', 'NCD', 'NCB')
			THEN FTS.[Calc Actual Cost (Allocated) NCT] 
			ELSE FTS.[Calc Actual Cost (Allocated) CT] 
  END AS [Total Actual Cost (Allocated)]
, FTS.[Calc Actual Cost (Allocated)]

		, [dbo].[udfDivide](case when CT.[Actual Total Hours (Allocated)] <= 0 then 0 else CT.[Actual Total Hours (Allocated)] end, FTS.[Calc Total Actual Total Hours (Allocated)])	AS [TS hours proportion]
		, [dbo].[udfDivide](case when CT.[SUM Function Period Actual Cost] <= 0 then 0 else CT.[SUM Function Period Actual Cost] end, FTS.[Calc SUM Function Period Actual Cost])		AS [Actual Cost Proportion]
, [dbo].[udfDivide](case when CT.[Actual Cost (Allocated)] <= 0 then 0 else CT.[Actual Cost (Allocated)] end, FTS.[Calc Actual Cost (Allocated)])										AS [Actual Cost (Allocated) Proportion]

		--, case when [dbo].[udfDivide](CT.[Actual Total Hours (Allocated)], CT.[SUM Task Period Approved Total Units]) <= ([dbo].[udfDivide](CT.[SUM Function Planned Total Hours], CT.[SUM Task Planned Total Units]) * 0.1)
		, case when CT.[Calculated Approved Units] <= (CT.[Calculated Planned Units] * 0.1)
				then 'yes'
				else 'no'
		  end as [IsApprvedUnitLessThan10PercentPlannedUnits]
	,CT.[Calculated Approved Units]
	,CT.[Calculated Planned Units]
	,CT.[Calculated Unit Cost]	

    FROM [STAGING_CADENCE].[CadenceCase0Data] CT with (nolock)
        INNER JOIN [STAGING_CADENCE].[AggregatedCountryTotals] AS FTS with (nolock) ON	
				CT.[Period Year]		= FTS.[Period Year]
            AND CT.[Period Month]		= FTS.[Period Month]
            AND CT.[Project Name]		= FTS.[Project Name]
            AND CT.[Task Code]			= FTS.[Task Code]
            AND CT.[Part Order Index]	= FTS.[Part Order Index]
            AND CT.[Segment Order Index]= FTS.[Segment Order Index]
            AND CT.[Task Country Name] = FTS.[Task Country Name]
        INNER JOIN (
				SELECT
                      CT.[Period Year]
					, CT.[Period Month]
					, CT.[Project Name]		
					, CT.[Task Code]
					, CT.[Part Order Index]
					, CT.[Segment Order Index]
			        , CT.[Task Country Name]

					, SUM((COALESCE(CT.[SUM Task Period Approved Total Units], 0) --* CT.[Calculated Unit Cost])
							* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
						 - (case when CT.[Task Name] like '%Project Management%' 
							 	  then 0
							 	  else case when FTS.[Calc Total Actual Total Hours (Allocated)] = 0
											then 0
											else  CASE WHEN CT.[Actual Total Hours (Allocated)] = 0 
													   THEN 0 
													   ELSE (COALESCE(CT.[SUM Task Period Approved Total Units], 0) --* CT.[Calculated Unit Cost])
													   	* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
														--* case when [dbo].[udfDivide](CT.[Actual Total Hours (Allocated)], CT.[SUM Task Period Approved Total Units]) <= ([dbo].[udfDivide](CT.[SUM Function Planned Total Hours], CT.[SUM Task Planned Total Units]) * 0.1) 
														* case when CT.[Calculated Approved Units] <= (CT.[Calculated Planned Units] * 0.1)
															   then 0 
															   else 0.5 
														  end
												  END
										end
							  end )
							) AS [Calc Total Non-allocated Earned Value]

, SUM((COALESCE(CT.[SUM Task Period Approved Total Units], 0) --* CT.[Calculated Unit Cost])
		* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
	 - (case when CT.[Task Name] like '%Project Management%' 
		 	  then 0
		 	  else case when FTS.[Calc Actual Cost (Allocated)] = 0
						then 0
						else  CASE WHEN CT.[Actual Cost (Allocated)] = 0 
								   THEN 0 
								   ELSE (COALESCE(CT.[SUM Task Period Approved Total Units], 0) --* CT.[Calculated Unit Cost])
								   	* [dbo].[udfDivide](COALESCE(CT.[SUM Function Planned Total Cost Adjusted], 0), COALESCE(CT.[SUM Task Planned Total Units], 0))) 
									--* case when [dbo].[udfDivide](CT.[Actual Total Hours (Allocated)], CT.[SUM Task Period Approved Total Units]) <= ([dbo].[udfDivide](CT.[SUM Function Planned Total Hours], CT.[SUM Task Planned Total Units]) * 0.1) 
									* case when CT.[Calculated Approved Units] <= (CT.[Calculated Planned Units] * 0.1)
										   then 0 
										   else 0.25 
									  end
							  END
					end
		  end )
		) AS [Calc Total Non-allocated Earned Value Version-2]

        FROM [STAGING_CADENCE].[CadenceCase0Data] CT with (nolock)
            INNER JOIN [STAGING_CADENCE].[AggregatedCountryTotals] AS FTS with (nolock) ON	
					CT.[Period Year]		= FTS.[Period Year]
                AND CT.[Period Month]		= FTS.[Period Month]
                AND CT.[Project Name]		= FTS.[Project Name]
                AND CT.[Task Code]			= FTS.[Task Code]
                AND CT.[Part Order Index]	= FTS.[Part Order Index]
                AND CT.[Segment Order Index]= FTS.[Segment Order Index]
                AND CT.[Task Country Name] = FTS.[Task Country Name]
        WHERE CT.[Task Country Name] IN ('Global', 'No Country')
        GROUP BY 
				  CT.[Period Year]
				, CT.[Period Month]
				, CT.[Project Name]		
				, CT.[Task Code]
				, CT.[Part Order Index]
				, CT.[Segment Order Index]
				, CT.[Task Country Name]
			)  Agg ON	
                CT.[Period Year]		= Agg.[Period Year]
            AND CT.[Period Month]		= Agg.[Period Month]
            AND CT.[Project Name]		= Agg.[Project Name]
            AND CT.[Task Code]			= Agg.[Task Code]
            AND CT.[Part Order Index]	= Agg.[Part Order Index]
            AND CT.[Segment Order Index]= Agg.[Segment Order Index]
            AND CT.[Task Country Name]  = Agg.[Task Country Name]
    WHERE CT.[Task Country Name] IN ('Global', 'No Country') 




EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[MonthlyTaskTaskCountryGlobalNoCountry] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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