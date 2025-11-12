#!/usr/bin/env python3
"""
Analyze Failed SPs - Why Did They Fail?

Shows concrete reasons for each failure to validate cleaning logic.
"""

import duckdb
import re

# Connect to database
conn = duckdb.connect('data/lineage_workspace.duckdb')

print("=" * 80)
print("FAILED SP ANALYSIS - Root Cause Investigation")
print("=" * 80)
print()

# Get failed SPs (no inputs AND no outputs)
print("🔍 IDENTIFYING FAILED SPS")
print("-" * 80)

results = conn.execute("""
    SELECT
        o.schema_name,
        o.object_name,
        o.object_type,
        d.ddl_text,
        l.confidence,
        l.inputs,
        l.outputs
    FROM lineage_metadata l
    JOIN objects o ON l.object_id = o.object_id
    LEFT JOIN unified_ddl d ON l.object_id = d.object_id
    WHERE l.primary_source = 'parser'
      AND (l.inputs IS NULL OR l.inputs = '')
      AND (l.outputs IS NULL OR l.outputs = '')
    ORDER BY o.schema_name, o.object_name
""").fetchall()

failed_count = len(results)
print(f"Total failed SPs: {failed_count}")
print()

if failed_count == 0:
    print("✅ No failed SPs! Parser success rate is 100%")
    conn.close()
    exit(0)

# Analyze each failure
print("=" * 80)
print("DETAILED FAILURE ANALYSIS")
print("=" * 80)
print()

failure_categories = {
    'dynamic_sql_only': [],
    'template_empty': [],
    'utility_system': [],
    'administrative': [],
    'unknown': []
}

for i, (schema, name, obj_type, ddl, confidence, inputs, outputs) in enumerate(results, 1):
    sp_name = f"{schema}.{name}"

    print(f"{'=' * 80}")
    print(f"FAILURE #{i}: {sp_name}")
    print(f"{'=' * 80}")

    # Analyze DDL
    ddl_clean = ddl.strip()
    ddl_body = ddl_clean.upper()

    # Category 1: Dynamic SQL only (EXEC @variable, EXEC sp_executesql)
    if re.search(r'EXEC\s+@\w+', ddl_body) or re.search(r'EXEC\s+sp_executesql', ddl_body):
        if not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|MERGE\s+INTO)\b', ddl_body):
            category = 'dynamic_sql_only'
            reason = "🔴 DYNAMIC SQL ONLY - No static table references"
            explanation = "SP uses EXEC @variable or sp_executesql with no static SQL"

    # Category 2: Template/Empty procedures
    elif len(ddl_clean) < 100 or ddl_body.count('SELECT') == 0:
        if 'BEGIN' in ddl_body and 'END' in ddl_body:
            between_begin_end = ddl_body[ddl_body.find('BEGIN')+5:ddl_body.find('END')].strip()
            if len(between_begin_end) < 20:
                category = 'template_empty'
                reason = "🟡 TEMPLATE/EMPTY PROCEDURE - No actual logic"
                explanation = "SP is a placeholder or stub with no meaningful code"
            else:
                category = 'unknown'
                reason = "⚪ UNKNOWN - Has code but no table references"
                explanation = "SP has logic but parser couldn't extract tables"
        else:
            category = 'template_empty'
            reason = "🟡 TEMPLATE/EMPTY PROCEDURE - No actual logic"
            explanation = "SP is a placeholder or stub with no meaningful code"

    # Category 3: Utility/System procedures (row counts, variable assignments)
    elif re.search(r'@@ROWCOUNT|@@ERROR|@@IDENTITY|@@VERSION', ddl_body):
        if not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM)\b', ddl_body):
            category = 'utility_system'
            reason = "🟠 UTILITY PROCEDURE - System variables only"
            explanation = "SP only queries system variables (@@ROWCOUNT, @@ERROR, etc.)"
        else:
            category = 'unknown'
            reason = "⚪ UNKNOWN - Has system variables and other logic"
            explanation = "Mixed utility and data logic"

    # Category 4: Administrative (only DECLARE, SET, PRINT)
    elif not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|MERGE\s+INTO)\b', ddl_body):
        if re.search(r'\b(DECLARE|SET|PRINT|RETURN|RAISERROR)\b', ddl_body):
            category = 'administrative'
            reason = "🟢 ADMINISTRATIVE ONLY - No data operations"
            explanation = "SP only does variable assignments, logging, error handling"
        else:
            category = 'unknown'
            reason = "⚪ UNKNOWN - No recognizable patterns"
            explanation = "SP has no table references and no clear pattern"

    # Unknown
    else:
        category = 'unknown'
        reason = "⚪ UNKNOWN - Parser couldn't extract dependencies"
        explanation = "Unexpected failure, needs manual investigation"

    failure_categories[category].append(sp_name)

    print(f"Reason: {reason}")
    print(f"Explanation: {explanation}")
    print()

    print("📄 DDL Preview (first 500 chars):")
    print("-" * 80)
    print(ddl_clean[:500])
    if len(ddl_clean) > 500:
        print(f"... ({len(ddl_clean) - 500} more characters)")
    print()

    # Check for specific patterns
    print("🔍 Pattern Analysis:")
    print("-" * 80)

    patterns = {
        'FROM clause': r'\bFROM\s+\[?[\w]+\]?\.',
        'JOIN clause': r'\b(INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+',
        'INSERT INTO': r'\bINSERT\s+INTO\s+',
        'UPDATE': r'\bUPDATE\s+\[?[\w]+\]?\.',
        'DELETE FROM': r'\bDELETE\s+FROM\s+',
        'MERGE INTO': r'\bMERGE\s+INTO\s+',
        'EXEC @variable': r'EXEC\s+@\w+',
        'EXEC sp_executesql': r'EXEC\s+sp_executesql',
        'System variables': r'@@(ROWCOUNT|ERROR|IDENTITY|VERSION)',
        'DECLARE': r'\bDECLARE\s+@',
        'SET': r'\bSET\s+@',
        'PRINT': r'\bPRINT\s+',
        'RETURN': r'\bRETURN\b',
    }

    for pattern_name, pattern_regex in patterns.items():
        matches = re.findall(pattern_regex, ddl_body)
        if matches:
            print(f"  ✅ {pattern_name}: {len(matches)} occurrence(s)")
        else:
            print(f"  ❌ {pattern_name}: Not found")

    print()

