# Code Improvement Examples
**Data Lineage Visualizer v4.0.3**
**Date:** 2025-11-05

This document provides ready-to-apply code improvements for the codebase cleanup.

---

## Example 1: Remove AI Dependency from requirements.txt

### Current (lines 29-31)
```python
# ------------------------------------------------------------------------------
# AI & LLM Integration
# ------------------------------------------------------------------------------
openai>=1.0.0                    # Azure OpenAI integration for AI disambiguation

```

### Improved
```python
# (Remove entire section)
```

### Testing
```bash
# After change, verify requirements install correctly
pip install -r requirements.txt
python -c "import duckdb, sqlglot, fastapi; print('✅ Core dependencies OK')"
```

---

## Example 2: Update API Main Module Docstring

### File: `api/main.py`

### Current (lines 1-5)
```python
"""
FastAPI Backend for Vibecoding Lineage Parser v3

Web API wrapper for existing lineage_v3 Python code.
"""
```

### Improved
```python
"""
Data Lineage Visualizer API

FastAPI backend providing REST API for lineage analysis and visualization.

Features:
- Parquet file upload with automatic schema detection
- Background job processing with status polling
- Full-text search across DDL definitions
- On-demand DDL fetching with caching
- Incremental and full-refresh parsing modes

Version: 4.0.3
"""
```

---

## Example 3: Replace Print Statements with Logging

### File: `api/main.py`

### Add at top (after imports)
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Replace print() calls

**Line 62-69 (lifespan function):**
```python
# BEFORE:
print("🚀 Vibecoding Lineage Parser API v3.0.0")
print(f"📁 Jobs directory: {JOBS_DIR}")
print(f"💾 Data directory: {DATA_DIR}")
if LATEST_DATA_FILE.exists():
    print(f"✅ Latest data file found: {LATEST_DATA_FILE.name}")
else:
    print(f"ℹ️  No existing data file (will be created on first upload)")
print(f"✅ API ready")

# AFTER:
logger.info("🚀 Data Lineage Visualizer API v4.0.3")
logger.info(f"📁 Jobs directory: {JOBS_DIR}")
logger.info(f"💾 Data directory: {DATA_DIR}")
if LATEST_DATA_FILE.exists():
    logger.info(f"✅ Latest data file found: {LATEST_DATA_FILE.name}")
else:
    logger.info(f"ℹ️  No existing data file (will be created on first upload)")
logger.info(f"✅ API ready")
```

**Line 134:**
```python
# BEFORE:
print(f"Error processing job {job_id}: {e}")

# AFTER:
logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
```

**Line 141:**
```python
# BEFORE:
print(f"✅ Upload lock released for job {job_id}")

# AFTER:
logger.debug(f"✅ Upload lock released for job {job_id}")
```

**Line 390:**
```python
# BEFORE:
print(f"❌ Search failed for query '{q}': {e}")

# AFTER:
logger.error(f"❌ Search failed for query '{q}': {e}", exc_info=True)
```

**Line 586:**
```python
# BEFORE:
print(f"✓ Cleaned up job {job_id}")

# AFTER:
logger.info(f"✓ Cleaned up job {job_id}")
```

---

## Example 4: Fix Bare Exception Handler

### File: `api/main.py` (lines 655-661)

### Current
```python
try:
    status_data = get_job_status_data(job_id)
    jobs.append({
        "job_id": job_id,
        "status": status_data["status"],
        "progress": status_data.get("progress", 0),
        "current_step": status_data.get("current_step", "Unknown")
    })
except:  # ❌ Bare except
    jobs.append({
        "job_id": job_id,
        "status": "unknown",
        "progress": 0,
        "current_step": "Error reading status"
    })
```

### Improved
```python
try:
    status_data = get_job_status_data(job_id)
    jobs.append({
        "job_id": job_id,
        "status": status_data["status"],
        "progress": status_data.get("progress", 0),
        "current_step": status_data.get("current_step", "Unknown")
    })
except Exception as e:  # ✅ Specific exception with logging
    logger.warning(f"Failed to read status for job {job_id}: {e}")
    jobs.append({
        "job_id": job_id,
        "status": "unknown",
        "progress": 0,
        "current_step": "Error reading status"
    })
```

