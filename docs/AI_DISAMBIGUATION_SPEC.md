# AI-Assisted SQL Disambiguation Specification

**Version:** 1.0
**Date:** 2025-10-31
**Status:** Phase 4 Ready - Implementation Pending
**Integration Target:** Parser v3.6.0 → v3.7.0

---

## 1. Executive Summary

This specification documents the integration of Azure OpenAI-based disambiguation into the Vibecoding Data Lineage Parser to improve confidence scores for ambiguous table references in T-SQL stored procedures.

**Key Achievements (Phase 1-3 Testing):**
- Model: `gpt-4.1-nano` validated
- Accuracy: 91.7% (11/12 test cases, exceeds 90% threshold)
- Cost: ~$0.0006 per disambiguation (~$100/year for daily parsing)
- Hallucination Risk: Low (0% observed, closed-set problem)
- Fine-Tuning: Not recommended (few-shot sufficient, cost-prohibitive)

**Production Impact:**
- Current: 80.7% high-confidence parsing (163/202 SPs ≥0.85)
- Expected: 98% high-confidence parsing after AI integration
- Coverage: ~39 SPs (19%) eligible for AI disambiguation (confidence ≤ 0.85)

---

## 2. Architecture Decision

### 2.1. Parser Strategy

**Selected Approach: Single Parser + AI Fallback**

```
SQL DDL → QualityAwareParser → Confidence ≤ 0.85? → AI Disambiguator → Enhanced Result
                                        ↓ No (>0.85)
                                    Use Parser Result
```

**Rejected Alternatives:**
- ❌ **DualParser Architecture:** Removed for simplicity (-200 lines of code)
- ❌ **Microsoft Agent Framework:** Overkill for closed-set classification task
- ❌ **Fine-Tuned Model:** Cost ($4,400 setup + $1,705/year) not justified for marginal 3.3% gain

**Rationale:**
1. QualityAwareParser (SQLGlot + regex baseline) is most accurate parser
2. AI handles edge cases better than dual-parser cross-validation
3. Direct Azure OpenAI API simpler than Agent Framework (100 lines vs 500+)
4. Few-shot prompt achieves 91.7% accuracy without training

### 2.2. AI Framework

**Selected: Direct Azure OpenAI API**

```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)
```

**Not using Microsoft Agent Framework because:**
- Task is simple closed-set choice (pick from 2-5 candidate tables)
- Agent Framework designed for complex multi-agent workflows
- Direct API: 1-2 days implementation, no framework dependency
- Agent Framework: 5-7 days, 500+ lines, maintenance burden

---

## 3. AI Trigger Logic

### 3.1. When to Use AI

**Trigger Condition:** Parser confidence ≤ 0.85

```python
# After QualityAwareParser completes
if quality_result['confidence'] <= 0.85:
    # Invoke AI disambiguator
    ai_result = disambiguator.disambiguate(
        reference=ambiguous_ref,
        candidates=candidate_tables,
        sql_context=sp_definition,
        parser_result=quality_result
    )

    if ai_result.is_valid and ai_result.confidence >= 0.70:
        # Use AI result
        return merge_results(quality_result, ai_result)
    else:
        # Fallback to original parser result
        return quality_result
```

**Impact Analysis:**
- Total SPs: 202
- High confidence (>0.85): 163 SPs (80.7%) - **skip AI**
- Medium confidence (0.70-0.84): 15 SPs (7.4%) - **use AI**
- Low confidence (<0.70): 24 SPs (11.9%) - **use AI**
- **Total AI calls:** ~39 SPs (19% of total)

### 3.2. Configuration Options

```python
# config.py or .env
AI_CONFIDENCE_THRESHOLD = 0.85  # Parser confidence threshold to trigger AI
AI_MIN_CONFIDENCE = 0.70        # Minimum AI confidence to accept result
AI_MAX_RETRIES = 2              # Maximum retry attempts with refined prompts
AI_TIMEOUT_SECONDS = 10         # API timeout
AI_ENABLED = True               # Feature flag (disable for testing/cost control)
```

---

## 4. Validation & Retry Loop

### 4.1. Three-Layer Validation

