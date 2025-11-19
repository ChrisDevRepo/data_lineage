# Database Connector Specification (v0.10.0)

**Document Version:** 1.0
**Feature Version:** v0.10.0
**Last Updated:** 2025-11-19

## Overview

The database connector feature enables direct metadata extraction from data warehouses and analytics platforms without requiring manual Parquet file generation. This feature is **optional** and **disabled by default** - users can choose between:

1. **Parquet Upload** (default): Upload pre-generated Parquet files from DMV extraction scripts
2. **Database Refresh** (optional): Connect directly to the database for automated metadata extraction

Both methods use the **same downstream processing pipeline**, ensuring consistent lineage analysis regardless of the data source.

## Feature Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  User triggers  │────────▶│  Database        │
│  refresh in UI  │         │  Connector       │
└─────────────────┘         │  (dialect-       │
                            │   specific)      │
                            └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Query DMVs      │
                            │  (YAML config)   │
                            └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Convert to      │
                            │  Parquet files   │
                            │  (objects.       │
                            │   definitions,   │
                            │   dependencies)  │
                            └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  SAME processing │◀── Parquet Upload
                            │  pipeline as     │    (manual files)
                            │  file upload     │
                            └──────────────────┘
```

## Metadata Contract

All database connectors MUST return data in this standardized format:

### StoredProcedureMetadata (Python Dataclass)

```python
@dataclass
class StoredProcedureMetadata:
    """Standard structure for stored procedure metadata."""
    schema_name: str                      # Required
    procedure_name: str                   # Required
    source_code: str                      # Required (full SQL definition)
    object_id: Optional[str] = None       # Optional (unique identifier)
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    definition_hash: Optional[bytes] = None  # For incremental refresh

    @property
    def full_name(self) -> str:
        """Return fully qualified name: schema.procedure"""
        return f"{self.schema_name}.{self.procedure_name}"
```

### Parquet File Output

Connectors must generate these three Parquet files:

#### 1. `objects.parquet`
| Column       | Type   | Description                          |
|--------------|--------|--------------------------------------|
| object_id    | int    | Unique identifier                    |
| schema_name  | str    | Database schema name                 |
| object_name  | str    | Stored procedure name                |
| object_type  | str    | Always 'P' for stored procedures     |

#### 2. `definitions.parquet`
| Column       | Type   | Description                          |
|--------------|--------|--------------------------------------|
| object_id    | int    | Matches objects.object_id            |
| definition   | str    | Full SQL source code                 |

#### 3. `dependencies.parquet`
| Column       | Type   | Description                          |
|--------------|--------|--------------------------------------|
| (empty)      | -      | Empty for direct DB connection*      |

\* **Note**: Dependencies are extracted during parsing (same as Parquet upload workflow), so this file can be empty for database connectors.

## YAML Query Configuration

Each database dialect has a YAML configuration file defining metadata extraction queries.

**Location**: `engine/connectors/queries/{dialect}/metadata.yaml`

### Structure

```yaml
# ==============================================================================
# {Database Name} Metadata Extraction Queries
# ==============================================================================
dialect: tsql  # Dialect identifier (matches SQL_DIALECT)
version: "1.0"

# Compatibility notes
# - List supported database versions
# - Note any limitations or special considerations

# Queries for extracting stored procedure metadata
queries:
  # Query 1: List all stored procedures with metadata (fast, no source code)
  list_stored_procedures:
    description: "Get list of all user stored procedures with metadata"
    sql: |
      SELECT
        schema_name,        -- Required: database schema
        procedure_name,     -- Required: procedure name
        object_id,          -- Required: unique identifier
        create_date,        -- Optional: creation timestamp
        modify_date,        -- Optional: modification timestamp
        definition_hash     -- Optional: hash of source code (for incremental refresh)
      FROM ...
      WHERE ...
      ORDER BY schema_name, procedure_name

  # Query 2: Get source code for a specific stored procedure
  get_procedure_source:
    description: "Get full SQL source code for a stored procedure by object_id"
    sql: |
      SELECT
        schema_name,        -- Required
        procedure_name,     -- Required
        source_code,        -- Required: full SQL definition
        modify_date         -- Optional
      FROM ...
      WHERE object_id = ?   -- Parameterized query (prevents SQL injection)

