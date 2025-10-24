CREATE PROC [CONSUMPTION_FINANCE].[spLoadArAnalyticsMetricsQuarterlyGlobal] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadArAnalyticsMetricsQuarterlyGlobal]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )

BEGIN TRY

DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[ArAnalyticsMetricsQuarterlyGlobal])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [CONSUMPTION_FINANCE].[ArAnalyticsMetricsQuarterlyGlobal];

begin transaction

insert into [CONSUMPTION_FINANCE].[ArAnalyticsMetricsQuarterlyGlobal]
select 
    q.[YearQuarter],
    qt.[FilterValue],
    q.[DaysInQuarter],
    SUM([EndingArChf]) as [EndingArChf],
    SUM([RevenueChf]) as [RevenueChf],
    SUM([ModifiedArChf]) as [ModifiedARBalance],    
    dbo.udfDivide(SUM([EndingArChf]) * [DaysInQuarter] , SUM([RevenueChf])) as [Dso],
    dbo.udfDivide(SUM([ModifiedArChf]) * [DaysInQuarter] , SUM([RevenueChf])) as [DSOBestCase],
    (dbo.udfDivide(SUM([EndingArChf]) * [DaysInQuarter] , SUM([RevenueChf]))
    - dbo.udfDivide(SUM([ModifiedArChf]) * [DaysInQuarter] , SUM([RevenueChf]))) as [DSOVariance],
    'spLoadArAnalyticsMetricsQuarterlyGlobal' as [CreatedBy],
    'spLoadArAnalyticsMetricsQuarterlyGlobal' as [UpdatedBy],
    getdate() as [CreatedAt],
    getdate() as [UpdatedAt]
From
    (
        select  
            [YearQuarter], [Year], [Month], [QuarterOfTheYear], [FirstDayOfQuarter], [LastDayOfQuarter], DATEDIFF(day, [FirstDayOfQuarter], [LastDayOfQuarter]) + 1 as [DaysInQuarter],
            ROW_NUMBER() OVER(ORDER BY AA.[Year] desc, AA.[QuarterOfTheYear] desc) as QuarterNumber
        FROM
        (
            select CONCAT(f.Year, '-Q', dod.[Quarter]) as [YearQuarter], f.[Year], f.[Month], dod.[Quarter] as [QuarterOfTheYear], dod.[FirstDayOfQuarter], dod.[LastDayOfQuarter] 
            from [CONSUMPTION_FINANCE].[COGNOS_PowerBIFacts] f
                left join [dbo].[DimDate] dod on dod.[Date] = DATEFROMPARTS(f.[Year], f.[Month], 1)
            where dod.LastDayOfQuarter < FORMAT(GetDate(), 'd', 'en-US') 
        ) AA

        group by  AA.yearQuarter, AA.Year, AA.Month, AA.QuarterOfTheYear, AA.FirstDayOfQuarter, AA.LastDayOfQuarter 
    ) q

left join 
    (
	    select 
              CONCAT(dod.[Year], '-Q', dod.[Quarter])   as yearquarter
            , SUM(COALESCE(f.[ChfNetAmountTc], 0))      as [ChfNetAmountTc]
	    from
            [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Summary] f 
            left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
            left join [dbo].[DimDate] dud on dud.[DimDateKey] = f.[DimDueDateKey]
            left join [dbo].[DimDate] pid on pid.[DimDateKey] = f.[DimPaidDateKey]
	    where
	        NetAmountTC <> 0 
        AND dod.[Date]      <= dod.LastDayOfQuarter 
        AND dud.[Date]      >  dod.LastDayOfQuarter 
        AND (pid.[Date]     >  dod.LastDayOfQuarter or pid.[Date] IS NULL)
	    group by 
            CONCAT(dod.[Year], '-Q', dod.[Quarter])
    ) sm ON sm.yearquarter = q.yearquarter
