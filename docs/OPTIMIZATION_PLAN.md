# Pre-Production Optimization Plan

**Branch:** `optimization/pre-production-hardening`
**Created:** 2025-10-31
**Target:** Production UAT readiness for multi-user Azure Web App deployment

## Deployment Context

- ✅ **Authentication:** Handled by Azure Web Apps (MFA at network layer)
- ✅ **Single-tenant:** All users see same data (expected behavior)
- ⚠️ **Multi-user concurrent access:** Need to handle simultaneous operations

---

## MUST-FIX Items (Production Blockers)

These are **mandatory** before production deployment. They prevent data corruption, crashes, or security vulnerabilities in multi-user scenarios.

### MUST-1: Database Concurrent Write Protection ⚠️ CRITICAL
**Problem:** Multiple users uploading Parquet files simultaneously will cause DuckDB write conflicts and "database is locked" errors.

**Current State:**
- No write locking mechanism
- Background parsing threads compete for DuckDB write access
- API uses `with DuckDBWorkspace()` without coordination

**Impact:**
- Failed uploads with cryptic errors
- Potential database corruption
- User frustration (upload appears to work but fails silently)

**Solution:** Implement write lock in DuckDB workspace manager

**Files to modify:**
- `lineage_v3/core/duckdb_workspace.py` - Add threading.Lock for writes
- `api/main.py` - Coordinate upload jobs with lock
- `api/background_tasks.py` - Acquire lock before parsing

**Estimated effort:** 6 hours
**Testing:** Simulate 3 concurrent uploads, verify serial processing

**Code example:**
```python
# lineage_v3/core/duckdb_workspace.py
import threading

class DuckDBWorkspace:
    _write_lock = threading.RLock()  # Class-level lock (singleton pattern)

    def connect_for_write(self):
        """Get connection with write lock acquired."""
        self._write_lock.acquire()
        try:
            return self.connect()
        except:
            self._write_lock.release()
            raise

    def release_write_lock(self):
        """Release write lock."""
        self._write_lock.release()
```

---

### MUST-2: SQL Injection Fixes ⚠️ CRITICAL
**Problem:** Even with Azure auth, internal users can exploit SQL injection vulnerabilities (malicious Parquet files, compromised accounts).

**Vulnerable locations:**
1. `lineage_v3/core/duckdb_workspace.py:539-555` - resolve_table_names_to_ids()
2. `lineage_v3/parsers/quality_aware_parser.py:830-834` - table name lookups
3. `lineage_v3/parsers/quality_aware_parser.py:859-865` - dependency queries

**Solution:** Replace f-string interpolation with parameterized queries

**Files to modify:**
- `lineage_v3/core/duckdb_workspace.py`
- `lineage_v3/parsers/quality_aware_parser.py`

**Estimated effort:** 3 hours
**Testing:** Inject SQL payloads in table names, verify rejection

**Code example:**
```python
# Before (VULNERABLE)
conditions.append(f"(schema_name = '{schema}' AND object_name = '{obj}')")
query = f"SELECT ... WHERE {where_clause}"
results = self.connection.execute(query).fetchall()

# After (SAFE)
placeholders = []
params = []
for schema, obj in lookup.values():
    placeholders.append("(schema_name = ? AND object_name = ?)")
    params.extend([schema, obj])

where_clause = ' OR '.join(placeholders)
query = f"SELECT ... WHERE {where_clause}"
results = self.connection.execute(query, params).fetchall()
```

---

### MUST-3: Path Traversal Protection ⚠️ CRITICAL
**Problem:** User-provided filenames could write outside job directory (even with Azure auth, malicious files could be uploaded).

**Vulnerable location:**
- `api/main.py:434-438` - File upload handling

**Solution:** Sanitize filenames and validate paths

**Files to modify:**
- `api/main.py`

**Estimated effort:** 1 hour
**Testing:** Upload file named `../../etc/passwd.parquet`, verify rejection

**Code example:**
```python
import os
from pathlib import Path

# Sanitize filename
filename = os.path.basename(upload_file.filename)  # Strip path components
if '..' in filename or '/' in filename or '\\' in filename:
    raise HTTPException(400, "Invalid filename - path characters not allowed")

# Validate resolved path stays within job directory
file_path = (job_dir / filename).resolve()
if not str(file_path).startswith(str(job_dir.resolve())):
    raise HTTPException(400, "Path traversal detected")
```

---

### MUST-4: Database Transaction Boundaries ⚠️ HIGH
**Problem:** Multi-step operations without transactions can corrupt workspace if interrupted.

