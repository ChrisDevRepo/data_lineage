# Azure Synapse Data Warehouse - Data Lineage Analysis

This repository contains SQL scripts for an Azure Synapse Analytics data warehouse implementation, along with autonomous data lineage analysis tools.

## 📁 Repository Structure

```
ws-psidwh/
├── Synapse_Data_Warehouse/       # Azure Synapse SQL objects
│   ├── Stored Procedures/        # ETL and data processing procedures
│   ├── Tables/                   # Table definitions
│   └── Views/                    # View definitions
│
├── scripts/                      # Lineage analysis scripts
│   └── autonomous_lineage.py     # Main autonomous lineage engine
│
├── ai_analyzer/                  # AI-assisted SQL analysis modules
│   ├── sql_complexity_detector.py
│   ├── ai_sql_parser.py
│   └── confidence_scorer.py
│
├── parsers/                      # SQL parsing modules
│   ├── sql_parser_enhanced.py
│   └── dependency_extractor.py
│
├── validators/                   # Dependency validation modules
│   ├── dependency_validator.py
│   └── iterative_refiner.py
│
├── output/                       # Output formatting modules
│   ├── json_formatter.py
│   └── confidence_reporter.py
│
├── lineage_output/              # Generated lineage analysis results
│   ├── *_lineage.json          # Complete lineage graphs
│   └── *_confidence.json       # Analysis quality reports
│
├── docs/                        # Documentation
│   ├── JSON_FORMAT_SPECIFICATION.md
│   ├── README_AUTONOMOUS_LINEAGE.md
│   └── ...
│
├── CLAUDE.md                    # AI assistant instructions
└── README.md                    # This file
```

## 🚀 Quick Start

### Generate Data Lineage for a SQL Object

```bash
# From repository root
python3 scripts/main.py <object_name>

# Examples:
python3 scripts/main.py spLoadFactGLCOGNOS
python3 scripts/main.py CadenceBudgetData
python3 scripts/main.py CONSUMPTION_FINANCE.FactGLCognos
```

### Output Files

Results are automatically saved to `lineage_output/`:
- `{object}_lineage.json` - Complete dependency graph in JSON format
- `{object}_confidence.json` - Analysis quality and confidence report

## 📊 Data Lineage Features

### Autonomous Lineage Engine

The lineage engine automatically:
- ✅ **Traces complete dependency chains** from any database object
- ✅ **Builds bidirectional graphs** (inputs + outputs for visualization)
- ✅ **Detects circular dependencies** (SP reads and writes same table)
- ✅ **Validates dependencies** against actual codebase
- ✅ **Generates confidence scores** for detected relationships
- ✅ **Handles complex SQL patterns** (MERGE, CTEs, dynamic SQL)

### Graph Structure

The JSON output follows a strict bidirectional format:

```json
{
  "id": "node_0",
  "name": "spLoadFactGLCOGNOS",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "StoredProcedure",
  "inputs": ["node_1", "node_2"],      // Tables/views it reads from
  "outputs": ["node_3"]                // Tables it writes to
}
```

**Supported for graph visualization tools:**
- D3.js force-directed graphs
- Graphviz DOT format
- Neo4j graph database
- Cytoscape network visualization
- Mermaid diagrams

## 🏗️ Data Warehouse Architecture

### Schema Layers

**STAGING Schemas:**
- `STAGING_CADENCE` - Intermediate Cadence system data processing
- `STAGING_FINANCE_SAP` - SAP staging data
- `STAGING_FINANCE_COGNOS` - Cognos staging data

**CONSUMPTION Schemas:**
- `CONSUMPTION_FINANCE` - Finance domain (dimensions, facts, SAP analytics)
- `CONSUMPTION_ClinOpsFinance` - Clinical Operations Finance integration
- `CONSUMPTION_POWERBI` - Power BI optimized tables
- `CONSUMPTION_PRIMA` - Prima system data
- `CONSUMPTION_PRIMAREPORTING` - Prima reporting views

### Key Patterns

**Stored Procedure Naming:**
- `spLoad{TargetTable}` - Load procedures
- `spLoad{Target}_Post` - Post-processing operations
- `spLoad{Target}_Aggregations` - Aggregation calculations

**Error Handling:**
All procedures use standardized logging via `dbo.LogMessage` and `dbo.spLastRowCount`.

**Table Distribution:**
- `DISTRIBUTION = REPLICATE` - Small dimension tables
- `DISTRIBUTION = HASH([columns])` - Large fact tables
- `CLUSTERED COLUMNSTORE INDEX` - Default for fact tables

## 📖 Documentation

See `docs/` folder for detailed documentation:
- **[README_AUTONOMOUS_LINEAGE.md](docs/README_AUTONOMOUS_LINEAGE.md)** - Lineage engine guide
- **[JSON_FORMAT_SPECIFICATION.md](docs/JSON_FORMAT_SPECIFICATION.md)** - Output format specification
- **[CLAUDE.md](CLAUDE.md)** - Project instructions for AI assistants

## 🛠️ Development

### Prerequisites

- Python 3.9+
- Azure Synapse Analytics workspace
- SQL Server Management Studio or Azure Data Studio (for deployment)

### Module Architecture

The lineage engine uses a modular pipeline:

1. **parsers/** - Regex-based SQL parsing and dependency extraction
2. **ai_analyzer/** - AI-assisted analysis for complex SQL patterns
3. **validators/** - Dependency validation and iterative refinement
4. **output/** - JSON formatting and confidence reporting

All modules are actively used during lineage analysis.

### Running Analysis

```bash
# Basic usage
python3 scripts/main.py <object_name>

# Specify custom Synapse directory
python3 scripts/main.py <object_name> --synapse-dir <path>
```

### Running Tests

```bash
# Run bidirectional graph validation tests
python3 tests/test_bidirectional_graph.py

# Or test a specific lineage file
python3 tests/test_bidirectional_graph.py lineage_output/<file>_lineage.json
```

## 📈 Performance

- **Simple objects** (1-10 dependencies): ~5-10 seconds
- **Complex objects** (50+ dependencies): ~20-30 seconds
- **Large trees** (100+ objects): ~30-80 seconds

## 🎯 Use Cases

1. **Impact Analysis** - Understand which objects are affected by changes
2. **Data Flow Documentation** - Generate visual data flow diagrams
3. **Troubleshooting** - Trace data issues through the ETL pipeline
4. **Compliance** - Document data lineage for regulatory requirements
5. **Optimization** - Identify redundant or unused objects

## 📝 License

[Your License Here]

## 🤝 Contributing

[Your Contributing Guidelines Here]
