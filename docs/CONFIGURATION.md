# Configuration Guide

**Complete reference for all environment variables and database setup**

---

## Table of Contents

- [Quick Setup](#quick-setup)
- [Environment Variables](#environment-variables)
- [Database Direct Connection](#database-direct-connection)
- [Security Best Practices](#security-best-practices)
- [Advanced Configuration](#advanced-configuration)

---

## Quick Setup

### Default Configuration (Works Out-of-the-Box)

No configuration needed! The application works with defaults:
- **SQL Dialect:** T-SQL (SQL Server/Azure SQL/Synapse/Fabric) - other dialects can be added
- **Data Source:** Parquet upload only
- **Log Level:** INFO
- **Runtime Mode:** Production

### Custom Configuration

```bash
# Copy template and edit
cp .env.example .env
```

---

## Environment Variables

### API Configuration

```bash
# CORS Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
```

**Development:** Use `http://localhost:3000`
**Production:** Add your frontend domain

---

### SQL Dialect

```bash
# Database dialect for parser
SQL_DIALECT=tsql
```

**Supported Values:**
- `tsql` - Microsoft SQL Server, Azure SQL, Synapse Analytics, Fabric (currently implemented)
- New dialects can be added through YAML rules + dialect implementation (see [ARCHITECTURE.md](ARCHITECTURE.md))

---

### Runtime Mode

```bash
# Runtime environment
RUN_MODE=production  # Options: demo | debug | production
```

| Mode | Use Case | Features |
|------|----------|----------|
| **production** | Default, live deployments | Optimized performance, INFO logging |
| **debug** | Development, troubleshooting | DEBUG logging, detailed errors |
| **demo** | Testing, demonstrations | Auto-load sample data (if available) |

---

### Logging Configuration

```bash
# Log level
LOG_LEVEL=INFO  # Options: DEBUG | INFO | WARNING | ERROR | CRITICAL

# Debug mode (additional validation)
DEBUG_MODE=false

# Log file retention (days)
LOG_RETENTION_DAYS=7
```

**Log Levels:**
- **DEBUG** - Per-object parsing details, rule matches
- **INFO** - Application lifecycle events
- **WARNING** - Non-critical issues (low parsing confidence)
- **ERROR** - Processing failures

**Log Location:** `logs/app.log`

---

### Schema Filtering

```bash
# Schemas to exclude from ALL processing
EXCLUDED_SCHEMAS=sys,information_schema,tempdb,master,msdb,model
```

---

### Path Configuration (Optional)

```bash
# DuckDB workspace file
PATH_WORKSPACE_FILE=lineage_workspace.duckdb

# Output directory for JSON
PATH_OUTPUT_DIR=lineage_output

# Parquet snapshots directory
PATH_PARQUET_DIR=parquet_snapshots
```

**Defaults work for most cases** - only change for custom deployment structures.

---

## Database Direct Connection

---

### Enable Database Connection

**Step 1: Configure `.env`**

```bash
DB_ENABLED=true
DB_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=your-server;DATABASE=your-db;UID=user;PWD=password;Encrypt=yes
DB_TIMEOUT=30
DB_SSL_ENABLED=true
```

**Step 2: Restart Application**

```bash
./stop-app.sh
./start-app.sh
```

**Step 3: Refresh from UI**

Click **"Refresh from Database"** button in Import modal.

---

## Troubleshooting

### Configuration Not Applied

1. Verify `.env` file exists (not `.env.example`)
2. Check syntax (no quotes around values)
3. Restart application: `./stop-app.sh && ./start-app.sh`

### Database Connection Fails

**Enable DEBUG logging:**
```bash
LOG_LEVEL=DEBUG
```

Check logs at `logs/app.log` for connection details.

### Parser Shows No Dependencies

1. Verify Parquet files uploaded successfully
2. Check `SQL_DIALECT` matches your database
3. Verify `EXCLUDED_SCHEMAS` not filtering everything
4. Enable DEBUG logging to see per-object parsing details

---

## Configuration Reference

**Complete `.env` template:**

```bash
# API
ALLOWED_ORIGINS=http://localhost:3000

# Dialect
SQL_DIALECT=tsql

# Runtime
RUN_MODE=production
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=7

# Filtering
EXCLUDED_SCHEMAS=sys,information_schema,tempdb

# Database (optional, disabled by default)
# DB_ENABLED=false
# DB_CONNECTION_STRING=
# DB_TIMEOUT=30
# DB_SSL_ENABLED=true

# Paths (optional, defaults work for most)
# PATH_WORKSPACE_FILE=lineage_workspace.duckdb
# PATH_OUTPUT_DIR=lineage_output
# PATH_PARQUET_DIR=parquet_snapshots
```

---

**See Also:**
- [QUICKSTART.md](../QUICKSTART.md) - Quick setup guide
- [DATA_SPECIFICATIONS.md](DATA_SPECIFICATIONS.md) - Parquet schemas, API endpoints
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design, parser internals
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development environment, YAML rules, DMV configuration
