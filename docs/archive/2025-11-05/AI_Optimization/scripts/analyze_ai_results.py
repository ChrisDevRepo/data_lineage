#!/usr/bin/env python3
"""
Analyze AI inference results - spot-check 20 tables
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lineage_v3'))

from core.duckdb_workspace import DuckDBWorkspace

def main():
    db = DuckDBWorkspace('lineage_workspace.duckdb')

    # Get AI-inferred tables with their matched SPs
    results = db.query("""
        SELECT
            o.schema_name,
            o.object_name,
            o.object_id,
            lm.confidence,
            lm.outputs
        FROM objects o
        JOIN lineage_metadata lm ON o.object_id = lm.object_id
        WHERE o.object_type = 'Table'
          AND lm.primary_source = 'ai'
        ORDER BY lm.confidence DESC
        LIMIT 20
    """)

    print("=" * 80)
    print("SPOT-CHECK: 20 AI-INFERRED TABLES (Sorted by Confidence)")
    print("=" * 80)

    correct = 0
    questionable = 0
    wrong = 0

    for schema, name, table_id, conf, outputs in results:
        print(f"\n{'=' * 60}")
        print(f"Table: {schema}.{name}")
        print(f"Confidence: {conf:.2f}")
        print(f"{'=' * 60}")

        if outputs:
            output_sp_ids = [int(x) for x in outputs.split(',')]
            print(f"AI matched {len(output_sp_ids)} SP(s):")

            has_warnings = False
            for sp_id in output_sp_ids:
                sp_info = db.query("""
                    SELECT schema_name, object_name
                    FROM objects
                    WHERE object_id = ?
                """, [sp_id])

                if sp_info:
                    sp_schema, sp_name = sp_info[0]
                    print(f"  ✅ {sp_schema}.{sp_name}")

                    # Simple plausibility checks
                    warnings = []

                    # Check 1: Schema mismatch
                    if sp_schema != schema:
                        warnings.append(f"Different schema: {sp_schema} vs {schema}")

                    # Check 2: Name similarity
                    sp_clean = sp_name.lower().replace('_', '').replace('spload', '')
                    table_clean = name.lower().replace('_', '')

                    if table_clean not in sp_clean and sp_clean not in table_clean:
                        warnings.append(f"Name mismatch: {sp_name} vs {name}")

                    if warnings:
                        has_warnings = True
                        for w in warnings:
                            print(f"     ⚠️  {w}")

            # Categorize result
            if has_warnings:
                print("  📊 Verdict: ⚠️  QUESTIONABLE")
                questionable += 1
            else:
                print("  📊 Verdict: ✅ LOOKS CORRECT")
                correct += 1
        else:
            print("  ⚠️  No SPs matched (empty outputs)")
            print("  📊 Verdict: ❌ WRONG")
            wrong += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Looks Correct: {correct}/20 ({correct/20*100:.0f}%)")
    print(f"⚠️  Questionable: {questionable}/20 ({questionable/20*100:.0f}%)")
    print(f"❌ Wrong: {wrong}/20 ({wrong/20*100:.0f}%)")

    accuracy = (correct / 20 * 100) if correct > 0 else 0
    print(f"\n🎯 Estimated Accuracy: {accuracy:.0f}%")

    if accuracy >= 90:
        print("✅ PASS: Ready for UAT deployment")
    elif accuracy >= 75:
        print("⚠️  ITERATE: Add more few-shot examples based on failures")
    else:
        print("❌ DEBUG: Review AI prompt and strategy")

    db.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
