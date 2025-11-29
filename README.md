# Data Lineage Visualizer

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Node](https://img.shields.io/badge/node-20+-green.svg)
![Status](https://img.shields.io/badge/status-proof%20of%20concept-yellow.svg)

**Interactive data lineage visualization for Microsoft SQL Server family databases**

> **⚠️ Proof of Concept**: This tool was developed and tested with Azure Synapse Analytics dedicated SQL pools and Azure SQL Database. Currently supports only Microsoft SQL Server family (SQL Server, Azure SQL, Synapse Analytics, Fabric). See [disclaimers](#disclaimers) below.

Analyze dependencies between tables, views, and stored procedures with an interactive graph interface.

### 📺 Watch the Demo Video

[![Data Lineage Visualizer Demo](https://img.youtube.com/vi/uZAk9PqHwJc/maxresdefault.jpg)](https://www.youtube.com/watch?v=uZAk9PqHwJc)

**[▶️ Watch Video Demo](https://www.youtube.com/watch?v=uZAk9PqHwJc)** • [Quick Start](#quick-start) • [Features](#features) • [Documentation](#documentation) • [Live Demo](https://datalineage.chwagner.eu/) • [Disclaimers](#disclaimers)

</div>

---

## Screenshots

<div align="center">

### Interactive Graph Visualization
![Data Lineage GUI](docs/images/data-lineage-gui.png)

</div>

---

## Why Data Lineage Visualizer?

- ✅ **YAML-Based Parser** - Pure regex extraction with metadata catalog validation (100% success in testing)
- ⚡ **5-Minute Setup** - One command installation
- 🔧 **Business-Maintainable** - YAML rule engine, no Python required for rule changes
- 🔌 **Flexible** - Parquet upload OR direct database connection
- 📊 **Interactive** - Trace mode, schema filtering, full-text search
- 🧪 **Extensible** - MIT licensed, YAML-based dialect system for easy adaptation

---

## Quick Start

```bash
# Install and run (Production mode - optimized for performance)
git clone https://github.com/your-org/data_lineage.git
cd data_lineage
pip install -r requirements.txt
./start-app.sh
```

**Access:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

**Startup Modes:**
- `./start-app.sh` - Production mode (default, fast <5s initial load)
- `./start-app.sh dev` - Development mode with HMR (slower ~2min due to React Flow dev mode)
- `./start-app.sh --rebuild` - Force rebuild production bundle

**Next Steps:** Upload Parquet files or [configure database connection](docs/CONFIGURATION.md#database-direct-connection)

**Setup Guides:**
- [QUICKSTART.md](QUICKSTART.md) - Detailed installation and setup
- [.devcontainer/README.md](.devcontainer/README.md) - VSCode devcontainer configuration
- [.azure-deploy/AZURE_DEPLOYMENT.md](.azure-deploy/AZURE_DEPLOYMENT.md) - Azure Container Apps deployment

---

## Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Interactive Graph** | Pan, zoom, explore with React Flow |
| **Trace Mode** | Analyze upstream/downstream dependencies (BFS traversal) |
| **SQL Viewer** | Monaco Editor with syntax highlighting |
| **Smart Filtering** | Schema, type, pattern-based, and focus filtering |
| **Search** | Full-text search across all definitions |

### Data Sources

| Method | Use Case |
|--------|----------|
| **Parquet Upload** | Manual metadata extraction (default) |
| **Database Direct** | Auto-refresh from SQL Server/Azure SQL/Synapse/Fabric |
| **JSON Export** | Share and version control lineage data |

### Supported Databases

**Implemented and Tested:**
- ✅ **Azure Synapse Analytics** (dedicated SQL pools) - Extensively tested
- ✅ **Azure SQL Database** - Tested with database direct import
- ✅ **SQL Server** - Uses same T-SQL connector as Synapse/Azure SQL
- ✅ **Microsoft Fabric** - Uses T-SQL dialect, same connector as SQL Server/Synapse

> **Note:** Only the Microsoft SQL Server family is currently supported. The YAML-based architecture allows for extension to other SQL dialects, but these are not yet implemented.

---

## Architecture

**System Flow:**

1. **Input** - Parquet files (manual upload) or Database Direct (SQL Server/Azure SQL/Synapse/Fabric) or JSON import
2. **Storage** - FastAPI + DuckDB analytics workspace
3. **Processing** - YAML Rule Engine applies dialect-specific regex patterns
4. **Extraction** - Regex-based dependency extraction (FROM/JOIN, INSERT/UPDATE/MERGE, EXEC, SELECT INTO)
5. **Validation** - Metadata catalog validates extracted dependencies (removes false positives)
6. **Output** - JSON format with validated lineage data
7. **Visualization** - React + React Flow interactive graph

**Parser:** Pure YAML regex patterns extract dependencies, validated against metadata catalog (100% success rate)

**Details:** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Documentation

| Document | Audience | Purpose |
|----------|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Users | 5-minute deployment guide |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Users/DBAs | Environment variables, database setup |
| [CONTRACTS.md](docs/CONTRACTS.md) | Developers/DBAs | Complete data contracts: interfaces, schemas, API endpoints |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Developers | System design, parser internals, rule engine |
| [DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md) | Contributors | Development environment setup |

---

## Disclaimers

### ⚠️ Proof of Concept Status

This tool was developed as a **proof of concept** using Claude Code and tested specifically with:
- Azure Synapse Analytics dedicated SQL pools (extensively tested)
- Azure SQL Database (tested with database direct import feature)

**Production Status:**
- ✅ Parser extensively tested with real-world stored procedures
- ✅ Core functionality validated in Azure environment
- ✅ Supports Microsoft SQL Server family only (SQL Server, Azure SQL, Synapse, Fabric)

### 🔧 Maintenance & Development

This repository is published as-is with the following expectations:

**Active Support (Initial Period):**
- Bug fixes for critical issues
- Documentation improvements
- Security patches if needed

**Long-Term:**
- No active feature development planned
- Community contributions welcome via pull requests
- Issues will be reviewed but fixes not guaranteed
- Consider this a reference implementation

### 📋 No Warranties

This software is provided "as is" under the MIT License:
- **No guarantees** of fitness for any particular purpose
- **No liability** for data loss or system issues
- **No SLA** or support commitments
- **Test thoroughly** in your environment before production use

### 🎯 Intended Use

**Best suited for:**
- Understanding SQL object dependencies in Microsoft SQL Server family environments
- Learning how to build lineage visualization tools
- Reference implementation for YAML-based SQL parsing

**Not recommended for:**
- Mission-critical production lineage without thorough testing
- Databases outside the Microsoft SQL Server family (not currently supported)
- Environments requiring guaranteed support or updates

### 🔐 Security Considerations

- Never commit credentials to version control
- Use Azure Key Vault or similar for production secrets
- This tool connects directly to your database - restrict access appropriately
- Uploaded Parquet files may contain sensitive metadata - handle accordingly

### 📚 Extensibility

The YAML-based architecture was designed for adaptability:
- Customize parsing rules without Python code changes
- Add new extraction patterns via YAML rules

See `engine/rules/` for YAML rule examples.

---

## License

**MIT License** - Free to use, modify, and distribute (even commercially).

**Simple terms:** Do whatever you want with this code, but I'm not responsible if something breaks.

See [LICENSE](LICENSE) for the official text.

---

## Contributing

Community contributions are welcome! See [DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md) for environment setup.

**Please note:** While contributions are welcome, active maintenance and review may be limited. Consider this when planning contributions.

---

## Support

- **Demo:** Try the live demo at [https://datalineage.chwagner.eu/](https://datalineage.chwagner.eu/)
- **Documentation:** [docs/](docs/) - Comprehensive guides and specifications
- **Quick Help:** [QUICKSTART.md](QUICKSTART.md) - 5-minute deployment guide

---

## Acknowledgments

- Developed using Claude Code (Anthropic)
- Tested with Adventure Works sample database (Microsoft)
- Built on FastAPI, React, DuckDB, React Flow, and Graphology

---

**Built with:** FastAPI • React • DuckDB • React Flow • Graphology
**Status:** Proof of Concept - Production tested with Azure Synapse/SQL
**Author:** Christian Wagner
**License:** MIT
