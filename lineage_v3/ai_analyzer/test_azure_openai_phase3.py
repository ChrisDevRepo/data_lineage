"""
Azure OpenAI Phase 3 Testing - Few-Shot Prompt Engineering
===========================================================

Purpose: Test AI disambiguation with enhanced few-shot system prompt to improve
accuracy from 58.3% baseline to ≥80% target.

Usage:
    python lineage_v3/ai_analyzer/test_azure_openai_phase3.py
"""

import os
import json
import time
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Azure OpenAI Configuration
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4.1-nano")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-nano")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# Test dataset (same as Phase 2)
TEST_DATASET = "lineage_v3/ai_analyzer/phase2_test_dataset.json"

# Enhanced system prompt with few-shot examples
ENHANCED_SYSTEM_PROMPT = """You are a SQL dependency analyzer specialized in disambiguating ambiguous table references in T-SQL stored procedures for an Azure Synapse data warehouse.

## Schema Architecture Rules

**Data Flow Patterns:**
1. **ETL Direction:** CONSUMPTION schemas load data FROM STAGING schemas
   - Example: `CONSUMPTION_FINANCE` procedures source from `STAGING_FINANCE` or `STAGING_CADENCE`

2. **Raw Data Layer:** `dbo` schema contains raw ingested data
   - STAGING procedures extract FROM `dbo` tables

3. **Same-Schema Preference:** Procedures typically query tables in their own schema first
   - Exception: When loading/transforming data (ETL pattern)

**Special Schema Conventions:**
- `STAGING_FINANCE_COGNOS.*` - Cognos system extracts (often prefixed with `t_`)
- `STAGING_CADENCE.*` - Cadence system data
- `STAGING_PRIMA.*` - Prima system data
- `CONSUMPTION_FINANCE.*` - Finance dimension/fact tables (Dim*, Fact*)
- `CONSUMPTION_POWERBI.*` - Power BI reporting tables
- `CONSUMPTION_ClinOpsFinance.*` - Clinical operations finance integration
- `dbo.*` - Common utilities (ErrorLog, logging tables) and raw data

## Few-Shot Examples

### Example 1: ETL Pattern (CONSUMPTION loads FROM STAGING)
```sql
CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimAccount] AS
BEGIN
    MERGE DimAccount AS target
    USING AccountHierarchy AS source  -- AMBIGUOUS
    ON target.AccountCode = source.AccountCode;
END
```
**Candidates:** STAGING_FINANCE.AccountHierarchy, CONSUMPTION_FINANCE.AccountHierarchy, dbo.AccountHierarchy
**Resolution:** `STAGING_FINANCE.AccountHierarchy`
**Reasoning:** CONSUMPTION procedure loading dimension follows ETL pattern - sources from STAGING schema, not same schema.

### Example 2: Cognos Table Pattern
```sql
CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimCompanyKoncern] AS
BEGIN
    SELECT Company, koncern
    FROM t_Company_filter  -- AMBIGUOUS (t_ prefix indicates Cognos)
    WHERE IsActive = 1;
END
```
**Candidates:** STAGING_FINANCE_COGNOS.t_Company_filter, STAGING_FINANCE.t_Company_filter, dbo.t_Company_filter
**Resolution:** `STAGING_FINANCE_COGNOS.t_Company_filter`
**Reasoning:** Tables with `t_` prefix typically come from Cognos extracts in STAGING_FINANCE_COGNOS schema.

### Example 3: Same-Schema Reference (within schema boundary)
```sql
CREATE PROCEDURE [CONSUMPTION_POWERBI].[spLoadGLReport] AS
BEGIN
    SELECT AccountCode, SUM(Amount)
    FROM FactGL  -- AMBIGUOUS
    GROUP BY AccountCode;
END
```
**Candidates:** CONSUMPTION_FINANCE.FactGL, CONSUMPTION_POWERBI.FactGL, dbo.FactGL
**Resolution:** `CONSUMPTION_POWERBI.FactGL`
**Reasoning:** Procedure is in POWERBI schema, querying own schema's table for reporting (not loading from another schema).

### Example 4: dbo Raw Data Layer
```sql
CREATE PROCEDURE [STAGING_FINANCE].[spExtractCustomerData] AS
BEGIN
    INSERT INTO STAGING_FINANCE.CustomerStaging
    SELECT * FROM CustomerMaster  -- AMBIGUOUS
    WHERE ModifiedDate > GETDATE() - 1;
END
```
**Candidates:** STAGING_FINANCE.CustomerMaster, dbo.CustomerMaster, CONSUMPTION_FINANCE.CustomerMaster
**Resolution:** `dbo.CustomerMaster`
**Reasoning:** STAGING procedure extracting data follows ETL pattern - sources from dbo (raw data layer), not same schema.

### Example 5: Context Clues (TRUNCATE/explicit reference)
```sql
CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadFactGLSAP] AS
BEGIN
    TRUNCATE TABLE STAGING_CADENCE.GL_Staging;  -- Explicit reference

    INSERT INTO FactGLSAP (AccountID, Amount)
    SELECT a.AccountID, g.Amount
    FROM GL_Staging g  -- AMBIGUOUS - same table referenced above
    INNER JOIN DimAccount a ON g.AccountCode = a.AccountCode;
END
```
**Candidates:** STAGING_CADENCE.GL_Staging, STAGING_FINANCE.GL_Staging, dbo.GL_Staging
**Resolution:** `STAGING_CADENCE.GL_Staging`
**Reasoning:** Same procedure explicitly references STAGING_CADENCE.GL_Staging in TRUNCATE - unqualified reference likely same table.

## Decision Framework

When disambiguating, follow this priority:

1. **Check for explicit context** - Look for same table referenced with schema qualifier elsewhere in procedure
2. **Identify procedure type:**
   - CONSUMPTION loading data → Source from STAGING
   - STAGING extracting data → Source from dbo
   - CONSUMPTION querying data → Use same schema
3. **Apply naming patterns:**
   - `t_` prefix → STAGING_FINANCE_COGNOS
   - Dim*/Fact* → CONSUMPTION_* schemas
   - ErrorLog, utility tables → dbo
4. **Cross-schema patterns:**
   - CONSUMPTION_ClinOpsFinance → May join STAGING_CADENCE (budget data)
   - CONSUMPTION_POWERBI → May join CONSUMPTION_FINANCE (dimensions)

## Output Format

Return JSON with this structure:
{
  "resolved_table": "schema.table_name",
  "confidence": 0.95,
  "reasoning": "Brief explanation referencing rules above"
}

**Confidence scoring:**
- 0.95-1.0: Explicit context (TRUNCATE, earlier qualified reference)
- 0.85-0.94: Clear ETL pattern or naming convention match
- 0.70-0.84: Logical inference from schema relationships
- Below 0.70: Uncertain, multiple valid interpretations
"""


