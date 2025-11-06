# File Organization Rules - AI Inference Work

## 🚨 CRITICAL RULES

### Working Directory
**ALL AI inference work MUST be in:** `/home/chris/sandbox/sqlglot_improvement/`

### File Placement

**✅ CORRECT:**
```
sqlglot_improvement/
├── docs/                          # All documentation
│   ├── AI_INFERENCE_MASTER_2025_11_03.md
│   ├── AI_ANALYSIS_SUBAGENT_USAGE.md
│   └── ITERATION_3_SUMMARY.md
├── scripts/                       # Helper scripts
│   ├── query_ai_results.py
│   └── analyze_ai_results.py
├── *.log                         # Test logs (root of sqlglot_improvement)
├── FILE_ORGANIZATION.md          # This file
└── README.md

lineage_v3/
└── lineage_workspace.duckdb      # DuckDB - NEVER in root!
```

**❌ WRONG - DO NOT CREATE:**
```
/home/chris/sandbox/*.log          # NO - logs in project root
/home/chris/sandbox/*.duckdb       # NO - DuckDB copy in root
/home/chris/sandbox/docs/*.md      # NO - main docs folder
/home/chris/sandbox/*.md           # NO - docs in root
```

### DuckDB Workspace
**ONLY Location:** `lineage_v3/lineage_workspace.duckdb`
**Never:** Copy to root, move, or create duplicates
**Why:** Parser creates it here, analysis scripts expect it here

### Test Commands
**Always use relative paths from sqlglot_improvement:**
```bash
cd lineage_v3
../venv/bin/python main.py run --parquet ../parquet_snapshots/ --full-refresh 2>&1 | tee ../sqlglot_improvement/ai_test_iter3.log
```

## Subagent Usage

### /sub_DL_AnalyzeAI
**Purpose:** Analyze AI test results efficiently
**Usage:**
```
Task(subagent_type="general-purpose", model="haiku",
     prompt="Analyze Iteration N results.
             Log: sqlglot_improvement/ai_test_iterN.log
             DB: lineage_v3/lineage_workspace.duckdb")
```

**Why:** Saves 75% tokens, preserves main agent context

## Documentation Rules

### Keep It Concise
- **Master doc:** High-level status + next actions only
- **Iteration results:** Key metrics + recommendations
- **Usage guides:** Essential steps only
- **Avoid:** Verbose explanations, repeated content

### Required Sections
1. **Status** (1 line)
2. **Results** (metrics table)
3. **Next Actions** (prioritized list)
4. **Files Changed** (list only)

### Avoid
- Long background explanations
- Duplicate information
- Example code (link to files instead)
- Detailed research findings (summarize only)
