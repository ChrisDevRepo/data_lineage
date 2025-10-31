# Phase 4 Implementation - Action Items

**Status:** Ready to Start
**Target:** Parser v3.6.0 → v3.7.0
**Timeline:** 1-2 days (~12.5 hours total effort)
**Date:** 2025-10-31

---

## Overview

Implement AI-assisted SQL disambiguation to improve parser confidence from 80.7% to 98% high-confidence coverage.

**Architecture:** Single Parser (QualityAwareParser) + AI Fallback (Direct Azure OpenAI API)

**Expected Impact:**
- Current: 163/202 SPs ≥0.85 confidence (80.7%)
- After AI: ~198/202 SPs ≥0.85 confidence (98%)
- Coverage: ~39 SPs (19%) eligible for AI improvement

---

## Prerequisites ✅

**Completed (Phase 1-3):**
- ✅ Azure OpenAI model validated (`gpt-4.1-nano`)
- ✅ Few-shot prompt tested (91.7% accuracy, 11/12 correct)
- ✅ Cost analysis complete (~$100/year, 18x ROI)
- ✅ Hallucination risk assessed (LOW, 0% observed)
- ✅ Fine-tuning decision (not recommended)
- ✅ Production prompt documented (`lineage_v3/ai_analyzer/production_prompt.txt`)
- ✅ Comprehensive specification written (`docs/AI_DISAMBIGUATION_SPEC.md`)

**Environment Configuration:**
- ✅ Azure OpenAI credentials in `.env`
- ✅ Environment variables template updated (`.env.template`)

---

## Implementation Checklist

### Day 1 - Core Implementation (6 hours)

#### Task 1.1: Create AIDisambiguator Module
**File:** `lineage_v3/parsers/ai_disambiguator.py` (~150 lines)
**Effort:** 4 hours

**Requirements:**
- [ ] Create `AIDisambiguator` class
  - [ ] `__init__(workspace: DuckDBWorkspace)` - Initialize Azure OpenAI client
  - [ ] `disambiguate(reference, candidates, sql_context, parser_result)` - Main entry point
  - [ ] `_load_prompt()` - Load few-shot system prompt from `production_prompt.txt`
- [ ] Implement 3-layer validation methods:
  - [ ] `_validate_catalog(resolved_table)` - Layer 1: Check table exists in metadata
  - [ ] `_validate_regex_improvement(ai_result, parser_result)` - Layer 2: Verify AI improves baseline
  - [ ] `_validate_query_logs(ai_result, sp_name)` - Layer 3: Cross-validate with runtime logs
- [ ] Implement retry loop:
  - [ ] `_disambiguate_with_retry(...)` - Max 2 attempts with refined prompts
  - [ ] `_refine_context(sql_context, failed_response)` - Generate refined prompt on retry
- [ ] Implement Azure OpenAI API call:
  - [ ] `_call_azure_openai(reference, candidates, sql_context, attempt)` - API wrapper
  - [ ] JSON response parsing and error handling
  - [ ] Timeout handling (10 seconds)
- [ ] Define `AIResult` dataclass for structured results

**Key Implementation Details:**
```python
from openai import AzureOpenAI
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AIResult:
    resolved_table: str
    sources: List[int]          # object_ids
    targets: List[int]          # object_ids
    confidence: float
    reasoning: str
    validation_layers_passed: int
    is_valid: bool

class AIDisambiguator:
    def __init__(self, workspace: DuckDBWorkspace):
        self.workspace = workspace
        self.client = AzureOpenAI(
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        self.system_prompt = self._load_prompt()
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-nano")

    def disambiguate(...) -> Optional[AIResult]:
        """Main entry point with validation/retry."""
        # Implementation from AI_DISAMBIGUATION_SPEC.md Section 4
```

**Testing Checkpoint:**
- [ ] Unit test: `test_ai_disambiguator.py::test_basic_connection`
- [ ] Unit test: `test_ai_disambiguator.py::test_catalog_validation`

---

#### Task 1.2: Integrate AI into QualityAwareParser
**File:** `lineage_v3/parsers/quality_aware_parser.py` (modify ~20 lines)
**Effort:** 1 hour

**Requirements:**
- [ ] Add AI trigger logic in `parse_stored_procedure()` method
  - [ ] Check if confidence ≤ 0.85 after quality calculation
  - [ ] Check if `AI_ENABLED` config flag is True
  - [ ] Call `AIDisambiguator.disambiguate()` with ambiguous references
- [ ] Merge AI result into quality result:
  - [ ] Update `sources` and `targets` with AI-resolved object_ids
  - [ ] Update `confidence` with AI confidence score
  - [ ] Set `provenance['primary_source'] = 'ai'`
  - [ ] Set `provenance['ai_used'] = True`
