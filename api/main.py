"""
Data Lineage Visualizer API

FastAPI backend providing REST API for lineage analysis and visualization.

Features:
- Parquet file upload with automatic schema detection
- Background job processing with status polling
- Full-text search across DDL definitions
- On-demand DDL fetching with caching
- Incremental and full-refresh parsing modes
"""

import os
import json
import time
import uuid
import shutil
import threading
import logging
from pathlib import Path
from typing import List, Optional, AsyncIterator, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

try:
    # Try absolute import first (for pytest from project root)
    from api.models import (
        UploadResponse,
        JobStatusResponse,
        LineageResultResponse,
        HealthResponse,
        ErrorResponse,
        JobStatus
    )
    from api.background_tasks import process_lineage_job
except ImportError:
    # Fall back to relative import (for running from api/ directory)
    from models import (
        UploadResponse,
        JobStatusResponse,
        LineageResultResponse,
        HealthResponse,
        ErrorResponse,
        JobStatus
    )
    from background_tasks import process_lineage_job

# Import settings first (needed for logging configuration)
from engine.config.settings import settings
from engine.utils.log_cleanup import cleanup_old_logs

# Configure logging based on settings (v0.9.0)
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Authentication
# ============================================================================

import base64

async def verify_azure_auth(
    x_ms_client_principal: Optional[str] = Header(None, alias="X-MS-CLIENT-PRINCIPAL")
) -> Optional[Dict[str, Any]]:
    """
    Trust Azure Container Apps Easy Auth platform-level authentication.
    Platform blocks unauthenticated requests - never reject in application code.
    """
    if not x_ms_client_principal:
        logger.debug("Request authenticated by platform")
        return None
    
    try:
        principal_json = base64.b64decode(x_ms_client_principal).decode('utf-8')
        principal_data = json.loads(principal_json)
        logger.info(f"User: {principal_data.get('userId', 'unknown')}")
        return principal_data
    except Exception as e:
        logger.warning(f"Header decode failed: {e}")
        return None

# ============================================================================
# Application Configuration
# ============================================================================

# API version (single source of truth)
API_VERSION = "0.9.0"

# Job storage configuration (ephemeral - can be lost on restart)
JOBS_DIR = Path("/tmp/jobs")

# Persistent data storage (survives container restarts if volume mounted)
# Priority: Environment variable > Azure default > Docker > Local dev
DATA_DIR = Path(os.getenv("PATH_OUTPUT_DIR", 
                          "/home/site/data" if Path("/home/site/data").exists() 
                          else "/app/data" if Path("/app").exists() 
                          else str(Path(__file__).parent.parent / "data")))
LATEST_DATA_FILE = DATA_DIR / "latest_frontend_lineage.json"

# API startup time (for uptime calculation)
START_TIME = time.time()

# In-memory job tracking (lost on restart - acceptable per spec)
active_jobs = {}  # job_id -> {"status": str, "thread": Thread}

# Global upload lock for multi-user safety (simple blocking approach)
# Prevents concurrent uploads from corrupting DuckDB workspace
upload_lock = threading.Lock()
current_upload_info = {"job_id": None, "started_at": None}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan event handler"""
    # Startup
    JOBS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed
    logger.info(f"🚀 Data Lineage Visualizer API v{API_VERSION}")
    logger.info(f"🔧 Run mode: {settings.run_mode.upper()}")
    logger.info(f"📁 Jobs directory: {JOBS_DIR}")
    logger.info(f"💾 Data directory: {DATA_DIR}")
    if LATEST_DATA_FILE.exists():
        logger.info(f"✅ Latest data file found: {LATEST_DATA_FILE.name}")
    else:
        logger.info(f"ℹ️  No existing data file (will be created on first upload)")
    logger.info(f"✅ API ready")
    yield
    # Shutdown
    logger.info("🛑 API shutting down")


app = FastAPI(
    title="Data Lineage Visualizer API",
    description="Web API for data lineage extraction from Synapse DMV Parquet files",
    version=API_VERSION,
    lifespan=lifespan
)

# CORS configuration (allow frontend to call API)
# Use environment variable for production deployment to Azure
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Configured via environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Only methods we use
    allow_headers=["Content-Type", "X-Requested-With"],
)

# Mount static files for Azure deployment (serves frontend build)
# In Azure: /home/site/wwwroot/static/ contains the built React app
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")
    logger.info(f"✅ Serving static files from: {STATIC_DIR}")
    
    # Serve logo and favicon files from root
    @app.get("/logo.png")
    async def get_logo():
        logo_path = STATIC_DIR / "logo.png"
        if logo_path.exists():
            return FileResponse(logo_path, media_type="image/png")
        raise HTTPException(status_code=404, detail="Logo not found")
    
    @app.get("/favicon.ico")
    async def get_favicon_ico():
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/x-icon")
        raise HTTPException(status_code=404, detail="Favicon not found")
    
    @app.get("/favicon.png")
    async def get_favicon_png():
        favicon_path = STATIC_DIR / "favicon.png"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/png")
        raise HTTPException(status_code=404, detail="Favicon not found")
    
    @app.get("/favicon-32x32.png")
    async def get_favicon_32():
        favicon_path = STATIC_DIR / "favicon-32x32.png"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/png")
        raise HTTPException(status_code=404, detail="Favicon not found")


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


def run_processing_thread(job_id: str, job_dir: Path, incremental: bool = False) -> None:
    """Thread function to run lineage processing in background"""
    try:
        result = process_lineage_job(job_id, job_dir, data_dir=DATA_DIR, incremental=incremental)
        active_jobs[job_id]["status"] = result["status"]
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
        active_jobs[job_id]["status"] = "failed"
    finally:
        # Always release upload lock when done (success or failure)
        upload_lock.release()
        current_upload_info["job_id"] = None
        current_upload_info["started_at"] = None
        logger.debug(f"✅ Upload lock released for job {job_id}")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint for container orchestration.

    Returns:
        Health status, version, and uptime
    """
    return HealthResponse(
        status="ok",
        version=API_VERSION,
        uptime_seconds=time.time() - START_TIME
    )


