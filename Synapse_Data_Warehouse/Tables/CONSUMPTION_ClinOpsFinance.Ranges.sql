CREATE TABLE [CONSUMPTION_ClinOpsFinance].Ranges
(
  RangeID SMALLINT
  ,RangeTypeID INT
  ,RangeLabel VARCHAR(50)
  ,RangeBeginDateID INT
  ,RangeBegin DATETIME
  ,RangeEndDateID INT
  ,RangeEnd DATETIME
)
WITH
(
	DISTRIBUTION = REPLICATE,
	CLUSTERED INDEX (RangeID)
)

GO
