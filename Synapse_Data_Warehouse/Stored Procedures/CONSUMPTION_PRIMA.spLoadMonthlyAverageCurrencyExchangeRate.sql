CREATE PROC [CONSUMPTION_PRIMA].[spLoadMonthlyAverageCurrencyExchangeRate] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname               NVARCHAR(128) = '[CONSUMPTION_PRIMA].[spLoadMonthlyAverageCurrencyExchangeRate]'
DECLARE @procid  VARCHAR(100) = ( SELECT OBJECT_ID(@procname))

/*-------------------------------------------------------------------------------*/
BEGIN TRY

-- ************** For Logging And Alerts  ************************
DECLARE @MSG					VARCHAR(max)  = 'Start Time:' 
											  +  CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) 
											  + ' ' + @ProcName
DECLARE @AffectedRecordCount	BIGINT = 0
DECLARE @ProcessId				BIGINT
DECLARE @RowsInTargetBegin		BIGINT
DECLARE @RowsInTargetEnd		BIGINT
DECLARE @StartTime              DATETIME 
DECLARE @EndTime                DATETIME 

SET @RowsInTargetBegin			= (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate])
SET @StartTime                  = GETDATE()

RAISERROR (@MSG ,0,0) 
-- ****************************************************************

TRUNCATE TABLE [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate]

	
INSERT INTO [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate]
(
	[Year],
	[Month],
	[FromCurrency],
	[ToCurrency],
	[Rate],
	[CREATED_AT], 
	[UPDATED_AT]
)
SELECT 
	AA.rate_year, 
	AA.rate_month, 
	CURRENCY_ID1,
	CURRENCY_ID2,
	AVG(AA.ask) as Rate
	,getdate()
	,getdate()
FROM 
	(
		SELECT 
			year(r.RATE_DATE) as rate_year,
			month(r.RATE_DATE) as rate_month,
			CURRENCY_ID1,
			CURRENCY_ID2,
			r.ask 
		FROM 
			[CONSUMPTION_PRIMA].[GlobalCurrencyRates] r
	) AA

GROUP BY
	AA.rate_year, 
	AA.rate_month,
	AA.CURRENCY_ID1,
	AA.CURRENCY_ID2


exec  [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedRecordCount output

SET @RowsInTargetEnd        = (SELECT COUNT(*) FROM [CONSUMPTION_PRIMA].[MonthlyAverageCurrencyExchangeRate])
SET @EndTime                = GETDATE()
SET	@MSG                    = @MSG + ': New Rows Processed = ' 
							+ CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' 
							+ CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30))  + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 



END TRY
/*----------------------------------------------------------------------*/
BEGIN CATCH

DECLARE @ErrorNum int, @ErrorLine int  ,@ErrorSeverity int ,@ErrorState int
DECLARE @ErrorProcedure nvarchar(126) ,@ErrorMessage nvarchar(2048) 


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

	SET	@MSG	= @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') 
	EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'DWH PRIMA ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
	RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 


END CATCH
 

END
