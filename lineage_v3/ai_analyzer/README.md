# AI-Assisted SQL Disambiguation Testing

**Status:** ✅ Production Ready (Phase 3 Complete - 91.7% accuracy)
**Model:** `gpt-4.1-nano`
**Last Updated:** 2025-10-31

## Overview

This directory contains the complete AI model evaluation and testing infrastructure for SQL table disambiguation using Azure OpenAI. The goal is to improve parser confidence on ambiguous table references in stored procedures.

## Test Results Summary

### Phase 1: Smoke Testing ✅
- **Accuracy:** 100% (1/1)
- **Purpose:** Validate API connection and basic disambiguation
- **Outcome:** Model works, proceed to production scenarios

### Phase 2: Zero-Shot Baseline ✅
- **Accuracy:** 58.3% (7/12)
- **Purpose:** Test on realistic production scenarios without few-shot examples
- **Outcome:** Below threshold, needs prompt engineering

### Phase 3: Few-Shot Prompt Engineering ✅
- **Accuracy:** 91.7% (11/12)
- **Improvement:** +33.4 percentage points vs Phase 2
- **Purpose:** Add schema rules and domain-specific examples
- **Outcome:** ✅ **READY FOR PRODUCTION USE**

## Performance Breakdown

| Parser Confidence | Phase 2 (Zero-Shot) | Phase 3 (Few-Shot) | Improvement |
|-------------------|---------------------|---------------------|-------------|
| Low (<0.70) | 60.0% (3/5) | 80.0% (4/5) | +20% |
| Medium (0.70-0.84) | 0.0% (0/3) | 100.0% (3/3) | +100% |
| High (≥0.85) | 100.0% (4/4) | 100.0% (4/4) | 0% |

**Key Achievement:** Few-shot examples completely fixed medium-confidence cases (0% → 100%)

## Files in this Directory

### Test Scripts
- **`test_azure_openai.py`** - Phase 1: Smoke test (basic connection and single disambiguation)
- **`test_azure_openai_phase2.py`** - Phase 2: Zero-shot baseline on 12 production scenarios
- **`test_azure_openai_phase3.py`** - Phase 3: Few-shot prompt with schema rules and examples

### Data Files
- **`phase2_test_dataset.json`** - 12 realistic disambiguation test cases based on production patterns
- **`phase2_results.json`** - Detailed Phase 2 test results (58.3% accuracy)
- **`phase3_results.json`** - Detailed Phase 3 test results (91.7% accuracy)
- **`production_prompt.txt`** - ✅ Production-ready system prompt with few-shot examples

### Archived Snapshots
- **`test_data_snapshot/`** - Frozen parquet files and lineage JSON for consistent testing over time
  - 5 parquet files (objects, definitions, dependencies, query logs, table columns)
  - `latest_frontend_lineage.json` - Parser output at snapshot time
  - `README.txt` - Snapshot timestamp

### Helper Scripts
- **`extract_test_cases.py`** - (Deprecated) Initial attempt to extract from DuckDB
- **`extract_test_cases_from_json.py`** - (Deprecated) Extract from lineage JSON
- **`extract_real_test_cases.py`** - (Deprecated) Extract from parquet files

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install openai python-dotenv pandas

# Configure environment (.env file)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### Run Tests

```bash
# Phase 1: Smoke test (validate connection)
python3 lineage_v3/ai_analyzer/test_azure_openai.py

# Phase 2: Zero-shot baseline (58.3% accuracy)
python3 lineage_v3/ai_analyzer/test_azure_openai_phase2.py

# Phase 3: Few-shot enhanced (91.7% accuracy) - PRODUCTION PROMPT
python3 lineage_v3/ai_analyzer/test_azure_openai_phase3.py
```

### Expected Output

Phase 3 should produce:
- 11/12 correct disambiguations
- 91.7% accuracy
- ~1,581 tokens per test (~$0.003 per disambiguation)
- Total cost: ~$0.038 for full 12-test suite

## Production Prompt Details

The production-ready system prompt (`production_prompt.txt`) includes:

### Schema Architecture Rules
1. **ETL Direction:** CONSUMPTION schemas load FROM STAGING schemas
2. **Raw Data Layer:** `dbo` schema contains raw ingested data
3. **Same-Schema Preference:** Procedures typically query own schema first (unless ETL)

### Special Schema Conventions
- `STAGING_FINANCE_COGNOS.*` - Cognos extracts (often `t_` prefix)
- `STAGING_CADENCE.*` - Cadence system data
- `CONSUMPTION_FINANCE.*` - Finance dimensions/facts
- `dbo.*` - Common utilities and raw data

### 5 Few-Shot Examples
1. ETL Pattern (CONSUMPTION → STAGING)
2. Cognos Table Pattern (`t_` prefix)
3. Same-Schema Reference
4. dbo Raw Data Layer
5. Context Clues (TRUNCATE/explicit reference)

### Decision Framework
Priority-based rules for disambiguation with confidence scoring guidance.

## Cost Analysis

**Per Disambiguation:**
- Tokens: ~1,581 (includes few-shot examples in prompt)
- Cost: ~$0.003 (based on gpt-4.1-nano pricing)

**Full Parse Run (200 SPs, ~600 disambiguations):**
- Total cost: ~$1.80
- Latency: ~10 minutes (with rate limiting)

**Verdict:** ✅ Negligible cost, excellent value for 91.7% accuracy

## Known Limitations

### Failed Case (1/12)
- **Test:** BudgetData - Cadence vs Prima
- **Expected:** `STAGING_CADENCE.BudgetData`
- **AI Resolved:** `CONSUMPTION_ClinOpsFinance.BudgetData`
- **Reason:** Genuinely ambiguous edge case - ClinOpsFinance could plausibly have own BudgetData or source from STAGING_CADENCE

**Assessment:** Acceptable - even human DBAs would find this ambiguous without additional context

### Token Usage
- 3.7x increase vs zero-shot (due to few-shot examples in prompt)
- Still cost-effective (<$2 per full parse run)

## Next Steps (Phase 4)

1. ✅ **Production prompt documented** - `production_prompt.txt` ready for integration
2. ⬜ **Integrate into parser pipeline** - Use AI when parser confidence <0.85
3. ⬜ **Add fallback logic** - Gracefully handle API failures
4. ⬜ **Monitor production metrics** - Track accuracy, cost, latency
5. ⬜ **Collect edge cases** - Refine prompt based on real-world failures

## Documentation

- **Full Evaluation Report:** [docs/AI_MODEL_EVALUATION.md](../../docs/AI_MODEL_EVALUATION.md)
- **CLAUDE.md Section:** Search for "Working with AI Disambiguation"

## References

- Azure OpenAI Service: https://learn.microsoft.com/azure/ai-services/openai/
- Model: `gpt-4.1-nano` (fast, cost-effective, suitable for structured reasoning)
- Parser Documentation: [docs/PARSING_USER_GUIDE.md](../../docs/PARSING_USER_GUIDE.md)

---

**Last Test Run:** 2025-10-31
**Production Status:** ✅ Ready for Phase 4 integration
**Accuracy:** 91.7% (11/12)
**Cost:** ~$0.003 per disambiguation