left join
(select 
CONCAT(dod.[Year], '-Q', dod.[Quarter])   as yearquarter
, SUM(COALESCE(f.[CHFTotalAmountTC], 0))      as [ModifiedArChf]
from
[CONSUMPTION_FINANCE].[Fact_SAP_Sales_Details] f 
left join [dbo].[DimDate] dod on dod.[DimDateKey] = f.[DimDocumentDateKey]
left join [dbo].[DimDate] dud on dud.[DimDateKey] = f.[DimDueDateKey]
left join [dbo].[DimDate] pid on pid.[DimDateKey] = f.[DimPaidDateKey]
where
 dod.[Date]      <= dod.LastDayOfQuarter 
AND dud.[Date]      >  dod.LastDayOfQuarter 
AND (pid.[Date]     >  dod.LastDayOfQuarter or pid.[Date] IS NULL)
and f.Account in (select distinct ColumnValue from [CONSUMPTION_FINANCE].[DataFilters] where [Tablename] = 'ArAnalyticsMetricsQuarterlyGlobal-Md/Ed' and ColumnName = 'Account'and IncludeExclude = 'Include' )	
group by 
CONCAT(dod.[Year], '-Q', dod.[Quarter])
)mr ON mr.yearquarter = q.yearquarter

join (  select f.[Year], f.[Month], SUM(COALESCE(f.[LocalAmountPTD], 0)) as [RevenueChf]
        from [CONSUMPTION_FINANCE].[COGNOS_PowerBIFacts] f 
        where f.Account in (select distinct ColumnValue from [CONSUMPTION_FINANCE].[DataFilters] where [Tablename] = 'ArAnalyticsMetricsQuarterlyGlobal-Revenue' and ColumnName = 'Account')
            and f.[Year] >= 2024
            and f.company = 'LE100' 
            and actuality = 'AC'
            and currency = 'CHF'
        group by f.[Year], f.[Month]
        UNION ALL
        select f.[Year], f.[Month], SUM(COALESCE(f.[LocalAmountPTD], 0)) as [RevenueChf]
        from [CONSUMPTION_FINANCE].[COGNOS_PowerBIFacts] f 
        where f.Account in (select distinct ColumnValue from [CONSUMPTION_FINANCE].[DataFilters] where [Tablename] = 'ArAnalyticsMetricsQuarterlyGlobal-Revenue' and ColumnName = 'Account')
            and f.[Year] < 2024
            and f.company  = 'FL0001' 
            and actuality = 'AC'
            and currency = 'CHF'
        group by f.[Year], f.[Month]
      ) RQ on  RQ.[Year] =q.[Year] 
           and RQ.[Month] = q.[Month]
left join [CONSUMPTION_FINANCE].[QuarterRanges] qt on qt.[YearQuarter] = q.[YearQuarter]
left join (     select qt.YearQuarter as [yearquarter], SUM(COALESCE(s.[CHFTotalAmountTC], 0))  as [EndingArChf], qt.filtervalue
			  from [CONSUMPTION_FINANCE].[QuarterRanges] qt 
                    left join(
					select s.account,CONCAT(dod.[Year], '-Q', dod.[Quarter])   as yearquarter, dod.LastDayOfQuarter, s.[CHFTotalAmountTC],s.NetAmountTC, pid.[Date] as Paiddate, dod.date as Documentdate
					from [CONSUMPTION_FINANCE].[Fact_SAP_Sales_Details] s 
					left join [dbo].[DimDate] dod on dod.[DimDateKey] = s.[DimDocumentDateKey]
					left join [dbo].[DimDate] pid on pid.[DimDateKey] = s.[DimPaidDateKey]
					) s
					on s.[Documentdate] <= qt.[LastDayOfTheQuarter] 	
				where
						(s.Paiddate    > qt.LastDayOfTheQuarter or s.Paiddate IS NULL)	and 
						s.Account in (select distinct ColumnValue from [CONSUMPTION_FINANCE].[DataFilters] where [Tablename] = 'ArAnalyticsMetricsQuarterlyGlobal-Md/Ed' and ColumnName = 'Account'and IncludeExclude = 'Include' )					
        		group by  qt.YearQuarter,qt.filtervalue
				) EQAR on 
				 EQAR.yearquarter = qt.yearquarter
				 And EQAR.FilterValue = qt.filtervalue
group by q.[YearQuarter], qt.[FilterValue], q.[DaysInQuarter]


	

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Details_Metrics])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

rollback transaction

DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048) 

--store all the error information for logging the error
SELECT @ErrorNum       = ERROR_NUMBER() 
      ,@ErrorLine      = 0
      ,@ErrorSeverity  = ERROR_SEVERITY()
      ,@ErrorState     = ERROR_STATE()
      ,@ErrorProcedure = ERROR_PROCEDURE()
      ,@ErrorMessage   = ERROR_MESSAGE()

SET @MSG = @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') 
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH

END
GO
