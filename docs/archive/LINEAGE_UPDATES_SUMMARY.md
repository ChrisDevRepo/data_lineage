# Data Lineage Updates Summary

## Date: 2025-10-24

## Overview

Major updates to the autonomous data lineage engine to properly handle circular dependencies and track both read and write operations.

---

## Problem Identified

The initial implementation had a critical flaw:

### Issue 1: Missing "outputs" Field
**Problem**: Stored procedures only tracked what they READ from (inputs), not what they WRITE to.

**Example**:
```sql
-- spLoadEmployeeContractUtilization_Aggregations
SELECT ... INTO [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly  -- WRITES
FROM [CONSUMPTION_ClinOpsFinance].HrContractAttendance                     -- READS
```

**Old JSON** (WRONG):
```json
{
  "name": "spLoadEmployeeContractUtilization_Aggregations",
  "inputs": ["HrContractAttendance"],
  "outputs": NOT PRESENT ❌
}
```

### Issue 2: Circular Dependencies Not Visible
**Problem**: Some stored procedures both CREATE a table and then READ from it in later queries within the same execution.

**Example**:
```sql
-- Line 119: Creates the table
SELECT ... INTO [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly

-- Line 156: Reads from the table it just created
SELECT ... FROM [CONSUMPTION_ClinOpsFinance].EmployeeContractFTE_Monthly
```

This circular dependency was invisible in the old format!

### Issue 3: Logging Objects Included
**Problem**: Logging tables like `ADMIN.Logs` appeared in lineage, cluttering the output.

---

## Solution Implemented

### 1. Added "outputs" Field

**New JSON Format (Version 2.0)**:
```json
{
  "id": "node_0",
  "name": "spLoadEmployeeContractUtilization_Aggregations",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "StoredProcedure",
  "inputs": [
    "node_1",  // HrContractAttendance (reads from)
    "node_3"   // EmployeeContractFTE_Monthly (reads from)
  ],
  "outputs": [
    "node_3",  // EmployeeContractFTE_Monthly (writes to) ← CIRCULAR!
    "node_8",  // Employee_Day_Hours (writes to)
    "node_9"   // EmployeeAttendanceExpectedHoursUtilization_Monthly (writes to)
  ]
}
```

Notice: `node_3` appears in BOTH `inputs` AND `outputs` - this is the circular dependency!

### 2. Complete Lineage Logic

#### For Stored Procedures:
- **inputs**: All tables/views it READS from
  - Extracted from: FROM, JOIN, EXISTS clauses
  - CTEs unwrapped to source tables
  - Temp tables resolved to source tables

- **outputs**: All tables it WRITES to
  - Extracted from: INSERT INTO, UPDATE, SELECT INTO, MERGE INTO, TRUNCATE TABLE
  - Temp tables excluded
  - Logging tables excluded

#### For Tables:
- **inputs**: Stored procedures that WRITE to it
- **outputs**: Always empty `[]`

#### For Views:
- **inputs**: Tables/views it READS from
- **outputs**: Always empty `[]`

### 3. Logging Objects Excluded

Automatically filtered:
- `ADMIN.Logs`
- `dbo.LogMessage`
- `dbo.spLastRowCount`

### 4. Schema-Qualified Lookups

Internal tracking uses full qualified names: `schema.object_name`

Ensures uniqueness when same table name exists in multiple schemas:
- `CONSUMPTION_ClinOpsFinance.Employee`
- `STAGING_CADENCE.Employee`
- `DBO.Employee`

---

## Test Results

### Test Case: spLoadEmployeeContractUtilization_Aggregations

**Execution Time**: 34.13 seconds
**Objects Discovered**: 91
**Confidence Score**: 0.935 (EXCELLENT)

#### Verified Outputs:

The stored procedure correctly shows it WRITES to 10 tables:
1. `EmployeeAttendanceExpectedHoursUtilization_Monthly`
2. `EmployeeContractFTE_Monthly` ← Also in inputs (circular!)
3. `AverageContractFTE_Monthly`
4. `AverageContractFTE_Monthly_RankDetail`
5. `BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation`
6. `Employee_Day_Hours`
7. `EmployeeTimeSheetHours_Utilization`
8. `Employee_Utilization_Hours`
9. `EmployeeAverageFTE_Monthly_Utilization_Hours`
10. `EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail`

#### Circular Dependency Verified:

**EmployeeContractFTE_Monthly** (node_3):
- ✅ Appears in SP's **inputs** (SP reads from it at line 156)
- ✅ Appears in SP's **outputs** (SP creates it at line 119)
- ✅ Table's **inputs** shows `["node_0"]` (the SP that writes to it)

This correctly represents the execution flow:
1. SP creates EmployeeContractFTE_Monthly (SELECT INTO)
2. SP later reads from EmployeeContractFTE_Monthly in subsequent query

---

## Files Updated

### Core Engine:
1. ✅ `autonomous_lineage.py`
   - Added output extraction for stored procedures
   - Updated lineage graph to include 'outputs' field
   - Enhanced table dependency fixing to track writers

