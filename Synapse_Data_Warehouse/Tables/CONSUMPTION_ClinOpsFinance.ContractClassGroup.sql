CREATE TABLE [CONSUMPTION_ClinOpsFinance].ContractClassGroup
(
  ContractClassGroupID SMALLINT
  ,ContractClassGroupName VARCHAR(100)
)
WITH
(
	DISTRIBUTION = REPLICATE,
	CLUSTERED INDEX (ContractClassGroupID)
)
GO