**After AI returns result, validate in 3 layers:**

#### Layer 1: Catalog Validation
```python
def validate_catalog(resolved_table: str, workspace: DuckDBWorkspace) -> bool:
    """Check if resolved table exists in DuckDB objects catalog."""
    schema, table = resolved_table.split('.')
    query = """
        SELECT COUNT(*) FROM objects
        WHERE schema_name = ? AND object_name = ? AND object_type = 'Table'
    """
    result = workspace.conn.execute(query, [schema, table]).fetchone()
    return result[0] > 0
```

**Purpose:** Prevent hallucination - AI cannot invent tables not in metadata

#### Layer 2: Regex Quality Improvement Check
```python
def validate_regex_improvement(ai_result: AIResult, parser_result: dict) -> bool:
    """Verify AI result is better than regex baseline."""
    regex_sources = parser_result['quality']['regex_sources']
    regex_targets = parser_result['quality']['regex_targets']

    # AI must find equal or more dependencies than regex
    ai_sources_count = len(ai_result.sources)
    ai_targets_count = len(ai_result.targets)

    return (ai_sources_count >= len(regex_sources) and
            ai_targets_count >= len(regex_targets))
```

**Purpose:** Ensure AI improves upon regex baseline (not worse)

#### Layer 3: Query Log Cross-Validation (Optional)
```python
def validate_query_logs(ai_result: AIResult, sp_name: str, workspace: DuckDBWorkspace) -> float:
    """Check if AI-resolved tables appear in runtime query logs for this SP."""
    if not workspace.has_query_logs():
        return ai_result.confidence  # No boost if logs unavailable

    # Find DML queries executed by this SP
    matching_queries = workspace.find_queries_by_sp(sp_name)

    # Check if AI-resolved tables appear in query logs
    confirmed_tables = set()
    for table in ai_result.sources + ai_result.targets:
        if any(table in query.text for query in matching_queries):
            confirmed_tables.add(table)

    # Boost confidence if confirmed by logs
    if confirmed_tables:
        confirmation_rate = len(confirmed_tables) / (len(ai_result.sources) + len(ai_result.targets))
        if confirmation_rate >= 0.8:
            return min(0.95, ai_result.confidence + 0.05)  # Boost to 0.95

    return ai_result.confidence
```

**Purpose:** Cross-validate AI result with runtime execution evidence

### 4.2. Retry Loop with Refined Prompts

```python
def disambiguate_with_retry(reference: str, candidates: List[str],
                            sql_context: str, max_retries: int = 2):
    """Attempt AI disambiguation with retry logic."""

    for attempt in range(max_retries):
        # Call AI
        ai_response = call_azure_openai(reference, candidates, sql_context, attempt)

        # Validate
        if validate_catalog(ai_response['resolved_table'], workspace):
            if validate_regex_improvement(ai_response, parser_result):
                # Valid result - apply query log validation
                final_confidence = validate_query_logs(ai_response, sp_name, workspace)
                return AIResult(
                    resolved_table=ai_response['resolved_table'],
                    confidence=final_confidence,
                    validation_layers_passed=3
                )

        # Validation failed - retry with refined prompt
        if attempt < max_retries - 1:
            sql_context = refine_context(sql_context, ai_response)

    # All retries failed - fallback to parser result
    return None
```

**Retry Strategy:**
- Attempt 1: Standard few-shot prompt
- Attempt 2 (if validation fails): Add explicit context from failed validation
  - Example: "Note: Candidate X does not exist in metadata. Choose from: Y, Z"
- Max 2 attempts to avoid cost escalation

---

## 5. Few-Shot System Prompt (Production)

### 5.1. Prompt Structure

**Components:**
1. Task definition
2. Schema architecture rules (ETL patterns, special conventions)
3. 5 few-shot examples demonstrating key patterns
4. Decision framework with priority rules
5. Output format specification (JSON)
6. Confidence scoring guidance

**File:** `lineage_v3/ai_analyzer/production_prompt.txt` (5,031 characters, ~1,257 tokens)

### 5.2. Schema Architecture Rules

