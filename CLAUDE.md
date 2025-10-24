# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains SQL scripts for an Azure Synapse Analytics data warehouse implementation. The codebase is organized into stored procedures, tables, and views across multiple schemas that support finance, clinical operations, and reporting workloads.

## Repository Structure

All database objects are located in `Synapse_Data_Warehouse/` with three main directories:
- `Stored Procedures/` - ETL and data processing procedures
- `Tables/` - Table definitions
- `Views/` - View definitions

## Schema Architecture

The data warehouse uses a layered architecture with distinct schemas for different purposes:

### STAGING Schemas
- **STAGING_CADENCE**: Staging tables for Cadence system data processing
  - Contains intermediate tables for country reallocation, reconciliation, and task/function mapping
  - Includes specialized logic for handling "No Country" and "Global" scenarios

### CONSUMPTION Schemas
- **CONSUMPTION_FINANCE**: Finance domain consumption layer
  - Dimension tables (DimProjects, DimCustomers, DimAccount, etc.)
  - Fact tables (FactGLSAP, FactGLCognos, FactAgingSAP, etc.)
  - SAP sales analysis tables and metrics
  - AR (Accounts Receivable) analytics tables

- **CONSUMPTION_ClinOpsFinance**: Clinical Operations Finance integration
  - Cadence budget data processing
  - Labor cost and earned value calculations
  - Employee contract utilization tracking
  - Productivity metrics
  - Junction tables for mapping Cadence departments to Prima departments

- **CONSUMPTION_POWERBI**: Tables optimized for Power BI reporting
  - Aggregated labor cost fact tables

- **CONSUMPTION_PRIMA**: Prima system data
  - Site events and enrollment plans
  - Currency exchange rates
  - Global country mappings

- **CONSUMPTION_PRIMAREPORTING**: Prima reporting views
  - HR supervisor hierarchies
  - Timesheet aggregations

## Key Patterns and Conventions

### Stored Procedure Naming
- Procedures follow pattern: `[Schema].[spLoad{TargetTable}]`
- Master procedures orchestrate multiple child procedures (e.g., `spLoadDimTables` calls individual dimension loaders)
- Suffixes indicate processing stage:
  - `_Post` - Post-processing operations
  - `_Aggregations` - Aggregation calculations
  - `_ETL` - Extract, Transform, Load operations

### Error Handling and Logging
All procedures use a standard pattern:
```sql
BEGIN TRY
    -- Logging start with dbo.LogMessage
    -- Main processing logic
    -- Logging completion with dbo.LogMessage
END TRY
BEGIN CATCH
    -- Error capture and logging with dbo.LogMessage
    -- RAISERROR to propagate error
END CATCH
```

Key logging components:
- `dbo.LogMessage` - Centralized logging stored procedure
- `dbo.spLastRowCount` - Captures affected row counts
- Log levels: INFO, ERROR

### Table Distribution Strategies
Tables use Azure Synapse-specific distribution:
- `DISTRIBUTION = REPLICATE` - For small dimension tables
- `DISTRIBUTION = HASH([columns])` - For large fact tables with specific distribution keys
- `CLUSTERED COLUMNSTORE INDEX` - Default for fact tables
- `HEAP` - For some dimension tables

### Temporal Tracking
Tables consistently include audit columns:
- `CreatedAt` / `CREATED_AT`
- `UpdatedAt` / `UPDATED_AT`
- `CreatedBy` / `UpdatedBy`

### Data Processing Patterns

**Truncate and Load**: Most consumption tables use TRUNCATE then INSERT pattern for full refresh

**Complex ETL with Temp Tables**: Large procedures (e.g., `spLoadCadenceBudgetData`) use:
1. Temporary tables with hash distribution for intermediate results
2. Multiple UNION operations to combine different data scenarios
3. Currency conversion joins to `MonthlyAverageCurrencyExchangeRate`
4. Department mapping with `PrimaDepartmentCount` for proportional allocation
5. Final UPDATE statements to adjust calculated fields

**Earned Value Calculations**: The Cadence budget processing includes sophisticated earned value methodology:
- Direct allocation (50% or 25% based on version)
- Indirect allocation based on proportions
- Special handling for "Project Management" tasks
- Multiple calculation versions (Version-2) for comparison

## Common Development Commands

Since this is a SQL-only repository for Azure Synapse, there are no build or test commands. Development workflow:

1. **Modify SQL scripts** in the appropriate directory
2. **Deploy to Synapse** using Azure Data Studio, SSMS, or Azure DevOps pipelines
3. **Test stored procedures** by executing them in Synapse with appropriate parameters
4. **Verify table structures** match distribution and indexing requirements

## Important Notes

### Country and Department Handling
- The system handles multiple scenarios: standard countries, "Global", "No Country"
- Department mapping uses `Full_Departmental_Map` to map Cadence departments to Prima departments
- A single Cadence department can map to multiple Prima departments, requiring proportional allocation via `PrimaDepartmentCount`

### Currency Conversion
- Uses `CONSUMPTION_PRIMA.MonthlyAverageCurrencyExchangeRate` table
- Supports CHF, GBP, USD, EUR as target currencies
- Applied via `COALESCE(cur.[Rate], 1)` pattern (defaults to 1.0 if no rate found)

### Record Update Types
Special handling for different record types:
- Standard records (default)
- 'OOS' - Out of Scope Service records
- 'REC' - Reconciliation records
- 'BKF' - Backfill records (exclude from Actual Cost of Work Performed)

### Table Hints
Procedures commonly use `with (nolock)` for read operations to avoid blocking
