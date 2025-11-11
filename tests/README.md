# Tests Directory

**Last Updated:** 2025-11-06
**Organization:** Unit Tests | Evaluation Framework | Baselines

---

## 📂 Directory Structure

```
tests/
├── README.md (this file)
├── unit/                    # Unit tests
│   ├── test_comment_hints_parser.py  # Comment hints extraction tests
│   └── run_hints_tests.py           # Test runner
├── evaluation/              # Parser evaluation framework
│   ├── __init__.py
│   ├── baseline_manager.py      # Baseline CRUD operations
│   ├── evaluation_runner.py     # Core evaluation logic
│   ├── report_generator.py      # Report generation
│   ├── score_calculator.py      # Precision/recall/F1
│   └── schemas.py              # DuckDB schemas
└── baselines/               # Test baselines
    ├── parser/              # Parser evaluation baselines
    │   └── README.md
    └── frontend/            # Frontend visual regression
        ├── desktop/
        │   └── homepage_loaded.png
        └── README.md
```

---

## 🧪 Unit Tests (`tests/unit/`)

**Purpose:** Unit tests for individual parser components

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_comment_hints_parser.py

# Run with coverage
pytest tests/unit/ --cov=lineage_v3/parsers
```

### Current Tests

| Test File | Component | Tests | Status |
|-----------|-----------|-------|--------|
| `test_comment_hints_parser.py` | Comment Hints Parser | 10 | ✅ Passing |

---

## 📊 Evaluation Framework (`tests/evaluation/`)

**Purpose:** Parser quality evaluation and regression testing

**What it does:**
- Runs parser on baseline stored procedures
- Compares results to expected dependencies (ground truth)
- Calculates precision, recall, F1 scores
- Generates evaluation reports
- Tracks quality improvements over time

**Usage:**

```bash
# Create baseline
/sub_DL_OptimizeParsing init --name baseline_v4.2.0

# Run full evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_v4.2.0

# View latest report
/sub_DL_OptimizeParsing report --latest

# Compare two runs
/sub_DL_OptimizeParsing compare --run1 run_A --run2 run_B
```

**Documentation:**
- See `docs/reference/SUB_DL_OPTIMIZE_PARSING_SPEC.md` for complete specification
- See `tests/baselines/parser/README.md` for baseline management

---

## 📸 Baselines (`tests/baselines/`)

**Purpose:** Store baseline snapshots for regression testing

### Parser Baselines (`tests/baselines/parser/`)

Stored procedure snapshots with expected dependencies (ground truth) for parser evaluation.

**Storage:** DuckDB files (~5-10 MB each)

**Files:**
- `baseline_v4.2.0.duckdb` - Current production baseline
- `current_evaluation.duckdb` - Evaluation run history
- `README.md` - Baseline management guide

**See:** [baselines/parser/README.md](baselines/parser/README.md)

### Frontend Baselines (`tests/baselines/frontend/`)

Visual regression testing baseline screenshots.

**Storage:** PNG images (~140 KB)

**Files:**
- `desktop/homepage_loaded.png` - Main graph view (1920x1080)
- `README.md` - Visual regression guide

**Usage:**
```bash
# Update baseline screenshots
/sub_DL_TestFrontend baseline

# Run visual regression tests
/sub_DL_TestFrontend visual
```

**See:** [baselines/frontend/README.md](baselines/frontend/README.md)

---

## 🎯 Testing Strategy

### Parser Testing Layers

1. **Unit Tests** (`tests/unit/`)
   - Test individual components in isolation
   - Fast feedback (<1 second)
   - Run on every commit

2. **Evaluation Framework** (`tests/evaluation/`)
   - Test parser on real stored procedures
   - Compare against ground truth
   - Run before releases and after major changes

3. **Integration Tests** (Future)
   - Test full pipeline (Parquet → JSON)
   - End-to-end validation

### Frontend Testing

1. **Visual Regression** (`tests/baselines/frontend/`)
   - Screenshot comparison
   - Detects unintended UI changes
   - Run before releases

2. **Functional Tests** (via `/sub_DL_TestFrontend`)
   - Node expansion/collapse
   - Filter functionality
   - Search behavior

---

## 📈 Quality Metrics

### Parser Quality (as of v4.2.0)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **SP Confidence** | ≥95% | 97.0% | ✅ Exceeded |
| **Overall Confidence** | ≥95% | 95.5% | ✅ Met |
| **Precision** | ≥90% | 96.8% | ✅ Exceeded |
| **Recall** | ≥90% | 94.2% | ✅ Exceeded |

### Test Coverage

| Component | Unit Tests | Evaluation | Status |
|-----------|------------|------------|--------|
| **Comment Hints Parser** | 10 tests | Included | ✅ |
| **Quality Aware Parser** | - | Full | ✅ |
| **Confidence Calculator** | - | Implicit | ⚠️ Needs unit tests |
| **SQL Cleaning Engine** | - | Planned | ⏳ Not yet integrated |

---

## 🔧 Development Workflow

### Before Making Parser Changes

1. **Create Baseline:**
```bash
/sub_DL_OptimizeParsing init --name baseline_before_mychange
```

2. **Run Evaluation:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_before_mychange
```

### After Making Changes

3. **Run Evaluation Again:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_before_mychange
```

4. **Compare Results:**
```bash
/sub_DL_OptimizeParsing compare --run1 <before_id> --run2 <after_id>
```

5. **Verify:**
- Zero regressions (no objects went from correct → incorrect)
- Expected improvements visible
- No unexpected side effects

---

## 📚 Related Documentation

**Setup & Configuration:**
- [docs/guides/SETUP_AND_DEPLOYMENT.md](../docs/SETUP.md)

**Parser Documentation:**
- [docs/reference/PARSER_SPECIFICATION.md](../docs/REFERENCE.md) - Complete parser spec
- [docs/reference/PARSER_EVOLUTION_LOG.md](../docs/REFERENCE.md) - Version history
- [docs/guides/PARSING_USER_GUIDE.md](../docs/USAGE.md) - Usage guide

**Evaluation:**
- [tests/baselines/parser/README.md](baselines/parser/README.md)

**Active Development:**
- [docs/development/sql_cleaning_engine/](../docs/development/sql_cleaning_engine/) - SQL pre-processing

---

## 🚀 Quick Commands

```bash
# Run unit tests
pytest tests/unit/

# Run parser evaluation
/sub_DL_OptimizeParsing run --mode full

# Run frontend tests
/sub_DL_TestFrontend

# View evaluation reports
ls -lh tests/baselines/parser/*.duckdb

# View visual baselines
ls -lh tests/baselines/frontend/desktop/
```

---

**For CI/CD Integration:** See `.github/workflows/` (coming soon)
