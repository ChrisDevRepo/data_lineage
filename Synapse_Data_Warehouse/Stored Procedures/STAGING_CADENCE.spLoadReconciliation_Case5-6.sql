CREATE PROC [STAGING_CADENCE].[spLoadReconciliation_Case5-6]
AS

BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadReconciliation_Case5-6'
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





-- ************************
-- ***** USE CASE 5/6 *****
-- ************************

IF OBJECT_ID(N'STAGING_CADENCE.ReconciliationCalc') IS NOT NULL
BEGIN
        TRUNCATE TABLE [STAGING_CADENCE].[ReconciliationCalc]
    END

insert into [STAGING_CADENCE].[ReconciliationCalc]
    select
          rc.[Project Name]
		, rc.[Period Year]
		, rc.[Period Month]
		, rc.[Data Period Year] 
		, rc.[Data Period Month]
		, rc.[Project Currency Code]
		, rc.[Project Currency Name]
		, rc.[Service]
		, rc.[Task Code]
		, rc.[Part Order Index]
		, rc.[Segment Order Index]
		, rc.[Task Name]
		, rc.[Task Country Name]
		, rc.[Function Code]
		, rc.[Function Name]
		, rc.[Function Country Name]
		, rc.[Department]
		, rc.[Unit type]
		, rc.[RecordUpdateType]
		, rc.[Project Ref Id]
		, rc.[Archived Project Ref Id]
		, rc.[PRIMA Project Id]
		, rc.[Project Status]
		, rc.[Project Phase]
		, rc.[Is Deleted Task]
		, rc.[SUM Function Reconciliation Approved Units]
		, rc.[Task Period CADENCE Earned Value]
		, rc.[Task Reconciliation CADENCE Earned Value]
		, rc.[Task CADENCE Earned Value]
		, rc.[Task CADENCE Planned Unit Cost]
		, rc.[SUM Function Planned Total Cost Adjusted]
		, cal.[Calc SUM Function Planned Total Cost Adjusted]
		, rc.[Function CurrentRate Adjusted]
		, rc.[SUM Task Planned Total Units] 
		, rc.[SUM Task Approved Total Units]
		, rc.[SUM Function Reconciliation TimeSheet Actual Total Hours]
		, rc.[SUM Function Actual Hours]
		, cal.[Calc SUM Function Reconciliation Actual Hours]
		, rc.[SUM Task Reconciliation Actual Cost]
		, cal.[Calc SUM Function Actual Cost]
		, rc.[SUM Function Actual Cost]
		, cal.[Calc SUM Function Reconciliation Actual Cost]
		, rc.[SUM Function Reconciliation Actual Cost]
		, ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) as [Budget Proportion]
		, ISNULL((case when rc.[SUM Function Reconciliation TimeSheet Actual Total Hours] <= 0 then 0 else rc.[SUM Function Reconciliation TimeSheet Actual Total Hours] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Hours], 0)), 0) as [TS hours proportion]
		--, ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0) as [Actual Cost Proportion]
		, ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0) as [Actual Cost Proportion]

		, case when [Task Name] like '%Project Management%'
				then case when cal.[Calc SUM Function Actual Cost] = 0 
							then ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0)
							--else ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0)
							else ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0)
					end
				--else ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) 
				else case when cal.[Calc SUM Function Actual Cost] = 0 
							then ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0)
							--else ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0)
							else ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0)
					end
		  end
        * rc.[Task Reconciliation CADENCE Earned Value] as [Earned Value (Budget)]

		, case when [Task Name]	 like '%Project Management%'
				then 0
				else case when cal.[Calc SUM Function Reconciliation Actual Hours] = 0
						  then 0
						  else case  when rc.[SUM Function Reconciliation TimeSheet Actual Total Hours] = 0 
									 then 0 
									 else  ( ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) 
                                           * rc.[Task Reconciliation CADENCE Earned Value]
										   * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end ) 
							   end
					 end
		  end as [Earned Value (50% Direct allocation)]


		, case when [Task Name]	 like '%Project Management%'
				then 0
				else case when cal.[Calc SUM Function Actual Cost] = 0
						  then 0
						  else case  when rc.[SUM Function Actual Cost] = 0 
									 then 0 
									 --else  ( ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) 
									 else  ( case when cal.[Calc SUM Function Actual Cost] = 0 
													then ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0)
													--else ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0)
													else ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0)
											end
                                           * rc.[Task Reconciliation CADENCE Earned Value]
										   * case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end ) 
							   end
					 end
		  end as [Earned Value (Direct allocation) Version-2]


		, (case when [Task Name] like '%Project Management%'
				then case when cal.[Calc SUM Function Reconciliation Actual Cost] = 0 
							then ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0)
							--else ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0)
							else ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0)
					end
				else ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) 
		   end
           * rc.[Task Reconciliation CADENCE Earned Value])
		  -	(case when [Task Name]	like '%Project Management%'
				 then 0
				 else case when cal.[Calc SUM Function Reconciliation Actual Hours] = 0
					  then 0
				 	  else	case  when rc.[SUM Function Reconciliation TimeSheet Actual Total Hours] = 0 
				 					then 0 
				 					else  (ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) 
                                            * rc.[Task Reconciliation CADENCE Earned Value]
											* case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.5 end ) 
				 			end
					  end
			 end ) as [Non-allocated Earned Value]

		, (case when [Task Name] like '%Project Management%'
				then case when cal.[Calc SUM Function Actual Cost] = 0 
							then ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0)
							--else ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0)
							else ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0)
					end
				--else ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) 
				else case when cal.[Calc SUM Function Actual Cost] = 0 
							then ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0)
							--else ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0)
							else ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0)
					end
		   end
          * rc.[Task Reconciliation CADENCE Earned Value])
		  -	(case when [Task Name]	like '%Project Management%'
				 then 0
				 else case when cal.[Calc SUM Function Actual Cost] = 0
					  then 0
				 	  else	case  when rc.[SUM Function Actual Cost] = 0 
				 					then 0 
				 					--else  (ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0) 
									else  (case when cal.[Calc SUM Function Actual Cost] = 0 
													then ISNULL((case when rc.[SUM Function Planned Total Cost Adjusted] <= 0 then 0 else rc.[SUM Function Planned Total Cost Adjusted] end / NULLIF( cal.[Calc SUM Function Planned Total Cost Adjusted], 0)), 0)
													--else ISNULL((case when rc.[SUM Function Reconciliation Actual Cost] <= 0 then 0 else rc.[SUM Function Reconciliation Actual Cost] end / NULLIF( cal.[Calc SUM Function Reconciliation Actual Cost], 0)), 0)
													else ISNULL((case when rc.[SUM Function Actual Cost] <= 0 then 0 else rc.[SUM Function Actual Cost] end / NULLIF( cal.[Calc SUM Function Actual Cost], 0)), 0)
											end
                                            * rc.[Task Reconciliation CADENCE Earned Value]
											* case when [IsApprvedUnitLessThan10PercentPlannedUnits] = 'yes' then 0 else 0.25 end ) 
				 			end
					  end
			 end ) as [Non-allocated Earned Value Version-2]

		, rc.[IsApprvedUnitLessThan10PercentPlannedUnits]

		, rc.[From Period]
		, rc.[To Period]
		, GetUtcDate() as [CREATED_AT]					 
		, GetUtcDate() as [UPDATED_AT]
    from
        [STAGING_CADENCE].[ReconciliationPopulation] rc with (nolock)
        inner join
        (
			select
            [Project Name]
				, [Period Year]
				, [Period Month]
				, [Task Code]
				, [Part Order Index]
				, [Segment Order Index]
				, [Task Country Name]
				, sum(case when [SUM Function Planned Total Cost Adjusted] < 0 then 0 else [SUM Function Planned Total Cost Adjusted] end)	as [Calc SUM Function Planned Total Cost Adjusted]
				, sum(case when [SUM Function Reconciliation TimeSheet Actual Total Hours] < 0 then 0 else [SUM Function Reconciliation TimeSheet Actual Total Hours] end)	as [Calc SUM Function Reconciliation Actual Hours]
				, sum(case when [SUM Function Reconciliation Actual Cost] < 0 then 0 else [SUM Function Reconciliation Actual Cost] end)	as [Calc SUM Function Reconciliation Actual Cost]
				, sum(case when [SUM Function Actual Cost] < 0 then 0 else [SUM Function Actual Cost] end)	as [Calc SUM Function Actual Cost]
            from
                [STAGING_CADENCE].[ReconciliationPopulation] with (nolock)
            group by
                [Project Name]
                , [Period Year]
                , [Period Month]
                , [Task Code]
                , [Part Order Index]
                , [Segment Order Index]
                , [Task Country Name]
		) cal on 
			(
				rc.[Project Name]			= cal.[Project Name]
            and rc.[Period Year]			= cal.[Period Year]
            and rc.[Period Month]			= cal.[Period Month]
            and rc.[Task Code]				= cal.[Task Code]
            and rc.[Part Order Index]		= cal.[Part Order Index]
            and rc.[Segment Order Index]	= cal.[Segment Order Index]
            and rc.[Task Country Name]		= cal.[Task Country Name]
			)





