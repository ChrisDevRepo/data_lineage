CREATE PROC [CONSUMPTION_ClinOpsFinance].[spLoadDateRangeDetails] @MonthToClose DATETIME, @CloseDate DATETIME, @Today DATETIME, @YearsToGoBack SMALLINT, @RangeCloseType VARCHAR(10) AS
BEGIN

-- Re-loads the [CONSUMPTION_ClinOpsFinance].DateRanges on the basis of the passed in parameter values.
--    @MonthToClose is the date of the month that is being considered for closing
--    @CloseDate is the date on which the @MonthToClose can be considered closed
--    @Today is generally Today, but parameterized for testing.  If @Today >= @CloseDate then @MonthToClose is considered closed
--          otherwise the prior month is considered to be the last month closed
--    @YearsToGoBack number or closed period year ranges to go back
--    @RangeCloseType - Month or QTR - determines if Ranges are Closed Months or Closed Quarters

-- EXEC [CONSUMPTION_ClinOpsFinance].[spLoadDateRangeDetails] @MonthToClose = '2023-01-01' , @CloseDate = '2023-02-15' , @Today = '2023-02-15' , @YearsToGoBack = 5, @RangeCloseType = 'Month' 
-- SELECT * FROM [CONSUMPTION_ClinOpsFinance].DateRanges_PM
-- SELECT TOP (100) * FROM [ADMIN].[Logs] WHERE CallSite = 'ClinicalOperationsFinance' AND ProcessName = '[CONSUMPTION_ClinOpsFinance].[spLoadDateRangeDetails]'  order by CreateDateTimeUTC desc

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
  ,@ProcShortName NVARCHAR(128) = 'spLoadDateRangeDetails'
DECLARE @ProcName NVARCHAR(128) = '[CONSUMPTION_ClinOpsFinance].['+@ProcShortName+']'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )
  ,@CallSite VARCHAR(255) = 'ClinicalOperationsFinance'
  ,@ErrorMsg NVARCHAR(2048) = ''
DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
  ,@AffectedRecordCount BIGINT = 0

BEGIN TRY

DECLARE  @RangeTypeID SMALLINT
  ,@MonthToCloseQTRBeginDate DATETIME 
  ,@MonthToCloseQTREndDate DATETIME
  ,@LatestClosedMonth DATETIME

DECLARE @RangeLabelPost VARCHAR(30) = ' year'
  ,@RangeCount SMALLINT
  ,@RangeLabel VARCHAR(100)
  ,@RangeLabelPre VARCHAR(50)
  ,@RangeLabePost VARCHAR(50)
  ,@RangeBeginMonth DATETIME
  ,@RangeEndMonth DATETIME
  ,@RangeEndDate DATETIME
  ,@RangeRank SMALLINT = 1 -- 1 is first year, 2 is first and second, 3 is first, secondC:\Source\Repos\SynapseDatabases\Synapse_Data_Warehouse\Stored Procedures and thrid, etc...
  ,@MonthCount SMALLINT = 1
  ,@QtrCount SMALLINT = 1
  ,@MonthID INT = 0 
  ,@MonthStart DATETIME
  ,@MonthEnd DATETIME
  ,@WorkDate DATETIME  -- this is the date variable that keeps getting decremented
  ,@DateDifference SMALLINT

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

SELECT @MSG = '@MonthToClose: ' +  ISNULL(CAST(@MonthToClose AS VARCHAR(30)),'NULL')
    + ', @CloseDate: ' +  ISNULL(CAST(@CloseDate AS VARCHAR(30)),'NULL')
    + ', @Today: ' +  ISNULL(CAST(@Today AS VARCHAR(30)),'NULL') 
    + ', @YearsToGoBack: ' +  ISNULL(CAST( @YearsToGoBack AS VARCHAR(30)),'NULL') 
    + ', @RangeCloseType: ' +  ISNULL(CAST( @RangeCloseType AS VARCHAR(30)),'NULL')
    ;

