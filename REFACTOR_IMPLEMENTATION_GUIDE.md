# Implementation Guide: AI Code Removal & Refactoring

**Date:** 2025-11-05
**Priority:** Critical fixes + Code cleanup
**Estimated Time:** 1-2 hours
**Risk Level:** Low

---

## Overview

This guide provides **exact code changes** to remove AI-related code and clean up the codebase. Each change is marked with risk level and testing steps.

---

## Part 1: Critical Fixes (Required)

### 1.1 Fix Broken Import 🔴 CRITICAL

**File:** `evaluation/evaluation_runner.py`
**Risk:** Low (removes broken code)
**Time:** 5 minutes

**Line 27 - REMOVE:**
```python
from lineage_v3.parsers.ai_disambiguator import run_standalone_ai_extraction
```

**Lines 503-550 - REMOVE entire method:**
```python
def _run_ai_method(
    self,
    object_id: int,
    object_name: str,
    ddl: str,
    expected_inputs: List[int],
    expected_outputs: List[int]
) -> Dict:
    """Run AI disambiguation on a single object."""
    # ... entire method body ...
```

**Lines 122, 222, 243 - REMOVE AI tracking variables:**
```python
# Line 122
total_ai_confidence = 0.0  # REMOVE

# Line 222
total_ai_confidence += result['ai']['confidence']  # REMOVE

# Line 243 (SQL query)
avg_ai_confidence = ?,  # REMOVE from SQL
```

**Test:**
```bash
python3 -c "from evaluation.evaluation_runner import EvaluationRunner; print('✅ Import fixed')"
```

---

## Part 2: Remove AI Configuration (High Priority)

### 2.1 Clean Settings Module 🟡

**File:** `lineage_v3/config/settings.py`
**Risk:** Low (not actively used)
**Time:** 15 minutes

#### Step 1: Remove AI Settings Classes

**Lines 21-57 - REMOVE entire class:**
```python
class AzureOpenAISettings(BaseSettings):
    """
    Azure OpenAI configuration for AI-assisted disambiguation.
    ...
    """
    # ... entire class ...
```

**Lines 59-110 - REMOVE entire class:**
```python
class AIDisambiguationSettings(BaseSettings):
    """
    AI-assisted SQL disambiguation configuration.
    ...
    """
    # ... entire class ...
```

#### Step 2: Update Main Settings Class

**Lines 194-200 - REMOVE from Settings class:**
```python
class Settings(BaseSettings):
    # Nested configuration sections
    azure_openai: AzureOpenAISettings = Field(  # REMOVE
        default_factory=AzureOpenAISettings
    )
    ai: AIDisambiguationSettings = Field(  # REMOVE
        default_factory=AIDisambiguationSettings
    )
    parser: ParserSettings = Field(
        default_factory=ParserSettings
    )
    # ... keep parser and paths ...
```

**Lines 229-236 - REMOVE property:**
```python
@property
def ai_available(self) -> bool:
    """Check if Azure OpenAI is properly configured and available."""
    return (
        self.ai.enabled and
        self.azure_openai.endpoint is not None and
        self.azure_openai.api_key is not None
    )
```

#### Step 3: Clean Up Exception Handler

**Lines 242-295 - SIMPLIFY exception handler:**

**BEFORE:**
```python
try:
    settings = Settings()
except ValidationError as e:
    # Graceful fallback for Pydantic nested BaseSettings validation bug
    # This happens when nested settings fail to inherit env vars properly
    error_str = str(e)
    if 'AzureOpenAISettings' in error_str or 'AZURE_OPENAI' in error_str:
        # ... 50 lines of workaround code ...
    else:
        raise
except Exception as e:
    raise
```

**AFTER:**
```python
try:
    settings = Settings()
except Exception as e:
    # Re-raise validation errors
    raise
```

**Test:**
```bash
python3 -c "from lineage_v3.config import settings; print('✅ Settings OK'); print(f'Parser confidence: {settings.parser.confidence_high}')"
```

---

### 2.2 Clean CLI Arguments 🟡

**File:** `lineage_v3/main.py`
**Risk:** Low (improves CLI clarity)
**Time:** 15 minutes

#### Change 1: Remove CLI Options

**Lines 111-120 - REMOVE:**
```python
@click.option(
    '--ai-enabled/--no-ai',
    default=True,
    help='Enable/disable AI disambiguation (default: enabled)'
)
@click.option(
    '--ai-threshold',
    default=0.85,
    type=float,
    help='Parser confidence threshold to trigger AI (default: 0.85)'
)
```

