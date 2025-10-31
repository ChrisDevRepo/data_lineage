# Simple Multi-User Optimization (Pragmatic Approach)

**Branch:** `optimization/pre-production-hardening`
**Philosophy:** Prevent crashes/corruption with **minimal code changes**. No overkill for rare concurrent scenarios.

---

## Core Strategy: Simple Blocking

**Assumption:** Two users uploading simultaneously is rare (< 5% of time)
**Solution:** When User A is uploading, User B gets clear "busy" message and waits

**Benefits:**
- ✅ No database corruption
- ✅ No "database locked" errors
- ✅ Simple to implement (5 hours vs 30 hours)
- ✅ Easy to understand and maintain

**Trade-off:** User B must wait (but this is acceptable given low probability)

---

## SIMPLIFIED MUST-FIX (5 items, 10 hours)

### 1. Global Upload Lock (Simple Blocking) ⭐ KEY FIX
**Effort:** 3 hours
**Impact:** Prevents all concurrent write issues

**How it works:**
1. API maintains single global flag: `is_processing = False`
2. Upload endpoint checks flag before accepting job
3. If busy → return HTTP 409 (Conflict) with friendly message
4. Frontend shows: "Another user is processing data. Please wait..."

**Implementation:**
```python
# api/main.py (add at top)
import threading

# Global state (simple, no Redis needed for single-tenant)
processing_lock = threading.Lock()
current_job_info = {"user": None, "started_at": None, "job_id": None}

@app.post("/api/upload-parquet")
async def upload_parquet(...):
    # Try to acquire lock (non-blocking)
    if not processing_lock.acquire(blocking=False):
        # Another upload in progress
        return JSONResponse(
            status_code=409,
            content={
                "error": "System is currently processing another upload",
                "message": "Please wait a few minutes and try again",
                "current_job": current_job_info
            }
        )

    try:
        # Process upload
        current_job_info.update({
            "user": "current_user",  # From Azure auth if available
            "started_at": datetime.now().isoformat(),
            "job_id": job_id
        })

        # ... existing upload logic ...

    finally:
        # Always release lock
        processing_lock.release()
        current_job_info.update({"user": None, "started_at": None, "job_id": None})
```

**Frontend handling:**
```typescript
// frontend/components/ImportDataModal.tsx
const response = await fetch(`${API_BASE_URL}/api/upload-parquet`, ...);

if (response.status === 409) {
    const data = await response.json();
    setError(`System is busy: ${data.message}. Please try again in a few minutes.`);
    return;
}
```

---

### 2. SQL Injection Fixes (Critical Security)
**Effort:** 2 hours
**Impact:** Prevents data theft even with Azure auth

**Fix 3 locations with parameterized queries:**
- `lineage_v3/core/duckdb_workspace.py:539-555`
- `lineage_v3/parsers/quality_aware_parser.py:830-834`
- `lineage_v3/parsers/quality_aware_parser.py:859-865`

**Quick fix pattern:**
```python
# BEFORE (vulnerable)
query = f"SELECT * FROM objects WHERE schema_name = '{schema}' AND object_name = '{obj}'"

# AFTER (safe)
query = "SELECT * FROM objects WHERE schema_name = ? AND object_name = ?"
result = self.connection.execute(query, [schema, obj])
```

---

### 3. Path Traversal Protection
**Effort:** 1 hour
**Impact:** Prevents arbitrary file writes

**One-liner fix:**
```python
# api/main.py (line ~434)
filename = os.path.basename(upload_file.filename)  # Strip path components
if '..' in filename or '/' in filename or '\\' in filename:
    raise HTTPException(400, "Invalid filename")
```

---

### 4. Frontend API URL Configuration
**Effort:** 2 hours
**Impact:** Required for Azure deployment

**Create config file:**
```typescript
// frontend/config.ts (NEW)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**Update 4 files to use it:**
- `ImportDataModal.tsx`
- `DetailSearchModal.tsx`
- `SqlViewer.tsx`
- `InteractiveTracePanel.tsx` (if has API calls)

---

### 5. CORS Configuration for Azure
**Effort:** 1 hour
**Impact:** Required for Azure deployment

**Update CORS:**
```python
# api/main.py
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Requested-With"],
)
```

**Add to .env.template:**
```
ALLOWED_ORIGINS=https://your-app.azurewebsites.net,http://localhost:3000
```

---

## OPTIONAL IMPROVEMENTS (Do Later if Needed)

### A. Read-Only Connections During Upload
**When:** If users report "database locked" errors during browsing
**Effort:** 2 hours

```python
# lineage_v3/core/duckdb_workspace.py
def __init__(self, workspace_path: Path, read_only: bool = False):
    self.read_only = read_only
    # ... existing code ...

# api/main.py (query endpoints)
@app.get("/api/ddl/{object_id}")
async def get_ddl(object_id: int):
    with DuckDBWorkspace(workspace_path=str(workspace_file), read_only=True) as db:
        # Read-only connection can run during uploads
        result = db.connection.execute(...)
```

---

### B. Transaction Boundaries (If Corruption Occurs)
**When:** If you see partial data after failed uploads
**Effort:** 3 hours

```python
# lineage_v3/core/duckdb_workspace.py
def _load_parquet_file(self, file_path: Path, table_name: str, replace: bool = False):
    try:
        self.connection.begin()
        # ... load operations ...
        self.connection.commit()
    except Exception as e:
        self.connection.rollback()
        raise
```

---

### C. File Size Limits (If Disk Issues)
**When:** If uploads fill disk or cause OOM
**Effort:** 1 hour

```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

