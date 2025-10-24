CREATE PROC [CONSUMPTION_FINANCE].[spLoadDimTables] AS

begin

exec CONSUMPTION_FINANCE.spLoadDimConsType;
exec CONSUMPTION_FINANCE.spLoadDimAccount;
exec CONSUMPTION_FINANCE.spLoadDimCurrency;
exec CONSUMPTION_FINANCE.spLoadDimActuality;
exec CONSUMPTION_FINANCE.spLoadDimCompany;
exec CONSUMPTION_FINANCE.spLoadDimCompanyKoncern;
exec CONSUMPTION_FINANCE.spLoadDimDepartment;
exec CONSUMPTION_FINANCE.spLoadDimPosition;
exec CONSUMPTION_FINANCE.spLoadDimAccountDetailsCognos;
exec CONSUMPTION_FINANCE.spLoadDimAccountDetailsSAP;

end