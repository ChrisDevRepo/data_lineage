# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

## Project: Data Lineage Visualizer v4.2.0
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **System:** Python 3.12.3, Node.js, WSL2
- **Dir:** `/home/chris/sandbox`
- **Branch:** `feature/dataflow-mode`
- **Parser:** v4.2.0 | 97.0% SP confidence | 95.5% overall
- **Confidence:** v2.0.0 (Multi-Factor) with detailed breakdown
- **Frontend:** v2.9.2

## Quick Start
```bash
# Backend: http://localhost:8000
cd /home/chris/sandbox/api && python3 main.py

# Frontend: http://localhost:3000
cd /home/chris/sandbox/frontend && npm run dev

# Parser (incremental / full-refresh)
python lineage_v3/main.py run --parquet parquet_snapshots/
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

## Parser (v4.2.0)
- **Strategy:** Regex → SQLGlot → Rule Engine
- **Performance:** 729/763 objects (95.5%), 196/202 SPs (97.0%)
- **Features:** Comment hints (@LINEAGE_INPUTS/@LINEAGE_OUTPUTS), dataflow mode, global target exclusion
- **Confidence:** Multi-factor model v2.0.0 with detailed breakdown (5 weighted factors)

## Parser Development (MANDATORY)

**🚨 ALWAYS use `/sub_DL_OptimizeParsing` for parser changes 🚨**

```bash
# 1. Before changes: Create baseline
/sub_DL_OptimizeParsing init --name baseline_$(date +%Y%m%d)_before_description
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description

# 2. Make changes to quality_aware_parser.py

# 3. After changes: Run evaluation (MANDATORY)
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description
/sub_DL_OptimizeParsing compare --run1 run_YYYYMMDD_HHMMSS --run2 run_YYYYMMDD_HHMMSS

# 4. Pass criteria: Zero regressions, expected improvements, progress toward 95%

