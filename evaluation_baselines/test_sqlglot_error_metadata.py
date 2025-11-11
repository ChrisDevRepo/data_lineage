#!/usr/bin/env python3
"""
Test SQLGlot Error Metadata and Parse Quality Information
==========================================================

Goal: Understand what metadata SQLGlot provides for confidence scoring
"""

import sqlglot
from sqlglot.errors import ErrorLevel
import logging

# Configure logging to see WARN messages
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

print("=" * 80)
print("SQLGlot Error Metadata Testing")
print("=" * 80)

# Test SQL with various issues
test_sqls = {
    "Valid T-SQL": """
        SELECT * FROM schema.table1
        JOIN schema.table2 ON table1.id = table2.id
        WHERE status = 'active'
    """,

    "T-SQL with DECLARE (unsupported)": """
        DECLARE @count INT
        SET @count = (SELECT COUNT(*) FROM schema.table1)
        INSERT INTO schema.table2 SELECT * FROM schema.table3
    """,

    "T-SQL with IF EXISTS": """
        IF EXISTS (SELECT 1 FROM schema.table1)
        BEGIN
            INSERT INTO schema.table2 SELECT * FROM schema.table3
        END
    """,

    "Complex stored procedure": """
        DECLARE @var INT = (SELECT COUNT(*) FROM schema.table1)

        IF OBJECT_ID('tempdb..#temp') IS NOT NULL
        BEGIN
            DROP TABLE #temp
        END

        CREATE TABLE #temp (id INT)

        INSERT INTO schema.output
        SELECT col1, col2
        FROM schema.input1
        JOIN schema.input2 ON input1.id = input2.id

        BEGIN TRY
            UPDATE schema.target SET status = 'done'
        END TRY
        BEGIN CATCH
            RAISERROR('Error occurred', 16, 1)
        END CATCH
    """
}

for name, sql in test_sqls.items():
    print(f"\n{'=' * 80}")
    print(f"Test: {name}")
    print(f"{'=' * 80}")

    # Parse with WARN mode
    try:
        parsed = sqlglot.parse(sql, dialect='tsql', error_level=ErrorLevel.WARN)

        print(f"\n✓ Parsing completed (WARN mode)")
        print(f"  Statements parsed: {len(parsed) if parsed else 0}")

        # Analyze parsed statements
        if parsed:
            for i, stmt in enumerate(parsed, 1):
                stmt_type = type(stmt).__name__
                print(f"  Statement {i}: {stmt_type}")

                # Check for Command nodes (unparseable sections)
                if stmt_type == 'Command':
                    print(f"    ⚠️  UNPARSEABLE: {str(stmt)[:100]}...")

                # Count tables found
                tables = list(stmt.find_all(sqlglot.exp.Table))
                if tables:
                    print(f"    Tables: {len(tables)}")
                    for table in tables[:3]:  # Show first 3
                        table_name = table.name
                        schema = table.db if table.db else None
                        print(f"      - {schema}.{table_name}" if schema else f"      - {table_name}")

        # Check if we can access parser errors (need to use Parser class directly)
        print(f"\n  Note: Using parse() function - error details logged but not returned")

    except Exception as e:
        print(f"\n✗ Parsing failed: {e}")

print("\n" + "=" * 80)
print("Testing with Parser class directly (to access error metadata)")
print("=" * 80)

from sqlglot import Parser
from sqlglot.dialects import Dialect

# Test with Parser class to access errors
dialect = Dialect.get_or_raise('tsql')
parser_class = dialect.parser_class

test_sql = """
DECLARE @count INT = (SELECT COUNT(*) FROM schema.table1)
IF EXISTS (SELECT 1 FROM invalid_syntax here)
BEGIN
    INSERT INTO schema.output SELECT * FROM schema.input
END
"""

print(f"\nTest SQL with intentional errors:\n{test_sql}\n")

# Parse with parser instance
parser = parser_class(error_level=ErrorLevel.WARN)
tokens = dialect.tokenizer_class().tokenize(test_sql)
parsed = parser.parse(tokens)

print(f"Statements parsed: {len(parsed)}")
print(f"Errors collected: {len(parser.errors)}")

if parser.errors:
    print("\nError details:")
    for i, error in enumerate(parser.errors, 1):
        print(f"\n  Error {i}:")
        print(f"    Message: {error.args[0] if error.args else 'N/A'}")
        # ParseError has these attributes
        if hasattr(error, 'errors'):
            for err_detail in error.errors:
                print(f"    Line: {err_detail.get('line', 'N/A')}")
                print(f"    Col: {err_detail.get('col', 'N/A')}")
                print(f"    Description: {err_detail.get('description', 'N/A')}")

print("\n" + "=" * 80)
print("CONCLUSION: Can we use SQLGlot metadata for confidence?")
print("=" * 80)

print("""
SQLGlot provides the following metadata for confidence scoring:

1. ✅ Statement count (len(parsed))
   - More statements parsed = better parse quality
   - But: WARN mode may create Command nodes for unparseable sections

2. ✅ Statement types (type(stmt).__name__)
   - Command nodes = unparseable sections (low confidence)
   - Select/Insert/Update/Delete = proper parsing (high confidence)
   - Ratio of Command nodes vs real DML = parse quality indicator

3. ✅ Table extraction count
   - More tables found = higher confidence
   - But: Need baseline to compare (how many SHOULD we find?)

4. ⚠️  Parse errors (parser.errors)
   - Available via Parser class, not parse() function
   - Requires using Tokenizer + Parser directly
   - More errors = lower confidence

5. ❌ No "parse quality score" built-in
   - SQLGlot doesn't provide a confidence metric
   - We must calculate our own based on above metadata

RECOMMENDATION:
- Use Command node ratio for confidence
- Formula: confidence = 100 * (non_command_stmts / total_stmts)
- OR: confidence = 100 if tables_found > 0 else 0
- Simpler and doesn't require manual hints!
""")
