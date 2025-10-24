CREATE PROC [CONSUMPTION_PRIMA].[spLoadDWH] AS
BEGIN

EXEC [CONSUMPTION_PRIMA].[spLoadEnrollmentPlanSitesHistory]
EXEC [CONSUMPTION_PRIMA].[spLoadMonthlyAverageCurrencyExchangeRate]
EXEC [CONSUMPTION_PRIMA].[spLoadSiteEvents_DurationByDay]
EXEC [CONSUMPTION_PRIMA].[spLoadSiteEvents_DurationByDayPlanned]

END
