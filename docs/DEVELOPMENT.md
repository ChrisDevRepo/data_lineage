# Development Guide

**Complete development setup, configuration, and customization guide**

---

## Table of Contents

- [Setup](#setup)
  - [VS Code Dev Container (Recommended)](#vs-code-dev-container-recommended)
  - [Development Tools](#development-tools)
  - [Common Workflows](#common-workflows)
- [Configuration](#configuration)
  - [DMV Queries (Database Direct Import)](#dmv-queries-database-direct-import)
  - [YAML Rule Configuration](#yaml-rule-configuration)
  - [Developer Panel](#developer-panel)
  - [Hardcoded SQL Options](#hardcoded-sql-options)

---

## Setup

### VS Code Dev Container (Recommended)

**⏱️ Time to Start:** 10-15 minutes (includes Docker build)

The fastest way to get started! Uses VS Code Dev Containers for a fully configured, reproducible development environment.

#### Prerequisites

- Docker Desktop installed
- VS Code installed with "Dev Containers" extension (`ms-vscode-remote.remote-containers`)

#### Getting Started

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd data_lineage
   ```

2. **Open in VS Code:**
   ```bash
   code .
   ```

3. **Reopen in Container:**
   - Press `F1` (or `Ctrl+Shift+P` / `Cmd+Shift+P`)
   - Type and select: `Dev Containers: Reopen in Container`
   - Wait for container to build (first time only: 10-15 minutes)

4. **Everything is ready!**
   - Python environment with all dependencies
   - Frontend dependencies installed
   - VS Code extensions pre-installed
   - Debugging configured
   - Tasks ready to use

---

### Development Tools

**Python Environment:**
- Python 3.11
- All project dependencies (FastAPI, DuckDB, pandas, etc.)
- Development tools: black, isort, pylint
- Debugging support with debugpy

**Frontend Environment:**
- Node.js 20 LTS
- npm/pnpm/yarn
- React development dependencies
- Tailwind CSS tooling

**Database Drivers:**
- Microsoft ODBC Driver 18 for SQL Server
- Support for Azure Synapse, Azure SQL, SQL Server, and Fabric

**VS Code Extensions:**
- Python: Pylance, Black formatter, isort, debugpy
- JavaScript/React: ESLint, Prettier, React snippets, Tailwind IntelliSense
- API Testing: REST Client, Thunder Client
- Docker, Git, YAML, Markdown support

#### Pre-configured Tasks

Access via `Ctrl+Shift+P` → `Tasks: Run Task`

- **Start Backend (FastAPI)** - Launch backend server with hot reload
- **Start Frontend (React)** - Launch Vite dev server
- **Start Full Stack** - Launch both backend and frontend
- **Build Frontend** - Build production frontend bundle
- **Format Python Code** - Run Black formatter
- **Sort Python Imports** - Run isort
- **Clean Build Artifacts** - Remove build files and caches

#### Debugging Configurations

Access via `F5` or Debug panel

- **Python: FastAPI Backend** - Debug FastAPI with breakpoints
- **Python: Current File** - Debug currently open Python file
- **Python: Parser Script** - Debug parser validation script
- **Attach to FastAPI (Remote)** - Attach to running FastAPI instance

---

### Common Workflows

#### Starting Development

```bash
# Backend only
Ctrl+Shift+P → Tasks: Run Task → Start Backend (FastAPI)
# Opens at http://localhost:8000

# Frontend only
Ctrl+Shift+P → Tasks: Run Task → Start Frontend (React)
# Opens at http://localhost:3000

# Both (Full Stack)
Ctrl+Shift+P → Tasks: Run Task → Start Full Stack (Backend + Frontend)
```

#### Debugging

1. Set breakpoints in your code (click left gutter)
2. Press `F5` or go to Debug panel
3. Select configuration: "Python: FastAPI Backend"
4. Start debugging

#### Formatting Code

```bash
# Auto-format on save (already configured)
# Or manually:
Ctrl+Shift+P → Tasks: Run Task → Format Python Code (Black)
```

#### Accessing Services

Once the container is running:

| Service | URL | Description |
|---------|-----|-------------|
| **Backend API** | http://localhost:8000 | FastAPI application |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | Health endpoint |
| **Frontend Dev** | http://localhost:3000 | Vite dev server |

---

## Configuration

### DMV Queries (Database Direct Import)

**Location:** `engine/connectors/queries/tsql/metadata.yaml`

**This is the ONLY file used at runtime.** The connector loads all SQL queries from this YAML file, allowing customization without code changes.

**Note:** `engine/dialects/tsql.py` contains similar SQL (lines 46-69) but this is legacy code that is NOT used. The YAML file is the single source of truth.

This YAML file contains 5 metadata extraction queries used for database direct import:

1. `list_stored_procedures` - Get all procedures with metadata
2. `list_tables` - Get all tables with column info
3. `list_views` - Get all views with DDL
4. `list_functions` - Get all functions (scalar, table-valued)
5. `list_dependencies` - Get object dependencies

#### Updating DMV Queries

**When to update:**
- Custom object types not covered by default queries
- Performance optimization for large databases
- Database-specific metadata requirements

**How to update:**

1. **Open the metadata file:**
   ```bash
   code engine/connectors/queries/tsql/metadata.yaml
   ```

2. **Edit the query:**
   ```yaml
   list_stored_procedures: |
     SELECT
         p.object_id,
         SCHEMA_NAME(p.schema_id) AS schema_name,
         p.name AS object_name,
         'PROCEDURE' AS object_type,
         m.definition AS sql_code
     FROM sys.procedures p
     LEFT JOIN sys.sql_modules m ON p.object_id = m.object_id
     WHERE p.is_ms_shipped = 0
       AND SCHEMA_NAME(p.schema_id) NOT IN ('sys', 'INFORMATION_SCHEMA')
     -- Add your custom filters here
   ```

3. **Test the query:**
   - Run directly in SQL Server Management Studio or Azure Data Studio
   - Verify column names match expected schema (see [DATA_SPECIFICATIONS.md](DATA_SPECIFICATIONS.md#interface-1-dmv-database-metadata-queries))

4. **Restart application:**
   ```bash
   ./stop-app.sh
   ./start-app.sh
   ```

**Important:** Query result columns must match the DMV interface specification. See [DATA_SPECIFICATIONS.md](DATA_SPECIFICATIONS.md#interface-1-dmv-database-metadata-queries) for required column names and types.

---

### Resetting DMV Queries

If you've modified queries and want to restore defaults:

1. **Check git for original file:**
   ```bash
   git diff engine/connectors/queries/tsql/metadata.yaml
   ```

2. **Restore from git:**
   ```bash
   git checkout engine/connectors/queries/tsql/metadata.yaml
   ```

3. **Restart application:**
   ```bash
   ./stop-app.sh
   ./start-app.sh
   ```

---

### YAML Rule Configuration

**Location:** `engine/rules/`

YAML rules define SQL cleaning and extraction patterns. Rules are organized by dialect with defaults for all dialects.

#### Folder Structure

```
engine/rules/
├── defaults/                      # ANSI-compliant rules (all dialects)
│   ├── 05_extract_sources_ansi.yaml
│   ├── 06_extract_targets_ansi.yaml
│   └── 10_comment_removal.yaml
│
├── tsql/                          # T-SQL specific rules
│   ├── 07_extract_sources_tsql_apply.yaml
│   ├── 08_extract_sp_calls_tsql.yaml
│   └── 10_extract_targets_tsql.yaml
│
├── TEMPLATE.yaml                  # Template for creating new rules
├── YAML_STRUCTURE.md              # Complete schema reference
└── rule_loader.py                 # Validation and loading logic
```

#### Creating Custom Rules

**Step 1: Copy template**
```bash
cp engine/rules/TEMPLATE.yaml engine/rules/tsql/99_my_custom_rule.yaml
```

**Step 2: Edit YAML file**
```yaml
name: extract_my_pattern
description: Extract my custom SQL pattern
dialect: tsql
enabled: true
priority: 85
category: extraction
rule_type: extraction
extraction_target: source
pattern: '\bMY_KEYWORD\s+([^\s,;()]+)'
replacement: ''
```

**Step 3: Restart and verify**
```bash
./stop-app.sh
./start-app.sh
```

**Step 4: Check in Developer Panel**
- Help (?) → "For Developers" → "Open Developer Panel"
- Navigate to "YAML Rules" tab
- Verify your rule appears and is enabled

#### Rule Priority Guidelines

| Priority | Category | Purpose | Examples |
|----------|----------|---------|----------|
| **1** | Preprocessing | Remove syntax that breaks regex | Comment removal |
| **5-6** | ANSI Extraction | Common SQL patterns | FROM, JOIN (5), INSERT, UPDATE (6) |
| **7-8** | Dialect-Specific | T-SQL specific patterns | APPLY (7), EXEC/SP calls (8) |
| **10+** | Custom Rules | User-defined patterns | Custom extraction |

#### Resetting YAML Rules

**Option 1: Reset from Developer Panel**
1. Open Developer Panel: Help (?) → "For Developers"
2. Navigate to "YAML Rules" tab
3. Click "Reset Rules to Defaults"
4. Confirm reset

**Option 2: Reset from Git**
```bash
# Check what changed
git diff engine/rules/

# Reset specific file
git checkout engine/rules/tsql/07_extract_sources_tsql_apply.yaml

# Reset all rules
git checkout engine/rules/
```

**Option 3: Restore from defaults folder**
The `engine/rules/defaults/` folder contains ANSI-compliant rules that work across all dialects. These are the source of truth for "Reset to Defaults" functionality.

---

### Developer Panel

**Access:** Help (?) → "For Developers" → "Open Developer Panel"

The Developer Panel provides debugging and management tools for development and troubleshooting.

#### Tabs

**1. Logs Tab**
- **Purpose:** Real-time log viewer with color-coding
- **Features:**
  - Last 500 log entries
  - Color-coded by level (DEBUG, INFO, WARNING, ERROR)
  - Auto-scroll to latest
  - Filter by level
- **Use case:** Debug parser failures, monitor diagnostics

**2. YAML Rules Tab**
- **Purpose:** Browse and inspect all loaded rules
- **Features:**
  - View all loaded rules (defaults + dialect-specific)
  - Rule details (priority, pattern, category)
  - Enable/disable toggle
  - Reset to defaults button
- **Use case:** Verify custom rules loaded, inspect extraction patterns

**3. Parser Diagnostics Tab**
- **Purpose:** View per-object parsing details
- **Features:**
  - Parse success/failure counts
  - Diagnostic counts (expected vs found tables)
  - Regex extraction details
- **Use case:** Troubleshoot low parse success rates

#### Enabling Developer Mode

**Permanent (via .env):**
```bash
# Edit .env file
LOG_LEVEL=DEBUG
RUN_MODE=debug
```

**Temporary (for current session):**
1. Open Developer Panel
2. Toggle "Debug Mode" switch
3. Logs will show DEBUG level messages

#### Cross-References

For detailed information on specific features, see:
- **YAML Rules:** [YAML Rule Configuration](#yaml-rule-configuration) above
- **DMV Queries:** [DMV Queries](#dmv-queries-database-direct-import) above
- **Parquet Schemas:** [DATA_SPECIFICATIONS.md](DATA_SPECIFICATIONS.md#parquet-file-specifications)
- **Parser Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md#parser-architecture)

---

### Hardcoded SQL Options

Some SQL options and configurations are hardcoded in the application for performance and compatibility. If you need to modify these, you'll need to edit the source code.

#### Object Type Mappings

**Location:** `engine/dialects/tsql.py`

```python
# Maps SQL Server sys.objects.type to friendly names
OBJECT_TYPE_MAPPING = {
    'P': 'Stored Procedure',
    'V': 'View',
    'U': 'Table',
    'FN': 'Function',  # Scalar function
    'IF': 'Function',  # Inline table-valued function
    'TF': 'Function',  # Table-valued function
}
```

**To modify:**
1. Edit `engine/dialects/tsql.py`
2. Update `OBJECT_TYPE_MAPPING` dictionary
3. Restart application

#### Excluded System Schemas

**Location:** `engine/core/settings.py`

```python
# Default system schemas to exclude
DEFAULT_EXCLUDED_SCHEMAS = [
    'sys',
    'information_schema',
    'tempdb',
    'master',
    'msdb',
    'model',
]
```

**To modify:**
- **Recommended:** Use `EXCLUDED_SCHEMAS` environment variable in `.env`
- **Alternative:** Edit `engine/core/settings.py` for permanent changes

#### SQL Dialect Registration

**Location:** `engine/dialects/registry.py`

```python
DIALECT_REGISTRY = {
    'tsql': TSQLDialect,
    # Add new dialects here:
    # 'postgresql': PostgreSQLDialect,
    # 'mysql': MySQLDialect,
}
```

**To add a new SQL dialect:**
1. Implement dialect class in `engine/dialects/<dialect>.py`
   - Extend `BaseDialect`
   - Implement `objects_query` and `definitions_query` properties
2. Create YAML rules in `engine/rules/<dialect>/`
3. Register in `engine/dialects/registry.py`
4. Update `SQL_DIALECT` options in documentation

**See also:** [ARCHITECTURE.md - Adding Support for New SQL Dialects](ARCHITECTURE.md#adding-support-for-new-sql-dialects)

---

## Troubleshooting

### Container Build Fails

**Issue:** Build fails during creation

**Solution:**
1. Check Docker is running: `docker ps`
2. Rebuild container:
   - `Ctrl+Shift+P` → `Dev Containers: Rebuild Container`
3. Check Docker logs in VS Code Output panel

### Ports Already in Use

**Issue:** Port 8000 or 3000 already in use

**Solution:**
```bash
# Find process using port (Windows)
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use stop script
./stop-app.sh
```

### Python Dependencies Not Found

**Issue:** `ModuleNotFoundError` when running code

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Dependencies Not Found

**Issue:** `npm` errors or missing packages

**Solution:**
```bash
cd frontend
npm install
```

---

## Tips & Best Practices

### 1. Use Tasks Instead of Terminal Commands

Tasks are pre-configured and easier to run:
- `Ctrl+Shift+P` → `Tasks: Run Task`

### 2. Format on Save

Already configured! Just save files for auto-formatting.

### 3. Use Debugger Instead of Print Statements

Set breakpoints and press `F5` - much more powerful than `print()`.

### 4. Terminal Selection

Use integrated terminal:
- `` Ctrl+` `` to open/close terminal
- Terminal is already in the container
- Virtual environment pre-activated in scripts

### 5. Keep Container Running

Don't rebuild unless necessary:
- Container persists dependencies in volumes
- Rebuilding is slow (10-15 minutes)
- Only rebuild for Dockerfile/devcontainer.json changes

---

## References

- **Main Documentation:** [README.md](../README.md)
- **Quick Start Guide:** [QUICKSTART.md](../QUICKSTART.md)
- **Architecture Overview:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Configuration Reference:** [CONFIGURATION.md](CONFIGURATION.md)
- **Data Specifications:** [DATA_SPECIFICATIONS.md](DATA_SPECIFICATIONS.md)
- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Specification](https://containers.dev/)

---

## Contributing

When contributing, ensure:
1. Dev container builds successfully
2. Code is formatted: Black + isort (auto on save)
3. Environment variables documented in `.env.example`
4. DMV query changes documented in this file
5. YAML rule changes include examples

---

## License

This project is licensed under the MIT License - see [LICENSE](../LICENSE) file for details.

---

**Last Updated:** 2025-01-30
