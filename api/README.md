# FastAPI Backend

**Version:** 3.0.1
**Status:** ✅ Production Ready

---

## Quick Start

```bash
# Install dependencies
cd api && pip install -r requirements.txt

# Start server
python3 main.py

# Server: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Architecture

FastAPI backend that wraps the `lineage_v3` Python parser for web-based lineage analysis.

**Key Principle:** Existing Python code runs **unchanged** - this is just a web API wrapper.

```
Frontend (Browser)
  ↓
  POST /api/upload-parquet (3-5 Parquet files)
  ↓
FastAPI Main Thread
  ├── Save files to /tmp/jobs/{job_id}/
  ├── Create status.json
  └── Start background thread
       ↓
Background Thread (LineageProcessor)
  ├── Load Parquet → DuckDB
  ├── Parse with lineage_v3 modules
  ├── Update status.json every few seconds
  └── Save result.json when complete
       ↓
Frontend Polling (every 2 seconds)
  ├── GET /api/status/{job_id}
  └── GET /api/result/{job_id} (when complete)
```

---

## Core Features

### Incremental Parsing (Default)
- **Performance:** 50-90% faster for typical updates
- **Trigger:** Only re-parses objects that are new, modified, or low confidence (<0.85)
- **Persistence:** DuckDB workspace persists between runs

**Usage:**
```bash
# Incremental (default, recommended)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" -F "files=@..."

# Full refresh (parser changes, complete re-analysis)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" -F "files=@..."
```

### Background Processing
- Progress updates every 5-10% (written to `status.json`)
- Linear time estimation based on elapsed time
- Graceful error handling (errors saved to `result.json`)
- All processing runs in background thread (non-blocking)

**Implementation:**
```python
from lineage_v3.core import DuckDBWorkspace
from lineage_v3.parsers import QualityAwareParser, AIDisambiguator
from lineage_v3.output import InternalFormatter, FrontendFormatter

# Run existing pipeline unchanged
with DuckDBWorkspace(workspace_path=workspace_file) as db:
    # Step 1: Load Parquet files
    db.load_parquet(job_dir, full_refresh=not incremental)

    # Step 2: Parse stored procedures
    parser = QualityAwareParser(db)
    ai_disambiguator = AIDisambiguator(db)

    for sp in sps_to_parse:
        result = parser.parse_object(sp[0])
        if result.should_run_ai(0.85):
            result = ai_disambiguator.disambiguate(result)
        db.update_metadata(result)

    # Step 3: Generate output files
    FrontendFormatter(db).generate()
    InternalFormatter(db).generate()
```

---

## API Endpoints

See [ENDPOINTS.md](ENDPOINTS.md) for detailed documentation, or use the interactive Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

**Key Endpoints:**
- `POST /api/upload-parquet` - Upload files, start processing
- `GET /api/status/{job_id}` - Poll job status (every 2s)
- `GET /api/result/{job_id}` - Get final lineage JSON
- `GET /api/search-ddl` - Full-text search across all DDL (tables, SPs, views)
- `GET /api/ddl/{object_id}` - Get complete DDL for specific object
- `GET /health` - Health check for orchestration
- `GET /api/jobs` - List all jobs (admin)
- `DELETE /api/jobs/{job_id}` - Cleanup job files

---

## Job Storage

Files stored in `/tmp/jobs/{job_id}/`:

**Uploaded Files:**
- `objects.parquet` (required)
- `dependencies.parquet` (required)
- `definitions.parquet` (required)
- `query_logs.parquet` (optional)
- `table_columns.parquet` (optional)

**Generated Files:**
- `status.json` - Real-time status for polling
- `result.json` - Final lineage data (frontend format)
- `lineage.json` - Internal format (integer IDs)
- `lineage_summary.json` - Statistics
- `lineage_workspace.duckdb` - DuckDB workspace

**Storage Notes:**
- Ephemeral storage (`/tmp/`) - lost on container restart (acceptable per spec)
- Job cleanup via `DELETE /api/jobs/{job_id}` or manual removal
- No persistent database required

---

## CORS Configuration

### Development (Current)
```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # All origins allowed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Production Security: CORS + Azure Authentication

When deploying to Azure, you'll use **two complementary security layers**:

**1. CORS (Cross-Origin Resource Sharing)**
- **What it does:** Browser-level security that controls *which websites* can make requests to your API
- **Purpose:** Prevents unauthorized websites from calling your API from users' browsers
- **Configuration:** Restrict to your frontend domain only

**2. Azure Built-in Authentication (Easy Auth)**
- **What it does:** Identity-level security that authenticates *who the user is*
- **Purpose:** Ensures only authenticated users can access the application
- **Configuration:** Configured in Azure App Service settings (not in code)

**Why you need both:**
- CORS protects against malicious websites trying to call your API
- Azure Auth protects against unauthorized users accessing your application
- They work together: CORS validates the website origin, Azure Auth validates the user identity

### Production Deployment Checklist

**1. Update CORS origins in .env:**
```bash
ALLOWED_ORIGINS=https://your-frontend-domain.azurewebsites.net
```

**2. Ensure api/main.py reads from environment variable:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(','),
    allow_credentials=True,  # REQUIRED for Azure Auth to work!
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**IMPORTANT:** `allow_credentials=True` is **required** for Azure Authentication to work. This allows the browser to send authentication cookies from Azure to your API.

**3. Configure Azure Built-in Authentication:**
- In Azure Portal → App Service → Authentication
- Enable authentication provider (Microsoft Entra ID, Google, etc.)
- Set "Action to take when request is not authenticated" to "Log in with [Provider]"
- Azure will handle authentication before requests reach your FastAPI application

---

## Files

- [main.py](main.py) - FastAPI application with all endpoints
- [background_tasks.py](background_tasks.py) - Background processing wrapper
- [models.py](models.py) - Pydantic models for request/response
- [requirements.txt](requirements.txt) - API-specific dependencies
- [ENDPOINTS.md](ENDPOINTS.md) - Detailed endpoint documentation

---

## Testing


**Quick Test:**
```bash
# Health check
curl http://localhost:8000/health

# Interactive API docs
open http://localhost:8000/docs
```

---

## Reference

- [http://localhost:8000/docs](http://localhost:8000/docs) - Interactive Swagger UI
- [http://localhost:8000/redoc](http://localhost:8000/redoc) - ReDoc documentation
