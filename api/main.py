"""
FastAPI Backend for Vibecoding Lineage Parser v3

Web API wrapper for existing lineage_v3 Python code.
"""

import os
import json
import time
import uuid
import shutil
import threading
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    UploadResponse,
    JobStatusResponse,
    LineageResultResponse,
    HealthResponse,
    ErrorResponse,
    JobStatus
)
from background_tasks import process_lineage_job

# ============================================================================
# Application Configuration
# ============================================================================

# Job storage configuration
JOBS_DIR = Path("/tmp/jobs")

# Persistent data storage (survives container restarts if volume mounted)
# Use /app/data in Docker, or ../data (parent dir) in dev
DATA_DIR = Path("/app/data") if Path("/app").exists() else Path(__file__).parent.parent / "data"
LATEST_DATA_FILE = DATA_DIR / "latest_frontend_lineage.json"

# API startup time (for uptime calculation)
START_TIME = time.time()

# In-memory job tracking (lost on restart - acceptable per spec)
active_jobs = {}  # job_id -> {"status": str, "thread": Thread}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup
    JOBS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed
    print("🚀 Vibecoding Lineage Parser API v3.0.0")
    print(f"📁 Jobs directory: {JOBS_DIR}")
    print(f"💾 Data directory: {DATA_DIR}")
    if LATEST_DATA_FILE.exists():
        print(f"✅ Latest data file found: {LATEST_DATA_FILE.name}")
    else:
        print(f"ℹ️  No existing data file (will be created on first upload)")
    print(f"✅ API ready")
    yield
    # Shutdown
    print("🛑 API shutting down")


app = FastAPI(
    title="Vibecoding Lineage Parser API",
    description="Web API for data lineage extraction from Synapse DMV Parquet files",
    version="3.0.0",
    lifespan=lifespan
)

# CORS configuration (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Helper Functions
# ============================================================================

def get_job_dir(job_id: str) -> Path:
    """Get directory path for a specific job"""
    return JOBS_DIR / job_id


def get_job_status_data(job_id: str) -> dict:
    """Read status.json for a job"""
    job_dir = get_job_dir(job_id)
    status_file = job_dir / "status.json"

    if not status_file.exists():
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    with open(status_file, 'r') as f:
        return json.load(f)


def get_job_result_data(job_id: str) -> dict:
    """Read result.json for a job"""
    job_dir = get_job_dir(job_id)
    result_file = job_dir / "result.json"

    if not result_file.exists():
        raise HTTPException(status_code=404, detail=f"Results for job {job_id} not found")

    with open(result_file, 'r') as f:
        return json.load(f)


