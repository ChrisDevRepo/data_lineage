CREATE TABLE [CONSUMPTION_ClinOpsFinance].ContractClassGroupMembers
(
  ContractClassGroupMembersID SMALLINT
  ,ContractClassGroupID SMALLINT
  ,ContractClassGroupMembersName VARCHAR(100)
)
WITH
(
	DISTRIBUTION = REPLICATE,
	CLUSTERED INDEX (ContractClassGroupMembersID)
)
GO

