r"""
SQL Lineage Parser - Pure YAML Regex Extraction
================================================

Strategy:
1. YAML regex rules scan full DDL → Extract dependencies
2. Validate against metadata catalog → Filter false positives
3. Return diagnostic counts (expected vs found)

All extraction patterns are maintained in YAML files that business users
can edit without Python knowledge.

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





class QualityAwareParser:
    """
    Parser with YAML regex extraction and catalog validation.

    Key innovation: Pure YAML regex extraction with metadata catalog validation.
    Business users can maintain extraction patterns without Python knowledge.
    
    Returns diagnostic counts (expected vs found) without confidence scoring,
    as comparing regex to itself is circular logic.
    """







    def __init__(self, workspace: DuckDBWorkspace):
        """
        Initialize parser with DuckDB workspace.

        Args:
            workspace: DuckDB workspace for catalog access
        """
        self.workspace = workspace
        self._object_catalog = None
        self.hints_parser = CommentHintsParser(workspace)

        # Load excluded schemas from settings
        from engine.config.settings import settings
        self.excluded_schemas = settings.excluded_schema_set

        # Load YAML rules for configured dialect (v4.3.5: extraction only)
        try:
            dialect = settings.dialect
            all_rules = load_rules(dialect, custom_dirs=None)

            if all_rules:
                # Filter for extraction and cleaning rules
                self.extraction_rules = [r for r in all_rules if r.rule_type == 'extraction']
                self.cleaning_rules = [r for r in all_rules if r.rule_type == 'cleaning']
                
                # Log rule stats
                logger.info(
                    f"SQL Parsing Engine loaded: "
                    f"{len(self.extraction_rules)} extraction rules, "
                    f"{len(self.cleaning_rules)} cleaning rules for {dialect.value}"
                )
            else:
                logger.warning(f"No YAML rules found for {dialect.value}")
                self.extraction_rules = []
                self.cleaning_rules = []

        except Exception as e:
            logger.error(f"Failed to load YAML rules: {e}")
            self.extraction_rules = []
            self.cleaning_rules = []

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

        # DEBUG DIAGNOSTIC: Dump DDL for the hint test SP
        if str(object_id) == '1607676775' or (ddl and 'usp_LineageTest_Hints' in ddl):
            logger.debug(f"DIAGNOSTIC DUMP for {object_id}:\n{ddl!r}")

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
            # Initialize obj_info to prevent UnboundLocalError
            obj_info = None

            # STEP 1: Regex baseline (expected counts)
            regex_sources, regex_targets, regex_sp_calls, regex_function_calls = self._regex_scan(ddl)
            regex_sources_valid = self._validate_against_catalog(regex_sources)
            regex_targets_valid = self._validate_against_catalog(regex_targets)
            regex_sp_calls_valid = self._validate_sp_calls(regex_sp_calls)
            regex_function_calls_valid = self._validate_function_calls(regex_function_calls)  # v4.3.0

            # STEP 2: Extract comment hints (v4.2.0)
            logger.debug(f"Parsing hints for object {object_id}")
            hint_inputs, hint_outputs = self.hints_parser.extract_hints(ddl, validate=True)
            logger.debug(f"Extracted hints for {object_id}: Inputs={hint_inputs}, Outputs={hint_outputs}")

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

            # Log summary for every object (requested by user)
            obj_name = f"{obj_info['schema']}.{obj_info['name']}" if obj_info else f"ID:{object_id}"
            logger.debug(f"Parsed {obj_name} ({object_id}): Success=True, Tables={found_tables}, Hints={has_hints}")

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

        # STEP 0: Preprocess DDL (Clean comments, normalize, etc.)
        # This applies YAML cleaning rules (like comment removal) to avoid false positives
        cleaned_ddl = self._preprocess_ddl(ddl)

        # STEP 1: Identify non-persistent objects to exclude (using CLEANED DDL)
        non_persistent = self._identify_non_persistent_objects(cleaned_ddl)
        logger.debug(f"Found {len(non_persistent)} non-persistent objects: {non_persistent}")

        # STEP 2: Apply extraction rules from YAML
        for rule in self.extraction_rules:
            if not rule.enabled:
                continue

            # Extract objects using rule (from CLEANED DDL)
            extracted = rule.extract(cleaned_ddl, verbose=False)

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

        **Goal:** Extract only the core business logic (data movement statements)
        and remove T-SQL specific syntax that complicates pattern matching.

        **Strategy:**
        1. Apply SQL Cleaning Engine rules (if enabled)
        2. Clean ANSI escape codes
        3. Remove CREATE PROC headers
        4. Normalize statement boundaries
        5. Simplify SELECT clauses

        Args:
            ddl: Raw DDL from sys.sql_modules.definition

        Returns:
        Cleaned DDL ready for parser consumption
    """
        # Legacy preprocessing (always used now)
        cleaned = ddl

        # Step 0: Apply YAML cleaning rules (High Priority)
        # This enables declarative cleaning (e.g. comment removal)
        if hasattr(self, 'cleaning_rules') and self.cleaning_rules:
            for rule in self.cleaning_rules:
                if rule.enabled:
                    cleaned = rule.apply(cleaned, verbose=False)

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

        # Step 4: [REMOVED] Control flow removal (Moved to YAML rules)

        # Step 5: Remove everything after COMMIT TRANSACTION
        # Post-commit code is usually logging, cleanup, administrative tasks
        # Not relevant for data lineage
        commit_match = re.search(r'\bCOMMIT\s+TRANSACTION\b', cleaned, re.IGNORECASE)
        if commit_match:
            cleaned = cleaned[:commit_match.end()]
            logger.debug("Removed post-COMMIT code (logging/cleanup)")

        # Step 6: [REMOVED] Enhanced removal patterns (Moved to YAML rules)

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
        # - (?:(?!\bSELECT\b).)* - Match any char EXCEPT another SELECT keyword (prevents cross-statement matching)
        # - (?=\s+FROM\b) - Lookahead for FROM keyword
        #
        # v4.3.3 Bug fix: Added negative lookahead for SELECT keyword to prevent matching
        # from one SELECT across INSERT INTO statements to another SELECT's FROM clause.
        # Example bug: "DECLARE @x = (SELECT id FROM t1) ... INSERT INTO t2 SELECT col FROM t3"
        # would match from first SELECT to last FROM, destroying the INSERT INTO.

        simplified = re.sub(
            r'\bSELECT\s+(TOP\s+\d+\s+|DISTINCT\s+)?(?:(?!\bSELECT\b).)*?(?=\s+FROM\b)',
            r'SELECT \g<1>*',
            sql,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Log if significant simplification occurred
        reduction = len(sql) - len(simplified)
        if reduction > 100:
            logger.debug(f"SELECT simplification: {len(sql)} → {len(simplified)} bytes ({reduction} bytes removed)")

        return simplified





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




