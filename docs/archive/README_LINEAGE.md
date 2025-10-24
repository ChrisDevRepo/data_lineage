# Data Lineage Reverse Engineering Script

## Overview

`reverse_engineer_lineage.py` is a Python script that reverse engineers data lineage from SQL stored procedures, tables, and views in an Azure Synapse Analytics data warehouse. It analyzes SQL files to identify dependencies and outputs a structured JSON representation of the data flow.

## Features

- **Automatic SQL Parsing**: Parses CREATE TABLE, CREATE VIEW, and CREATE PROCEDURE statements
- **Dependency Extraction**: Identifies dependencies from:
  - INSERT INTO statements
  - UPDATE statements
  - SELECT FROM clauses
  - JOIN clauses
- **Recursive Tracing**: Recursively traces back dependencies to find all source objects
- **Schema Support**: Properly handles multiple schemas (STAGING_CADENCE, CONSUMPTION_ClinOpsFinance, CONSUMPTION_FINANCE, etc.)
- **Edge Case Handling**:
  - Temp tables (starting with #)
  - CTEs (Common Table Expressions)
  - UNION queries
  - Table hints like WITH (NOLOCK)
  - Complex UPDATE statements with aliases
- **JSON Output**: Generates lineage in a standard JSON format for easy integration with visualization tools

## Installation

### Requirements

- Python 3.6 or higher
- No external dependencies required (uses only standard library)

### Setup

1. Ensure the script is executable:
   ```bash
   chmod +x reverse_engineer_lineage.py
   ```

2. Verify the Synapse_Data_Warehouse directory structure:
   ```
   Synapse_Data_Warehouse/
   ├── Tables/
   ├── Views/
   └── Stored Procedures/
   ```

## Usage

### Basic Syntax

```bash
python reverse_engineer_lineage.py <target_table_name> [options]
```

### Command-Line Options

- `target_table`: (Required) The table, view, or stored procedure name to analyze
  - Can be specified with or without schema: `TableName` or `SCHEMA.TableName`

- `--output, -o`: Output JSON file path (default: `<target_table>_lineage.json`)

- `--synapse-dir`: Path to Synapse_Data_Warehouse directory (default: `./Synapse_Data_Warehouse`)

- `--help, -h`: Show help message and exit

### Examples

#### Example 1: Analyze a table by name only
```bash
python reverse_engineer_lineage.py CadenceBudgetData
```
Output: `CadenceBudgetData_lineage.json`

#### Example 2: Analyze a table with fully qualified name
```bash
python reverse_engineer_lineage.py CONSUMPTION_FINANCE.FactGLSAP
```
Output: `FactGLSAP_lineage.json`

#### Example 3: Specify custom output file
```bash
python reverse_engineer_lineage.py DimProjects --output my_lineage.json
```
Output: `my_lineage.json`

#### Example 4: Analyze a view
```bash
python reverse_engineer_lineage.py vCadenceProjects
```
Output: `vCadenceProjects_lineage.json`

#### Example 5: Specify custom Synapse directory
```bash
python reverse_engineer_lineage.py CadenceBudgetData --synapse-dir /path/to/Synapse_Data_Warehouse
```

## Output Format

The script generates a JSON array where each object represents a node in the lineage graph:

```json
[
  {
    "id": "node_0",
    "name": "TableOrViewName",
    "schema": "SchemaName",
    "object_type": "Table|View|StoredProcedure",
    "inputs": ["node_1", "node_2"]
  }
]
```

### Field Descriptions

- **id**: Unique identifier for the node (format: `node_N`)
- **name**: Name of the database object (without schema)
- **schema**: Schema name (e.g., CONSUMPTION_FINANCE, STAGING_CADENCE, dbo)
- **object_type**: Type of database object:
  - `Table`: Physical table
  - `View`: Database view
  - `StoredProcedure`: Stored procedure
- **inputs**: Array of node IDs representing objects that this object depends on

### Interpretation

- **Empty inputs array**: Indicates a source object with no dependencies (e.g., staging tables, external data sources)
- **Multiple inputs**: Indicates the object combines data from multiple sources
- **Object appears in multiple inputs**: Indicates the object is used by multiple downstream objects

## Example Output

For the table `CONSUMPTION_ClinOpsFinance.CadenceBudgetData`, the script generates:

```json
[
  {
    "id": "node_0",
    "name": "CadenceBudgetData",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "Table",
    "inputs": []
  },
  {
    "id": "node_1",
    "name": "spLoadCadenceBudgetData",
    "schema": "CONSUMPTION_ClinOpsFinance",
    "object_type": "StoredProcedure",
    "inputs": [
      "node_0",
      "node_2",
      "node_3"
    ]
  },
  {
    "id": "node_2",
    "name": "MonthlyAverageCurrencyExchangeRate",
    "schema": "CONSUMPTION_PRIMA",
    "object_type": "Table",
    "inputs": []
  },
  {
    "id": "node_3",
    "name": "MonthlyTaskTaskCountry",
    "schema": "STAGING_CADENCE",
    "object_type": "Table",
    "inputs": []
  }
]
```

This shows:
- `CadenceBudgetData` table is loaded by `spLoadCadenceBudgetData` stored procedure
- The stored procedure reads from `MonthlyAverageCurrencyExchangeRate` and `MonthlyTaskTaskCountry` tables

## How It Works

### 1. SQL File Scanning

The script scans all `.sql` files in three directories:
- `Tables/` - Contains CREATE TABLE statements
- `Views/` - Contains CREATE VIEW statements
- `Stored Procedures/` - Contains CREATE PROCEDURE statements

### 2. Object Identification

For each file:
- Extracts the schema and object name from the filename (e.g., `SCHEMA.ObjectName.sql`)
- Falls back to parsing the CREATE statement if filename parsing fails
- Stores object metadata (type, name, schema, file path)

### 3. Dependency Extraction

For each object:
- **Tables**: No dependencies (unless they're materialized views)
- **Views**: Extracts tables/views from FROM and JOIN clauses
- **Stored Procedures**:
  - Identifies target tables from INSERT INTO and UPDATE statements
  - Extracts source tables/views from FROM and JOIN clauses
  - Associates procedures with tables they modify

### 4. Lineage Graph Construction

Starting from the target object:
- Performs breadth-first traversal of dependencies
- Recursively follows each dependency to its sources
- Builds a complete dependency graph
- Handles circular dependencies by tracking processed objects

### 5. JSON Generation

- Assigns unique node IDs (`node_0`, `node_1`, etc.)
- Converts object references to node ID references
- Outputs structured JSON array

## SQL Patterns Supported

### Table Creation
```sql
CREATE TABLE [SCHEMA].[TableName] (
    ...
)
```

### View Creation
```sql
CREATE VIEW [SCHEMA].[ViewName] AS
SELECT * FROM [SCHEMA].[SourceTable]
```

### Stored Procedure Creation
```sql
CREATE PROC [SCHEMA].[ProcName] AS
BEGIN
    INSERT INTO [SCHEMA].[TargetTable]
    SELECT * FROM [SCHEMA].[SourceTable]
END
```

### INSERT Statements
```sql
INSERT INTO [SCHEMA].[Table] (col1, col2)
SELECT col1, col2 FROM [SCHEMA].[Source]
```

### UPDATE Statements
```sql
-- Direct update
UPDATE [SCHEMA].[Table]
SET col1 = value

-- Aliased update
UPDATE t
SET t.col1 = s.col1
FROM [SCHEMA].[Table] t
JOIN [SCHEMA].[Source] s ON t.id = s.id
```

### UNION Queries
```sql
SELECT * FROM [SCHEMA].[Table1]
UNION
SELECT * FROM [SCHEMA].[Table2]
```

### Table Hints
```sql
SELECT * FROM [SCHEMA].[Table] WITH (NOLOCK)
```

### Temp Tables
```sql
CREATE TABLE #TempTable (...)
```
Note: Temp tables are excluded from lineage output

### CTEs (Common Table Expressions)
```sql
WITH CTE AS (
    SELECT * FROM [SCHEMA].[Table]
)
SELECT * FROM CTE
```
Note: CTEs are not treated as real tables in the lineage

## Limitations

1. **Dynamic SQL**: Cannot trace dependencies in dynamic SQL strings (EXEC statements with string concatenation)

2. **Cross-Database References**: Only analyzes objects within the Synapse_Data_Warehouse directory

3. **External Data Sources**: Cannot trace dependencies to external systems (e.g., external tables, OPENROWSET)

4. **Complex PL/SQL Logic**: May not capture all dependencies in very complex procedural logic with conditional branching

5. **Synonyms**: Does not resolve synonym references

6. **Temp Tables**: Excludes temporary tables (starting with #) from output

## Troubleshooting

### Error: "Target table 'X' not found"

**Cause**: The specified table/view/procedure doesn't exist in the SQL files

**Solution**:
- Run the script to see the list of available objects
- Check spelling and schema name
- Verify the SQL file exists in the correct directory

### Error: "Synapse directory not found"

**Cause**: The script cannot find the Synapse_Data_Warehouse directory

**Solution**:
- Ensure you're running the script from the correct directory
- Use `--synapse-dir` option to specify the correct path
- Check directory permissions

### No dependencies found for a table

**Cause**:
- The table is a source table with no upstream dependencies
- The stored procedures haven't been properly parsed

**Solution**:
- Check if there are stored procedures that load this table
- Verify the SQL files follow the expected naming pattern
- Check if the CREATE PROC statements are formatted correctly

### Incomplete lineage graph

**Cause**:
- Some SQL patterns may not be recognized
- Complex SQL with nested queries may be partially parsed

**Solution**:
- Review the SQL files for unsupported patterns
- Check the console output for parsing warnings
- Manually verify complex dependencies

## Integration with Visualization Tools

The JSON output can be easily integrated with graph visualization tools:

### Example: Python NetworkX

```python
import json
import networkx as nx
import matplotlib.pyplot as plt

# Load lineage JSON
with open('CadenceBudgetData_lineage.json', 'r') as f:
    lineage = json.load(f)

# Create directed graph
G = nx.DiGraph()

# Add nodes
for node in lineage:
    G.add_node(node['id'],
               name=node['name'],
               schema=node['schema'],
               type=node['object_type'])

# Add edges (inputs → current node)
for node in lineage:
    for input_id in node['inputs']:
        G.add_edge(input_id, node['id'])

# Visualize
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue',
        node_size=1500, font_size=8, arrows=True)
plt.show()
```

### Example: D3.js Web Visualization

The JSON format is compatible with D3.js force-directed graphs:

```javascript
d3.json('CadenceBudgetData_lineage.json').then(data => {
    const nodes = data;
    const links = [];

    // Convert inputs to links
    data.forEach(node => {
        node.inputs.forEach(inputId => {
            links.push({
                source: inputId,
                target: node.id
            });
        });
    });

    // Use D3 force simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id))
        .force('charge', d3.forceManyBody())
        .force('center', d3.forceCenter(width/2, height/2));

    // Render nodes and links...
});
```

## Advanced Usage

### Batch Processing

Process multiple tables:

```bash
#!/bin/bash
tables=(
    "CadenceBudgetData"
    "FactGLSAP"
    "DimProjects"
)

for table in "${tables[@]}"; do
    echo "Processing $table..."
    python reverse_engineer_lineage.py "$table"
done
```

### Combining Lineages

Merge multiple lineage files into one:

```python
import json
import glob

all_nodes = []
node_ids = set()

for file in glob.glob('*_lineage.json'):
    with open(file, 'r') as f:
        lineage = json.load(f)
        for node in lineage:
            if node['id'] not in node_ids:
                all_nodes.append(node)
                node_ids.add(node['id'])

with open('combined_lineage.json', 'w') as f:
    json.dump(all_nodes, f, indent=2)
```

## Contributing

To extend the script:

1. **Add new SQL patterns**: Update the regex patterns in extraction methods
2. **Support new object types**: Add new parsing methods
3. **Enhance dependency detection**: Improve the `extract_*_dependencies` methods
4. **Add validation**: Include data quality checks on the lineage graph

## License

This script is provided as-is for internal use with the Azure Synapse Analytics data warehouse project.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the console output for parsing details
3. Examine the SQL files for unsupported patterns
4. Contact the data engineering team

## Version History

- **v1.0** (2025-01-24): Initial release
  - Support for tables, views, and stored procedures
  - Recursive dependency tracing
  - JSON output format
  - Multi-schema support
  - Handle temp tables, CTEs, and table hints