# Summary
print("=" * 80)
print("FAILURE CATEGORY SUMMARY")
print("=" * 80)
print()

category_names = {
    'dynamic_sql_only': '🔴 Dynamic SQL Only (EXEC @var)',
    'template_empty': '🟡 Template/Empty Procedures',
    'utility_system': '🟠 Utility/System Procedures',
    'administrative': '🟢 Administrative Only',
    'unknown': '⚪ Unknown/Unexpected'
}

for category, color_name in category_names.items():
    count = len(failure_categories[category])
    pct = (count / failed_count) * 100 if failed_count > 0 else 0

    print(f"{color_name}: {count} SPs ({pct:.1f}%)")

    if count > 0:
        for sp_name in failure_categories[category]:
            print(f"  - {sp_name}")
    print()

# Cleaning logic assessment
print("=" * 80)
print("CLEANING LOGIC ASSESSMENT")
print("=" * 80)
print()

expected_failures = (
    len(failure_categories['dynamic_sql_only']) +
    len(failure_categories['template_empty']) +
    len(failure_categories['utility_system']) +
    len(failure_categories['administrative'])
)

unexpected_failures = len(failure_categories['unknown'])

print(f"Expected failures: {expected_failures}/{failed_count} ({expected_failures/failed_count*100:.1f}%)")
print(f"  - These SPs have NO static table references by design")
print(f"  - Cleaning logic is CORRECT for these")
print()

print(f"Unexpected failures: {unexpected_failures}/{failed_count} ({unexpected_failures/failed_count*100:.1f}%)")
if unexpected_failures > 0:
    print(f"  ⚠️ These need manual investigation")
    print(f"  - May indicate cleaning logic issue")
    print(f"  - May indicate regex pattern gaps")
else:
    print(f"  ✅ No unexpected failures!")
print()

print("=" * 80)
print("✅ Analysis complete!")
print()
print("CONCLUSION:")
if unexpected_failures == 0:
    print("✅ All failures are EXPECTED (dynamic SQL, templates, utilities)")
    print("✅ Cleaning logic is working correctly")
    print("✅ No action needed")
else:
    print(f"⚠️ {unexpected_failures} unexpected failure(s) need investigation")
    print("   Check DDL above to identify root cause")
print("=" * 80)

conn.close()