- [ ] Add graceful fallback on AI failure:
  - [ ] If AI validation fails, keep original parser result
  - [ ] Log AI failure for monitoring
  - [ ] Track AI usage in `parser_comparison_log` table

**Integration Point:**
```python
# In parse_stored_procedure(), after line ~210 (confidence calculation)

if quality_result['confidence'] <= 0.85 and config.AI_ENABLED:
    from lineage_v3.parsers.ai_disambiguator import AIDisambiguator

    disambiguator = AIDisambiguator(self.workspace)
    ai_result = disambiguator.disambiguate(
        reference=ambiguous_ref,
        candidates=candidate_tables,
        sql_context=definition,
        parser_result=quality_result
    )

    if ai_result and ai_result.is_valid:
        # Merge AI result
        quality_result['sources'] = ai_result.sources
        quality_result['targets'] = ai_result.targets
        quality_result['confidence'] = ai_result.confidence
        quality_result['provenance']['primary_source'] = 'ai'
        quality_result['provenance']['ai_used'] = True

        # Track in database
        self._log_ai_usage(object_id, ai_result)
```

**Testing Checkpoint:**
- [ ] Unit test: `test_quality_aware_parser.py::test_ai_trigger_threshold`
- [ ] Integration test: Parse single SP with confidence <0.85

---

#### Task 1.3: Remove DualParser Wrapper
**File:** `lineage_v3/main.py` (modify ~10 lines)
**Effort:** 30 minutes

**Requirements:**
- [ ] Remove `from lineage_v3.parsers.dual_parser import DualParser`
- [ ] Replace with `from lineage_v3.parsers.quality_aware_parser import QualityAwareParser`
- [ ] Update parser instantiation: `parser = QualityAwareParser(workspace)`
- [ ] Remove DualParser-specific configuration/logging
- [ ] Verify no other files import DualParser

**Before:**
```python
from lineage_v3.parsers.dual_parser import DualParser
parser = DualParser(workspace)
```

**After:**
```python
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
parser = QualityAwareParser(workspace)
```

**Testing Checkpoint:**
- [ ] Smoke test: `python lineage_v3/main.py validate` (ensure no import errors)
- [ ] Integration test: Full parse run completes successfully

---

#### Task 1.4: Add Configuration Options
**File:** `lineage_v3/config.py` or environment-based (new or modify)
**Effort:** 30 minutes

**Requirements:**
- [ ] Add AI configuration constants:
  ```python
  # AI Disambiguation Configuration
  AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"
  AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.85"))
  AI_MIN_CONFIDENCE = float(os.getenv("AI_MIN_CONFIDENCE", "0.70"))
  AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))
  AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "10"))
  ```
- [ ] Add CLI arguments to `main.py`:
  - [ ] `--ai-enabled / --no-ai` (enable/disable AI feature)
  - [ ] `--ai-threshold <float>` (adjust confidence threshold, default 0.85)
- [ ] Document in `.env.template`:
  ```bash
  # Optional: AI Disambiguation Settings (defaults shown)
  # AI_ENABLED=true
  # AI_CONFIDENCE_THRESHOLD=0.85
  # AI_MIN_CONFIDENCE=0.70
  # AI_MAX_RETRIES=2
  # AI_TIMEOUT_SECONDS=10
  ```

**Testing Checkpoint:**
- [ ] Test CLI: `python lineage_v3/main.py run --parquet ... --no-ai` (AI disabled)
- [ ] Test CLI: `python lineage_v3/main.py run --parquet ... --ai-threshold 0.75`

---

### Day 2 - Testing & Documentation (6.5 hours)

#### Task 2.1: Create Unit Tests
**File:** `tests/test_ai_disambiguator.py` (new, ~200 lines)
**Effort:** 3 hours

**Requirements:**
- [ ] Test catalog validation:
  ```python
  def test_catalog_validation_rejects_nonexistent_table()
  def test_catalog_validation_accepts_valid_table()
  ```
- [ ] Test regex improvement validation:
  ```python
  def test_regex_improvement_rejects_worse_result()
  def test_regex_improvement_accepts_equal_or_better()
  ```
- [ ] Test query log validation:
  ```python
  def test_query_log_validation_boosts_confidence()
  def test_query_log_validation_no_boost_if_not_found()
  ```
- [ ] Test retry loop:
  ```python
  def test_retry_loop_succeeds_on_second_attempt()
  def test_retry_loop_fails_after_max_retries()
  ```
