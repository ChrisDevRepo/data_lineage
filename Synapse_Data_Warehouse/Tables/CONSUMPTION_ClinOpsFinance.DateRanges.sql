CREATE TABLE [CONSUMPTION_ClinOpsFinance].DateRanges
 (
  RangeID SMALLINT
  ,RangeTypeID INT
  ,RangeLabel VARCHAR(50)
  ,MonthID INT
  ,MonthStart DATETIME
  ,MonthEnd DATETIME
  ,DateDifference SMALLINT
)
WITH
(
	DISTRIBUTION = REPLICATE,
	CLUSTERED INDEX (RangeID,MonthID DESC)
)
GO