# Incremental refresh support (optional but recommended)
incremental:
  enabled: true
  hash_column: definition_hash     # Column name for procedure hash
  modified_column: modify_date     # Column name for modification date
  description: "Use definition_hash to detect changed procedures"
```

### Key Requirements

1. **Two Query Pattern**:
   - `list_stored_procedures`: Fast metadata scan (no source code)
   - `get_procedure_source`: Fetch full SQL for specific procedure

2. **Parameterized Queries**: Use `?` placeholders to prevent SQL injection

3. **Incremental Refresh**: Include hash column (e.g., SHA2_256 of source code)

4. **System Schema Filtering**: Exclude system schemas (e.g., `sys`, `information_schema`)

## Implementing a New Connector

### Step 1: Create YAML Query Configuration

Create `engine/connectors/queries/{dialect}/metadata.yaml`:

```yaml
dialect: snowflake
version: "1.0"

queries:
  list_stored_procedures:
    description: "List all stored procedures in Snowflake"
    sql: |
      SELECT
        PROCEDURE_SCHEMA as schema_name,
        PROCEDURE_NAME as procedure_name,
        PROCEDURE_ID as object_id,
        CREATED as create_date,
        LAST_ALTERED as modify_date,
        SHA2(PROCEDURE_DEFINITION, 256) as definition_hash
      FROM INFORMATION_SCHEMA.PROCEDURES
      WHERE PROCEDURE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'SNOWFLAKE')
      ORDER BY PROCEDURE_SCHEMA, PROCEDURE_NAME

  get_procedure_source:
    description: "Get procedure source code by ID"
    sql: |
      SELECT
        PROCEDURE_SCHEMA as schema_name,
        PROCEDURE_NAME as procedure_name,
        PROCEDURE_DEFINITION as source_code,
        LAST_ALTERED as modify_date
      FROM INFORMATION_SCHEMA.PROCEDURES
      WHERE PROCEDURE_ID = ?

incremental:
  enabled: true
  hash_column: definition_hash
  modified_column: modify_date
```

### Step 2: Create Python Connector Class

Create `engine/connectors/{dialect}_connector.py`:

```python
"""
{Database Name} connector for metadata extraction.
"""
import logging
from typing import List
from .base import DatabaseConnector, StoredProcedureMetadata, ConnectionError

logger = logging.getLogger(__name__)