**Data Flow Patterns:**
1. **ETL Direction:** CONSUMPTION schemas load FROM STAGING schemas
2. **Raw Data Layer:** dbo schema contains raw ingested data
3. **Same-Schema Preference:** Procedures typically query own schema first (unless ETL)

**Special Schema Conventions:**
- `STAGING_FINANCE_COGNOS.*` - Cognos extracts (often `t_` prefix)
- `STAGING_CADENCE.*` - Cadence system data
- `CONSUMPTION_FINANCE.*` - Finance dimensions/facts
- `dbo.*` - Common utilities and raw data

### 5.3. Few-Shot Examples (5 patterns)

1. **ETL Pattern:** CONSUMPTION procedure sources from STAGING
2. **Cognos Table Pattern:** `t_` prefix → STAGING_FINANCE_COGNOS
3. **Same-Schema Reference:** Procedure queries own schema
4. **dbo Raw Data Layer:** STAGING extracts from dbo
5. **Context Clues:** TRUNCATE/explicit reference earlier in procedure

### 5.4. Confidence Scoring Guidance

```
Output format (JSON):
{
  "resolved_table": "schema.table_name",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}

Confidence scoring:
- 0.95-1.0: Explicit context (TRUNCATE, earlier qualified reference)
- 0.85-0.94: Clear ETL pattern or naming convention match
- 0.70-0.84: Logical inference from schema relationships
- Below 0.70: Uncertain, multiple valid interpretations
```

---

## 6. Integration Points

### 6.1. File Modifications

#### New File: `lineage_v3/parsers/ai_disambiguator.py` (~150 lines)

```python
class AIDisambiguator:
    """Azure OpenAI-based SQL table disambiguation with validation/retry."""

    def __init__(self, workspace: DuckDBWorkspace):
        self.client = AzureOpenAI(...)
        self.workspace = workspace
        self.system_prompt = self._load_prompt()

    def disambiguate(self, reference: str, candidates: List[str],
                     sql_context: str, parser_result: dict) -> Optional[AIResult]:
        """Main entry point - disambiguate with validation/retry."""
        return self._disambiguate_with_retry(reference, candidates, sql_context,
                                              parser_result, max_retries=2)

    def _disambiguate_with_retry(self, ...):
        """Internal retry loop with 3-layer validation."""
        # See Section 4.2 for implementation

    def _validate_catalog(self, resolved_table: str) -> bool:
        """Layer 1: Check table exists in metadata."""

    def _validate_regex_improvement(self, ai_result: AIResult, parser_result: dict) -> bool:
        """Layer 2: Verify AI improves upon regex baseline."""

    def _validate_query_logs(self, ai_result: AIResult, sp_name: str) -> float:
        """Layer 3: Cross-validate with runtime query logs."""
```

#### Modified File: `lineage_v3/parsers/quality_aware_parser.py` (~20 line addition)

```python
# In parse_stored_procedure() method, after confidence calculation:

if quality_result['confidence'] <= 0.85 and AI_ENABLED:
    from lineage_v3.parsers.ai_disambiguator import AIDisambiguator

    disambiguator = AIDisambiguator(self.workspace)
    ai_result = disambiguator.disambiguate(
        reference=ambiguous_ref,
        candidates=candidate_tables,
        sql_context=definition,
        parser_result=quality_result
    )

    if ai_result and ai_result.is_valid:
        # Merge AI result into quality result
        quality_result['sources'] = ai_result.sources
        quality_result['targets'] = ai_result.targets
        quality_result['confidence'] = ai_result.confidence
        quality_result['provenance']['primary_source'] = 'ai'
        quality_result['provenance']['ai_used'] = True
```

#### Modified File: `lineage_v3/main.py` (~10 line removal)

```python
# REMOVE DualParser wrapper

# Before (v3.6.0):
from lineage_v3.parsers.dual_parser import DualParser
parser = DualParser(workspace)

# After (v3.7.0):
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
parser = QualityAwareParser(workspace)
```

**Impact:** -200 lines removed (DualParser complexity), +150 lines added (AIDisambiguator), net -50 lines

### 6.2. Database Schema Updates

**DuckDB workspace already has AI tracking columns:**