def run_processing_thread(job_id: str, job_dir: Path, incremental: bool = True):
    """Thread function to run lineage processing in background"""
    try:
        result = process_lineage_job(job_id, job_dir, data_dir=DATA_DIR, incremental=incremental)
        active_jobs[job_id]["status"] = result["status"]
    except Exception as e:
        print(f"Error processing job {job_id}: {e}")
        active_jobs[job_id]["status"] = "failed"


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for container orchestration.

    Returns:
        Health status, version, and uptime
    """
    return HealthResponse(
        status="ok",
        version="3.0.0",
        uptime_seconds=time.time() - START_TIME
    )


@app.get("/api/latest-data", tags=["Data"])
async def get_latest_data():
    """
    Get the latest processed lineage data (frontend JSON format).

    This endpoint serves the most recently processed lineage data that persists
    across container restarts (when DATA_DIR is volume-mounted).

    Returns:
        JSON array of lineage nodes, or empty array if no data exists
    """
    if not LATEST_DATA_FILE.exists():
        return JSONResponse(
            content=[],
            status_code=200,
            headers={"X-Data-Available": "false"}
        )

    try:
        with open(LATEST_DATA_FILE, 'r') as f:
            data = json.load(f)

        # Get file modification time
        mtime = LATEST_DATA_FILE.stat().st_mtime
        upload_timestamp = datetime.fromtimestamp(mtime).isoformat()

        return JSONResponse(
            content=data,
            status_code=200,
            headers={
                "X-Data-Available": "true",
                "X-Node-Count": str(len(data)) if isinstance(data, list) else "unknown",
                "X-Upload-Timestamp": upload_timestamp
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load latest data: {str(e)}"
        )


@app.get("/api/metadata", tags=["Data"])
async def get_metadata():
    """
    Get metadata about the current lineage data.

    Returns information about:
    - Whether data is available
    - Last upload timestamp
    - Number of nodes
    - File size

    Returns:
        Metadata object or null if no data available
    """
    if not LATEST_DATA_FILE.exists():
        return JSONResponse(
            content={"available": False},
            status_code=200
        )

    try:
        # Get file stats
        file_stats = LATEST_DATA_FILE.stat()
        mtime = file_stats.st_mtime
        upload_timestamp = datetime.fromtimestamp(mtime).isoformat()
        file_size_kb = file_stats.st_size / 1024

        # Count nodes
        with open(LATEST_DATA_FILE, 'r') as f:
            data = json.load(f)
            node_count = len(data) if isinstance(data, list) else 0

        return JSONResponse(
            content={
                "available": True,
                "upload_timestamp": upload_timestamp,
                "upload_timestamp_human": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "node_count": node_count,
                "file_size_kb": round(file_size_kb, 2)
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metadata: {str(e)}"
        )


@app.get("/api/ddl/{object_id}", tags=["Data"])
async def get_ddl(object_id: int):
    """
    Get DDL definition for a specific object on demand.

    This endpoint fetches DDL from the latest processed lineage workspace.
    Supports Stored Procedures, Views, and Tables (if table_columns was provided).

    Args:
        object_id: The database object_id (integer)

    Returns:
        JSON with ddl_text field, or 404 if not found
    """
    # Use persistent workspace in data directory
    workspace_file = DATA_DIR / "lineage_workspace.duckdb"

    if not workspace_file.exists():
        raise HTTPException(status_code=404, detail="No lineage data available. Please upload data first.")

    try:
        # Import here to avoid startup dependency
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from lineage_v3.core import DuckDBWorkspace

        with DuckDBWorkspace(workspace_path=str(workspace_file)) as db:
            # Query unified_ddl view (combines real DDL + generated table DDL)
            result = db.connection.execute("""
                SELECT
                    object_id,
                    object_name,
                    schema_name,
                    object_type,
                    ddl_text
                FROM unified_ddl
                WHERE object_id = ?
            """, [object_id]).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail=f"Object {object_id} not found in unified_ddl view")

            obj_id, object_name, schema_name, object_type, ddl_text = result

            return JSONResponse(content={
                "object_id": obj_id,
                "object_name": object_name,
                "schema_name": schema_name,
                "object_type": object_type,
                "ddl_text": ddl_text
            })

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch DDL: {str(e)}"
        )


@app.get("/api/search-ddl", tags=["Data"])
async def search_ddl(q: str = Query(..., min_length=1, max_length=200, description="Search query")):
    """
    Full-text search across all DDL definitions using DuckDB FTS.

    Search features:
    - Case-insensitive search by default
    - Searches object_name and definition_text
    - BM25 relevance ranking (most relevant first)
    - Automatic stemming (e.g., "customer" matches "customers")
    - Phrase search support (e.g., "SELECT * FROM")
    - Boolean operators (AND, OR, NOT)
    - Wildcard support (e.g., "cust*")

    Args:
        q: Search query string (1-200 chars, required)

    Returns:
        List of matching objects sorted by relevance score:
        [
            {
                "id": "1234567890",
                "name": "spLoadCustomers",
                "type": "Stored Procedure",
                "schema": "CONSUMPTION_FINANCE",
                "score": 2.456,
                "snippet": "SELECT * FROM DimCustomers WHERE..."
            }
        ]

    Raises:
        404: No lineage data available
        500: Search failed
    """
    # Use persistent workspace in data directory
    workspace_file = DATA_DIR / "lineage_workspace.duckdb"

    if not workspace_file.exists():
        raise HTTPException(
            status_code=404,
            detail="No lineage data available. Please upload data first."
        )

    try:
        # Import here to avoid startup dependency
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from lineage_v3.core import DuckDBWorkspace

        with DuckDBWorkspace(workspace_path=str(workspace_file)) as db:
            # Query FTS index for matching objects
            # Returns ranked results with BM25 relevance scores
            results = db.connection.execute("""
                SELECT
                    d.object_id::TEXT as id,
                    d.object_name as name,
                    o.object_type as type,
                    d.schema_name as schema,
                    fts_main_definitions.match_bm25(d.object_id, ?) as score,
                    substr(d.definition, 1, 150) as snippet
                FROM definitions d
                JOIN objects o ON d.object_id = o.object_id
                WHERE fts_main_definitions.match_bm25(d.object_id, ?) IS NOT NULL
                ORDER BY score DESC
                LIMIT 100
            """, [q, q]).fetchdf()

            # Convert to list of dicts for JSON response
            search_results = results.to_dict('records')

            return JSONResponse(content=search_results)

    except Exception as e:
        # Log the error for debugging
        print(f"❌ Search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/api/upload-parquet", response_model=UploadResponse, tags=["Lineage"])
async def upload_parquet(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Parquet files (any names - will be auto-detected)"),
    incremental: bool = True
):
    """
    Upload Parquet files and start lineage processing.

    The backend automatically detects file types by analyzing their schema.
    You can upload files with any names - they will be validated and identified.

    Required files (3):
    - objects.parquet (object metadata)
    - dependencies.parquet (DMV dependencies)
    - definitions.parquet (DDL for views/procedures)

    Optional files (2):
    - query_logs.parquet (runtime execution logs)
    - table_columns.parquet (table column metadata for DDL generation)

    Args:
        files: List of Parquet files (3-5 files expected)
        incremental: If True, only re-parse modified objects (default: True)

    Returns:
        Job ID for status polling
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    # Track received files
    files_received = []

    try:
        # Validate we got files
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="No files uploaded")

        # Save all uploaded files (keep original names)
        for upload_file in files:
            if not upload_file.filename:
                continue

            # Ensure .parquet extension
            filename = upload_file.filename
            if not filename.endswith('.parquet'):
                raise HTTPException(status_code=400, detail=f"File '{filename}' is not a Parquet file")

            file_path = job_dir / filename
            with open(file_path, 'wb') as f:
                content = await upload_file.read()
                f.write(content)
            files_received.append(filename)

        # Initialize status file
        status_data = {
            "status": "pending",
            "progress": 0.0,
            "current_step": "Queued",
            "message": "Job created, waiting to start...",
            "elapsed_seconds": 0.0
        }
        with open(job_dir / "status.json", 'w') as f:
            json.dump(status_data, f, indent=2)

        # Start background processing in a thread with incremental flag
        thread = threading.Thread(
            target=run_processing_thread,
            args=(job_id, job_dir, incremental),
            daemon=True
        )
        thread.start()

        # Track job
        active_jobs[job_id] = {
            "status": "processing",
            "thread": thread,
            "created_at": time.time(),
            "incremental": incremental
        }

        mode_text = "incremental" if incremental else "full refresh"
        return UploadResponse(
            job_id=job_id,
            message=f"Files uploaded successfully. Processing started in {mode_text} mode.",
            files_received=files_received
        )

    except Exception as e:
        # Clean up on error
        if job_dir.exists():
            shutil.rmtree(job_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/status/{job_id}", response_model=JobStatusResponse, tags=["Lineage"])
async def get_job_status(job_id: str):
    """
    Poll job status (called every 2 seconds by frontend).

    Args:
        job_id: Job identifier from upload response

    Returns:
        Current job status and progress information
    """
    try:
        status_data = get_job_status_data(job_id)

        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus(status_data["status"]),
            progress=status_data.get("progress"),
            current_step=status_data.get("current_step"),
            elapsed_seconds=status_data.get("elapsed_seconds"),
            estimated_remaining_seconds=status_data.get("estimated_remaining_seconds"),
            message=status_data.get("message"),
            errors=status_data.get("errors"),
            warnings=status_data.get("warnings")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving status: {str(e)}")


@app.get("/api/result/{job_id}", response_model=LineageResultResponse, tags=["Lineage"])
async def get_job_result(job_id: str):
    """
    Get final lineage JSON when job is complete.

    Args:
        job_id: Job identifier

    Returns:
        Lineage graph data (frontend format) and summary statistics
    """
    try:
        # Check status first
        status_data = get_job_status_data(job_id)

        # Get result data (works for both completed and failed)
        result_data = get_job_result_data(job_id)

        # Clean up job files after retrieval (completed OR failed)
        job_dir = get_job_dir(job_id)
        if job_dir.exists():
            try:
                shutil.rmtree(job_dir)
                if job_id in active_jobs:
                    del active_jobs[job_id]
                print(f"✓ Cleaned up job {job_id}")
            except Exception as cleanup_error:
                # Log but don't fail the request
                print(f"Warning: Failed to cleanup job {job_id}: {cleanup_error}")

        return LineageResultResponse(
            job_id=job_id,
            status=JobStatus(result_data["status"]),
            data=result_data.get("data"),
            summary=result_data.get("summary"),
            errors=result_data.get("errors")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving result: {str(e)}")


@app.delete("/api/jobs/{job_id}", tags=["Admin"])
async def delete_job(job_id: str):
    """
    Delete job files (cleanup).

    Args:
        job_id: Job identifier

    Returns:
        Success message
    """
    job_dir = get_job_dir(job_id)

    if not job_dir.exists():
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    try:
        shutil.rmtree(job_dir)

        # Remove from active jobs tracking
        if job_id in active_jobs:
            del active_jobs[job_id]

        return {"message": f"Job {job_id} deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")


@app.get("/api/jobs", tags=["Admin"])
async def list_jobs():
    """
    List all jobs (for debugging/admin).

    Returns:
        List of all job IDs and their status
    """
    jobs = []

    for job_id in os.listdir(JOBS_DIR):
        job_dir = get_job_dir(job_id)
        if job_dir.is_dir():
            try:
                status_data = get_job_status_data(job_id)
                jobs.append({
                    "job_id": job_id,
                    "status": status_data["status"],
                    "progress": status_data.get("progress", 0),
                    "current_step": status_data.get("current_step", "Unknown")
                })
            except:
                jobs.append({
                    "job_id": job_id,
                    "status": "unknown",
                    "progress": 0,
                    "current_step": "Error reading status"
                })

    return {"jobs": jobs, "total": len(jobs)}


@app.delete("/api/clear-data", tags=["Admin"])
async def clear_all_data():
    """
    Clear all lineage data (DuckDB workspace and JSON files).

    This endpoint:
    1. Deletes the persistent DuckDB workspace
    2. Removes the latest_frontend_lineage.json file
    3. Deletes all temporary job directories
    4. Clears in-memory job tracking

    Use this to start fresh before uploading new Parquet files.

    Returns:
        Success message with items cleared
    """
    items_cleared = []

    try:
        # 1. Clear persistent DuckDB workspace
        workspace_file = DATA_DIR / "lineage_workspace.duckdb"
        if workspace_file.exists():
            workspace_file.unlink()
            items_cleared.append("DuckDB workspace")

        # Also clean up WAL file if it exists
        wal_file = DATA_DIR / "lineage_workspace.duckdb.wal"
        if wal_file.exists():
            wal_file.unlink()

        # 2. Clear all job directories
        if JOBS_DIR.exists():
            for job_dir in JOBS_DIR.iterdir():
                if job_dir.is_dir():
                    shutil.rmtree(job_dir)
                    items_cleared.append(f"Job directory: {job_dir.name}")

        # 3. Clear latest data file
        if LATEST_DATA_FILE.exists():
            LATEST_DATA_FILE.unlink()
            items_cleared.append("Latest frontend lineage JSON")

        # 4. Clear in-memory job tracking
        cleared_jobs = len(active_jobs)
        active_jobs.clear()
        if cleared_jobs > 0:
            items_cleared.append(f"{cleared_jobs} active job(s) from memory")

        if not items_cleared:
            return {
                "message": "No data to clear (already empty)",
                "items_cleared": []
            }

        return {
            "message": f"Successfully cleared {len(items_cleared)} item(s)",
            "items_cleared": items_cleared
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear data: {str(e)}"
        )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