- [ ] Test fallback logic:
  ```python
  def test_fallback_to_parser_result_on_validation_failure()
  def test_fallback_to_parser_result_on_api_error()
  ```
- [ ] Test Azure OpenAI API integration (mocked):
  ```python
  def test_api_call_parses_json_response()
  def test_api_call_handles_timeout()
  def test_api_call_handles_rate_limit()
  ```

**Testing Checkpoint:**
- [ ] All unit tests pass: `pytest tests/test_ai_disambiguator.py -v`
- [ ] Coverage ≥90%: `pytest --cov=lineage_v3.parsers.ai_disambiguator tests/test_ai_disambiguator.py`

---

#### Task 2.2: Run Integration Tests
**Effort:** 2 hours

**Requirements:**
- [ ] Test on production snapshot with AI enabled:
  ```bash
  python lineage_v3/main.py run --parquet parquet_snapshots/ --ai-enabled --full-refresh
  ```
- [ ] Compare results against v3.6.0 baseline:
  ```bash
  python tests/parser_regression_test.py --compare baselines/baseline_20251028.json
  ```
- [ ] Verify acceptance criteria:
  - [ ] Zero regressions (no high-confidence SPs drop below 0.85)
  - [ ] ~39 SPs improve from ≤0.85 to higher confidence
  - [ ] Average confidence increases by ≥0.05 (0.800 → 0.850+)
  - [ ] Total high-confidence SPs ≥180 (was 163, target ~198)
- [ ] Measure cost and latency:
  - [ ] Cost per parse run <$1 (target ~$0.05-$0.08)
  - [ ] Average latency per SP <2 seconds
  - [ ] Total parse time reasonable (incremental mode)
- [ ] Capture new baseline:
  ```bash
  python tests/parser_regression_test.py --capture-baseline baselines/baseline_v3.7.0.json
  ```

**Testing Checkpoint:**
- [ ] Regression test PASSES
- [ ] Improvement metrics meet targets
- [ ] New baseline captured for v3.7.0

---

#### Task 2.3: Update Documentation
**Effort:** 1.5 hours

**Requirements:**
- [ ] Update [CLAUDE.md](../CLAUDE.md):
  - [ ] Change parser version to v3.7.0
  - [ ] Update AI Enhancement Status to "Phase 4 Complete - Production Deployed"
  - [ ] Update performance metrics (80.7% → 98% high-confidence)
  - [ ] Add AI configuration section to Quick Start Guide
- [ ] Update [docs/PARSER_EVOLUTION_LOG.md](PARSER_EVOLUTION_LOG.md):
  - [ ] Add v3.7.0 entry with:
    - Date, changes summary
    - Architecture decision (single parser + AI fallback)
    - Performance improvement (before/after metrics)
    - Lessons learned
- [ ] Update [README.md](../README.md):
  - [ ] Mention AI disambiguation feature
  - [ ] Update parser version and accuracy stats
  - [ ] Add link to AI_DISAMBIGUATION_SPEC.md
- [ ] Update [lineage_specs.md](../lineage_specs.md):
  - [ ] Mark spec version 2.2 as implemented (was "planned")
  - [ ] Update parser version to v3.7.0
  - [ ] Update confidence model table (Section 8)
- [ ] Create [docs/PHASE4_COMPLETION.md](PHASE4_COMPLETION.md):
  - [ ] Summary of changes
  - [ ] Before/after metrics
  - [ ] Cost analysis results
  - [ ] Production readiness checklist

**Testing Checkpoint:**
- [ ] All documentation links valid
- [ ] No broken references
- [ ] Version numbers consistent across all files

---

## Acceptance Criteria

**Phase 4 Complete When:**
- [ ] All code changes complete (AIDisambiguator, QualityAwareParser, main.py, config)
- [ ] All unit tests pass (≥90% coverage on AIDisambiguator)
- [ ] Integration tests show improvement:
  - [ ] ≥90% high-confidence coverage (target 98%)
  - [ ] Zero regressions (baseline SPs stay ≥0.85)
  - [ ] Average confidence increases ≥0.05
- [ ] Cost targets met:
  - [ ] Cost per parse run <$1
  - [ ] Annual projected cost ~$100-200
- [ ] Performance targets met:
  - [ ] Latency per SP <2 seconds
  - [ ] No significant slowdown in total parse time
- [ ] Documentation updated:
  - [ ] CLAUDE.md, README.md, PARSER_EVOLUTION_LOG.md
  - [ ] AI_DISAMBIGUATION_SPEC.md marked as implemented
  - [ ] New baseline captured

---

## Rollback Plan

**If Phase 4 implementation fails acceptance criteria:**

