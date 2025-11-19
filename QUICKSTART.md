# Quick Start Guide

**Audience:** Power Users & DBAs
**Time to Deploy:** 5-10 minutes
**License:** MIT (Copyright 2025 Christian Wagner)

---

## Installation (One Command)

```bash
# Clone and install
git clone <repo-url> && cd data_lineage
pip install -r requirements.txt
./start-app.sh
```

**That's it!** Application runs on:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Configuration (Optional)

**Default:** Works out-of-the-box, no configuration needed.

**Custom Settings:**
```bash
cp .env.example .env
# Edit .env for custom configuration
```

### Key Configuration Options

#### 1. Database Dialect (Multi-Database Support)
```bash
SQL_DIALECT=tsql  # Default: SQL Server/Synapse/Fabric
```

**Supported Dialects:**
- `tsql` - SQL Server, Azure SQL, Synapse Analytics, Microsoft Fabric
- `postgres` - PostgreSQL
- `snowflake` - Snowflake Data Cloud
- `oracle` - Oracle Database
- `bigquery` - Google BigQuery
- `redshift` - Amazon Redshift

#### 2. Runtime Mode
```bash
RUN_MODE=production  # demo | debug | production
LOG_LEVEL=INFO       # DEBUG for detailed parsing logs
LOG_RETENTION_DAYS=7 # Auto-cleanup old logs
```

#### 3. Schema Filtering
```bash
# Schemas to exclude from all processing
EXCLUDED_SCHEMAS=sys,information_schema,tempdb,master,msdb,model
```

#### 4. Database Direct Connection (v0.10.0 - OPTIONAL)

**Disabled by default.** Enable for automated metadata refresh:

```bash
DB_ENABLED=true
DB_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_user;PWD=your_password;Encrypt=yes
DB_TIMEOUT=30
DB_SSL_ENABLED=true
```

**Security Best Practices:**
- **Development:** Use `.env` file (gitignored)
- **Production:** Use Azure Key Vault references:
  ```bash
  DB_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/db-connection)
  ```
- **Docker:** Use Docker secrets
- **Never commit** connection strings to git!

**Connection String Example (MSSQL):**

| Database | Example |
|----------|---------|
| **SQL Server/Synapse (MSSQL)** | `DRIVER={ODBC Driver 18 for SQL Server};SERVER=myserver;DATABASE=mydb;UID=user;PWD=pass;Encrypt=yes` |
| PostgreSQL | `postgresql://user:password@host:5432/database?sslmode=require` |
| Snowflake | `snowflake://user:password@account.region.snowflakecomputing.com/database/schema` |

**See:** [docs/DATABASE_CONNECTOR_SPECIFICATION.md](docs/DATABASE_CONNECTOR_SPECIFICATION.md) for complete connection details.

---

## Data Sources

### Option A: Parquet Upload (Default)

**Upload metadata files via UI or API:**

```bash
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" \
  -F "files=@objects.parquet" \
  -F "files=@definitions.parquet" \
  -F "files=@dependencies.parquet"
```

**Required Files (3):**
1. `objects.parquet` - From `sys.objects`, `sys.schemas`
2. `definitions.parquet` - From `sys.sql_modules`
3. `dependencies.parquet` - From `sys.sql_expression_dependencies`

**Optional Files (2):**
- `query_logs.parquet` - From `sys.dm_pdw_exec_requests` (validation)
- `table_columns.parquet` - From `sys.tables`, `sys.columns` (DDL)

**Output:** JSON format saved to `data/latest_frontend_lineage.json`

### Option B: Database Direct Connection (v0.10.0)

**For DBAs who want automated refresh:**

1. **Enable in `.env`:**
   ```bash
   DB_ENABLED=true
   DB_CONNECTION_STRING=<your-connection-string>
   ```

2. **Restart app:** `./stop-app.sh && ./start-app.sh`

3. **Click "Refresh from Database"** in Import modal

**Features:**
- **Incremental Refresh:** Only processes changed procedures (hash-based detection)
- **Same Pipeline:** Uses identical processing as Parquet upload
- **Metadata Cache:** Tracks previous hashes for efficiency
- **Multi-Database:** Extensible connector framework

### Option C: JSON Export/Import

**Download Processed Lineage:**
```bash
# Export current lineage to JSON file
curl http://localhost:8000/api/latest-data > my_lineage.json
```

**JSON Format:**
```json
[
  {
    "id": 123,
    "label": "spMyProcedure",
    "type": "P",
    "schema": "dbo",
    "confidence": 100,
    "sources": [101, 102],
    "targets": [201],
    "definition": "CREATE PROCEDURE..."
  }
]
```

**Use Cases:**
- Backup lineage data
- Share with team members
- Version control for metadata
- Offline analysis

**Location:** `data/latest_frontend_lineage.json`

---

## Power User Features (v0.9.0)

### YAML Rule Engine

**Customize SQL preprocessing without Python code!**

**Location:** `engine/rules/{dialect}/`


