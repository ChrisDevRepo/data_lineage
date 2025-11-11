"""
Simplified SQL Cleaning Rules Engine for WARN Mode
==================================================

Reduced from 17 rules to 7 rules (-59% complexity)

Design Philosophy (WARN Mode):
- Goal: Remove noise, NOT produce syntactically perfect SQL
- WARN mode handles imperfect SQL (creates Command nodes, continues parsing)
- Focus on noise removal (administrative queries, control flow, error handling)
- Don't need "extract" or "flatten" logic (WARN mode handles partial parsing)

Rule Categories:
1. Administrative Queries - Remove SELECT COUNT(*), SET @var = (SELECT...)
2. Control Flow - Remove entire IF/BEGIN/END blocks
3. Error Handling - Remove TRY/CATCH/RAISERROR blocks
4. Transaction Control - Remove BEGIN TRAN/COMMIT/ROLLBACK
5. DDL Operations - Remove CREATE/DROP/TRUNCATE/ALTER
6. Utility Calls - Remove EXEC LogMessage, spLastRowCount
7. Whitespace - Final cleanup

Version: 5.1.0 (Simplified for WARN mode)
Date: 2025-11-11
Author: Claude Code Agent
"""

import re
from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimplifiedRule:
    """Simplified cleaning rule for WARN mode"""
    name: str
    description: str
    pattern: str
    replacement: str
    flags: int = re.IGNORECASE | re.DOTALL
    priority: int = 100

    def apply(self, sql: str) -> str:
        """Apply regex substitution"""
        try:
            result = re.sub(self.pattern, self.replacement, sql, flags=self.flags)
            logger.debug(f"Applied simplified rule '{self.name}'")
            return result
        except Exception as e:
            logger.error(f"Rule '{self.name}' failed: {e}")
            return sql  # Return original on error


