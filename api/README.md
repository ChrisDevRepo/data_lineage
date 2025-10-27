# FastAPI Backend

**Status:** ✅ **Week 2 Days 1-5 COMPLETE** - Backend API Fully Implemented

## Overview

FastAPI backend that wraps existing `lineage_v3` Python code for web-based lineage parsing.

**Key Principle:** Existing Python code runs **unchanged** - this is just a web API wrapper.

## Files

- [main.py](main.py) - FastAPI application with all endpoints ✅ COMPLETE
- [background_tasks.py](background_tasks.py) - Background processing wrapper ✅ COMPLETE
- [models.py](models.py) - Pydantic models for request/response ✅ COMPLETE
- [requirements.txt](requirements.txt) - API-specific dependencies ✅ COMPLETE

## Installation

```bash
# Install dependencies (in addition to root requirements.txt)
cd /workspaces/ws-psidwh/api
pip install --break-system-packages -r requirements.txt
```

## Running the API

```bash
# Start development server (auto-reload enabled)
cd /workspaces/ws-psidwh/api
python3 main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: **http://0.0.0.0:8000**

API Documentation (OpenAPI/Swagger):
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## API Endpoints

### 1. POST /api/upload-parquet
Upload 4 Parquet files and start lineage processing.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/upload-parquet" \
  -F "objects=@objects.parquet" \
  -F "dependencies=@dependencies.parquet" \
  -F "definitions=@definitions.parquet" \
  -F "query_logs=@query_logs.parquet"
```

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Files uploaded successfully. Processing started.",
  "files_received": [
    "objects.parquet",
    "dependencies.parquet",
    "definitions.parquet",
    "query_logs.parquet"
  ]
}
```

### 2. GET /api/status/{job_id}
Poll for job status (called every 2 seconds by frontend).

**Request:**
```bash
curl "http://localhost:8000/api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response (Processing):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "progress": 45.5,
  "current_step": "Parsing stored procedures (8/16)",
  "elapsed_seconds": 23.5,
  "estimated_remaining_seconds": 28.2,
  "message": "Analyzing CONSUMPTION_FINANCE.spLoadFactSales..."
}
```

**Response (Complete):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "progress": 100,
  "current_step": "Complete",
  "elapsed_seconds": 51.7,
  "estimated_remaining_seconds": 0,
  "message": "Lineage analysis finished successfully"
}
```

### 3. GET /api/result/{job_id}
Get final lineage JSON when job is complete.

**Request:**
```bash
curl "http://localhost:8000/api/result/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "data": [
    {
      "id": "1986106116",
      "name": "DimCustomers",
      "schema": "CONSUMPTION_FINANCE",
      "object_type": "Table",
      "inputs": [],
      "outputs": ["350624292"],
      "description": "Confidence: 1.00",
      "data_model_type": "Dimension"
    }
  ],
  "summary": {
    "total_objects": 150,
    "parsed_objects": 145,
    "coverage": 96.7,
    "confidence_distribution": {
      "high": 120,
      "medium": 15,
      "low": 10
    }
  },
  "errors": null
}
```

### 4. GET /health
Health check for container orchestration.

**Request:**
```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "ok",
  "version": "3.0.0",
  "uptime_seconds": 3600.5
}
```

### 5. GET /api/jobs
List all jobs (admin/debugging).

**Request:**
```bash
curl "http://localhost:8000/api/jobs"
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "completed",
      "progress": 100,
      "current_step": "Complete"
    },
    {
      "job_id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
      "status": "processing",
      "progress": 62.3,
      "current_step": "Building graph relationships"
    }
  ],
  "total": 2
}
```

### 6. DELETE /api/jobs/{job_id}
Delete job files (cleanup).

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/jobs/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response:**
```json
{
  "message": "Job a1b2c3d4-e5f6-7890-abcd-ef1234567890 deleted successfully"
}
```

## Background Processing