#### Change 2: Update Function Signature

**Line 121 - UPDATE:**

**BEFORE:**
```python
def run(parquet, output, full_refresh, format, skip_query_logs, workspace, ai_enabled, ai_threshold):
```

**AFTER:**
```python
def run(parquet, output, full_refresh, format, skip_query_logs, workspace):
```

#### Change 3: Remove AI Settings Override

**Lines 136-143 - REMOVE:**
```python
# Override settings from CLI if provided (without modifying os.environ)
from lineage_v3.config import settings

# CLI arguments override config file settings
if not ai_enabled:
    settings.ai.enabled = False
if ai_threshold != 0.85:  # Non-default value
    settings.ai.confidence_threshold = ai_threshold
```

#### Change 4: Update Startup Message

**Line 151 - REMOVE:**
```python
click.echo(f"🤖 AI Disambiguation: {'Enabled' if settings.ai.enabled else 'Disabled'} (threshold: {settings.ai.confidence_threshold})")
```

#### Change 5: Remove AI Usage Tracking

**Lines 310, 318-319 - REMOVE:**
```python
# Line 310
ai_used_count = 0  # REMOVE

# Lines 318-319
if result.get('quality_check', {}).get('ai_used', False):
    ai_used_count += 1  # REMOVE
```

**Lines 355-359 - UPDATE summary output:**

**BEFORE:**
```python
click.echo(f"✅ Parsing Complete!")
click.echo(f"   - High confidence (≥0.85): {high_confidence_count}")
click.echo(f"   - Medium confidence (≥0.75): {medium_confidence_count}")
click.echo(f"   - Low confidence (<0.75): {low_confidence_count}")
click.echo(f"   - AI used: {ai_used_count}")
```

**AFTER:**
```python
click.echo(f"✅ Parsing Complete!")
click.echo(f"   - High confidence (≥0.85): {high_confidence_count}")
click.echo(f"   - Medium confidence (≥0.75): {medium_confidence_count}")
click.echo(f"   - Low confidence (<0.75): {low_confidence_count}")
```

**Test:**
```bash
python lineage_v3/main.py run --help
# Verify no --ai-enabled or --ai-threshold options

python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh --format frontend
# Should run without errors
```

---

## Part 3: Documentation Updates (High Priority)

### 3.1 Update README.md 🟡

**File:** `README.md`
**Risk:** None
**Time:** 2 minutes

**Line 167 - REMOVE:**
```markdown
**Environment Variables:**
```bash
cp .env.template .env
# Azure OpenAI credentials not required in v4.0.0 (slim architecture)  <-- REMOVE THIS LINE
```
```

**AFTER:**
```markdown
**Environment Variables:**
```bash
cp .env.template .env
# No external credentials required - parser uses local SQLGlot
```
```

---

### 3.2 Update CLAUDE.md 🟡

**File:** `CLAUDE.md`
**Risk:** None
**Time:** 2 minutes

**Search for any AI references and remove/update them.**

Currently clean - no changes needed.

---

## Part 4: Validation & Testing

### 4.1 Import Validation

Run all import tests:

```bash
# Backend imports
python3 -c "from lineage_v3.config import settings; print('✅ Settings OK')"
python3 -c "from lineage_v3.parsers import QualityAwareParser; print('✅ Parser OK')"
python3 -c "from lineage_v3.core import DuckDBWorkspace; print('✅ DuckDB OK')"
python3 -c "from evaluation.evaluation_runner import EvaluationRunner; print('✅ Eval OK')"

# API import
python3 -c "from api.main import app; print('✅ API OK')"
```

Expected output:
```
✅ Settings OK
✅ Parser OK
✅ DuckDB OK
✅ Eval OK
✅ API OK
```

---

### 4.2 CLI Validation

Test CLI functionality:

```bash
# Check help text
python lineage_v3/main.py run --help

# Verify options (should NOT include --ai-enabled or --ai-threshold)
# Expected: --parquet, --output, --full-refresh, --format, --skip-query-logs, --workspace
```

---

### 4.3 API Validation

Start and test API:

```bash
# Start API in background
cd /home/user/sandbox
python3 api/main.py &
API_PID=$!

# Wait for startup
sleep 3

# Test health endpoint
curl -s http://localhost:8000/health | python3 -m json.tool

# Expected output:
# {
#   "status": "ok",
#   "version": "4.0.3",
#   "uptime_seconds": ...
# }

# Cleanup
kill $API_PID
```