# 5. Update docs/PARSER_EVOLUTION_LOG.md
```

**DO NOT:**
- Skip evaluation "because change is small"
- Commit parser changes without running subagent
- Rely on manual testing

---

## Sub-Agents

- **`/sub_DL_OptimizeParsing`** - Parser evaluation (precision/recall/F1)
- **`/sub_DL_TestFrontend`** - Browser testing (functional + visual regression)
- **`/sub_DL_Clean`** - Archive old docs, optimize CLAUDE.md
- **`/sub_DL_Build`** - Azure deployment package
- **`/sub_DL_GitPush`** - Commit and push to remote
- **`/sub_DL_Restart`** - Kill ports 3000/8000, restart servers

See [.claude/commands/](/.claude/commands/) for detailed docs.

---

## Key Features

### Incremental Parsing
- DuckDB persists between runs
- Re-parses only modified/new + low confidence objects (<0.85)
- 50-90% faster

### Parquet File Detection
- Auto-detects by schema
- Required: objects, dependencies, definitions
- Optional: query_logs, table_columns

### Confidence Model (v2.0.0 - Multi-Factor)
**5 Weighted Factors (sum to 1.0):**
- **Parse Success (30%)**: Did parsing complete without errors?
- **Method Agreement (25%)**: Do regex and SQLGlot agree?
- **Catalog Validation (20%)**: Do extracted objects exist in catalog?
- **Comment Hints (10%)**: Did developer provide @LINEAGE hints?
- **UAT Validation (15%)**: Has user verified this SP?

**Confidence Levels:**
- **High (0.85)**: total_score ≥ 0.80
- **Medium (0.75)**: total_score ≥ 0.65
- **Low (0.50)**: total_score > 0
- **Failed (0.0)**: total_score = 0

**Every parsed object includes detailed breakdown:**
```json
{
  "parse_success": {"score": 1.0, "weight": 0.30, "contribution": 0.30},
  "method_agreement": {"score": 0.95, "weight": 0.25, "contribution": 0.2375},
  "catalog_validation": {"score": 1.0, "weight": 0.20, "contribution": 0.20},
  "comment_hints": {"score": 0.0, "weight": 0.10, "contribution": 0.0},
  "uat_validation": {"score": 0.0, "weight": 0.15, "contribution": 0.0},
  "total_score": 0.7375,
  "bucketed_confidence": 0.75,
  "label": "Medium",
  "color": "yellow"
}
```

**Single Source of Truth:** `ConfidenceCalculator.calculate_multifactor()`

### Quality Assurance
- **`check_unrelated_objects.py`** - Finds objects with no inputs AND outputs
  - Pattern analysis (INSERT, UPDATE, FROM, JOIN)
  - Export: `temp/unrelated_objects_report.json`

---

## Git Guidelines

- **Branch:** `feature/slim-parser-no-ai` | **Main:** `main`
- **DO:** Commit frequently, push to origin
- **DON'T:** Rebase, merge from other branches, merge to main (requires approval)

---

## Essential Documentation

**Start Here:**
- [README.md](README.md) - Project overview
- [lineage_specs.md](lineage_specs.md) - Parser spec
- [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) - **NEW** Architecture & components
- [docs/SETUP_AND_DEPLOYMENT.md](docs/SETUP_AND_DEPLOYMENT.md) - **NEW** Installation & deployment
- [docs/MAINTENANCE_GUIDE.md](docs/MAINTENANCE_GUIDE.md) - **NEW** Operations & troubleshooting

**Parser & Technical:**
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing guide
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema

**Evaluation:**
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Parser evaluation framework
- [evaluation_baselines/README.md](evaluation_baselines/README.md) - Baseline management

**Component-Specific:**
- [api/README.md](api/README.md) - Backend API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide
- [frontend/docs/UI_STANDARDIZATION_GUIDE.md](frontend/docs/UI_STANDARDIZATION_GUIDE.md) - UI design system
- [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md) - Performance optimizations

---

## Troubleshooting

**Import Errors:**
```bash
python lineage_v3/main.py validate
pip install -r requirements.txt
```

**Low Confidence (<0.85):**
- Use `/sub_DL_OptimizeParsing` to analyze quality
- Review [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
- Improve regex patterns + SQLGlot preprocessing

**Frontend Issues:**
- Check JSON path in Import Data modal
- Verify JSON format
- Check browser console

**Performance (Large Datasets >1,000 nodes):**
- **v2.9.1 optimizations:** Debouncing, layout caching, optimized filtering
- See [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md)
- **Supports 5,000+ nodes** smoothly (100x faster schema toggling)

**Port Conflicts:**
```bash
lsof -ti:8000 | xargs -r kill  # Backend
lsof -ti:3000 | xargs -r kill  # Frontend
```

---

**Last Updated:** 2025-11-06 (Multi-Factor Confidence System v2.0.0)
**Version:** v4.2.0 (Comment Hints Parser + Multi-Factor Confidence)
**Parser:** 97.0% SP confidence | 95.5% overall | Dataflow mode + no circular dependencies
**Confidence:** v2.0.0 (Multi-Factor with detailed breakdown)
**Frontend:** v2.9.2 (Global exclusion patterns + UI simplified) | **API:** v4.0.3

**Recent Changes (2025-11-06):**
- ✅ **Phase 3**: Multi-factor confidence system (v2.0.0) with 5 weighted factors
- ✅ **Phase 2**: Comment hints parser (@LINEAGE_INPUTS/@LINEAGE_OUTPUTS)
- ✅ **Phase 1**: UAT feedback system integration (15% weight)
- ✅ Confidence breakdown stored in database and exported in all JSON formats
- ✅ Comprehensive smoke testing (31/31 tests passed)
- ✅ Updated PARSER_EVOLUTION_LOG.md with all three phases
- ✅ Single source of truth: ConfidenceCalculator.calculate_multifactor()
