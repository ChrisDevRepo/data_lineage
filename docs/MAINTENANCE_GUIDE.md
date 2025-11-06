# Data Lineage Visualizer - Maintenance & Troubleshooting Guide

**Version:** 1.0
**Last Updated:** 2025-11-06
**Audience:** DevOps, SRE, Support Engineers

---

## Table of Contents

1. [Health Monitoring](#health-monitoring)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Performance Tuning](#performance-tuning)
4. [Database Maintenance](#database-maintenance)
5. [Log Analysis](#log-analysis)
6. [Backup & Recovery](#backup--recovery)
7. [Operational Runbooks](#operational-runbooks)

---

## Health Monitoring

### Backend API Health Checks

**Endpoint:** `GET /health`

```bash
# Local development
curl http://localhost:8000/health

# Production
curl https://lineage-api-prod.azurewebsites.net/health

# Expected response
{
  "status": "healthy",
  "version": "4.0.3",
  "timestamp": "2025-11-06T12:34:56Z"
}
```

**Monitoring Thresholds:**
- Response time: <100ms (healthy), 100-500ms (degraded), >500ms (critical)
- Availability: >99.5% uptime
- HTTP 5xx errors: <1% of requests

### Frontend Health Indicators

**Indicators:**
1. **Load Time** - Initial page load <2 seconds
2. **API Connectivity** - Successful API calls to `/health`
3. **Console Errors** - No JavaScript errors in browser console
4. **Resource Loading** - All static assets load successfully

**Browser DevTools Check:**
```javascript
// Open browser console (F12)
fetch('/health')
  .then(r => r.json())
  .then(d => console.log('✅ API healthy:', d))
  .catch(e => console.error('❌ API unreachable:', e));
```

### Parser Performance Metrics

**Key Metrics:**
- Confidence rate: >95% high confidence (≥0.85)
- Parse success rate: >99%
- Parse time: <2 minutes for 200 SPs
- Memory usage: <2GB during parsing

**Check Current Stats:**
```bash
# From DuckDB workspace
python3 -c "
from lineage_v3.core import DuckDBWorkspace
with DuckDBWorkspace('data/lineage_workspace.duckdb') as db:
    stats = db.get_statistics()
    print(f'Objects: {stats[\"objects_count\"]}')
    print(f'High confidence: {stats[\"high_confidence_count\"]}')
    print(f'Confidence rate: {stats[\"high_confidence_rate\"]:.1%}')
"
```

---

## Common Issues & Solutions

### Issue 1: Backend Not Starting

**Symptoms:**
- `curl http://localhost:8000/health` fails
- Port 8000 not listening
- Process crashes immediately

**Diagnostic Steps:**

```bash
# 1. Check if port is already in use
lsof -i:8000
# If occupied: kill -9 <PID>

# 2. Check Python dependencies
python3 -c "import fastapi, duckdb, sqlglot; print('✅ Dependencies OK')"
# If failed: pip install -r requirements.txt

# 3. Check log output
python3 api/main.py
# Look for error messages in startup
```

**Common Causes & Fixes:**

| Cause | Symptom | Fix |
|-------|---------|-----|
| Port conflict | `Address already in use` | `lsof -ti:8000 \| xargs kill` |
| Missing dependencies | `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Permission error | `Permission denied: /tmp/jobs` | `chmod 777 /tmp/jobs` |
| Invalid .env | `KeyError: 'API_PORT'` | Verify `.env` file exists |

### Issue 2: Frontend Build Failures

**Symptoms:**
- `npm run build` fails
- TypeScript compilation errors
- Vite build hangs

**Diagnostic Steps:**

```bash
# 1. Clean install
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# 2. Type check
npm run type-check

# 3. Check Node.js version
node --version  # Should be 24.x+

# 4. Test development mode
npm run dev
```

**Common Fixes:**

```bash
# Out of memory during build
NODE_OPTIONS="--max-old-space-size=4096" npm run build

# TypeScript errors
npm run type-check  # Fix reported errors

# Dependency conflicts
npm install --legacy-peer-deps
```

### Issue 3: Parser Low Confidence Results

**Symptoms:**
- Confidence rate <95%
- Many SPs marked as 0.50 confidence
- Missing dependencies in lineage graph

**Diagnostic Steps:**

```bash
# 1. Check parser version
python3 -c "from lineage_v3 import __version__; print(__version__)"

# 2. Run parser validation
cd lineage_v3
python3 main.py validate

# 3. Check for low-confidence objects
python3 -c "
from lineage_v3.core import DuckDBWorkspace
with DuckDBWorkspace('data/lineage_workspace.duckdb') as db:
    low_conf = db.query('''
        SELECT o.name, lm.confidence, lm.primary_source
        FROM objects o
        JOIN lineage_metadata lm ON o.object_id = lm.object_id
        WHERE lm.confidence < 0.85
        ORDER BY lm.confidence
        LIMIT 10
    ''')
    for row in low_conf:
        print(f'{row[0]}: {row[1]:.2f} ({row[2]})')
"
```

**Troubleshooting:**

1. **SQLGlot Parse Failures**
   ```bash
   # Enable debug logging
   LOG_LEVEL=DEBUG python3 api/main.py

   # Check for specific error patterns in logs
   grep "SQLGlot failed" /tmp/backend.log
   ```

2. **Missing Query Logs**
   - Upload `query_logs.parquet` file for validation boost (0.85 → 0.95)
   - Ensure query log has SP execution records

3. **Complex SQL Patterns**
   - See [PARSING_USER_GUIDE.md](PARSING_USER_GUIDE.md) for supported patterns
   - Consider SP refactoring for better parsing

### Issue 4: Frontend Freezing on Large Datasets

**Symptoms:**
- Browser freezes when deselecting schemas
- Slow pan/zoom with >1,000 nodes
- Filter changes take >2 seconds

**Diagnostic Steps:**

```bash
# 1. Check dataset size
# In browser DevTools Console:
console.log('Nodes:', allData.length);
console.log('Edges:', edges.length);

# 2. Verify debouncing is enabled
# Check useDataFiltering.ts:36-74
grep -A 5 "shouldDebounce" frontend/hooks/useDataFiltering.ts

# 3. Check browser performance
# DevTools → Performance tab → Record → Reproduce freezing
```

**Solutions:**

| Issue | Fix |
|-------|-----|
| No debouncing | Verify `useDataFiltering.ts` has debounce logic (v2.9.1+) |
| Layout not cached | Check `layoutCache.ts` implementation |
| Too many nodes | Filter dataset before loading or upgrade to v2.9.1+ |
| Browser memory | Close other tabs, increase browser memory limit |

**Performance Verification:**
```typescript
// Browser console
performance.mark('filter-start');
// Deselect a schema
performance.mark('filter-end');
performance.measure('filter-time', 'filter-start', 'filter-end');
console.log(performance.getEntriesByName('filter-time')[0].duration);
// Should be <50ms with debouncing
```

### Issue 5: CORS Errors in Production

**Symptoms:**
```
Access to fetch at 'https://api.example.com/api/upload-parquet' from origin
'https://frontend.example.com' has been blocked by CORS policy
```

**Diagnostic Steps:**

```bash
# 1. Check current CORS settings (Azure)
az webapp cors show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME

# 2. Verify frontend domain matches
echo $FRONTEND_DOMAIN
# Should match allowed origin exactly (https://, no trailing slash)

# 3. Check backend code
grep "allow_origins" api/main.py
# Should include frontend domain
```

**Fixes:**

```bash
# Add frontend domain to CORS
az webapp cors add \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --allowed-origins "https://your-frontend.azurewebsites.net"

# Verify allow_credentials=True in code
grep -A 5 "CORSMiddleware" api/main.py
# Must have: allow_credentials=True
```

### Issue 6: Job Processing Stuck

**Symptoms:**
- Job status shows "processing" for >10 minutes
- No progress updates
- `/api/status/{job_id}` returns same percentage

**Diagnostic Steps:**

```bash
# 1. Check job files
ls -lh /tmp/jobs/{job_id}/
# Should see: status.json, parquet files, workspace.duckdb

# 2. Check background process
ps aux | grep "python.*background_tasks"
# If missing: job thread crashed

# 3. Read status file
cat /tmp/jobs/{job_id}/status.json
# Check for error messages

# 4. Check backend logs
tail -f /tmp/backend.log
# Look for exceptions or parse errors
```

**Fixes:**

| Cause | Fix |
|-------|-----|
| Thread crashed | Restart backend, re-upload parquet files |
| Large dataset timeout | Increase processing timeout (default: 10 minutes) |
| DuckDB corruption | Delete `/tmp/jobs/{job_id}/*.duckdb`, restart |
| Out of memory | Reduce dataset size or increase server memory |

---

## Performance Tuning

### Parser Optimization

**Incremental vs Full Refresh:**

```bash
# Incremental (default, 50-90% faster)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" \
  -F "files=@objects.parquet" ...

# Full refresh (use after parser version upgrade)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" \
  -F "files=@objects.parquet" ...
```

**When to use Full Refresh:**
- Parser version upgraded (new logic)
- Confidence threshold changed
- DuckDB schema changed
- Debugging parse results

**When to use Incremental:**
- Regular data updates
- Only metadata changed
- Small number of SP modifications

### Frontend Optimization

**Browser Performance Settings:**

```javascript
// In frontend/App.tsx
const PERFORMANCE_CONFIG = {
  MAX_NODES_WITHOUT_DEBOUNCE: 500,  // Debounce threshold
  DEBOUNCE_DELAY: 150,              // ms
  LAYOUT_CACHE_ENABLED: true,
  REACT_FLOW_ATTRIBUTION: false     // Disable attribution overlay
};
```

**Recommended Browser Settings:**
- Chrome/Edge: Enable "Hardware Acceleration"
- Firefox: `about:config` → `layout.frame_rate` = 60
- Close unused tabs (each tab consumes memory)

### Backend Optimization

**Uvicorn Server Settings:**

```bash
# Development (single worker)
python3 api/main.py

# Production (multiple workers) - Azure handles this
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**DuckDB Performance:**

```python
# In parser initialization
workspace = DuckDBWorkspace(
    workspace_path="lineage_workspace.duckdb",
    read_only=False,
    config={
        'threads': 4,           # Use 4 CPU cores
        'memory_limit': '2GB',  # Prevent OOM
        'temp_directory': '/tmp/duckdb_temp'
    }
)
```

---

## Database Maintenance

### DuckDB Workspace Files

**Location:** `/tmp/jobs/{job_id}/lineage_workspace.duckdb`

**Maintenance Tasks:**

```bash
# 1. Check database size
du -sh /tmp/jobs/*/lineage_workspace.duckdb

# 2. Vacuum database (reclaim space)
python3 -c "
import duckdb
conn = duckdb.connect('lineage_workspace.duckdb')
conn.execute('VACUUM')
conn.close()
"

# 3. Verify database integrity
python3 -c "
import duckdb
conn = duckdb.connect('lineage_workspace.duckdb', read_only=True)
tables = conn.execute('SHOW TABLES').fetchall()
print(f'✅ {len(tables)} tables found')
conn.close()
"
```

### Job Cleanup

**Automatic Cleanup:**
- Jobs older than 7 days auto-deleted (if configured)
- Failed jobs cleaned up after 24 hours

**Manual Cleanup:**

```bash
# Delete specific job
curl -X DELETE "http://localhost:8000/api/jobs/{job_id}"

# Clean all old jobs (30+ days)
find /tmp/jobs -type d -mtime +30 -exec rm -rf {} \;

# Clean failed jobs
python3 -c "
import os, json
from pathlib import Path
for job_dir in Path('/tmp/jobs').iterdir():
    status_file = job_dir / 'status.json'
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
            if status.get('status') == 'failed':
                print(f'Removing failed job: {job_dir.name}')
                os.system(f'rm -rf {job_dir}')
"
```

### Parquet File Storage

**Best Practices:**
- Store source parquet files in Azure Data Lake (not in app)
- Keep snapshots with timestamps (e.g., `snapshot_20251106.zip`)
- Document schema changes in CHANGELOG
- Test with sample data before full dataset

---

## Log Analysis

### Backend Logs

**Log Locations:**

| Environment | Location | Format |
|-------------|----------|--------|
| Local Dev | `/tmp/backend.log` | Text |
| Azure App Service | Application Insights | JSON |
| Azure (Stream) | `az webapp log tail` | Text |

**Key Log Patterns:**

```bash
# Parse failures
grep "SQLGlot failed" /tmp/backend.log

# Performance issues
grep "took.*seconds" /tmp/backend.log | grep -E "took [0-9]{2,}"

# API errors
grep "ERROR" /tmp/backend.log | tail -20

# Job processing
grep "Job.*processing" /tmp/backend.log
```

**Log Levels:**

| Level | When to Use | Example |
|-------|------------|---------|
| DEBUG | Development, troubleshooting | Parse step details |
| INFO | Production (default) | Job start/complete |
| WARNING | Unexpected but handled | Low confidence SP |
| ERROR | Requires attention | Parse crash, API error |

### Frontend Logs

**Browser Console:**

```javascript
// Enable debug logging
localStorage.setItem('debug', 'lineage:*');

// Disable debug logging
localStorage.removeItem('debug');

// View stored data
console.log('Loaded data:', localStorage.getItem('lineage_data'));
```

**Common Error Patterns:**

| Error | Cause | Fix |
|-------|-------|-----|
| `TypeError: Cannot read property 'map'` | API returned null | Check backend health |
| `Network Error` | Backend unreachable | Verify API URL in .env |
| `CORS policy` | CORS misconfiguration | See Issue #5 above |
| `Out of memory` | Dataset too large | Reduce nodes or upgrade RAM |

---

## Backup & Recovery

### Backup Strategy

**What to Backup:**
1. ✅ **Source Parquet Files** - Critical (versioned in Azure Data Lake)
2. ✅ **Configuration Files** - `.env.template`, `azure-*.yml`
3. ⚠️ **DuckDB Workspace** - Optional (can be regenerated from parquet)
4. ❌ **Job Files** - Not needed (ephemeral)

**Backup Commands:**

```bash
# Backup parquet snapshots
tar -czf lineage_backup_$(date +%Y%m%d).tar.gz \
  parquet_snapshots/*.parquet \
  .env.template

# Upload to Azure Storage
az storage blob upload \
  --account-name <storage-account> \
  --container-name backups \
  --name lineage_backup_$(date +%Y%m%d).tar.gz \
  --file lineage_backup_$(date +%Y%m%d).tar.gz
```

### Recovery Procedures

**Scenario 1: Backend Crash**

```bash
# 1. Restart backend
./stop-app.sh && ./start-app.sh

# 2. Verify health
curl http://localhost:8000/health

# 3. Re-upload parquet files if needed
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" \
  -F "files=@objects.parquet" ...
```

**Scenario 2: Corrupted DuckDB**

```bash
# 1. Delete corrupted workspace
rm -rf /tmp/jobs/{job_id}/lineage_workspace.duckdb*

# 2. Re-upload parquet files (full refresh)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" \
  -F "files=@objects.parquet" ...
```

**Scenario 3: Lost Parquet Files**

```bash
# 1. Download from Azure Data Lake
az storage blob download \
  --account-name <storage-account> \
  --container-name snapshots \
  --name latest/objects.parquet \
  --file objects.parquet

# Repeat for other parquet files

# 2. Re-upload to application
curl -X POST "http://localhost:8000/api/upload-parquet" ...
```

---

## Operational Runbooks

### Daily Operations

**Health Check (5 minutes):**

```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Backend Health ==="
curl -s http://localhost:8000/health | jq

echo "=== Frontend Access ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
echo

echo "=== Disk Usage ==="
df -h /tmp | grep -v Filesystem
du -sh /tmp/jobs

echo "=== Process Status ==="
ps aux | grep -E "python.*api|npm.*dev" | grep -v grep
```

### Weekly Operations

**Cleanup (15 minutes):**

```bash
#!/bin/bash
# weekly_cleanup.sh

# Remove old jobs (7+ days)
find /tmp/jobs -type d -mtime +7 -exec rm -rf {} \;

# Vacuum DuckDB files
for db in /tmp/jobs/*/lineage_workspace.duckdb; do
  [ -f "$db" ] && sqlite3 "$db" "VACUUM;"
done

# Clear old logs
find /tmp -name "*.log" -mtime +14 -delete
```

### Monthly Operations

**Performance Review (30 minutes):**

1. Review Application Insights metrics (if enabled)
2. Analyze parser confidence trends
3. Check for new low-confidence patterns
4. Review user feedback and issues
5. Update documentation as needed

---

## Related Documentation

- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - Architecture overview
- [SETUP_AND_DEPLOYMENT.md](SETUP_AND_DEPLOYMENT.md) - Installation guide
- [PARSING_USER_GUIDE.md](PARSING_USER_GUIDE.md) - SQL parsing details
- [api/README.md](../api/README.md) - Backend API reference
- [frontend/README.md](../frontend/README.md) - Frontend guide

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Status:** ✅ Production Ready
