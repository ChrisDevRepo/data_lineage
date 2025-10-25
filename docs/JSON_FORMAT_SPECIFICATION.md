# Data Lineage JSON Format Specification

## Overview

This document defines the **strict JSON format** for data lineage output from the autonomous lineage engine.

## Format Version

**Version:** 2.0 (with outputs field)
**Date:** 2025-10-24

## JSON Structure

The output is a JSON array containing node objects. Each node represents a database object (Table, View, or Stored Procedure).

### Required Fields

Each node **MUST** contain these required fields:

```json
{
  "id": "string",
  "name": "string",
  "schema": "string",
  "object_type": "string",
  "inputs": ["string"],
  "outputs": ["string"]
}
```

### Optional Fields

Each node **MAY** contain these optional fields:

```json
{
  "description": "string",
  "data_model_type": "string"
}
```

### Field Definitions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | string | ✅ Yes | Unique node identifier | `"node_0"`, `"node_1"` |
| `name` | string | ✅ Yes | Object name (without schema) | `"CadenceBudgetData"` |
| `schema` | string | ✅ Yes | Schema name | `"CONSUMPTION_ClinOpsFinance"` |
| `object_type` | string | ✅ Yes | One of: `"Table"`, `"View"`, `"Stored Procedure"` | `"Table"` |
| `description` | string | ⚪ Optional | Brief description of object's purpose (empty by default) | `"Contains customer information"` |
| `data_model_type` | string | ⚪ Optional | Role in data model: `"Dimension"`, `"Fact"`, `"Other"` | `"Dimension"` |
| `inputs` | array | ✅ Yes | Array of node IDs this object depends on | `["node_1", "node_2"]` |
| `outputs` | array | ✅ Yes | Array of node IDs this object writes to | `["node_3", "node_4"]` |

### Data Model Type Classification

The `data_model_type` field is automatically inferred from object naming patterns:

- **"Dimension"**: Object name starts with `Dim` (e.g., `DimCustomers`, `DimAccount`)
- **"Fact"**: Object name starts with `Fact` (e.g., `FactGLCognos`, `FactOrders`)
- **"Other"**: All other objects including:
  - Stored procedures
  - Views
  - Staging tables
  - Junction tables
  - Configuration tables

## Lineage Logic

### For Stored Procedures

```json
{
  "id": "node_0",
  "name": "spLoadCadenceBudgetData",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "Stored Procedure",
  "description": "",
  "data_model_type": "Other",
  "inputs": ["node_1", "node_2"],     // Tables/Views it READS from (FROM, JOIN)
  "outputs": ["node_3", "node_4"]     // Tables it WRITES to (INSERT, UPDATE, SELECT INTO)
}
```

**inputs**: All tables and views referenced in:
- `FROM` clauses
- `JOIN` clauses (INNER, LEFT, RIGHT, FULL OUTER, CROSS)
- `EXISTS` subqueries
- CTEs (Common Table Expressions) - unwrapped to source tables

**outputs**: All tables modified via:
- `INSERT INTO`
- `UPDATE`
- `SELECT INTO`
- `MERGE INTO`
- `TRUNCATE TABLE`

**Exclusions**:
- Temp tables (starting with `#`)
- Logging objects (`ADMIN.Logs`, `dbo.LogMessage`, `dbo.spLastRowCount`)

### For Tables

```json
{
  "id": "node_3",
  "name": "CadenceBudgetData",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "Table",
  "description": "",
  "data_model_type": "Other",
  "inputs": ["node_0"],    // Stored Procedures that WRITE to it
  "outputs": []            // Always empty for tables
}
```

**Example with Dimension table:**

```json
{
  "id": "node_4",
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "description": "",
  "data_model_type": "Dimension",
  "inputs": ["node_0"],
  "outputs": []
}
```

**inputs**: All stored procedures that write to this table
**outputs**: Always empty array `[]`

### For Views

```json
{
  "id": "node_2",
  "name": "vFull_Departmental_Map_ActivePrima",
  "schema": "CONSUMPTION_ClinOpsFinance",
  "object_type": "View",
  "description": "",
  "data_model_type": "Other",
  "inputs": ["node_5", "node_6"],    // Tables/Views it READS from
  "outputs": []                       // Always empty for views
}
```

**inputs**: All tables and views referenced in the view definition
**outputs**: Always empty array `[]`

## Circular Dependencies

A stored procedure can both READ from and WRITE to the same table, creating a circular dependency:

```json
[
  {
    "id": "node_0",
    "name": "spLoadEmployeeContractUtilization_Aggregations",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "Stored Procedure",
    "description": "",
    "data_model_type": "Other",
    "inputs": ["node_1", "node_3"],      // Reads from node_3
    "outputs": ["node_3", "node_4"]      // Writes to node_3 (CIRCULAR!)
  },
  {
    "id": "node_3",
    "name": "EmployeeContractFTE_Monthly",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "Table",
    "description": "",
    "data_model_type": "Other",
    "inputs": ["node_0"],                // SP writes to it
    "outputs": []
  }
]
```

In this case:
- `node_3` appears in BOTH `inputs` and `outputs` of `node_0`
- This represents: SP creates the table, then reads from it in a later query

## Complete Example

