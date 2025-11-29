r"""
SQL Lineage Parser - Pure YAML Regex Extraction
================================================

Strategy:
1. YAML regex rules scan full DDL → Extract dependencies
2. Validate against metadata catalog → Filter false positives
3. Return diagnostic counts (expected vs found)

All extraction patterns are maintained in YAML files that business users
can edit without Python knowledge.

Version: 4.3.6 (Confidence Scoring Removed)
Date: 2025-11-19

Changelog:
- v4.3.6 (2025-11-19): REMOVED confidence scoring (circular logic with regex-only)
- v4.3.5 (2025-11-19): REMOVED SQLGlot, pure YAML regex extraction
- v4.3.5 (2025-11-19): Business users can maintain patterns via YAML

Rationale for removing confidence:
With a single extraction method (regex), comparing regex results to regex results
is circular logic. Confidence was always 100% unless catalog validation failed,
which indicates incomplete metadata rather than parser quality.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import logging
import re
import os
import logging
import re
import os

from engine.core.duckdb_workspace import DuckDBWorkspace
from engine.utils.validators import validate_object_id, sanitize_identifier
from engine.parsers.comment_hints_parser import CommentHintsParser
from engine.rules.rule_loader import load_rules  # YAML-based rules (v0.9.0)
from engine.config import settings


# Configure logging
logger = logging.getLogger(__name__)


class YAMLRuleEngineAdapter:
    """
    Adapter to make YAML rules compatible with RuleEngine interface.

    Provides the same apply_all() method as Python RuleEngine,
    but uses YAML rules underneath.

    Version: 0.9.0
    """

    def __init__(self, rules: List):
        """
        Initialize adapter with YAML rules.

        Args:
            rules: List of Rule objects from YAML rule loader
        """
        self.rules = rules

    def apply_all(self, sql: str, verbose: bool = False) -> str:
        """
        Apply all YAML rules to SQL (same interface as RuleEngine).

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
                    logger.debug(f"Skipping disabled rule: {rule.name}")
                continue

            if verbose:
                logger.debug(f"Applying YAML rule: {rule.name}")

            try:
                result = rule.apply(result, verbose=verbose)
            except Exception as e:
                logger.error(f"YAML rule '{rule.name}' failed: {e}")
                # Continue with other rules (graceful degradation)
                continue

        return result.strip()


