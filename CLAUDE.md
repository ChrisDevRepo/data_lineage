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

## Data Lineage Analysis Tools

This repository includes autonomous data lineage tools for reverse-engineering SQL dependencies.

### Autonomous Lineage Engine

**Location**: `autonomous_lineage.py`

**Purpose**: Automatically generates complete data lineage from any database object (table, view, or stored procedure) by analyzing SQL code.

**Usage**:
```bash
python3 autonomous_lineage.py <object_name>
```

**Examples**:
```bash
# Analyze a table
python3 autonomous_lineage.py CadenceBudgetData

# Analyze a stored procedure
python3 autonomous_lineage.py spLoadEmployeeContractUtilization_Aggregations

# With full schema qualification
python3 autonomous_lineage.py CONSUMPTION_ClinOpsFinance.CadenceBudgetData
```

**Output Files**:
- `{object}_lineage.json` - Complete lineage in strict JSON format (see JSON_FORMAT_SPECIFICATION.md)
- `{object}_confidence.json` - Analysis quality report with confidence scores

**Key Features**:
- **Fully Autonomous**: No manual approvals required
- **Hybrid Analysis**: Combines regex parsing + AI analysis for complex SQL patterns
- **Circular Dependency Tracking**: Detects when SPs both read and write to the same table
- **Confidence Scoring**: Provides reliability metrics for each detected dependency
- **Validation**: Cross-checks all dependencies against actual codebase
- **Logging Exclusion**: Automatically filters out logging objects (ADMIN.Logs, dbo.LogMessage, dbo.spLastRowCount)

### JSON Lineage Format (Version 2.0)

Each object in the lineage has:
```json
{
  "id": "node_0",
  "name": "ObjectName",
  "schema": "SchemaName",
  "object_type": "Table|View|StoredProcedure",
  "inputs": ["node_1", "node_2"],
  "outputs": ["node_3", "node_4"]
}
```

**Lineage Rules**:

**Stored Procedures**:
- `inputs`: Tables/views it READS from (FROM, JOIN clauses)
- `outputs`: Tables it WRITES to (INSERT, UPDATE, SELECT INTO, MERGE, TRUNCATE)

**Tables**:
- `inputs`: Stored procedures that WRITE to it
- `outputs`: Always empty `[]`

**Views**:
- `inputs`: Tables/views it READS from
- `outputs`: Always empty `[]`

**Circular Dependencies**:
A stored procedure can appear in both `inputs` and `outputs` of a table when it both creates and reads from that table within the same execution.

**Complete Specification**: See `JSON_FORMAT_SPECIFICATION.md` for detailed format documentation.

### Architecture Components

The lineage engine consists of modular components:

**Parsers** (`parsers/`):
- `sql_parser_enhanced.py` - Regex-based SQL parsing with confidence scoring
- `dependency_extractor.py` - Extracts all SQL dependency types

**AI Analyzer** (`ai_analyzer/`):
- `sql_complexity_detector.py` - Detects complex patterns needing AI review
- `ai_sql_parser.py` - Handles MERGE, CTEs, dynamic SQL, PIVOT/UNPIVOT
- `confidence_scorer.py` - Combines regex + AI results with weighted confidence

**Validators** (`validators/`):
- `dependency_validator.py` - Verifies objects exist in codebase
- `iterative_refiner.py` - Uses Grep/Glob to find missing dependencies

**Output** (`output/`):
- `json_formatter.py` - Generates strict JSON format
- `confidence_reporter.py` - Creates analysis quality reports

### Common Lineage Patterns

**1. Source Tables**: Tables with no inputs (no SP writes to them)
```json
{
  "id": "node_1",
  "name": "HrContractAttendance",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "Table",
  "inputs": [],
  "outputs": []
}
```

**2. ETL Stored Procedures**: Read from source tables, write to target tables
```json
{
  "id": "node_0",
  "name": "spLoadCadenceBudgetData",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "StoredProcedure",
  "inputs": ["node_1", "node_2"],    // Source tables
  "outputs": ["node_3"]               // Target table
}
```

**3. Views**: Read from tables, don't write
```json
{
  "id": "node_2",
  "name": "vFull_Departmental_Map_ActivePrima",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "View",
  "inputs": ["node_4", "node_5"],    // Base tables
  "outputs": []
}
```

**4. Target Tables**: Written to by SPs
```json
{
  "id": "node_3",
  "name": "CadenceBudgetData",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "Table",
  "inputs": ["node_0"],              // SP that creates it
  "outputs": []
}
```

**5. Circular Dependencies**: SP both reads and writes same table
```json
{
  "id": "node_0",
  "name": "spLoadEmployeeContractUtilization_Aggregations",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "StoredProcedure",
  "inputs": ["node_3"],              // Reads from EmployeeContractFTE_Monthly
  "outputs": ["node_3"]              // Also writes to it (CIRCULAR!)
}
```

### Performance Characteristics

- **Simple objects** (1-10 dependencies): ~5-10 seconds
- **Complex objects** (50+ dependencies): ~20-30 seconds
- **Large dependency trees** (100+ objects): ~30-60 seconds

The engine automatically handles:
- CTEs (Common Table Expressions)
- Temp tables (unwrapped to source tables)
- Dynamic SQL (basic pattern detection)
- MERGE statements
- Complex joins and subqueries
- Cross-schema dependencies

### Troubleshooting Lineage Analysis

**Low Confidence Scores** (< 0.7):
- Review uncertain dependencies in confidence report
- Check for dynamic SQL or complex patterns
- Consider manual verification of flagged dependencies

**Invalid Dependencies**:
- May indicate temp tables created at runtime
- Could reference objects in external databases
- Check if object names are dynamically constructed

**Missing Objects**:
- Object may be created via `SELECT INTO` within a stored procedure
- Analyze the stored procedure that creates it instead
- Use the confidence report to identify creation source
