"""
Database schemas for sub_DL_OptimizeParsing evaluation infrastructure.

These schemas are used exclusively by the evaluation subagent and do NOT
affect production database (lineage_workspace.duckdb).

Author: Claude Code Agent
Date: 2025-11-02
Version: 1.0
"""

# Baseline database schema (frozen snapshots)
BASELINE_METADATA_SCHEMA = """
    CREATE TABLE IF NOT EXISTS baseline_metadata (
        baseline_name TEXT PRIMARY KEY,
        created_at TIMESTAMP,
        parser_version TEXT,
        total_objects INTEGER,
        description TEXT,
        source_workspace_path TEXT
    )
"""

BASELINE_OBJECTS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS baseline_objects (
        object_id INTEGER PRIMARY KEY,
        object_name TEXT NOT NULL,
        schema_name TEXT NOT NULL,
        object_type TEXT NOT NULL,
        ddl_text TEXT NOT NULL,
        ddl_hash TEXT NOT NULL,

        -- Ground truth dependencies (manually verified or high-confidence production)
        expected_inputs_json TEXT,   -- JSON array of object_ids: [123, 456, 789]
        expected_outputs_json TEXT,  -- JSON array of object_ids: [111, 222]

        -- Metadata
        verified BOOLEAN DEFAULT FALSE,
        notes TEXT,
        captured_at TIMESTAMP NOT NULL
    )
"""

BASELINE_INDEXES = """
    CREATE INDEX IF NOT EXISTS idx_baseline_ddl_hash ON baseline_objects(ddl_hash);
    CREATE INDEX IF NOT EXISTS idx_baseline_object_name ON baseline_objects(object_name);
    CREATE INDEX IF NOT EXISTS idx_baseline_schema_name ON baseline_objects(schema_name);
"""

# Evaluation database schema (historical tracking)
EVALUATION_RUNS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS evaluation_runs (
        run_id TEXT PRIMARY KEY,
        run_timestamp TIMESTAMP NOT NULL,
        baseline_name TEXT NOT NULL,
        mode TEXT NOT NULL,  -- 'full' or 'incremental'
        total_objects_evaluated INTEGER,

        -- Aggregate scores across all objects
        avg_regex_confidence REAL,
        avg_sqlglot_confidence REAL,
        avg_ai_confidence REAL,

        -- Summary counts
        objects_above_095 INTEGER,
        objects_below_095 INTEGER,
        objects_with_ddl_changes INTEGER,
        new_objects_added INTEGER,

        -- Progress tracking
        progress_to_goal_pct REAL,  -- (objects_above_095 / total) * 100

        -- Status
        completed BOOLEAN DEFAULT FALSE,
        duration_seconds INTEGER,
        report_path TEXT
    )
"""

EVALUATION_HISTORY_SCHEMA = """
    CREATE TABLE IF NOT EXISTS evaluation_history (
        run_id TEXT NOT NULL,
        object_id INTEGER NOT NULL,
        object_name TEXT NOT NULL,

        -- DDL tracking
        ddl_hash TEXT NOT NULL,
        ddl_changed BOOLEAN DEFAULT FALSE,

        -- Regex results
        regex_confidence REAL,
        regex_inputs_count INTEGER,
        regex_outputs_count INTEGER,
        regex_precision REAL,
        regex_recall REAL,
        regex_f1_score REAL,
        regex_execution_ms INTEGER,

        -- SQLGlot results
        sqlglot_confidence REAL,
        sqlglot_inputs_count INTEGER,
        sqlglot_outputs_count INTEGER,
        sqlglot_precision REAL,
        sqlglot_recall REAL,
        sqlglot_f1_score REAL,
        sqlglot_quality_match REAL,
        sqlglot_execution_ms INTEGER,

        -- AI results
        ai_confidence REAL,
        ai_inputs_count INTEGER,
        ai_outputs_count INTEGER,
        ai_precision REAL,
        ai_recall REAL,
        ai_f1_score REAL,
        ai_execution_ms INTEGER,
        ai_cost_estimate REAL,
        ai_validation_passed BOOLEAN,

        -- Best method determination
        best_method TEXT,  -- 'regex', 'sqlglot', or 'ai'
        best_confidence REAL,
        meets_goal BOOLEAN,  -- best_confidence >= 0.95

        -- Historical comparison (vs previous run)
        prev_run_id TEXT,
        sqlglot_confidence_delta REAL,
        ai_confidence_delta REAL,

        PRIMARY KEY (run_id, object_id)
    )
"""

EVALUATION_INDEXES = """
    CREATE INDEX IF NOT EXISTS idx_eval_run_timestamp ON evaluation_history(run_id);
    CREATE INDEX IF NOT EXISTS idx_eval_object ON evaluation_history(object_id);
    CREATE INDEX IF NOT EXISTS idx_eval_best_confidence ON evaluation_history(best_confidence);
    CREATE INDEX IF NOT EXISTS idx_eval_below_goal ON evaluation_history(meets_goal) WHERE meets_goal = FALSE;
    CREATE INDEX IF NOT EXISTS idx_eval_ddl_changed ON evaluation_history(ddl_changed) WHERE ddl_changed = TRUE;
"""

BASELINE_CHANGE_LOG_SCHEMA = """
    CREATE TABLE IF NOT EXISTS baseline_change_log (
        change_id INTEGER PRIMARY KEY,
        baseline_name TEXT NOT NULL,
        object_id INTEGER NOT NULL,
        change_type TEXT NOT NULL,  -- 'ddl_updated', 'new_object', 'removed_object'
        old_ddl_hash TEXT,
        new_ddl_hash TEXT,
        changed_at TIMESTAMP NOT NULL,
        detected_in_run TEXT NOT NULL  -- run_id that detected the change
    )
"""


def initialize_baseline_db(connection):
    """
    Initialize baseline database schema.

    Args:
        connection: DuckDB connection object

    Usage:
        import duckdb
        conn = duckdb.connect('evaluation_baselines/baseline_v3.7.0.duckdb')
        initialize_baseline_db(conn)
    """
    connection.execute(BASELINE_METADATA_SCHEMA)
    connection.execute(BASELINE_OBJECTS_SCHEMA)
    connection.execute(BASELINE_INDEXES)
    connection.execute(BASELINE_CHANGE_LOG_SCHEMA)
    print("✅ Baseline database schema initialized")


def initialize_evaluation_db(connection):
    """
    Initialize evaluation database schema.

    Args:
        connection: DuckDB connection object

    Usage:
        import duckdb
        conn = duckdb.connect('evaluation_baselines/current_evaluation.duckdb')
        initialize_evaluation_db(conn)
    """
    connection.execute(EVALUATION_RUNS_SCHEMA)
    connection.execute(EVALUATION_HISTORY_SCHEMA)
    connection.execute(EVALUATION_INDEXES)
    print("✅ Evaluation database schema initialized")