def load_test_dataset():
    """Load Phase 2 test dataset."""
    with open(TEST_DATASET, 'r') as f:
        return json.load(f)


def create_user_prompt(test_case):
    """Generate user prompt for a specific test case."""
    candidates_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(test_case['candidates'])])

    prompt = f"""
SQL Context:
```sql
{test_case['sql_context']}
```

Ambiguous Reference: "{test_case['ambiguous_reference']}"

Candidate Tables:
{candidates_str}

Question: Which table does "{test_case['ambiguous_reference']}" refer to?
"""
    return prompt


def call_ai_disambiguation(client, test_case):
    """Call Azure OpenAI with enhanced few-shot prompt."""
    user_prompt = create_user_prompt(test_case)

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": ENHANCED_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=500,
            temperature=0.0,  # Deterministic
            model=DEPLOYMENT
        )

        result = response.choices[0].message.content
        tokens = response.usage.total_tokens

        # Parse JSON response
        try:
            ai_response = json.loads(result)
        except json.JSONDecodeError:
            ai_response = {"raw_response": result, "error": "Invalid JSON"}

        return ai_response, tokens

    except Exception as e:
        return {"error": str(e)}, 0


def evaluate_result(test_case, ai_response):
    """Evaluate AI response against expected resolution."""
    if "error" in ai_response:
        return {
            "correct": False,
            "ai_confidence": 0.0,
            "parser_confidence": test_case['parser_confidence'],
            "status": "ERROR",
            "error": ai_response.get("error", "Unknown error")
        }

    resolved_table = ai_response.get("resolved_table", "").strip()
    expected_table = test_case['expected_resolution'].strip()

    correct = (resolved_table.lower() == expected_table.lower())

    return {
        "correct": correct,
        "ai_confidence": ai_response.get("confidence", 0.0),
        "ai_resolved": resolved_table,
        "expected": expected_table,
        "parser_confidence": test_case['parser_confidence'],
        "ai_reasoning": ai_response.get("reasoning", "N/A"),
        "status": "CORRECT" if correct else "INCORRECT"
    }


