CREATE PROC [CONSUMPTION_FINANCE].[spLoadArAnalyticsMetricsETL] AS
BEGIN
 SET NOCOUNT ON; 
 
 EXEC [CONSUMPTION_FINANCE].[spLoadSAPSalesSummary];
 EXEC [CONSUMPTION_FINANCE].[spLoadSAPSalesDetails];

-- Metrics
 EXEC [CONSUMPTION_FINANCE].[spLoadSAPSalesSummaryMetrics];
 EXEC [CONSUMPTION_FINANCE].[spLoadSAPSalesDetailsMetrics];
 EXEC [CONSUMPTION_FINANCE].[spLoadSAPSalesRetainerDetailsMetrics];
 EXEC [CONSUMPTION_FINANCE].[spLoadSAPSalesInterestSummaryMetrics];

--Dims
 EXEC [CONSUMPTION_FINANCE].[spLoadDimCustomers];
 EXEC [CONSUMPTION_FINANCE].[spLoadDimProjects];
 EXEC [CONSUMPTION_FINANCE].[spLoadDimCustomersProjects];

--Facts
 EXEC [CONSUMPTION_FINANCE].[spLoadFact_SAP_Sales_Summary];
 EXEC [CONSUMPTION_FINANCE].[spLoadFact_SAP_Sales_Details];
 EXEC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesInterestSummary];
 EXEC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesRetainerDetails];

 EXEC [CONSUMPTION_FINANCE].[spLoadQuarterRanges];

 --Aggregations
EXEC [CONSUMPTION_FINANCE].[spLoadArAnalyticsMetrics];
 EXEC [CONSUMPTION_FINANCE].[spLoadArAnalyticsDetailMetrics];
 EXEC [CONSUMPTION_FINANCE].[spLoadArAnalyticsMetricsQuarterlyGlobal]
 EXEC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskInterestQuarterly];
 EXEC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskRetainerQuarterly];
 EXEC [CONSUMPTION_FINANCE].[spLoadFactSAPSalesSponsorRiskSnapshot];
END