The `LineageProcessor` class in [background_tasks.py](background_tasks.py) wraps the existing pipeline:

```python
from lineage_v3.core import DuckDBWorkspace, GapDetector
from lineage_v3.parsers import DualParser
from lineage_v3.output import InternalFormatter, FrontendFormatter, SummaryFormatter

# Run existing pipeline unchanged
with DuckDBWorkspace(workspace_path=workspace_file) as db:
    # Step 1: Load Parquet files
    db.load_parquet(job_dir, full_refresh=True)

    # Step 2: Load DMV dependencies (Views)
    # ... (existing logic)

    # Step 3: Detect gaps
    gap_detector = GapDetector(db)
    gaps = gap_detector.detect_gaps()

    # Step 4: Parse with dual-parser
    dual_parser = DualParser(db)
    for sp in all_sps:
        result = dual_parser.parse_object(sp[0])
        db.update_metadata(...)

    # Step 5: Build bidirectional graph
    # ... (reverse lookup logic)

    # Step 6: Generate output files
    internal_formatter = InternalFormatter(db)
    frontend_formatter = FrontendFormatter(db)
    summary_formatter = SummaryFormatter(db)
```

**Key Features:**
- Progress updates every 5-10% (written to `status.json`)
- Linear time estimation based on elapsed time
- Graceful error handling (errors saved to `result.json`)
- All processing runs in background thread

## Job Storage

Files stored in `/tmp/jobs/{job_id}/`:

**Uploaded Files:**
- `objects.parquet` (required)
- `dependencies.parquet` (required)
- `definitions.parquet` (required)
- `query_logs.parquet` (optional)

**Generated Files:**
- `status.json` - Real-time status for polling
- `result.json` - Final lineage data (frontend format)
- `lineage.json` - Internal format (int IDs)
- `lineage_summary.json` - Statistics
- `lineage_workspace.duckdb` - DuckDB workspace

**Storage Notes:**
- Ephemeral storage (`/tmp/`) - lost on container restart (acceptable per spec)
- Job cleanup via DELETE endpoint or manual removal
- No persistent database required

## Architecture

```
Frontend (Browser)
  ↓
  POST /api/upload-parquet (4 Parquet files)
  ↓
FastAPI Main Thread
  ├── Save files to /tmp/jobs/{job_id}/
  ├── Create status.json
  └── Start background thread
       ↓
Background Thread (LineageProcessor)
  ├── Load Parquet → DuckDB
  ├── Parse with existing lineage_v3 modules
  ├── Update status.json every few seconds
  └── Save result.json when complete
       ↓
Frontend Polling (every 2 seconds)
  ├── GET /api/status/{job_id}
  └── GET /api/result/{job_id} (when status = "completed")
```

## Implementation Status

✅ **COMPLETE - Week 2 Days 1-5:**
- ✅ Day 1-2: File upload endpoint (`POST /api/upload-parquet`)
- ✅ Day 3-4: Background processing wrapper (`LineageProcessor`)
- ✅ Day 5: Status & result endpoints (`GET /api/status`, `GET /api/result`)

📋 **PENDING - Week 2-3 Days 6-10:**
- Day 6-7: Frontend upload UI (React component)
- Day 8: Frontend progress display (polling modal)
- Day 9: Docker container (multi-stage build)
- Day 10: Integration testing

## Testing

See [API Testing Guide](../docs/API_TESTING.md) for comprehensive testing instructions including:
- Health check testing
- File upload testing with sample Parquet files
- Status polling examples
- Result retrieval
- Error handling scenarios

## CORS Configuration

Currently allows all origins (`allow_origins=["*"]`) for development.

**Production:** Update CORS to restrict origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.azurewebsites.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "JobNotFound",
  "detail": "Job a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad request (missing files, invalid data)
- `404` - Job not found
- `500` - Internal server error

## Reference

See [docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md) - Section 5 for complete specification.
