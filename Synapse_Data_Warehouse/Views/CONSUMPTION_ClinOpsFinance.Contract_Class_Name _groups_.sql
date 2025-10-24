CREATE VIEW [CONSUMPTION_ClinOpsFinance].[Contract_Class_Name (groups)]
AS 
SELECT TOP 10000 CCG.ContractClassGroupID, 
  CCGM.ContractClassGroupMembersID, 
  CCG.ContractClassGroupName, 
  CCGM.ContractClassGroupMembersName
FROM [CONSUMPTION_ClinOpsFinance].ContractClassGroup CCG
JOIN [CONSUMPTION_ClinOpsFinance].ContractClassGroupMembers CCGM
  ON CCG.ContractClassGroupID = CCGM.ContractClassGroupID
ORDER BY CCG.ContractClassGroupName, CCGM.ContractClassGroupMembersName
