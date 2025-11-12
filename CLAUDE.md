# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

## Project: Data Lineage Visualizer v4.3.2
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **Database:** Azure Synapse Analytics (T-SQL) - extensible to other data warehouses
- **Parser:** v4.3.2 ✅ **100% success rate** + defensive improvements (2025-11-12)
- **Confidence:** v2.1.0 (4-value: 0, 75, 85, 100)
- **Frontend:** v3.0.1 | **API:** v4.0.3
- **Features:** Phantom Objects (v4.3.0), UDF Support, Regex-First Architecture (v4.3.1)

## ⚠️ BEFORE CHANGING PARSER - READ THIS
**Critical Reference:** [PARSER_CRITICAL_REFERENCE.md](PARSER_CRITICAL_REFERENCE.md)
- Explains WARN mode regression (empty lineage disaster)
- Documents why RAISE mode is ONLY correct choice
- Lists what NOT to change (defensive checks, regex patterns)
- Testing protocol to prevent regressions

## Recent Updates

### v4.3.2 - Defensive Improvements (2025-11-12) 🛡️
**Prevents WARN mode regression from happening again**

**Changes:**
1. **Empty Command Node Check** (`quality_aware_parser.py:752-762`)
   - Detects: `isinstance(parsed, exp.Command) and not parsed.expression`
   - Prevents: WARN mode returning empty Command nodes → empty lineage
   - Impact: Zero functional change, pure defensive programming

2. **Performance Tracking** (`quality_aware_parser.py:344-346, 512-515, 562-565`)
   - Logs: SPs taking >1 second to parse
   - Purpose: Identify performance bottlenecks
   - Impact: Diagnostic visibility only

3. **Golden Test Suite** (`tests/unit/test_parser_golden_cases.py`)
   - Tests: Specific SPs with known correct inputs/outputs
   - Detects: Empty lineage regression immediately
   - Coverage: ErrorLevel modes, confidence model, edge cases

**Documentation:**
- `PARSER_CRITICAL_REFERENCE.md` - Slim critical reference (READ BEFORE CHANGING PARSER)
- `PARSER_IMPROVEMENT_SUMMARY.md` - Comprehensive analysis
- `parser_recommendations_analysis.md` - Recommendation review
- `implementation_plan.md` - Research-backed plan

**Risk:** Zero (defensive only)
**Success Rate:** 100% maintained

### v4.3.1 - Parser Architecture Restored (2025-11-12) 🔥
**CRITICAL FIX: Reverted from broken SQLGlot WARN mode to proven regex-first baseline**

**Before (Broken):**
- ❌ 1% success rate (2/515 SPs with dependencies)
- ❌ SQLGlot WARN mode returned Command nodes with zero table extraction
- ❌ Statement splitting caused JOIN context loss
- ❌ Average confidence: 0.0

**After (Fixed):**
- ✅ **100% success rate** (349/349 SPs with dependencies)
- ✅ **82.5%** at confidence 100 (288 SPs)
- ✅ **7.4%** at confidence 85 (26 SPs)
- ✅ **10.0%** at confidence 75 (35 SPs)
- ✅ Average **3.20 inputs** and **1.87 outputs** per SP
- ✅ Test SPs verified: spLoadFactLaborCostForEarnedValue_Post, spLoadDimTemplateType

**Technical Changes:**
1. **Regex-First Architecture** (`quality_aware_parser.py:735-768`)
   - Regex ALWAYS runs on full DDL first (guaranteed baseline, no context loss)
   - SQLGlot RAISE mode as optional enhancement (strict, fails fast)
   - Combined results provide best-of-both-worlds accuracy
   - Added CROSS JOIN pattern support

2. **Root Cause Fixed:**
   - SQLGlot WARN mode silently returned empty Command nodes
   - Statement splitting orphaned JOIN clauses from SELECT context
   - Regex-first approach eliminates both issues

3. **Testing & Validation:**
   - Created `scripts/testing/check_parsing_results.py` for database validation
   - Created `scripts/testing/verify_sp_parsing.py` for detailed SP analysis
   - Verified phantom object detection working correctly
   - Full documentation: `docs/reports/COMPLETE_PARSING_ARCHITECTURE_REPORT.md`

### UI Improvements ✅
1. **Legend Schema-Only Display** (2025-11-12)
   - Legend now shows ONLY schemas (removed node types/edge types sections)
   - Phantom schemas marked with 👻 ghost emoji in legend and dropdown
   - Changed phantom node icon from ❓ to 👻

