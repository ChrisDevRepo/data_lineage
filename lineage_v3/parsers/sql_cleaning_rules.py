"""
SQL Cleaning Rules Engine for SQLGlot Pre-processing

A declarative, testable rule-based system for cleaning T-SQL stored procedures
before parsing with SQLGlot.

Design Principles:
1. Each rule is self-documenting (name, description, examples)
2. Rules are testable independently
3. Rules can be enabled/disabled easily
4. Clear execution order
5. Comprehensive logging for debugging

Architecture:
- Rule: Base class for all cleaning rules
- RuleEngine: Orchestrates rule execution
- Built-in rules: Common T-SQL constructs to remove
- Extensible: Easy to add new rules

Version: 1.0.0
Date: 2025-11-06
Author: Claude Code Agent
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Set, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RuleCategory(Enum):
    """Categories for organizing cleaning rules"""
    BATCH_SEPARATOR = "batch_separator"      # GO statements
    VARIABLE_DECLARATION = "variable_decl"   # DECLARE, SET
    ERROR_HANDLING = "error_handling"        # TRY/CATCH, RAISERROR
    EXECUTION = "execution"                  # EXEC, dynamic SQL
    TRANSACTION = "transaction"              # BEGIN TRAN, COMMIT, ROLLBACK
    TABLE_MANAGEMENT = "table_mgmt"          # TRUNCATE, temp tables
    COMMENT = "comment"                      # Comments that confuse parser
    WRAPPER = "wrapper"                      # CREATE PROC, BEGIN/END
    EXTRACTION = "extraction"                # Extract core DML


@dataclass
class CleaningRule(ABC):
    """
    Base class for SQL cleaning rules.

    Each rule is responsible for one specific cleaning operation.
    Rules are self-documenting and testable.
    """

    name: str
    category: RuleCategory
    description: str
    enabled: bool = True
    priority: int = 100  # Lower number = higher priority
    examples_before: List[str] = field(default_factory=list)
    examples_after: List[str] = field(default_factory=list)

    @abstractmethod
    def apply(self, sql: str) -> str:
        """
        Apply the cleaning rule to SQL.

        Args:
            sql: SQL text to clean

        Returns:
            Cleaned SQL text

        Raises:
            Exception: If rule application fails
        """
        pass

    def test(self) -> bool:
        """
        Test the rule with built-in examples.

        Returns:
            True if all examples pass, False otherwise
        """
        for before, expected_after in zip(self.examples_before, self.examples_after):
            actual_after = self.apply(before)
            if actual_after.strip() != expected_after.strip():
                logger.error(f"Rule '{self.name}' test failed!")
                logger.error(f"  Input: {before}")
                logger.error(f"  Expected: {expected_after}")
                logger.error(f"  Actual: {actual_after}")
                return False
        return True

    def __str__(self):
        return f"{self.name} ({self.category.value}): {self.description}"


@dataclass
class RegexRule(CleaningRule):
    """
    Regex-based cleaning rule.

    Simple pattern → replacement cleaning.
    """

    pattern: str = ""
    replacement: str = ""
    flags: int = re.IGNORECASE

    def apply(self, sql: str) -> str:
        """Apply regex substitution"""
        if not self.pattern:
            return sql

        try:
            result = re.sub(self.pattern, self.replacement, sql, flags=self.flags)
            logger.debug(f"Applied rule '{self.name}'")
            return result
        except Exception as e:
            logger.error(f"Rule '{self.name}' failed: {e}")
            return sql  # Return original on error


@dataclass
class CallbackRule(CleaningRule):
    """
    Callback-based cleaning rule.

    For complex logic that can't be expressed as simple regex.
    """

    callback: Optional[Callable[[str], str]] = None

    def apply(self, sql: str) -> str:
        """Apply callback function"""
        if not self.callback:
            return sql

        try:
            result = self.callback(sql)
            logger.debug(f"Applied rule '{self.name}'")
            return result
        except Exception as e:
            logger.error(f"Rule '{self.name}' failed: {e}")
            return sql  # Return original on error


# ============================================================================
# BUILT-IN CLEANING RULES
# ============================================================================

class SQLCleaningRules:
    """
    Collection of built-in SQL cleaning rules.

    Organized by category for clarity.
    """

    # ------------------------------------------------------------------------
    # BATCH SEPARATORS
    # ------------------------------------------------------------------------

    @staticmethod
    def remove_go_statements() -> RegexRule:
        """
        Remove GO statements (T-SQL batch separator).

        GO is not valid SQL - it's a batch separator for SQL Server Management Studio.
        SQLGlot doesn't understand it and will fail.

        Example:
            SELECT * FROM Table1
            GO
            SELECT * FROM Table2
            GO

        Becomes:
            SELECT * FROM Table1
            SELECT * FROM Table2
        """
        return RegexRule(
            name="RemoveGO",
            category=RuleCategory.BATCH_SEPARATOR,
            description="Remove GO batch separators",
            pattern=r'^\s*GO\s*$',
            replacement='',
            flags=re.MULTILINE | re.IGNORECASE,
            priority=10,  # High priority
            examples_before=["SELECT 1\nGO\nSELECT 2"],
            examples_after=["SELECT 1\n\nSELECT 2"]
        )

    # ------------------------------------------------------------------------
    # VARIABLE DECLARATIONS
    # ------------------------------------------------------------------------

    @staticmethod
    def remove_declare_statements() -> RegexRule:
        """
        Remove DECLARE statements (variable declarations).

        DECLARE is T-SQL specific for declaring variables.
        SQLGlot has limited support, especially for complex declarations.

        Example:
            DECLARE @var VARCHAR(100) = SERVERPROPERTY('ServerName')
            DECLARE @count INT

        Becomes:
            (removed)
        """
        return RegexRule(
            name="RemoveDECLARE",
            category=RuleCategory.VARIABLE_DECLARATION,
            description="Remove DECLARE variable declarations",
            pattern=r'DECLARE\s+@\w+[^;]*;?',
            replacement='',
            flags=re.IGNORECASE,
            priority=20,
            examples_before=["DECLARE @var VARCHAR(100);\nSELECT 1"],
            examples_after=["\nSELECT 1"]
        )

    @staticmethod
    def remove_set_statements() -> RegexRule:
        """
        Remove SET statements (variable assignments).

        SET is used for variable assignments in T-SQL.
        We remove these since variables don't affect table dependencies.

        Example:
            SET @var = 'value'
            SET @count = (SELECT COUNT(*) FROM Table1)

        Becomes:
            (removed)
        """
        return RegexRule(
            name="RemoveSET",
            category=RuleCategory.VARIABLE_DECLARATION,
            description="Remove SET variable assignments",
            pattern=r'SET\s+@\w+\s*=[^;]*;?',
            replacement='',
            flags=re.IGNORECASE,
            priority=21,
            examples_before=["SET @var = 'test';\nSELECT 1"],
            examples_after=["\nSELECT 1"]
        )

    # ------------------------------------------------------------------------
    # ERROR HANDLING
    # ------------------------------------------------------------------------

    @staticmethod
    def extract_try_content() -> CallbackRule:
        """
        Extract content from BEGIN TRY...END TRY blocks.

        TRY/CATCH is T-SQL error handling. SQLGlot doesn't support it.
        Strategy: Keep the TRY content (business logic), remove CATCH block.

        Example:
            BEGIN TRY
                INSERT INTO Table1 SELECT * FROM Table2
            END TRY
            BEGIN CATCH
                RAISERROR('Error', 16, 1)
            END CATCH

        Becomes:
            INSERT INTO Table1 SELECT * FROM Table2
        """

        def extract_try(sql: str) -> str:
            # First, remove all CATCH blocks
            sql = re.sub(
                r'BEGIN\s+CATCH\s+.*?\s+END\s+CATCH',
                '',
                sql,
                flags=re.IGNORECASE | re.DOTALL
            )

            # Then extract TRY content
            try_pattern = r'BEGIN\s+TRY\s+(.*?)\s+END\s+TRY'
            matches = re.findall(try_pattern, sql, flags=re.IGNORECASE | re.DOTALL)

            for try_content in matches:
                sql = re.sub(
                    r'BEGIN\s+TRY\s+.*?\s+END\s+TRY',
                    try_content,
                    sql,
                    count=1,
                    flags=re.IGNORECASE | re.DOTALL
                )

            return sql

        return CallbackRule(
            name="ExtractTRY",
            category=RuleCategory.ERROR_HANDLING,
            description="Extract content from TRY blocks, remove CATCH",
            callback=extract_try,
            priority=30,
            examples_before=["BEGIN TRY\nSELECT 1\nEND TRY\nBEGIN CATCH\nSELECT 2\nEND CATCH"],
            examples_after=["SELECT 1"]
        )

    @staticmethod
    def remove_raiserror() -> RegexRule:
        """
        Remove RAISERROR statements.

        RAISERROR is T-SQL for throwing errors.
        Not relevant for table dependency extraction.

        Example:
            RAISERROR('Error message', 16, 1)
            RAISERROR(@msg, @severity, @state)

        Becomes:
            (removed)
        """
        return RegexRule(
            name="RemoveRAISERROR",
            category=RuleCategory.ERROR_HANDLING,
            description="Remove RAISERROR statements",
            pattern=r'RAISERROR\s*\([^)]*\)',
            replacement='',
            flags=re.IGNORECASE,
            priority=31,
            examples_before=["RAISERROR('test', 0, 0);\nSELECT 1"],
            examples_after=["\nSELECT 1"]
        )

    # ------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------

    @staticmethod
    def remove_exec_statements() -> RegexRule:
        """
        Remove EXEC statements (dynamic SQL execution).

        EXEC is used to call stored procedures or execute dynamic SQL.
        Can't extract table dependencies from dynamic SQL at parse time.

        Example:
            EXEC dbo.LogMessage @Param1 = 'value', @Param2 = 123
            EXEC sp_executesql @sql

        Becomes:
            (removed)
        """
        return RegexRule(
            name="RemoveEXEC",
            category=RuleCategory.EXECUTION,
            description="Remove EXEC statements",
            pattern=r'EXEC(?:UTE)?\s+\[?[a-zA-Z_\[\]\.]+\]?\s+[^;]*;?',
            replacement='',
            flags=re.IGNORECASE,
            priority=40,
            examples_before=["EXEC dbo.Test @param = 1;\nSELECT 1"],
            examples_after=["\nSELECT 1"]
        )

    # ------------------------------------------------------------------------
    # TRANSACTIONS
    # ------------------------------------------------------------------------

    @staticmethod
    def remove_transaction_control() -> RegexRule:
        """
        Remove transaction control statements.

        BEGIN TRAN, COMMIT, ROLLBACK are for transaction management.
        Not relevant for table dependency extraction.

        Example:
            BEGIN TRANSACTION
            INSERT INTO Table1 VALUES (1)
            COMMIT TRANSACTION

        Becomes:
            INSERT INTO Table1 VALUES (1)
        """
        return RegexRule(
            name="RemoveTransactionControl",
            category=RuleCategory.TRANSACTION,
            description="Remove BEGIN TRAN, COMMIT, ROLLBACK",
            pattern=r'(?:BEGIN|COMMIT|ROLLBACK)\s+TRAN(?:SACTION)?\s*;?',
            replacement='',
            flags=re.IGNORECASE,
            priority=50,
            examples_before=["BEGIN TRAN;\nSELECT 1;\nCOMMIT TRAN"],
            examples_after=["\nSELECT 1;\n"]
        )

    # ------------------------------------------------------------------------
    # TABLE MANAGEMENT
    # ------------------------------------------------------------------------

    @staticmethod
    def remove_truncate() -> RegexRule:
        """
        Remove TRUNCATE TABLE statements.

        TRUNCATE is DDL for emptying tables.
        The table reference is the target, not a dependency.

        Example:
            TRUNCATE TABLE dbo.TempTable

        Becomes:
            (removed)
        """
        return RegexRule(
            name="RemoveTRUNCATE",
            category=RuleCategory.TABLE_MANAGEMENT,
            description="Remove TRUNCATE TABLE statements",
            pattern=r'TRUNCATE\s+TABLE\s+[^;]+;?',
            replacement='',
            flags=re.IGNORECASE,
            priority=60,
            examples_before=["TRUNCATE TABLE dbo.Test;\nSELECT 1"],
            examples_after=["\nSELECT 1"]
        )

    # ------------------------------------------------------------------------
    # WRAPPER EXTRACTION
    # ------------------------------------------------------------------------

    @staticmethod
    def extract_core_dml() -> CallbackRule:
        """
        Extract core DML from CREATE PROC wrapper.

        Strategy:
        1. Look for WITH (CTEs) or main DML (INSERT/SELECT/UPDATE/DELETE/MERGE)
        2. Extract the longest continuous block
        3. Remove CREATE PROC...AS BEGIN...END wrapper

        This is the KEY transformation that makes SQLGlot work!

        Example:
            CREATE PROC dbo.Test AS
            BEGIN
                WITH cte AS (SELECT * FROM Source)
                INSERT INTO Target SELECT * FROM cte
            END

        Becomes:
            WITH cte AS (SELECT * FROM Source)
            INSERT INTO Target SELECT * FROM cte
        """

        def extract_dml(sql: str) -> str:
            # Pattern for WITH...INSERT/SELECT/UPDATE/DELETE/MERGE
            core_pattern = r'(WITH\s+\w+\s+AS\s*\(.*?\)\s*(?:,\s*\w+\s+AS\s*\(.*?\))*\s*(?:INSERT|SELECT|UPDATE|DELETE|MERGE)\s+.*?)(?=\n\s*(?:END|$))'

            matches = re.findall(core_pattern, sql, flags=re.DOTALL | re.IGNORECASE)
            if matches:
                # Return longest match (most complete)
                return max(matches, key=len).strip()

            # Fallback: Try standalone DML
            dml_pattern = r'((?:INSERT|SELECT|UPDATE|DELETE|MERGE)\s+(?:INTO\s+)?\s*.*?)(?=\n\s*(?:END|$))'
            dml_matches = re.findall(dml_pattern, sql, flags=re.DOTALL | re.IGNORECASE)
            if dml_matches:
                return max(dml_matches, key=len).strip()

            # If no DML found, return cleaned original
            return sql

        return CallbackRule(
            name="ExtractCoreDML",
            category=RuleCategory.EXTRACTION,
            description="Extract core DML from CREATE PROC wrapper",
            callback=extract_dml,
            priority=90,  # Run near end, after other cleaning
            examples_before=["CREATE PROC dbo.T AS BEGIN\nSELECT * FROM T1\nEND"],
            examples_after=["SELECT * FROM T1"]
        )

    # ------------------------------------------------------------------------
    # WHITESPACE CLEANUP
    # ------------------------------------------------------------------------

    @staticmethod
    def cleanup_whitespace() -> RegexRule:
        """
        Clean up excessive whitespace.

        After removing T-SQL constructs, we may have multiple blank lines.
        Clean these up for readability.

        Example:
            SELECT 1


            SELECT 2

        Becomes:
            SELECT 1

            SELECT 2
        """
        return RegexRule(
            name="CleanupWhitespace",
            category=RuleCategory.COMMENT,
            description="Remove excessive blank lines",
            pattern=r'\n\s*\n\s*\n+',
            replacement='\n\n',
            flags=0,
            priority=99,  # Run last
            examples_before=["SELECT 1\n\n\n\nSELECT 2"],
            examples_after=["SELECT 1\n\nSELECT 2"]
        )

    # ------------------------------------------------------------------------
    # NEW RULES (2025-11-07) - Simple, Smart Improvements
    # ------------------------------------------------------------------------

    @staticmethod
    def replace_temp_tables() -> RegexRule:
        """
        Replace temp table references (#table) with dummy schema (dummy.table).

        This is a BRILLIANT simple solution that makes temp tables parseable by SQLGlot!
        Instead of trying to remove temp table DDL, we replace # with dummy. schema,
        making it valid SQL that SQLGlot can parse. Then filter out dummy.* in catalog validation.

        Example:
            SELECT * INTO #TempData FROM SourceTable
            INSERT INTO #TempData VALUES (1, 2)
            SELECT * FROM #TempData

        Becomes:
            SELECT * INTO dummy.TempData FROM SourceTable
            INSERT INTO dummy.TempData VALUES (1, 2)
            SELECT * FROM dummy.TempData

        Why it works:
        - Valid SQL syntax (SQLGlot can parse it)
        - Simple regex replacement
        - Filter out dummy.* objects later
        - No need to handle CREATE TABLE #temp / DROP TABLE #temp separately
        """
        return RegexRule(
            name="ReplaceTempTables",
            category=RuleCategory.TABLE_MANAGEMENT,
            description="Replace #table with dummy.table for parseability",
            pattern=r'#(\w+)',
            replacement=r'dummy.\1',
            flags=re.IGNORECASE,
            priority=15,  # Early - before DECLARE removal
            examples_before=[
                "SELECT * INTO #temp FROM Table1",
                "INSERT INTO #staging SELECT * FROM Table2",
                "SELECT a.ID FROM #temp a JOIN Table3 b ON a.ID = b.ID"
            ],
            examples_after=[
                "SELECT * INTO dummy.temp FROM Table1",
                "INSERT INTO dummy.staging SELECT * FROM Table2",
                "SELECT a.ID FROM dummy.temp a JOIN Table3 b ON a.ID = b.ID"
            ]
        )

    @staticmethod
    def remove_if_object_id_checks() -> RegexRule:
        """
        Remove IF object_id(...) administrative checks.

        These are administrative existence checks before dropping temp tables,
        not actual data lineage. Remove them to reduce noise.

        Example:
            if object_id(N'tempdb..#temp') is not null
            begin drop table #temp; end;

        Becomes:
            (removed)

        Why: Administrative cleanup, not data flow
        """
        return RegexRule(
            name="RemoveIFObjectID",
            category=RuleCategory.TABLE_MANAGEMENT,
            description="Remove IF object_id(...) administrative checks",
            pattern=r"if\s+object_id\s*\(\s*N?['\"]tempdb\.\.[#\w]+['\"]\\s*\)\s+is\s+not\s+null\s+begin\s+drop\s+table\s+[#\w\.]+\s*;?\s*end\s*;?",
            replacement='',
            flags=re.IGNORECASE | re.DOTALL,
            priority=25,  # After temp table replacement
            examples_before=[
                "if object_id(N'tempdb..#temp') is not null\nbegin drop table #temp; end;",
                "IF OBJECT_ID(N'tempdb..#staging') IS NOT NULL BEGIN DROP TABLE #staging END"
            ],
            examples_after=[
                "",
                ""
            ]
        )

    @staticmethod
    def remove_drop_table() -> RegexRule:
        """
        Remove DROP TABLE statements.

        DROP TABLE is administrative cleanup, not data lineage.
        After replacing #temp with dummy.temp, we can safely remove all DROP statements.

        Example:
            DROP TABLE #temp
            DROP TABLE IF EXISTS staging

        Becomes:
            (removed)

        Why: Cleanup operations don't show data flow
        """
        return RegexRule(
            name="RemoveDropTable",
            category=RuleCategory.TABLE_MANAGEMENT,
            description="Remove DROP TABLE statements (not lineage-relevant)",
            pattern=r'drop\s+table\s+(?:if\s+exists\s+)?[#\w\.\[\]]+\s*;?',
            replacement='',
            flags=re.IGNORECASE,
            priority=26,  # After IF EXISTS removal
            examples_before=[
                "DROP TABLE #temp",
                "DROP TABLE IF EXISTS staging.temp_data",
                "drop table [dbo].[TempStaging];"
            ],
            examples_after=[
                "",
                "",
                ""
            ]
        )

    @staticmethod
    def flatten_simple_begin_end() -> RegexRule:
        """
        Flatten standalone BEGIN/END blocks (non-control-flow).

        Remove BEGIN/END wrappers that don't belong to IF/WHILE/TRY control structures.
        This reduces nesting depth without losing DML statements.

        Example:
            BEGIN
                INSERT INTO Table1 SELECT * FROM Table2
            END

        Becomes:
            INSERT INTO Table1 SELECT * FROM Table2

        Why: Standalone BEGIN/END adds complexity without value
        Note: Preserves BEGIN/END for TRY/CATCH, IF, WHILE (handled by other rules)
        """
        return RegexRule(
            name="FlattenSimpleBEGIN",
            category=RuleCategory.WRAPPER,
            description="Remove standalone BEGIN/END wrappers",
            pattern=r'\n\s*BEGIN\s*\n\s*((?:INSERT|UPDATE|DELETE|MERGE|SELECT|WITH)[\s\S]*?)\n\s*END\s*;?',
            replacement=r'\n\1\n',
            flags=re.IGNORECASE,
            priority=35,  # After control flow handling
            examples_before=[
                "\nBEGIN\n    INSERT INTO Target SELECT * FROM Source\nEND",
                "\nBEGIN\n    UPDATE Table1 SET X = 1\nEND;"
            ],
            examples_after=[
                "\n    INSERT INTO Target SELECT * FROM Source\n",
                "\n    UPDATE Table1 SET X = 1\n"
            ]
        )

    @staticmethod
    def extract_if_block_dml() -> RegexRule:
        """
        Extract DML from simple IF blocks.

        Pull INSERT/UPDATE/DELETE/MERGE statements from IF wrappers.
        This captures conditional lineage even when condition might not be met at runtime.

        Example:
            IF @condition = 1
            BEGIN
                INSERT INTO Target SELECT * FROM Source
            END

        Becomes:
            INSERT INTO Target SELECT * FROM Source

        Why: We want lineage regardless of runtime condition
        Note: Only handles simple single-statement IF blocks
        """
        return RegexRule(
            name="ExtractIFBlockDML",
            category=RuleCategory.EXTRACTION,
            description="Extract DML from IF blocks",
            pattern=r'IF\s+[^B]+?\s+BEGIN\s+(INSERT|UPDATE|DELETE|MERGE)\s+([^;]+?)\s*;?\s*END',
            replacement=r'\1 \2',
            flags=re.IGNORECASE | re.DOTALL,
            priority=40,  # After BEGIN/END flattening
            examples_before=[
                "IF @x = 1 BEGIN INSERT INTO T1 SELECT * FROM T2 END",
                "IF EXISTS (SELECT 1) BEGIN UPDATE Table SET X = 1 END"
            ],
            examples_after=[
                "INSERT INTO T1 SELECT * FROM T2",
                "UPDATE Table SET X = 1"
            ]
        )


class RuleEngine:
    """
    Orchestrates execution of SQL cleaning rules.

    Features:
    - Rules executed in priority order
    - Can enable/disable rules
    - Comprehensive logging
    - Rule testing
    """

    def __init__(self, rules: Optional[List[CleaningRule]] = None):
        """
        Initialize rule engine.

        Args:
            rules: List of cleaning rules (uses defaults if None)
        """
        if rules is None:
            # Load all built-in rules
            self.rules = self._load_default_rules()
        else:
            self.rules = rules

        # Sort by priority (lower number = higher priority)
        self.rules.sort(key=lambda r: r.priority)

    @staticmethod
    def _load_default_rules() -> List[CleaningRule]:
        """Load all built-in cleaning rules (15 total - 10 original + 5 new)"""
        return [
            SQLCleaningRules.remove_go_statements(),
            SQLCleaningRules.replace_temp_tables(),              # NEW (Priority 15)
            SQLCleaningRules.remove_declare_statements(),
            SQLCleaningRules.remove_set_statements(),
            SQLCleaningRules.remove_if_object_id_checks(),       # NEW (Priority 25)
            SQLCleaningRules.remove_drop_table(),                # NEW (Priority 26)
            SQLCleaningRules.extract_try_content(),
            SQLCleaningRules.remove_raiserror(),
            SQLCleaningRules.flatten_simple_begin_end(),         # NEW (Priority 35)
            SQLCleaningRules.extract_if_block_dml(),             # NEW (Priority 40)
            SQLCleaningRules.remove_exec_statements(),
            SQLCleaningRules.remove_transaction_control(),
            SQLCleaningRules.remove_truncate(),
            SQLCleaningRules.extract_core_dml(),
            SQLCleaningRules.cleanup_whitespace(),
        ]

    def apply_all(self, sql: str, verbose: bool = False) -> str:
        """
        Apply all enabled rules to SQL.

        Args:
            sql: SQL to clean
            verbose: If True, log each rule application

        Returns:
            Cleaned SQL
        """
        result = sql

        for rule in self.rules:
            if not rule.enabled:
                if verbose:
                    logger.info(f"Skipping disabled rule: {rule.name}")
                continue

            if verbose:
                logger.info(f"Applying rule: {rule.name}")

            result = rule.apply(result)

        return result.strip()

    def test_all_rules(self) -> bool:
        """
        Test all rules with their built-in examples.

        Returns:
            True if all tests pass, False otherwise
        """
        all_passed = True

        for rule in self.rules:
            if not rule.examples_before:
                logger.warning(f"Rule '{rule.name}' has no test examples")
                continue

            if rule.test():
                logger.info(f"✓ Rule '{rule.name}' tests passed")
            else:
                logger.error(f"✗ Rule '{rule.name}' tests FAILED")
                all_passed = False

        return all_passed

    def get_rules_by_category(self, category: RuleCategory) -> List[CleaningRule]:
        """Get all rules in a specific category"""
        return [r for r in self.rules if r.category == category]

    def disable_rule(self, rule_name: str):
        """Disable a rule by name"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"Disabled rule: {rule_name}")
                return
        logger.warning(f"Rule not found: {rule_name}")

    def enable_rule(self, rule_name: str):
        """Enable a rule by name"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"Enabled rule: {rule_name}")
                return
        logger.warning(f"Rule not found: {rule_name}")

    def list_rules(self):
        """Print all rules"""
        print("\n" + "="*80)
        print("SQL CLEANING RULES")
        print("="*80)

        by_category = {}
        for rule in self.rules:
            cat = rule.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(rule)

        for category, rules in sorted(by_category.items()):
            print(f"\n{category.upper()}")
            print("-" * 80)
            for rule in rules:
                status = "✓" if rule.enabled else "✗"
                print(f"  {status} [{rule.priority:3d}] {rule.name}")
                print(f"      {rule.description}")

        print("\n" + "="*80)
