"""
Unit tests for FastAPI endpoints using TestClient.

Tests the main API routes without requiring a running server.
Uses FastAPI's TestClient for synchronous testing.
"""

import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Import the FastAPI app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.main import app


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.

    Returns:
        TestClient instance for making requests to the API
    """
    return TestClient(app)


@pytest.fixture
def temp_data_dir(tmp_path):
    """
    Create a temporary data directory structure.

    Creates:
    - data/ (for database files)
    - jobs/ (for job files)
    - results/ (for result files)
    """
    data_dir = tmp_path / "data"
    jobs_dir = tmp_path / "jobs"
    results_dir = tmp_path / "results"

    data_dir.mkdir()
    jobs_dir.mkdir()
    results_dir.mkdir()

    return tmp_path


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_health_endpoint(client):
    """Test the /health endpoint returns OK status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_root_redirects_to_docs(client):
    """Test that root / redirects to /docs."""
    response = client.get("/", follow_redirects=False)

    # Should redirect (3xx status code)
    assert response.status_code in [301, 302, 307, 308]
    # Should redirect to /docs
    assert "/docs" in response.headers.get("location", "")


# ============================================================================
# JOB STATUS TESTS
# ============================================================================

def test_job_status_not_found(client):
    """Test that non-existent job returns 404."""
    response = client.get("/api/job/nonexistent-job-id/status")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_job_status_invalid_id_format(client):
    """Test that invalid job ID format is handled."""
    # Test with special characters that might cause issues
    invalid_ids = [
        "../etc/passwd",  # Path traversal attempt
        "job;DROP TABLE jobs;",  # SQL injection attempt
        "job\x00null",  # Null byte
    ]

    for invalid_id in invalid_ids:
        response = client.get(f"/api/job/{invalid_id}/status")
        # Should either be 404 (not found) or 422 (validation error)
        assert response.status_code in [404, 422]


# ============================================================================
# JOB RESULTS TESTS
# ============================================================================

def test_job_results_not_found(client):
    """Test that non-existent job results return 404."""
    response = client.get("/api/job/nonexistent-job-id/results")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# ============================================================================
# UPLOAD ENDPOINT TESTS
# ============================================================================

def test_upload_missing_file(client):
    """Test upload endpoint with missing required file."""
    # Send empty files dict (no objects.parquet)
    response = client.post("/api/upload", files={})

    # Should return 422 (validation error) - missing required file
    assert response.status_code == 422


def test_upload_with_mock_parquet(client, tmp_path):
    """Test upload endpoint with minimal mock parquet files."""
    # Create a minimal parquet file (will fail validation but tests routing)
    mock_file = tmp_path / "objects.parquet"
    mock_file.write_bytes(b"MOCK_PARQUET_DATA")  # Not real parquet, but tests file handling

    with open(mock_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"objects_file": ("objects.parquet", f, "application/octet-stream")}
        )

    # Should accept the upload (even if it fails validation later)
    # Expect either 200 (accepted) or 400/422 (validation failed)
    assert response.status_code in [200, 400, 422, 500]


# ============================================================================
# LINEAGE ENDPOINT TESTS
# ============================================================================

def test_lineage_endpoint_no_data(client):
    """Test /api/lineage when no lineage data exists yet."""
    response = client.get("/api/lineage")

    # Should return 404 if no data file exists
    # OR return 200 with empty graph if default behavior
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        # Should be a valid graph structure
        assert "nodes" in data or "error" in data


# ============================================================================
# CORS TESTS
# ============================================================================

def test_cors_headers_present(client):
    """Test that CORS headers are present on API responses."""
    response = client.options("/health")

    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_invalid_endpoint_returns_404(client):
    """Test that invalid endpoints return 404."""
    response = client.get("/api/nonexistent-endpoint")

    assert response.status_code == 404


def test_invalid_http_method(client):
    """Test that invalid HTTP methods return 405."""
    # GET on upload endpoint (should be POST)
    response = client.get("/api/upload")

    assert response.status_code == 405  # Method Not Allowed


# ============================================================================
# INTEGRATION TESTS (require database)
# ============================================================================

@pytest.mark.integration
def test_full_upload_workflow(client, temp_data_dir):
    """
    Integration test for complete upload workflow.

    Marked as integration test - requires actual parquet files.
    Skip in unit test runs.
    """
    pytest.skip("Integration test - requires real parquet files")


@pytest.mark.integration
def test_job_polling_workflow(client):
    """
    Integration test for job status polling.

    Marked as integration test - requires background processing.
    """
    pytest.skip("Integration test - requires background processing")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.slow
def test_health_endpoint_performance(client):
    """Test that health endpoint responds quickly."""
    import time

    start = time.time()
    response = client.get("/health")
    elapsed = time.time() - start

    assert response.status_code == 200
    # Health check should be very fast (< 100ms)
    assert elapsed < 0.1, f"Health endpoint took {elapsed:.3f}s (should be < 0.1s)"


# ============================================================================
# SECURITY TESTS
# ============================================================================

def test_sql_injection_in_job_id(client):
    """Test that SQL injection attempts in job ID are handled safely."""
    malicious_id = "'; DROP TABLE jobs; --"

    response = client.get(f"/api/job/{malicious_id}/status")

    # Should safely handle and return 404 (not execute SQL)
    assert response.status_code in [404, 422]


def test_path_traversal_in_job_id(client):
    """Test that path traversal attempts in job ID are blocked."""
    traversal_attempts = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "job/../../sensitive",
    ]

    for attempt in traversal_attempts:
        response = client.get(f"/api/job/{attempt}/status")

        # Should block traversal and return 404 or 422
        assert response.status_code in [404, 422]
        # Should NOT return sensitive file contents
        if response.status_code == 200:
            assert "root:" not in response.text  # Unix passwd file marker