def compare_with_phase2(phase3_results, phase2_file="lineage_v3/ai_analyzer/phase2_results.json"):
    """Compare Phase 3 results with Phase 2 baseline."""
    try:
        with open(phase2_file, 'r') as f:
            phase2_results = json.load(f)

        phase2_correct = sum(1 for r in phase2_results if r['evaluation']['correct'])
        phase3_correct = sum(1 for r in phase3_results if r['evaluation']['correct'])

        improvement = phase3_correct - phase2_correct

        print("\n" + "=" * 80)
        print("PHASE 2 vs PHASE 3 COMPARISON")
        print("=" * 80)
        print(f"Phase 2 (zero-shot): {phase2_correct}/12 correct (58.3%)")
        print(f"Phase 3 (few-shot):  {phase3_correct}/12 correct ({(phase3_correct/12)*100:.1f}%)")
        print(f"Improvement: {'+' if improvement >= 0 else ''}{improvement} cases")

        if improvement > 0:
            print("\n✅ Few-shot examples improved accuracy!")
        elif improvement == 0:
            print("\n⚠️  No improvement - consider alternative approaches")
        else:
            print("\n❌ Accuracy decreased - revert to Phase 2 prompt")

    except FileNotFoundError:
        print("\n⚠️  Phase 2 results not found - skipping comparison")


def run_phase3_tests():
    """Run Phase 3 tests with enhanced prompt."""
    print("=" * 80)
    print("PHASE 3: FEW-SHOT PROMPT ENGINEERING")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print(f"Enhancement: Schema rules + 5 few-shot examples")
    print()

    # Initialize client
    if not API_KEY or not ENDPOINT:
        print("❌ ERROR: Azure OpenAI credentials not configured in .env")
        return

    client = AzureOpenAI(
        api_version=API_VERSION,
        azure_endpoint=ENDPOINT,
        api_key=API_KEY,
    )

    # Load test dataset
    dataset = load_test_dataset()
    test_cases = dataset['test_cases']

    print(f"Loaded {len(test_cases)} test cases (same as Phase 2)\n")

    # Run tests
    results = []
    total_tokens = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Testing: {test_case['name']}")
        print(f"  Parser confidence: {test_case['parser_confidence']:.2f}")

        # Call AI with enhanced prompt
        ai_response, tokens = call_ai_disambiguation(client, test_case)
        total_tokens += tokens

        # Evaluate
        evaluation = evaluate_result(test_case, ai_response)

        print(f"  AI resolved: {evaluation.get('ai_resolved', 'N/A')}")
        print(f"  AI confidence: {evaluation['ai_confidence']:.2f}")
        print(f"  Status: {evaluation['status']}")
        print()

        results.append({
            "test_id": test_case['test_id'],
            "test_name": test_case['name'],
            "evaluation": evaluation,
            "tokens": tokens
        })

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Calculate metrics
    print_summary(results, total_tokens)

    # Compare with Phase 2
    compare_with_phase2(results)

    return results


