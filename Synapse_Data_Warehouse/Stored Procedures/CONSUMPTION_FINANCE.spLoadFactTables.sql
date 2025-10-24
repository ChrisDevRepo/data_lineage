CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactTables] AS

begin

exec CONSUMPTION_FINANCE.spLoadGLCognosData;
exec CONSUMPTION_FINANCE.spLoadFactGLCOGNOS;
exec CONSUMPTION_FINANCE.spLoadFactGLSAP;
exec CONSUMPTION_FINANCE.spLoadFactAgingSAP;
exec CONSUMPTION_POWERBI.spLoadFactLaborCostForEarnedValue_1;
exec CONSUMPTION_POWERBI.spLoadFactLaborCostForEarnedValue_2;
exec CONSUMPTION_POWERBI.spLoadFactAggregatedLaborCost;

end
GO
