# AI Token Optimization Strategy

**Version:** 1.0
**Date:** 2025-11-02
**Author:** Claude Code Agent

## Overview

The AI disambiguator uses Azure OpenAI API for table reference resolution. Token costs are the primary operational expense, making optimization critical for scalability.

---

## Current Token Usage

### Per-Request Breakdown

```
Total Tokens per Request = System Prompt + User Prompt + Response

System Prompt:  ~300 tokens  (few-shot examples + instructions)
User Prompt:    ~800 tokens  (DDL snippet + candidates + formatting)
Response:       ~100 tokens  (JSON output)
─────────────────────────────────────────────────────────────
TOTAL:         ~1200 tokens per AI call
```

### Monthly Cost Projection (31 SPs needing AI)

```
Scenario: Weekly full parse (4x/month)

Token usage:
- 31 SPs × 1200 tokens = 37,200 tokens per run
- 4 runs/month = 148,800 tokens/month

Cost (gpt-4.1-nano at $0.30/1M input tokens):
- Input: 148,800 × $0.30 = $0.04/month
- Output: negligible
────────────────────────────────────────────
TOTAL: ~$0.05/month (VERY LOW)
```

**NOTE:** While current costs are minimal, optimization principles apply for:
1. Future scaling (more SPs, larger codebase)
2. Model upgrades (gpt-4-turbo, o1)
3. Higher parsing frequency
4. Multi-tenant deployments

---

## Optimization Strategies

### 1. Few-Shot Prompt Optimization

#### Current State: Fallback Prompt

```python
# ai_disambiguator.py line 116
"""You are a SQL dependency analyzer. Disambiguate ambiguous table references.

Return JSON:
{
  "resolved_table": "schema.table_name",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}
"""
# Tokens: ~50
```

#### Optimal Few-Shot Design

**Principles:**
- **2-3 examples maximum** (not 5-10, diminishing returns)
- **Diverse scenarios:** simple, complex, multi-candidate
- **Concise SQL snippets:** 3-5 lines, not full procedures
- **Target:** 200-400 tokens total

**Example Structure:**

```
System Prompt (~300 tokens):

"You are a SQL table disambiguation expert.

[RULES]
1. Use schema naming conventions (STAGING_*, CONSUMPTION_*, ADMIN)
2. Prefer explicit context clues (JOIN conditions, WHERE clauses)
3. Return confidence 0.85-0.95 based on evidence strength

[EXAMPLE 1 - Simple]
Ambiguous: DimAccount
Candidates: dbo.DimAccount, CONSUMPTION_FINANCE.DimAccount
Context: SELECT * FROM DimAccount WHERE AccountType = 'GL'
→ CONSUMPTION_FINANCE.DimAccount (confidence: 0.90, consumption layer usage)

[EXAMPLE 2 - Complex]
Ambiguous: FactTransaction
Candidates: STAGING_PRIMA.FactTransaction, CONSUMPTION_PRIMA.FactTransaction
Context: INSERT INTO FactTransaction SELECT * FROM STAGING_PRIMA.SourceData
→ STAGING_PRIMA.FactTransaction (confidence: 0.95, explicit staging load pattern)

Return JSON: {"resolved_table": "schema.table", "confidence": 0.90, "reasoning": "brief"}
"
```

**Token Budget:**
- Instructions: 100 tokens
- Rules: 50 tokens
- Examples (2x): 150 tokens
- Format spec: 50 tokens
- **TOTAL: ~350 tokens** (vs potential 800+ with verbose examples)

#### Pythonic Config-Driven Approach (RECOMMENDED)

**Why Config Over Text Files:**
- ✅ Type-safe with Pydantic validation
- ✅ Version-controlled (no separate .txt files)
- ✅ Testable (unit test example selection logic)
- ✅ Environment-aware (dev/prod examples)
- ✅ Integrated with existing settings system

**Pydantic Model Design:**

