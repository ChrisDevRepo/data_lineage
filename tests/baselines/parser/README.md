# Parser Evaluation Baselines

**Location:** `tests/baselines/parser/`
**Purpose:** Store baseline snapshots and evaluation history for the `sub_DL_OptimizeParsing` subagent

---

## Directory Structure

```
tests/baselines/parser/
├── baseline_v4.2.0.duckdb          # Current production baseline
├── baseline_v3.8.0.duckdb          # Previous version baseline
├── current_evaluation.duckdb        # Evaluation run history
└── README.md                        # This file
```

---

## Baseline Database Files

Each baseline is a frozen snapshot of:
- **DDL text** for all Stored Procedures (SHA256 hashed for change detection)
- **Expected dependencies** (inputs/outputs from high-confidence production run)

### Naming Convention

`baseline_<parser_version>.duckdb`

Examples:
- `baseline_v3.7.0.duckdb` - Captured on 2025-10-28 with parser v3.7.0
- `baseline_v3.8.0.duckdb` - Captured after TRUNCATE support added

### When to Create a New Baseline

**Option 1: After Major Parser Changes**
```bash
# After implementing significant parser improvements
/sub_DL_OptimizeParsing init --name baseline_v3.8.0
```

**Option 2: After Data Refresh**
```bash
# After new Parquet snapshot with many new/changed SPs
/sub_DL_OptimizeParsing init --name baseline_20251102
```

**Option 3: Before Major Refactoring**
```bash
# Capture current state before risky changes
/sub_DL_OptimizeParsing init --name baseline_pre_refactor
```

---

## Baseline Schema

### Table: `baseline_metadata`
```sql
CREATE TABLE baseline_metadata (
    baseline_name TEXT PRIMARY KEY,      -- 'baseline_v3.7.0'
    created_at TIMESTAMP,                -- 2025-10-28 10:30:00
    parser_version TEXT,                 -- 'v3.7.0'
    total_objects INTEGER,               -- 202
    description TEXT,                    -- User description
    source_workspace_path TEXT           -- Path to lineage_workspace.duckdb
);
```

### Table: `baseline_objects`
```sql
CREATE TABLE baseline_objects (
    object_id INTEGER PRIMARY KEY,
    object_name TEXT NOT NULL,
    schema_name TEXT NOT NULL,
    object_type TEXT NOT NULL,           -- 'Stored Procedure'
    ddl_text TEXT NOT NULL,              -- Full DDL
    ddl_hash TEXT NOT NULL,              -- SHA256 hash for change detection

    -- Ground truth (verified dependencies)
    expected_inputs_json TEXT,           -- JSON: [123, 456, 789]
    expected_outputs_json TEXT,          -- JSON: [111, 222]

    -- Metadata
    verified BOOLEAN DEFAULT FALSE,      -- Manually verified?
    notes TEXT,                          -- Special notes
    captured_at TIMESTAMP NOT NULL
);
```

### Table: `baseline_change_log`
```sql
CREATE TABLE baseline_change_log (
    change_id INTEGER PRIMARY KEY,
    baseline_name TEXT NOT NULL,
    object_id INTEGER NOT NULL,
    change_type TEXT NOT NULL,           -- 'ddl_updated', 'new_object'
    old_ddl_hash TEXT,
    new_ddl_hash TEXT,
    changed_at TIMESTAMP NOT NULL,
    detected_in_run TEXT NOT NULL        -- run_id that detected change
);
```

**Purpose:** Tracks DDL changes detected during evaluation runs. The subagent auto-updates baselines when DDL changes are detected and logs them here.

---

## Evaluation Database (`current_evaluation.duckdb`)

Stores historical evaluation run data.

### Table: `evaluation_runs`
Metadata for each evaluation run.

### Table: `evaluation_history`
Detailed per-object per-method results for each run.

---

## Baseline Lifecycle

### 1. Creation
```bash
/sub_DL_OptimizeParsing init --name baseline_v3.7.0
```

**What happens:**
- Reads production `lineage_workspace.duckdb`
- Exports all SP DDLs
- Extracts current dependencies as "expected" values
- Creates `baseline_v3.7.0.duckdb`

### 2. Usage
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_v3.7.0
```

**What happens:**
- Loads baseline objects
- Runs all 3 methods (regex, SQLGlot, AI)
- Compares results to expected dependencies
- Auto-updates baseline if DDL changed

### 3. Auto-Update
When evaluation detects DDL changes:
- **Auto-updates** DDL text and hash in baseline
- **Logs change** to `baseline_change_log`
- **Preserves** expected dependencies (unless manually updated)

**View changes:**
```sql
-- Connect to baseline database
SELECT * FROM baseline_change_log
ORDER BY changed_at DESC
LIMIT 10;
```

### 4. Archival
Old baselines can be kept for historical reference:
```bash
mv baseline_v3.7.0.duckdb archive/baseline_v3.7.0.duckdb
```

---

## Best Practices

### ✅ DO:
- Create baseline **before** major parser changes (for regression testing)
- Use **descriptive names** (`baseline_v3.7.0`, `baseline_pre_cte_refactor`)
- Keep baselines **under version control** (they're small - ~5MB for 202 SPs)
- Review `baseline_change_log` after each evaluation run

### ❌ DON'T:
- Delete baselines that are still referenced in evaluation runs
- Manually edit baseline databases (use subagent commands)
- Create baselines from incomplete production data

---

## Troubleshooting

### Issue: "Baseline not found"
```bash
# List available baselines
ls -lh evaluation_baselines/*.duckdb

# Expected output:
# baseline_v3.7.0.duckdb
# current_evaluation.duckdb
```

### Issue: "Too many DDL changes detected"
This means production data has changed significantly since baseline was captured.

**Solution:**
```bash
# Create new baseline from current production data
/sub_DL_OptimizeParsing init --name baseline_v3.7.1
```

### Issue: "Low confidence scores across all methods"
Check if expected dependencies are accurate:

```sql
-- Connect to baseline database
SELECT
    object_name,
    expected_inputs_json,
    expected_outputs_json,
    verified
FROM baseline_objects
WHERE object_id = 12345;
```

If expected values are wrong, the baseline was created from low-quality production data.

---

## Storage Size

**Typical sizes:**
- Single baseline: ~5-10 MB (for 202 SPs)
- Evaluation history: ~1-2 MB per run
- Total directory: ~50-100 MB (with 10+ baselines and 100+ evaluation runs)

**Disk space is minimal** - keeping historical baselines is recommended for trend analysis.

---

## Related Commands

```bash
# Create baseline
/sub_DL_OptimizeParsing init --name baseline_v3.7.0

# Run evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_v3.7.0

# View report
/sub_DL_OptimizeParsing report --latest

# Compare runs
/sub_DL_OptimizeParsing compare --run1 run_A --run2 run_B
```

---

**Last Updated:** 2025-11-02
**Maintained By:** Data Lineage Team