```json
[
  {
    "id": "node_0",
    "name": "spLoadCadenceBudgetData",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "Stored Procedure",
    "description": "",
    "data_model_type": "Other",
    "inputs": [
      "node_1",
      "node_2"
    ],
    "outputs": [
      "node_3"
    ]
  },
  {
    "id": "node_1",
    "name": "MonthlyAverageCurrencyExchangeRate",
    "schema": "CONSUMPTION_PRIMA",
    "object_type": "Table",
    "description": "",
    "data_model_type": "Other",
    "inputs": [],
    "outputs": []
  },
  {
    "id": "node_2",
    "name": "vFull_Departmental_Map",
    "schema": "DBO",
    "object_type": "View",
    "description": "",
    "data_model_type": "Other",
    "inputs": [
      "node_4",
      "node_5"
    ],
    "outputs": []
  },
  {
    "id": "node_3",
    "name": "CadenceBudgetData",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "Table",
    "description": "",
    "data_model_type": "Other",
    "inputs": [
      "node_0"
    ],
    "outputs": []
  },
  {
    "id": "node_4",
    "name": "Full_Departmental_Map",
    "schema": "DBO",
    "object_type": "Table",
    "description": "",
    "data_model_type": "Other",
    "inputs": [],
    "outputs": []
  },
  {
    "id": "node_5",
    "name": "HrDepartments",
    "schema": "CONSUMPTION_PRIMA",
    "object_type": "Table",
    "description": "",
    "data_model_type": "Other",
    "inputs": [],
    "outputs": []
  },
  {
    "id": "node_6",
    "name": "DimCustomers",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Table",
    "description": "",
    "data_model_type": "Dimension",
    "inputs": [],
    "outputs": []
  },
  {
    "id": "node_7",
    "name": "FactGLCognos",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Table",
    "description": "",
    "data_model_type": "Fact",
    "inputs": [],
    "outputs": []
  }
]
```

## Validation Rules

### Required Field Validation
1. ✅ Each node MUST have all 6 required fields: `id`, `name`, `schema`, `object_type`, `inputs`, `outputs`
2. ✅ `id` must be unique across all nodes
3. ✅ `id` must follow format: `node_N` where N is an integer
4. ✅ `object_type` must be one of: `"Table"`, `"View"`, `"StoredProcedure"`
5. ✅ `inputs` and `outputs` must be arrays (can be empty)
6. ✅ All node IDs referenced in `inputs`/`outputs` must exist in the array
7. ✅ Node IDs should be sequential starting from `node_0`
8. ✅ For Tables and Views: `outputs` must be empty `[]`
9. ✅ Node IDs in `inputs`/`outputs` should be sorted

### Optional Field Validation
10. ✅ `description` (if present) must be a string
11. ✅ `data_model_type` (if present) must be one of: `"Dimension"`, `"Fact"`, `"Other"`

## Schema Qualification

- Full object names use format: `{schema}.{object_name}`
- Same object name can exist in different schemas
- Internal tracking uses full qualified names
- JSON output separates `schema` and `name` fields for clarity

## Key Differences from Version 1.0

| Aspect | Version 1.0 | Version 2.0 |
|--------|-------------|-------------|
| Output field | ❌ Not present | ✅ Added |
| SP outputs tracking | ❌ Not tracked | ✅ Tracked |
| Circular dependencies | ❌ Not visible | ✅ Visible via inputs+outputs |
| Logging objects | ❌ Included | ✅ Excluded |
| Table inputs | ❌ Empty | ✅ Shows writer SPs |

## Usage

Generate lineage JSON using:

```bash
python3 autonomous_lineage.py <object_name>
```

Output files:
- `{object}_lineage.json` - Lineage in this format
- `{object}_confidence.json` - Quality metadata

## Validation Script

```python
import json

def validate_lineage_json(data):
    required_fields = {'id', 'name', 'schema', 'object_type', 'inputs', 'outputs'}
    valid_types = {'Table', 'View', 'Stored Procedure'}
    valid_data_model_types = {'Dimension', 'Fact', 'Other'}

    # Collect all node IDs
    node_ids = {node['id'] for node in data}

    for node in data:
        # Check required fields
        if not required_fields.issubset(node.keys()):
            return False

        # Check object_type
        if node['object_type'] not in valid_types:
            return False

        # Check arrays
        if not isinstance(node['inputs'], list):
            return False
        if not isinstance(node['outputs'], list):
            return False

        # Check optional fields
        if 'description' in node and not isinstance(node['description'], str):
            return False
        if 'data_model_type' in node:
            if not isinstance(node['data_model_type'], str):
                return False
            if node['data_model_type'] not in valid_data_model_types:
                return False

        # Check all references exist
        for ref_id in node['inputs'] + node['outputs']:
            if ref_id not in node_ids:
                return False

        # Tables and Views should have empty outputs
        if node['object_type'] in ['Table', 'View']:
            if node['outputs'] != []:
                return False

    return True

# Usage
with open('lineage.json') as f:
    data = json.load(f)
    is_valid = validate_lineage_json(data)
    print(f"Valid: {is_valid}")
```

## Version History

- **2.1** (2025-10-25): Added optional `description` and `data_model_type` fields
- **2.0** (2025-10-24): Added `outputs` field, improved circular dependency tracking
- **1.0** (2025-10-24): Initial specification with `inputs` only
