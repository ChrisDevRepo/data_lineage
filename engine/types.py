"""
Type definitions for Data Lineage Visualizer

Provides TypedDict definitions for complex data structures used throughout
the application. This improves type safety and IDE autocomplete.

Version: 1.0.0
Date: 2025-11-14
"""

from typing import TypedDict, List, Optional, Dict, Any, Literal


# ============================================================================
# PARSING RESULTS
# ============================================================================

class ParseResult(TypedDict):
    """
    Result from parsing a single stored procedure, view, or function.

    Returned by QualityAwareParser.parse_object()
    """
    object_id: int
    object_name: str
    schema_name: str
    object_type: str
    inputs: List[int]  # List of input table object IDs
    outputs: List[int]  # List of output table object IDs
    confidence: int  # Confidence score: 0, 75, 85, or 100
    parse_time_ms: float
    sqlglot_success: bool
    regex_table_count: int
    sqlglot_table_count: int
    error_message: Optional[str]


class LineageMetadata(TypedDict):
    """
    Lineage metadata stored in database for an object.

    Stored in lineage_metadata table
    """
    object_id: int
    inputs: Optional[str]  # JSON string: ["schema.table1", "schema.table2"]
    outputs: Optional[str]  # JSON string: ["schema.output1"]
    confidence: int
    parse_timestamp: str
    sqlglot_success: bool
    regex_table_count: int
    sqlglot_table_count: int


# ============================================================================
# CATALOG & OBJECTS
# ============================================================================

class DatabaseObject(TypedDict):
    """
    Database object (table, view, stored procedure, function).

    From objects table
    """
    object_id: int
    object_name: str
    schema_name: str
    object_type: str  # "Table", "View", "Stored Procedure", "Function"
    create_date: Optional[str]
    modify_date: Optional[str]


class TableReference(TypedDict):
    """
    Fully-qualified table reference with resolution status.

    Used during parsing to track table references
    """
    schema: str
    table: str
    full_name: str  # "schema.table"
    object_id: Optional[int]  # None if not in catalog (phantom)
    is_phantom: bool


# ============================================================================
# WORKSPACE & STATISTICS
# ============================================================================

class WorkspaceStats(TypedDict):
    """
    DuckDB workspace statistics.

    Returned by DuckDBWorkspace.get_statistics()
    """
    total_objects: int
    total_stored_procedures: int
    total_tables: int
    total_views: int
    total_functions: int
    total_dependencies: int
    total_definitions: int
    query_log_count: int
    database_size_mb: float
    source_breakdown: Dict[str, int]  # {"sys.sql_expression_dependencies": 1234, "regex": 567}


class ParsingStatistics(TypedDict):
    """
    Statistics from parsing job.

    Returned by background job after completion
    """
    total_objects: int
    successful: int
    failed: int
    confidence_100: int
    confidence_85: int
    confidence_75: int
    confidence_0: int
    avg_parse_time_ms: float
    total_parse_time_s: float
    sqlglot_success_rate: float


# ============================================================================
# JOB STATUS
# ============================================================================

JobStatus = Literal["pending", "processing", "completed", "failed"]


class JobStatusData(TypedDict):
    """
    Background job status information.

    Returned by GET /api/job/{job_id}/status
    """
    job_id: str
    status: JobStatus
    progress: float  # 0.0 to 1.0
    message: str
    created_at: str
    updated_at: str
    error: Optional[str]
    result: Optional[Dict[str, Any]]


class ProcessingJobResult(TypedDict):
    """
    Result from completed processing job.

    Stored in job_status['result'] after successful completion
    """
    total_objects: int
    successful_parses: int
    failed_parses: int
    workspace_path: str
    processing_time_s: float
    statistics: ParsingStatistics


# ============================================================================
# API REQUESTS & RESPONSES
# ============================================================================

class UploadFilesRequest(TypedDict):
    """
    Request body for POST /api/upload endpoint.

    Files uploaded as multipart/form-data
    """
    objects_file: bytes  # Parquet file
    dependencies_file: Optional[bytes]  # Parquet file
    definitions_file: Optional[bytes]  # Parquet file
    query_logs_file: Optional[bytes]  # Parquet file


class LineageGraphNode(TypedDict):
    """
    Node in frontend lineage graph.

    Returned by GET /api/lineage endpoint
    """
    id: str  # "schema.table" or "schema.spName"
    label: str
    type: str  # "table", "view", "stored_procedure", "function"
    schema: str
    object_name: str
    confidence: Optional[int]  # Only for SPs/functions/views


class LineageGraphEdge(TypedDict):
    """
    Edge in frontend lineage graph.

    Connects source → target
    """
    id: str  # "source_id->target_id"
    source: str  # Node ID
    target: str  # Node ID
    label: str  # e.g., "reads", "writes"


class LineageGraphResponse(TypedDict):
    """
    Complete lineage graph response.

    Returned by GET /api/lineage
    """
    nodes: List[LineageGraphNode]
    edges: List[LineageGraphEdge]
    statistics: Dict[str, Any]


# ============================================================================
# RULE ENGINE
# ============================================================================

class RuleMatch(TypedDict):
    """
    Result from applying a SQL cleaning rule.

    Used for debugging rule execution
    """
    rule_name: str
    pattern: str
    matched: bool
    match_count: int
    original_sql: str
    cleaned_sql: str


# ============================================================================
# CONFIGURATION
# ============================================================================

class DialectConfig(TypedDict):
    """
    SQL dialect configuration.

    Loaded from engine/config/dialect_config.py
    """
    name: str  # "tsql", "bigquery", "snowflake", etc.
    sqlglot_dialect: str
    system_schemas: List[str]
    temp_table_prefix: str
    supports_cte: bool
    supports_merge: bool


# ============================================================================
# USER-VERIFIED TEST CASES
# ============================================================================

class UserVerifiedCase(TypedDict):
    """
    User-verified test case metadata.

    Loaded from tests/fixtures/user_verified_cases/*.yaml
    """
    sp_name: str
    reported_date: str
    reported_by: str
    issue: str
    root_cause: str
    fix_version: Optional[str]
    fix_description: Optional[str]
    expected_inputs: List[str]  # List of "schema.table"
    expected_outputs: List[str]
    expected_confidence: int
    do_not_change: Optional[List[str]]  # Patterns/rules that should not be removed


# ============================================================================
# HELPER TYPE ALIASES
# ============================================================================

ObjectID = int
ConfidenceScore = Literal[0, 75, 85, 100]
ObjectType = Literal["Table", "View", "Stored Procedure", "Function", "Phantom"]