### Formatters:
2. ✅ `output/json_formatter.py`
   - Added outputs field to JSON generation
   - Updated validation to require outputs field
   - Ensures outputs array is properly formatted

### Documentation:
3. ✅ `JSON_FORMAT_SPECIFICATION.md` (NEW)
   - Complete specification of JSON format v2.0
   - Field definitions and examples
   - Circular dependency explanation
   - Validation rules and script

4. ✅ `CLAUDE.md`
   - Added Data Lineage Analysis Tools section
   - Usage examples and patterns
   - Architecture component descriptions
   - Troubleshooting guide

5. ✅ `README_AUTONOMOUS_LINEAGE.md`
   - Comprehensive user guide (created earlier)

---

## Breaking Changes

### JSON Format Change

**Version 1.0** (OLD):
```json
{
  "id": "node_0",
  "name": "StoredProcedure",
  "schema": "Schema",
  "object_type": "StoredProcedure",
  "inputs": ["node_1"]
  // No outputs field
}
```

**Version 2.0** (NEW):
```json
{
  "id": "node_0",
  "name": "StoredProcedure",
  "schema": "Schema",
  "object_type": "StoredProcedure",
  "inputs": ["node_1"],
  "outputs": ["node_2"]  // ← NEW REQUIRED FIELD
}
```

**Migration**: All existing lineage JSON files need to be regenerated.

---

## Usage Examples

### Basic Usage:
```bash
# Generate lineage for any object
python3 autonomous_lineage.py CadenceBudgetData

# Output files:
# - CadenceBudgetData_lineage.json (with inputs + outputs)
# - CadenceBudgetData_confidence.json (quality report)
```

### Example Output:
```json
[
  {
    "id": "node_0",
    "name": "spLoadCadenceBudgetData",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "StoredProcedure",
    "inputs": [
      "node_1",  // MonthlyAverageCurrencyExchangeRate
      "node_2"   // vFull_Departmental_Map
    ],
    "outputs": [
      "node_3"   // CadenceBudgetData
    ]
  },
  {
    "id": "node_3",
    "name": "CadenceBudgetData",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "Table",
    "inputs": [
      "node_0"   // spLoadCadenceBudgetData creates it
    ],
    "outputs": []
  }
]
```

---

## Validation

### Validation Script:
```python
import json

def validate_lineage_v2(data):
    required_fields = {'id', 'name', 'schema', 'object_type', 'inputs', 'outputs'}

    for node in data:
        # Check all required fields present
        if not required_fields.issubset(node.keys()):
            return False

        # Tables and Views must have empty outputs
        if node['object_type'] in ['Table', 'View']:
            if node['outputs'] != []:
                return False

    return True

# Usage
with open('lineage.json') as f:
    data = json.load(f)
    print(f"Valid v2.0: {validate_lineage_v2(data)}")
```

---

## Benefits

### 1. Complete Data Flow Visibility
- See what SPs READ from (inputs)
- See what SPs WRITE to (outputs)
- Understand full data transformation pipeline

### 2. Circular Dependency Detection
- Identify when SPs both create and consume same tables
- Critical for understanding execution order
- Helps detect potential issues

### 3. Cleaner Output
- Logging objects automatically excluded
- Focus on actual data flow
- Reduced noise in lineage graphs

### 4. Better Analysis
- Confidence scoring remains intact
- Validation checks both inputs and outputs
- More accurate dependency tracking

---

## Known Limitations

### 1. Dynamic SQL
Tables constructed at runtime with variables cannot be reliably detected:
```sql
DECLARE @TableName VARCHAR(100) = 'MyTable_' + CONVERT(VARCHAR, GETDATE(), 112)
EXEC('SELECT * FROM ' + @TableName)  -- Cannot detect
```

### 2. External Dependencies
Objects in linked servers or external databases are not tracked:
```sql
SELECT * FROM [LinkedServer].[Database].[Schema].[Table]  -- Not tracked
```

### 3. Temp Tables
Temp tables (`#temp`) are excluded from outputs but resolved in inputs when possible.

---

## Future Enhancements

Potential improvements:
- [ ] Visualization of lineage graphs
- [ ] Impact analysis (what breaks if I change this?)
- [ ] Lineage comparison over time
- [ ] Web UI for interactive exploration
- [ ] Support for SSIS packages
- [ ] Cross-database dependency tracking

---

## References

- **JSON Format Spec**: `JSON_FORMAT_SPECIFICATION.md`
- **User Guide**: `README_AUTONOMOUS_LINEAGE.md`
- **Project Instructions**: `CLAUDE.md`
- **Main Script**: `autonomous_lineage.py`

---

## Version History

- **v2.0** (2025-10-24): Added outputs field, circular dependency tracking
- **v1.0** (2025-10-24): Initial autonomous lineage engine

---

## Support

For issues or questions:
1. Review this summary
2. Check `JSON_FORMAT_SPECIFICATION.md` for format details
3. Review confidence report for specific objects
4. Consult `CLAUDE.md` for codebase context