IF @MonthToClose IS NULL OR @CloseDate IS NULL OR @Today IS NULL OR @YearsToGoBack IS NULL OR @RangeCloseType IS NULL 
BEGIN
  SELECT @ErrorMsg = 'Parameter value is null check: ' + @MSG
    ;

  PRINT @ErrorMsg;

  THROW 200000, @ErrorMsg, 1;
END
ELSE 
BEGIN
  SELECT @MSG = 'Parameter values: ' + @MSG
  EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
END 
SELECT @MSG = ''

IF @Today < @MonthToClose
BEGIN
  SELECT @ErrorMsg =  '@Today: ' +  ISNULL(CAST(@Today AS VARCHAR(30)),'NULL') + ' Must be > @MonthToClose: ' +  ISNULL(CAST(@MonthToClose AS VARCHAR(30)),'NULL')

  PRINT @ErrorMsg;

  THROW 200100, @ErrorMsg, 1;

END

IF dbo.udfDateToBomDate(@CloseDate) <= @MonthToClose
BEGIN
  SELECT @ErrorMsg =  '@CloseDate: ' +  ISNULL(CAST(@CloseDate AS VARCHAR(30)),'NULL') + ' can not be in same or earlier month than @MonthToClose: ' +  ISNULL(CAST(@MonthToClose AS VARCHAR(30)),'NULL')

  PRINT @ErrorMsg;

  THROW 200100, @ErrorMsg, 1;

END
IF @RangeCloseType NOT IN ('Month','Qtr')
BEGIN
  SELECT @ErrorMsg = 'Parameter @RangeCloseType value is not Month or Qtr: ' +  ISNULL(CAST(@RangeCloseType AS VARCHAR(30)),'NULL')

  PRINT @ErrorMsg;

  THROW 200200, @ErrorMsg, 1;

END

SELECT  @Today = ISNULL(@Today,GETDATE()), 
  @YearsToGoBack = ISNULL(@YearsToGoBack,5), 
  @RangeCloseType = ISNULL(@RangeCloseType,'Month')

 --SELECT @CloseDay AS CloseDay, @Today AS Today, @YearsToGoBack AS  YearsToGoBack  , @RangeCloseType AS RangeCloseType

SELECT @RangeTypeID = RangeTypeID
FROM [CONSUMPTION_ClinOpsFinance].RangeType
WHERE RangeCloseType = @RangeCloseType

-- Range Close type is currently Month and QTR 
IF @RangeCloseType = 'Month'
BEGIN

  SELECT @RangeLabelPre = 'Last '
    ,@RangeLabelPost = ' year'

  IF @Today >=  @CloseDate
  BEGIN
    SELECT @LatestClosedMonth = @MonthToClose;
  END
  ELSE
  BEGIN
    SELECT @LatestClosedMonth = DATEADD(MONTH, -1, @MonthToClose);
  END

END
ELSE
BEGIN 

  SELECT @MonthToCloseQTRBeginDate = DATEADD(QUARTER,DATEDIFF(QUARTER, 0, @MonthToClose),0) 
  SELECT @MonthToCloseQTREndDate = DATEADD(QUARTER,DATEDIFF(QUARTER, 0, @MonthToClose) +1,0)

  SELECT @RangeLabelPre = 'Last '
   ,@RangeLabelPost = ' Closed Quarters'

  IF @Today >= @CloseDate AND @Today >= @MonthToCloseQTREndDate
  BEGIN
    SELECT @LatestClosedMonth = @MonthToCloseQTRBeginDate; -- last month in last  QTR
  END
  ELSE
  BEGIN
    SELECT @LatestClosedMonth = DATEADD(MONTH,-4,@MonthToCloseQTRBeginDate); -- last month 2 QTRs back
  END
END

-- Clear maintained tables for the Range type being run
DELETE FROM [CONSUMPTION_ClinOpsFinance].Ranges
WHERE RangeTypeID = @RangeTypeID;

DELETE FROM [CONSUMPTION_ClinOpsFinance].DateRanges
WHERE RangeTypeID = @RangeTypeID;

-- Loop through the number of Ranges
SELECT @RangeRank = 1