**Scenarios:**
- User A uploads → parsing starts → User B uploads → User A's parsing fails midway
- Database left in inconsistent state (partial table loads, missing metadata)

**Vulnerable locations:**
- `lineage_v3/core/duckdb_workspace.py:329-383` - _load_parquet_file()
- `lineage_v3/core/duckdb_workspace.py:593-613` - update_metadata()
- `api/background_tasks.py:308-335` - Batch parsing loop

**Solution:** Wrap operations in BEGIN/COMMIT/ROLLBACK

**Files to modify:**
- `lineage_v3/core/duckdb_workspace.py`
- `api/background_tasks.py`

**Estimated effort:** 4 hours
**Testing:** Kill process mid-upload, verify database consistency

**Code example:**
```python
def _load_parquet_file(self, file_path: Path, table_name: str, replace: bool = False):
    try:
        self.connection.begin()

        if replace:
            self.connection.execute(f"DROP TABLE IF EXISTS {table_name}")

        self.connection.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_parquet('{file_path}')
        """)

        self.connection.commit()
    except Exception as e:
        self.connection.rollback()
        raise RuntimeError(f"Failed to load {file_path}: {e}") from e
```

---

### MUST-5: CORS Configuration for Azure Deployment ⚠️ HIGH
**Problem:** `allow_origins=["*"]` accepts requests from any domain, enabling CSRF attacks.

**Vulnerable location:**
- `api/main.py:78-84`

**Solution:** Restrict to Azure Web App frontend domain

**Files to modify:**
- `api/main.py`
- `.env.template` (add ALLOWED_ORIGINS)

**Estimated effort:** 1 hour
**Testing:** Verify frontend works, external domains blocked

**Code example:**
```python
# api/main.py
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # From environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Requested-With"],
)
```

```bash
# .env.template
# Comma-separated list of allowed origins
ALLOWED_ORIGINS=https://your-frontend.azurewebsites.net,http://localhost:3000
```

---

### MUST-6: Frontend Environment-Based API URLs ⚠️ HIGH
**Problem:** Hardcoded `http://localhost:8000` URLs won't work in Azure deployment.

**Vulnerable locations:**
- `frontend/components/ImportDataModal.tsx` (lines 170, 219)
- `frontend/components/DetailSearchModal.tsx` (line 136)
- `frontend/components/SqlViewer.tsx` (line 45)

**Solution:** Use environment variables for API base URL

**Files to create/modify:**
- `frontend/config.ts` (NEW)
- `frontend/.env.production` (NEW)
- Update all components to use config

**Estimated effort:** 2 hours
**Testing:** Build for production, verify API URL correct

**Code example:**
```typescript
// frontend/config.ts (NEW FILE)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// frontend/.env.production (NEW FILE)
VITE_API_URL=https://your-backend.azurewebsites.net

// Usage in components
import { API_BASE_URL } from '../config';
const response = await fetch(`${API_BASE_URL}/api/metadata`);
```

---

### MUST-7: Job Queue for Serial Upload Processing ⚠️ HIGH
**Problem:** Multiple concurrent uploads create race conditions even with write lock (jobs compete for resources).

**Current state:**
- Each upload spawns background thread immediately
- No queue management
- No "currently processing" indicator

**Impact:**
- User A uploads → starts parsing (takes 10 min)
- User B uploads → blocked by lock, appears hung
- User B sees no feedback, thinks app is broken

**Solution:** Implement job queue with status tracking

**Files to modify:**
- `api/main.py` - Add job queue management
- `api/models.py` - Add "queued" status
- Frontend (optional) - Show queue position

**Estimated effort:** 6 hours
**Testing:** Submit 3 uploads, verify serial processing with status updates

**Code example:**
```python
# api/main.py
from queue import Queue
from dataclasses import dataclass

@dataclass
class UploadJob:
    job_id: str
    files: List[Path]
    incremental: bool
    task: BackgroundTask

# Global job queue (in production, use Redis or RabbitMQ)
job_queue = Queue()
active_job_id = None  # Currently processing job

def process_job_queue():
    """Background worker to process jobs serially."""
    global active_job_id
    while True:
        job = job_queue.get()  # Blocks until job available
        active_job_id = job.job_id
        try:
            job.task.run()
        finally:
            active_job_id = None
            job_queue.task_done()

# Start queue worker on startup
@app.on_event("startup")
def startup():
    thread = threading.Thread(target=process_job_queue, daemon=True)
    thread.start()

@app.post("/api/upload-parquet")
async def upload_parquet(...):
    # ... save files ...

    job = UploadJob(job_id, file_paths, incremental, task)
    job_queue.put(job)

    return {
        "job_id": job_id,
        "status": "queued",
        "queue_position": job_queue.qsize()
    }
```