---

## Example 5: Update Health Endpoint Version

### File: `api/main.py` (line 156-160)

### Current
```python
return HealthResponse(
    status="ok",
    version="4.0.0",  # Inconsistent version
    uptime_seconds=time.time() - START_TIME
)
```

### Improved
```python
return HealthResponse(
    status="ok",
    version="4.0.3",  # Match current release
    uptime_seconds=time.time() - START_TIME
)
```

---

## Example 6: Update Parser Comments

### File: `lineage_v3/parsers/quality_aware_parser.py`

### Line 82
```python
# BEFORE:
CONFIDENCE_LOW = 0.5      # Major difference (>25%) - needs AI review

# AFTER:
CONFIDENCE_LOW = 0.5      # Major difference (>25%) - needs review/refinement
```

### Line 253
```python
# BEFORE:
'needs_improvement': quality['needs_ai']  # Renamed from needs_ai

# AFTER:
'needs_improvement': quality['needs_improvement']  # Quality flag for review
```

### Line 455
```python
# BEFORE:
needs_ai = (source_diff > self.THRESHOLD_FAIR or
           target_diff > self.THRESHOLD_FAIR)

# AFTER:
needs_improvement = (source_diff > self.THRESHOLD_FAIR or
                    target_diff > self.THRESHOLD_FAIR)
```

### Line 474-475 (docstring)
```python
# BEFORE:
"""
- Overall match <75% → 0.5 (low confidence, needs AI)
"""

# AFTER:
"""
- Overall match <75% → 0.5 (low confidence, needs review/rule refinement)
"""
```

---

## Example 7: Update .env.template

### File: `.env.template`

### Remove lines 43-63
```bash
# DELETE THIS ENTIRE SECTION:
# ------------------------------------------------------------------------------
# AI Disambiguation Configuration (NEW in v3.7.0)
# ------------------------------------------------------------------------------
# Enable/disable AI-assisted disambiguation (true/false)
# When enabled, AI helps resolve ambiguous table references for SPs with confidence ≤ threshold
AI_ENABLED=true

# Parser confidence threshold to trigger AI disambiguation (0.0 - 1.0)
# Default: 0.85 (SPs with confidence ≤ 0.85 will use AI assistance)
AI_CONFIDENCE_THRESHOLD=0.85

# Minimum AI confidence to accept result (0.0 - 1.0)
# Results below this threshold are rejected and fall back to parser result
AI_MIN_CONFIDENCE=0.70

# Maximum retry attempts with refined prompts
# Default: 2 (one initial attempt + one retry)
AI_MAX_RETRIES=2

# API timeout in seconds
# Default: 10 seconds per AI call
AI_TIMEOUT_SECONDS=10
```

### Update header (lines 1-3)
```bash
# BEFORE:
# ==============================================================================
# Vibecoding Lineage Parser v3 - Environment Configuration Template
# ==============================================================================

# AFTER:
# ==============================================================================
# Data Lineage Visualizer v4.0.3 - Environment Configuration Template
# ==============================================================================
```

---

## Example 8: Add Frontend Environment Configuration

### File: `frontend/.env` (NEW FILE)

```bash
# ==============================================================================
# Data Lineage Visualizer - Frontend Configuration
# ==============================================================================

# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_DEBUG_LOGGING=false
VITE_ENABLE_PERFORMANCE_MONITORING=false

# UI Configuration
VITE_DEFAULT_LAYOUT=LR
VITE_POLL_INTERVAL_MS=2000

# ==============================================================================
# Production Configuration (Azure)
# ==============================================================================
# For production deployment, override VITE_API_BASE_URL:
# VITE_API_BASE_URL=https://your-api.azurewebsites.net
# ==============================================================================
```

### File: `frontend/config.ts` (NEW FILE)