```python
# lineage_v3/config/settings.py

from pydantic import BaseModel, Field
from typing import List, Literal

class FewShotExample(BaseModel):
    """Single few-shot example for AI disambiguation."""
    ambiguous_ref: str = Field(..., description="Unqualified table name")
    candidates: List[str] = Field(..., description="Possible fully-qualified names")
    sql_context: str = Field(..., max_length=500, description="Minimal SQL snippet")
    resolved_table: str = Field(..., description="Correct resolution")
    confidence: float = Field(..., ge=0.85, le=0.95, description="Expected confidence")
    reasoning: str = Field(..., max_length=100, description="Brief explanation")

    class Config:
        json_schema_extra = {
            "example": {
                "ambiguous_ref": "DimAccount",
                "candidates": ["dbo.DimAccount", "CONSUMPTION_FINANCE.DimAccount"],
                "sql_context": "SELECT * FROM DimAccount WHERE AccountType = 'GL'",
                "resolved_table": "CONSUMPTION_FINANCE.DimAccount",
                "confidence": 0.90,
                "reasoning": "consumption layer usage pattern"
            }
        }

class AIDisambiguationSettings(BaseSettings):
    enabled: bool = Field(default=True)
    confidence_threshold: float = Field(default=0.90)
    min_confidence: float = Field(default=0.70)
    max_retries: int = Field(default=2)
    timeout_seconds: int = Field(default=10)

    # Few-shot examples (inline, versioned with code)
    few_shot_examples: List[FewShotExample] = Field(
        default_factory=lambda: [
            FewShotExample(
                ambiguous_ref="DimAccount",
                candidates=["dbo.DimAccount", "CONSUMPTION_FINANCE.DimAccount"],
                sql_context="SELECT * FROM DimAccount WHERE AccountType = 'GL'",
                resolved_table="CONSUMPTION_FINANCE.DimAccount",
                confidence=0.90,
                reasoning="consumption layer usage pattern"
            ),
            FewShotExample(
                ambiguous_ref="FactTransaction",
                candidates=["STAGING_PRIMA.FactTransaction", "CONSUMPTION_PRIMA.FactTransaction"],
                sql_context="INSERT INTO FactTransaction SELECT * FROM STAGING_PRIMA.SourceData",
                resolved_table="STAGING_PRIMA.FactTransaction",
                confidence=0.95,
                reasoning="explicit staging load pattern"
            ),
            FewShotExample(
                ambiguous_ref="DimDate",
                candidates=["dbo.DimDate", "CONSUMPTION_FINANCE.DimDate", "CONSUMPTION_PRIMA.DimDate"],
                sql_context="UPDATE DimDate SET IsHoliday = 1 WHERE CountryCode = 'US'",
                resolved_table="dbo.DimDate",
                confidence=0.88,
                reasoning="admin table in dbo schema"
            ),
        ],
        description="Few-shot examples for AI prompt (2-3 diverse cases)"
    )

    model_config = SettingsConfigDict(
        env_prefix='AI_',
        case_sensitive=False
    )
```

**AI Disambiguator Integration:**

```python
# lineage_v3/parsers/ai_disambiguator.py

def _build_system_prompt(self) -> str:
    """Build system prompt from config few-shot examples."""
    settings = self.settings  # AIDisambiguationSettings instance

    # Header
    prompt_parts = [
        "You are a SQL table disambiguation expert.",
        "",
        "[RULES]",
        "1. Use schema naming conventions (STAGING_*, CONSUMPTION_*, ADMIN, dbo)",
        "2. Prefer explicit context clues (JOIN, WHERE, INSERT INTO)",
        "3. Return confidence 0.85-0.95 based on evidence strength",
        "",
    ]

    # Add examples from config
    for i, example in enumerate(settings.few_shot_examples, start=1):
        prompt_parts.extend([
            f"[EXAMPLE {i}]",
            f"Ambiguous: {example.ambiguous_ref}",
            f"Candidates: {', '.join(example.candidates)}",
            f"Context: {example.sql_context}",
            f"→ {example.resolved_table} (confidence: {example.confidence:.2f}, {example.reasoning})",
            "",
        ])

    # Footer
    prompt_parts.extend([
        'Return JSON: {"resolved_table": "schema.table", "confidence": 0.90, "reasoning": "brief"}',
    ])

    return "\n".join(prompt_parts)

# Usage in disambiguate():
system_prompt = self._build_system_prompt()
# No need for fallback prompt or production_prompt.txt file
```