---

### MUST-8: File Upload Size Limits ⚠️ MEDIUM
**Problem:** Unlimited upload size can exhaust disk/memory, crash server.

**Vulnerable location:**
- `api/main.py:383-438` - No size validation

**Solution:** Add max file size check (500MB reasonable for Parquet)

**Files to modify:**
- `api/main.py`

**Estimated effort:** 2 hours
**Testing:** Upload 1GB file, verify rejection

**Code example:**
```python
MAX_PARQUET_SIZE = 500 * 1024 * 1024  # 500MB

for upload_file in files:
    # Check size before reading
    upload_file.file.seek(0, 2)  # Seek to end
    file_size = upload_file.file.tell()
    upload_file.file.seek(0)  # Reset

    if file_size > MAX_PARQUET_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File {upload_file.filename} exceeds 500MB limit"
        )
```

---

### MUST-9: Database Performance Indexes ⚠️ MEDIUM
**Problem:** Missing indexes slow down queries, especially with 10K+ objects. Multi-user load exacerbates this.

**Impact:**
- Incremental query on objects table scans entire table (slow)
- DDL lookups without indexes degrade with data growth
- Multiple users = multiple slow queries = poor UX

**Solution:** Add strategic indexes

**Files to modify:**
- `lineage_v3/core/duckdb_workspace.py` - Add index creation to schema setup

**Estimated effort:** 2 hours
**Testing:** Compare query times before/after with 10K objects

**Code example:**
```python
# lineage_v3/core/duckdb_workspace.py (add to _initialize_metadata_tables)

def _create_performance_indexes(self):
    """Create indexes for frequently-queried columns."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_objects_type ON objects(object_type)",
        "CREATE INDEX IF NOT EXISTS idx_objects_schema_name ON objects(schema_name, object_name)",
        "CREATE INDEX IF NOT EXISTS idx_metadata_object_id ON lineage_metadata(object_id)",
        "CREATE INDEX IF NOT EXISTS idx_metadata_confidence ON lineage_metadata(confidence)",
        "CREATE INDEX IF NOT EXISTS idx_dependencies_refs ON dependencies(referencing_object_id, referenced_object_id)",
    ]

    for idx_sql in indexes:
        try:
            self.connection.execute(idx_sql)
        except Exception as e:
            logger.warning(f"Index creation skipped: {e}")
```

---

### MUST-10: Logging Standardization ⚠️ MEDIUM
**Problem:** Mixed `print()` and `logger` usage makes production debugging impossible. Multi-user scenarios require clear logging to identify which user's action caused issues.

**Current state:**
- `api/main.py` uses `print()` exclusively
- `api/background_tasks.py` uses `logging.getLogger()`
- No request ID tracking

**Impact:**
- Can't debug production issues (print goes to stdout, not logs)
- Can't correlate errors to specific user actions
- No structured logging for Azure Application Insights

**Solution:** Replace all print() with logger, add request IDs

**Files to modify:**
- `api/main.py` - Replace print() statements
- `api/background_tasks.py` - Add request ID to logs

**Estimated effort:** 3 hours
**Testing:** Review logs in Azure, verify structured format

**Code example:**
```python
# api/main.py (top of file)
import logging
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Add to request context
from fastapi import Request
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Replace
print(f"❌ Search failed for query '{q}': {e}")
# With
logger.error(f"Search failed for query '{q}': {e}", extra={'request_id': request_id_var.get()})
```

---

## MUST-FIX Summary

| # | Item | Severity | Effort | Multi-User Impact |
|---|------|----------|--------|-------------------|
| 1 | Database write lock | CRITICAL | 6h | Prevents concurrent write corruption |
| 2 | SQL injection fixes | CRITICAL | 3h | Prevents data theft/corruption |
| 3 | Path traversal | CRITICAL | 1h | Prevents arbitrary file writes |
| 4 | Transaction boundaries | HIGH | 4h | Prevents partial data corruption |
| 5 | CORS configuration | HIGH | 1h | Prevents CSRF attacks |
| 6 | Frontend API URLs | HIGH | 2h | Required for deployment |
| 7 | Job queue | HIGH | 6h | Serial processing for multi-user |
| 8 | File size limits | MEDIUM | 2h | Prevents DOS via uploads |
| 9 | Database indexes | MEDIUM | 2h | Improves multi-user performance |
| 10 | Logging | MEDIUM | 3h | Enables production debugging |

