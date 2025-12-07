# Data Lineage Visualizer

![Data Lineage Visualizer](https://raw.githubusercontent.com/ChrisDevRepo/data_lineage/main/docs/images/data-lineage-gui.png)

**Interactive data lineage visualization for Microsoft SQL Server family databases**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/ChrisDevRepo/data_lineage/blob/main/LICENSE)
[![Docker Image](https://img.shields.io/docker/v/chwagneraltyca/data-lineage-visualizer?label=docker)](https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer)
[![GitHub](https://img.shields.io/badge/GitHub-ChrisDevRepo%2Fdata__lineage-181717?logo=github)](https://github.com/ChrisDevRepo/data_lineage)

---

## 🚀 Quick Start

```bash
docker run -d \
  -p 8000:8000 \
  -v data-lineage-config:/app/config \
  --name data-lineage-visualizer \
  chwagneraltyca/data-lineage-visualizer:latest
```

**Access:** http://localhost:8000

---

## 📦 Features

- **YAML-Based SQL Parser** - Pure regex extraction with metadata catalog validation
- **Interactive Graph** - Pan, zoom, explore with React Flow
- **Trace Mode** - Analyze upstream/downstream dependencies
- **SQL Viewer** - Monaco Editor with syntax highlighting
- **Smart Filtering** - Schema, type, and pattern-based filtering
- **Multiple Import Methods** - Parquet upload, direct database connection, or JSON export

---

## 🗄️ Supported Databases

- ✅ **Azure Synapse Analytics** (dedicated SQL pools)
- ✅ **Azure SQL Database**
- ✅ **SQL Server**
- ✅ **Microsoft Fabric**

---

## 🎯 Use Cases

- Understand SQL object dependencies
- Impact analysis before making changes
- Documentation generation for data warehouses
- Compliance and audit requirements
- Data governance initiatives

---

## 📚 Documentation

- **[GitHub Repository](https://github.com/ChrisDevRepo/data_lineage)** - Full source code and documentation
- **[Quick Start Guide](https://github.com/ChrisDevRepo/data_lineage/blob/main/QUICKSTART.md)** - Detailed installation steps
- **[Configuration Guide](https://github.com/ChrisDevRepo/data_lineage/blob/main/docs/CONFIGURATION.md)** - Environment setup and database connections
- **[Live Demo](https://datalineage.chwagner.eu/)** - Try it online
- **[Video Demo](https://www.youtube.com/watch?v=uZAk9PqHwJc)** - YouTube walkthrough

---

## 🐳 Docker Usage

### Basic Usage

```bash
# Pull the image
docker pull chwagneraltyca/data-lineage-visualizer:latest

# Run with named volume
docker run -d \
  -p 8000:8000 \
  -v data-lineage-config:/app/config \
  --name data-lineage-visualizer \
  chwagneraltyca/data-lineage-visualizer:latest
```

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
services:
  data-lineage-visualizer:
    image: chwagneraltyca/data-lineage-visualizer:1.0.1
    container_name: data-lineage-visualizer
    ports:
      - "8000:8000"
    volumes:
      - data-lineage-config:/app/config
    environment:
      - ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
      - LOG_LEVEL=INFO
      - RUN_MODE=production
      - SQL_DIALECT=tsql
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  data-lineage-config:
    driver: local
```

Then run:

```bash
docker-compose up -d
```

---

## 🔧 Configuration

All configuration stored in `/app/config` volume:

- `.env` - Environment variables (auto-created from template)
- `data/` - DuckDB database and outputs
- `logs/` - Application logs
- `rules/` - SQL extraction rules (customizable YAML)
- `queries/` - Query templates (customizable YAML)

**Customize rules:** Edit files in the volume to adjust SQL parsing behavior without rebuilding the image.

---

## 🔗 Links

- **GitHub Repository:** https://github.com/ChrisDevRepo/data_lineage
- **Live Demo:** https://datalineage.chwagner.eu/
- **YouTube Demo:** https://www.youtube.com/watch?v=uZAk9PqHwJc
- **Author:** Christian Wagner
- **License:** MIT

---

## 📊 Architecture

**Tech Stack:**
- **Backend:** FastAPI + Python 3.12
- **Database:** DuckDB (embedded analytics)
- **Frontend:** React + TypeScript
- **Visualization:** React Flow + Graphology
- **Parser:** YAML-based regex engine

**Data Flow:**
1. Import from Parquet/Database/JSON
2. YAML rule engine extracts dependencies
3. Metadata catalog validates results
4. Interactive graph visualization

---

## 🏷️ Tags

`data-lineage` `sql-server` `azure-sql` `synapse-analytics` `microsoft-fabric` `data-governance` `metadata` `visualization` `fastapi` `react` `duckdb` `dependency-analysis` `impact-analysis` `sql-parser` `yaml`

---

## ⚠️ Disclaimers

This is a **proof of concept** tool:

- Extensively tested with Azure Synapse Analytics and Azure SQL Database
- Supports Microsoft SQL Server family only
- Best suited for understanding dependencies and impact analysis
- Test thoroughly before production use

**Limitations:**
- Object-level tracking only (not column-level)
- Cannot parse dynamic SQL
- Single database scope (no cross-database tracking)

---

## 📄 License

MIT License - Free to use, modify, and distribute (even commercially).

See [LICENSE](https://github.com/ChrisDevRepo/data_lineage/blob/main/LICENSE) for details.

---

## 🤝 Contributing

Community contributions welcome! See [DEVELOPMENT.md](https://github.com/ChrisDevRepo/data_lineage/blob/main/docs/DEVELOPMENT.md) for setup instructions.

---

**Built with:** FastAPI • React • DuckDB • React Flow • Graphology
**Status:** Proof of Concept - Production tested with Azure Synapse/SQL
**Author:** Christian Wagner
**Version:** 1.0.1
