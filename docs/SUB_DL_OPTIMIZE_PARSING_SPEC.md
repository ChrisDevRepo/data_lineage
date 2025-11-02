# Sub_DL_OptimizeParsing - Complete Specification

**Version:** 1.0
**Date:** 2025-11-02
**Status:** Approved - Ready for Implementation
**Author:** Claude Code Agent (Approved by User)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [One-Time Infrastructure Changes](#one-time-infrastructure-changes)
4. [Database Schema](#database-schema)
5. [File Structure](#file-structure)
6. [Subagent Implementation](#subagent-implementation)
7. [Command Interface](#command-interface)
8. [Workflows](#workflows)
9. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Purpose

**Sub_DL_OptimizeParsing** is an autonomous evaluation tool designed to track parsing quality improvements over time by:

1. Running all 3 parsing methods (regex, SQLGlot, AI) independently on each stored procedure
2. Comparing results against a frozen baseline with verified dependencies
3. Tracking confidence scores, precision, recall, and performance metrics
4. Detecting DDL changes and auto-updating baseline
5. Generating detailed reports to measure progress toward 95%+ confidence goal

### Scope Separation

This specification clearly separates three distinct components:

| Component | Scope | Changes Required |
|-----------|-------|------------------|
| **Production App** (`lineage_v3/`) | Parser + Visualizer | ❌ No changes (except minimal infrastructure additions) |
| **One-Time Infrastructure** | Supporting utilities | ⚠️ Add once (public wrappers for parsing methods) |
| **Subagent** (`evaluation/`) | Evaluation tool | ✅ New code (autonomous, does not modify app logic) |

### Key Principles

- **Autonomous**: Subagent operates independently from production parser
- **Non-invasive**: Does not modify app parsing logic or production database
- **Scalable**: Designed for 202 → 1000+ objects
- **Forensic**: Tracks full history for debugging and optimization decisions

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCTION APP (untouched)                  │
│  lineage_v3/                                                    │
│    ├── parsers/quality_aware_parser.py                         │
│    ├── parsers/ai_disambiguator.py                             │
│    ├── core/duckdb_workspace.py                                │
│    └── main.py                                                  │
│                                                                  │
│  Database: lineage_workspace.duckdb (production data)          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Imports parsing utilities
                              │ (via public wrapper methods)
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│              ONE-TIME INFRASTRUCTURE CHANGES                    │
│                                                                  │
│  File: lineage_v3/parsers/quality_aware_parser.py              │
│    ADD: extract_regex_dependencies()                            │
│    ADD: extract_sqlglot_dependencies()                          │
│                                                                  │
│  File: lineage_v3/parsers/ai_disambiguator.py                  │
│    ADD: run_standalone_ai_extraction()                          │
│                                                                  │
│  File: evaluation/schemas.py (NEW)                              │
│    Contains: DuckDB schema definitions for baseline/evaluation │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Uses utilities (hybrid approach)
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                    SUBAGENT (autonomous)                        │
│  .claude/commands/sub_DL_OptimizeParsing.md                    │
│                                                                  │
│  evaluation/                          (NEW - All subagent code) │
│    ├── __init__.py                                              │
│    ├── baseline_manager.py            # Baseline CRUD           │
│    ├── evaluation_runner.py           # Run all 3 methods       │
│    ├── score_calculator.py            # Precision/recall/F1     │
│    ├── report_generator.py            # JSON + console output   │
│    └── schemas.py                      # DuckDB schemas         │
│                                                                  │
│  Databases:                                                     │
│    - evaluation_baselines/baseline_v3.7.0.duckdb (read-only)   │
│    - evaluation_baselines/current_evaluation.duckdb (r/w)      │
│                                                                  │
│  Reports:                                                       │
│    - optimization_reports/run_YYYYMMDD_HHMMSS.json             │
└─────────────────────────────────────────────────────────────────┘
```

---

## One-Time Infrastructure Changes

### Change 1: Public Wrappers in Quality Aware Parser

**File:** `lineage_v3/parsers/quality_aware_parser.py`

**Location:** Add at end of `QualityAwareParser` class (after existing methods)

```python
# ============================================================================
# PUBLIC EVALUATION WRAPPERS (for sub_DL_OptimizeParsing subagent)
# ============================================================================
# These methods expose internal parsing logic for evaluation purposes.
# They do NOT affect production parsing behavior.

def extract_regex_dependencies(self, ddl: str) -> Dict[str, Any]:
    """
    Public wrapper for regex extraction (used by evaluation subagent).

    Runs regex pattern matching to extract table dependencies.
    This is the baseline method used for quality checking.

    Args:
        ddl: SQL DDL text

    Returns:
        {
            'sources': Set[str],           # Raw schema.table names found
            'targets': Set[str],           # Raw schema.table names found
            'sources_validated': Set[str], # After catalog validation
            'targets_validated': Set[str], # After catalog validation
            'sources_count': int,
            'targets_count': int
        }
    """
    # Use existing internal regex scan
    sources, targets = self._regex_scan(ddl)

    # Validate against catalog (same as production)
    sources_validated = self._validate_against_catalog(sources)
    targets_validated = self._validate_against_catalog(targets)

    return {
        'sources': sources,
        'targets': targets,
        'sources_validated': sources_validated,
        'targets_validated': targets_validated,
        'sources_count': len(sources_validated),
        'targets_count': len(targets_validated)
    }

def extract_sqlglot_dependencies(self, ddl: str) -> Dict[str, Any]:
    """
    Public wrapper for SQLGlot extraction (used by evaluation subagent).

    Runs SQLGlot AST parsing with preprocessing.
    Includes quality check metrics (comparison to regex baseline).

    Args:
        ddl: SQL DDL text

    Returns:
        {
            'sources': Set[str],
            'targets': Set[str],
            'sources_validated': Set[str],
            'targets_validated': Set[str],
            'sources_count': int,
            'targets_count': int,
            'quality_check': {
                'regex_sources': int,
                'regex_targets': int,
                'parser_sources': int,
                'parser_targets': int,
                'source_match': float,
                'target_match': float,
                'overall_match': float,
                'needs_ai': bool
            }
        }
    """
    # Preprocess DDL (same as production)
    cleaned_ddl = self._preprocess_ddl(ddl)

    # Parse with SQLGlot
    sources, targets = self._sqlglot_parse(cleaned_ddl, ddl)

    # Validate against catalog
    sources_validated = self._validate_against_catalog(sources)
    targets_validated = self._validate_against_catalog(targets)

    # Run quality check (compare to regex baseline)
    regex_result = self.extract_regex_dependencies(ddl)
    quality = self._calculate_quality(
        len(regex_result['sources_validated']),
        len(regex_result['targets_validated']),
        len(sources_validated),
        len(targets_validated)
    )

    return {
        'sources': sources,
        'targets': targets,
        'sources_validated': sources_validated,
        'targets_validated': targets_validated,
        'sources_count': len(sources_validated),
        'targets_count': len(targets_validated),
        'quality_check': quality
    }
```

**Impact:**
- ✅ Minimal change (2 new methods)
- ✅ No modification to existing parsing logic
- ✅ No impact on production behavior
- ✅ Enables subagent to use proven parsing utilities

---

### Change 2: Standalone AI Extraction

**File:** `lineage_v3/parsers/ai_disambiguator.py`

**Location:** Add as new module-level function (after `AIDisambiguator` class)

```python
# ============================================================================
# STANDALONE AI EXTRACTION (for sub_DL_OptimizeParsing subagent)
# ============================================================================

def run_standalone_ai_extraction(
    ddl: str,
    workspace: DuckDBWorkspace,
    object_id: int,
    sp_name: str
) -> Dict[str, Any]:
    """
    Standalone AI extraction for evaluation purposes.

    Runs AI disambiguation independently without triggering conditions
    (confidence threshold, ambiguous references, etc.). Used by evaluation
    subagent to test AI parsing capability on all objects.

    Args:
        ddl: SQL DDL text
        workspace: DuckDB workspace for catalog lookups
        object_id: Object ID being parsed
        sp_name: Stored procedure name (schema.name)

    Returns:
        {
            'sources': List[int],        # Input object_ids
            'targets': List[int],        # Output object_ids
            'confidence': float,         # 0.85-0.95
            'resolved_tables': List[str], # Qualified table names
            'validation_passed': bool,
            'execution_time_ms': int,
            'cost_estimate_usd': float   # Optional: API cost
        }
    """
    import time
    from lineage_v3.parsers.quality_aware_parser import QualityAwareParser

    start_time = time.time()

    try:
        # Initialize disambiguator
        disambiguator = AIDisambiguator(workspace)

        # Create parser instance for reference extraction
        parser = QualityAwareParser(workspace)

        # Extract ambiguous references from DDL
        # (Use parser's internal method or regex scan)
        regex_sources, regex_targets = parser._regex_scan(ddl)

        # Find first ambiguous reference (for testing)
        # In evaluation mode, we attempt AI even if no ambiguity
        reference = None
        candidates = []

        # Try to find unqualified table names
        import re
        unqualified_pattern = r'\b(?:FROM|JOIN|INSERT\s+INTO|UPDATE)\s+(\w+)\b'
        matches = re.findall(unqualified_pattern, ddl, re.IGNORECASE)

        for table_name in set(matches):
            if not table_name.startswith('#') and not table_name.startswith('@'):
                # Find candidates from catalog
                query = """
                    SELECT schema_name, object_name
                    FROM objects
                    WHERE LOWER(object_name) = LOWER(?)
                      AND object_type = 'Table'
                """
                results = workspace.connection.execute(query, [table_name]).fetchall()

                if len(results) > 1:
                    reference = table_name
                    candidates = [f"{schema}.{name}" for schema, name in results]
                    break

        # If no ambiguous reference found, still try AI with full DDL
        if not reference:
            # Use first regex source as reference
            if regex_sources:
                reference = list(regex_sources)[0].split('.')[-1]
                candidates = list(regex_sources)

        # Build parser result for validation
        parser_result = {
            'quality': {
                'regex_sources': len(regex_sources),
                'regex_targets': len(regex_targets),
                'parser_sources': 0,  # Not relevant for AI-only eval
                'parser_targets': 0
            }
        }

        # Run AI disambiguation
        if reference and candidates:
            ai_result = disambiguator.disambiguate(
                reference=reference,
                candidates=candidates,
                sql_context=ddl,
                parser_result=parser_result,
                sp_name=sp_name
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            if ai_result and ai_result.is_valid:
                return {
                    'sources': ai_result.sources,
                    'targets': ai_result.targets,
                    'confidence': ai_result.confidence,
                    'resolved_tables': [ai_result.resolved_table],
                    'validation_passed': True,
                    'execution_time_ms': execution_time_ms,
                    'cost_estimate_usd': 0.001  # Placeholder: ~$0.001 per call
                }
            else:
                return {
                    'sources': [],
                    'targets': [],
                    'confidence': 0.5,
                    'resolved_tables': [],
                    'validation_passed': False,
                    'execution_time_ms': execution_time_ms,
                    'cost_estimate_usd': 0.001
                }
        else:
            # No candidates found - return empty result
            return {
                'sources': [],
                'targets': [],
                'confidence': 0.5,
                'resolved_tables': [],
                'validation_passed': False,
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'cost_estimate_usd': 0.0
            }

    except Exception as e:
        logger.error(f"AI extraction failed for {sp_name}: {e}")
        return {
            'sources': [],
            'targets': [],
            'confidence': 0.0,
            'resolved_tables': [],
            'validation_passed': False,
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'cost_estimate_usd': 0.0,
            'error': str(e)
        }
```

**Impact:**
- ✅ New standalone function (no modification to existing class)
- ✅ Can test AI independently of production triggers
- ✅ Enables cost tracking for AI usage

---

### Change 3: Evaluation Schemas

**File:** `evaluation/schemas.py` (NEW)

```python
"""
Database schemas for sub_DL_OptimizeParsing evaluation infrastructure.

These schemas are used exclusively by the evaluation subagent and do NOT
affect production database (lineage_workspace.duckdb).
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
        change_id INTEGER PRIMARY KEY AUTOINCREMENT,
        baseline_name TEXT NOT NULL,
        object_id INTEGER NOT NULL,
        change_type TEXT NOT NULL,  -- 'ddl_updated', 'new_object', 'removed_object'
        old_ddl_hash TEXT,
        new_ddl_hash TEXT,
        changed_at TIMESTAMP NOT NULL,
        detected_in_run TEXT NOT NULL  -- run_id that detected the change
    )
"""

# Helper function to initialize databases
def initialize_baseline_db(connection):
    """Initialize baseline database schema."""
    connection.execute(BASELINE_METADATA_SCHEMA)
    connection.execute(BASELINE_OBJECTS_SCHEMA)
    connection.execute(BASELINE_INDEXES)
    connection.execute(BASELINE_CHANGE_LOG_SCHEMA)

def initialize_evaluation_db(connection):
    """Initialize evaluation database schema."""
    connection.execute(EVALUATION_RUNS_SCHEMA)
    connection.execute(EVALUATION_HISTORY_SCHEMA)
    connection.execute(EVALUATION_INDEXES)
```

**Impact:**
- ✅ New file (no modification to existing code)
- ✅ Schemas isolated from production database
- ✅ Provides structure for baseline and evaluation tracking

---

## Database Schema

### Baseline Database (`baseline_v3.7.0.duckdb`)

**Purpose:** Frozen snapshot of DDL + verified dependencies

#### Table: `baseline_metadata`
```sql
CREATE TABLE baseline_metadata (
    baseline_name TEXT PRIMARY KEY,      -- 'baseline_v3.7.0'
    created_at TIMESTAMP,                -- When baseline was captured
    parser_version TEXT,                 -- 'v3.7.0'
    total_objects INTEGER,               -- 202
    description TEXT,                    -- User description
    source_workspace_path TEXT           -- Path to production DB
);
```

#### Table: `baseline_objects`
```sql
CREATE TABLE baseline_objects (
    object_id INTEGER PRIMARY KEY,
    object_name TEXT NOT NULL,
    schema_name TEXT NOT NULL,
    object_type TEXT NOT NULL,           -- 'Stored Procedure'
    ddl_text TEXT NOT NULL,              -- Full DDL
    ddl_hash TEXT NOT NULL,              -- SHA256 hash for change detection

    -- Ground truth (verified dependencies)
    expected_inputs_json TEXT,           -- '[123, 456, 789]'
    expected_outputs_json TEXT,          -- '[111, 222]'

    -- Metadata
    verified BOOLEAN DEFAULT FALSE,      -- Manually verified?
    notes TEXT,                          -- Special notes
    captured_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_baseline_ddl_hash ON baseline_objects(ddl_hash);
CREATE INDEX idx_baseline_object_name ON baseline_objects(object_name);
```

**Example Row:**
```json
{
  "object_id": 12345,
  "object_name": "spLoadDimAccount",
  "schema_name": "dbo",
  "object_type": "Stored Procedure",
  "ddl_text": "CREATE PROCEDURE [dbo].[spLoadDimAccount] AS BEGIN...",
  "ddl_hash": "a3f2b1c4d5e6...",
  "expected_inputs_json": "[67890, 11111]",
  "expected_outputs_json": "[22222]",
  "verified": true,
  "notes": "High-confidence production run",
  "captured_at": "2025-10-28T10:30:00Z"
}
```

---

### Evaluation Database (`current_evaluation.duckdb`)

**Purpose:** Historical tracking of evaluation runs

#### Table: `evaluation_runs`
```sql
CREATE TABLE evaluation_runs (
    run_id TEXT PRIMARY KEY,             -- 'run_20251102_143022'
    run_timestamp TIMESTAMP NOT NULL,
    baseline_name TEXT NOT NULL,         -- 'baseline_v3.7.0'
    mode TEXT NOT NULL,                  -- 'full' or 'incremental'
    total_objects_evaluated INTEGER,

    -- Aggregate scores
    avg_regex_confidence REAL,
    avg_sqlglot_confidence REAL,
    avg_ai_confidence REAL,

    -- Summary counts
    objects_above_095 INTEGER,
    objects_below_095 INTEGER,
    objects_with_ddl_changes INTEGER,
    new_objects_added INTEGER,

    -- Progress
    progress_to_goal_pct REAL,

    -- Status
    completed BOOLEAN DEFAULT FALSE,
    duration_seconds INTEGER,
    report_path TEXT
);
```

#### Table: `evaluation_history`
```sql
CREATE TABLE evaluation_history (
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

    -- Best method
    best_method TEXT,
    best_confidence REAL,
    meets_goal BOOLEAN,                  -- >= 0.95

    -- Historical comparison
    prev_run_id TEXT,
    sqlglot_confidence_delta REAL,
    ai_confidence_delta REAL,

    PRIMARY KEY (run_id, object_id)
);

CREATE INDEX idx_eval_below_goal ON evaluation_history(meets_goal) WHERE meets_goal = FALSE;
```

#### Table: `baseline_change_log`
```sql
CREATE TABLE baseline_change_log (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    baseline_name TEXT NOT NULL,
    object_id INTEGER NOT NULL,
    change_type TEXT NOT NULL,           -- 'ddl_updated', 'new_object'
    old_ddl_hash TEXT,
    new_ddl_hash TEXT,
    changed_at TIMESTAMP NOT NULL,
    detected_in_run TEXT NOT NULL
);
```

---

## File Structure

```

├── evaluation/                          # NEW - Subagent code
│   ├── __init__.py                      # Package init
│   ├── baseline_manager.py              # Baseline CRUD operations
│   ├── evaluation_runner.py             # Core evaluation logic
│   ├── score_calculator.py              # Metrics computation
│   ├── report_generator.py              # Report formatting
│   └── schemas.py                       # DuckDB schemas
│
├── evaluation_baselines/                # NEW - Database storage
│   ├── baseline_v3.7.0.duckdb          # Frozen baseline
│   ├── current_evaluation.duckdb        # Evaluation history
│   └── README.md                        # Baseline documentation
│
├── optimization_reports/                # NEW - JSON reports
│   ├── run_20251102_143022.json        # Full evaluation report
│   ├── run_20251103_091544.json        # Next run
│   └── latest.json                      # Symlink to latest
│
├── .claude/commands/                    # Slash command
│   └── sub_DL_OptimizeParsing.md       # NEW - Subagent entry point
│
├── docs/                                # Documentation
│   └── SUB_DL_OPTIMIZE_PARSING_SPEC.md # NEW - This specification
│
├── lineage_v3/                          # MODIFIED (minimal)
│   ├── parsers/
│   │   ├── quality_aware_parser.py      # ADD: 2 public wrapper methods
│   │   └── ai_disambiguator.py          # ADD: 1 standalone function
│   └── ...
│
└── (existing files unchanged)
```

---

## Subagent Implementation

### Module 1: `baseline_manager.py`

**Responsibilities:**
- Create baseline snapshots from production workspace
- Load baseline objects for evaluation
- Update baseline when DDL changes detected
- Log baseline changes

**Key Functions:**
```python
class BaselineManager:
    def __init__(self, baseline_dir: Path):
        """Initialize baseline manager"""

    def create_baseline(self, name: str, workspace_path: Path) -> int:
        """
        Create new baseline from production workspace.

        Returns:
            Number of objects captured
        """

    def load_baseline(self, name: str) -> Dict[int, Dict]:
        """
        Load baseline objects.

        Returns:
            Dict mapping object_id -> {ddl, expected_inputs, expected_outputs}
        """

    def update_object(self, baseline_name: str, object_id: int,
                     new_ddl: str, run_id: str) -> None:
        """
        Update baseline object DDL (auto-update on change detection).
        Logs change to baseline_change_log.
        """

    def add_new_object(self, baseline_name: str, object_id: int,
                      object_data: Dict, run_id: str) -> None:
        """
        Add new object to baseline (auto-add when discovered).
        """
```

---

### Module 2: `evaluation_runner.py`

**Responsibilities:**
- Orchestrate evaluation runs
- Call all 3 parsing methods for each object
- Detect DDL changes
- Store results in evaluation database

**Key Functions:**
```python
class EvaluationRunner:
    def __init__(self, baseline_manager: BaselineManager,
                 workspace_path: Path):
        """Initialize runner with baseline and production workspace"""

    def run_full_evaluation(self, baseline_name: str) -> str:
        """
        Run full evaluation (all objects, all methods).

        Returns:
            run_id
        """

    def run_incremental_evaluation(self, baseline_name: str) -> str:
        """
        Run incremental evaluation (only changed DDLs).

        Returns:
            run_id
        """

    def evaluate_object(self, object_id: int, ddl: str,
                       expected_inputs: List[int],
                       expected_outputs: List[int]) -> Dict:
        """
        Evaluate single object with all 3 methods.

        Returns:
            {
                'regex_result': {...},
                'sqlglot_result': {...},
                'ai_result': {...},
                'best_method': 'sqlglot',
                'best_confidence': 0.92
            }
        """
```

---

### Module 3: `score_calculator.py`

**Responsibilities:**
- Calculate precision, recall, F1 scores
- Compare method results to expected dependencies
- Determine best method for each object

**Key Functions:**
```python
class ScoreCalculator:
    @staticmethod
    def calculate_precision_recall(found_ids: List[int],
                                   expected_ids: List[int]) -> Tuple[float, float, float]:
        """
        Calculate precision, recall, F1.

        Precision = True Positives / (True Positives + False Positives)
        Recall = True Positives / (True Positives + False Negatives)
        F1 = 2 * (Precision * Recall) / (Precision + Recall)

        Returns:
            (precision, recall, f1_score)
        """

    @staticmethod
    def calculate_confidence_score(precision: float, recall: float) -> float:
        """
        Calculate confidence score (F1-based).

        Returns:
            Confidence score between 0.0 and 1.0
        """

    @staticmethod
    def determine_best_method(regex_conf: float, sqlglot_conf: float,
                             ai_conf: float) -> Tuple[str, float]:
        """
        Determine which method gave best confidence.

        Returns:
            (method_name, confidence_score)
        """
```

---

### Module 4: `report_generator.py`

**Responsibilities:**
- Generate console summary
- Generate detailed JSON report
- Format tables and progress bars

**Key Functions:**
```python
class ReportGenerator:
    def __init__(self, evaluation_db_path: Path):
        """Initialize with evaluation database"""

    def generate_console_summary(self, run_id: str) -> str:
        """
        Generate formatted console output.

        Returns:
            Multi-line string with summary, tables, progress bars
        """

    def generate_json_report(self, run_id: str, output_path: Path) -> None:
        """
        Generate detailed JSON report.

        Includes:
            - Summary statistics
            - Method comparison
            - Objects below 0.95 (full details)
            - Baseline changes
            - Optional: Full results for all objects
        """

    def compare_runs(self, run_id_1: str, run_id_2: str) -> str:
        """
        Compare two evaluation runs.

        Returns:
            Formatted comparison report
        """
```

---

## Command Interface

### Slash Command: `/sub_DL_OptimizeParsing`

**File:** `.claude/commands/sub_DL_OptimizeParsing.md`

```markdown
# sub_DL_OptimizeParsing

Autonomous parsing evaluation and optimization tracking tool.

## Description

Evaluates parsing quality by running all 3 methods (regex, SQLGlot, AI) on stored procedures and comparing results against a frozen baseline with verified dependencies. Tracks confidence scores, precision, recall, and performance metrics over time.

## Available Commands

### 1. Initialize Baseline
Create a new baseline snapshot from production workspace.

**Syntax:**
```bash
/sub_DL_OptimizeParsing init --name <baseline_name>
```

**Example:**
```bash
/sub_DL_OptimizeParsing init --name baseline_v3.7.0
```

**Output:**
- Creates `evaluation_baselines/baseline_v3.7.0.duckdb`
- Exports all SP DDLs + current high-confidence dependencies
- Prints summary: "✅ Baseline baseline_v3.7.0 created with 202 objects"

---

### 2. Run Full Evaluation
Evaluate all objects with all methods.

**Syntax:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline <baseline_name>
```

**Example:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_v3.7.0
```

**Process:**
1. Load baseline (202 objects)
2. For each object:
   - Check DDL hash (detect changes)
   - Run regex extraction
   - Run SQLGlot extraction
   - Run AI extraction
   - Calculate precision/recall vs expected dependencies
3. Store results in `current_evaluation.duckdb`
4. Auto-update baseline if DDL changed (log to change_log)
5. Generate report (console + JSON)

**Output:**
- Console summary with progress bars, aggregate stats
- JSON report saved to `optimization_reports/run_YYYYMMDD_HHMMSS.json`

---

### 3. Run Incremental Evaluation
Evaluate only objects with DDL changes since last run.

**Syntax:**
```bash
/sub_DL_OptimizeParsing run --mode incremental --baseline <baseline_name>
```

**Example:**
```bash
/sub_DL_OptimizeParsing run --mode incremental --baseline baseline_v3.7.0
```

**Process:**
1. Load last evaluation run
2. Compare DDL hashes
3. Evaluate only changed objects
4. Much faster for quick validation after parser improvements

---

### 4. View Latest Report
Display summary of most recent evaluation run.

**Syntax:**
```bash
/sub_DL_OptimizeParsing report --latest
```

**Output:**
- Console summary from latest run
- Path to detailed JSON report

---

### 5. Compare Runs
Compare two evaluation runs.

**Syntax:**
```bash
/sub_DL_OptimizeParsing compare --run1 <run_id_1> --run2 <run_id_2>
```

**Example:**
```bash
/sub_DL_OptimizeParsing compare --run1 run_20251101_120000 --run2 run_20251102_143022
```

**Output:**
- Score deltas for each method
- Objects that improved/regressed
- Method-by-method comparison

---

## Usage Workflow

### Scenario 1: First Time Setup
```bash
# 1. Create initial baseline from production data
/sub_DL_OptimizeParsing init --name baseline_v3.7.0

# 2. Run first evaluation to establish scores
/sub_DL_OptimizeParsing run --mode full --baseline baseline_v3.7.0

# 3. Review baseline report
/sub_DL_OptimizeParsing report --latest
```

### Scenario 2: Testing Parser Improvement
```bash
# (User modifies quality_aware_parser.py - e.g., improve CTE preprocessing)

# 1. Run incremental evaluation (faster)
/sub_DL_OptimizeParsing run --mode incremental --baseline baseline_v3.7.0

# 2. Compare to previous run
/sub_DL_OptimizeParsing compare --run1 <prev_run_id> --run2 <new_run_id>

# 3. If improvements confirmed, commit parser changes
```

### Scenario 3: New Data Snapshot
```bash
# (New Parquet files with added/modified SPs)

# 1. Run full evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_v3.7.0

# 2. Subagent auto-detects:
#    - DDL changes (auto-updates baseline + logs)
#    - New objects (auto-adds to baseline)

# 3. Review change log
# Query: SELECT * FROM baseline_change_log ORDER BY changed_at DESC LIMIT 10;
```

---

## Notes

- **Autonomous Operation**: Subagent does not modify production parser code
- **Auto-Update**: DDL changes are auto-updated in baseline with full logging
- **Cost Tracking**: AI method includes execution time and cost estimates
- **Scalability**: Designed for 202 → 1000+ objects
- **Goal Tracking**: Progress toward 95%+ confidence goal
```

---

## Workflows

### Workflow 1: Create Initial Baseline

```
User Command:
  /sub_DL_OptimizeParsing init --name baseline_v3.7.0

┌─────────────────────────────────────────────────────────────┐
│ Step 1: Connect to Production Workspace                    │
│   - Open lineage_workspace.duckdb                           │
│   - Read objects, definitions tables                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Create Baseline Database                           │
│   - Create evaluation_baselines/baseline_v3.7.0.duckdb     │
│   - Initialize schemas (baseline_metadata, baseline_objects)│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Export Objects                                     │
│   For each Stored Procedure:                               │
│     - object_id, object_name, schema_name                   │
│     - DDL text from definitions table                       │
│     - Calculate SHA256 hash of DDL                          │
│     - Extract expected dependencies from lineage_metadata   │
│       (use high-confidence production results as ground truth)│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Store Baseline                                     │
│   INSERT INTO baseline_metadata:                            │
│     - baseline_name = 'baseline_v3.7.0'                     │
│     - created_at = NOW()                                    │
│     - parser_version = 'v3.7.0'                             │
│     - total_objects = 202                                   │
│                                                              │
│   INSERT INTO baseline_objects (202 rows):                  │
│     - object_id, object_name, ddl_text, ddl_hash            │
│     - expected_inputs_json, expected_outputs_json           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Output:                                                     │
│   ✅ Baseline baseline_v3.7.0 created with 202 objects      │
│   📁 Location: evaluation_baselines/baseline_v3.7.0.duckdb  │
│   📊 Average confidence: 0.800 (from production run)        │
└─────────────────────────────────────────────────────────────┘
```

---

### Workflow 2: Run Full Evaluation

```
User Command:
  /sub_DL_OptimizeParsing run --mode full --baseline baseline_v3.7.0

┌─────────────────────────────────────────────────────────────┐
│ Step 1: Load Baseline                                      │
│   - Open baseline_v3.7.0.duckdb (read-only)                │
│   - Load 202 objects with expected dependencies             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Initialize Evaluation Run                          │
│   - Generate run_id = 'run_20251102_143022'                │
│   - Create row in evaluation_runs table                     │
│   - Open production workspace (for catalog validation)      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Evaluate Each Object (Loop: 202 iterations)        │
│                                                              │
│   For object_id in baseline_objects:                        │
│                                                              │
│     3a. Check DDL Hash                                      │
│         - Compare baseline DDL hash to current production   │
│         - If different: Log to baseline_change_log          │
│                        Auto-update baseline DDL             │
│                                                              │
│     3b. Run Regex Extraction                                │
│         - Import QualityAwareParser                         │
│         - parser.extract_regex_dependencies(ddl)            │
│         - Resolve table names to object_ids                 │
│         - Calculate precision/recall vs expected_inputs/outputs│
│         - Record execution time                             │
│                                                              │
│     3c. Run SQLGlot Extraction                              │
│         - parser.extract_sqlglot_dependencies(ddl)          │
│         - Resolve table names to object_ids                 │
│         - Calculate precision/recall                        │
│         - Record quality_check metrics                      │
│         - Record execution time                             │
│                                                              │
│     3d. Run AI Extraction                                   │
│         - run_standalone_ai_extraction(ddl, workspace, ...)│
│         - Calculate precision/recall                        │
│         - Record execution time + cost estimate             │
│                                                              │
│     3e. Determine Best Method                               │
│         - Compare confidence scores                         │
│         - best_method = argmax(regex, sqlglot, ai)          │
│         - meets_goal = (best_confidence >= 0.95)            │
│                                                              │
│     3f. Store Results                                       │
│         - INSERT INTO evaluation_history                    │
│         - All metrics (precision, recall, F1, execution time)│
│                                                              │
│     3g. Progress Indicator                                  │
│         - Print: "Processing 45/202 (22.3%)..."             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Calculate Aggregates                               │
│   - avg_regex_confidence                                    │
│   - avg_sqlglot_confidence                                  │
│   - avg_ai_confidence                                       │
│   - objects_above_095                                       │
│   - objects_below_095                                       │
│   - progress_to_goal_pct = (objects_above_095 / 202) * 100 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Update Run Metadata                                │
│   - UPDATE evaluation_runs SET:                             │
│       completed = TRUE                                      │
│       total_objects_evaluated = 202                         │
│       avg_*_confidence = ...                                │
│       duration_seconds = 223                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Generate Reports                                   │
│   - Console summary (see output format in spec)            │
│   - JSON report → optimization_reports/run_20251102_143022.json│
│   - Symlink latest.json → run_20251102_143022.json         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Output:                                                     │
│   ✅ EVALUATION COMPLETE                                    │
│   📊 150/202 objects above 0.95 confidence (74.3%)          │
│   📈 SQLGlot best for 150 objects, AI best for 52           │
│   📁 Report: optimization_reports/run_20251102_143022.json  │
└─────────────────────────────────────────────────────────────┘
```

---

### Workflow 3: Incremental Evaluation (Fast Path)

```
User Command:
  /sub_DL_OptimizeParsing run --mode incremental --baseline baseline_v3.7.0

┌─────────────────────────────────────────────────────────────┐
│ Step 1: Load Last Evaluation Run                           │
│   - Query: SELECT MAX(run_timestamp) FROM evaluation_runs  │
│   - Load evaluation_history for last run                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Detect DDL Changes                                 │
│   - Compare DDL hashes from baseline to production          │
│   - Identify changed objects only                           │
│   - Example: 3 objects changed, 199 unchanged               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Evaluate Changed Objects Only                      │
│   - Run same evaluation as full mode                        │
│   - But only for 3 objects (not 202)                        │
│   - Much faster: 10 seconds vs 4 minutes                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Copy Unchanged Results                             │
│   - For 199 unchanged objects:                              │
│     - Copy results from last evaluation run                 │
│     - Update run_id to current run                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Output:                                                     │
│   ✅ INCREMENTAL EVALUATION COMPLETE                        │
│   📊 3 objects re-evaluated, 199 copied from last run       │
│   ⚡ Duration: 10 seconds (vs 4 minutes for full)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### Phase 1: Infrastructure (One-Time Changes)

- [ ] **1.1** Add public wrappers to `quality_aware_parser.py`
  - [ ] `extract_regex_dependencies()` method
  - [ ] `extract_sqlglot_dependencies()` method
  - [ ] Test: Verify methods return expected structure

- [ ] **1.2** Add standalone AI function to `ai_disambiguator.py`
  - [ ] `run_standalone_ai_extraction()` function
  - [ ] Test: Verify AI can run independently

- [ ] **1.3** Create `evaluation/schemas.py`
  - [ ] Define all schema constants
  - [ ] Add `initialize_baseline_db()` helper
  - [ ] Add `initialize_evaluation_db()` helper

- [ ] **1.4** Create directory structure
  - [ ] `mkdir evaluation/`
  - [ ] `mkdir evaluation_baselines/`
  - [ ] `mkdir optimization_reports/`

---

### Phase 2: Core Modules

- [ ] **2.1** Implement `evaluation/baseline_manager.py`
  - [ ] `BaselineManager` class
  - [ ] `create_baseline()` method
  - [ ] `load_baseline()` method
  - [ ] `update_object()` method
  - [ ] `add_new_object()` method
  - [ ] Test: Create baseline from test workspace

- [ ] **2.2** Implement `evaluation/score_calculator.py`
  - [ ] `ScoreCalculator` class
  - [ ] `calculate_precision_recall()` method
  - [ ] `calculate_confidence_score()` method
  - [ ] `determine_best_method()` method
  - [ ] Test: Verify metrics match expected values

- [ ] **2.3** Implement `evaluation/evaluation_runner.py`
  - [ ] `EvaluationRunner` class
  - [ ] `run_full_evaluation()` method
  - [ ] `run_incremental_evaluation()` method
  - [ ] `evaluate_object()` method (core logic)
  - [ ] Progress indicators (1/202, 2/202, ...)
  - [ ] DDL change detection
  - [ ] Test: Run on 5 test objects

- [ ] **2.4** Implement `evaluation/report_generator.py`
  - [ ] `ReportGenerator` class
  - [ ] `generate_console_summary()` method
  - [ ] `generate_json_report()` method
  - [ ] `compare_runs()` method
  - [ ] Test: Verify JSON structure matches spec

---

### Phase 3: Slash Command Interface

- [ ] **3.1** Create `.claude/commands/sub_DL_OptimizeParsing.md`
  - [ ] Write command documentation
  - [ ] Define argument parsing
  - [ ] Wire up to evaluation modules

- [ ] **3.2** Implement command handlers
  - [ ] `init` command → `baseline_manager.create_baseline()`
  - [ ] `run` command → `evaluation_runner.run_*_evaluation()`
  - [ ] `report` command → `report_generator.generate_*_summary()`
  - [ ] `compare` command → `report_generator.compare_runs()`

- [ ] **3.3** Error handling
  - [ ] Baseline not found
  - [ ] Production workspace not accessible
  - [ ] Invalid run_id

---

### Phase 4: Testing & Validation

- [ ] **4.1** Integration tests
  - [ ] Create test baseline with 10 objects
  - [ ] Run full evaluation
  - [ ] Verify all 3 methods execute
  - [ ] Verify metrics calculated correctly
  - [ ] Verify JSON report generated

- [ ] **4.2** Performance tests
  - [ ] Benchmark full evaluation (202 objects)
  - [ ] Benchmark incremental evaluation (3 changed objects)
  - [ ] Verify execution time acceptable

- [ ] **4.3** Edge case tests
  - [ ] DDL change detection
  - [ ] New object auto-add
  - [ ] Empty baseline
  - [ ] AI failure handling

---

### Phase 5: Documentation

- [ ] **5.1** Update `CLAUDE.md`
  - [ ] Add subagent description
  - [ ] Add usage examples

- [ ] **5.2** Create `evaluation_baselines/README.md`
  - [ ] Document baseline versioning strategy
  - [ ] Document change log usage

- [ ] **5.3** Update `.vscode/mcp.json` (if needed)
  - [ ] Register subagent

---

## Success Criteria

The implementation is complete and successful when:

1. ✅ **Infrastructure Changes Applied**
   - Public wrappers added to `quality_aware_parser.py`
   - Standalone AI function added to `ai_disambiguator.py`
   - No impact on production parser behavior

2. ✅ **Baseline Management Works**
   - Can create baseline from production workspace
   - Baseline contains DDL + expected dependencies
   - DDL change detection functional
   - Auto-update with logging functional

3. ✅ **Evaluation Runs Successfully**
   - All 3 methods (regex, SQLGlot, AI) execute for each object
   - Precision, recall, F1 calculated correctly
   - Results stored in `evaluation_history`
   - Both full and incremental modes work

4. ✅ **Reports Generated Correctly**
   - Console summary displays formatted output
   - JSON report contains all required fields
   - Objects below 0.95 listed with details
   - Baseline changes logged

5. ✅ **Scalability Validated**
   - Full evaluation completes in <5 minutes for 202 objects
   - Incremental evaluation <30 seconds for typical changes
   - Database queries optimized with indexes

6. ✅ **User Workflow Validated**
   - User can create baseline with single command
   - User can run evaluation with single command
   - User can compare runs to measure improvement
   - User can track progress toward 95% goal

---

## Next Steps After Implementation

1. **Initial Baseline**: Create `baseline_v3.7.0` from current production data
2. **Baseline Evaluation**: Run first evaluation to establish baseline scores
3. **Parser Improvements**: Make targeted improvements to SQLGlot preprocessing
4. **Re-Evaluation**: Run incremental evaluation to measure improvement
5. **Iteration**: Repeat steps 3-4 until 95%+ goal reached

---

**End of Specification**

**Approval Status:** ✅ Approved by User (2025-11-02)
**Ready for Implementation:** Yes
**Estimated Implementation Time:** 8-12 hours
