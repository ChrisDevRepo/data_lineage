CREATE VIEW [CONSUMPTION_ClinOpsFinance].[vFull_Departmental_Map_ActivePrima]
AS
SELECT FDM.*
FROM DBO.Full_Departmental_Map FDM
LEFT JOIN CONSUMPTION_PRIMA.HrDepartments HrD
ON FDM.PrimaDepartmentID = Hrd.Department_ID
-- to remove a department that is causing duplicates
WHERE HrD.Record_Active = 1
UNION
-- to add back in a needed inactive department
SELECT * FROM DBO.Full_Departmental_Map
WHERE PrimaDepartmentName = 'Marketing & Events Management';