```sql
-- In parser_comparison_log table (already exists)
ai_used BOOLEAN,                -- Was AI invoked for this SP?
ai_sources_found INTEGER,       -- Number of sources AI resolved
ai_targets_found INTEGER,       -- Number of targets AI resolved
ai_confidence REAL              -- AI confidence score
```

**No schema changes needed** - AI columns already prepared in v3.6.0

---

## 7. Cost & Performance

### 7.1. Cost Analysis

**Per Disambiguation:**
- Tokens: ~1,581 (includes few-shot prompt)
- Cost: ~$0.0006 (gpt-4.1-nano pricing)

**Full Parse Run (200 SPs):**
- Eligible SPs (confidence ≤0.85): 39 SPs (19%)
- Avg disambiguations per SP: 2-3
- Total AI calls: ~80-120 disambiguations
- **Total cost per run: $0.05-$0.08** (negligible)

**Annual Cost (Daily Parsing):**
- Runs per year: 365
- **Annual cost: ~$100**
- DBA time saved: ~$1,845/year
- **ROI: 18x return on investment**
- Break-even: <2 weeks

### 7.2. Performance Targets

| Metric | Target | Expected |
|--------|--------|----------|
| **Accuracy** | ≥80% | 91.7% ✅ |
| **High-Confidence Coverage** | ≥90% | 98% ✅ |
| **Cost per Parse Run** | <$1 | $0.05-$0.08 ✅ |
| **Latency per SP** | <2 seconds | <1 second ✅ |
| **API Availability** | ≥99.5% | Azure SLA 99.9% ✅ |

---

## 8. Risk Assessment

### 8.1. Hallucination Risk: LOW ✅

**Why Low:**
- Closed-set problem (AI chooses from provided candidates, cannot invent tables)
- 3-layer validation prevents hallucinated results from being used
- 0% hallucination observed in 13 test cases
- Fallback to regex baseline if validation fails

**Mitigation:**
- Catalog validation rejects tables not in metadata
- Regex improvement check ensures AI doesn't worsen baseline
- Query log validation confirms against runtime evidence

### 8.2. Cost Overrun Risk: LOW ✅

**Worst-Case Scenario:**
- 10x usage spike (1,200 disambiguations instead of 120)
- Cost: ~$0.72 per run, ~$263/year
- **Still 7x cheaper than DBA manual work ($1,845/year saved)**

**Mitigation:**
- Set spending alerts at $20/month, $50/month
- AI feature flag for emergency disable
- Budget $500/year (conservative, 5x headroom)

### 8.3. Technical Risk: MEDIUM ⚠️

**Risks:**
- Azure OpenAI API downtime (SLA 99.9%, ~8 hours/year)
- Model deprecation (gpt-4.1-nano replaced)
- Schema changes invalidate few-shot examples

**Mitigation:**
- Graceful fallback to regex baseline on API failure
- Version control prompt, easy to update on model change
- Few-shot prompt easier to update than fine-tuned model (5 min vs 40 hours)

---

## 9. Testing Strategy

### 9.1. Unit Tests (`tests/test_ai_disambiguator.py`)

```python
def test_catalog_validation():
    """Test Layer 1: Catalog validation rejects nonexistent tables."""

def test_regex_improvement_validation():
    """Test Layer 2: AI must improve upon regex baseline."""

def test_query_log_validation():
    """Test Layer 3: Confidence boost from query log confirmation."""

def test_retry_logic():
    """Test retry loop with refined prompts."""

def test_fallback_on_validation_failure():
    """Test fallback to parser result when AI validation fails."""
```

### 9.2. Integration Tests

```bash
# Test on production snapshot with AI enabled
python lineage_v3/main.py run --parquet parquet_snapshots/ --ai-enabled

# Compare results against v3.6.0 baseline
python tests/parser_regression_test.py --compare baselines/baseline_20251028.json

# Verify:
# - Zero regressions (high-confidence SPs stay ≥0.85)
# - ~39 SPs improve from ≤0.85 to higher confidence
# - Average confidence increases
```

### 9.3. Acceptance Criteria