**Benefits Over Text Files:**

| Aspect | Config-Driven | Text File (production_prompt.txt) |
|--------|--------------|-----------------------------------|
| Type Safety | ✅ Pydantic validation | ❌ Manual parsing |
| Versioning | ✅ Git tracks with code | ⚠️ Separate file can drift |
| Testing | ✅ Unit test example logic | ❌ Hard to mock |
| Environment | ✅ Override with env vars | ❌ File-based only |
| Token Limit | ✅ Field validation (max_length=500) | ❌ No validation |
| Example Count | ✅ List length validation | ❌ Manual counting |
| IDE Support | ✅ Autocomplete, type hints | ❌ Plain text |

**Token Budget Enforcement:**

```python
# Automatic validation
class FewShotExample(BaseModel):
    sql_context: str = Field(..., max_length=500)  # ~125 tokens max
    reasoning: str = Field(..., max_length=100)    # ~25 tokens max

class AIDisambiguationSettings(BaseSettings):
    few_shot_examples: List[FewShotExample] = Field(
        ...,
        min_length=2,
        max_length=3,  # Enforce 2-3 examples only
        description="Few-shot examples (2-3 for optimal token usage)"
    )
```

**Testing Strategy:**

```python
# tests/test_ai_prompt_building.py
def test_system_prompt_token_budget():
    """Ensure system prompt stays under 400 tokens."""
    settings = AIDisambiguationSettings()  # Default examples
    disambiguator = AIDisambiguator(workspace, settings)

    system_prompt = disambiguator._build_system_prompt()
    token_count = len(system_prompt) // 4  # Rough estimate (4 chars = 1 token)

    assert token_count < 400, f"System prompt exceeds 400 tokens: {token_count}"
    assert len(settings.few_shot_examples) <= 3, "Too many examples"

def test_example_diversity():
    """Ensure examples cover different disambiguation scenarios."""
    settings = AIDisambiguationSettings()
    examples = settings.few_shot_examples

    # Check for schema diversity
    schemas = {ex.resolved_table.split('.')[0] for ex in examples}
    assert len(schemas) >= 2, "Examples should cover multiple schema types"

    # Check for operation diversity (SELECT, INSERT, UPDATE, etc.)
    operations = {ex.sql_context.split()[0].upper() for ex in examples}
    assert len(operations) >= 2, "Examples should cover different SQL operations"
```

---

### 2. DDL Cleaning (User Prompt Optimization)

#### Current State: Raw DDL

```python
# ai_disambiguator.py line 261
truncated_context = sql_context[:3000]  # Raw DDL, first 3000 chars

# Example raw DDL sent to AI:
"""
-- =============================================
-- Author:      John Smith
-- Create date: 2023-01-15
-- Description: Load dimensional account data
-- Modified:    2024-06-20 - Added error handling
-- =============================================
CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimAccount]
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets
    SET NOCOUNT ON;

    -- Variable declarations
    DECLARE @StartTime DATETIME = GETDATE();
    DECLARE @RowCount INT = 0;
    DECLARE @ErrorMessage NVARCHAR(4000);

    -- Business logic
    INSERT INTO DimAccount (AccountID, AccountName, ...)
    SELECT AccountID, AccountName, ...
    FROM STAGING_FINANCE.SourceAccounts
    WHERE IsActive = 1;

    SET @RowCount = @@ROWCOUNT;

    -- Error handling
    ...
END
"""
# Tokens: ~350-400 (with comments, whitespace, DECLARE statements)
```

#### Optimized: Cleaned DDL

```python
# quality_aware_parser.py already has preprocessor (lines 120-140):
# - Remove -- comments
# - Remove /* */ comments
# - Remove DECLARE statements
# - Normalize whitespace
# - Keep only essential SQL

# Clean DDL sent to AI:
"""
CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimAccount]
AS
BEGIN
SET NOCOUNT ON;
INSERT INTO DimAccount (AccountID, AccountName, ...)
SELECT AccountID, AccountName, ...
FROM STAGING_FINANCE.SourceAccounts
WHERE IsActive = 1;
END
"""
# Tokens: ~200-250 (30-40% reduction)
```

