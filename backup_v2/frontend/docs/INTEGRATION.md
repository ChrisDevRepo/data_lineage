# Backend Integration Guide

**Application:** Data Lineage Visualizer
**Backend:** Python Lineage Parser v3.0
**Last Updated:** 2025-10-26

---

## Table of Contents

1. [Overview](#overview)
2. [Data Flow Architecture](#data-flow-architecture)
3. [JSON Data Contract](#json-data-contract)
4. [Integration Methods](#integration-methods)
5. [Development Workflow](#development-workflow)
6. [Production Workflow](#production-workflow)
7. [Testing Integration](#testing-integration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The frontend and backend are **decoupled** systems that communicate via JSON files:

```
┌─────────────────────────────────────┐
│   Python Lineage Parser (Backend)   │
│                                      │
│   Input:  Parquet snapshots (DMVs)  │
│   Process: Extract → Parse → Merge  │
│   Output: JSON files                │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   lineage_output/                    │
│   ├── lineage.json         (internal)│
│   ├── frontend_lineage.json  ⭐ THIS │
│   └── lineage_summary.json  (stats) │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   React Frontend (Visualizer)        │
│                                       │
│   Input:  JSON (DataNode[])          │
│   Process: Graph → Layout → Render   │
│   Output: Interactive visualization  │
└───────────────────────────────────────┘
```

**Key Points:**
- ✅ No API calls or real-time communication
- ✅ Frontend loads JSON files statically
- ✅ Backend runs independently, generates files
- ✅ Perfect for development and production

---

## Data Flow Architecture

### Development Environment (Same Devcontainer)

```
┌─────────────────────────────────────────────────────────┐
│          VSCode Devcontainer (ws-psidwh)               │
│                                                         │
│  ┌─────────────────┐          ┌────────────────────┐  │
│  │  Terminal 1     │          │   Terminal 2       │  │
│  │                 │          │                    │  │
│  │  Python Backend │          │   React Frontend   │  │
│  │                 │          │                    │  │
│  │  $ python       │          │   $ cd frontend    │  │
│  │    lineage_v3/  │          │   $ npm run dev    │  │
│  │    main.py run  │────┐     │                    │  │
│  │                 │    │     │   Serves on :3000  │  │
│  └─────────────────┘    │     └────────────────────┘  │
│                          │                             │
│                          ▼                             │
│         ┌────────────────────────────┐                │
│         │  lineage_output/           │                │
│         │  frontend_lineage.json     │                │
│         └────────────┬─────────────── │                │
│                      │                │                │
└──────────────────────┼────────────────┼────────────────┘
                       │                │
                       └────────────────┘
                  User loads via Import Data modal
```

### Production Environment (Separate Deployments)

```
┌──────────────────────────┐
│   Synapse Data Warehouse │
│   (Azure SQL)            │
└────────┬─────────────────┘
         │ DMV snapshots (Parquet)
         ▼
┌──────────────────────────────┐
│   Python Script (Scheduled)   │
│   Runs: lineage_v3/main.py    │
│   Output: frontend_lineage.json│
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   Azure Blob Storage         │
│   OR                         │
│   File Share / CDN           │
└────────┬─────────────────────┘
         │ HTTPS URL
         ▼
┌──────────────────────────────┐
│   React App (Azure Web App)  │
│   Loads JSON via fetch() OR  │
│   Imports via UI             │
└──────────────────────────────┘
```

---

## JSON Data Contract

### Frontend Input Format: `frontend_lineage.json`

**Type:** Array of DataNode objects

**Required Structure:**
```typescript
type DataNode = {
  id: string;                    // Must be unique, format: "node_X"
  name: string;                  // Object name (e.g., "DimCustomers")
  schema: string;                // UPPERCASE schema name
  object_type: 'Table' | 'View' | 'Stored Procedure';
  description?: string;           // Optional description
  data_model_type?: 'Dimension' | 'Fact' | 'Lookup' | 'Other';
  inputs: string[];               // Array of node IDs this depends on
  outputs: string[];              // Array of node IDs that depend on this
};
```

**Example:**
```json
[
  {
    "id": "node_0",
    "name": "DimCustomers",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Table",
    "description": "Customer dimension table",
    "data_model_type": "Dimension",
    "inputs": ["node_5"],
    "outputs": ["node_1", "node_3"]
  },
  {
    "id": "node_1",
    "name": "spLoadFactOrders",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Stored Procedure",
    "description": "Load fact table for orders",
    "data_model_type": "Other",
    "inputs": ["node_0", "node_2"],
    "outputs": ["node_4"]
  }
]
```

### Backend Output Format: `lineage.json` (Internal)

**Different from frontend format:**
- Uses integer `object_id` instead of `"node_X"` strings
- Contains additional fields: `modify_date`, `provenance`, `confidence`
- Not directly consumed by frontend

**Backend generates BOTH:**
1. `lineage.json` - Internal format (for backend processing)
2. `frontend_lineage.json` - Frontend format (for visualization)

---

## Integration Methods

### Method 1: File-Based (Current - Development)

**Best for:** Development in same devcontainer

**Steps:**

1. **Generate lineage data:**
   ```bash
   cd /workspaces/ws-psidwh
   python lineage_v3/main.py run --parquet parquet_snapshots/
   ```

2. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Load data in UI:**
   - Click **Import Data** button
   - Click **Upload File**
   - Select `../lineage_output/frontend_lineage.json`
   - Click **Apply Changes**

**Pros:**
- ✅ Simple, no configuration needed
- ✅ Works offline
- ✅ Perfect for development

**Cons:**
- ⚠️ Manual refresh needed
- ⚠️ File path must be accessible

---

### Method 2: Rebuild with Production Data

**Best for:** Production deployment with static data

**Steps:**

1. **Generate lineage data:**
   ```bash
   python lineage_v3/main.py run --parquet parquet_snapshots/
   ```

2. **Copy JSON to frontend:**
   ```bash
   cp lineage_output/frontend_lineage.json frontend/src/production-data.json
   ```

3. **Update `frontend/utils/data.ts`:**
   ```typescript
   import productionData from '../src/production-data.json';

   export const generateSampleData = (): DataNode[] => {
     // Return production data instead of sample
     return productionData as DataNode[];
   };
   ```

4. **Rebuild frontend:**
   ```bash
   cd frontend
   npm run build
   ```

5. **Deploy `dist/` folder to Azure**

**Pros:**
- ✅ Data embedded in app
- ✅ Fast initial load
- ✅ No external dependencies

**Cons:**
- ⚠️ Requires rebuild to update data
- ⚠️ Bundle size increases

---

### Method 3: Fetch from URL (Production)

**Best for:** Production with dynamic data updates

**Architecture:**
```
Azure Blob Storage (Public)
  └── frontend_lineage.json
       ↓ (HTTPS)
Azure Web App (React)
  └── fetch() on load
```

**Steps:**

1. **Upload JSON to Azure Blob Storage:**
   ```bash
   # Upload to Azure Storage
   az storage blob upload \
     --account-name <storage-account> \
     --container-name lineage-data \
     --name frontend_lineage.json \
     --file lineage_output/frontend_lineage.json \
     --content-type application/json

   # Get public URL
   echo "https://<storage-account>.blob.core.windows.net/lineage-data/frontend_lineage.json"
   ```

2. **Update frontend to fetch:**

   **File:** `frontend/App.tsx`
   ```typescript
   const [allData, setAllData] = useState<DataNode[]>([]);

   useEffect(() => {
     // Fetch production data on mount
     fetch('https://youraccount.blob.core.windows.net/lineage-data/frontend_lineage.json')
       .then(res => res.json())
       .then(data => {
         setAllData(data);
         addNotification('Production data loaded successfully', 'info');
       })
       .catch(err => {
         console.error('Failed to load data:', err);
         setAllData(generateSampleData()); // Fallback to sample
         addNotification('Using sample data (failed to load production data)', 'error');
       });
   }, []);
   ```

3. **Enable CORS on Blob Storage:**
   ```bash
   az storage cors add \
     --services b \
     --methods GET \
     --origins https://your-webapp.azurewebsites.net \
     --allowed-headers "*" \
     --account-name <storage-account>
   ```

**Pros:**
- ✅ Update data without redeploying frontend
- ✅ Small app bundle size
- ✅ Can serve multiple environments

**Cons:**
- ⚠️ Requires Azure Blob Storage (~$0.02/GB/month)
- ⚠️ Slower initial load (network fetch)
- ⚠️ Requires internet connection

---

### Method 4: Scheduled Automation (Full Production)

**Best for:** Enterprise production with daily updates

**Architecture:**
```
┌─────────────────────┐
│  Azure Logic App    │  Daily trigger (2 AM)
│  OR                 │
│  Azure Function     │
└──────┬──────────────┘
       │
       ▼
┌───────────────────────────┐
│  Python Container         │  Run lineage parser
│  (Azure Container Instance)│
└──────┬────────────────────┘
       │
       ▼
┌───────────────────────────┐
│  Azure Blob Storage       │  Upload frontend_lineage.json
└──────┬────────────────────┘
       │
       ▼
┌───────────────────────────┐
│  Azure CDN (optional)     │  Cache & serve globally
└──────┬────────────────────┘
       │
       ▼
┌───────────────────────────┐
│  React Web App            │  Fetch on load
└───────────────────────────┘
```

**Implementation:**

1. **Create Azure Function (Python):**
   ```python
   # function_app.py
   import azure.functions as func
   import subprocess
   from azure.storage.blob import BlobServiceClient

   app = func.FunctionApp()

   @app.schedule(schedule="0 0 2 * * *", arg_name="timer")
   def lineage_daily_update(timer: func.TimerRequest) -> None:
       # Run lineage parser
       subprocess.run([
           "python", "lineage_v3/main.py", "run",
           "--parquet", "parquet_snapshots/"
       ])

       # Upload to Blob Storage
       blob_service = BlobServiceClient.from_connection_string(
           os.environ["AzureWebJobsStorage"]
       )
       blob_client = blob_service.get_blob_client(
           container="lineage-data",
           blob="frontend_lineage.json"
       )
       with open("lineage_output/frontend_lineage.json", "rb") as data:
           blob_client.upload_blob(data, overwrite=True)
   ```

2. **Deploy Azure Function**

3. **Frontend fetches from Blob URL** (see Method 3)

**Pros:**
- ✅ Fully automated
- ✅ Always up-to-date
- ✅ Scalable

**Cons:**
- ⚠️ Higher infrastructure cost
- ⚠️ More complex setup

---

## Development Workflow

### Recommended Development Process

**1. Backend Development (Python):**
```bash
# Terminal 1
cd /workspaces/ws-psidwh

# Make changes to lineage_v3/
# Test changes
python lineage_v3/main.py run --parquet parquet_snapshots/

# Verify output
cat lineage_output/frontend_lineage.json | jq '.[] | select(.name == "DimCustomers")'
```

**2. Frontend Development (React):**
```bash
# Terminal 2
cd /workspaces/ws-psidwh/frontend

# Start dev server
npm run dev

# Load latest data via Import modal
# Test visualization
# Make UI changes (auto-reload)
```

**3. Integration Testing:**
```bash
# Generate fresh data
python lineage_v3/main.py run --parquet parquet_snapshots/

# Reload in browser (Import Data → Upload File)

# Verify:
# - All nodes appear
# - Edges are correct
# - Filters work
# - Trace mode works
# - Export works
```

---

## Production Workflow

### Option A: Static Deployment

**Ideal for:** Infrequent updates (weekly/monthly)

```bash
# 1. Generate lineage
python lineage_v3/main.py run --parquet parquet_snapshots/

# 2. Copy to frontend
cp lineage_output/frontend_lineage.json frontend/src/production-data.json

# 3. Update frontend code to import (see Method 2)

# 4. Build frontend
cd frontend
npm run build

# 5. Deploy to Azure
cd dist
zip -r ../deploy.zip .
cd ..
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src deploy.zip
```

### Option B: Dynamic Deployment

**Ideal for:** Frequent updates (daily)

```bash
# 1. Generate lineage
python lineage_v3/main.py run --parquet parquet_snapshots/

# 2. Upload to Blob Storage
az storage blob upload \
  --account-name <storage> \
  --container-name lineage-data \
  --name frontend_lineage.json \
  --file lineage_output/frontend_lineage.json \
  --overwrite

# 3. Frontend auto-fetches on next user load
# (No redeployment needed!)
```

---

## Testing Integration

### Validate JSON Contract

**Script:** `frontend/validate-json.sh`

```bash
#!/bin/bash
# Validate frontend_lineage.json matches contract

FILE="../lineage_output/frontend_lineage.json"

echo "Validating $FILE..."

# Check if file exists
if [ ! -f "$FILE" ]; then
  echo "❌ File not found!"
  exit 1
fi

# Check if valid JSON
if ! jq empty "$FILE" 2>/dev/null; then
  echo "❌ Invalid JSON syntax!"
  exit 1
fi

# Check if array
if [ "$(jq 'type' "$FILE")" != '"array"' ]; then
  echo "❌ Root must be an array!"
  exit 1
fi

# Check required fields
MISSING=$(jq -r '
  .[] |
  select(
    .id == null or
    .name == null or
    .schema == null or
    .object_type == null or
    .inputs == null or
    .outputs == null
  ) |
  .id // "unknown"
' "$FILE")

if [ -n "$MISSING" ]; then
  echo "❌ Missing required fields in nodes: $MISSING"
  exit 1
fi

echo "✅ Validation passed!"
echo "   Nodes: $(jq 'length' "$FILE")"
echo "   Schemas: $(jq '[.[].schema] | unique | length' "$FILE")"
```

**Run:**
```bash
cd frontend
chmod +x validate-json.sh
./validate-json.sh
```

### Integration Test Checklist

- [ ] Backend generates `frontend_lineage.json` without errors
- [ ] JSON file is valid (use `jq` or validator)
- [ ] All nodes have required fields (`id`, `name`, `schema`, `object_type`, `inputs`, `outputs`)
- [ ] No duplicate node IDs
- [ ] All `inputs` and `outputs` reference valid node IDs
- [ ] Schema names are UPPERCASE
- [ ] `object_type` is one of: "Table", "View", "Stored Procedure"
- [ ] Frontend import succeeds without validation errors
- [ ] Graph renders correctly
- [ ] All schemas appear in filter dropdown
- [ ] Interactive trace works
- [ ] Export to SVG works

---

## Troubleshooting

### Issue: Import Fails with Validation Errors

**Symptoms:**
```
Validation Results
Errors (must be fixed to import):
- Node (ID: node_5) has an invalid or non-existent input ID "node_999".
```

**Cause:** Backend generated invalid references

**Solution:**
```bash
# Re-run backend with fresh data
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# Validate output
jq '.[] | select(.inputs[] == "node_999")' lineage_output/frontend_lineage.json
```

### Issue: Some Nodes Don't Appear

**Symptoms:** Node count mismatch between JSON and frontend

**Debugging:**
```bash
# Count nodes in JSON
jq 'length' lineage_output/frontend_lineage.json

# Check browser console for errors
# Look for "Node X referenced but not found"
```

**Solution:** Ensure all referenced IDs exist

### Issue: Edges Not Showing

**Symptoms:** Nodes render, but no arrows

**Cause:** Bidirectional edge inconsistency

**Fix:** Frontend auto-fixes this, but check backend output:
```bash
# Check if outputs match inputs bidirectionally
jq '
  .[] |
  select(.outputs | length > 0) |
  {name, outputs}
' lineage_output/frontend_lineage.json
```

### Issue: Schemas Not Uppercase

**Symptoms:** Multiple schema variants ("Sales" vs "SALES")

**Solution:** Backend ensures uppercase; if not, update backend:
```python
# In output formatter
node['schema'] = node['schema'].upper()
```

### Issue: Large JSON File (>10MB)

**Symptoms:** Slow load time, browser freezes

**Solutions:**
1. **Filter data:** Export only relevant schemas/objects
2. **Pagination:** Split into multiple JSON files
3. **Compression:** Serve as `.json.gz` (Azure Blob supports)
4. **Virtualization:** Update frontend to lazy-load nodes

---

## Data Update Frequency

### Recommended Update Schedules

| Environment | Frequency | Method |
|-------------|-----------|--------|
| **Development** | On-demand | Manual run + Import |
| **Staging** | Daily (2 AM) | Scheduled Azure Function |
| **Production** | Weekly (Sunday 2 AM) | Scheduled Azure Function |
| **Hotfix** | Immediate | Manual upload to Blob |

---

## Security Considerations

### JSON Data Exposure

**If using Blob Storage:**
- ✅ Use private containers + SAS tokens (recommended)
- ⚠️ Or public container with CORS (less secure)

**SAS Token Example:**
```bash
# Generate SAS token (expires in 30 days)
az storage blob generate-sas \
  --account-name <storage> \
  --container-name lineage-data \
  --name frontend_lineage.json \
  --permissions r \
  --expiry 2025-11-26 \
  --https-only

# Use in frontend:
fetch('https://storage.blob.core.windows.net/lineage-data/frontend_lineage.json?<SAS_TOKEN>')
```

### Sensitive Data

**Redact sensitive information in backend:**
```python
# In output formatter
if 'password' in node['name'].lower() or 'secret' in node['name'].lower():
    node['description'] = '[REDACTED]'
```

---

## Performance Optimization

### Large Datasets (1000+ Nodes)

**Backend:**
- Use `--skip-query-logs` if not needed
- Filter by schema (export only relevant schemas)

**Frontend:**
- Lazy load nodes (virtual scrolling)
- Cluster nodes by schema in initial view
- Debounce filter updates

**Example filter in backend:**
```python
# Export only CONSUMPTION_* schemas
filtered_nodes = [
    node for node in all_nodes
    if node['schema'].startswith('CONSUMPTION_')
]
```

---

## Future Enhancements

1. **Real-Time Updates:**
   - WebSocket connection for live lineage updates
   - SignalR for Azure integration

2. **Versioning:**
   - Store multiple versions of lineage data
   - Compare changes over time (diff view)

3. **Incremental Loading:**
   - Load schema-by-schema on demand
   - Reduce initial bundle size

4. **Metadata Sync:**
   - Pull descriptions from Azure Purview
   - Sync data model types from documentation

---

## Quick Reference

### File Locations

| File | Purpose |
|------|---------|
| `lineage_output/frontend_lineage.json` | Frontend data source |
| `lineage_output/lineage.json` | Backend internal format |
| `lineage_output/lineage_summary.json` | Coverage statistics |
| `frontend/utils/data.ts` | Sample data generator |

### Commands

| Command | Purpose |
|---------|---------|
| `python lineage_v3/main.py run` | Generate lineage JSON |
| `npm run dev` | Start frontend dev server |
| `jq . file.json` | Validate JSON syntax |
| `az storage blob upload` | Upload to Azure Blob |

---

**End of Integration Guide**