WHILE @RangeRank <= @YearsToGoBack -- Year Range Loop
BEGIN
-- Counting down months
  SELECT @MonthCount = @RangeRank * 12 -- number of months in a Date Range - 1 has 12, 2 has 24, ... 5 has 60
    ,@QtrCount = @RangeRank * 4 -- number of qtrs in a Date Range
    ,@WorkDate = @LatestClosedMonth -- Initialize WorkDate which will be incremented by month in month loop

  IF @RangeCloseType = 'Month'
    SELECT @RangeCount = @RangeRank
  ELSE 
    SELECT @RangeCount = @QtrCount

  SELECT @RangeLabel = @RangeLabelPre + CAST(@RangeCount AS VARCHAR(10)) + @RangeLabelPost
    ,@RangeEndMonth = DATEADD(month, DATEDIFF(month, 0, @WorkDate), 0)
    ,@RangeBeginMonth =  DATEADD(month, -1*(@MonthCount-1), DATEADD(month, DATEDIFF(month, 0, @WorkDate), 0))

  SELECT @RangeEndDate = DATEADD(millisecond,-2,DATEADD(month, DATEDIFF(month, 0, @RangeEndMonth)+1, 0)) --Get last day of EndMonth

  PRINT 'Range: ' + @RangeLabel
    + ', Range Type: ' + @RangeCloseType 
    + ' ,RangeBeginMonth: ' + CAST(@RangeBeginMonth AS VARCHAR(30))
    + ' ,RangeEndMonth: ' + CAST(@RangeEndDate AS VARCHAR(30))

  INSERT INTO [CONSUMPTION_ClinOpsFinance].Ranges
  (RangeID, RangeTypeID, RangeLabel, RangeBeginDateID, RangeBegin, RangeEndDateID, RangeEnd) 
  SELECT @RangeRank, @RangeTypeID, @RangeLabel, dbo.udfDateToBOMDateKey(@RangeBeginMonth),@RangeBeginMonth, dbo.udfDateToDateKey(@RangeEndDate),@RangeEndDate

  -- loop down through the number of months in the range  
  WHILE @MonthCount >= 1 -- Months in Year Range loop: will increment down to the first month 
  BEGIN

    SELECT @MonthID = dbo.udfDateToBOMDateKey(@WorkDate) --DATEDIFF(MONTH, 0 , @WorkDate)
      ,@MonthStart = DATEADD(MONTH, DATEDIFF(MONTH, 0, @WorkDate), 0) --AS StartOfMonth
      ,@MonthEnd = DATEADD(millisecond,-2,DATEADD(MONTH, DATEDIFF(MONTH, 0, @WorkDate)+1, 0))--AS EndOfMonth
      ,@DateDifference = DATEDIFF(MONTH,@Today,@WorkDate)

    PRINT '    In Month: ' + CAST(@MonthCount AS VARCHAR(10)) 
      + ', Range Type: ' + @RangeCloseType 
      + ', For Range: ' + CAST(@RangeRank AS VARCHAR(10)) 
      + ', MonthID: ' + CAST(@MonthID AS VARCHAR(10)) 
      + ', Month Start: ' + CAST(@MonthStart AS VARCHAR(50)) 
      + ', Month End: ' + CAST(@MonthEnd AS VARCHAR(50)) 
      + ', Range: ' + @RangeLabel
      + ', DateDifference: ' + CAST(@DateDifference AS VARCHAR(50)) 

    INSERT INTO [CONSUMPTION_ClinOpsFinance].DateRanges
    (RangeID, RangeTypeID, RangeLabel, MonthID, MonthStart, MonthEnd, DateDifference)
    SELECT @RangeRank, @RangeTypeID, @RangeLabel, @MonthID, @MonthStart, @MonthEnd, @DateDifference

-- Increment down months
    SELECT @MonthCount = @MonthCount - 1, @WorkDate = DATEADD(month,-1,@WorkDate)
  END

  IF @RangeLabelPost =  ' year'
    SELECT @RangeLabelPost =  ' years';

-- counting up year ranges
  SELECT @RangeRank = @RangeRank + 1
END

SELECT @MSG  = 'End Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = @CallSite, @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL

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
