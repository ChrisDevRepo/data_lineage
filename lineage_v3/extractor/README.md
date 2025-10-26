# Synapse DMV Extractor

**Standalone utility to export Azure Synapse metadata for Vibecoding Lineage Parser v2.0**

## Overview

This tool extracts metadata from your Azure Synapse Dedicated SQL Pool using Dynamic Management Views (DMVs) and exports it to Parquet files. These Parquet files serve as input for the Vibecoding Lineage Parser v2.0, which generates data lineage graphs.

**Key Features:**
- Standalone script - no dependencies on the lineage parser
- Exports 4 Parquet files containing all necessary metadata
- Works with Azure Synapse Dedicated SQL Pool
- Supports both .env file and command-line credentials
- Optional query log extraction (can be skipped if DMV access restricted)

## Prerequisites

### System Requirements
- Python >= 3.10
- Microsoft ODBC Driver 18 for SQL Server

### Python Dependencies
```bash
pip install pyodbc pandas pyarrow python-dotenv
```

### Azure Synapse Permissions

Your SQL user needs the following permissions:

```sql
-- Minimum required permissions
GRANT VIEW DATABASE STATE TO [your_username];
GRANT VIEW DEFINITION TO [your_username];

-- For query logs (optional)
GRANT VIEW SERVER STATE TO [your_username];
```

## Installation

### Option 1: Standalone Script (Recommended for External Users)

1. Download the extractor script:
   ```bash
   wget https://raw.githubusercontent.com/yourorg/ws-psidwh/main/lineage_v3/extractor/synapse_dmv_extractor.py
   ```

2. Install dependencies:
   ```bash
   pip install pyodbc pandas pyarrow python-dotenv
   ```

3. Verify ODBC driver installation:
   ```bash
   # Linux/macOS
   odbcinst -j

   # Windows
   # Check "ODBC Data Sources" in Control Panel
   ```

### Option 2: Clone Full Repository

```bash
git clone https://github.com/yourorg/ws-psidwh.git
cd ws-psidwh
pip install -r requirements.txt
```

## Configuration

### Method 1: Using .env File (Recommended)

Create a `.env` file in the same directory as the script:

```env
SYNAPSE_SERVER=yourserver.sql.azuresynapse.net
SYNAPSE_DATABASE=yourdatabase
SYNAPSE_USERNAME=youruser
SYNAPSE_PASSWORD=yourpassword
```

**Security Note:** Never commit `.env` files to version control!

### Method 2: Command-Line Arguments

Pass credentials directly (not recommended for production):

```bash
python synapse_dmv_extractor.py \
    --server yourserver.sql.azuresynapse.net \
    --database yourdatabase \
    --username youruser \
    --password yourpassword \
    --output parquet_snapshots/
```

## Usage

### Basic Usage

```bash
# Extract all DMVs to parquet_snapshots/ directory
python synapse_dmv_extractor.py --output parquet_snapshots/
```

### Advanced Options

```bash
# Skip query logs (if DMV access restricted)
python synapse_dmv_extractor.py --skip-query-logs --output parquet_snapshots/

# Use custom .env file location
python synapse_dmv_extractor.py --env-file /path/to/.env --output parquet_snapshots/

# Specify custom output directory
python synapse_dmv_extractor.py --output /data/synapse_metadata/
```

### Get Help

```bash
python synapse_dmv_extractor.py --help
```

## Output Files

The extractor generates 4 Parquet files:

| File | Source DMVs | Size (Typical) | Description |
|------|-------------|----------------|-------------|
| **objects.parquet** | `sys.objects`, `sys.schemas` | ~100 KB - 1 MB | All database objects (tables, views, procedures) with metadata |
| **dependencies.parquet** | `sys.sql_expression_dependencies` | ~50 KB - 500 KB | Object dependencies (which objects reference which) |
| **definitions.parquet** | `sys.sql_modules` | ~500 KB - 5 MB | DDL definitions for views and procedures |
| **query_logs.parquet** | `sys.dm_pdw_exec_requests` | ~1 MB - 10 MB | Recent query execution logs (last 7 days, max 10,000 queries) |

**Note:** `query_logs.parquet` is optional. Use `--skip-query-logs` if you don't have `VIEW SERVER STATE` permission.

## Example Output

```
======================================================================
Synapse DMV Extractor
======================================================================
Server: yourserver.sql.azuresynapse.net
Database: yourdatabase
Output Directory: parquet_snapshots
Timestamp: 2025-10-26 14:30:00
======================================================================

[INFO] Connecting to yourserver.sql.azuresynapse.net...
[SUCCESS] Connected to database: yourdatabase
[INFO] Extracting database objects (tables, views, procedures)...
[SUCCESS] Extracted 2,847 rows in 3.42s
[INFO] Saving to parquet_snapshots/objects.parquet...
[SUCCESS] Saved objects.parquet (428.15 KB)

[INFO] Extracting object dependencies...
[SUCCESS] Extracted 5,621 rows in 4.18s
[INFO] Saving to parquet_snapshots/dependencies.parquet...
[SUCCESS] Saved dependencies.parquet (256.82 KB)

[INFO] Extracting object definitions (DDL)...
[SUCCESS] Extracted 1,523 rows in 5.67s
[INFO] Saving to parquet_snapshots/definitions.parquet...
[SUCCESS] Saved definitions.parquet (2.34 MB)

[INFO] Extracting query execution logs (last 7 days, max 10,000)...
[SUCCESS] Extracted 10,000 rows in 12.45s
[INFO] Saving to parquet_snapshots/query_logs.parquet...
[SUCCESS] Saved query_logs.parquet (4.87 MB)

======================================================================
Extraction Complete!
======================================================================

Generated Files:
  - objects: parquet_snapshots/objects.parquet
  - dependencies: parquet_snapshots/dependencies.parquet
  - definitions: parquet_snapshots/definitions.parquet
  - query_logs: parquet_snapshots/query_logs.parquet

Next Steps:
  Run lineage parser: python lineage_v3/main.py run --parquet parquet_snapshots
======================================================================
```

