CREATE VIEW [CONSUMPTION_ClinOpsFinance].[vCadenceDepartments]
AS SELECT DISTINCT TOP 100000 CadenceDepartmentID, CadenceDepartmentName
FROM [CONSUMPTION_ClinOpsFinance].vFull_Departmental_Map_ActivePrima
ORDER BY CadenceDepartmentName;
GO


