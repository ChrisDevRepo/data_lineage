# temp/

This folder contains intermediate scripts, testing files, and debugging code that are not part of the production implementation.

## Purpose

- **Keep root folder clean** - Move temporary files here instead of cluttering the project root
- **Gitignored** - Contents are not tracked by git (except this README)
- **Safe to delete** - These files can be removed when no longer needed

## Current Contents

### Phase 3 Testing (2025-11-06)

**Multi-Factor Confidence System Tests:**
1. **smoke_test_confidence.py** - Core confidence calculator tests (21 tests)
2. **test_hints_standalone.py** - Standalone comment hints parser tests (10 tests)
3. **smoke_test_report.py** - Test orchestration and reporting
4. **SMOKE_TEST_RESULTS.md** - Comprehensive test documentation (31/31 tests passed)

**Phase Planning & Analysis:**
5. **parsing_review/** - Analysis documents from parsing review phase
6. **uat_feedback/** - Phase 1 UAT feedback system implementation

### Moved from Root (2025-11-03)

1. **run_evaluation.py** - CLI wrapper for `/sub_DL_OptimizeParsing` (superseded by subagent)
2. **generate_report.py** - One-off report generation script (hardcoded run_id)
3. **smoke_test_sp.py** - SP dependency testing script (results archived in `docs/archive/2025-11-02/`)

## Usage Guidelines

When working on the project, place temporary files here:
- Ad-hoc testing scripts
- Debugging utilities
- One-off data analysis scripts
- Experimental code snippets
- SQL test files

**Do NOT place here:**
- Production code
- Documentation
- Configuration files
- Anything that needs to be committed to git