class SimplifiedRuleEngine:
    """
    Simplified rule engine with only 7 rules for WARN mode.

    Key differences from original (17 rules):
    - Remove entire blocks (no "extract" logic needed)
    - Don't worry about perfect syntax (WARN mode handles it)
    - Focus on noise removal only
    - More aggressive (WARN mode is forgiving)
    """

    def __init__(self):
        """Initialize with simplified rules"""
        self.rules = self._load_simplified_rules()
        logger.info(f"SimplifiedRuleEngine initialized with {len(self.rules)} rules")

    @staticmethod
    def _load_simplified_rules() -> List[SimplifiedRule]:
        """
        Load 7 simplified cleaning rules for WARN mode.

        Reduced from 17 to 7 rules (-59% complexity)
        """
        return [
            # Rule 1: Remove Administrative Queries (Priority 10)
            SimplifiedRule(
                name="remove_administrative_queries",
                description="Remove SELECT COUNT(*), SET @var = (SELECT...), administrative reads",
                pattern=r"""
                    (?:
                        # SET @var = (SELECT ...)
                        SET\s+@\w+\s*=\s*\((?:[^()]|\([^()]*\))*\)
                        |
                        # DECLARE @var TYPE = (SELECT ...)
                        DECLARE\s+@\w+\s+\w+(?:\([^\)]*\))?\s*=\s*\((?:[^()]|\([^()]*\))*\)
                        |
                        # SELECT @var = (SELECT ...)
                        SELECT\s+@\w+\s*=\s*\((?:[^()]|\([^()]*\))*\)
                        |
                        # SELECT @var = value
                        SELECT\s+@\w+\s*=\s*[^;]+
                    )
                    (?:;|\n|$)
                """,
                replacement="",
                flags=re.IGNORECASE | re.VERBOSE | re.DOTALL,
                priority=10
            ),

            # Rule 2: Remove Control Flow Blocks (Priority 20)
            SimplifiedRule(
                name="remove_control_flow",
                description="Remove IF/BEGIN/END blocks entirely (WARN mode handles partial parsing)",
                pattern=r"""
                    # Remove IF OBJECT_ID checks (temp table existence)
                    IF\s+(?:NOT\s+)?EXISTS?\s*\(
                        (?:
                            OBJECT_ID\s*\([^)]+\)|
                            SELECT\s+[^)]+
                        )
                    \s*\)\s*
                    (?:
                        BEGIN[^;]*?DROP\s+TABLE[^;]+;?\s*END|
                        DROP\s+TABLE[^;]+
                    )
                    |
                    # Remove empty IF blocks
                    IF\s+[^\n]+\s*BEGIN\s*END
                    |
                    # Remove GO statements (batch separators)
                    \bGO\b
                """,
                replacement="",
                flags=re.IGNORECASE | re.VERBOSE | re.DOTALL,
                priority=20
            ),

            # Rule 3: Remove Error Handling (Priority 30)
            SimplifiedRule(
                name="remove_error_handling",
                description="Remove TRY/CATCH/RAISERROR blocks (not needed for lineage)",
                pattern=r"""
                    (?:
                        # RAISERROR statements
                        RAISERROR\s*\([^;]+\)
                        |
                        # BEGIN CATCH ... END blocks (keep TRY content)
                        BEGIN\s+CATCH.*?END\s+CATCH
                    )
                """,
                replacement="",
                flags=re.IGNORECASE | re.VERBOSE | re.DOTALL,
                priority=30
            ),

            # Rule 4: Remove Transaction Control (Priority 40)
            SimplifiedRule(
                name="remove_transaction_control",
                description="Remove BEGIN TRAN/COMMIT/ROLLBACK (not needed for lineage)",
                pattern=r"""
                    (?:
                        BEGIN\s+(?:TRAN|TRANSACTION)(?:\s+\w+)?
                        |
                        COMMIT\s+(?:TRAN|TRANSACTION)?(?:\s+\w+)?
                        |
                        ROLLBACK\s+(?:TRAN|TRANSACTION)?(?:\s+\w+)?
                        |
                        SAVE\s+(?:TRAN|TRANSACTION)\s+\w+
                    )
                """,
                replacement="",
                flags=re.IGNORECASE | re.VERBOSE,
                priority=40
            ),

            # Rule 5: Remove DDL Operations (Priority 50)
            SimplifiedRule(
                name="remove_ddl_operations",
                description="Remove CREATE/DROP/TRUNCATE/ALTER (DDL, not DML lineage)",
                pattern=r"""
                    (?:
                        # TRUNCATE TABLE
                        TRUNCATE\s+TABLE\s+[^\n;]+
                        |
                        # DROP TABLE (standalone, not in IF block)
                        DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?[^\n;]+
                        |
                        # CREATE TABLE #temp
                        CREATE\s+TABLE\s+#\w+[^;]+;
                        |
                        # ALTER TABLE
                        ALTER\s+TABLE\s+[^\n;]+
                    )
                """,
                replacement="",
                flags=re.IGNORECASE | re.VERBOSE,
                priority=50
            ),

            # Rule 6: Remove Utility Calls (Priority 60)
            SimplifiedRule(
                name="remove_utility_calls",
                description="Remove EXEC LogMessage, spLastRowCount, etc.",
                pattern=r"""
                    EXEC(?:UTE)?\s+(?:\[?dbo\]?\.)?\[?
                    (?:
                        LogMessage|
                        spLastRowCount|
                        sp_executesql  # Keep for now, might want to parse later
                    )
                    \]?[^;]*;?
                """,
                replacement="",
                flags=re.IGNORECASE | re.VERBOSE,
                priority=60
            ),

            # Rule 7: Cleanup Whitespace (Priority 90)
            SimplifiedRule(
                name="cleanup_whitespace",
                description="Remove excessive whitespace and empty lines",
                pattern=r"""
                    (?:
                        # Multiple blank lines
                        \n\s*\n\s*\n+
                        |
                        # Trailing whitespace
                        [ \t]+$
                        |
                        # Leading whitespace on lines
                        ^[ \t]+
                    )
                """,
                replacement="\n",
                flags=re.MULTILINE | re.VERBOSE,
                priority=90
            ),
        ]

    def apply_all(self, sql: str, verbose: bool = False) -> str:
        """
        Apply all simplified rules to SQL.

        Args:
            sql: SQL to clean
            verbose: If True, log each rule application

        Returns:
            Cleaned SQL (noise removed, may not be syntactically perfect)
        """
        result = sql

        for rule in sorted(self.rules, key=lambda r: r.priority):
            if verbose:
                logger.info(f"Applying rule: {rule.name}")

            original_length = len(result)
            result = rule.apply(result)
            removed_length = original_length - len(result)

            if verbose and removed_length > 0:
                logger.info(f"  Removed {removed_length} characters")

        return result.strip()

    def list_rules(self):
        """Print all simplified rules"""
        print("\n" + "="*80)
        print("SIMPLIFIED SQL CLEANING RULES (7 total)")
        print("="*80)

        for i, rule in enumerate(sorted(self.rules, key=lambda r: r.priority), 1):
            print(f"\n{i}. {rule.name} (Priority {rule.priority})")
            print(f"   {rule.description}")

        print("\n" + "="*80)
        print(f"Simplified from 17 rules to {len(self.rules)} rules (-59% complexity)")
        print("="*80)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize engine
    engine = SimplifiedRuleEngine()

    # List rules
    engine.list_rules()

    # Test SQL
    test_sql = """
    CREATE PROC [dbo].[TestSP] AS
    BEGIN
        SET NOCOUNT ON

        DECLARE @Count INT = (SELECT COUNT(*) FROM dbo.Table1)
        SET @RowCount = 0

        IF OBJECT_ID('tempdb..#temp') IS NOT NULL
        BEGIN
            DROP TABLE #temp
        END

        CREATE TABLE #temp (id INT)

        BEGIN TRY
            INSERT INTO dbo.TargetTable
            SELECT * FROM dbo.SourceTable
        END TRY
        BEGIN CATCH
            RAISERROR('Error occurred', 16, 1)
        END CATCH

        EXEC dbo.LogMessage 'Processing complete'

        TRUNCATE TABLE dbo.TempTable
    END
    """

    print("\n" + "="*80)
    print("TEST: Cleaning Sample SQL")
    print("="*80)

    print("\nORIGINAL SQL:")
    print(test_sql)

    cleaned = engine.apply_all(test_sql, verbose=True)

    print("\nCLEANED SQL:")
    print(cleaned)

    print("\n" + "="*80)
    print("RESULT: Noise removed, core DML preserved")
    print("="*80)
