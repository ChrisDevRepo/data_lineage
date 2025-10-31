"""
Azure OpenAI Phase 2 Testing - Production Case Comparison
==========================================================

Purpose: Test AI disambiguation on realistic production scenarios and compare
against actual parser confidence scores to evaluate AI effectiveness.

Usage:
    python lineage_v3/ai_analyzer/test_azure_openai_phase2.py
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

# Test dataset
TEST_DATASET = "lineage_v3/ai_analyzer/phase2_test_dataset.json"

# System prompt
SYSTEM_PROMPT = """You are a SQL dependency analyzer specialized in disambiguating ambiguous table references in T-SQL stored procedures.

Your task: Given a SQL stored procedure and a list of candidate table names, identify which specific table is being referenced.

Rules:
1. Use context clues (nearby schema names, naming patterns, business logic)
2. Consider schema conventions (CONSUMPTION_FINANCE.Dim*, STAGING_*, etc.)
3. If multiple tables match, rank them by likelihood
4. Provide confidence score (0.0-1.0)
5. Explain your reasoning briefly

Output format (JSON):
{
  "resolved_table": "schema.table_name",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}
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
    """Call Azure OpenAI to disambiguate a test case."""
    user_prompt = create_user_prompt(test_case)

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=500,
            temperature=0.0,  # Deterministic
            model=DEPLOYMENT
        )

        result = response.choices[0].message.content
        tokens = response.usage.total_tokens

        # Try to parse JSON response
        try:
            ai_response = json.loads(result)
        except json.JSONDecodeError:
            # If not valid JSON, extract manually
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


def run_phase2_tests():
    """Run all Phase 2 test cases."""
    print("=" * 80)
    print("PHASE 2: AI DISAMBIGUATION ON PRODUCTION SCENARIOS")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print(f"Endpoint: {ENDPOINT}")
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

    print(f"Loaded {len(test_cases)} test cases from {TEST_DATASET}\n")

    # Run tests
    results = []
    total_tokens = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Testing: {test_case['name']}")
        print(f"  Parser confidence: {test_case['parser_confidence']:.2f}")

        # Call AI
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
    print_summary(results, total_tokens, test_cases)

    return results


def print_summary(results, total_tokens, test_cases):
    """Print test summary and analysis."""
    print("=" * 80)
    print("PHASE 2 TEST RESULTS")
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

    # Confidence analysis
    ai_confidences = [r['evaluation']['ai_confidence'] for r in results if r['evaluation']['correct']]
    parser_confidences = [r['evaluation']['parser_confidence'] for r in results]

    if ai_confidences:
        avg_ai_conf = sum(ai_confidences) / len(ai_confidences)
        print(f"\nConfidence Scores:")
        print(f"  AI avg (correct cases): {avg_ai_conf:.2f}")
        print(f"  Parser avg (all cases): {sum(parser_confidences) / len(parser_confidences):.2f}")

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
        print(f"  ✅ AI model is suitable for production use")
    elif accuracy >= 80:
        print(f"  ✅ GOOD: {accuracy:.1f}% accuracy meets 80% threshold")
        print(f"  📋 Consider refining system prompt for edge cases")
    else:
        print(f"  ⚠️  NEEDS IMPROVEMENT: {accuracy:.1f}% accuracy below 80%")
        print(f"  📋 Recommend: Add few-shot examples or fine-tuning")

    # Comparison with parser
    ai_better = sum(1 for r in results if r['evaluation']['correct'] and r['evaluation']['parser_confidence'] < 0.85)
    if ai_better > 0:
        print(f"  ✅ AI improved {ai_better} low-confidence parser cases")


def main():
    """Run Phase 2 tests."""
    print("\n🧪 AZURE OPENAI PHASE 2 TESTING")
    print("Purpose: Compare AI disambiguation vs parser confidence on production scenarios\n")

    results = run_phase2_tests()

    # Save results
    output_file = "lineage_v3/ai_analyzer/phase2_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")
    print("\n📋 NEXT STEPS:")
    print("1. Review failed cases in phase2_results.json")
    print("2. Update docs/AI_MODEL_EVALUATION.md with Phase 2 findings")
    print("3. Decide: Proceed with implementation or refine prompt?")


if __name__ == "__main__":
    main()
