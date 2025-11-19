"""
Tests for Comment Hints Parser

Tests the extraction and validation of @LINEAGE_INPUTS and @LINEAGE_OUTPUTS
comment hints from stored procedures.

Version: 4.2.0
Date: 2025-11-06
"""

import pytest
from engine.parsers.comment_hints_parser import CommentHintsParser


class TestCommentHintsParser:
    """Test suite for CommentHintsParser"""

    def test_basic_input_hints(self):
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

        assert inputs == {'dbo.Customers', 'dbo.Orders'}
        assert outputs == set()

    def test_basic_output_hints(self):
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

        assert inputs == set()
        assert outputs == {'dbo.TargetTable'}

    def test_both_input_and_output_hints(self):
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

        assert inputs == {'dbo.Source1', 'dbo.Source2'}
        assert outputs == {'dbo.Target1', 'dbo.Target2'}

    def test_multiple_hint_comments(self):
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

        # Should merge all hints
        assert inputs == {'dbo.Table1', 'dbo.Table2'}
        assert outputs == {'dbo.Target'}

    def test_bracketed_table_names(self):
        """Test table names with SQL brackets"""
        ddl = """
        -- @LINEAGE_INPUTS: [dbo].[Customers], [FINANCE].[Accounts]
        -- @LINEAGE_OUTPUTS: [dbo].[Target]
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'dbo.Customers', 'FINANCE.Accounts'}
        assert outputs == {'dbo.Target'}

    def test_mixed_bracket_formats(self):
        """Test various bracket format combinations"""
        ddl = """
        -- @LINEAGE_INPUTS: [dbo].Customers, dbo.[Orders], [FINANCE].[Accounts]
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'dbo.Customers', 'dbo.Orders', 'FINANCE.Accounts'}

    def test_no_schema_defaults_to_dbo(self):
        """Test that table names without schema default to dbo"""
        ddl = """
        -- @LINEAGE_INPUTS: Customers, Orders
        -- @LINEAGE_OUTPUTS: Target
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'dbo.Customers', 'dbo.Orders'}
        assert outputs == {'dbo.Target'}

    def test_whitespace_handling(self):
        """Test handling of various whitespace patterns"""
        ddl = """
        --@LINEAGE_INPUTS:dbo.Table1,dbo.Table2
        --   @LINEAGE_OUTPUTS:   dbo.Target
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'dbo.Table1', 'dbo.Table2'}
        assert outputs == {'dbo.Target'}

    def test_case_insensitive_keywords(self):
        """Test that hint keywords are case-insensitive"""
        ddl = """
        -- @lineage_inputs: dbo.Table1
        -- @LINEAGE_OUTPUTS: dbo.Table2
        -- @Lineage_Inputs: dbo.Table3
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'dbo.Table1', 'dbo.Table3'}
        assert outputs == {'dbo.Table2'}

    def test_hints_in_catch_block(self):
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

        assert inputs == {'dbo.Source'}
        assert outputs == {'dbo.ErrorTable'}

    def test_hints_in_conditional_logic(self):
        """Test extraction of hints documenting all conditional paths"""
        ddl = """
        CREATE PROC dbo.spTest @type VARCHAR(20)
        AS
        BEGIN
            -- @LINEAGE_INPUTS: dbo.Customers, dbo.Orders, dbo.Products
            -- @LINEAGE_OUTPUTS: dbo.Target
            IF @type = 'customers'
                INSERT INTO dbo.Target SELECT * FROM dbo.Customers;
            ELSE IF @type = 'orders'
                INSERT INTO dbo.Target SELECT * FROM dbo.Orders;
            ELSE
                INSERT INTO dbo.Target SELECT * FROM dbo.Products;
        END
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        # Hints document all possible code paths
        assert inputs == {'dbo.Customers', 'dbo.Orders', 'dbo.Products'}
        assert outputs == {'dbo.Target'}

    def test_dynamic_sql_documentation(self):
        """Test hints for dynamic SQL scenarios"""
        ddl = """
        CREATE PROC dbo.spDynamicLoad @tableName VARCHAR(100)
        AS
        BEGIN
            -- @LINEAGE_INPUTS: dbo.SourceData
            -- @LINEAGE_OUTPUTS: dbo.Customers, dbo.Orders
            -- Reason: Dynamic SQL - table name from parameter

            DECLARE @sql NVARCHAR(MAX);
            SET @sql = 'INSERT INTO ' + @tableName + ' SELECT * FROM dbo.SourceData';
            EXEC sp_executesql @sql;
        END
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'dbo.SourceData'}
        assert outputs == {'dbo.Customers', 'dbo.Orders'}

    def test_empty_ddl(self):
        """Test handling of empty DDL"""
        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints("", validate=False)

        assert inputs == set()
        assert outputs == set()

    def test_no_hints(self):
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

        assert inputs == set()
        assert outputs == set()

    def test_invalid_hint_format_ignored(self):
        """Test that invalid hint formats are ignored gracefully"""
        ddl = """
        -- @LINEAGE_INPUTS dbo.Table1 (missing colon)
        -- @LINEAGE_INPUTS: dbo.Table2
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        # Only valid hint should be extracted
        assert inputs == {'dbo.Table2'}
        assert outputs == set()

    def test_duplicate_hints_deduplicated(self):
        """Test that duplicate hints are deduplicated"""
        ddl = """
        -- @LINEAGE_INPUTS: dbo.Customers, dbo.Orders
        -- @LINEAGE_INPUTS: dbo.Customers, dbo.Products
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        # Customers should appear only once
        assert inputs == {'dbo.Customers', 'dbo.Orders', 'dbo.Products'}

    def test_hint_stats(self):
        """Test hint statistics calculation"""
        ddl = """
        -- @LINEAGE_INPUTS: dbo.Table1, dbo.Table2, dbo.InvalidTable
        -- @LINEAGE_OUTPUTS: dbo.Table3
        """

        parser = CommentHintsParser()
        stats = parser.get_hint_stats(ddl)

        assert stats['total_hints'] == 4  # 3 inputs + 1 output
        assert stats['input_hints'] == 3
        assert stats['output_hints'] == 1

    def test_real_world_example_1(self):
        """Test real-world example: Error recovery pattern"""
        ddl = """
        CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactSales]
        AS
        BEGIN TRY
            TRUNCATE TABLE CONSUMPTION_FINANCE.FactSales;

            INSERT INTO CONSUMPTION_FINANCE.FactSales
            SELECT * FROM STAGING.SalesData;

            COMMIT TRANSACTION;
        END TRY
        BEGIN CATCH
            -- @LINEAGE_INPUTS: STAGING.SalesData
            -- @LINEAGE_OUTPUTS: CONSUMPTION_FINANCE.ErrorRecovery
            -- Reason: CATCH block has real data operation (not just logging)

            ROLLBACK TRANSACTION;

            -- Move failed records to recovery table
            INSERT INTO CONSUMPTION_FINANCE.ErrorRecovery
            SELECT * FROM STAGING.SalesData WHERE ValidationStatus = 'Failed';
        END CATCH
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'STAGING.SalesData'}
        assert outputs == {'CONSUMPTION_FINANCE.ErrorRecovery'}

    def test_real_world_example_2(self):
        """Test real-world example: Multi-path conditional"""
        ddl = """
        CREATE PROC [dbo].[spLoadByEntity] @entityType VARCHAR(50)
        AS
        BEGIN
            -- @LINEAGE_INPUTS: dbo.CustomerData, dbo.SupplierData, dbo.EmployeeData
            -- @LINEAGE_OUTPUTS: dbo.EntityTarget
            -- Reason: Conditional logic - different sources based on parameter

            IF @entityType = 'CUSTOMER'
                INSERT INTO dbo.EntityTarget SELECT * FROM dbo.CustomerData;
            ELSE IF @entityType = 'SUPPLIER'
                INSERT INTO dbo.EntityTarget SELECT * FROM dbo.SupplierData;
            ELSE IF @entityType = 'EMPLOYEE'
                INSERT INTO dbo.EntityTarget SELECT * FROM dbo.EmployeeData;
        END
        """

        parser = CommentHintsParser()
        inputs, outputs = parser.extract_hints(ddl, validate=False)

        assert inputs == {'dbo.CustomerData', 'dbo.SupplierData', 'dbo.EmployeeData'}
        assert outputs == {'dbo.EntityTarget'}


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