## Troubleshooting

### Connection Issues

**Error:** `[ERROR] Connection failed: Login failed for user`

**Solution:**
- Verify credentials in .env file
- Check firewall rules in Azure Portal (Add your IP address)
- Verify SQL authentication is enabled (not just Azure AD)

---

**Error:** `[ERROR] Connection failed: Driver not found`

**Solution:**
- Install Microsoft ODBC Driver 18 for SQL Server
- Linux: https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
- Windows: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
- macOS: `brew install msodbcsql18`

### Permission Issues

**Error:** `[ERROR] Failed to extract query execution logs: VIEW SERVER STATE permission denied`

**Solution:**
- Use `--skip-query-logs` flag
- Or request `VIEW SERVER STATE` permission from your DBA

---

**Error:** `[ERROR] Failed to extract object definitions: VIEW DEFINITION permission denied`

**Solution:**
- Contact your DBA to grant `VIEW DEFINITION` permission
- This permission is required for the extractor to work

### Performance Issues

**Slow extraction on large databases:**

The extractor processes the following volumes:
- Objects: ~1000-5000 rows (fast)
- Dependencies: ~5000-50000 rows (moderate)
- Definitions: ~1000-10000 rows (moderate, large DDL text)
- Query Logs: 10,000 rows max (can be slow)

**Optimization:**
- Use `--skip-query-logs` if you don't need runtime validation
- Run during off-peak hours for large databases
- Consider increasing `Connection Timeout` in the script if needed

## Data Privacy & Security

### What Data is Extracted?

The extractor captures **metadata only** - no actual table data is extracted:

- **objects.parquet**: Object names, schemas, types, timestamps
- **dependencies.parquet**: Dependency relationships (object_id references)
- **definitions.parquet**: DDL source code (CREATE PROCEDURE, CREATE VIEW, etc.)
- **query_logs.parquet**: Query text and execution metadata (no result sets)

### Security Best Practices

1. **Credentials:**
   - Use `.env` file, never hardcode passwords
   - Add `.env` to `.gitignore`
   - Use Azure Key Vault in production environments

2. **Network:**
   - Use Azure Private Link for production
   - Restrict firewall rules to specific IPs
   - Enable SSL/TLS encryption (already enabled in connection string)

3. **File Handling:**
   - Store Parquet files in secure locations
   - Set appropriate file permissions (chmod 600)
   - Delete old snapshots after analysis

## Scheduling Automated Extractions

### Linux/macOS (cron)

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/extractor && /usr/bin/python3 synapse_dmv_extractor.py --output /data/snapshots/$(date +\%Y\%m\%d) >> /var/log/dmv_extractor.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2:00 AM)
4. Action: Start a program
   - Program: `python`
   - Arguments: `synapse_dmv_extractor.py --output C:\snapshots\%date:~-4,4%%date:~-10,2%%date:~-7,2%`
   - Start in: `C:\path\to\extractor`

### Azure DevOps Pipeline

```yaml
# azure-pipelines.yml
trigger: none

schedules:
- cron: "0 2 * * *"
  displayName: Daily DMV extraction
  branches:
    include:
    - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.12'

- script: |
    pip install pyodbc pandas pyarrow python-dotenv
  displayName: 'Install dependencies'

- script: |
    python lineage_v3/extractor/synapse_dmv_extractor.py \
      --server $(SYNAPSE_SERVER) \
      --database $(SYNAPSE_DATABASE) \
      --username $(SYNAPSE_USERNAME) \
      --password $(SYNAPSE_PASSWORD) \
      --output $(Build.ArtifactStagingDirectory)/parquet_snapshots
  displayName: 'Extract DMV data'

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: '$(Build.ArtifactStagingDirectory)/parquet_snapshots'
    artifactName: 'dmv_snapshots'
```

## Integration with Lineage Parser

Once you've extracted the Parquet files, use them with the Vibecoding Lineage Parser v2.0:

```bash
# Run lineage analysis
python lineage_v3/main.py run --parquet parquet_snapshots/

# Output: lineage.json, frontend_lineage.json, lineage_summary.json
```

For more information about the lineage parser, see the main documentation.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-26 | Initial release - Production-ready extractor for external users |

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourorg/ws-psidwh/issues
- Documentation: [lineage_specs_v2.md](../../lineage_specs_v2.md)

## License

Copyright (c) 2025 Vibecoding. All rights reserved.
