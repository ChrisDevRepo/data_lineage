"""
Simple test runner for Comment Hints Parser (no pytest required)

Version: 4.2.0
Date: 2025-11-06
"""

from lineage_v3.parsers.comment_hints_parser import CommentHintsParser


def test_basic_input_hints():
    """Test extraction of basic input hints"""
    ddl = """
    CREATE PROC dbo.spTest
    AS
    BEGIN
        -- @LINEAGE_INPUTS: dbo.Customers, dbo.Orders
        SELECT * FROM dbo.Customers;
    END
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == {'dbo.Customers', 'dbo.Orders'}, f"Expected {{''dbo.Customers', 'dbo.Orders'}}, got {inputs}"
    assert outputs == set(), f"Expected empty set, got {outputs}"
    print("✓ test_basic_input_hints")


def test_basic_output_hints():
    """Test extraction of basic output hints"""
    ddl = """
    CREATE PROC dbo.spTest
    AS
    BEGIN
        -- @LINEAGE_OUTPUTS: dbo.TargetTable
        INSERT INTO dbo.TargetTable SELECT * FROM dbo.Source;
    END
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == set(), f"Expected empty set, got {inputs}"
    assert outputs == {'dbo.TargetTable'}, f"Expected {{'dbo.TargetTable'}}, got {outputs}"
    print("✓ test_basic_output_hints")


def test_both_hints():
    """Test extraction of both input and output hints"""
    ddl = """
    CREATE PROC dbo.spTest
    AS
    BEGIN
        -- @LINEAGE_INPUTS: dbo.Source1, dbo.Source2
        -- @LINEAGE_OUTPUTS: dbo.Target1, dbo.Target2
        INSERT INTO dbo.Target1 SELECT * FROM dbo.Source1;
    END
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == {'dbo.Source1', 'dbo.Source2'}, f"Inputs mismatch: {inputs}"
    assert outputs == {'dbo.Target1', 'dbo.Target2'}, f"Outputs mismatch: {outputs}"
    print("✓ test_both_hints")


def test_bracketed_names():
    """Test table names with SQL brackets"""
    ddl = """
    -- @LINEAGE_INPUTS: [dbo].[Customers], [FINANCE].[Accounts]
    -- @LINEAGE_OUTPUTS: [dbo].[Target]
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == {'dbo.Customers', 'FINANCE.Accounts'}, f"Inputs mismatch: {inputs}"
    assert outputs == {'dbo.Target'}, f"Outputs mismatch: {outputs}"
    print("✓ test_bracketed_names")


def test_no_schema_defaults_dbo():
    """Test that table names without schema default to dbo"""
    ddl = """
    -- @LINEAGE_INPUTS: Customers, Orders
    -- @LINEAGE_OUTPUTS: Target
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == {'dbo.Customers', 'dbo.Orders'}, f"Inputs mismatch: {inputs}"
    assert outputs == {'dbo.Target'}, f"Outputs mismatch: {outputs}"
    print("✓ test_no_schema_defaults_dbo")


def test_dynamic_sql():
    """Test hints for dynamic SQL scenarios"""
    ddl = """
    CREATE PROC dbo.spDynamicLoad @tableName VARCHAR(100)
    AS
    BEGIN
        -- @LINEAGE_INPUTS: dbo.SourceData
        -- @LINEAGE_OUTPUTS: dbo.Customers, dbo.Orders

        DECLARE @sql NVARCHAR(MAX);
        SET @sql = 'INSERT INTO ' + @tableName + ' SELECT * FROM dbo.SourceData';
        EXEC sp_executesql @sql;
    END
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == {'dbo.SourceData'}, f"Inputs mismatch: {inputs}"
    assert outputs == {'dbo.Customers', 'dbo.Orders'}, f"Outputs mismatch: {outputs}"
    print("✓ test_dynamic_sql")


def test_catch_block_hints():
    """Test extraction of hints from CATCH blocks"""
    ddl = """
    CREATE PROC dbo.spTest
    AS
    BEGIN TRY
        INSERT INTO dbo.Target SELECT * FROM dbo.Source;
    END TRY
    BEGIN CATCH
        -- @LINEAGE_INPUTS: dbo.Source
        -- @LINEAGE_OUTPUTS: dbo.ErrorTable
        INSERT INTO dbo.ErrorTable SELECT * FROM dbo.Source WHERE Status = 'Failed';
    END CATCH
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == {'dbo.Source'}, f"Inputs mismatch: {inputs}"
    assert outputs == {'dbo.ErrorTable'}, f"Outputs mismatch: {outputs}"
    print("✓ test_catch_block_hints")


def test_no_hints():
    """Test DDL without any hints"""
    ddl = """
    CREATE PROC dbo.spTest
    AS
    BEGIN
        INSERT INTO dbo.Target SELECT * FROM dbo.Source;
    END
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == set(), f"Expected empty set, got {inputs}"
    assert outputs == set(), f"Expected empty set, got {outputs}"
    print("✓ test_no_hints")


def test_multiple_hint_comments():
    """Test extraction from multiple hint comments"""
    ddl = """
    CREATE PROC dbo.spTest
    AS
    BEGIN
        -- @LINEAGE_INPUTS: dbo.Table1
        SELECT * FROM dbo.Table1;

        -- @LINEAGE_INPUTS: dbo.Table2
        SELECT * FROM dbo.Table2;

        -- @LINEAGE_OUTPUTS: dbo.Target
        INSERT INTO dbo.Target VALUES (1);
    END
    """

    parser = CommentHintsParser()
    inputs, outputs = parser.extract_hints(ddl, validate=False)

    assert inputs == {'dbo.Table1', 'dbo.Table2'}, f"Inputs mismatch: {inputs}"
    assert outputs == {'dbo.Target'}, f"Outputs mismatch: {outputs}"
    print("✓ test_multiple_hint_comments")


def test_hint_stats():
    """Test hint statistics calculation"""
    ddl = """
    -- @LINEAGE_INPUTS: dbo.Table1, dbo.Table2, dbo.Table3
    -- @LINEAGE_OUTPUTS: dbo.Table4
    """

    parser = CommentHintsParser()
    stats = parser.get_hint_stats(ddl)

    assert stats['total_hints'] == 4, f"Expected 4 total hints, got {stats['total_hints']}"
    assert stats['input_hints'] == 3, f"Expected 3 input hints, got {stats['input_hints']}"
    assert stats['output_hints'] == 1, f"Expected 1 output hint, got {stats['output_hints']}"
    print("✓ test_hint_stats")


def run_all_tests():
    """Run all tests"""
    tests = [
        test_basic_input_hints,
        test_basic_output_hints,
        test_both_hints,
        test_bracketed_names,
        test_no_schema_defaults_dbo,
        test_dynamic_sql,
        test_catch_block_hints,
        test_no_hints,
        test_multiple_hint_comments,
        test_hint_stats,
    ]

    print("="*60)
    print("Running Comment Hints Parser Tests")
    print("="*60)

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR - {e}")
            failed += 1

    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