**Phase 4 Implementation Complete When:**
- ✅ Unit tests pass (100% coverage on AIDisambiguator)
- ✅ Integration tests show ≥90% high-confidence coverage
- ✅ Zero regressions in baseline SPs
- ✅ Average confidence increases by ≥0.05
- ✅ Cost per parse run <$1
- ✅ Documentation updated (CLAUDE.md, PARSER_EVOLUTION_LOG.md)

---

## 10. Implementation Roadmap

### 10.1. Phase 4 Tasks (1-2 days)

**Day 1 - Core Implementation:**
1. Create `lineage_v3/parsers/ai_disambiguator.py` (~150 lines)
   - AIDisambiguator class with retry/validation logic
   - 3-layer validation methods
   - Azure OpenAI client integration
2. Modify `lineage_v3/parsers/quality_aware_parser.py` (~20 lines)
   - Add AI trigger logic (confidence ≤ 0.85)
   - Integrate AIDisambiguator
3. Modify `lineage_v3/main.py` (~10 lines removed)
   - Remove DualParser wrapper
   - Use only QualityAwareParser

**Day 2 - Testing & Documentation:**
4. Create unit tests (`tests/test_ai_disambiguator.py`)
   - Test all 3 validation layers
   - Test retry loop
   - Test fallback logic
5. Run integration tests
   - Full parse with AI enabled
   - Regression test against baseline
   - Measure improvement
6. Update documentation
   - CLAUDE.md (architecture decision)
   - PARSER_EVOLUTION_LOG.md (v3.7.0 entry)
   - README.md (AI feature description)

### 10.2. Timeline

| Task | Effort | Owner | Dependencies |
|------|--------|-------|--------------|
| Create AIDisambiguator | 4 hours | Dev | Production prompt ready ✅ |
| Modify QualityAwareParser | 1 hour | Dev | AIDisambiguator complete |
| Remove DualParser | 30 min | Dev | QualityAwareParser updated |
| Create unit tests | 3 hours | Dev | AIDisambiguator complete |
| Run integration tests | 2 hours | Dev | All code changes complete |
| Update documentation | 2 hours | Dev | Testing complete |
| **Total** | **12.5 hours** | | **~1.5 days** |

### 10.3. Deployment Checklist

**Before Production:**
- [ ] All unit tests pass
- [ ] Integration tests show improvement
- [ ] Zero regressions confirmed
- [ ] Cost monitoring configured (Azure alerts at $20/month)
- [ ] API credentials secured in `.env`
- [ ] Feature flag added (easy disable if needed)
- [ ] Documentation updated

**Production Monitoring (First Week):**
- [ ] Track AI usage rate (should be ~19% of SPs)
- [ ] Monitor cost (should be <$1 per parse run)
- [ ] Check accuracy (spot-check AI-resolved SPs)
- [ ] Validate latency (should be <2 seconds per SP)
- [ ] Review error logs (API failures, validation failures)

---

## 11. Configuration Reference

### 11.1. Environment Variables

```bash
# .env file
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### 11.2. Runtime Configuration

```python
# config.py or environment-based
AI_ENABLED = True                  # Master switch (disable for testing)
AI_CONFIDENCE_THRESHOLD = 0.85     # Parser confidence to trigger AI
AI_MIN_CONFIDENCE = 0.70           # Minimum AI confidence to accept
AI_MAX_RETRIES = 2                 # Retry attempts with refined prompts
AI_TIMEOUT_SECONDS = 10            # API call timeout
AI_CACHE_ENABLED = False           # Future: Cache common patterns (Phase 5)
```

### 11.3. CLI Flags

```bash
# Enable AI (default)
python lineage_v3/main.py run --parquet parquet_snapshots/ --ai-enabled

# Disable AI (for testing/cost control)
python lineage_v3/main.py run --parquet parquet_snapshots/ --no-ai