1. **Revert code changes:**
   ```bash
   git checkout feature/v3-implementation -- lineage_v3/parsers/ai_disambiguator.py
   git checkout feature/v3-implementation -- lineage_v3/parsers/quality_aware_parser.py
   git checkout feature/v3-implementation -- lineage_v3/main.py
   ```

2. **Disable AI feature:**
   ```bash
   # In .env
   AI_ENABLED=false
   ```

3. **Revert to v3.6.0 baseline:**
   - Parser falls back to regex baseline (confidence 0.50)
   - No AI calls made
   - Existing functionality preserved

**Rollback scenarios:**
- Accuracy drops below 80% (regressions detected)
- Cost exceeds $5 per parse run (budget overrun)
- API failure rate >10% (Azure service issues)
- Latency unacceptable (>5 seconds per SP)

---

## Production Deployment Checklist

**Before deploying to production:**
- [ ] All acceptance criteria met
- [ ] Code reviewed by team
- [ ] Unit tests pass (100%)
- [ ] Integration tests pass (zero regressions)
- [ ] Documentation updated and reviewed
- [ ] Azure OpenAI credentials secured in production `.env`
- [ ] Cost monitoring configured:
  - [ ] Azure spending alerts set ($20/month warning, $50/month critical)
  - [ ] Budget approved ($500/year conservative estimate)
- [ ] Feature flag configured (`AI_ENABLED=true` in production `.env`)
- [ ] Rollback plan tested and validated

**Production monitoring (first week):**
- [ ] Day 1: Check AI usage rate (~19% of SPs expected)
- [ ] Day 1: Monitor cost (should be ~$0.05-$0.08 per parse run)
- [ ] Day 3: Spot-check 10 AI-resolved SPs for accuracy
- [ ] Day 3: Review error logs (API failures, validation failures)
- [ ] Day 7: Calculate average confidence improvement
- [ ] Day 7: Validate latency metrics (<2 seconds per SP)
- [ ] Week 1 Report: Summarize findings, adjust if needed

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Azure API downtime | Low (99.9% SLA) | Medium | Graceful fallback to regex baseline |
| Cost overrun | Low | Low | Spending alerts at $20/50/month, feature flag for disable |
| Accuracy regression | Low | High | Regression tests, rollback plan |
| Latency issues | Low | Medium | Timeout handling (10s), API call optimization |
| Model deprecation | Medium (1-2 years) | Low | Prompt version control, easy model swap |

---

## Files Modified/Created Summary

### New Files (2)
1. `lineage_v3/parsers/ai_disambiguator.py` (~150 lines)
2. `tests/test_ai_disambiguator.py` (~200 lines)

### Modified Files (4-5)
1. `lineage_v3/parsers/quality_aware_parser.py` (+20 lines: AI trigger logic)
2. `lineage_v3/main.py` (-10 lines: Remove DualParser, use QualityAwareParser)
3. `lineage_v3/config.py` or equivalent (+20 lines: AI configuration)
4. `.env.template` (+5 lines: AI optional settings)
5. CLI argument parser (+10 lines: --ai-enabled, --ai-threshold flags)

### Documentation Updated (6)
1. `CLAUDE.md` (AI status, performance metrics)
2. `docs/PARSER_EVOLUTION_LOG.md` (v3.7.0 entry)
3. `README.md` (parser version, AI feature mention)
4. `lineage_specs.md` (mark v2.2 implemented, update confidence model)
5. `docs/AI_MODEL_EVALUATION.md` (Phase 4 completion notes)
6. `docs/PHASE4_COMPLETION.md` (new, summary report)

### Net Code Change
- Lines added: ~400 (AIDisambiguator + tests + config)
- Lines removed: ~210 (DualParser complexity)
- **Net: +190 lines** (25% increase in parser code)

---

## References

- **[docs/AI_DISAMBIGUATION_SPEC.md](AI_DISAMBIGUATION_SPEC.md)** - Complete implementation specification
- **[docs/AI_MODEL_EVALUATION.md](AI_MODEL_EVALUATION.md)** - Testing results (Phase 1-3)
- **[lineage_v3/ai_analyzer/README.md](../lineage_v3/ai_analyzer/README.md)** - Test artifacts and production prompt
- **[lineage_v3/ai_analyzer/production_prompt.txt](../lineage_v3/ai_analyzer/production_prompt.txt)** - Few-shot system prompt
- **[docs/PARSING_USER_GUIDE.md](PARSING_USER_GUIDE.md)** - SQL parsing best practices

---

**Last Updated:** 2025-10-31
**Status:** Ready to Start
**Target Completion:** 2025-11-02 (2 days)
**Assignee:** Development Team
