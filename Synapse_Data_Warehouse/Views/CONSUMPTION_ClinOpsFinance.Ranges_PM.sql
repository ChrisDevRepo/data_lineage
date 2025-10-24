CREATE VIEW [CONSUMPTION_ClinOpsFinance].Ranges_PM
AS  SELECT TOP 1000000  [RangeID] AS Rank
      ,[RangeLabel] AS [Last X Years]
      ,RangeBeginDateID AS RankBeginDateID
      ,RangeEndDateID AS RankEndDateID 
FROM [CONSUMPTION_ClinOpsFinance].[Ranges]
WHERE RangeTypeID = 1
ORDER BY RangeID