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

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
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

# API startup time (for uptime calculation)
START_TIME = time.time()

# In-memory job tracking (lost on restart - acceptable per spec)
active_jobs = {}  # job_id -> {"status": str, "thread": Thread}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup
    JOBS_DIR.mkdir(exist_ok=True)
    print("🚀 Vibecoding Lineage Parser API v3.0.0")
    print(f"📁 Jobs directory: {JOBS_DIR}")
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


def run_processing_thread(job_id: str, job_dir: Path):
    """Thread function to run lineage processing in background"""
    try:
        result = process_lineage_job(job_id, job_dir)
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


@app.post("/api/upload-parquet", response_model=UploadResponse, tags=["Lineage"])
async def upload_parquet(
    background_tasks: BackgroundTasks,
    objects: UploadFile = File(..., description="objects.parquet"),
    dependencies: UploadFile = File(..., description="dependencies.parquet"),
    definitions: UploadFile = File(..., description="definitions.parquet"),
    query_logs: Optional[UploadFile] = File(None, description="query_logs.parquet (optional)")
):
    """
    Upload Parquet files and start lineage processing.

    Args:
        objects: objects.parquet file
        dependencies: dependencies.parquet file
        definitions: definitions.parquet file
        query_logs: query_logs.parquet file (optional)

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
        # Save uploaded files
        required_files = [
            (objects, "objects.parquet"),
            (dependencies, "dependencies.parquet"),
            (definitions, "definitions.parquet")
        ]

        for upload_file, filename in required_files:
            if upload_file is None:
                raise HTTPException(status_code=400, detail=f"Missing required file: {filename}")

            file_path = job_dir / filename
            with open(file_path, 'wb') as f:
                content = await upload_file.read()
                f.write(content)
            files_received.append(filename)

        # Save optional query_logs if provided
        if query_logs:
            file_path = job_dir / "query_logs.parquet"
            with open(file_path, 'wb') as f:
                content = await query_logs.read()
                f.write(content)
            files_received.append("query_logs.parquet")

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

        # Start background processing in a thread
        thread = threading.Thread(
            target=run_processing_thread,
            args=(job_id, job_dir),
            daemon=True
        )
        thread.start()

        # Track job
        active_jobs[job_id] = {
            "status": "processing",
            "thread": thread,
            "created_at": time.time()
        }

        return UploadResponse(
            job_id=job_id,
            message="Files uploaded successfully. Processing started.",
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
            message=status_data.get("message")
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

        if status_data["status"] != "completed":
            return LineageResultResponse(
                job_id=job_id,
                status=JobStatus(status_data["status"]),
                data=None,
                summary=None,
                errors=[status_data.get("message", "Job not completed")]
            )

        # Get result data
        result_data = get_job_result_data(job_id)

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
