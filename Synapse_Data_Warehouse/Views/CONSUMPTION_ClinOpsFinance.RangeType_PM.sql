CREATE VIEW [CONSUMPTION_ClinOpsFinance].RangeType_PM
AS  SELECT TOP 1000000  [RangeTypeID] AS RangeTypeID
      ,RangeCloseType AS [RangeCloseType]
FROM CONSUMPTION_ClinOpsFinance.[RangeType]
WHERE RangeTypeID = 1
ORDER BY RangeTypeID
