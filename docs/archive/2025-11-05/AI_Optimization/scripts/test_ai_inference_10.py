#!/usr/bin/env python3
"""
Test AI inference on 10 sample unreferenced tables
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lineage_v3'))

from core.duckdb_workspace import DuckDBWorkspace
from parsers.ai_disambiguator import AIDisambiguator
from config import settings

def main():
    print("=" * 80)
    print("TESTING AI INFERENCE ON 10 UNREFERENCED TABLES")
    print("=" * 80)

    # Check AI availability
    if not settings.ai_available:
        print("\n❌ ERROR: AI not configured")
        print("Set AZURE_OPENAI_* variables in .env")
        return 1

    # Connect to workspace
    db = DuckDBWorkspace('lineage_workspace.duckdb')

    # Get 10 test tables (diverse sample)
    test_tables = [
        ('CONSUMPTION_POWERBI', 'AggregatedCadenceBudgetData'),
        ('CONSUMPTION_FINANCE', 'ArAnalyticsDetailMetrics'),
        ('CONSUMPTION_FINANCE', 'ArAnalyticsDetailMetrics_Test'),
        ('CONSUMPTION_FINANCE', 'ArAnalyticsMetricsQuarterlyGlobal'),
        ('CONSUMPTION_POWERBI', 'AverageFTE_Daily'),
        ('CONSUMPTION_POWERBI', 'AverageFTE_Monthly'),
        ('CONSUMPTION_FINANCE', 'COGNOS_Account'),
        ('CONSUMPTION_FINANCE', 'COGNOS_Actuality'),
        ('CONSUMPTION_FINANCE', 'COGNOS_ClosingVersion'),
        ('CONSUMPTION_FINANCE', 'COGNOS_Company'),
    ]

    # Get all SP data
    all_sps = db.query("""
        SELECT object_id, schema_name, object_name
        FROM objects
        WHERE object_type = 'Stored Procedure'
    """)

    sp_data = [{'object_id': oid, 'schema': schema, 'name': name}
               for oid, schema, name in all_sps]

    print(f"\nTesting {len(test_tables)} tables")
    print(f"Available SPs: {len(sp_data)}")

    # Initialize AI
    disambiguator = AIDisambiguator(db)

    # Test each table
    results = []

    for i, (schema, name) in enumerate(test_tables, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/10] {schema}.{name}")
        print(f"{'='*60}")

        try:
            result = disambiguator.infer_dependencies_for_unreferenced_table(
                table_schema=schema,
                table_name=name,
                all_sp_data=sp_data
            )

            if result and result.is_valid:
                method = 'RULE' if 'Rule-based' in result.reasoning else 'AI'
                print(f"✅ {method}: confidence={result.confidence:.2f}")
                print(f"   Reasoning: {result.reasoning}")

                if result.sources:  # SPs that write to table
                    print(f"   Matched {len(result.sources)} SP(s):")
                    for sp_id in result.sources[:3]:
                        sp_info = db.query(
                            "SELECT schema_name, object_name FROM objects WHERE object_id=?",
                            [sp_id]
                        )
                        if sp_info:
                            sp_schema, sp_name = sp_info[0]
                            print(f"      - {sp_schema}.{sp_name}")

                            # Simple validation
                            if sp_schema != schema:
                                print(f"        ⚠️  Different schema: {sp_schema} vs {schema}")

                            sp_clean = sp_name.lower().replace('_', '')
                            table_clean = name.lower().replace('_', '')
                            if table_clean not in sp_clean:
                                print(f"        ⚠️  Name mismatch: {sp_name} vs {name}")

                results.append({
                    'table': f"{schema}.{name}",
                    'success': True,
                    'confidence': result.confidence,
                    'method': method,
                    'sp_count': len(result.sources)
                })
            else:
                print(f"⚠️  No match found")
                results.append({
                    'table': f"{schema}.{name}",
                    'success': False,
                    'confidence': 0.0,
                    'method': 'NONE',
                    'sp_count': 0
                })

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                'table': f"{schema}.{name}",
                'success': False,
                'confidence': 0.0,
                'method': 'ERROR',
                'sp_count': 0,
                'error': str(e)
            })

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    success = sum(1 for r in results if r['success'])
    rule = sum(1 for r in results if r.get('method') == 'RULE')
    ai = sum(1 for r in results if r.get('method') == 'AI')

    print(f"\nTotal: {total}")
    print(f"Success: {success}/{total} ({success/total*100:.0f}%)")
    print(f"  - Rule-based: {rule}")
    print(f"  - AI-based: {ai}")
    print(f"  - No match: {total - success}")

    if success > 0:
        avg_conf = sum(r['confidence'] for r in results if r['success']) / success
        print(f"\nAverage confidence: {avg_conf:.2f}")

    print("\nDetailed Results:")
    print(f"{'Table':<50} {'Status':<8} {'Conf':<6} {'Method':<6} {'SPs':<4}")
    print("-" * 80)
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{r['table']:<50} {status:<8} {r['confidence']:<6.2f} {r['method']:<6} {r['sp_count']:<4}")

    db.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