**Example Rule (T-SQL Target Extraction):**
```yaml
# Extracts T-SQL specific target patterns (SELECT INTO, CTAS)
name: extract_targets_tsql
description: |
  Extract T-SQL specific target table references.
  Handles SELECT INTO and CREATE TABLE AS SELECT patterns.
dialect: tsql
category: extraction
enabled: true
priority: 10
rule_type: extraction
extraction_target: target
pattern_type: regex
pattern: (?i)(?:\bINTO\s+([^\s,;()]+(?:\s+FROM)?)|\bCREATE\s+TABLE\s+([^\s,;()]+)\s+AS\s+SELECT)
debug:
  log_matches: true
  log_replacements: false
  show_context_lines: 2
metadata:
  author: vibecoding
  created: "2025-11-19"
  affects_lineage: true
  impact: "Extracts T-SQL specific target patterns (SELECT INTO, CTAS)."
```

**Add Custom Rules:**
1. Copy `engine/rules/TEMPLATE.yaml`
2. Edit pattern and replacement
3. Save to `engine/rules/{your-dialect}/`
4. Restart application

**Documentation:**
- [engine/rules/README.md](engine/rules/README.md) - Complete guide
- [engine/rules/YAML_STRUCTURE.md](engine/rules/YAML_STRUCTURE.md) - Field reference

### Developer Mode

**Access:** Help (?) → "For Developers" → "Open Developer Panel"

**Features:**
- **Logs Tab:** Real-time log viewer (last 500 entries)
- **YAML Rules Tab:** Browse and inspect all active rules
- **Reset to Defaults:** Restore factory rules with one click

**Enable DEBUG Logging:**
```bash
# .env file
LOG_LEVEL=DEBUG
```

**DEBUG Output Format:**
```
[PARSE] dbo.spMyProc: Path=[Regex-only] Regex=[7S + 4T] Final=[7S + 4T] Confidence=100
```

---

## Parser Performance

**Current Results (v4.3.3):**
- **100% success rate** (349/349 stored procedures)
- **82.5% perfect** (288 SPs at confidence 100)
- **7.4% good** (26 SPs at confidence 85)
- **10.0% acceptable** (35 SPs at confidence 75)
- **Zero parse failures**

**Architecture:**
1. **Regex-First Baseline** - Full DDL scan (100% coverage)
2. **YAML Regex Extraction** - Business users can maintain patterns
3. **UNION Strategy** - Keeps all findings from both methods
4. **Post-Processing** - Removes system objects, temp tables
5. **Confidence Scoring** - (found / expected) * 100

---

## Testing & Validation

**Unit Tests (73 tests):**
```bash
source venv/bin/activate
pytest tests/unit/ -v
```

**Integration Tests (64 tests):**
```bash
source venv/bin/activate
pytest tests/integration/ -v
```

**Frontend E2E Tests (Playwright):**
```bash
cd frontend
npm run test:e2e
```

**Parser Validation:**
```bash
source venv/bin/activate
python scripts/testing/check_parsing_results.py
```

---

## Deployment

### Azure Static Web Apps

```bash
# Frontend
cd frontend && npm run build

# Deploy
az staticwebapp deploy \
  --name <app-name> \
  --resource-group <rg-name> \
  --source-path ./dist
```

### Docker

```bash
# Build
docker build -t lineage-viz .

# Run
docker run -p 8000:8000 -p 3000:3000 lineage-viz
```

**Environment Variables:** Pass via `-e` flag or Docker secrets

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port conflicts | Run `./stop-app.sh` to kill existing processes |
| Missing dependencies | `pip install -r requirements.txt && cd frontend && npm install` |
| Low confidence scores | Add `@LINEAGE_INPUTS`/`@LINEAGE_OUTPUTS` hints to SP comments |
| CORS errors | Check `ALLOWED_ORIGINS` in `.env` |
| Parser issues | Set `LOG_LEVEL=DEBUG` and check `/api/debug/logs` |
| Rule debugging | Set `debug.log_matches: true` in YAML rule |

---

## Documentation

### For Power Users
- **[engine/rules/README.md](engine/rules/README.md)** - YAML rules system
- **[.env.example](.env.example)** - All configuration options
- **[CLAUDE.md](CLAUDE.md)** - Complete technical reference

### For DBAs
- **[docs/DATABASE_CONNECTOR_SPECIFICATION.md](docs/DATABASE_CONNECTOR_SPECIFICATION.md)** - Database setup
- **Metadata Contract** - Required DMV queries
- **Security Best Practices** - Key Vault integration

### For Developers
- **[CLAUDE.md](CLAUDE.md)** - Development guide
- **[docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)** - Parser architecture
- **[.github/workflows/README.md](.github/workflows/README.md)** - CI/CD workflows

---

## Support

**Issues:** Use GitHub issue tracker
**Developer Guide:** See [CLAUDE.md](CLAUDE.md)
**License:** MIT - See [LICENSE](LICENSE)

---

**Built with:** [Claude Code](https://claude.com/claude-code)
**Status:** Production Ready v0.10.0
**Author:** Christian Wagner
