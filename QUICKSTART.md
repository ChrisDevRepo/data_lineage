# Quick Start Guide

**Get running in 5 minutes** • For users and DBAs • [Try the demo](https://datalineage.chwagner.eu/)

---

## Installation

### Prerequisites

- Python 3.10+ ([download](https://www.python.org/downloads/))
- Node.js 18+ ([download](https://nodejs.org/))
- Git

### One-Command Install

```bash
git clone https://github.com/your-org/data_lineage.git
cd data_lineage
pip install -r requirements.txt
./start-app.sh
```

**That's it!** The application is now running in production mode:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

**Startup Modes:**
- `./start-app.sh` - Production mode (default, fast <5s load)
- `./start-app.sh dev` - Development mode with HMR (first load ~2min due to React Flow dev mode)
- `./start-app.sh --rebuild` - Force rebuild production bundle

> **Note:** Development mode is slower because React Flow runs with additional checks and warnings. Production mode is significantly faster.

---

## First-Time Setup

### Option 1: Upload Parquet Files

**Parquet Files Overview:**

The system supports 5 Parquet files, but only 3 are required to get started:

**Required:**
1. `objects.parquet` - Database objects (tables, views, SPs)
2. `definitions.parquet` - Object definitions (DDL)
3. `dependencies.parquet` - SQL expression dependencies

**Optional:**
4. `query_logs.parquet` - Query execution logs (validation)
5. `table_columns.parquet` - Table schema metadata (enhanced search)


**How to Generate Parquet Files:**
See [DATA_SPECIFICATIONS.md](docs/DATA_SPECIFICATIONS.md#parquet-file-specifications) for DMV queries.

---

### Option 2: Direct Database Connection (Optional)

**For direct refresh from the DB:**

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`:**
   ```bash
   DB_ENABLED=true
   DB_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=user;PWD=password;Encrypt=yes
   ```

3. **Restart application:**
   ```bash
   ./stop-app.sh
   ./start-app.sh
   ```

4. **Click "Refresh from Database"** in Import modal

**Security:** See [CONFIGURATION.md](docs/CONFIGURATION.md#database-connection-security) for production deployment best practices.

---

## Verify Installation

### 1. Check Services

```bash
# Backend should show:
# ✅ API server ready on http://localhost:8000

# Frontend should show:
# ✅ Frontend ready on http://localhost:3000
```

### 2. Test Frontend

1. Open http://localhost:3000
2. You should see the graph canvas with help modal
3. Click **"Import Data"** - Upload UI should appear

### 3. Test API

```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Should return:
# {"status": "healthy"}
```

---

## Next Steps

### Explore the UI

| Feature | How to Access |
|---------|---------------|
| **Trace Mode** | Right-click any node → "Start Tracing from Here" |
| **Schema Filter** | Click schema dropdown → Select schemas |
| **SQL Viewer** | Click any node → View definition in Monaco Editor |
| **Search** | Use search box in toolbar → Find nodes by name |
| **Developer Mode** | Help (?) → "For Developers" → "Open Developer Panel" |

### Configure for Your Database

1. **Exclude Schemas:**
   ```bash
   EXCLUDED_SCHEMAS=sys,information_schema,tempdb,master,msdb,model
   ```

2. **Enable Debug Logging:**
   ```bash
   LOG_LEVEL=DEBUG  # See per-object parsing details
   ```

See [CONFIGURATION.md](docs/CONFIGURATION.md) for all options.

### Customize YAML Rules

**Location:** `engine/rules/{dialect}/`

**Add Custom Extraction Pattern:**
1. Copy `engine/rules/TEMPLATE.yaml`
2. Edit `pattern` and `replacement` fields
3. Save to `engine/rules/tsql/` (or your dialect)
4. Restart application

**Example:**
```yaml
name: extract_custom_pattern
description: Extract my custom SQL pattern
category: extraction
enabled: true
priority: 20
patterns:
  - '\bMY_CUSTOM_KEYWORD\s+([^\s,;()]+)'
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md#yaml-rule-engine) for complete guide.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port already in use** | Run `./stop-app.sh` to kill existing processes |
| **Database import button disabled** | Check API is running: `curl http://localhost:8000/health` |
| **Missing dependencies** | Run `pip install -r requirements.txt && cd frontend && npm install` |
| **Parquet upload fails** | Check file formats match [DATA_SPECIFICATIONS.md](docs/DATA_SPECIFICATIONS.md#parquet-file-specifications) |
| **Database connection fails** | Verify connection string, check firewall, ensure ODBC driver installed |
| **Parser shows 0 dependencies** | Enable DEBUG logging (`LOG_LEVEL=DEBUG`), check `/api/debug/logs` |
| **Frontend blank screen** | Check browser console, verify backend is running on port 8000 |


---

## Stopping the Application

```bash
# Stop everything (backend + frontend)
./stop-app.sh
```

**How it works:**
- `stop-app.sh` - Kills both backend (port 8000) and frontend (port 3000)

---

## Initial Database Configuration & Deployment

Setting up the application for your specific database environment.

**Key Documents:**
1. **[DATA_SPECIFICATIONS.md](docs/DATA_SPECIFICATIONS.md)** - The 4 core interfaces (DMV, Parquet, JSON, YAML)
2. **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and YAML rule engine

**Database Requirements:**
The system currently supports **Microsoft SQL Server family** (SQL Server, Azure SQL, Synapse Analytics, Fabric). Other SQL dialects can be added with generic development effort:
1. **Parquet files** - Export metadata using T-SQL DMV queries (see [DATA_SPECIFICATIONS.md](docs/DATA_SPECIFICATIONS.md#parquet-file-specifications))
2. **ODBC driver** - [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) (for database direct connection)
3. **Custom YAML rules** - Optional extraction rules for custom SQL patterns (see `engine/rules/TEMPLATE.yaml`)
4. **Dialect Extension** - See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for adding new SQL dialects

---

## What's Next?

- **Customize Parsing:** [ARCHITECTURE.md](docs/ARCHITECTURE.md#parser-architecture)
- **API Integration:** [DATA_SPECIFICATIONS.md](docs/DATA_SPECIFICATIONS.md#rest-api-endpoints)
- **Development Setup:** [DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Full Configuration:** [CONFIGURATION.md](docs/CONFIGURATION.md)

---

**Built with:** FastAPI • React • DuckDB • React Flow
**License:** MIT