"""
Quality-Aware SQLGlot Parser - Smart extraction with built-in QA
=================================================================

Strategy:
1. Regex scan full DDL → Get expected entity count (baseline)
2. Preprocess & split DDL → Parse with SQLGlot
3. Compare counts:
   - Match (±10%) → High confidence (0.85)
   - Partial match (±25%) → Medium confidence (0.75)
   - Major difference (>25%) → Flag for AI (0.5)

This gives us quality assurance built into the parser!

Author: Vibecoding
Version: 3.2.0
Date: 2025-10-26
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import sqlglot
from sqlglot import exp, parse_one
import logging
import re

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from lineage_v3.utils.validators import validate_object_id, sanitize_identifier


# Configure logging
logger = logging.getLogger(__name__)


class QualityAwareParser:
    """
    Parser with built-in quality assurance via regex baseline comparison.

    Key innovation: Use regex count as quality check, not just fallback.
    If SQLGlot results differ significantly from regex baseline, reduce
    confidence and flag for AI review.
    """

    # Confidence scores
    CONFIDENCE_HIGH = 0.85    # Regex and SQLGlot agree (±10%)
    CONFIDENCE_MEDIUM = 0.75  # Partial agreement (±25%)
    CONFIDENCE_LOW = 0.5      # Major difference (>25%) - needs AI review

    # Quality check thresholds
    THRESHOLD_GOOD = 0.10     # ±10% difference
    THRESHOLD_FAIR = 0.25     # ±25% difference

    # System schemas to exclude
    EXCLUDED_SCHEMAS = {'sys', 'INFORMATION_SCHEMA', 'tempdb'}

    # T-SQL control flow patterns to remove
    CONTROL_FLOW_PATTERNS = [
        # IF statements with temp table drops
        (r'\bIF\s+OBJECT_ID\s*\([^)]+\)\s+IS\s+NOT\s+NULL\s+BEGIN\s+DROP\s+TABLE\s+[^;]+;\s*END',
         '-- IF removed'),
        (r'\bIF\s+OBJECT_ID\s*\([^)]+\)\s+IS\s+NOT\s+NULL\s+DROP\s+TABLE\s+[^;]+;?',
         '-- IF removed'),

        # BEGIN/END blocks
        (r'\bBEGIN\s+TRY\b', 'BEGIN /* TRY */'),
        (r'\bEND\s+TRY\b', 'END /* TRY */'),
        (r'\bBEGIN\s+CATCH\b', 'BEGIN /* CATCH */'),
        (r'\bEND\s+CATCH\b', 'END /* CATCH */'),

        # RAISERROR and PRINT
        (r'\bRAISERROR\s*\([^)]+\)', '-- RAISERROR removed'),
        (r'\bPRINT\s+[^\n;]+', '-- PRINT removed'),
    ]

    # Enhanced preprocessing patterns (2025-10-26)
    # Based on user feedback: focus on TRY block, remove CATCH, EXEC, post-COMMIT
    ENHANCED_REMOVAL_PATTERNS = [
        # Remove entire CATCH blocks (including nested content)
        (r'BEGIN\s+/\*\s*CATCH\s*\*/.*?END\s+/\*\s*CATCH\s*\*/', '-- CATCH block removed', re.DOTALL),

        # Remove EXEC commands (stored procedure calls)
        (r'\bEXEC\s+\[?[^\]]+\]?\.\[?[^\]]+\]?[^;]*;?', '-- EXEC removed', 0),

        # Remove DECLARE statements (variable declarations clutter parsing)
        (r'\bDECLARE\s+@\w+\s+[^;]+;', '-- DECLARE removed', 0),

        # Remove SET statements (variable assignments)
        (r'\bSET\s+@\w+\s*=\s*[^;]+;', '-- SET removed', 0),
    ]

    def __init__(self, workspace: DuckDBWorkspace):
        """Initialize parser with DuckDB workspace."""
        self.workspace = workspace
        self._object_catalog = None

    def parse_object(self, object_id: int) -> Dict[str, Any]:
        """
        Parse DDL with built-in quality check.

        Returns:
            {
                'object_id': int,
                'inputs': List[int],
                'outputs': List[int],
                'confidence': float,  # Adjusted based on quality check
                'source': 'parser',
                'parse_error': Optional[str],
                'quality_check': {
                    'regex_sources': int,
                    'regex_targets': int,
                    'parser_sources': int,
                    'parser_targets': int,
                    'source_match': float,  # 0.0-1.0
                    'target_match': float,  # 0.0-1.0
                    'overall_match': float,  # 0.0-1.0
                    'needs_ai': bool
                }
            }
        """
        # Fetch DDL
        ddl = self._fetch_ddl(object_id)
        if not ddl:
            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'confidence': 0.0,
                'source': 'parser',
                'parse_error': 'No DDL definition found'
            }

        try:
            # STEP 1: Regex baseline (expected counts)
            regex_sources, regex_targets = self._regex_scan(ddl)
            regex_sources_valid = self._validate_against_catalog(regex_sources)
            regex_targets_valid = self._validate_against_catalog(regex_targets)

            # STEP 2: Preprocess and parse with SQLGlot
            cleaned_ddl = self._preprocess_ddl(ddl)
            parser_sources, parser_targets = self._sqlglot_parse(cleaned_ddl, ddl)
            parser_sources_valid = self._validate_against_catalog(parser_sources)
            parser_targets_valid = self._validate_against_catalog(parser_targets)

            # STEP 3: Compare counts and calculate quality metrics
            quality = self._calculate_quality(
                len(regex_sources_valid),
                len(regex_targets_valid),
                len(parser_sources_valid),
                len(parser_targets_valid)
            )

            # STEP 4: Adjust confidence based on quality
            confidence = self._determine_confidence(quality)

            # STEP 5: Resolve to object_ids
            input_ids = self._resolve_table_names(parser_sources_valid)
            output_ids = self._resolve_table_names(parser_targets_valid)

            return {
                'object_id': object_id,
                'inputs': input_ids,
                'outputs': output_ids,
                'confidence': confidence,
                'source': 'parser',
                'parse_error': None,
                'quality_check': {
                    'regex_sources': len(regex_sources_valid),
                    'regex_targets': len(regex_targets_valid),
                    'parser_sources': len(parser_sources_valid),
                    'parser_targets': len(parser_targets_valid),
                    'source_match': quality['source_match'],
                    'target_match': quality['target_match'],
                    'overall_match': quality['overall_match'],
                    'needs_ai': quality['needs_ai']
                }
            }

        except Exception as e:
            logger.error(f"Failed to parse object_id {object_id}: {e}")
            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'confidence': 0.0,
                'source': 'parser',
                'parse_error': str(e)
            }

    def _regex_scan(self, ddl: str) -> Tuple[Set[str], Set[str]]:
        """
        Scan full DDL with regex to get expected entity counts.

        This is the BASELINE - what we expect to find.

        Enhanced filtering (2025-10-26):
        - Excludes CTEs (WITH ... AS)
        - Excludes temp tables (#table)
        - Excludes table variables (@table TABLE)
        """
        sources = set()
        targets = set()

        # Remove comments
        ddl = re.sub(r'--[^\n]*', '', ddl)
        ddl = re.sub(r'/\*.*?\*/', '', ddl, flags=re.DOTALL)

        # STEP 1: Identify non-persistent objects to exclude
        non_persistent = self._identify_non_persistent_objects(ddl)
        logger.debug(f"Found {len(non_persistent)} non-persistent objects: {non_persistent}")

        # SOURCE patterns (FROM, JOIN)
        source_patterns = [
            r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bJOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bINNER\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bLEFT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bRIGHT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bFULL\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
        ]

        for pattern in source_patterns:
            matches = re.findall(pattern, ddl, re.IGNORECASE)
            for schema, table in matches:
                # Existing exclusions (system schemas)
                if self._is_excluded(schema, table):
                    continue

                # NEW: Filter non-persistent objects
                if self._is_non_persistent(schema, table, non_persistent):
                    continue

                sources.add(f"{schema}.{table}")

        # TARGET patterns (INSERT, UPDATE, MERGE, TRUNCATE, DELETE)
        target_patterns = [
            r'\bINSERT\s+(?:INTO\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bUPDATE\s+\[?(\w+)\]?\.\[?(\w+)\]?\s+SET',
            r'\bMERGE\s+(?:INTO\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bTRUNCATE\s+TABLE\s+\[?(\w+)\]?\.\[?(\w+)\]?',
        ]

        for pattern in target_patterns:
            matches = re.findall(pattern, ddl, re.IGNORECASE)
            for schema, table in matches:
                # Existing exclusions
                if self._is_excluded(schema, table):
                    continue

                # NEW: Filter non-persistent objects
                if self._is_non_persistent(schema, table, non_persistent):
                    continue

                targets.add(f"{schema}.{table}")

        logger.debug(f"Regex baseline: {len(sources)} sources, {len(targets)} targets (after filtering)")
        return sources, targets

    def _sqlglot_parse(self, cleaned_ddl: str, original_ddl: str) -> Tuple[Set[str], Set[str]]:
        """
        Parse with SQLGlot after preprocessing.
        """
        sources = set()
        targets = set()

        # Split into statements
        statements = self._split_statements(cleaned_ddl)

        # Try parsing each statement
        for stmt in statements:
            try:
                parsed = parse_one(stmt, dialect='tsql', error_level=None)
                if parsed:
                    stmt_sources, stmt_targets = self._extract_from_ast(parsed)
                    sources.update(stmt_sources)
                    targets.update(stmt_targets)
            except Exception:
                # SQLGlot failed, try regex fallback on this statement
                regex_s, regex_t = self._regex_scan(stmt)
                sources.update(regex_s)
                targets.update(regex_t)

        # If SQLGlot got nothing, fallback to regex on original DDL
        if not sources and not targets:
            sources, targets = self._regex_scan(original_ddl)

        return sources, targets

    def _calculate_quality(
        self,
        regex_sources: int,
        regex_targets: int,
        parser_sources: int,
        parser_targets: int
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics by comparing regex baseline to parser results.

        Returns:
            {
                'source_match': float (0.0-1.0),
                'target_match': float (0.0-1.0),
                'overall_match': float (0.0-1.0),
                'needs_ai': bool
            }
        """
        # Calculate match percentages
        if regex_sources > 0:
            source_match = min(parser_sources / regex_sources, 1.0)
        else:
            source_match = 1.0 if parser_sources == 0 else 0.0

        if regex_targets > 0:
            target_match = min(parser_targets / regex_targets, 1.0)
        else:
            target_match = 1.0 if parser_targets == 0 else 0.0

        # Overall match (weighted average - targets more important)
        overall_match = (source_match * 0.4) + (target_match * 0.6)

        # Flag for AI if either is significantly off
        source_diff = abs(regex_sources - parser_sources) / max(regex_sources, 1)
        target_diff = abs(regex_targets - parser_targets) / max(regex_targets, 1)

        needs_ai = (source_diff > self.THRESHOLD_FAIR or
                   target_diff > self.THRESHOLD_FAIR)

        return {
            'source_match': source_match,
            'target_match': target_match,
            'overall_match': overall_match,
            'needs_ai': needs_ai
        }

    def _determine_confidence(self, quality: Dict[str, Any]) -> float:
        """
        Determine confidence score based on quality check.

        Rules:
        - Overall match ≥90% → 0.85 (high confidence)
        - Overall match ≥75% → 0.75 (medium confidence)
        - Overall match <75% → 0.5 (low confidence, needs AI)
        """
        match = quality['overall_match']

        if match >= 0.90:
            return self.CONFIDENCE_HIGH
        elif match >= 0.75:
            return self.CONFIDENCE_MEDIUM
        else:
            return self.CONFIDENCE_LOW

    def _is_excluded(self, schema: str, table: str) -> bool:
        """Check if table should be excluded (temp tables, system schemas)."""
        if schema.lower() in self.EXCLUDED_SCHEMAS:
            return True
        if table.startswith('#') or table.startswith('@'):
            return True
        return False

    def _identify_non_persistent_objects(self, ddl: str) -> Set[str]:
        """
        Identify non-persistent objects that should be excluded from baseline.

        Returns:
            Set of table names (without schema) that are non-persistent:
            - CTEs (WITH ... AS)
            - Temp tables (#table)
            - Table variables (@table TABLE)
        """
        non_persistent = set()

        # 1. CTEs (Common Table Expressions)
        # Pattern: WITH cte_name AS (...)
        cte_pattern = r'\bWITH\s+(\w+)\s+AS\s*\('
        ctes = re.findall(cte_pattern, ddl, re.IGNORECASE)
        non_persistent.update(ctes)

        # Also handle: WITH cte1 AS (...), cte2 AS (...)
        multi_cte_pattern = r',\s*(\w+)\s+AS\s*\('
        multi_ctes = re.findall(multi_cte_pattern, ddl, re.IGNORECASE)
        non_persistent.update(multi_ctes)

        # 2. Temp tables already handled by _is_excluded (starts with #)
        # But capture them here for logging purposes
        temp_pattern = r'#\w+'
        temps = re.findall(temp_pattern, ddl)
        non_persistent.update(temps)

        # 3. Table variables
        # Pattern: DECLARE @table_name TABLE
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
        Preprocess DDL to make it parseable.

        Enhanced (2025-10-26): Focus on TRY block only, remove CATCH/EXEC/post-COMMIT.
        """
        cleaned = ddl

        # Remove ANSI escape codes
        cleaned = re.sub(r'\x1b\[[0-9;]+m', '', cleaned)
        cleaned = re.sub(r'\[4m|\[0m', '', cleaned)

        # Remove CREATE PROC header (including parameter list)
        # Pattern: CREATE PROC [schema].[name] @param1 type, @param2 type, ... AS BEGIN
        match = re.search(r'CREATE\s+PROC(?:EDURE)?\s+\[[^\]]+\]\.\[[^\]]+\].*?AS\s+BEGIN',
                         cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[match.end():]
            cleaned = re.sub(r'\s*END\s*$', '', cleaned, flags=re.IGNORECASE)

        # Apply control flow removal (convert BEGIN TRY/CATCH to comments)
        for pattern, replacement in self.CONTROL_FLOW_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.DOTALL)

        # ENHANCED: Remove everything after COMMIT TRANSACTION (logging, error handling)
        # Keep only the core business logic
        commit_match = re.search(r'\bCOMMIT\s+TRANSACTION\b', cleaned, re.IGNORECASE)
        if commit_match:
            cleaned = cleaned[:commit_match.end()]
            logger.debug("Removed post-COMMIT code (logging/cleanup)")

        # ENHANCED: Apply enhanced removal patterns
        for pattern, replacement, flags in self.ENHANCED_REMOVAL_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=flags)

        logger.debug(f"Preprocessing complete: {len(ddl)} → {len(cleaned)} chars")

        # Normalize whitespace
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned.strip()

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

    def _extract_from_ast(self, parsed: exp.Expression) -> Tuple[Set[str], Set[str]]:
        """Extract tables from SQLGlot AST."""
        sources = set()
        targets = set()

        # STEP 1: Extract targets FIRST (INSERT, UPDATE, MERGE, DELETE)
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

        # STEP 2: Extract sources (FROM, JOIN) - exclude targets
        for table in parsed.find_all(exp.Table):
            name = self._get_table_name(table)
            if name and name not in targets:
                sources.add(name)

        return sources, targets

    def _extract_dml_target(self, target_node) -> Optional[str]:
        """
        Extract target table from DML statement (INSERT/UPDATE/MERGE/DELETE).

        Handles both:
        - exp.Table: Direct table reference
        - exp.Schema: Wrapped table (happens with bracketed identifiers like [ADMIN].Logs)
        """
        if isinstance(target_node, exp.Table):
            # Direct table reference
            return self._get_table_name(target_node)

        elif isinstance(target_node, exp.Schema):
            # Schema wraps the table (happens with bracketed identifiers)
            # Schema structure: Schema.this = Table
            if target_node.this and isinstance(target_node.this, exp.Table):
                return self._get_table_name(target_node.this)

        return None

    def _get_table_name(self, table: exp.Table) -> Optional[str]:
        """Extract schema.table from Table node."""
        try:
            name = table.name
            if not name:
                return None

            name = name.strip('[]')
            schema = table.db if table.db else 'dbo'
            schema = schema.strip('[]')

            return f"{schema}.{name}"
        except Exception:
            return None

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

    def _validate_against_catalog(self, table_names: Set[str]) -> Set[str]:
        """Only return tables that exist in database."""
        catalog = self._get_object_catalog()
        validated = set()

        for name in table_names:
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

        query = f"""
        SELECT definition
        FROM definitions
        WHERE object_id = {validated_id}
        """

        results = self.workspace.query(query)
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

            query = f"""
            SELECT object_id
            FROM objects
            WHERE LOWER(schema_name) = LOWER('{schema}')
              AND LOWER(object_name) = LOWER('{obj_name}')
            """

            results = self.workspace.query(query)
            if results:
                object_ids.append(results[0][0])

        return object_ids

    def get_parse_statistics(self) -> Dict[str, Any]:
        """Get parser statistics."""
        query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN confidence >= 0.85 THEN 1 ELSE 0 END) as high_conf,
            SUM(CASE WHEN confidence >= 0.75 AND confidence < 0.85 THEN 1 ELSE 0 END) as med_conf,
            SUM(CASE WHEN confidence > 0 AND confidence < 0.75 THEN 1 ELSE 0 END) as low_conf,
            SUM(CASE WHEN confidence = 0 THEN 1 ELSE 0 END) as failed
        FROM lineage_metadata
        WHERE primary_source = 'parser'
        """

        results = self.workspace.query(query)
        if not results:
            return {}

        row = results[0]
        total = row[0]

        return {
            'total_parsed': total,
            'high_confidence': row[1],
            'medium_confidence': row[2],
            'low_confidence': row[3],
            'failed': row[4],
            'success_rate': (total - row[4]) / total * 100 if total > 0 else 0
        }