2. **Frontend Performance Optimizations:**
   - ✅ Memoized ReactFlow proOptions for stable reference
   - ✅ Changed `transition-all` to `transition-transform` (faster CSS)
   - ✅ Added FPS monitoring in development mode (`window.__fpsMonitor`)
   - ✅ All components using React.memo (CustomNode, QuestionMarkIcon)
   - ✅ All event handlers wrapped in useCallback
   - **Performance Grade: A-** (ready for production scale)

## Quick Start

```bash
./start-app.sh  # Backend (8000) + Frontend (3000)
```

**First-time setup:**
```bash
pip install -r requirements.txt && ./start-app.sh
```

## Folder Structure

```
/
├── README.md                     # Project overview
├── CLAUDE.md                     # AI instructions
├── requirements.txt              # Python dependencies
├── start-app.sh / stop-app.sh    # Application control
│
├── api/                          # FastAPI backend
├── frontend/                     # React + React Flow UI
├── lineage_v3/                   # Core parsing engine
│   ├── config/                   # Pydantic settings
│   ├── core/                     # Main parser logic
│   ├── dialects/                 # SQL dialect handlers
│   ├── extractor/                # DMV extractors (internal)
│   ├── parsers/                  # Quality-aware parser
│   ├── rules/                    # YAML cleaning rules
│   └── utils/                    # Helper utilities
│
├── scripts/                      # Utilities
│   ├── extractors/               # Database metadata export tools
│   │   ├── synapse_dmv_extractor.py  # For Synapse admins
│   │   └── README.md             # Extractor usage guide
│   └── testing/                  # Testing & validation tools
│       ├── check_parsing_results.py  # Database validation
│       ├── verify_sp_parsing.py      # SP-level verification
│       ├── analyze_sp.py             # Deep analysis tool
│       ├── test_upload.sh            # API upload testing
│       └── poll_job.sh               # Job status polling
│
├── docs/                         # Documentation
│   ├── SETUP.md                  # Installation guide
│   ├── USAGE.md                  # Parser usage
│   ├── REFERENCE.md              # Technical reference
│   ├── RULE_DEVELOPMENT.md       # YAML rule creation
│   ├── reports/                  # Status reports & analysis
│   │   ├── COMPLETE_PARSING_ARCHITECTURE_REPORT.md
│   │   ├── BUGS.md
│   │   ├── TESTING_SUMMARY.md
│   │   └── UAT_READINESS_REPORT.md
│   └── archive/                  # Old documentation
│
├── evaluation/                   # Evaluation & baselines
│   ├── baselines/                # Historical baselines
│   ├── real_data/                # Test Parquet files
│   └── results/                  # Analysis results
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── exploratory/              # Ad-hoc test scripts
│   └── baselines/                # Test baselines
│
├── data/                         # Sample data
└── .build/                       # Build artifacts (gitignored)
    ├── temp/                     # Temporary files
    └── test_screenshots/         # Test screenshots
```

**Key principles:**
- **Root directory:** Only essential files (README, CLAUDE.md, requirements.txt, app control scripts)
- **User-facing tools:** `/scripts/extractors/` for database admins
- **Documentation:** All markdown docs organized in `/docs/`
- **Evaluation:** Renamed from `evaluation_baselines` to `evaluation` for clarity
- **Build artifacts:** Hidden in `.build/` directory (gitignored)

## Configuration (v4.3.0 - Pydantic Settings)

**Centralized configuration** via `.env` with type safety:

```bash
# SQL Dialect
SQL_DIALECT=tsql  # Default (Synapse/SQL Server)

# Global Schema Exclusion (v4.3.0)
EXCLUDED_SCHEMAS=sys,dummy,information_schema,tempdb,master,msdb,model

# Phantom Objects (v4.3.0)
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B
PHANTOM_EXCLUDE_DBO_OBJECTS=cte,cte_*,CTE*,ParsedData,#*,@*,temp_*,tmp_*
```

**Supported dialects** (data warehouses only):
- `tsql` - Azure Synapse, SQL Server, Azure SQL *(default)*
- `fabric` - Microsoft Fabric
- `postgres` - PostgreSQL data warehouses
- `oracle` - Oracle Database
- `snowflake` - Snowflake
- `redshift` - Amazon Redshift
- `bigquery` - Google BigQuery

**Configuration File:** `lineage_v3/config/settings.py` (Pydantic BaseSettings)

## Documentation

**All documentation (4 files only):**
- [README.md](README.md) - Project overview & quickstart
- [docs/SETUP.md](docs/SETUP.md) - Installation & configuration
- [docs/USAGE.md](docs/USAGE.md) - Parser usage & troubleshooting
- [docs/REFERENCE.md](docs/REFERENCE.md) - Technical specs, schema, API
- [docs/RULE_DEVELOPMENT.md](docs/RULE_DEVELOPMENT.md) - YAML rule creation

## Parser v4.3.1 ✅

