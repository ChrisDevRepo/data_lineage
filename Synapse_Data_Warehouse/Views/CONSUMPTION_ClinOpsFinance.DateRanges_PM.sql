CREATE VIEW [CONSUMPTION_ClinOpsFinance].DateRanges_PM
AS  SELECT TOP 1000000  [RangeID] AS Rank
      ,[RangeLabel] AS [Last X Years]
      ,[MonthID] AS DateID
      ,[MonthStart] AS Date
      ,dbo.udfDateToDateKey([MonthEnd]) AS MonthEndDateID
      ,[DateDifference] AS DateDifference
FROM [CONSUMPTION_ClinOpsFinance].[DateRanges]
WHERE RangeTypeID = 1
ORDER BY RangeID, DateID DESC
go