```typescript
/**
 * Application Configuration
 *
 * Centralized configuration management using environment variables.
 */

export const CONFIG = {
  // API Configuration
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',

  // Feature Flags
  DEBUG_LOGGING: import.meta.env.VITE_ENABLE_DEBUG_LOGGING === 'true',
  PERFORMANCE_MONITORING: import.meta.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true',

  // UI Configuration
  DEFAULT_LAYOUT: (import.meta.env.VITE_DEFAULT_LAYOUT || 'LR') as 'LR' | 'TB',
  POLL_INTERVAL_MS: parseInt(import.meta.env.VITE_POLL_INTERVAL_MS || '2000', 10),

  // Timeouts
  API_TIMEOUT_MS: 30000,
  DEBOUNCE_DELAY_MS: 300,
} as const;
```

### File: `frontend/App.tsx` (update line 52)

```typescript
// BEFORE:
const response = await fetch('http://localhost:8000/api/latest-data');

// AFTER:
import { CONFIG } from './config';

// In useEffect:
const response = await fetch(`${CONFIG.API_BASE_URL}/api/latest-data`);
```

---

## Example 9: Update DuckDB Workspace Docstring

### File: `lineage_v3/core/duckdb_workspace.py` (lines 1-17)

### Current
```python
#!/usr/bin/env python3
"""
DuckDB Workspace Manager
========================

Manages the persistent DuckDB database for lineage analysis.

This module provides:
1. DuckDB connection management with persistent workspace
2. Parquet ingestion into DuckDB tables
3. Incremental load metadata tracking
4. Query interface for DMV data access

Author: Vibecoding Team
Version: 3.0.0
Phase: 3 (Core Engine)
"""
```

### Improved
```python
#!/usr/bin/env python3
"""
DuckDB Workspace Manager
========================

Manages the persistent DuckDB database for lineage analysis.

This module provides:
1. DuckDB connection management with persistent workspace
2. Parquet ingestion into DuckDB tables with schema auto-detection
3. Incremental load metadata tracking
4. Query interface for DMV data access
5. Full-text search (FTS) on DDL definitions

Features:
- Automatic schema creation and validation
- MERGE support for incremental updates
- BM25 relevance ranking for text search
- Context manager for safe connection handling

Version: 4.0.3
"""
```

---

## Example 10: Update Frontend package.json Author

### File: `frontend/package.json` (line 7)

### Current
```json
"author": "Vibecoding",
```

### Improved (Option A - Generic)
```json
"author": "Data Lineage Team",
```

### Improved (Option B - Remove)
```json
(delete line)
```

---

## Testing After Changes

### Backend Testing
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify imports
python -c "from api.main import app; print('✅ API imports OK')"
python -c "from lineage_v3.core import DuckDBWorkspace; print('✅ Parser imports OK')"

# 3. Start API and check health
python api/main.py &
API_PID=$!
sleep 2
curl http://localhost:8000/health
kill $API_PID

# 4. Run validation
python lineage_v3/main.py validate
```

### Frontend Testing
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Type check
npm run type-check

# 3. Build verification
npm run build

# 4. Start dev server
npm run dev
```

### Integration Testing
```bash
# Terminal 1: Start backend
python api/main.py

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Test upload
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" \
  -F "files=@test_data/objects.parquet" \
  -F "files=@test_data/dependencies.parquet" \
  -F "files=@test_data/definitions.parquet"

# Check frontend at http://localhost:3000
```

---

## Rollback Plan

If any changes cause issues:

```bash
# 1. Stash changes
git stash

# 2. Test original code
# ... run tests ...

# 3. Apply changes incrementally
git stash pop
git checkout -- <problematic_file>

# 4. Test each change individually
```

---

## Summary of Changes

| File | Change | Risk | Impact |
|------|--------|------|--------|
| `requirements.txt` | Remove openai | Low | Reduces dependencies |
| `api/main.py` | Add logging | Low | Better debugging |
| `api/main.py` | Fix exceptions | Low | Better error handling |
| `api/main.py` | Update versions | None | Consistency |
| `.env.template` | Remove AI config | None | Cleanup |
| `quality_aware_parser.py` | Update comments | None | Clarity |
| `duckdb_workspace.py` | Update docstring | None | Documentation |
| `frontend/.env` | Add config file | Low | Better configuration |
| `frontend/config.ts` | Add config module | Low | Centralized config |
| `package.json` | Update author | None | Branding |

**Total Estimated Time:** 2-3 hours
**Risk Level:** LOW (all changes are non-breaking)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-05