def print_summary(results, total_tokens):
    """Print test summary."""
    print("=" * 80)
    print("PHASE 3 TEST RESULTS (FEW-SHOT)")
    print("=" * 80)

    # Overall metrics
    total = len(results)
    correct = sum(1 for r in results if r['evaluation']['correct'])
    accuracy = (correct / total) * 100 if total > 0 else 0

    print(f"\nOverall Performance:")
    print(f"  Total test cases: {total}")
    print(f"  Correct: {correct}")
    print(f"  Incorrect: {total - correct}")
    print(f"  Accuracy: {accuracy:.1f}%")

    # Token usage
    avg_tokens = total_tokens / total if total > 0 else 0
    print(f"\nToken Usage:")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Average per test: {avg_tokens:.0f}")
    print(f"  Estimated cost: ~${(total_tokens / 1000) * 0.002:.3f}")

    # Performance by parser confidence bucket
    print(f"\nPerformance by Parser Confidence:")
    low_conf = [r for r in results if r['evaluation']['parser_confidence'] < 0.70]
    med_conf = [r for r in results if 0.70 <= r['evaluation']['parser_confidence'] < 0.85]
    high_conf = [r for r in results if r['evaluation']['parser_confidence'] >= 0.85]

    for bucket, name in [(low_conf, "Low (<0.70)"), (med_conf, "Medium (0.70-0.84)"), (high_conf, "High (≥0.85)")]:
        if bucket:
            bucket_correct = sum(1 for r in bucket if r['evaluation']['correct'])
            bucket_accuracy = (bucket_correct / len(bucket)) * 100
            print(f"  {name}: {bucket_correct}/{len(bucket)} ({bucket_accuracy:.1f}%)")

    # Failed cases
    failed = [r for r in results if not r['evaluation']['correct']]
    if failed:
        print(f"\n❌ Failed Cases ({len(failed)}):")
        for r in failed:
            print(f"  • {r['test_name']}")
            print(f"    Expected: {r['evaluation']['expected']}")
            print(f"    AI resolved: {r['evaluation'].get('ai_resolved', 'N/A')}")

    # Key insights
    print(f"\n📊 KEY INSIGHTS:")

    if accuracy >= 90:
        print(f"  ✅ EXCELLENT: {accuracy:.1f}% accuracy exceeds 90% threshold")
        print(f"  ✅ Ready for production use!")
    elif accuracy >= 80:
        print(f"  ✅ GOOD: {accuracy:.1f}% accuracy meets 80% threshold")
        print(f"  ✅ Few-shot examples were effective")
        print(f"  📋 Consider: Fine-tune remaining edge cases")
    elif accuracy >= 70:
        print(f"  ⚠️  MARGINAL: {accuracy:.1f}% accuracy improved but below 80%")
        print(f"  📋 Recommend: Add more few-shot examples or try gpt-4o")
    else:
        print(f"  ❌ INSUFFICIENT: {accuracy:.1f}% accuracy still too low")
        print(f"  📋 Recommend: Try gpt-4o or hybrid approach")


def main():
    """Run Phase 3 tests."""
    print("\n🧪 AZURE OPENAI PHASE 3 TESTING")
    print("Purpose: Test few-shot prompt engineering to improve accuracy\n")

    results = run_phase3_tests()

    # Save results
    output_file = "lineage_v3/ai_analyzer/phase3_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")

    # Determine next steps
    correct = sum(1 for r in results if r['evaluation']['correct'])
    accuracy = (correct / len(results)) * 100

    print("\n📋 NEXT STEPS:")
    if accuracy >= 80:
        print("1. ✅ Few-shot prompt achieved target accuracy")
        print("2. Proceed to Phase 4: Production implementation")
        print("3. Document final prompt in parser codebase")
    else:
        print(f"1. ⚠️  Accuracy ({accuracy:.1f}%) still below 80% threshold")
        print("2. Options:")
        print("   a) Add more domain-specific few-shot examples")
        print("   b) Try gpt-4o (more capable model)")
        print("   c) Implement hybrid approach (heuristics + AI)")


if __name__ == "__main__":
    main()
