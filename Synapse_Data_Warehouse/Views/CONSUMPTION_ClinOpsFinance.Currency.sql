CREATE VIEW [CONSUMPTION_ClinOpsFinance].[Currency] 
AS 
SELECT * FROM CONSUMPTION_FINANCE.DimCurrency WHERE Currency in ('CHF','EUR','GBP','USD')