---

### 4.4 Full Integration Test

If you have test data:

```bash
# Run full pipeline
python lineage_v3/main.py run \
  --parquet parquet_snapshots/ \
  --output lineage_output/ \
  --full-refresh \
  --format both

# Verify output files created
ls -lh lineage_output/
# Should see: lineage.json, frontend_lineage.json
```

---

## Part 5: Commit Strategy

### 5.1 Commit Structure

Create **separate commits** for each logical change:

**Commit 1: Fix broken import**
```bash
git add evaluation/evaluation_runner.py
git commit -m "fix: remove broken AI disambiguator import

- Remove import of non-existent ai_disambiguator module
- Remove _run_ai_method() function
- Clean up AI tracking variables in evaluation

Fixes import error when running evaluation code.
"
```

**Commit 2: Remove AI configuration**
```bash
git add lineage_v3/config/settings.py
git commit -m "refactor: remove AI configuration classes

- Remove AzureOpenAISettings class
- Remove AIDisambiguationSettings class
- Remove ai_available property
- Simplify exception handler

The slim parser (v4.0+) uses Regex + SQLGlot only, no AI.
"
```

**Commit 3: Clean CLI options**
```bash
git add lineage_v3/main.py
git commit -m "refactor: remove AI CLI options

- Remove --ai-enabled and --ai-threshold flags
- Update function signature
- Remove AI usage tracking
- Update help text

CLI now accurately reflects slim parser architecture.
"
```

**Commit 4: Update documentation**
```bash
git add README.md CLAUDE.md
git commit -m "docs: remove AI references from documentation

- Update README environment variables section
- Remove mentions of Azure OpenAI credentials
- Clarify that parser is fully local (no external APIs)
"
```

---

### 5.2 Single Commit Alternative

If you prefer one commit:

```bash
git add -A
git commit -m "refactor: complete AI code removal and cleanup

This commit completes the migration to the slim parser architecture
by removing all AI-related code and configuration.

Changes:
- Fix broken ai_disambiguator import in evaluation_runner.py
- Remove AI configuration classes from settings.py
- Remove AI CLI options from main.py
- Update documentation to remove AI references

The parser now uses Regex + SQLGlot only (no AI).
All tests pass. No breaking changes to API or parser behavior.

Related: Issue #<number> - Complete AI removal for v4.0+
"
```

---

## Part 6: Rollback Plan

If something breaks, rollback steps:

```bash
# Check current commit
git log --oneline -1

# Rollback last commit
git reset --soft HEAD~1

# Or rollback all commits in this session
git reset --soft <starting-commit-hash>

# Revert changes but keep files
git reset --mixed HEAD~1

# Hard reset (loses changes - be careful!)
git reset --hard HEAD~1
```

---

## Part 7: Optional Refactors (Medium Priority)

### 7.1 Extract API Helpers

**File:** `api/main.py`

Create new file: `api/utils.py`

```python
"""API utility functions."""

from pathlib import Path
import json
from typing import Dict, Any

def read_json_file(filepath: Path) -> Dict[str, Any]:
    """
    Read and parse JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def write_json_file(filepath: Path, data: Dict[str, Any], indent: int = 2):
    """
    Write dictionary to JSON file.

    Args:
        filepath: Path to output file
        data: Dictionary to serialize
        indent: JSON indentation level
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent)
```

Then update `api/main.py` to use these helpers.

---

## Part 8: Post-Implementation Checklist

- [ ] All imports working (no errors)
- [ ] CLI help text accurate (no AI options)
- [ ] API starts without errors
- [ ] Frontend connects to API successfully
- [ ] Documentation updated (README, CLAUDE.md)
- [ ] Changes committed with clear messages
- [ ] Tests pass (if you have tests)
- [ ] Code review completed (self or peer)
- [ ] Production deployment plan documented

---

## Summary

**Total Changes:**
- 3 files modified (settings.py, main.py, evaluation_runner.py)
- 2 files updated (README.md, optional CLAUDE.md)
- ~200 lines removed
- 0 lines added (pure deletion + minor updates)

**Risk:** ✅ Low - All changes remove unused code

**Testing:** ✅ Simple - Import tests + CLI help + API health check

**Time:** ⏱️ 1-2 hours total

**Impact:** ✅ High - Cleaner codebase, accurate documentation, no confusion

---

**Ready to implement?** Follow this guide step-by-step for a clean refactor.