**Total MUST-FIX effort:** 30 hours (~4 days)

---

## OPTIONAL Improvements (Post-UAT)

These improve user experience, code quality, or future maintainability but are NOT blockers for production UAT.

### OPTIONAL-1: Frontend Accessibility (ARIA Labels)
**Benefit:** Screen reader support, better UX for keyboard users
**Effort:** 2 hours
**Files:** `frontend/components/Toolbar.tsx`, `frontend/components/InteractiveTracePanel.tsx`

---

### OPTIONAL-2: Frontend Responsive Design
**Benefit:** Mobile/tablet support
**Effort:** 8 hours
**Files:** All frontend components
**Note:** If users only access via desktop, can defer

---

### OPTIONAL-3: API Rate Limiting
**Benefit:** Prevent abuse, resource exhaustion
**Effort:** 3 hours
**Files:** `api/main.py` - Add slowapi middleware
**Note:** Azure Web Apps may have built-in rate limiting

---

### OPTIONAL-4: API Automated Tests
**Benefit:** Prevent regressions, enable safe refactoring
**Effort:** 16 hours (70% coverage target)
**Files:** Create `api/tests/` directory
**Priority:** HIGH for long-term maintainability

---

### OPTIONAL-5: Database Foreign Key Constraints
**Benefit:** Referential integrity enforcement
**Effort:** 2 hours
**Files:** `lineage_v3/core/duckdb_workspace.py`
**Note:** Current data validation logic is adequate

---

### OPTIONAL-6: API Timeout Handling
**Benefit:** Prevent hung requests
**Effort:** 4 hours
**Files:** `api/main.py`, `api/background_tasks.py`
**Note:** Azure Web Apps has default timeouts

---

### OPTIONAL-7: Process Pool for Parsing (Replace Threading)
**Benefit:** Better CPU utilization for parsing
**Effort:** 6 hours
**Files:** `api/main.py` - Use ProcessPoolExecutor
**Note:** Only needed if parsing becomes bottleneck

---

### OPTIONAL-8: Python Package Configuration (pyproject.toml)
**Benefit:** Proper package installation, dependency management
**Effort:** 2 hours
**Files:** Create `pyproject.toml`
**Priority:** MEDIUM for development workflow

---

### OPTIONAL-9: Type Hints Completion
**Benefit:** Better IDE support, catch errors with mypy
**Effort:** 8 hours
**Files:** All Python files missing type hints
**Priority:** LOW, mainly code quality

---

### OPTIONAL-10: Frontend Color Contrast Fixes
**Benefit:** WCAG AA compliance
**Effort:** 1 hour
**Files:** `frontend/components/InfoModal.tsx`

---

### OPTIONAL-11: Frontend Empty State Illustrations
**Benefit:** Better UX when no data
**Effort:** 2 hours
**Files:** Modal components

---

### OPTIONAL-12: API Security Headers
**Benefit:** Defense-in-depth
**Effort:** 1 hour
**Files:** `api/main.py` - Add middleware
**Note:** Azure Web Apps may set these

---

### OPTIONAL-13: Batch Commit Optimization
**Benefit:** 5-10x faster metadata updates
**Effort:** 3 hours
**Files:** `api/background_tasks.py`
**Priority:** MEDIUM if parsing is slow

---

### OPTIONAL-14: Real-Time Job Status Updates (SSE/WebSockets)
**Benefit:** Users see live progress without polling
**Effort:** 8 hours
**Files:** Add SSE endpoint, update frontend
**Priority:** HIGH for UX, but not essential for UAT

---

## OPTIONAL Summary

| # | Item | Benefit | Effort | Priority |
|---|------|---------|--------|----------|
| 1 | ARIA labels | Accessibility | 2h | LOW |
| 2 | Responsive design | Mobile support | 8h | LOW (if desktop-only) |
| 3 | Rate limiting | DOS prevention | 3h | MEDIUM |
| 4 | Automated tests | Quality assurance | 16h | HIGH (post-UAT) |
| 5 | Foreign keys | Data integrity | 2h | LOW |
| 6 | Timeout handling | Reliability | 4h | MEDIUM |
| 7 | Process pool | Performance | 6h | LOW |
| 8 | Package config | Dev workflow | 2h | MEDIUM |
| 9 | Type hints | Code quality | 8h | LOW |
| 10 | Color contrast | Accessibility | 1h | LOW |
| 11 | Empty states | UX polish | 2h | LOW |
| 12 | Security headers | Defense-in-depth | 1h | LOW |
| 13 | Batch commits | Performance | 3h | MEDIUM |
| 14 | Real-time status | UX polish | 8h | HIGH (post-UAT) |