@app.get("/api/latest-data", tags=["Data"])
async def get_latest_data(user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> JSONResponse:
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
async def get_metadata(user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> JSONResponse:
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
            content={
                "available": False,
                "run_mode": settings.run_mode
            },
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
                "run_mode": settings.run_mode,
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
async def get_ddl(object_id: int, user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> JSONResponse:
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
        from engine.core import DuckDBWorkspace

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
async def search_ddl(q: str = Query(..., min_length=1, max_length=200, description="Search query"), user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> JSONResponse:
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
        from engine.core import DuckDBWorkspace

        with DuckDBWorkspace(workspace_path=str(workspace_file)) as db:
            # Query FTS index for matching objects
            # Returns ranked results with BM25 relevance scores
            results = db.connection.execute("""
                SELECT
                    d.object_id::TEXT as id,
                    d.object_name as name,
                    o.object_type as type,
                    d.schema_name as schema,
                    fts_main_unified_ddl_materialized.match_bm25(d.object_id, ?) as score,
                    substr(d.definition, 1, 150) as snippet
                FROM definitions d
                JOIN objects o ON d.object_id = o.object_id
                WHERE fts_main_unified_ddl_materialized.match_bm25(d.object_id, ?) IS NOT NULL
                ORDER BY score DESC
                LIMIT 100
            """, [q, q]).fetchdf()

            # Convert to list of dicts for JSON response
            search_results = results.to_dict('records')

            return JSONResponse(content=search_results)

    except Exception as e:
        # Log the error for debugging
        logger.error(f"❌ Search failed for query '{q}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/api/upload-parquet", response_model=UploadResponse, tags=["Lineage"])
async def upload_parquet(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Parquet files (any names - will be auto-detected)"),
    incremental: bool = False,
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> UploadResponse:
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
        incremental: If True, only re-parse modified objects (default: False)

    Returns:
        Job ID for status polling
    """
    # Check if another upload is in progress (multi-user safety)
    if not upload_lock.acquire(blocking=False):
        # Another user is uploading - return friendly error
        return JSONResponse(
            status_code=409,
            content={
                "error": "System busy",
                "message": "Another upload is currently being processed. Please wait a few minutes and try again.",
                "current_job_id": current_upload_info.get("job_id"),
                "started_at": current_upload_info.get("started_at")
            }
        )

    # Generate unique job ID
    job_id = str(uuid.uuid4())
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    # Track current upload
    current_upload_info["job_id"] = job_id
    current_upload_info["started_at"] = datetime.now().isoformat()

    # Clean up old log files (v0.9.0)
    # Triggered on import as requested by user
    try:
        cleanup_stats = cleanup_old_logs(settings.log_retention_days)
        if cleanup_stats['deleted'] > 0:
            logger.info(f"Log cleanup: {cleanup_stats['deleted']} file(s) deleted, {cleanup_stats['total_size_freed_mb']:.2f} MB freed")
    except Exception as e:
        logger.warning(f"Log cleanup failed (non-critical): {e}")

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

            # Sanitize filename to prevent path traversal attacks
            filename = os.path.basename(upload_file.filename)  # Strip any path components

            # Additional validation: reject suspicious characters
            if '..' in filename or '/' in filename or '\\' in filename:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filename '{upload_file.filename}' - path characters not allowed"
                )

            # Ensure .parquet extension
            if not filename.endswith('.parquet'):
                raise HTTPException(status_code=400, detail=f"File '{filename}' is not a Parquet file")

            # Validate resolved path stays within job directory
            file_path = (job_dir / filename).resolve()
            if not str(file_path).startswith(str(job_dir.resolve())):
                raise HTTPException(status_code=400, detail="Path traversal detected")
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
        # Release lock on error (before thread starts)
        upload_lock.release()
        current_upload_info["job_id"] = None
        current_upload_info["started_at"] = None

        # Clean up on error
        if job_dir.exists():
            shutil.rmtree(job_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/status/{job_id}", response_model=JobStatusResponse, tags=["Lineage"])
async def get_job_status(job_id: str, user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> JobStatusResponse:
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
async def get_job_result(job_id: str, user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> LineageResultResponse:
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
                logger.info(f"✓ Cleaned up job {job_id}")
            except Exception as cleanup_error:
                # Log but don't fail the request
                logger.warning(f"Failed to cleanup job {job_id}: {cleanup_error}")

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
async def delete_job(job_id: str, user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> Dict[str, str]:
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
async def list_jobs(user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> Dict[str, Any]:
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
            except Exception as e:
                logger.warning(f"Failed to read status for job {job_id}: {e}")
                jobs.append({
                    "job_id": job_id,
                    "status": "unknown",
                    "progress": 0,
                    "current_step": "Error reading status"
                })

    return {"jobs": jobs, "total": len(jobs)}


# ============================================================================
# Developer Mode Endpoints (v0.9.0)
# ============================================================================

@app.get("/api/debug/logs", tags=["Developer"])
async def get_debug_logs(
    lines: int = Query(1000, ge=1, le=10000),
    level: Optional[str] = Query(None),
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> Dict[str, Any]:
    """
    Get recent log entries for debugging (Developer Mode).

    Args:
        lines: Number of recent log lines to return (default: 1000, max: 10000)
        level: Filter by log level (INFO, WARNING, ERROR, DEBUG)

    Returns:
        Dictionary with logs array and metadata
    """
    # Try multiple log locations
    log_paths = [
        Path("/tmp/backend.log"),  # Created by start-app.sh
        Path("/tmp/data_lineage.log"),
        Path("logs/data_lineage.log"),
        Path("/home/site/data/logs/app.log"),
    ]

    log_file = None
    for path in log_paths:
        if path.exists():
            log_file = path
            break

    if not log_file:
        return {
            "logs": [],
            "total": 0,
            "source": "No log file found",
            "searched_paths": [str(p) for p in log_paths]
        }

    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()

        # Get last N lines
        recent_lines = all_lines[-lines:]

        # Filter by level if specified
        if level:
            filtered_lines = [
                line for line in recent_lines
                if f" {level.upper()} " in line
            ]
        else:
            filtered_lines = recent_lines

        return {
            "logs": filtered_lines,
            "total": len(filtered_lines),
            "source": str(log_file),
            "level_filter": level
        }

    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")


@app.delete("/api/debug/logs/clear", tags=["Developer"])
async def clear_debug_logs(
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> Dict[str, Any]:
    """
    Clear the backend log file (Developer Mode).

    Returns:
        Dictionary with success status and message
    """
    # Try multiple log locations (same as get_debug_logs)
    log_paths = [
        Path("/tmp/backend.log"),  # Created by start-app.sh
        Path("/tmp/data_lineage.log"),
        Path("logs/data_lineage.log"),
        Path("/home/site/data/logs/app.log"),
    ]

    log_file = None
    for path in log_paths:
        if path.exists():
            log_file = path
            break

    if not log_file:
        return {
            "success": False,
            "message": "No log file found",
            "searched_paths": [str(p) for p in log_paths]
        }

    try:
        # Truncate the log file (clear all contents)
        log_file.write_text("")
        logger.info(f"Log file cleared: {log_file}")

        return {
            "success": True,
            "message": f"Log file cleared: {log_file}",
            "file": str(log_file)
        }

    except Exception as e:
        logger.error(f"Failed to clear log file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")


@app.get("/api/debug/log-level", tags=["Developer"])
async def get_log_level(
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> Dict[str, Any]:
    """
    Get current logging level (Developer Mode).

    Returns:
        Dictionary with current log level
    """
    return {
        "log_level": settings.log_level,
        "run_mode": settings.run_mode
    }


# ==============================================================================
# Database Direct Connection Endpoints (v0.10.0)
# ==============================================================================

@app.get("/api/database/test-connection", tags=["Database"])
async def test_database_connection(
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> Dict[str, Any]:
    """
    Test if database is reachable.

    Returns:
        Dictionary with success status and message

    Example responses:
        Success: {"success": true, "message": "Database connection successful"}
        Disabled: {"success": false, "message": "Database connection not enabled (DB_ENABLED=false)"}
        Error: {"success": false, "message": "Database not reachable: connection refused"}
    """
    try:
        from engine.services import DatabaseRefreshService

        service = DatabaseRefreshService(settings)
        success, message = service.test_connection()

        logger.info(f"Database connection test: {'✅ SUCCESS' if success else '❌ FAILED'} - {message}")

        return {
            "success": success,
            "message": message,
            "dialect": settings.sql_dialect,
            "enabled": settings.db.enabled
        }

    except Exception as e:
        logger.error(f"Database connection test failed: {e}", exc_info=settings.is_debug_mode)
        return {
            "success": False,
            "message": f"Connection test error: {str(e)}",
            "dialect": settings.sql_dialect,
            "enabled": settings.db.enabled
        }


@app.post("/api/database/refresh", tags=["Database"])
async def refresh_from_database(
    background_tasks: BackgroundTasks,
    incremental: bool = False,
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> UploadResponse:
    """
    Refresh metadata from database and start lineage processing.

    This endpoint fetches stored procedures from the database, converts them
    to Parquet files, and triggers the SAME processing pipeline as file upload.

    Args:
        incremental: If True, only fetch changed procedures (faster, default: False)

    Returns:
        Job ID for status polling (same as upload-parquet endpoint)

    Example response:
        {
            "job_id": "20250119_083045_abc123",
            "message": "Database refresh started (incremental mode). Fetched 349 procedures (5 new, 3 updated).",
            "files_received": ["objects.parquet", "dependencies.parquet", "definitions.parquet"]
        }
    """
    # Check if another upload/refresh is in progress
    if not upload_lock.acquire(blocking=False):
        other_job_id = current_upload_info.get("job_id")
        elapsed = time.time() - current_upload_info.get("started_at", time.time())
        raise HTTPException(
            status_code=409,
            detail=f"Another import is in progress (job {other_job_id}, running for {elapsed:.0f}s). Please wait."
        )

    # Generate job ID
    job_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    job_dir = Path("uploads") / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Track upload info
    current_upload_info["job_id"] = job_id
    current_upload_info["started_at"] = time.time()

    try:
        logger.info(f"🔄 Starting database metadata refresh (job_id={job_id}, incremental={incremental})")

        # Fetch metadata from database and convert to Parquet files
        from engine.services import DatabaseRefreshService

        service = DatabaseRefreshService(settings)
        result = service.refresh_and_convert_to_parquet(
            job_dir=job_dir,
            incremental=incremental
        )

        if not result.success:
            # Database fetch failed - release lock and return error
            upload_lock.release()
            current_upload_info["job_id"] = None
            current_upload_info["started_at"] = None

            raise HTTPException(
                status_code=500,
                detail=result.message + (f" Errors: {', '.join(result.errors)}" if result.errors else "")
            )

        # Initialize status file
        status_data = {
            "status": "pending",
            "progress": 0.0,
            "current_step": "Queued",
            "message": "Metadata fetched from database, starting lineage processing...",
            "elapsed_seconds": 0.0
        }
        with open(job_dir / "status.json", 'w') as f:
            json.dump(status_data, f, indent=2)

        # Start background processing (SAME as Parquet upload!)
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
        stats = f"{result.new_procedures} new, {result.updated_procedures} updated" if incremental else f"{result.total_procedures} total"

        return UploadResponse(
            job_id=job_id,
            message=f"Database refresh started ({mode_text} mode). Fetched {result.total_procedures} procedures ({stats}).",
            files_received=["objects.parquet", "dependencies.parquet", "definitions.parquet"]
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is

    except Exception as e:
        # Release lock on error
        upload_lock.release()
        current_upload_info["job_id"] = None
        current_upload_info["started_at"] = None

        logger.error(f"❌ Database refresh failed: {e}", exc_info=settings.is_debug_mode)
        raise HTTPException(status_code=500, detail=f"Database refresh failed: {str(e)}")


@app.get("/api/rules/{dialect}", tags=["Developer"])
async def list_rules(
    dialect: str,
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> Dict[str, Any]:
    """
    List all YAML rules for a specific dialect (Developer Mode).

    Args:
        dialect: SQL dialect (tsql, snowflake, bigquery, etc.)

    Returns:
        List of rule files with metadata
    """
    # API runs from /api directory, so go up one level to find engine/
    rules_dir = Path(__file__).parent.parent / "engine" / "rules" / dialect

    if not rules_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No rules found for dialect: {dialect}"
        )

    rules = []
    for yaml_file in sorted(rules_dir.glob("*.yaml")):
        try:
            import yaml
            with open(yaml_file, 'r') as f:
                content = yaml.safe_load(f)

            rules.append({
                "filename": yaml_file.name,
                "name": content.get("name", "unknown"),
                "description": content.get("description", ""),
                "priority": content.get("priority", 999),
                "enabled": content.get("enabled", True),
                "category": content.get("category", "general"),
                "size_bytes": yaml_file.stat().st_size
            })
        except Exception as e:
            logger.warning(f"Failed to parse {yaml_file.name}: {e}")
            rules.append({
                "filename": yaml_file.name,
                "name": "error",
                "description": f"Failed to parse: {str(e)}",
                "priority": 999,
                "enabled": False,
                "category": "error",
                "size_bytes": yaml_file.stat().st_size
            })

    # Sort by priority
    rules.sort(key=lambda r: r["priority"])

    return {
        "dialect": dialect,
        "rules": rules,
        "total": len(rules)
    }


@app.get("/api/rules/{dialect}/{filename}", tags=["Developer"])
async def get_rule_content(
    dialect: str,
    filename: str,
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> Dict[str, Any]:
    """
    Get full content of a specific YAML rule file (Developer Mode).

    Args:
        dialect: SQL dialect (tsql, snowflake, bigquery, etc.)
        filename: Rule filename (e.g., 10_batch_separator.yaml)

    Returns:
        Rule content as text
    """
    # Security: validate filename (prevent path traversal)
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    rule_file = Path(__file__).parent.parent / "engine" / "rules" / dialect / filename

    if not rule_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Rule file not found: {dialect}/{filename}"
        )

    try:
        with open(rule_file, 'r') as f:
            content = f.read()

        return {
            "dialect": dialect,
            "filename": filename,
            "content": content,
            "size_bytes": rule_file.stat().st_size,
            "path": str(rule_file)
        }
    except Exception as e:
        logger.error(f"Failed to read rule file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read rule: {str(e)}")


@app.post("/api/rules/reset/{dialect}", tags=["Developer"])
async def reset_rules_to_defaults(
    dialect: str,
    user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)
) -> Dict[str, Any]:
    """
    Reset YAML rules to defaults for a specific dialect (Developer Mode).

    Copies pristine rules from engine/rules/defaults/{dialect}/ to engine/rules/{dialect}/.

    Args:
        dialect: SQL dialect (tsql, snowflake, bigquery, etc.)

    Returns:
        Status message with number of files reset
    """
    import shutil

    base_dir = Path(__file__).parent.parent / "engine" / "rules"
    defaults_dir = base_dir / "defaults" / dialect
    active_dir = base_dir / dialect

    if not defaults_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No default rules available for dialect: {dialect}"
        )

    try:
        # Count files before reset
        before_count = len(list(active_dir.glob("*.yaml"))) if active_dir.exists() else 0

        # Remove current rules and copy defaults
        if active_dir.exists():
            shutil.rmtree(active_dir)
        shutil.copytree(defaults_dir, active_dir)

        # Count files after reset
        after_count = len(list(active_dir.glob("*.yaml")))

        logger.info(f"Reset {dialect} rules: {before_count} → {after_count} files")

        return {
            "status": "success",
            "dialect": dialect,
            "files_before": before_count,
            "files_after": after_count,
            "message": f"Reset {after_count} rule files to defaults"
        }

    except Exception as e:
        logger.error(f"Failed to reset rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset rules: {str(e)}")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """
    Serve the frontend React application (for Azure deployment).
    
    In Azure, static files are in /home/site/wwwroot/static/
    Locally, this returns a 404 (use separate Vite dev server).
    """
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # In development, frontend runs separately on port 3000
        return JSONResponse(
            content={
                "message": "Frontend not available",
                "tip": "In development, run frontend separately: cd frontend && npm run dev",
                "production": "In Azure, frontend is served from /static directory"
            },
            status_code=404
        )


@app.delete("/api/clear-data", tags=["Admin"])
async def clear_all_data(user: Optional[Dict[str, Any]] = Depends(verify_azure_auth)) -> Dict[str, Any]:
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
        reload=False,  # Disabled for production/UAT (enable for local dev)
        log_level="info"
    )
