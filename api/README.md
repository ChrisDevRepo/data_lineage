# FastAPI Backend

**Status:** 🚧 **Week 2-3 Implementation** (Not yet started)

## Overview

FastAPI backend that wraps existing `lineage_v3` Python code for web-based lineage parsing.

**Key Principle:** Existing Python code runs **unchanged** - this is just a web API wrapper.

## Files

- `main.py` - FastAPI application with all endpoints
- `background_tasks.py` - Background processing wrapper
- `models.py` - Pydantic models for request/response
- `requirements.txt` - API-specific dependencies

## Endpoints

### POST /api/upload-parquet
Upload 4 Parquet files, get job ID back.

### GET /api/status/{job_id}
Poll for job status (every 2 seconds).

### GET /api/result/{job_id}
Get final lineage JSON when complete.

### GET /health
Health check for container orchestration.

## Background Processing

The `process_lineage()` function wraps existing modules:

```python
from lineage_v3.core import DuckDBWorkspace
from lineage_v3.parsers import QualityAwareParser
from lineage_v3.output import FrontendFormatter

# Run existing pipeline unchanged
workspace = DuckDBWorkspace()
workspace.load_parquet(job_dir)  # EXISTING METHOD
parser = QualityAwareParser(workspace)
formatter = FrontendFormatter(workspace)
```

## Job Storage

Files stored in `/tmp/jobs/{job_id}/`:
- `objects.parquet` (uploaded)
- `dependencies.parquet` (uploaded)
- `definitions.parquet` (uploaded)
- `query_logs.parquet` (optional)
- `status.json` (for polling)
- `result.json` (final output)

**Note:** Ephemeral storage - lost on container restart (acceptable).

## Implementation Timeline

**Week 2-3 (10 days):**
- Day 1-2: File upload endpoint
- Day 3-4: Background processing wrapper
- Day 5: Status & result endpoints
- Day 6-7: (Frontend upload UI)
- Day 8: (Frontend progress display)
- Day 9: (Docker container)
- Day 10: Integration testing

## Reference

See [docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md) - Section 5