**Implementation:**

```python
# ai_disambiguator.py line 613 - BEFORE:
ai_result = disambiguator.disambiguate(
    reference=reference,
    candidates=candidates,
    sql_context=ddl,  # ❌ RAW DDL
    ...
)

# AFTER:
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
parser = QualityAwareParser(workspace)
cleaned_ddl = parser._preprocess_ddl(ddl)  # ✅ CLEANED DDL

ai_result = disambiguator.disambiguate(
    reference=reference,
    candidates=candidates,
    sql_context=cleaned_ddl[:3000],  # Truncate AFTER cleaning
    ...
)
```

**Token Savings:**
- Raw DDL: 800 tokens (avg)
- Cleaned DDL: 500 tokens (avg)
- **Savings: 300 tokens/call (37.5%)**

---

### 3. Smart Truncation

#### Current: Naive Character Truncation

```python
# ai_disambiguator.py line 261
truncated_context = sql_context[:3000]  # May cut mid-statement
```

**Problem:** Can break SQL syntax, lose critical table references at end.

#### Optimized: Statement-Aware Truncation

```python
def _smart_truncate(self, sql: str, max_chars: int = 3000) -> str:
    """
    Truncate SQL at statement boundary, not mid-statement.

    Prioritizes:
    1. Table references (FROM, JOIN, INSERT INTO, UPDATE, MERGE)
    2. Complete statements (don't cut in middle of SELECT)
    3. Most recent 3000 characters (reverse order)
    """
    # Find all statement boundaries
    statements = re.split(r';\s*', sql)

    # Build from end (most recent logic) within budget
    result = []
    current_length = 0

    for stmt in reversed(statements):
        stmt_length = len(stmt)
        if current_length + stmt_length <= max_chars:
            result.insert(0, stmt)
            current_length += stmt_length
        else:
            break

    return ';\n'.join(result)
```

**Benefit:** Preserve complete statements with table references instead of arbitrary cutoff.

---

## Implementation Roadmap

### Phase 1: DDL Cleaning (CURRENT PRIORITY)

**Goal:** Reduce user prompt tokens by 30-40%

**Steps:**
1. Modify `quality_aware_parser.py` line 613 to call preprocessor before AI
2. Run evaluation to verify zero regression
3. Measure token reduction in logs
4. Commit with performance comparison

**Pass Criteria:**
- ✅ AI confidence unchanged or improved
- ✅ Zero regressions (no objects ≥0.85 drop below 0.85)
- ✅ Token reduction >25%

### Phase 2: Config-Driven Few-Shot Optimization

**Goal:** Implement Pydantic-based few-shot examples in settings

**Steps:**
1. Analyze 10 successful AI disambiguations from evaluation logs (run_20251102_114143)
2. Extract 2-3 diverse, concise examples covering different scenarios
3. Add `FewShotExample` model to `lineage_v3/config/settings.py`
4. Update `AIDisambiguationSettings` with `few_shot_examples` field
5. Modify `ai_disambiguator.py` to build system prompt from config
6. A/B test: fallback prompt vs config-driven prompt
7. Measure accuracy improvement and token usage

**Pass Criteria:**
- ✅ AI confidence improves by ≥0.05
- ✅ System prompt tokens <400 (enforced via Pydantic validation)
- ✅ Reduction in retry rate
- ✅ Unit tests verify prompt building and token budget
- ✅ Examples cover diverse scenarios (2+ schemas, 2+ SQL operations)

### Phase 3: Smart Truncation

**Goal:** Preserve critical table references when truncating

**Steps:**
1. Implement statement-aware truncation
2. Test on long SPs (>5000 chars)
3. Verify no loss of table references
4. Measure impact on confidence

---

## Monitoring & Metrics

### Token Usage Tracking

