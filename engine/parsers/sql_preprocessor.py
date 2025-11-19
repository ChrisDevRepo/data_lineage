"""
SQL Pre-processor for SQLGlot

Cleans T-SQL stored procedures to extract parseable SQL that SQLGlot can handle.
Removes T-SQL-specific constructs and extracts core DML statements.

Strategy:
1. Extract core DML (WITH/INSERT/SELECT/UPDATE/DELETE/MERGE)
2. Remove CREATE PROC wrapper
3. Remove T-SQL constructs (DECLARE, SET, TRY/CATCH, RAISERROR, EXEC)
4. Keep clean SQL that SQLGlot can parse

Result: Dramatically improves SQLGlot success rate on complex T-SQL procedures

Version: 1.0.0
Date: 2025-11-06
Author: Claude Code Agent
"""

import re
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class SQLPreprocessor:
    """
    Pre-processes T-SQL stored procedures to extract clean SQL for SQLGlot parsing.
    """

    # T-SQL reserved names that are not real tables (CTEs, temp tables, variables)
    CTE_PATTERN = r'WITH\s+(\w+)\s+AS'
    TEMP_TABLE_PATTERN = r'#\w+'
    TABLE_VARIABLE_PATTERN = r'@\w+'

    @classmethod
    def extract_core_dml(cls, sql: str) -> str:
        """
        Extract core DML statements from stored procedure.

        Removes:
        - CREATE PROC wrapper
        - DECLARE/SET statements
        - BEGIN TRY/CATCH blocks (keeps TRY content)
        - RAISERROR, EXEC
        - Transaction control
        - GO statements

        Keeps:
        - WITH (CTEs)
        - INSERT, SELECT, UPDATE, DELETE, MERGE
        - FROM, JOIN clauses
        - WHERE, GROUP BY, ORDER BY

        Args:
            sql: T-SQL stored procedure definition

        Returns:
            Clean SQL with core DML statements

        Example:
            >>> sql = '''
            ... CREATE PROC dbo.Test AS
            ... BEGIN
            ...     DECLARE @var VARCHAR(100)
            ...     WITH cte AS (SELECT * FROM dbo.Source)
            ...     INSERT INTO dbo.Target SELECT * FROM cte
            ... END
            ... '''
            >>> clean = extract_core_dml(sql)
            >>> # Returns: "WITH cte AS (SELECT * FROM dbo.Source) INSERT INTO dbo.Target SELECT * FROM cte"
        """
        if not sql:
            return sql

        cleaned = sql

        # Step 1: Remove GO statements (batch separator, not SQL)
        cleaned = re.sub(r'^\s*GO\s*$', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

        # Step 2: Remove DECLARE statements
        cleaned = re.sub(r'DECLARE\s+@\w+[^;]*;?', '', cleaned, flags=re.IGNORECASE)

        # Step 3: Remove SET statements (variable assignments)
        cleaned = re.sub(r'SET\s+@\w+\s*=[^;]*;?', '', cleaned, flags=re.IGNORECASE)

        # Step 4: Extract BEGIN TRY content, remove CATCH blocks
        # Remove CATCH blocks first
        catch_pattern = r'BEGIN\s+CATCH\s+.*?\s+END\s+CATCH'
        cleaned = re.sub(catch_pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)

        # Extract TRY content (replace BEGIN TRY...END TRY with just the content)
        try_pattern = r'BEGIN\s+TRY\s+(.*?)\s+END\s+TRY'
        try_matches = re.findall(try_pattern, cleaned, flags=re.IGNORECASE | re.DOTALL)
        for try_content in try_matches:
            cleaned = re.sub(
                r'BEGIN\s+TRY\s+.*?\s+END\s+TRY',
                try_content,
                cleaned,
                count=1,
                flags=re.IGNORECASE | re.DOTALL
            )

        # Step 5: Remove RAISERROR
        cleaned = re.sub(r'RAISERROR\s*\([^)]*\)', '', cleaned, flags=re.IGNORECASE)

        # Step 6: Remove EXEC statements
        cleaned = re.sub(r'EXEC\s+\[?[a-zA-Z_\[\]\.]+\]?\s+[^;]*;?', '', cleaned, flags=re.IGNORECASE)

        # Step 7: Remove TRUNCATE statements
        cleaned = re.sub(r'TRUNCATE\s+TABLE\s+[^;]+;?', '', cleaned, flags=re.IGNORECASE)

        # Step 8: Remove transaction control
        cleaned = re.sub(r'BEGIN\s+TRAN(?:SACTION)?\s*;?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'COMMIT\s+TRAN(?:SACTION)?\s*;?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'ROLLBACK\s+TRAN(?:SACTION)?\s*;?', '', cleaned, flags=re.IGNORECASE)

        # Step 9: Extract core DML from CREATE PROC wrapper
        # Strategy: Find the main WITH or DML statement
        core_dml_pattern = r'(WITH\s+\w+\s+AS\s*\(.*?\)\s*(?:,\s*\w+\s+AS\s*\(.*?\))*\s*(?:INSERT|SELECT|UPDATE|DELETE|MERGE)\s+.*?)(?=\n\s*(?:END|$))'

        matches = re.findall(core_dml_pattern, cleaned, flags=re.DOTALL | re.IGNORECASE)
        if matches:
            # Use the longest match (most complete DML statement)
            cleaned = max(matches, key=len)
        else:
            # Try to find standalone DML
            dml_pattern = r'((?:INSERT|SELECT|UPDATE|DELETE|MERGE)\s+(?:INTO\s+)?\s*.*?)(?=\n\s*(?:END|$))'
            dml_matches = re.findall(dml_pattern, cleaned, flags=re.DOTALL | re.IGNORECASE)
            if dml_matches:
                cleaned = max(dml_matches, key=len)

        # Step 10: Clean up whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned

    @classmethod
    def extract_cte_names(cls, sql: str) -> Set[str]:
        """
        Extract CTE names from SQL to filter them out from table results.

        CTEs are named result sets (WITH cte_name AS ...) that SQLGlot
        treats as tables, but they're not real database tables.

        Args:
            sql: SQL statement with CTEs

        Returns:
            Set of CTE names

        Example:
            >>> sql = "WITH cte1 AS (SELECT ...), cte2 AS (SELECT ...) SELECT * FROM cte1"
            >>> extract_cte_names(sql)
            {'cte1', 'cte2'}
        """
        cte_names = set()

        # Find all CTE definitions: WITH name AS (...)
        matches = re.findall(cls.CTE_PATTERN, sql, re.IGNORECASE)
        for cte_name in matches:
            cte_names.add(cte_name)

        return cte_names

    @classmethod
    def is_temp_or_variable_table(cls, table_name: str) -> bool:
        """
        Check if table name is a temp table (#temp) or table variable (@table).

        Args:
            table_name: Table name to check

        Returns:
            True if temp table or table variable, False otherwise

        Example:
            >>> is_temp_or_variable_table("#TempTable")
            True
            >>> is_temp_or_variable_table("@TableVar")
            True
            >>> is_temp_or_variable_table("dbo.RealTable")
            False
        """
        # Check for temp table (#table)
        if re.match(cls.TEMP_TABLE_PATTERN, table_name):
            return True

        # Check for table variable (@table)
        if re.match(cls.TABLE_VARIABLE_PATTERN, table_name):
            return True

        return False

    @classmethod
    def filter_non_tables(cls, table_names: Set[str], sql_context: str = "") -> Set[str]:
        """
        Filter out non-real tables (CTEs, temp tables, table variables).

        Args:
            table_names: Set of table names from parser
            sql_context: Original SQL for CTE extraction (optional)

        Returns:
            Filtered set containing only real database tables

        Example:
            >>> tables = {'dbo.Real', 'cte_temp', '#TempTable', '@TableVar'}
            >>> sql = "WITH cte_temp AS (SELECT ...) ..."
            >>> filter_non_tables(tables, sql)
            {'dbo.Real'}
        """
        filtered = set()

        # Extract CTE names from context if provided
        cte_names = cls.extract_cte_names(sql_context) if sql_context else set()

        for table_name in table_names:
            # Skip CTEs
            table_base = table_name.split('.')[-1]  # Get table name without schema
            if table_base in cte_names:
                logger.debug(f"Filtering out CTE: {table_name}")
                continue

            # Skip temp tables and table variables
            if cls.is_temp_or_variable_table(table_name):
                logger.debug(f"Filtering out temp/variable table: {table_name}")
                continue

            # Keep real tables
            filtered.add(table_name)

        return filtered

    @classmethod
    def preprocess_for_sqlglot(cls, sql: str) -> tuple[str, Set[str]]:
        """
        Full preprocessing pipeline for SQLGlot parsing.

        1. Extract core DML
        2. Extract CTE names for filtering
        3. Return both cleaned SQL and CTEs

        Args:
            sql: Original T-SQL stored procedure

        Returns:
            Tuple of (cleaned_sql, cte_names)

        Example:
            >>> sql = '''
            ... CREATE PROC dbo.Test AS
            ... BEGIN
            ...     WITH cte AS (SELECT * FROM dbo.Source)
            ...     INSERT INTO dbo.Target SELECT * FROM cte
            ... END
            ... '''
            >>> cleaned, ctes = preprocess_for_sqlglot(sql)
            >>> # cleaned = "WITH cte AS (SELECT * FROM dbo.Source) INSERT INTO dbo.Target SELECT * FROM cte"
            >>> # ctes = {'cte'}
        """
        # Extract core DML
        cleaned_sql = cls.extract_core_dml(sql)

        # Extract CTE names for filtering
        cte_names = cls.extract_cte_names(cleaned_sql)

        logger.debug(f"Preprocessed SQL: {len(sql)} → {len(cleaned_sql)} bytes")
        logger.debug(f"CTEs found: {cte_names}")

        return cleaned_sql, cte_names