**Total OPTIONAL effort:** 66 hours (~8 days)

---

## Recommended Phasing

### Phase 1: Production UAT Readiness (30 hours / 4 days)
**Target:** Safe multi-user deployment to Azure Web Apps
**Items:** MUST-1 through MUST-10

### Phase 2: Post-UAT Improvements (24 hours / 3 days)
**Target:** Production hardening and monitoring
**Items:**
- OPTIONAL-4: Automated tests (16h)
- OPTIONAL-3: Rate limiting (3h)
- OPTIONAL-6: Timeout handling (4h)
- OPTIONAL-13: Batch commits (3h)

### Phase 3: UX Enhancements (18 hours / 2 days)
**Target:** Polish and user experience
**Items:**
- OPTIONAL-14: Real-time status (8h)
- OPTIONAL-2: Responsive design (8h) - IF needed
- OPTIONAL-1: ARIA labels (2h)

### Phase 4: Technical Debt (24 hours / 3 days)
**Target:** Long-term maintainability
**Items:**
- OPTIONAL-9: Type hints (8h)
- OPTIONAL-8: Package config (2h)
- OPTIONAL-7: Process pool (6h)
- OPTIONAL-5: Foreign keys (2h)
- Others: 6h

---

## Testing Plan

### Must-Test Scenarios (Before UAT)
1. **Concurrent Upload Test:**
   - 3 users upload Parquet files simultaneously
   - Verify: Serial processing, no errors, all data visible

2. **Upload + Query Test:**
   - User A starts upload (long-running parse)
   - User B browses lineage during upload
   - Verify: No "database locked" errors, queries succeed

3. **Race Condition Test:**
   - Rapid-fire job submissions
   - Verify: Queue processes correctly, no lost jobs

4. **Security Test:**
   - Upload malicious filename: `../../etc/passwd.parquet`
   - Upload SQL injection payload in schema name
   - Verify: Both rejected with clear error

5. **Crash Recovery Test:**
   - Kill API process mid-upload
   - Restart, verify database consistency
   - Verify: Can resume operations

6. **Load Test:**
   - 10 concurrent users browsing/searching
   - 2 concurrent uploads (queued)
   - Monitor: Response times, memory usage, CPU

---

## Deployment Checklist

### Pre-Deployment
- [ ] All MUST-FIX items completed and tested
- [ ] `.env` configured for Azure (ALLOWED_ORIGINS, API URLs)
- [ ] Database indexes created
- [ ] Logging outputs to Azure Application Insights
- [ ] Frontend built with production environment variables

### Azure Configuration
- [ ] Azure Web App MFA enabled and tested
- [ ] CORS headers verified in Azure
- [ ] File upload limits set in Azure App Service
- [ ] Monitoring/alerts configured
- [ ] Backup strategy for DuckDB workspace file

### Post-Deployment Validation
- [ ] Test login with 2+ users
- [ ] Test concurrent upload + browse scenario
- [ ] Monitor logs for errors in first 24h
- [ ] Performance baseline established
- [ ] Rollback plan documented

---

## Questions for Review

1. **Job Queue:** Do you want visible queue position in UI, or is "processing" status sufficient?

2. **File Size Limits:** Is 500MB per Parquet file reasonable for your data volumes?

3. **Logging:** Do you use Azure Application Insights or another logging service?

4. **Testing:** Do you have test Parquet files we can use for load testing?

5. **Rollout:** Pilot with small group first, or full team immediately?

6. **Optional Items:** Which OPTIONAL items (if any) should be prioritized for Phase 2?

7. **Mobile Access:** Do users need mobile/tablet support? (Affects OPTIONAL-2 priority)

---

## Next Steps

**⚠️ SUPERSEDED BY SIMPLIFIED APPROACH**

See **[SIMPLE_MULTI_USER_FIX.md](SIMPLE_MULTI_USER_FIX.md)** for pragmatic implementation plan.

**Simplified plan reduces scope:**
- Original: 10 MUST-FIX items, 30 hours
- Simplified: 5 MUST-FIX items, 10 hours
- Approach: Simple blocking instead of job queue

**Rationale:** Low probability of concurrent uploads means simple "busy" blocking is sufficient. Avoids over-engineering while ensuring safety.

---

**Estimated Timeline (Simplified):**
- Phase 1 (Simplified MUST-FIX): 1.5 days (10 hours)
- Testing: 0.5 day
- **Total to UAT-ready:** 2 days