```python
# ai_disambiguator.py - Add to response logging:
logger.info(
    f"AI call for {sp_name}: "
    f"prompt_tokens={response.usage.prompt_tokens}, "
    f"completion_tokens={response.usage.completion_tokens}, "
    f"total={response.usage.total_tokens}"
)
```

### Cost Tracking

```python
# Calculate cost per call (gpt-4.1-nano pricing):
INPUT_COST_PER_1M = 0.30  # $0.30/1M input tokens
OUTPUT_COST_PER_1M = 1.20  # $1.20/1M output tokens

cost_usd = (
    (prompt_tokens / 1_000_000) * INPUT_COST_PER_1M +
    (completion_tokens / 1_000_000) * OUTPUT_COST_PER_1M
)
```

### Optimization Metrics

Track in `evaluation_history`:
- `ai_prompt_tokens`: Input tokens per call
- `ai_completion_tokens`: Output tokens per call
- `ai_cost_estimate`: USD cost per call

**Dashboard Query:**

```sql
SELECT
    COUNT(*) as ai_calls,
    AVG(ai_prompt_tokens) as avg_prompt_tokens,
    SUM(ai_cost_estimate) as total_cost_usd,
    AVG(ai_confidence) as avg_confidence
FROM evaluation_history
WHERE run_id = 'run_20251102_114143'
  AND best_method = 'ai';
```

---

## Best Practices

### DO:
- ✅ Preprocess DDL to remove noise (comments, DECLARE, whitespace)
- ✅ Use 2-3 diverse few-shot examples
- ✅ Truncate at statement boundaries, not mid-statement
- ✅ Monitor token usage per call
- ✅ Evaluate changes with baseline comparison

### DON'T:
- ❌ Send raw DDL with comments to AI
- ❌ Use 5+ few-shot examples (diminishing returns)
- ❌ Truncate arbitrarily (breaks SQL syntax)
- ❌ Optimize without measuring impact
- ❌ Trade accuracy for token savings without evaluation

---

## Failed Experiments

### Phase 1 DDL Cleaning (REVERTED 2025-11-02)

**Hypothesis:** Sending `_preprocess_ddl()` output to AI would reduce tokens by 30-40% with no accuracy loss.

**Implementation:**
Changed `quality_aware_parser.py:257` to send `cleaned_ddl` (removes DECLARE, EXEC, comments, control flow) instead of raw DDL to AI.

**Evaluation Results (run_20251102_120914 vs run_20251102_114143):**
```
❌ Major AI Confidence Regressions:
   - 60 objects changed confidence
   - 17 objects dropped from 1.0 → 0.0 (total failure)
   - Avg AI confidence: 0.480 → 0.447 (regression)

❌ Zero Token Cost Reduction:
   - Both runs: $0.1720 (identical cost)
   - Expected: 30-40% reduction
   - Actual: 0% reduction
```

**Root Cause:**
The `_preprocess_ddl()` method is designed for SQLGlot parsing (which needs simple SQL), not AI disambiguation. It removes critical context:
- DECLARE statements → AI loses table variable type information
- EXEC calls → AI loses context about called procedures
- Control flow → AI loses conditional logic understanding

These removals break the AI's ability to understand ambiguous table references.

**Lesson Learned:**
AI and SQLGlot have **opposite** preprocessing needs:
- SQLGlot: Simple, clean SQL (fewer tokens, less context)
- AI: Full context, semantic information (more tokens, better understanding)

**Status:** REVERTED - Code returned to sending raw DDL to AI

**Alternative Approach:**
Create AI-specific preprocessing that removes only noise (comments, excess whitespace) while preserving semantic context (DECLARE, EXEC, control flow).

---

## Related Documentation

- [AI_DISAMBIGUATION_SPEC.md](AI_DISAMBIGUATION_SPEC.md) - Core AI implementation
- [PARSING_USER_GUIDE.md](PARSING_USER_GUIDE.md) - SQL preprocessing details
- [SUB_DL_OPTIMIZE_PARSING_SPEC.md](SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Evaluation process

---

**Last Updated:** 2025-11-02
**Next Review:** After Phase 1 DDL cleaning implementation