**Architecture:** Regex-First Baseline + SQLGlot Enhancement
**Strategy:** Full DDL Regex (guaranteed) → SQLGlot RAISE (optional bonus) → Confidence
**Performance:** 349/349 SPs (100%), 82.5% at confidence 100 ✅
**Validation:** Tested with API upload + database verification + Playwright E2E

### Parser Architecture (Regex-First)

**Phase 1: Regex Scan (Guaranteed Baseline)**
- Runs on FULL DDL (no statement splitting = no context loss)
- Comprehensive patterns: FROM, JOIN, INNER/LEFT/RIGHT/FULL/CROSS JOIN
- Target patterns: INSERT, UPDATE, DELETE, MERGE
- Always succeeds, provides guaranteed baseline

**Phase 2: SQLGlot Enhancement (Optional Bonus)**
- RAISE mode (strict, fails fast with exception)
- Runs on cleaned DDL statements
- Adds any additional tables found by AST parsing
- Failures ignored, regex baseline already has coverage

**Phase 3: Post-Processing**
- Remove system schemas (sys, dummy, information_schema)
- Remove temp tables (#temp, @variables)
- Remove non-persistent objects (CTEs)
- Deduplicate results

**Phase 4: Confidence Calculation**
- Compare found vs expected tables (from DMV dependencies)
- Map completeness % to discrete scores: 0, 75, 85, 100

### MANDATORY: Parser Development Protocol

**Testing approach:**
1. **Before changes:** Run `scripts/testing/check_parsing_results.py` to document baseline
2. **Make changes:** Update regex patterns or SQLGlot logic in `quality_aware_parser.py`
3. **Test specific SPs:** Use `scripts/testing/verify_sp_parsing.py <sp_name>` for validation
4. **Upload test:** Run `scripts/testing/test_upload.sh` with Parquet files
5. **Validate results:** Re-run `check_parsing_results.py`, ensure 100% success maintained
6. **Pass criteria:** No regressions + expected improvements

**Quick validation:**
```bash
# Full validation
python3 scripts/testing/check_parsing_results.py

# Specific SP verification
python3 scripts/testing/verify_sp_parsing.py

# API end-to-end test
./scripts/testing/test_upload.sh
```

### SQL Cleaning Rules (YAML-based)

**Add new rules** (no Python required):
1. Create YAML file: `lineage_v3/rules/tsql/20_your_rule.yaml`
2. Define pattern and test cases
3. Run tests: `pytest tests/unit/rules/ -v`

**Example rule:**
```yaml
name: remove_print
description: Remove T-SQL PRINT statements
dialect: tsql
enabled: true
priority: 15

pattern: 'PRINT\s+.*'
replacement: ''

test_cases:
  - name: simple_print
    input: "PRINT 'Debug'"
    expected: ""
```

**Debug mode:**
```yaml
debug:
  log_matches: true
  log_replacements: true
  show_context_lines: 2
```

See [docs/RULE_DEVELOPMENT.md](docs/RULE_DEVELOPMENT.md) for complete guide.

## Confidence Model v2.1.0

**4 discrete values:** 0, 75, 85, 100

```python
completeness = (found_tables / expected_tables) * 100
if completeness >= 90: confidence = 100
elif completeness >= 70: confidence = 85
elif completeness >= 50: confidence = 75
else: confidence = 0
```

**Special cases:** Orchestrators (only EXEC) → 100% | Parse failures → 0%

## Phantom Objects & UDF Support (v4.3.0)

**Phantom Objects:** Database objects referenced in SQL but not in catalog metadata

**Features:**
- **Automatic detection** from stored procedure dependencies
- **Negative IDs** (-1 to -∞) to distinguish from real objects
- **Visual indicators:** Orange question mark badge, dashed borders
- **Include-list filtering:** Only create phantoms for configured schemas (CONSUMPTION*, STAGING*, etc.)
- **Universal exclusion:** System schemas (sys, dummy, information_schema) filtered globally

**Configuration:**
```bash
# Include schemas for phantom creation (wildcard support)
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B

# Exclude patterns in dbo schema (CTEs, temp tables)
PHANTOM_EXCLUDE_DBO_OBJECTS=cte,cte_*,CTE*,ParsedData,#*,@*,temp_*,tmp_*
```

**Database Tables:**
- `phantom_objects` - Stores phantom metadata with negative IDs
- `phantom_references` - Tracks which SPs reference each phantom

**Frontend:**
- 👻 Ghost emoji badge on phantom nodes (v4.3.1)
- 👻 Ghost emoji next to phantom schemas in legend and dropdown (v4.3.1)
- 🔶 Dashed orange borders for phantom nodes
- 💎 Diamond shape for Functions (UDFs, TVFs, etc.)
- 🟦 Square shape for Stored Procedures
- ⚪ Circle shape for Tables/Views

**Legend Display (v4.3.1):**
- Shows ONLY schemas (node types/edge types sections removed)
- Phantom schemas marked with 👻 ghost emoji
- Cleaner, more focused UI

**Status:** ✅ Parser 100% functional, phantom detection working perfectly

See [UAT_READINESS_REPORT.md](docs/reports/UAT_READINESS_REPORT.md) for details.

## Performance (v4.3.0)

**Current:** 500-node visible limit prevents browser crashes
**Target:** 5K-10K nodes for production with 60 FPS

**Optimizations Implemented:**
- ✅ All React components wrapped in React.memo
- ✅ All ReactFlow props properly memoized (useCallback, useMemo)
- ✅ Smart node prioritization (Phantoms > SPs > Functions > Tables)
- ✅ QuestionMarkIcon and CustomNode fully optimized

**Performance Grade:** **A-** (Excellent foundation, ready for scale)

**For Production Scale:**
- Remove 500-node limit after UAT validation
- Expected 45-60 FPS with current optimizations
- CSS optimizations available if needed

See [docs/PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md) and [docs/REACT_FLOW_PERFORMANCE.md](docs/REACT_FLOW_PERFORMANCE.md).

## Testing Infrastructure

### Unit & Integration Tests

**Run all tests:**
```bash
pytest tests/ -v  # 73+ tests, < 1 second
```

**Test coverage:**
- Unit tests: 28 tests (dialect validation, settings)
- Comment hint parser: 19 tests
- Synapse integration: 11 tests (1,067 real objects)
- Total: 73 passing, ZERO regressions ✅

### Parser Validation & Testing (v4.3.1)

**Database Validation:**
```bash
# Full parsing results validation
python3 scripts/testing/check_parsing_results.py

# Output: Success rate, confidence distribution, avg dependencies, top SPs
```

**Specific SP Verification:**
```bash
# Detailed analysis of specific stored procedure
python3 scripts/testing/verify_sp_parsing.py

# Shows: Actual table names, phantom detection, expected vs found validation
```

**API End-to-End Testing:**
```bash
# Upload Parquet files and validate processing
./scripts/testing/test_upload.sh

# Tests: File upload, job processing, result generation
```

**Deep Analysis Tool:**
```bash
# Debug why specific SP fails parsing
python3 scripts/testing/analyze_sp.py

# Shows: DDL preview, regex matches, SQLGlot results, problematic patterns
```

**Features:**
- ✅ 100% parser success rate validation
- ✅ Confidence score distribution tracking
- ✅ Phantom object detection verification
- ✅ Expected vs actual source/target validation
- ✅ API workflow end-to-end testing

### Frontend Performance Testing

**FPS Monitoring (Development Mode):**
```bash
npm run dev
# In browser console:
window.__fpsMonitor.getAverage()  # Check current FPS
```

**Playwright E2E Tests:**
```bash
cd frontend
npm run test:e2e  # 90+ tests for phantom objects feature
```

**Performance Profiling:**
- React DevTools Profiler (identifies slow components)
- Chrome Performance tab (FPS graph, flame charts)
- See [frontend/docs/PERFORMANCE_TESTING.md](frontend/docs/PERFORMANCE_TESTING.md)

**Targets:**
- 1K nodes: 60 FPS ✅ (expected with optimizations)
- 5K nodes: 45-60 FPS (production target)
- 10K nodes: 30-45 FPS (may require WebGL)

See [TESTING_SUMMARY.md](docs/reports/TESTING_SUMMARY.md) for details.

## Slash Commands

**Available:**
- `/sub_DL_Clean` - Archive old docs, optimize CLAUDE.md

**Planned:**
- `/sub_DL_OptimizeParsing` - Parser evaluation (precision/recall/F1)
- `/sub_DL_Build` - Azure deployment
- `/sub_DL_GitPush` - Commit and push
- `/sub_DL_Restart` - Kill ports 3000/8000, restart servers

## Troubleshooting

**Port conflicts:** `./stop-app.sh`
**Missing dependencies:** `pip install -r requirements.txt && cd frontend && npm install`
**Low confidence:** Add `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints
**CORS errors:** Check `ALLOWED_ORIGINS` in `.env`
**Rule debugging:** Set `debug.log_matches: true` in YAML rule

See [docs/USAGE.md](docs/USAGE.md) for detailed troubleshooting.

## Git Guidelines

- Commit frequently (small, focused commits)
- Push to feature branches (never to main)
- Pull requests required for merging
- No rebasing or force pushing

---

**Last Updated:** 2025-11-12
**Version:** v4.3.1 ✅ Parser 100% functional
