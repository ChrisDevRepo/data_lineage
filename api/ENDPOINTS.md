# API Endpoints Reference

**Version:** 3.0.1

Detailed endpoint documentation for the FastAPI backend. For interactive testing, use the auto-generated Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 1. POST /api/upload-parquet

Upload 3-5 Parquet files and start lineage processing.

**Parameters:**
- `files` (required): Parquet files (3 required + 2 optional)
- `incremental` (optional, default: `true`): Enable incremental parsing

**Request (Incremental mode - default):**
```bash
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" \
  -F "files=@objects.parquet" \
  -F "files=@dependencies.parquet" \
  -F "files=@definitions.parquet" \
  -F "files=@query_logs.parquet" \
  -F "files=@table_columns.parquet"
```

**Request (Full refresh mode):**
```bash
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" \
  -F "files=@objects.parquet" \
  -F "files=@dependencies.parquet" \
  -F "files=@definitions.parquet"
```

**Incremental Mode:**
- Only re-parses objects that are new, modified, or low confidence (<0.85)
- **50-90% faster** for typical updates
- **Default behavior** (recommended)

**Full Refresh Mode:**
- Re-parses all objects from scratch
- Use when parser bugs are fixed or complete re-analysis needed

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Files uploaded successfully. Processing started in incremental mode.",
  "files_received": [
    "objects.parquet",
    "dependencies.parquet",
    "definitions.parquet",
    "query_logs.parquet",
    "table_columns.parquet"
  ]
}
```

---

## 2. GET /api/status/{job_id}

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

---

## 3. GET /api/result/{job_id}

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

---

## 4. GET /api/search-ddl

Full-text search across all DDL definitions using DuckDB FTS with BM25 ranking.

**Parameters:**
- `q` (required): Search query string (1-200 characters)

**Request:**
```bash
curl "http://localhost:8000/api/search-ddl?q=FeasibilityContacts"
```

**Features:**
- Case-insensitive search by default
- Searches object names and DDL text
- BM25 relevance ranking (most relevant first)
- Automatic stemming (e.g., "customer" matches "customers")
- Phrase search support (e.g., "SELECT * FROM")
- Boolean operators (AND, OR, NOT)
- Wildcard support (e.g., "cust*")

**Response:**
```json
[
  {
    "id": "1275862257",
    "name": "FeasibilityContacts",
    "type": "Table",
    "schema": "CONSUMPTION_PRIMA",
    "score": 4.402409414093763,
    "snippet": "CREATE TABLE [CONSUMPTION_PRIMA].[FeasibilityContacts] (\n    [RECORD_ID] int NULL,\n    [CONTACT_DATE] datetime NULL,\n    [CONTACT_ORIGINATOR] int NULL"
  },
  {
    "id": "1811106209",
    "name": "spLoadFeasibilityData",
    "type": "Stored Procedure",
    "schema": "CONSUMPTION_PRIMA",
    "score": 2.156,
    "snippet": "CREATE PROC [CONSUMPTION_PRIMA].[spLoadFeasibilityData] AS\nBEGIN\nINSERT INTO FeasibilityContacts..."
  }
]
```

**Search Results Include:**
- Tables with generated CREATE TABLE statements (from table_columns)
- Stored Procedures with real DDL (from definitions)
- Views with real DDL (from definitions)

**Error Responses:**
```json
// 404 - No lineage data available
{
  "detail": "No lineage data available. Please upload data first."
}

// 500 - Search failed
{
  "detail": "Search failed: [error message]"
}
```

---

## 5. GET /api/ddl/{object_id}

Get complete DDL for a specific object (on-demand).

**Parameters:**
- `object_id` (required): Object ID from search results or lineage graph

**Request:**
```bash
curl "http://localhost:8000/api/ddl/1275862257"
```

**Response:**
```json
{
  "object_id": "1275862257",
  "object_name": "FeasibilityContacts",
  "schema_name": "CONSUMPTION_PRIMA",
  "object_type": "Table",
  "ddl": "CREATE TABLE [CONSUMPTION_PRIMA].[FeasibilityContacts] (\n    [RECORD_ID] int NULL,\n    [CONTACT_DATE] datetime NULL,\n    [CONTACT_ORIGINATOR] int NULL,\n    [CONTACT_ID] int NULL,\n    [CONTACT_TYPE] varchar(50) NULL,\n    [NOTES] varchar(MAX) NULL,\n    [CREATED_AT] datetime NULL\n);"
}
```

**Error Responses:**
```json
// 404 - Object not found
{
  "detail": "Object 1275862257 not found in unified_ddl view"
}

// 404 - No lineage data available
{
  "detail": "No lineage data available. Please upload data first."
}
```

---

## 6. GET /health

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

---

## 7. GET /api/jobs

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

---

## 8. DELETE /api/jobs/{job_id}

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

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "JobNotFound",
  "detail": "Job a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad request (missing files, invalid data)
- `404` - Job not found
- `500` - Internal server error