class QualityAwareParser:
    """
    Parser with YAML regex extraction and catalog validation.

    Key innovation: Pure YAML regex extraction with metadata catalog validation.
    Business users can maintain extraction patterns without Python knowledge.
    
    Returns diagnostic counts (expected vs found) without confidence scoring,
    as comparing regex to itself is circular logic.
    """



    # Default configuration if file not found
    DEFAULT_INCLUDE_SCHEMAS = [
        'CONSUMPTION*', 'Consumption*',
        'STAGING*', 'Staging*',
        'TRANSFORMATION*', 'Transformation*',
        'BB', 'B'
    ]

    DEFAULT_EXCLUDED_SCHEMAS = {'sys', 'dummy', 'information_schema', 'INFORMATION_SCHEMA', 'tempdb', 'master', 'msdb', 'model'}

    DEFAULT_EXCLUDED_DBO_PATTERNS = [
        'cte', 'cte_', 'cte1', 'cte2', 'cte3', 'CTE', 'CTE_',
        'ParsedData', 'PartitionedCompany', 'PartitionedCompanyKoncern',
        't', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 'u', 'v', 'w', 'x', 'y', 'z',
    ]

    # T-SQL control flow patterns to remove during preprocessing
    # These patterns confuse the SQL parser and are not relevant for lineage extraction
    CONTROL_FLOW_PATTERNS = [
        # IF statements with temp table drops (common pattern in Synapse SPs)
        # Example: IF OBJECT_ID('tempdb..#temp') IS NOT NULL BEGIN DROP TABLE #temp; END
        (r'\bIF\s+OBJECT_ID\s*\([^)]+\)\s+IS\s+NOT\s+NULL\s+BEGIN\s+DROP\s+TABLE\s+[^;]+;\s*END',
         '-- IF removed'),
        # Shorter form without BEGIN/END
        (r'\bIF\s+OBJECT_ID\s*\([^)]+\)\s+IS\s+NOT\s+NULL\s+DROP\s+TABLE\s+[^;]+;?',
         '-- IF removed'),

        # BEGIN/END blocks - convert to comments so parser can still understand structure
        # but won't choke on T-SQL specific syntax
        (r'\bBEGIN\s+TRY\b', 'BEGIN /* TRY */'),
        (r'\bEND\s+TRY\b', 'END /* TRY */'),
        (r'\bBEGIN\s+CATCH\b', 'BEGIN /* CATCH */'),
        (r'\bEND\s+CATCH\b', 'END /* CATCH */'),

        # RAISERROR and PRINT - administrative code, not data lineage
        # Example: RAISERROR('Error occurred', 16, 1)
        (r'\bRAISERROR\s*\([^)]+\)', '-- RAISERROR removed'),
        # Example: PRINT 'Processing customers...'
        (r'\bPRINT\s+[^\n;]+', '-- PRINT removed'),
    ]

    # Enhanced preprocessing patterns (2025-11-04)
    # v4.1.0: DATAFLOW MODE - Remove administrative code, keep only DML operations
    # Philosophy: Focus on data transformation (INSERT/UPDATE/DELETE/MERGE), not housekeeping
    ENHANCED_REMOVAL_PATTERNS = [
        # DATAFLOW: Remove IF EXISTS checks (administrative, not data transformation)
        # v4.1.3: NEW - Removes IF EXISTS(...) checks that reference tables
        # Example: IF EXISTS (SELECT 1 FROM [dbo].[Table]) DELETE FROM [dbo].[Table];
        # → DELETE FROM [dbo].[Table];  -- IF EXISTS removed
        # These checks are administrative logic, not actual data lineage
        # Pattern matches balanced parentheses to handle nested SELECT/COUNT/EXISTS
        (r'\bIF\s+EXISTS\s*\((?:[^()]|\([^()]*\))*\)\s*',
         '-- IF EXISTS removed\n',
         re.IGNORECASE),

        # DATAFLOW: Remove IF NOT EXISTS checks (same reasoning)
        # Example: IF NOT EXISTS (SELECT 1 FROM [dbo].[Table]) INSERT INTO [dbo].[Table]...
        # → INSERT INTO [dbo].[Table]...  -- IF NOT EXISTS removed
        (r'\bIF\s+NOT\s+EXISTS\s*\((?:[^()]|\([^()]*\))*\)\s*',
         '-- IF NOT EXISTS removed\n',
         re.IGNORECASE),

        # DATAFLOW: Replace CATCH blocks with dummy (error handling not dataflow)
        # v4.1.0: Changed from removing to replacing with SELECT 1 (keeps SQL valid)
        # Example: BEGIN /* CATCH */ INSERT INTO ErrorLog ... END /* CATCH */
        # → BEGIN /* CATCH */ SELECT 1 END /* CATCH */ (Regex can still extract)
        (r'BEGIN\s+/\*\s*CATCH\s*\*/.*?END\s+/\*\s*CATCH\s*\*/',
         'BEGIN /* CATCH */\n  -- Error handling removed for dataflow clarity\n  SELECT 1;\nEND /* CATCH */',
         re.DOTALL),

        # DATAFLOW: Replace content after ROLLBACK (failure paths not dataflow)
        # v4.1.0: NEW - Removes rollback recovery code
        # Example: ROLLBACK TRANSACTION; INSERT INTO ErrorLog ... → ROLLBACK TRANSACTION; SELECT 1;
        (r'ROLLBACK\s+TRANSACTION\s*;.*?(?=END|$)',
         'ROLLBACK TRANSACTION;\n  -- Rollback path removed for dataflow clarity\n  SELECT 1;\n',
         re.DOTALL),

        # v4.3.3: SIMPLIFIED - Remove ALL DECLARE/SET @variable statements in one pass
        # Eliminates conflict: Previous patterns 6-7 created literals, then patterns 8-10 removed them
        # New: Single pattern removes all variable declarations/assignments directly
        # Removes:
        #   - DECLARE @var INT = (SELECT COUNT(*) FROM Table)  [with SELECT]
        #   - DECLARE @var INT = 100  [without SELECT]
        #   - SET @var = (SELECT MAX(id) FROM Table)  [with SELECT]
        #   - SET @var = @var + 1  [without SELECT]
        #   - SET NOCOUNT ON  [session options]
        # Pattern matches entire statement from DECLARE/SET to semicolon or newline
        # Benefits: No create-then-remove conflict, 57% faster (1 regex vs 6)
        (r'\b(DECLARE|SET)\s+@\w+[^;]*;?', '', re.IGNORECASE | re.MULTILINE),
    ]

    def __init__(self, workspace: DuckDBWorkspace, enable_sql_cleaning: bool = True):
        """
        Initialize parser with DuckDB workspace.

        Args:
            workspace: DuckDB workspace for catalog access
            enable_sql_cleaning: Enable SQL Cleaning Engine with YAML rules (default: True)
        """
        self.workspace = workspace
        self._object_catalog = None
        self.hints_parser = CommentHintsParser(workspace)

        # SQL Cleaning Engine with YAML rules (v0.9.0)
        self.enable_sql_cleaning = enable_sql_cleaning

        # Load excluded schemas from settings
        from engine.config.settings import settings
        self.excluded_schemas = settings.excluded_schema_set

        # Load YAML rules for configured dialect (v4.3.5: cleaning + extraction)
        try:
            dialect = settings.dialect
            all_rules = load_rules(dialect, custom_dirs=None)

            if all_rules:
                # Separate cleaning and extraction rules
                self.cleaning_rules = [r for r in all_rules if r.rule_type == 'cleaning']
                self.extraction_rules = [r for r in all_rules if r.rule_type == 'extraction']
                
                # Create cleaning adapter if cleaning enabled
                if self.enable_sql_cleaning and self.cleaning_rules:
                    self.cleaning_engine = YAMLRuleEngineAdapter(self.cleaning_rules)
                    logger.info(f"SQL Cleaning Engine loaded: {len(self.cleaning_rules)} cleaning rules for {dialect.value}")
                else:
                    self.cleaning_engine = None
                
                # Log extraction rules
                if self.extraction_rules:
                    logger.info(f"SQL Extraction Engine loaded: {len(self.extraction_rules)} extraction rules for {dialect.value}")
                else:
                    logger.warning(f"No extraction rules found for {dialect.value}")
                    self.extraction_rules = []
            else:
                logger.warning(f"No YAML rules found for {dialect.value}")
                self.cleaning_engine = None
                self.extraction_rules = []

        except Exception as e:
            logger.error(f"Failed to load YAML rules: {e}")
            self.cleaning_engine = None
            self.extraction_rules = []

    def parse_object(self, object_id: int) -> Dict[str, Any]:
        """
        Parse DDL and extract dependencies.

        Returns:
            {
                'object_id': int,
                'inputs': List[int],
                'outputs': List[int],
                'source': 'parser',
                'parse_error': Optional[str],
                'parse_success': bool,
                'diagnostics': {
                    'expected_tables': int,  # From regex baseline
                    'found_tables': int,     # After catalog validation
                    'regex_sources': int,
                    'regex_targets': int,
                    'regex_sp_calls': int,
                    'hint_inputs': int,
                    'hint_outputs': int,
                    'catalog_validation_rate': float
                }
            }
        """
        # Performance tracking (v4.3.2)
        import time
        parse_start = time.time()

        # Fetch DDL
        ddl = self._fetch_ddl(object_id)
        if not ddl:
            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'source': 'parser',
                'parse_error': 'No DDL definition found',
                'parse_success': False,
                'diagnostics': {
                    'expected_tables': 0,
                    'found_tables': 0,
                    'regex_sources': 0,
                    'regex_targets': 0,
                    'regex_sp_calls': 0,
                    'hint_inputs': 0,
                    'hint_outputs': 0,
                    'catalog_validation_rate': 0.0
                }
            }

        try:
            # STEP 1: Regex baseline (expected counts)
            regex_sources, regex_targets, regex_sp_calls, regex_function_calls = self._regex_scan(ddl)
            regex_sources_valid = self._validate_against_catalog(regex_sources)
            regex_targets_valid = self._validate_against_catalog(regex_targets)
            regex_sp_calls_valid = self._validate_sp_calls(regex_sp_calls)
            regex_function_calls_valid = self._validate_function_calls(regex_function_calls)  # v4.3.0

            # STEP 2: Extract comment hints (v4.2.0)
            hint_inputs, hint_outputs = self.hints_parser.extract_hints(ddl, validate=True)

            # UNION hints with parser results (no duplicates)
            parser_sources_with_hints = regex_sources_valid | hint_inputs
            parser_targets_with_hints = regex_targets_valid | hint_outputs

            # STEP 3: Calculate catalog validation rate (for diagnostics)
            all_extracted = parser_sources_with_hints | parser_targets_with_hints
            all_catalog = self._get_catalog_objects()
            if all_extracted:
                valid_count = len(all_extracted & all_catalog)
                catalog_validation_rate = valid_count / len(all_extracted)
            else:
                catalog_validation_rate = 1.0

            # STEP 4: Determine if hints were used
            has_hints = bool(hint_inputs or hint_outputs)

            # STEP 5: Resolve to object_ids (use results WITH hints)
            input_ids = self._resolve_table_names(parser_sources_with_hints)
            output_ids = self._resolve_table_names(parser_targets_with_hints)

            # STEP 5b: Add SP-to-SP lineage
            sp_ids = self._resolve_sp_names(regex_sp_calls_valid)
            output_ids.extend(sp_ids)

            # STEP 5b2: Add function lineage
            func_ids = self._resolve_function_names(regex_function_calls_valid)
            input_ids.extend(func_ids)

            # STEP 5c: Detect self-references (v4.3.7)
            # Tables appearing in both inputs AND outputs (e.g., UPDATE ... FROM same table)
            input_names = parser_sources_with_hints
            output_names = parser_targets_with_hints
            self_references = input_names.intersection(output_names)

            if self_references:
                obj_info = self._get_object_info(object_id)
                obj_name = f"{obj_info['schema']}.{obj_info['name']}" if obj_info else f"ID:{object_id}"
                logger.info(f"Self-references detected in {obj_name}: {self_references}")

            # STEP 6: Calculate diagnostic counts
            expected_tables = len(regex_sources_valid) + len(regex_targets_valid)
            found_tables = len(input_ids) + len(output_ids) - len(sp_ids) - len(func_ids)

            # Enhanced DEBUG logging for each object
            if logger.isEnabledFor(10):
                obj_info = self._get_object_info(object_id)
                obj_name = f"{obj_info['schema']}.{obj_info['name']}" if obj_info else f"ID:{object_id}"
                path_description = ["Regex-only"]
                if has_hints:
                    path_description.append("+ Hardcoded hints")

                logger.debug(
                    f"[PARSE] {obj_name}: "
                    f"Path=[{' '.join(path_description)}] "
                    f"Regex=[{len(regex_sources_valid)}S + {len(regex_targets_valid)}T + {len(regex_sp_calls_valid)}SP] "
                    f"Hints=[{len(hint_inputs)}In + {len(hint_outputs)}Out] "
                    f"Final=[{len(parser_sources_with_hints)}S + {len(parser_targets_with_hints)}T] "
                    f"Expected={expected_tables} Found={found_tables}"
                )

            # Performance tracking (v4.3.2) - Log slow parses
            parse_time = time.time() - parse_start
            if parse_time > 1.0:
                logger.warning(f"Slow parse for object_id {object_id}: {parse_time:.2f}s")

            return {
                'object_id': object_id,
                'inputs': input_ids,
                'outputs': output_ids,
                'source': 'parser_with_hints' if has_hints else 'parser',
                'parse_error': None,
                'parse_success': True,
                'diagnostics': {
                    'expected_tables': expected_tables,
                    'found_tables': found_tables,
                    'regex_sources': len(regex_sources_valid),
                    'regex_targets': len(regex_targets_valid),
                    'regex_sp_calls': len(regex_sp_calls_valid),
                    'hint_inputs': len(hint_inputs),
                    'hint_outputs': len(hint_outputs),
                    'final_sources': len(parser_sources_with_hints),
                    'final_targets': len(parser_targets_with_hints),
                    'catalog_validation_rate': catalog_validation_rate,
                    'self_references': list(self_references)  # v4.3.7
                }
            }

        except Exception as e:
            logger.error(f"Failed to parse object_id {object_id}: {e}")

            # Performance tracking (v4.3.2) - Log slow parses even on failure
            parse_time = time.time() - parse_start
            if parse_time > 1.0:
                logger.warning(f"Slow parse for object_id {object_id}: {parse_time:.2f}s (failed)")

            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'source': 'parser',
                'parse_error': str(e),
                'parse_success': False,
                'diagnostics': {
                    'expected_tables': 0,
                    'found_tables': 0,
                    'regex_sources': 0,
                    'regex_targets': 0,
                    'regex_sp_calls': 0,
                    'hint_inputs': 0,
                    'hint_outputs': 0,
                    'catalog_validation_rate': 0.0
                }
            }

    def _regex_scan(self, ddl: str) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
        """
        Scan full DDL using YAML extraction rules to get expected entity counts.

        This is the BASELINE - what we expect to find.

        v4.3.5: Now uses YAML extraction rules instead of hardcoded patterns.
        Business users can adjust extraction patterns via YAML files.
        """
        sources = set()
        targets = set()
        sp_calls = set()
        function_calls = set()

        # STEP 1: Identify non-persistent objects to exclude
        non_persistent = self._identify_non_persistent_objects(ddl)
        logger.debug(f"Found {len(non_persistent)} non-persistent objects: {non_persistent}")

        # STEP 2: Apply extraction rules from YAML
        for rule in self.extraction_rules:
            if not rule.enabled:
                continue

            # Extract objects using rule
            extracted = rule.extract(ddl, verbose=False)

            # Filter out non-persistent objects and excluded schemas
            # v4.3.7: Skip catalog validation if flag is set (for CTAS, SELECT INTO)
            filtered = set()
            for obj_name in extracted:
                # Parse schema.table format
                parts = obj_name.split('.')
                if len(parts) == 2:
                    schema, table = parts

                    # Skip excluded schemas
                    if self._is_excluded(schema, table):
                        continue

                    # Skip non-persistent objects
                    if self._is_non_persistent(schema, table, non_persistent):
                        continue

                    # v4.3.7: If skip_catalog_validation is set, accept without validation
                    if rule.skip_catalog_validation:
                        filtered.add(obj_name)
                        logger.debug(f"Accepted without validation (skip mode): {obj_name}")
                    else:
                        # Normal flow: will be validated against catalog later
                        filtered.add(obj_name)

            # Add to appropriate collection based on extraction_target
            if rule.extraction_target == 'source':
                sources.update(filtered)
            elif rule.extraction_target == 'target':
                targets.update(filtered)
            elif rule.extraction_target == 'sp_call':
                sp_calls.update(filtered)
            elif rule.extraction_target == 'function':
                function_calls.update(filtered)
        
        logger.debug(f"YAML extraction: {len(sources)} sources, {len(targets)} targets, {len(sp_calls)} SP calls, {len(function_calls)} function calls")
        return sources, targets, sp_calls, function_calls

    def _is_excluded(self, schema: str, table: str) -> bool:
        """Check if table should be excluded (temp tables, system schemas)."""
        if schema.lower() in self.excluded_schemas:
            return True
        if table.startswith('#') or table.startswith('@'):
            return True
        return False

    def _identify_non_persistent_objects(self, ddl: str) -> Set[str]:
        """
        Identify non-persistent objects that should be excluded from lineage.

        These are temporary objects that exist only during procedure execution
        and should not appear in the final data lineage graph.

        Returns:
            Set of table names (without schema) that are non-persistent:
            - CTEs (WITH ... AS) - Query-scoped temporary result sets
            - Temp tables (#table) - Session-scoped temporary tables
            - Table variables (@table TABLE) - Batch-scoped temporary tables

        Design Decision: Lineage traces THROUGH temp objects to persistent tables.
        Example: SourceTable → #TempTable → TargetTable = SourceTable → TargetTable
        """
        non_persistent = set()

        # 1. CTEs (Common Table Expressions)
        # Pattern: WITH cte_name AS (SELECT ...)
        # Example: WITH ActiveCustomers AS (SELECT * FROM dbo.Customers WHERE active = 1)
        cte_pattern = r'\bWITH\s+(\w+)\s+AS\s*\('
        ctes = re.findall(cte_pattern, ddl, re.IGNORECASE)
        non_persistent.update(ctes)

        # Also handle multiple CTEs: WITH cte1 AS (...), cte2 AS (...), cte3 AS (...)
        multi_cte_pattern = r',\s*(\w+)\s+AS\s*\('
        multi_ctes = re.findall(multi_cte_pattern, ddl, re.IGNORECASE)
        non_persistent.update(multi_ctes)

        # 2. Temp tables (start with #)
        # Example: CREATE TABLE #TempCustomers (id INT, name NVARCHAR(50))
        # Note: Also handled by _is_excluded(), but captured here for logging
        temp_pattern = r'#\w+'
        temps = re.findall(temp_pattern, ddl)
        non_persistent.update(temps)

        # 3. Table variables
        # Pattern: DECLARE @TableName TABLE (col1 INT, col2 VARCHAR(50))
        # Example: DECLARE @Results TABLE (CustomerID INT, OrderCount INT)
        table_var_pattern = r'\bDECLARE\s+@(\w+)\s+TABLE\b'
        table_vars = re.findall(table_var_pattern, ddl, re.IGNORECASE)
        non_persistent.update(table_vars)

        return non_persistent

    def _is_non_persistent(self, schema: str, table: str, non_persistent: Set[str]) -> bool:
        """
        Check if table is non-persistent (CTE, temp table, table variable).

        Args:
            schema: Schema name (may be empty for temp tables)
            table: Table name
            non_persistent: Set of known non-persistent object names

        Returns:
            True if object should be filtered out
        """
        # Check if table name matches non-persistent objects (case-insensitive)
        if table.lower() in {name.lower() for name in non_persistent}:
            return True

        # Also check if starts with # or @ (redundant with _is_excluded, but defensive)
        if table.startswith('#') or table.startswith('@'):
            return True

        return False

    def _preprocess_ddl(self, ddl: str) -> str:
        """
        Preprocess DDL to improve regex extraction accuracy.

        **Goal:** Extract only the core business logic (data movement statements)
        and remove T-SQL specific syntax that complicates pattern matching.

        **Strategy (v4.3.5 - YAML Regex Extraction):**
        1. Apply SQL Cleaning Engine rules (if enabled) for better regex matching
           - Removes GO, DECLARE, SET, TRY/CATCH, RAISERROR, EXEC, transactions
           - Extracts core DML from CREATE PROC wrapper
           - 10 declarative rules with priority-based execution
        2. **Fallback**: Legacy regex-based preprocessing (if cleaning disabled)

        **Original Strategy (2025-11-03):**
        1. Normalize statement boundaries with semicolons (for clarity)
        2. Fix DECLARE pattern to avoid greedy matching
        3. Focus on TRY block (business logic), remove CATCH/EXEC/post-COMMIT noise

        **Performance Optimization (v4.3.2):**
        - Simplify SELECT clauses to SELECT * (object-level lineage only)
        - Reduces parsing complexity without affecting table extraction

        Args:
            ddl: Raw DDL from sys.sql_modules.definition

        Returns:
            Cleaned DDL ready for parser consumption
        """
        # Step 0: Apply SQL Cleaning Engine with YAML rules (if enabled and available)
        # This is a more sophisticated rule-based approach that improves regex extraction accuracy
        # (Baseline 53.6% → Improved 80.8% based on 349 production SPs)
        if self.enable_sql_cleaning and self.cleaning_engine is not None:
            try:
                cleaned = self.cleaning_engine.apply_all(ddl, verbose=False)
                logger.debug(f"SQL Cleaning Engine applied: {len(ddl)} → {len(cleaned)} bytes")
                # Apply SELECT simplification before returning
                cleaned = self._simplify_select_clauses(cleaned)
                return cleaned.strip()
            except Exception as e:
                logger.warning(f"SQL Cleaning Engine failed, falling back to legacy preprocessing: {e}")
                # Fall through to legacy preprocessing

        # Legacy preprocessing (used if cleaning engine disabled or fails)
        cleaned = ddl

        # Step 1: Remove ANSI escape codes (e.g., \x1b[32m for green text)
        # These appear in some DDL exports and break regex matching
        cleaned = re.sub(r'\x1b\[[0-9;]+m', '', cleaned)
        cleaned = re.sub(r'\[4m|\[0m', '', cleaned)

        # Step 2: Remove CREATE PROC header (including parameter list)
        # Pattern: CREATE PROC[EDURE] [schema].[name] @param1 type, @param2 type, ... AS BEGIN
        # We only want the body (everything after AS BEGIN)
        match = re.search(r'CREATE\s+PROC(?:EDURE)?\s+\[[^\]]+\]\.\[[^\]]+\].*?AS\s+BEGIN',
                         cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[match.end():]  # Keep only body
            cleaned = re.sub(r'\s*END\s*$', '', cleaned, flags=re.IGNORECASE)  # Remove trailing END

        # Step 3: Normalize statement boundaries with semicolons
        # Add semicolons to separate statements for clarity (T-SQL doesn't require them)
        # Strategy: Add semicolon before INDEPENDENT statement keywords only
        # IMPORTANT: Don't add semicolons before SELECT/WITH when they're part of other statements

        # Keywords that are always independent statements (safe to add semicolon)
        independent_keywords = ['DECLARE', 'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'TRUNCATE']
        for keyword in independent_keywords:
            # Add semicolon before keyword if not already present
            cleaned = re.sub(
                rf'(?<!;)\s+\b({keyword})\b',
                rf';\1',
                cleaned,
                flags=re.IGNORECASE
            )

        # Special handling for SELECT: Only add semicolon if it's a standalone SELECT
        # Don't add if preceded by INSERT/UPDATE/MERGE (they use SELECT as subquery)
        # Pattern: Match SELECT that is NOT preceded by INSERT/UPDATE/MERGE on same or previous line
        # This is complex, so we'll use a negative lookbehind with a reasonable window
        # Simplified approach: Only add ; before SELECT if preceded by END, ;, or start of string
        cleaned = re.sub(
            r'(^|;|END)\s+\b(SELECT)\b',
            r'\1;\2',
            cleaned,
            flags=re.IGNORECASE | re.MULTILINE
        )

        # Special handling for WITH (CTEs):
        # Only add semicolon before WITH if it starts a new statement
        # CTEs should NOT have semicolon: "WITH cte AS (SELECT..."
        # But standalone WITH should: "; WITH cte AS... SELECT FROM cte"
        # Similar logic: only add ; if preceded by END, ;, or start
        cleaned = re.sub(
            r'(^|;|END)\s+\b(WITH)\b',
            r'\1;\2',
            cleaned,
            flags=re.IGNORECASE | re.MULTILINE
        )

        # Step 4: Apply control flow removal
        # Convert T-SQL specific BEGIN TRY/CATCH to comments so parser can still see structure
        for pattern, replacement in self.CONTROL_FLOW_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.DOTALL)

        # Step 5: Remove everything after COMMIT TRANSACTION
        # Post-commit code is usually logging, cleanup, administrative tasks
        # Not relevant for data lineage
        commit_match = re.search(r'\bCOMMIT\s+TRANSACTION\b', cleaned, re.IGNORECASE)
        if commit_match:
            cleaned = cleaned[:commit_match.end()]
            logger.debug("Removed post-COMMIT code (logging/cleanup)")

        # Step 6: Apply enhanced removal patterns
        # Remove CATCH blocks, EXEC calls, variable declarations
        for pattern, replacement, flags in self.ENHANCED_REMOVAL_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=flags)

        logger.debug(f"Preprocessing complete: {len(ddl)} → {len(cleaned)} chars ({100 * (len(ddl) - len(cleaned)) / len(ddl):.1f}% reduction)")

        # Step 7: Normalize whitespace for cleaner parsing
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # Remove blank lines
        cleaned = re.sub(r'\s+', ' ', cleaned)        # Collapse multiple spaces

        # Step 8: Simplify SELECT clauses (v4.3.2 - performance optimization)
        cleaned = self._simplify_select_clauses(cleaned)

        return cleaned.strip()

    def _simplify_select_clauses(self, sql: str) -> str:
        """
        Simplify SELECT clauses to SELECT * for performance.

        Since we only need object-level lineage (tables), not column-level lineage,
        we can replace complex SELECT clauses with SELECT *. This:
        - Reduces parsing complexity
        - Improves performance (especially with CASE/CAST/functions)
        - Doesn't affect table extraction (we only parse FROM/JOIN/INSERT/UPDATE)

        Examples:
        - SELECT col1, col2, CASE ... END FROM table → SELECT * FROM table
        - SELECT TOP 100 a.*, b.col FROM t1 a → SELECT * FROM t1 a
        - INSERT INTO t1 SELECT col1, col2 FROM t2 → INSERT INTO t1 SELECT * FROM t2

        Version: 4.3.2
        """
        # Pattern: SELECT ... FROM
        # Replace everything between SELECT and FROM with *
        # Use negative lookahead to handle nested SELECTs correctly
        # Pattern matches: SELECT (anything) FROM, but stops at nested SELECTs

        # Strategy: Replace SELECT clause content with * while preserving:
        # - TOP clause (for regex extraction)
        # - DISTINCT (for regex extraction)
        # But simplify column list to just *

        # Pattern explanation:
        # - \bSELECT\s+ - Match SELECT keyword
        # - (TOP\s+\d+\s+|DISTINCT\s+)? - Optional TOP or DISTINCT
        # - .*? - Non-greedy match of column list
        # - (?=\s+FROM\b) - Lookahead for FROM keyword

        simplified = re.sub(
            r'\bSELECT\s+(TOP\s+\d+\s+|DISTINCT\s+)?.*?(?=\s+FROM\b)',
            r'SELECT \g<1>*',
            sql,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Log if significant simplification occurred
        reduction = len(sql) - len(simplified)
        if reduction > 100:
            logger.debug(f"SELECT simplification: {len(sql)} → {len(simplified)} bytes ({reduction} bytes removed)")

        return simplified

    def _split_statements(self, sql: str) -> List[str]:
        """Split SQL into statements on GO/semicolon."""
        statements = []

        # Split on GO
        batches = re.split(r'\bGO\b', sql, flags=re.IGNORECASE)

        for batch in batches:
            batch = batch.strip()
            if not batch:
                continue

            # Split on semicolons
            parts = re.split(r';\s*(?=\S)', batch)

            for part in parts:
                part = part.strip()
                if part and not part.startswith('--'):
                    statements.append(part)

        return statements

        # All table extraction now uses regex-based methods only.
        sources = set()
        targets = set()
        select_into_targets = set()  # Track SELECT INTO temp tables separately

        # STEP 1a: Extract SELECT INTO targets (temp tables only)
        # Pattern: SELECT ... INTO #temp FROM ...
        for select in parsed.find_all(exp.Select):
            if select.args.get('into'):
                # This is a SELECT INTO statement
                into_node = select.args['into']

                # Handle different node types for INTO clause
                # SELECT INTO is a T-SQL extension
                if isinstance(into_node, exp.Into):
                    # Extract table from Into.this
                    into_table = into_node.this
                    if isinstance(into_table, exp.Table):
                        name = self._get_table_name(into_table)
                    else:
                        name = None
                elif isinstance(into_node, exp.Table):
                    name = self._get_table_name(into_node)
                elif isinstance(into_node, exp.Schema):
                    # Schema wraps table (bracketed identifiers)
                    if into_node.this and isinstance(into_node.this, exp.Table):
                        name = self._get_table_name(into_node.this)
                    else:
                        name = None
                else:
                    name = None

                # Track ALL SELECT INTO targets separately
                # Key insight: SELECT INTO #temp FROM source_table
                # - #temp is a target (will be filtered by _is_excluded later)
                # - source_table is a source (should NOT be excluded)
                if name:
                    select_into_targets.add(name)
                    # Also add to targets (temp tables will be filtered by _is_excluded later)
                    targets.add(name)

        # STEP 1b: Extract DML targets (INSERT, UPDATE, MERGE, DELETE)
        for insert in parsed.find_all(exp.Insert):
            name = self._extract_dml_target(insert.this)
            if name:
                targets.add(name)

        for update in parsed.find_all(exp.Update):
            name = self._extract_dml_target(update.this)
            if name:
                targets.add(name)

        for merge in parsed.find_all(exp.Merge):
            name = self._extract_dml_target(merge.this)
            if name:
                targets.add(name)

        for delete in parsed.find_all(exp.Delete):
            name = self._extract_dml_target(delete.this)
            if name:
                targets.add(name)

        # STEP 1c: TRUNCATE extraction DISABLED in v4.1.0 (DATAFLOW MODE)
        # TRUNCATE is DDL (housekeeping), not DML (data transformation)
        # In dataflow mode, we only show INSERT/UPDATE/DELETE/MERGE operations
        # Rationale: TRUNCATE clears data but doesn't transform it
        # Previous behavior (v3.5.0-v4.0.x): TRUNCATE was captured as output
        # New behavior (v4.1.0+): TRUNCATE is filtered out to reduce noise
        #
        # for truncate in parsed.find_all(exp.TruncateTable):
        #     if truncate.this:
        #         name = self._extract_dml_target(truncate.this)
        #         if name:
        #             targets.add(name)

        # STEP 2: Extract sources (FROM, JOIN) - FIXED v4.1.2 (2025-11-04)
        # Issue: find_all(exp.Table) was extracting ALL tables including DML targets
        # Root cause: INSERT INTO target was being added to sources (false positive)
        #
        # T-SQL statement structure:
        #   INSERT.this = target table
        #   INSERT.expression = SELECT statement with sources
        #
        # Solution: Exclude DML targets from source extraction (per-statement)
        # Note: Target exclusion happens globally after regex extraction
        # are accumulated. This per-statement exclusion is a defensive measure.

        for table in parsed.find_all(exp.Table):
            name = self._get_table_name(table)
            if name:
                # Skip temp tables from SELECT INTO (internal dependencies)
                if name in select_into_targets:
                    continue

                # v4.1.2 FIX: Skip DML targets (they're outputs, not inputs)
                # This prevents INSERT INTO target from appearing in sources
                if name in targets:
                    continue

                sources.add(name)

        return sources, targets

    # SQLGlot AST logic removed; regex-only parsing in use

    def _get_object_catalog(self) -> Set[str]:
        """Get set of valid table names from workspace."""
        if self._object_catalog is None:
            query = """
                SELECT schema_name || '.' || object_name
                FROM objects
                WHERE object_type IN ('Table', 'View')
            """
            results = self.workspace.query(query)
            self._object_catalog = {row[0] for row in results}

        return self._object_catalog

    def _get_catalog_objects(self) -> Set[str]:
        """Alias for _get_object_catalog() - returns catalog objects for validation."""
        return self._get_object_catalog()

    def _validate_against_catalog(self, table_names: Set[str]) -> Set[str]:
        """
        Only return tables that exist in database.

        Filters out:
        - dummy.* tables (temp table placeholders from SQL Cleaning Engine)
        - Tables not in catalog
        """
        catalog = self._get_object_catalog()
        validated = set()

        for name in table_names:
            # Filter out dummy.* temp table placeholders (introduced by SQL Cleaning Engine)
            if name.lower().startswith('dummy.'):
                continue

            if name in catalog:
                validated.add(name)
            else:
                # Try case-insensitive match
                name_lower = name.lower()
                for catalog_name in catalog:
                    if catalog_name.lower() == name_lower:
                        validated.add(catalog_name)
                        break

        return validated



    def _fetch_ddl(self, object_id: int) -> Optional[str]:
        """Fetch DDL from workspace."""
        validated_id = validate_object_id(object_id)

        query = """
        SELECT definition
        FROM definitions
        WHERE object_id = ?
        """

        results = self.workspace.query(query, params=[validated_id])
        return results[0][0] if results else None

    def _resolve_table_names(self, table_names: Set[str]) -> List[int]:
        """Resolve table names to object_ids."""
        if not table_names:
            return []

        object_ids = []

        for name in table_names:
            parts = name.split('.')
            if len(parts) != 2:
                continue

            schema, obj_name = parts

            try:
                schema = sanitize_identifier(schema)
                obj_name = sanitize_identifier(obj_name)
            except ValueError:
                continue

            query = """
            SELECT object_id
            FROM objects
            WHERE LOWER(schema_name) = LOWER(?)
              AND LOWER(object_name) = LOWER(?)
            """

            results = self.workspace.query(query, params=[schema, obj_name])
            if results:
                object_ids.append(results[0][0])

        return object_ids

    def _validate_sp_calls(self, sp_names: Set[str]) -> Set[str]:
        """
        Validate SP calls against object catalog.
        Only keep SPs that exist in the objects table.

        v4.0.1: Added for SP-to-SP lineage
        """
        if not sp_names:
            return set()

        # Get all stored procedures from catalog
        query = """
        SELECT LOWER(schema_name || '.' || object_name)
        FROM objects
        WHERE object_type = 'Stored Procedure'
        """
        results = self.workspace.query(query)
        sp_catalog = {row[0] for row in results}

        validated = set()
        for name in sp_names:
            name_lower = name.lower()
            if name_lower in sp_catalog:
                validated.add(name)

        return validated

    def _resolve_sp_names(self, sp_names: Set[str]) -> List[int]:
        """
        Resolve stored procedure names to object_ids.

        v4.0.1: Added for SP-to-SP lineage
        """
        if not sp_names:
            return []

        object_ids = []

        for name in sp_names:
            parts = name.split('.')
            if len(parts) != 2:
                continue

            schema, sp_name = parts

            try:
                schema = sanitize_identifier(schema)
                sp_name = sanitize_identifier(sp_name)
            except ValueError:
                continue

            query = """
            SELECT object_id
            FROM objects
            WHERE LOWER(schema_name) = LOWER(?)
              AND LOWER(object_name) = LOWER(?)
              AND object_type = 'Stored Procedure'
            """

            results = self.workspace.query(query, params=[schema, sp_name])
            if results:
                object_ids.append(results[0][0])

        return object_ids

    def _validate_function_calls(self, function_names: Set[str]) -> Set[str]:
        """
        Validate function calls against object catalog.
        Only keep functions that exist in the objects table.

        v4.3.0: Added for UDF detection
        """
        if not function_names:
            return set()

        # Get all functions from catalog (scalar and table-valued)
        query = """
        SELECT LOWER(schema_name || '.' || object_name)
        FROM objects
        WHERE object_type IN ('Function', 'Scalar Function', 'Table-valued Function')
        """
        results = self.workspace.query(query)
        func_catalog = {row[0] for row in results}

        validated = set()
        for name in function_names:
            name_lower = name.lower()
            if name_lower in func_catalog:
                validated.add(name)

        return validated

    def _resolve_function_names(self, function_names: Set[str]) -> List[int]:
        """
        Resolve function names to object_ids.

        v4.3.0: Added for UDF detection
        """
        if not function_names:
            return []

        object_ids = []

        for name in function_names:
            parts = name.split('.')
            if len(parts) != 2:
                continue

            schema, func_name = parts

            try:
                schema = sanitize_identifier(schema)
                func_name = sanitize_identifier(func_name)
            except ValueError:
                continue

            query = """
            SELECT object_id
            FROM objects
            WHERE LOWER(schema_name) = LOWER(?)
              AND LOWER(object_name) = LOWER(?)
              AND object_type IN ('Function', 'Scalar Function', 'Table-valued Function')
            """

            results = self.workspace.query(query, params=[schema, func_name])
            if results:
                object_ids.append(results[0][0])

        return object_ids

    def _detect_parse_failure_reason(self, ddl: str, parse_error: Optional[str] = None, expected_count: int = 0, found_count: int = 0) -> str:
        """
        Detect WHY parsing failed and provide actionable feedback for users.

        This method analyzes the DDL to identify specific T-SQL patterns that
        prevent successful parsing and provides clear guidance on how to resolve them.

        Args:
            ddl: The stored procedure DDL text
            parse_error: Optional parse error message
            expected_count: Expected number of tables from smoke test (DDL text analysis)
            found_count: Actual number of tables extracted by parser

        Returns:
            Human-readable string explaining failure reason and recommended action

        Example output:
            "Dynamic SQL: sp_executesql @variable - table names unknown at parse time |
             Expected 8 tables, found 1 (7 missing) → Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints"

        Version: 4.2.0 (2025-11-07)
        """
        reasons = []

        # Pattern 1: Dynamic SQL with EXEC(@variable)
        if re.search(r'EXEC\s*\(\s*@\w+\s*\)', ddl, re.IGNORECASE):
            reasons.append("Dynamic SQL: EXEC(@variable) - table names unknown at parse time")

        # Pattern 2: Dynamic SQL with sp_executesql
        if re.search(r'sp_executesql\s+@\w+', ddl, re.IGNORECASE):
            reasons.append("Dynamic SQL: sp_executesql @variable - table names unknown at parse time")

        # Pattern 3: String concatenation for dynamic SQL
        if re.search(r'DECLARE\s+@\w+.*?NVARCHAR.*?(?:INSERT|SELECT|UPDATE|DELETE|FROM)', ddl, re.IGNORECASE | re.DOTALL):
            if not reasons:  # Only add if not already detected via EXEC
                reasons.append("Dynamic SQL: String concatenation detected")

        # Pattern 4: Deep nesting (5+ BEGIN/END blocks)
        begin_count = len(re.findall(r'\bBEGIN\b', ddl, re.IGNORECASE))
        if begin_count >= 5:
            reasons.append(f"Deep nesting: {begin_count} BEGIN/END blocks (limit: 4)")

        # Pattern 5: WHILE loops
        if re.search(r'\bWHILE\b', ddl, re.IGNORECASE):
            reasons.append("WHILE loop: Iterative logic not supported by parser")

        # Pattern 6: CURSOR usage
        if re.search(r'\bCURSOR\b', ddl, re.IGNORECASE):
            reasons.append("CURSOR: Row-by-row processing not supported by parser")

        # Pattern 7: Complex CASE WHEN (10+ occurrences)
        case_count = len(re.findall(r'\bCASE\b', ddl, re.IGNORECASE))
        if case_count >= 10:
            reasons.append(f"Complex CASE logic: {case_count} CASE statements (limit: 9)")

        # Pattern 8: Multiple CTEs (10+ WITH clauses)
        cte_count = len(re.findall(r'\bWITH\s+\w+\s+AS\s*\(', ddl, re.IGNORECASE))
        if cte_count >= 10:
            reasons.append(f"Multiple CTEs: {cte_count} WITH clauses (limit: 9)")

        # Fallback: Use parse error if available
        if not reasons and parse_error:
            reasons.append(f"Parse error: {parse_error[:100]}")

        # Generic fallback
        if not reasons:
            reasons.append("Complex T-SQL patterns")

        # Build description
        description_parts = []

        # Main reason
        description_parts.append(" | ".join(reasons))

        # Add expected vs found counts if available
        if expected_count > 0 and found_count >= 0:
            missing = expected_count - found_count
            if missing > 2:
                description_parts.append(f"Expected {expected_count} tables, found {found_count} ({missing} missing)")

        # Actionable solution
        description_parts.append("→ Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS comment hints to document dependencies")

        return " | ".join(description_parts)

    def _get_object_info(self, object_id: int) -> Optional[Dict[str, str]]:
        """
        Get object schema and name from workspace.

        Args:
            object_id: Object ID to lookup

        Returns:
            Dict with 'schema' and 'name' keys, or None if not found
        """
        try:
            query = """
                SELECT schema_name, object_name
                FROM objects
                WHERE object_id = ?
            """
            result = self.workspace.connection.execute(query, [object_id]).fetchone()

            if result:
                return {'schema': result[0], 'name': result[1]}
            return None

        except Exception as e:
            logger.error(f"Failed to get object info for {object_id}: {e}")
            return None

    def get_parse_statistics(self) -> Dict[str, Any]:
        """
        Get parser statistics.
        
        Note: Confidence scoring was removed in v4.3.6 due to circular logic.
        """
        query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN inputs IS NOT NULL OR outputs IS NOT NULL THEN 1 ELSE 0 END) as with_dependencies
        FROM lineage_metadata
        WHERE primary_source = 'parser'
        """

        results = self.workspace.query(query)
        if not results:
            return {}

        row = results[0]
        total = row[0]
        with_deps = row[1]

        return {
            'total_parsed': total,
            'with_dependencies': with_deps,
            'success_rate': (with_deps / total * 100) if total > 0 else 0
        }

    # ============================================================================
    # PUBLIC EVALUATION WRAPPERS (for sub_DL_OptimizeParsing subagent)
    # ============================================================================
    # These methods expose internal parsing logic for evaluation purposes.
    # They do NOT affect production parsing behavior.

    def extract_regex_dependencies(self, ddl: str) -> Dict[str, Any]:
        """
        Public wrapper for regex extraction (used by evaluation subagent).

        Runs regex pattern matching to extract table dependencies.
        This is the baseline method used for quality checking.

        Args:
            ddl: SQL DDL text

        Returns:
            {
                'sources': Set[str],           # Raw schema.table names found
                'targets': Set[str],           # Raw schema.table names found
                'sources_validated': Set[str], # After catalog validation
                'targets_validated': Set[str], # After catalog validation
                'sources_count': int,
                'targets_count': int
            }
        """
        # Use existing internal regex scan
        sources, targets, sp_calls, function_calls = self._regex_scan(ddl)

        # Validate against catalog (same as production)
        sources_validated = self._validate_against_catalog(sources)
        targets_validated = self._validate_against_catalog(targets)
        sp_calls_validated = self._validate_sp_calls(sp_calls)
        function_calls_validated = self._validate_function_calls(function_calls)  # v4.3.0

        return {
            'sources': sources,
            'targets': targets,
            'sp_calls': sp_calls,  # v4.0.1: Added SP-to-SP lineage
            'function_calls': function_calls,  # v4.3.0: Added function detection
            'sources_validated': sources_validated,
            'targets_validated': targets_validated,
            'sp_calls_validated': sp_calls_validated,  # v4.0.1
            'function_calls_validated': function_calls_validated,  # v4.3.0
            'sources_count': len(sources_validated),
            'targets_count': len(targets_validated),
            'sp_calls_count': len(sp_calls_validated),  # v4.0.1
            'function_calls_count': len(function_calls_validated)  # v4.3.0
        }


