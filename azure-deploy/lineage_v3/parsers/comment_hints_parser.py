"""
Comment Hints Parser

Extracts table dependency hints from specially formatted SQL comments.
Handles edge cases that regex/SQLGlot can't parse (dynamic SQL, complex CATCH blocks, etc.)

Syntax:
    -- @LINEAGE_INPUTS: schema.table1, schema.table2
    -- @LINEAGE_OUTPUTS: schema.table3

Version: 4.2.0
Date: 2025-11-06
"""

import re
from typing import Tuple, Set, Dict, List
import logging

logger = logging.getLogger(__name__)


class CommentHintsParser:
    """Parse @LINEAGE_ hints from SQL comments"""

    # Regex patterns for hint extraction
    INPUT_PATTERN = r'--\s*@LINEAGE_INPUTS:\s*(.+?)(?:\n|$)'
    OUTPUT_PATTERN = r'--\s*@LINEAGE_OUTPUTS:\s*(.+?)(?:\n|$)'

    # Table name pattern: schema.table or [schema].[table]
    TABLE_NAME_PATTERN = r'(?:\[?([a-zA-Z_][a-zA-Z0-9_]*)\]?\.)?(?:\[?([a-zA-Z_][a-zA-Z0-9_]*)\]?)'

    def __init__(self, workspace=None):
        """
        Initialize comment hints parser.

        Args:
            workspace: DuckDBWorkspace for catalog validation (optional)
        """
        self.workspace = workspace
        self._catalog_cache = None

    def extract_hints(self, ddl: str, validate: bool = True) -> Tuple[Set[str], Set[str]]:
        """
        Extract input/output hints from SQL comments.

        Args:
            ddl: SQL stored procedure definition
            validate: Whether to validate against catalog (default True)

        Returns:
            Tuple of (input_tables, output_tables) as sets of schema.table strings
        """
        if not ddl:
            return set(), set()

        # Extract raw hints
        raw_inputs = self._extract_tables_from_hints(ddl, self.INPUT_PATTERN)
        raw_outputs = self._extract_tables_from_hints(ddl, self.OUTPUT_PATTERN)

        logger.debug(f"Raw hints extracted: {len(raw_inputs)} inputs, {len(raw_outputs)} outputs")

        # Validate against catalog if workspace provided
        if validate and self.workspace:
            valid_inputs = self._validate_tables(raw_inputs)
            valid_outputs = self._validate_tables(raw_outputs)

            # Log validation results
            invalid_inputs = raw_inputs - valid_inputs
            invalid_outputs = raw_outputs - valid_outputs

            if invalid_inputs:
                logger.warning(f"Invalid input hints (not in catalog): {invalid_inputs}")
            if invalid_outputs:
                logger.warning(f"Invalid output hints (not in catalog): {invalid_outputs}")

            return valid_inputs, valid_outputs
        else:
            return raw_inputs, raw_outputs

    def _extract_tables_from_hints(self, ddl: str, pattern: str) -> Set[str]:
        """
        Extract table names from hint comments.

        Args:
            ddl: SQL code
            pattern: Regex pattern for hint type (INPUT or OUTPUT)

        Returns:
            Set of normalized table names (schema.table)
        """
        tables = set()

        # Find all matching hint comments
        matches = re.finditer(pattern, ddl, re.IGNORECASE | re.MULTILINE)

        for match in matches:
            hint_content = match.group(1).strip()

            # Split by comma to get individual table names
            table_list = [t.strip() for t in hint_content.split(',')]

            for table_str in table_list:
                if not table_str:
                    continue

                # Normalize table name
                normalized = self._normalize_table_name(table_str)
                if normalized:
                    tables.add(normalized)

        return tables

    def _normalize_table_name(self, table_str: str) -> str:
        """
        Normalize table name to schema.table format.

        Handles formats:
        - schema.table
        - [schema].[table]
        - [schema].table
        - schema.[table]
        - table (assumes dbo schema)

        Args:
            table_str: Raw table name string

        Returns:
            Normalized schema.table string, or empty string if invalid
        """
        table_str = table_str.strip()
        if not table_str:
            return ""

        # Remove brackets and split by dot
        parts = table_str.replace('[', '').replace(']', '').split('.')

        if len(parts) == 2:
            schema, table = parts
            return f"{schema.strip()}.{table.strip()}"
        elif len(parts) == 1:
            # No schema specified, assume dbo
            table = parts[0].strip()
            logger.debug(f"No schema specified for '{table}', assuming dbo")
            return f"dbo.{table}"
        else:
            logger.warning(f"Invalid table name format: '{table_str}' (expected schema.table)")
            return ""

    def _validate_tables(self, tables: Set[str]) -> Set[str]:
        """
        Validate table names against catalog.

        Args:
            tables: Set of schema.table strings

        Returns:
            Set of valid table names (found in catalog)
        """
        if not tables:
            return set()

        # Build catalog cache if not already done
        if self._catalog_cache is None:
            self._build_catalog_cache()

        valid_tables = set()

        for table in tables:
            # Case-insensitive lookup
            table_lower = table.lower()

            if table_lower in self._catalog_cache:
                # Return original case from catalog
                valid_tables.add(self._catalog_cache[table_lower])
            else:
                logger.debug(f"Table not found in catalog: {table}")

        return valid_tables

    def _build_catalog_cache(self):
        """Build case-insensitive catalog cache from workspace."""
        if not self.workspace:
            self._catalog_cache = {}
            return

        try:
            # Query all objects from catalog
            result = self.workspace.conn.execute("""
                SELECT schema_name, object_name, object_type
                FROM objects
                WHERE object_type IN ('Table', 'View', 'Stored Procedure')
            """).fetchall()

            # Build case-insensitive lookup
            self._catalog_cache = {}
            for row in result:
                schema, name, obj_type = row
                full_name = f"{schema}.{name}"
                self._catalog_cache[full_name.lower()] = full_name

            logger.debug(f"Built catalog cache with {len(self._catalog_cache)} objects")

        except Exception as e:
            logger.error(f"Failed to build catalog cache: {e}")
            self._catalog_cache = {}

    def get_hint_stats(self, ddl: str) -> Dict[str, int]:
        """
        Get statistics about hints in a stored procedure.

        Args:
            ddl: SQL stored procedure definition

        Returns:
            Dictionary with hint counts and validation stats
        """
        raw_inputs, raw_outputs = self.extract_hints(ddl, validate=False)
        valid_inputs, valid_outputs = self.extract_hints(ddl, validate=True)

        return {
            'total_hints': len(raw_inputs) + len(raw_outputs),
            'input_hints': len(raw_inputs),
            'output_hints': len(raw_outputs),
            'valid_hints': len(valid_inputs) + len(valid_outputs),
            'invalid_hints': (len(raw_inputs) - len(valid_inputs)) + (len(raw_outputs) - len(valid_outputs))
        }