# Adjust AI threshold (default 0.85)
python lineage_v3/main.py run --parquet parquet_snapshots/ --ai-threshold 0.75
```

---

## 12. Maintenance & Updates

### 12.1. Prompt Updates (Schema Changes)

**When new schemas added or conventions change:**

1. Edit `lineage_v3/ai_analyzer/production_prompt.txt`
2. Update schema architecture rules or add 6th few-shot example
3. Re-run Phase 3 tests to validate accuracy
4. Document in PARSER_EVOLUTION_LOG.md
5. **Time:** 5 minutes to 1 hour (vs 40 hours for fine-tuned model retraining)

### 12.2. Model Upgrades

**If Azure deprecates gpt-4.1-nano:**

1. Update `.env` with new model deployment name
2. Re-run Phase 3 tests to validate accuracy
3. Adjust confidence thresholds if needed
4. Update cost estimates in documentation
5. **Time:** 1-2 days

### 12.3. Monitoring Metrics

**Track weekly in production:**
- AI usage rate (% of SPs using AI)
- AI accuracy (spot-check 10 random AI-resolved SPs)
- Cost per parse run
- Average confidence improvement
- API failure rate

**Red flags:**
- AI usage >30% (unexpected increase in low-confidence SPs)
- Cost >$5 per parse run (usage spike or rate limit issue)
- Accuracy <80% (model drift or schema changes)
- API failure rate >1% (Azure service degradation)

---

## 13. Future Enhancements (Phase 5+)

### 13.1. Caching Common Patterns

**Goal:** Reduce AI calls by 50-70%

```python
# Cache frequently disambiguated patterns
cache = {
    ("GL_Staging", "CONSUMPTION_FINANCE"): "STAGING_CADENCE.GL_Staging",
    ("DimCustomers", "CONSUMPTION_POWERBI"): "CONSUMPTION_FINANCE.DimCustomers"
}
```

**Benefit:** ~$30-50/year cost savings, faster parsing

### 13.2. Batch API Calls

**Goal:** Send multiple disambiguations in single API call

**Benefit:** 20-30% cost reduction (avoid per-call overhead)

**Complexity:** Requires custom prompt engineering for batch format

### 13.3. Model Upgrade to gpt-4o

**Trigger:** If accuracy drops below 80% or new use cases emerge

**Trade-off:** 3x cost increase ($0.002 per disambiguation vs $0.0006)

**Expected:** 91.7% → 95%+ accuracy

---

## 14. References

### 14.1. Documentation

- **Testing Results:** [docs/AI_MODEL_EVALUATION.md](AI_MODEL_EVALUATION.md)
- **Cost Analysis:** [lineage_v3/ai_analyzer/COST_ANALYSIS.md](../lineage_v3/ai_analyzer/COST_ANALYSIS.md)
- **Hallucination Risk:** [lineage_v3/ai_analyzer/HALLUCINATION_ANALYSIS.md](../lineage_v3/ai_analyzer/HALLUCINATION_ANALYSIS.md)
- **Fine-Tuning Decision:** [lineage_v3/ai_analyzer/TRAINING_DECISION.md](../lineage_v3/ai_analyzer/TRAINING_DECISION.md)
- **Production Prompt:** [lineage_v3/ai_analyzer/production_prompt.txt](../lineage_v3/ai_analyzer/production_prompt.txt)

### 14.2. Test Scripts

- **Phase 1 (Smoke Test):** [lineage_v3/ai_analyzer/test_azure_openai.py](../lineage_v3/ai_analyzer/test_azure_openai.py)
- **Phase 2 (Zero-Shot):** [lineage_v3/ai_analyzer/test_azure_openai_phase2.py](../lineage_v3/ai_analyzer/test_azure_openai_phase2.py)
- **Phase 3 (Few-Shot):** [lineage_v3/ai_analyzer/test_azure_openai_phase3.py](../lineage_v3/ai_analyzer/test_azure_openai_phase3.py)
- **Test Dataset:** [lineage_v3/ai_analyzer/phase2_test_dataset.json](../lineage_v3/ai_analyzer/phase2_test_dataset.json)

### 14.3. External Resources

- **Azure OpenAI:** https://learn.microsoft.com/azure/ai-services/openai/
- **Model Pricing:** https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/
- **SQLGlot Parser:** https://sqlglot.com/

---

**Last Updated:** 2025-10-31
**Status:** Phase 4 Ready - Implementation Pending
**Version:** 1.0
**Target:** Parser v3.7.0