IF OBJECT_ID(N'STAGING_CADENCE.ReconciliationEV') IS NOT NULL
BEGIN
        TRUNCATE TABLE [STAGING_CADENCE].[ReconciliationEV]
    END

insert into [STAGING_CADENCE].[ReconciliationEV]
    select
        rc.[Project Name]
		, rc.[Period Year]
		, rc.[Period Month]
		, rc.[Data Period Year] 
		, rc.[Data Period Month]
		, rc.[Project Currency Code]
		, rc.[Project Currency Name]
		, rc.[Service]
		, rc.[Task Code]
		, rc.[Part Order Index]
		, rc.[Segment Order Index]
		, rc.[Task Name]
		, rc.[Task Country Name]
		, rc.[Function Code]
		, rc.[Function Name]
		, rc.[Function Country Name]
		, rc.[Department]
		, rc.[Unit type]
		, rc.[RecordUpdateType]
		, rc.[Project Ref Id]
		, rc.[Archived Project Ref Id]
		, rc.[PRIMA Project Id]
		, rc.[Project Status]
		, rc.[Project Phase]
		, rc.[Is Deleted Task]
		, rc.[SUM Function Reconciliation Approved Units]
		, rc.[Task Period CADENCE Earned Value]
		, rc.[Task Reconciliation CADENCE Earned Value]
		, rc.[Task CADENCE Earned Value]
		, rc.[Task CADENCE Planned Unit Cost]
		, rc.[SUM Function Planned Total Cost Adjusted]
		, rc.[Calc SUM Function Planned Total Cost Adjusted]
		, rc.[Function CurrentRate Adjusted]
		, rc.[SUM Task Planned Total Units] 
		, rc.[SUM Task Approved Total Units]
		, rc.[SUM Function Reconciliation TimeSheet Actual Total Hours]
		, rc.[SUM Function Actual Hours]
		, rc.[Calc SUM Function Reconciliation Actual Hours]
		, rc.[SUM Task Reconciliation Actual Cost]
		, rc.[SUM Function Actual Cost]
		, rc.[Calc SUM Function Reconciliation Actual Cost]
		, rc.[SUM Function Reconciliation Actual Cost]
		, rc.[Budget Proportion]		as [Budget Proportion]	
		, rc.[TS hours proportion]		as [TS hours proportion]	
		, rc.[Actual Cost Proportion]	as [Actual Cost Proportion]

		, rc.[Earned Value (Budget)]
		, rc.[Earned Value (50% Direct allocation)]

        , rc.[Earned Value (Direct allocation) Version-2]
		, rc.[Non-allocated Earned Value]

        , rc.[Non-allocated Earned Value Version-2]

		, cal.[Calc Non-allocated Earned Value]								as [Total Indirect Earned Value (Task)]
        
        , cal.[Non-allocated Earned Value Version-2]                        as [Total Indirect Earned Value (Task) Version-2]

		, cal.[Calc Non-allocated Earned Value] 
			*	case when rc.[Task Name] like '%Project Management%' 
					 then rc.[Actual Cost Proportion] 
					 else rc.[TS hours proportion]	
				end															as [Earned Value (Indirect allocation)]

	    , cal.[Non-allocated Earned Value Version-2] * rc.[Actual Cost Proportion] as [Earned Value (Indirect allocation) Version-2]

		, case when ((rc.[Task Name] not like '%Project Management%' and [Calc SUM Function Reconciliation Actual Hours] = 0 ) or (rc.[Task Name] like '%Project Management%' and [Calc SUM Function Reconciliation Actual Cost] = 0 ))
			then rc.[Earned Value (Budget)] 
				+ rc.[Earned Value (50% Direct allocation)] 
				+ (
					cal.[Calc Non-allocated Earned Value] * 
						case when rc.[Task Name] like '%Project Management%' 
							 then rc.[Actual Cost Proportion] 
							 else rc.[TS hours proportion]	
						end
				  )	
			else
				rc.[Earned Value (50% Direct allocation)] 
				+ (
					cal.[Calc Non-allocated Earned Value] * 
						case when rc.[Task Name]	 like '%Project Management%' 
							 then rc.[Actual Cost Proportion] 
							 else rc.[TS hours proportion]	
						end
				  )		end													as [Earned Value (Total Allocated)]															
				
	    --, case when ((rc.[Task Name] not like '%Project Management%' and [Calc SUM Function Reconciliation Actual Hour] = 0 ) or (rc.[Task Name] like '%Project Management%' and [Calc SUM Function Reconciliation Actual Cost] = 0 ))
		, case	when (rc.[Task Name] like '%Project Management%' and [Calc SUM Function Actual Cost] = 0 )
	    			then rc.[Earned Value (Budget)] 
	    		when (rc.[Task Name] like '%Project Management%' and [Calc SUM Function Actual Cost] <> 0 )
		    		then (cal.[Non-allocated Earned Value Version-2] * rc.[Actual Cost Proportion])		
				when (rc.[Task Name] not like '%Project Management%' and [Calc SUM Function Actual Cost] = 0 )
					then rc.[Earned Value (Direct allocation) Version-2]  + rc.[Non-allocated Earned Value Version-2]
				else 
					rc.[Earned Value (Direct allocation) Version-2] + (cal.[Non-allocated Earned Value Version-2] * rc.[Actual Cost Proportion])	
          end                                                             as [Earned Value (Total Allocated) Version-2]	

		, rc.[From Period]
		, rc.[To Period]
		, GetUtcDate() as [CREATED_AT]					 
		, GetUtcDate() as [UPDATED_AT]

    from
        [STAGING_CADENCE].[ReconciliationCalc] rc with (nolock)
        inner join
        (
			select
            [Period Year],
            [Period Month],
            [Project Name],
            [Task Code],
            [Part Order Index],
            [Segment Order Index],
            [Task Country Name],
            sum([Non-allocated Earned Value])           as [Calc Non-allocated Earned Value],
            sum([Non-allocated Earned Value Version-2]) as [Non-allocated Earned Value Version-2]
        from
            [STAGING_CADENCE].[ReconciliationCalc] with (nolock)
        group by
				[Period Year],
				[Period Month],
				[Project Name],
				[Task Code],
				[Part Order Index],
				[Segment Order Index],
				[Task Country Name]
		) cal on
			(
				rc.[Project Name]			= cal.[Project Name]
            and rc.[Period Year]			= cal.[Period Year]
            and rc.[Period Month]			= cal.[Period Month]
            and rc.[Task Code]				= cal.[Task Code]
            and rc.[Part Order Index]		= cal.[Part Order Index]
            and rc.[Segment Order Index]	= cal.[Segment Order Index]
            and rc.[Task Country Name]		= cal.[Task Country Name]
			)



EXEC [dbo].[spLastRowCount] @Count = @Count output
SET @AffectedRecordCount = @Count + @AffectedRecordCount

SELECT @MSG  = 'Completed load of [STAGING_CADENCE].[ReconciliationEV] in ' + CAST(DATEDIFF(second, @ProcessingTime, GETDATE()) AS VARCHAR(10)) + ' Seconds' ;
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