def extract_comment_hints(ddl: str, workspace=None) -> Tuple[Set[str], Set[str]]:
    """
    Convenience function to extract comment hints.

    Args:
        ddl: SQL stored procedure definition
        workspace: DuckDBWorkspace for catalog validation (optional)

    Returns:
        Tuple of (input_tables, output_tables)
    """
    parser = CommentHintsParser(workspace)
    return parser.extract_hints(ddl)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # Example 1: Dynamic SQL
    example1 = """
    CREATE PROC [dbo].[spDynamicLoad] @tableName VARCHAR(100)
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
    inputs, outputs = parser.extract_hints(example1, validate=False)

    print("Example 1: Dynamic SQL")
    print(f"  Inputs: {inputs}")
    print(f"  Outputs: {outputs}")
    print()

    # Example 2: CATCH block
    example2 = """
    CREATE PROC [dbo].[spLoadWithRecovery]
    AS
    BEGIN TRY
        INSERT INTO dbo.Target SELECT * FROM dbo.Source;
    END TRY
    BEGIN CATCH
        -- @LINEAGE_INPUTS: dbo.Source
        -- @LINEAGE_OUTPUTS: dbo.ErrorRecoveryTable

        INSERT INTO dbo.ErrorRecoveryTable
        SELECT * FROM dbo.Source WHERE ValidationStatus = 'Failed';
    END CATCH
    """

    inputs, outputs = parser.extract_hints(example2, validate=False)

    print("Example 2: CATCH Block")
    print(f"  Inputs: {inputs}")
    print(f"  Outputs: {outputs}")
    print()

    # Example 3: Various formats
    example3 = """
    -- @LINEAGE_INPUTS: [CONSUMPTION_FINANCE].[DimCustomers], dbo.Staging, InvalidTable
    -- @LINEAGE_OUTPUTS: TargetTable
    """

    inputs, outputs = parser.extract_hints(example3, validate=False)

    print("Example 3: Various Formats")
    print(f"  Inputs: {inputs}")
    print(f"  Outputs: {outputs}")