class {Dialect}Connector(DatabaseConnector):
    """
    {Database Name} connector.

    Connection String Format:
        {example connection string}
    """

    def __init__(self, connection_string: str, timeout: int = 30):
        super().__init__(connection_string, dialect="{dialect}", timeout=timeout)
        self.connection = None

    def _connect(self):
        """Establish database connection."""
        try:
            # Import dialect-specific library
            import {db_library}

            # Parse connection string and connect
            conn = {db_library}.connect(
                self.connection_string,
                timeout=self.timeout
            )

            logger.info(f"{self.dialect} connection established")
            return conn

        except Exception as e:
            logger.error(f"Failed to connect to {self.dialect}: {e}")
            raise ConnectionError(f"Connection failed: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.connection = self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.connection:
            self.connection.close()
            logger.debug(f"{self.dialect} connection closed")

    def test_connection(self) -> bool:
        """Test if database connection is reachable."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")  # Simple test query
            cursor.fetchone()
            conn.close()
            logger.info(f"{self.dialect} connection test successful")
            return True
        except Exception as e:
            logger.error(f"{self.dialect} connection test failed: {e}")
            raise ConnectionError(f"Database not reachable: {e}")

    def list_procedures(self) -> List[StoredProcedureMetadata]:
        """List all stored procedures with metadata."""
        if not self.connection:
            raise ConnectionError("Not connected to database")

        cursor = self.connection.cursor()
        query = self.queries['queries']['list_stored_procedures']['sql']
        cursor.execute(query)

        procedures = []
        for row in cursor.fetchall():
            procedures.append(StoredProcedureMetadata(
                schema_name=row[0],
                procedure_name=row[1],
                object_id=str(row[2]),
                source_code="",  # Not fetched yet (performance)
                created_date=row[3] if len(row) > 3 else None,
                modified_date=row[4] if len(row) > 4 else None,
                definition_hash=row[5] if len(row) > 5 else None
            ))

        logger.info(f"Found {len(procedures)} stored procedures")
        return procedures

    def get_procedure_source(self, object_id: str) -> StoredProcedureMetadata:
        """Get full source code for a specific stored procedure."""
        if not self.connection:
            raise ConnectionError("Not connected to database")

        cursor = self.connection.cursor()
        query = self.queries['queries']['get_procedure_source']['sql']
        cursor.execute(query, (object_id,))  # Parameterized query

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Procedure not found: {object_id}")

        return StoredProcedureMetadata(
            schema_name=row[0],
            procedure_name=row[1],
            source_code=row[2],
            object_id=object_id,
            modified_date=row[3] if len(row) > 3 else None
        )
```

### Step 3: Register Connector in Factory

Update `engine/connectors/factory.py`:

```python
from .{dialect}_connector import {Dialect}Connector

CONNECTOR_REGISTRY = {
    "tsql": TsqlConnector,
    "{dialect}": {Dialect}Connector,  # Add your connector
}
```

### Step 4: Add Python Dependency

Update `requirements/api.txt`:

```
# Database Connectors (v0.10.0)
pyodbc==5.2.0                  # T-SQL
{library}=={version}           # {Database Name}
```

### Step 5: Document Connection String

Update `.env.example`:

```bash
# Example: {Database Name}
# DB_ENABLED=true
# DB_CONNECTION_STRING={example connection string}
```

## Connection String Examples

### T-SQL (SQL Server / Azure Synapse / Fabric)
```bash
DB_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=myserver.database.windows.net;DATABASE=mydb;UID=myuser;PWD=mypassword;Encrypt=yes
```

### PostgreSQL / Redshift
```bash
DB_CONNECTION_STRING=postgresql://myuser:mypassword@myhost:5432/mydb?sslmode=require
```

### Snowflake
```bash
DB_CONNECTION_STRING=snowflake://myuser:mypassword@myaccount.myregion.snowflakecomputing.com/mydb/myschema
```

### Oracle
```bash
DB_CONNECTION_STRING=oracle+cx_oracle://myuser:mypassword@myhost:1521/myservice
```

### BigQuery (via SQLAlchemy)
```bash
DB_CONNECTION_STRING=bigquery://myproject/mydataset
```

## Security Considerations

### Production Deployment

**⚠️ NEVER commit connection strings to version control!**

#### Option 1: Azure Key Vault (Recommended for Azure)
```bash
# .env (references Key Vault secret)
DB_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=https://myvault.vault.azure.net/secrets/db-connection-string)
```

#### Option 2: Docker Secrets (Recommended for containers)
```bash
# docker-compose.yml
services:
  api:
    environment:
      - DB_CONNECTION_STRING_FILE=/run/secrets/db_connection_string
    secrets:
      - db_connection_string

secrets:
  db_connection_string:
    file: ./secrets/db_connection_string.txt
```

#### Option 3: Environment Variables (CI/CD)
```bash
# Set in CI/CD pipeline or hosting platform
export DB_CONNECTION_STRING="..."
```

### SSL/TLS Configuration

Always enable SSL/TLS for production:

```bash
DB_SSL_ENABLED=true  # Enforced by default

# T-SQL: Encrypt=yes in connection string
# PostgreSQL: sslmode=require
# Snowflake: TLS enabled by default
```

### Connection Timeout

Set reasonable timeouts to prevent hanging connections:

```bash
DB_TIMEOUT=30  # Default: 30 seconds
```

### Credential Rotation

For automated credential rotation:
1. Use managed identities (Azure, AWS IAM)
2. Update connection string in Key Vault/secrets manager
3. Restart service to pick up new credentials

## Testing Your Connector

### Unit Tests

Create `tests/unit/connectors/test_{dialect}_connector.py`:

```python
import pytest
from engine.connectors import get_connector

def test_connection():
    """Test database connection."""
    connector = get_connector(
        dialect="{dialect}",
        connection_string="test_connection_string"
    )

    with connector:
        assert connector.test_connection()

def test_list_procedures():
    """Test listing stored procedures."""
    connector = get_connector(
        dialect="{dialect}",
        connection_string="test_connection_string"
    )

    with connector:
        procedures = connector.list_procedures()
        assert len(procedures) > 0
        assert procedures[0].schema_name
        assert procedures[0].procedure_name

def test_get_procedure_source():
    """Test fetching procedure source code."""
    connector = get_connector(
        dialect="{dialect}",
        connection_string="test_connection_string"
    )

    with connector:
        procedures = connector.list_procedures()
        if procedures:
            source = connector.get_procedure_source(procedures[0].object_id)
            assert source.source_code
```

### Manual Testing

1. **Enable database connection**:
   ```bash
   # .env
   DB_ENABLED=true
   DB_CONNECTION_STRING=your_test_connection_string
   SQL_DIALECT={dialect}
   ```

2. **Start the application**:
   ```bash
   ./start-app.sh
   ```

3. **Test connection**:
   - Open Import Data modal
   - Click "Refresh from Database" tab
   - Verify connection status banner shows "Database Connected"

4. **Test full refresh**:
   - Uncheck "Incremental Refresh"
   - Click "Refresh from Database"
   - Monitor progress and verify lineage appears

5. **Test incremental refresh**:
   - Make changes to a stored procedure in your database
   - Check "Incremental Refresh"
   - Click "Refresh from Database"
   - Verify only changed procedures are re-parsed

## Troubleshooting

### Connection Issues

**Problem**: "Database not reachable"

**Solutions**:
- Check network connectivity (`ping`, `telnet`)
- Verify firewall rules allow connection
- Test connection string with native client
- Check SSL/TLS requirements
- Verify credentials and permissions

### Hash-Based Incremental Refresh Not Working

**Problem**: Incremental refresh re-fetches all procedures

**Solutions**:
- Verify `incremental.enabled: true` in YAML
- Check that `hash_column` is computed correctly
- Ensure hash is deterministic (same SQL → same hash)
- Verify hash column is `VARBINARY` or equivalent

### Performance Issues

**Problem**: Refresh takes too long with many procedures

**Solutions**:
- Use incremental refresh (default)
- Optimize `list_stored_procedures` query (no JOIN if possible)
- Add database indexes on `object_id`, `schema_name`
- Increase `DB_TIMEOUT` for large databases
- Consider filtering schemas in query (`WHERE schema_name IN (...)`)

## Reference Implementation: T-SQL Connector

See `engine/connectors/tsql_connector.py` for the complete reference implementation.

**Key features**:
- pyodbc-based connection
- SHA2_256 hash for incremental refresh
- Parameterized queries for security
- Comprehensive error handling
- Context manager pattern
- Logging for debugging

## FAQ

### Q: Do I need to implement a connector for my database?

**A:** No, the database connector feature is optional. You can continue using Parquet file uploads (the default method).

### Q: Can I use both Parquet upload and database refresh?

**A:** Yes! Both methods use the same processing pipeline. Use whichever is more convenient for your workflow.

### Q: What databases are currently supported?

**A:** v0.10.0 includes T-SQL (SQL Server, Synapse, Fabric) as a reference implementation. Additional connectors can be added by following this specification.

### Q: Does database refresh support views and tables?

**A:** The current implementation focuses on stored procedures. Support for views and user-defined functions can be added by extending the YAML queries and metadata structures.

### Q: How does incremental refresh determine if a procedure changed?

**A:** It compares a hash (e.g., SHA2_256) of the procedure's source code. If the hash differs from the cached value, the procedure is re-fetched and re-parsed.

### Q: What happens if my database doesn't support hash functions?

**A:** Incremental refresh will fall back to comparing modification timestamps. If neither is available, set `incremental.enabled: false` in YAML and use full refresh only.

## Version History

| Version | Date       | Changes                                      |
|---------|------------|----------------------------------------------|
| 1.0     | 2025-11-19 | Initial specification for v0.10.0 release    |

## See Also

- `.env.example` - Environment configuration examples
- `engine/connectors/` - Connector implementation directory
- `engine/connectors/queries/` - YAML query configurations
- `engine/services/database_refresh.py` - Database refresh orchestration
- `api/main.py` - API endpoints (`/api/database/test-connection`, `/api/database/refresh`)

---

**License:** MIT
**Maintainer:** Data Lineage Visualizer Team
**Contact:** See repository README for support information
