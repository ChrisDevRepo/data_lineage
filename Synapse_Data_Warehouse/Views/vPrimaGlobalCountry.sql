CREATE VIEW [CONSUMPTION_ClinOpsFinance].[vPrimaGlobalCountry] AS SELECT DISTINCT TOP 100000 [PrimaGlobalCountryName]
FROM [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc]
WHERE [PrimaGlobalCountryName] IS NOT NULL
ORDER BY [PrimaGlobalCountryName];