if file_size > MAX_FILE_SIZE:
    raise HTTPException(413, "File too large")
```

---

### D. Database Indexes (If Queries Slow)
**When:** If users complain about slow searches with 10K+ objects
**Effort:** 1 hour

```sql
CREATE INDEX IF NOT EXISTS idx_objects_type ON objects(object_type);
CREATE INDEX IF NOT EXISTS idx_objects_schema_name ON objects(schema_name, object_name);
```

---

### E. Better Logging (If Hard to Debug)
**When:** Production issues occur
**Effort:** 2 hours

Replace `print()` with `logger.info()` in api/main.py

---

## Implementation Order

### Phase 1: Core Multi-User (10 hours / 1.5 days)
1. ✅ Global upload lock (3h) - **PRIORITY 1**
2. ✅ SQL injection fixes (2h) - **PRIORITY 2**
3. ✅ Path traversal fix (1h) - **PRIORITY 3**
4. ✅ Frontend API URLs (2h) - **PRIORITY 4**
5. ✅ CORS config (1h) - **PRIORITY 5**
6. ✅ Testing (1h)

### Phase 2: If Problems Occur (Optional)
- Read-only connections (2h) - If "database locked" errors
- Transaction boundaries (3h) - If data corruption
- File size limits (1h) - If disk issues
- Database indexes (1h) - If slow queries
- Better logging (2h) - If debugging needed

---

## Testing Plan (Simple)

### Test 1: Concurrent Upload Blocking
**Steps:**
1. User A starts upload (takes 5+ minutes)
2. User B tries to upload immediately
3. **Expected:** User B gets HTTP 409 with friendly message
4. User A finishes
5. User B retries → succeeds

### Test 2: Browse During Upload
**Steps:**
1. User A starts upload
2. User B browses lineage, searches, views DDL
3. **Expected:** All queries work (may be slightly slower, but no errors)

### Test 3: Security
**Steps:**
1. Upload file named: `../../etc/passwd.parquet`
2. **Expected:** Rejected with "Invalid filename"

### Test 4: Azure Deployment
**Steps:**
1. Deploy to Azure Web Apps
2. Access from browser
3. **Expected:** API calls work, CORS headers correct

---

## User Experience

### Scenario: User B tries to upload while User A is processing

**Current (BROKEN):**
- ❌ Cryptic "database locked" error
- ❌ App appears frozen
- ❌ Potential data corruption

**After Fix (SIMPLE):**
- ✅ Clear message: "System is currently processing another upload. Please wait a few minutes and try again."
- ✅ User B knows to wait
- ✅ No crashes, no corruption
- ✅ Optional: Show "Started at: 2:45 PM" so user knows how long to wait

---

## Monitoring (Optional)

If you want visibility into concurrent access patterns:

```python
# api/main.py
upload_attempts = 0
blocked_attempts = 0

@app.get("/api/stats")
async def get_stats():
    return {
        "upload_attempts": upload_attempts,
        "blocked_attempts": blocked_attempts,
        "currently_processing": processing_lock.locked()
    }
```

Track in Application Insights:
- How often does blocking occur? (If > 20%, consider job queue)
- Average upload duration? (Optimize if > 10 min)

---

## Configuration Files Needed

### 1. Backend `.env`
```bash
# Add to .env
ALLOWED_ORIGINS=https://your-frontend.azurewebsites.net,http://localhost:3000
```

### 2. Frontend `.env.production`
```bash
# Create frontend/.env.production
VITE_API_URL=https://your-backend.azurewebsites.net
```

### 3. Frontend `.env.development` (existing)
```bash
# frontend/.env.development (or .env)
VITE_API_URL=http://localhost:8000
```

---

## Deployment Checklist

- [ ] Backend: Add `ALLOWED_ORIGINS` to Azure App Settings
- [ ] Frontend: Set `VITE_API_URL` in Azure build configuration
- [ ] Test: Login with 2 users, verify concurrent upload blocking
- [ ] Test: User B can browse while User A uploads
- [ ] Monitor: Check logs for 409 errors (indicates blocking working)

---

## Why This Approach Works

**Simple blocking is sufficient because:**

1. **Low concurrency:** 2-5 users, rarely simultaneous uploads
2. **Predictable:** Users understand "busy" message
3. **Safe:** No database corruption possible
4. **Maintainable:** ~100 lines of code, easy to understand
5. **Extensible:** Can add job queue later if needed

**Avoids over-engineering:**
- ❌ Redis/RabbitMQ job queue (adds complexity)
- ❌ Connection pooling (DuckDB file-based, not needed)
- ❌ Distributed locks (single-tenant app)
- ❌ WebSockets (polling is fine for rare uploads)

---

## Cost-Benefit Analysis

| Approach | Effort | Pros | Cons |
|----------|--------|------|------|
| **Simple blocking (CHOSEN)** | 10h | Simple, safe, maintainable | User B waits |
| Job queue | 30h | Professional UX | Over-engineered |
| Do nothing | 0h | Zero effort | Crashes, corruption |

**Verdict:** Simple blocking is the sweet spot for your use case.

---

## Next Steps

**Approve this simplified plan?**

If yes, I will:
1. Implement the 5 MUST-FIX items (10 hours)
2. Test concurrent scenarios
3. Document changes
4. Create PR for review

**Timeline:** 1.5 days (10 hours + testing)

**After deployment, monitor:**
- Frequency of HTTP 409 errors (blocking)
- If > 20% of uploads blocked → consider job queue
- If = 0 errors → perfect, no changes needed
