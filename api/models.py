"""
Pydantic models for FastAPI endpoints.

Defines request/response schemas for the lineage parser API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response after successful file upload"""
    job_id: str = Field(..., description="Unique job identifier")
    message: str = Field(..., description="Success message")
    files_received: List[str] = Field(..., description="List of received filenames")


class JobStatusResponse(BaseModel):
    """Response for job status polling"""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    current_step: Optional[str] = Field(None, description="Current processing step")
    elapsed_seconds: Optional[float] = Field(None, description="Elapsed time in seconds")
    estimated_remaining_seconds: Optional[float] = Field(None, description="Estimated remaining time")
    message: Optional[str] = Field(None, description="Status message or error details")
    errors: Optional[List[str]] = Field(None, description="List of errors if job failed")
    warnings: Optional[List[str]] = Field(None, description="List of warnings")


class LineageResultResponse(BaseModel):
    """Response containing final lineage JSON"""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Lineage graph nodes (frontend format)")
    summary: Optional[Dict[str, Any]] = Field(None, description="Lineage summary statistics")
    errors: Optional[List[str]] = Field(None, description="List of errors if job failed")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Health status (ok/degraded/down)")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="API uptime in seconds")


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    job_id: Optional[str] = Field(None, description="Job ID if applicable")
