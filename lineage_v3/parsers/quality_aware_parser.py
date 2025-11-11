r"""
Quality-Aware SQLGlot Parser - Smart extraction with built-in QA
================================================================

Strategy:
1. Regex scan full DDL → Get expected entity count (baseline)
2. Preprocess & split DDL → Parse with SQLGlot
3. Compare counts:
   - Match (±10%) → High confidence (0.85)
   - Partial match (±25%) → Medium confidence (0.75)
   - Major difference (>25%) → Low confidence (0.5)

This gives us quality assurance built into the parser!

Version: 4.1.3 (Dataflow-Focused Lineage - IF EXISTS Administrative Query Filtering)
Date: 2025-11-04

Changelog:
- v4.1.3 (2025-11-04): CRITICAL FIX - IF EXISTS/IF NOT EXISTS filtering
    Fixed: IF EXISTS (SELECT ... FROM Table) checks no longer create false input dependencies
    Issue: Administrative IF EXISTS checks were treated as data lineage sources
    Example: IF EXISTS (SELECT 1 FROM FactTable) DELETE FROM FactTable
             Previously: FactTable appeared as both input AND output (circular dependency)
             Now: FactTable appears only as output (correct)
    Root cause: IF EXISTS checks are control flow logic, not actual data dependencies
    Solution: Remove IF EXISTS/IF NOT EXISTS patterns during preprocessing (lines 150-165)
    Impact: Eliminates false bidirectional lineage for tables with existence checks
    Test case: spLoadFactLaborCostForEarnedValue now shows FactLaborCostForEarnedValue
               only as output, not as input
    Files: quality_aware_parser.py ENHANCED_REMOVAL_PATTERNS

- v4.1.2 (2025-11-04): CRITICAL FIX - Global target exclusion from sources
    Fixed: INSERT INTO target tables no longer appear in sources list
    Issue: find_all(exp.Table) extracts ALL tables from entire AST including DML targets
    Root cause: Target exclusion was per-statement, but sources accumulated across statements
    Example: Statement 1: INSERT INTO target → excludes target ✅
             Statement 2: WITH cte AS (SELECT FROM target) → includes target ❌
             Accumulated sources = {target} ← FALSE POSITIVE
    Solution: Global exclusion after all statements parsed (line 462: sources - targets)
    Impact: Eliminates false positive inputs for all DML operations
    Test: spLoadGLCognosData now shows GLCognosData only in outputs, not inputs
    Files: quality_aware_parser.py lines 430-464 (_sqlglot_parse method)

- v4.1.2 (2025-11-04): Balanced parentheses matching for administrative queries
    Fixed: SET/DECLARE @var = (SELECT COUNT(*) FROM Table) now correctly removes entire statement
    Solution: Pattern (?:[^()]|\([^()]*\))* matches balanced parentheses (1 level deep)
    Files: quality_aware_parser.py lines 166, 177

- v4.1.1 (2025-11-04): REGEX FIX attempt (incomplete - superseded by v4.1.2)
    Issue: Pattern still stopped at first ) in COUNT(*)
    Root cause: Non-greedy .*? still matched minimal content

- v4.1.0 (2025-11-04): DATAFLOW-FOCUSED LINEAGE
    Philosophy: Show only data transformation operations (DML), not housekeeping (DDL)
    Changes:
      1. Preprocessing: Replace CATCH blocks and ROLLBACK sections with SELECT 1 dummy
      2. Preprocessing: Replace DECLARE/SET @var = (SELECT ...) with literals (removes admin queries)
      3. AST Extraction: Only extract INSERT/UPDATE/DELETE/MERGE (exclude TRUNCATE/DROP)
    Impact: Cleaner lineage focused on business logic, removes administrative noise
    Example: spLoadGLCognosData now shows INSERT only (not SELECT COUNT or TRUNCATE)
    Breaking: Dataflow mode is now the default behavior (replaces "complete" mode)
- v4.0.3 (2025-11-04): CRITICAL FIX - SP-to-SP lineage direction
    Issue: EXEC/EXECUTE calls were added as INPUTS, making arrows point wrong direction in GUI
    Example: spLoadFactTables showed incoming arrows from SPs it calls (should be outgoing)
    Root Cause: Line 226-227 added sp_ids to input_ids instead of output_ids
    Fix: Changed sp_ids.extend(input_ids) → sp_ids.extend(output_ids)
    Rationale: When SP_A executes SP_B, SP_B is a TARGET/OUTPUT of SP_A (SP_A → SP_B)
    Impact: Corrects 151 SP-to-SP relationships to show proper call hierarchy
- v4.0.2 (2025-11-03): Orchestrator SP confidence fix
    Issue: SPs with only EXEC calls (no tables) got 0.50 confidence (divide-by-zero edge case)
    Fix: Special handling in _determine_confidence() for orchestrator SPs (0 tables + SP calls > 0)
    Result: 12 orchestrator/utility SPs 0.50→0.85 confidence (190→202 SPs = 100% at ≥0.85)
    Examples: spLoadFactTables, spLoadDimTables, spLoadArAnalyticsMetricsETL
- v4.0.1 (2025-11-03): CRITICAL IMPROVEMENTS
  Part 1: Statement boundary normalization
    Issue: SQLGlot requires semicolons, T-SQL doesn't - causing parse failures
    Fix 1: Add semicolons before DECLARE/SELECT/INSERT/UPDATE/DELETE/MERGE/TRUNCATE/WITH
    Fix 2: DECLARE pattern was greedy ([^;]+;) - now stops at line end ([^\n;]+(?:;|\n))
    Fix 3: SET pattern also fixed to be non-greedy
    Result: +69 stored procedures improved to high confidence (121→190 SPs at ≥0.85)
  Part 2: SP-to-SP lineage
    Issue: Removing ALL EXEC statements lost 151 business SP calls (17.8% of total)
    Fix: Only remove utility EXEC calls (LogMessage, spLastRowCount - 82.2%)
    Added: _validate_sp_calls() and _resolve_sp_names() methods
    Result: SP dependencies now tracked as inputs in lineage graph (CORRECTED in v4.0.3)
- v4.0.0 (2025-11-03): Remove AI disambiguation - focus on Regex + SQLGlot + Rule Engine
- v3.6.0 (2025-10-28): Add self-referencing pattern support
  Issue #2: Staging patterns (INSERT → SELECT → INSERT) not captured
  Fix: Statement-level target exclusion instead of global exclusion
- v3.5.0 (2025-10-28): Add TRUNCATE statement support
  Issue: spLoadGLCognosData and other SPs missing TRUNCATE outputs
  Fix: Add exp.TruncateTable extraction in _extract_from_ast()
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import sqlglot
from sqlglot import exp, parse_one
import logging
import re
import os

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from lineage_v3.utils.validators import validate_object_id, sanitize_identifier
from lineage_v3.utils.confidence_calculator import ConfidenceCalculator
from lineage_v3.parsers.comment_hints_parser import CommentHintsParser
from lineage_v3.parsers.sql_cleaning_rules import RuleEngine
from lineage_v3.config import settings


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
    CONFIDENCE_LOW = 0.5      # Major difference (>25%) - needs review/refinement

    # Quality check thresholds
    THRESHOLD_GOOD = 0.10     # ±10% difference
    THRESHOLD_FAIR = 0.25     # ±25% difference

    # Phantom schema configuration (v4.3.0)
    # Loaded from phantom_schema_config.yaml - INCLUDE list approach with wildcards
    PHANTOM_CONFIG_FILE = 'phantom_schema_config.yaml'

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
        # → BEGIN /* CATCH */ SELECT 1 END /* CATCH */ (SQLGlot can still parse)
        (r'BEGIN\s+/\*\s*CATCH\s*\*/.*?END\s+/\*\s*CATCH\s*\*/',
         'BEGIN /* CATCH */\n  -- Error handling removed for dataflow clarity\n  SELECT 1;\nEND /* CATCH */',
         re.DOTALL),

        # DATAFLOW: Replace content after ROLLBACK (failure paths not dataflow)
        # v4.1.0: NEW - Removes rollback recovery code
        # Example: ROLLBACK TRANSACTION; INSERT INTO ErrorLog ... → ROLLBACK TRANSACTION; SELECT 1;
        (r'ROLLBACK\s+TRANSACTION\s*;.*?(?=END|$)',
         'ROLLBACK TRANSACTION;\n  -- Rollback path removed for dataflow clarity\n  SELECT 1;\n',
         re.DOTALL),

        # Remove UTILITY EXEC commands (logging, counting, etc.)
        # Keep business SP calls - they are important lineage!
        # v4.0.1: Changed from removing ALL EXEC to only removing utility calls
        # Utility SPs: LogMessage, spLastRowCount (82.2% of all EXEC calls)
        # Example: EXEC [dbo].[LogMessage] 'Processing complete'
        (r'\bEXEC(?:UTE)?\s+(?:\[?dbo\]?\.)?\[?(spLastRowCount|LogMessage)\]?[^;]*;?', '', re.IGNORECASE),

        # DATAFLOW: Replace DECLARE @var = (SELECT ...) with literal (removes admin queries)
        # v4.1.0: Changed from removing to replacing with literal value
        # v4.1.1: Fixed regex to handle nested parentheses (e.g., COUNT(*))
        # v4.1.2: Proper balanced parentheses matching - handles COUNT(*), MAX(), etc.
        # Example: DECLARE @RowCount INT = (SELECT COUNT(*) FROM Table)
        # → DECLARE @RowCount INT = 1  -- Administrative query removed
        # This prevents SELECT COUNT(*) from appearing as lineage dependency
        # Pattern: (?:[^()]|\([^()]*\))* matches nested parens correctly
        (r'DECLARE\s+(@\w+)\s+(\w+(?:\([^\)]*\))?)\s*=\s*\((?:[^()]|\([^()]*\))*\)',
         r'DECLARE \1 \2 = 1  -- Administrative query removed',
         0),

        # DATAFLOW: Replace SET @var = (SELECT ...) with literal (removes admin queries)
        # v4.1.0: Changed from removing to replacing with literal value
        # v4.1.1: Fixed regex to handle nested parentheses (e.g., COUNT(*))
        # v4.1.2: Proper balanced parentheses matching - handles COUNT(*), MAX(), etc.
        # Example: SET @RowCount = (SELECT COUNT(*) FROM Table)
        # → SET @RowCount = 1  -- Administrative query removed
        # Pattern: (?:[^()]|\([^()]*\))* matches nested parens (1 level deep) correctly
        (r'SET\s+(@\w+)\s*=\s*\((?:[^()]|\([^()]*\))*\)',
         r'SET \1 = 1  -- Administrative query removed',
         0),

        # Remove other DECLARE statements (variable declarations clutter parsing)
        # Variables without SELECT are simple declarations, safe to remove
        # Example: DECLARE @StartDate DATETIME = GETDATE()
        (r'\bDECLARE\s+@\w+\s+[^\n;]+(?:;|\n)', '', 0),

        # Remove other SET statements (variable assignments without SELECT)
        # Example: SET @Count = @Count + 1
        (r'\bSET\s+@\w+\s*=\s*[^\n;]+(?:;|\n)', '', 0),

        # Remove SET session options (NOCOUNT, XACT_ABORT, etc.)
        # Session settings don't affect data lineage
        # Example: SET NOCOUNT ON, SET XACT_ABORT ON, SET ANSI_NULLS ON
        (r'\bSET\s+(NOCOUNT|XACT_ABORT|ANSI_NULLS|QUOTED_IDENTIFIER|ANSI_PADDING|ANSI_WARNINGS|ARITHABORT|CONCAT_NULL_YIELDS_NULL|NUMERIC_ROUNDABORT)\s+(ON|OFF)\b', '', 0),
    ]

    def __init__(self, workspace: DuckDBWorkspace, enable_sql_cleaning: bool = True):
        """
        Initialize parser with DuckDB workspace.

        Args:
            workspace: DuckDB workspace for catalog access
            enable_sql_cleaning: Enable SQL Cleaning Engine for improved SQLGlot success (default: True)
        """
        self.workspace = workspace
        self._object_catalog = None
        self.hints_parser = CommentHintsParser(workspace)

        # SQL Cleaning Engine integration (v4.2.0 improvement)
        self.enable_sql_cleaning = enable_sql_cleaning
        if self.enable_sql_cleaning:
            self.cleaning_engine = RuleEngine()
            logger.info("SQL Cleaning Engine enabled (expected +27% SQLGlot success rate)")

        # Load phantom schema configuration (v4.3.0)
        self._load_phantom_config()

    def _load_phantom_config(self):
        """Load phantom schema configuration from centralized settings (v4.3.0)."""
        import re
        from lineage_v3.config.settings import settings

        # Load from centralized Pydantic settings (configured via .env or defaults)
        self.include_schemas = settings.phantom.include_schema_list
        self.excluded_schemas = settings.excluded_schema_set  # Global universal exclusion
        self.excluded_dbo_patterns = settings.phantom.exclude_dbo_pattern_list

        logger.info(f"Loaded phantom config from settings.py: {len(self.include_schemas)} include patterns")
        logger.debug(f"Include patterns: {self.include_schemas}")
        logger.debug(f"Universal excluded schemas: {self.excluded_schemas}")

        # Compile include patterns to regex for efficient matching
        self.include_schema_patterns = []
        for pattern in self.include_schemas:
            # Convert wildcard pattern to regex
            regex_pattern = pattern.replace('*', '.*')
            self.include_schema_patterns.append(re.compile(f'^{regex_pattern}$', re.IGNORECASE))

    def _schema_matches_include_list(self, schema: str) -> bool:
        """
        Check if schema matches any include pattern (v4.3.0).

        Uses wildcard matching (e.g., CONSUMPTION* matches CONSUMPTION_FINANCE).
        Returns True if schema should have phantoms created.
        """
        # First check if it's in the global excluded_schemas (universal filter)
        if schema.lower() in [s.lower() for s in self.excluded_schemas]:
            return False

        # Check if schema matches any include pattern
        for pattern in self.include_schema_patterns:
            if pattern.match(schema):
                return True

        return False

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
                    'needs_improvement': bool
                }
            }
        """
        # Fetch DDL
        ddl = self._fetch_ddl(object_id)
        if not ddl:
            # Generate failure breakdown for missing DDL (v2.1.0)
            result = ConfidenceCalculator.calculate_simple(
                parse_succeeded=False,
                expected_tables=0,
                found_tables=0,
                is_orchestrator=False,
                parse_failure_reason='No DDL definition found'
            )

            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'confidence': result['confidence'],  # 0 for missing DDL
                'source': 'parser',
                'parse_error': 'No DDL definition found',
                'confidence_breakdown': result['breakdown']
            }

        try:
            # STEP 1: Regex baseline (expected counts)
            regex_sources, regex_targets, regex_sp_calls, regex_function_calls = self._regex_scan(ddl)
            regex_sources_valid = self._validate_against_catalog(regex_sources)
            regex_targets_valid = self._validate_against_catalog(regex_targets)
            regex_sp_calls_valid = self._validate_sp_calls(regex_sp_calls)
            regex_function_calls_valid = self._validate_function_calls(regex_function_calls)  # v4.3.0

            # STEP 2: Preprocess and parse with SQLGlot
            cleaned_ddl = self._preprocess_ddl(ddl)
            parser_sources, parser_targets = self._sqlglot_parse(cleaned_ddl, ddl)
            parser_sources_valid = self._validate_against_catalog(parser_sources)
            parser_targets_valid = self._validate_against_catalog(parser_targets)

            # STEP 2b: Extract comment hints (v4.2.0)
            # Use original DDL (not cleaned) to preserve hints in CATCH blocks
            hint_inputs, hint_outputs = self.hints_parser.extract_hints(ddl, validate=True)

            # Log hint extraction
            if hint_inputs or hint_outputs:
                logger.info(f"Comment hints found: {len(hint_inputs)} inputs, {len(hint_outputs)} outputs")
                logger.debug(f"  Hint inputs: {hint_inputs}")
                logger.debug(f"  Hint outputs: {hint_outputs}")

            # UNION hints with parser results (no duplicates)
            parser_sources_with_hints = parser_sources_valid | hint_inputs
            parser_targets_with_hints = parser_targets_valid | hint_outputs

            # STEP 2c: Detect phantom objects (v4.3.0 - Phantom Objects Feature)
            # Phantoms are tables NOT in catalog (missing metadata)
            phantom_sources = self._detect_phantom_tables(parser_sources | hint_inputs)
            phantom_targets = self._detect_phantom_tables(parser_targets | hint_outputs)
            all_phantoms = phantom_sources | phantom_targets

            if all_phantoms:
                logger.info(f"Detected {len(all_phantoms)} phantom objects: {all_phantoms}")

            # STEP 3: Calculate catalog validation rate (for diagnostics)
            # Get all objects from catalog for validation
            all_extracted = parser_sources_with_hints | parser_targets_with_hints
            all_catalog = self._get_catalog_objects()
            if all_extracted:
                valid_count = len(all_extracted & all_catalog)
                catalog_validation_rate = valid_count / len(all_extracted)
            else:
                catalog_validation_rate = 1.0  # No objects to validate = 100% valid

            # STEP 4: Determine if hints were used
            has_hints = bool(hint_inputs or hint_outputs)

            # STEP 5: Resolve to object_ids (use results WITH hints)
            input_ids = self._resolve_table_names(parser_sources_with_hints)
            output_ids = self._resolve_table_names(parser_targets_with_hints)

            # STEP 5b: Add SP-to-SP lineage (v4.0.1)
            # Stored procedures are OUTPUTS (we call/execute them)
            # When SP_A executes SP_B: SP_A → SP_B (SP_B is a target/output)
            sp_ids = self._resolve_sp_names(regex_sp_calls_valid)
            output_ids.extend(sp_ids)

            # STEP 5b2: Add function lineage (v4.3.0 - UDF support)
            # Functions are INPUTS (we use/read them)
            # When SP_A uses func_B: func_B → SP_A (func_B is a source/input)
            func_ids = self._resolve_function_names(regex_function_calls_valid)
            input_ids.extend(func_ids)

            # STEP 5c: Handle phantom objects (v4.3.0)
            # Create/get phantom objects and their negative IDs
            # Add to inputs/outputs for visualization, but DON'T count in confidence
            phantom_ids_map = self._create_or_get_phantom_objects(all_phantoms, object_type='Table')

            # Add phantom IDs to inputs/outputs
            phantom_input_ids = [phantom_ids_map[name] for name in phantom_sources if name in phantom_ids_map]
            phantom_output_ids = [phantom_ids_map[name] for name in phantom_targets if name in phantom_ids_map]
            input_ids.extend(phantom_input_ids)
            output_ids.extend(phantom_output_ids)

            # Track phantom references for impact analysis (used during promotion)
            if phantom_ids_map:
                dependency_types = {}
                for name in phantom_sources:
                    dependency_types[name] = 'input'
                for name in phantom_targets:
                    dependency_types[name] = 'output'
                self._track_phantom_references(object_id, phantom_ids_map, dependency_types)

            # STEP 5d: Handle phantom functions (v4.3.0 - UDF support)
            # Detect functions not in catalog
            phantom_functions = set()
            for func_name in regex_function_calls:
                if func_name not in regex_function_calls_valid:
                    # Function not in catalog, check if it's excluded
                    parts = func_name.split('.')
                    if len(parts) == 2:
                        schema, name = parts
                        if not self._is_excluded(schema, name):
                            phantom_functions.add(func_name)

            if phantom_functions:
                logger.info(f"Detected {len(phantom_functions)} phantom functions: {phantom_functions}")
                phantom_func_ids_map = self._create_or_get_phantom_objects(phantom_functions, object_type='Function')

                # Add phantom function IDs to inputs
                phantom_func_ids = [phantom_func_ids_map[name] for name in phantom_functions if name in phantom_func_ids_map]
                input_ids.extend(phantom_func_ids)

                # Track phantom function references
                if phantom_func_ids_map:
                    func_dependency_types = {name: 'input' for name in phantom_functions}
                    self._track_phantom_references(object_id, phantom_func_ids_map, func_dependency_types)

            # STEP 6: Calculate expected vs found counts for confidence calculation (v2.1.0)
            # IMPORTANT: Phantoms and functions do NOT count in found_count (confidence based on real catalog table matches only)
            expected_count = len(regex_sources_valid) + len(regex_targets_valid)
            # Exclude: SP IDs, function IDs, and all phantom IDs
            phantom_func_ids_count = len(phantom_func_ids) if phantom_functions else 0
            found_count = len(input_ids) + len(output_ids) - len(sp_ids) - len(func_ids) - len(phantom_input_ids) - len(phantom_output_ids) - phantom_func_ids_count

            # Detect orchestrator SPs (only calls other SPs, no table access)
            is_orchestrator = (expected_count == 0 and len(regex_sp_calls_valid) > 0)

            # STEP 7: Calculate simplified confidence (v2.1.0)
            parse_success = True  # If we got here, parsing succeeded
            confidence, confidence_breakdown = self._determine_confidence(
                parse_success=parse_success,
                expected_count=expected_count,
                found_count=found_count,
                is_orchestrator=is_orchestrator,
                parse_failure_reason=None  # No failure, parsing succeeded
            )

            # Generate failure reason if confidence is low (for diagnostics)
            parse_failure_reason = None
            if confidence < 75:  # v2.1.0: confidence < 75 means poor quality
                parse_failure_reason = self._detect_parse_failure_reason(
                    ddl=ddl,
                    parse_error=None,
                    expected_count=expected_count,
                    found_count=found_count
                )
                logger.warning(f"Low confidence ({confidence}) for object_id {object_id}: {parse_failure_reason}")

            return {
                'object_id': object_id,
                'inputs': input_ids,
                'outputs': output_ids,
                'confidence': confidence,
                'source': 'parser_with_hints' if has_hints else 'parser',
                'parse_error': None,
                'parse_failure_reason': parse_failure_reason,  # v4.2.0: Actionable guidance
                'expected_count': expected_count,  # v4.2.0: From smoke test
                'found_count': found_count,        # v4.2.0: Actual extracted
                'quality_check': {
                    'regex_sources': len(regex_sources_valid),
                    'regex_targets': len(regex_targets_valid),
                    'regex_sp_calls': len(regex_sp_calls_valid),
                    'parser_sources': len(parser_sources_valid),
                    'parser_targets': len(parser_targets_valid),
                    'hint_inputs': len(hint_inputs),
                    'hint_outputs': len(hint_outputs),
                    'final_sources': len(parser_sources_with_hints),
                    'final_targets': len(parser_targets_with_hints),
                    'catalog_validation_rate': catalog_validation_rate
                },
                'confidence_breakdown': confidence_breakdown  # Simplified breakdown (v2.1.0)
            }

        except Exception as e:
            logger.error(f"Failed to parse object_id {object_id}: {e}")

            # Detect failure reason (v4.2.0)
            parse_failure_reason = self._detect_parse_failure_reason(
                ddl=ddl,
                parse_error=str(e),
                expected_count=0,
                found_count=0
            )

            # Generate failure breakdown (v2.1.0)
            result = ConfidenceCalculator.calculate_simple(
                parse_succeeded=False,
                expected_tables=0,
                found_tables=0,
                is_orchestrator=False,
                parse_failure_reason=parse_failure_reason
            )

            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'confidence': result['confidence'],  # 0 for parse failures
                'source': 'parser',
                'parse_error': str(e),
                'parse_failure_reason': parse_failure_reason,  # v4.2.0: Actionable guidance
                'expected_count': 0,  # v4.2.0
                'found_count': 0,     # v4.2.0
                'confidence_breakdown': result['breakdown']
            }

    def _regex_scan(self, ddl: str) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
        """
        Scan full DDL with regex to get expected entity counts.

        This is the BASELINE - what we expect to find.

        CRITICAL (2025-11-08): Smoke test counts BUSINESS LOGIC only
        - Runs on RAW DDL (no pre-filtering to detect aggressive cleaning)
        - Counts DML only: INSERT, UPDATE, DELETE, MERGE (data transformation)
        - Excludes DDL: TRUNCATE, CREATE, DROP, ALTER (housekeeping)
        - Excludes temp objects: CTEs, #temp tables, @table variables
        - Rationale: Align baseline with dataflow mode expectations
        """
        sources = set()
        targets = set()

        # Remove comments
        ddl = re.sub(r'--[^\n]*', '', ddl)
        ddl = re.sub(r'/\*.*?\*/', '', ddl, flags=re.DOTALL)

        # STEP 1: Identify non-persistent objects to exclude
        non_persistent = self._identify_non_persistent_objects(ddl)
        logger.debug(f"Found {len(non_persistent)} non-persistent objects: {non_persistent}")

        # STEP 2: Remove administrative queries before counting (2025-11-08)
        # These are filtered by cleaning engine, so shouldn't be in baseline count
        # Pattern: SET/DECLARE @var = (SELECT ... FROM Table) → Remove entire statement
        # Handles nested parentheses like COUNT(*) correctly
        # Result: COUNT(*) and other administrative SELECT won't be counted
        ddl_no_admin = re.sub(
            r'(?:SET|DECLARE)\s+@\w+.*?(?:;|\n)',
            '\n',
            ddl,
            flags=re.IGNORECASE | re.DOTALL
        )
        logger.debug("Removed administrative SET/DECLARE queries from smoke test count")

        # SOURCE patterns (tables we READ FROM)
        # Pattern explanation:
        # - \b = word boundary (ensures we match full keywords)
        # - \[? and \]? = optional brackets (Synapse allows [schema].[table])
        # - (\w+) = capture group for schema/table name (alphanumeric + underscore)
        # - (?:OUTER\s+)? = optional OUTER keyword (non-capturing group)
        source_patterns = [
            r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?',                      # FROM [schema].[table]
            r'\bJOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',                      # JOIN [schema].[table]
            r'\bINNER\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',              # INNER JOIN
            r'\bLEFT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',  # LEFT [OUTER] JOIN
            r'\bRIGHT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?', # RIGHT [OUTER] JOIN
            r'\bFULL\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',  # FULL [OUTER] JOIN
        ]

        for pattern in source_patterns:
            # Run patterns on DDL with admin queries removed
            matches = re.findall(pattern, ddl_no_admin, re.IGNORECASE)
            for schema, table in matches:
                # Existing exclusions (system schemas)
                if self._is_excluded(schema, table):
                    continue

                # NEW: Filter non-persistent objects
                if self._is_non_persistent(schema, table, non_persistent):
                    continue

                sources.add(f"{schema}.{table}")

        # TARGET patterns (tables we WRITE TO)
        # CRITICAL (2025-11-08): Smoke test counts ONLY DML operations (data transformation)
        # - Counts: INSERT, UPDATE, DELETE, MERGE (actual data changes)
        # - Excludes: TRUNCATE, CREATE, DROP, ALTER (DDL housekeeping)
        # - Rationale: Align baseline with dataflow mode (business logic only)
        # Pattern explanation: Same as SOURCE patterns above
        target_patterns = [
            r'\bINSERT\s+(?:INTO\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',  # INSERT [INTO] [schema].[table]
            r'\bUPDATE\s+\[?(\w+)\]?\.\[?(\w+)\]?\s+SET',        # UPDATE [schema].[table] SET
            r'\bMERGE\s+(?:INTO\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',   # MERGE [INTO] [schema].[table]
            r'\bDELETE\s+(?:FROM\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',  # DELETE [FROM] [schema].[table]
            # TRUNCATE excluded - DDL housekeeping, not data transformation
            # CREATE/DROP/ALTER excluded - DDL, not counted by smoke test
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

        # SP CALL patterns (stored procedures we call)
        # v4.0.1: Added SP-to-SP lineage detection
        # Pattern: EXEC [schema].[sp_name] or EXECUTE [schema].[sp_name]
        # Note: Utility SPs (LogMessage, spLastRowCount) are already removed by preprocessing
        sp_calls = set()
        sp_call_patterns = [
            r'\bEXEC(?:UTE)?\s+\[?(\w+)\]?\.\[?(\w+)\]?',  # EXEC [schema].[sp_name]
        ]

        for pattern in sp_call_patterns:
            matches = re.findall(pattern, ddl, re.IGNORECASE)
            for schema, sp_name in matches:
                # Skip utility SPs (in case they weren't removed by preprocessing)
                if sp_name.lower() in ['splastrowcount', 'logmessage']:
                    continue

                # Skip system schemas
                if self._is_excluded(schema, sp_name):
                    continue

                sp_calls.add(f"{schema}.{sp_name}")

        # FUNCTION CALL patterns (UDFs - v4.3.0)
        # Detects both scalar and table-valued functions:
        # - Scalar: SELECT dbo.GetPrice(id) FROM Table
        # - Table-valued: FROM dbo.GetOrders() o, FROM dbo.GetOrdersByDate(@date) AS o
        # Pattern: [schema].[function_name](...) - function call with parentheses
        function_calls = set()
        function_patterns = [
            # Table-valued functions in FROM/JOIN (most common)
            r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # FROM [schema].[function](
            r'\bJOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # JOIN [schema].[function](
            r'\bINNER\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # INNER JOIN [schema].[function](
            r'\bLEFT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # LEFT JOIN [schema].[function](
            r'\bRIGHT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # RIGHT JOIN [schema].[function](
            r'\bCROSS\s+APPLY\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # CROSS APPLY [schema].[function](
            r'\bOUTER\s+APPLY\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # OUTER APPLY [schema].[function](
            # Scalar functions anywhere (general pattern)
            # Matches schema.function( pattern - catches all UDF calls
            r'\b\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # [schema].[function](
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, ddl, re.IGNORECASE)
            for schema, func_name in matches:
                # Skip built-in functions (CAST, CONVERT, etc.)
                if func_name.upper() in ['CAST', 'CONVERT', 'COALESCE', 'ISNULL', 'CASE', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN']:
                    continue

                # Skip system schemas
                if self._is_excluded(schema, func_name):
                    continue

                function_calls.add(f"{schema}.{func_name}")

        logger.debug(f"Regex baseline: {len(sources)} sources, {len(targets)} targets, {len(sp_calls)} SP calls, {len(function_calls)} function calls (after filtering)")
        return sources, targets, sp_calls, function_calls

    def _sqlglot_parse(self, cleaned_ddl: str, original_ddl: str) -> Tuple[Set[str], Set[str]]:
        """
        Parse with SQLGlot after preprocessing.

        v4.1.2 CRITICAL FIX: Exclude targets from sources GLOBALLY
        ----------------------------------------------------------
        Previous bug: Targets were excluded per-statement, but sources from
        other statements could reference the same table as a source.

        Example:
          Statement 1: INSERT INTO target SELECT FROM source
                       → targets={target}, sources={source} ✅ target excluded
          Statement 2: WITH cte AS (SELECT FROM target) SELECT FROM cte
                       → targets={}, sources={target} ❌ target NOT excluded (not a target in THIS statement)

        Solution: Collect all targets first, then remove from final sources.
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
                regex_s, regex_t, _, _ = self._regex_scan(stmt)  # Ignore SP/function calls in statement fallback
                sources.update(regex_s)
                targets.update(regex_t)

        # If SQLGlot got nothing, fallback to regex on original DDL
        if not sources and not targets:
            sources, targets, _, _ = self._regex_scan(original_ddl)  # Ignore SP/function calls in full fallback

        # v4.1.2 FIX: Remove all targets from sources AFTER parsing all statements
        # This prevents false positives where a table is a target in one statement
        # but appears as a source in another statement (e.g., CTEs, temp tables)
        sources_final = sources - targets

        return sources_final, targets

    def _calculate_quality(
        self,
        regex_sources: int,
        regex_targets: int,
        parser_sources: int,
        parser_targets: int
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics by comparing regex baseline to parser results.

        KEY FIX: If BOTH regex and parser find zero dependencies, this indicates
        a PARSE FAILURE (DDL too complex), not a perfect match. Returns 0.0.

        Returns:
            {
                'source_match': float (0.0-1.0),
                'target_match': float (0.0-1.0),
                'overall_match': float (0.0-1.0),
                'needs_improvement': bool
            }
        """
        # CRITICAL FIX: Detect parse failure (both found nothing)
        # This means the DDL is too complex for both regex AND parser to handle
        if (regex_sources == 0 and regex_targets == 0 and
            parser_sources == 0 and parser_targets == 0):
            return {
                'source_match': 0.0,
                'target_match': 0.0,
                'overall_match': 0.0,  # FAIL, not 1.0!
                'needs_improvement': True
            }

        # Calculate match percentages
        if regex_sources > 0:
            source_match = min(parser_sources / regex_sources, 1.0)
        else:
            # If regex found nothing but parser found something, that's good
            source_match = 1.0 if parser_sources == 0 else 1.0

        if regex_targets > 0:
            target_match = min(parser_targets / regex_targets, 1.0)
        else:
            # If regex found nothing but parser found something, that's good
            target_match = 1.0 if parser_targets == 0 else 1.0

        # Overall match (weighted average - targets more important)
        overall_match = (source_match * 0.4) + (target_match * 0.6)

        # Flag for review if either is significantly off
        source_diff = abs(regex_sources - parser_sources) / max(regex_sources, parser_sources, 1)
        target_diff = abs(regex_targets - parser_targets) / max(regex_targets, parser_targets, 1)

        needs_improvement = (source_diff > self.THRESHOLD_FAIR or
                            target_diff > self.THRESHOLD_FAIR)

        return {
            'source_match': source_match,
            'target_match': target_match,
            'overall_match': overall_match,
            'needs_improvement': needs_improvement
        }

    def _determine_confidence(
        self,
        parse_success: bool,
        expected_count: int,
        found_count: int,
        is_orchestrator: bool = False,
        parse_failure_reason: Optional[str] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Determine confidence score using simplified model (v2.1.0).

        Uses unified ConfidenceCalculator.calculate_simple() for consistency
        across the application.

        Simplified 4-value Model:
        - Parse failed → 0%
        - Orchestrator (only EXEC, no tables) → 100%
        - Completeness ≥90% → 100%
        - Completeness 70-89% → 85%
        - Completeness 50-69% → 75%
        - Completeness <50% → 0%

        Args:
            parse_success: Whether parsing completed without errors
            expected_count: Number of tables expected (from regex baseline)
            found_count: Number of tables actually found by parser
            is_orchestrator: Whether SP only calls other SPs (no table access)
            parse_failure_reason: Optional reason for parse failure

        Returns:
            Tuple of (confidence_score, breakdown_dict)
                confidence_score: 0 | 75 | 85 | 100
                breakdown_dict: {parse_succeeded, expected_tables, found_tables,
                                completeness_pct, explanation, to_improve}
        """
        # Use unified simplified confidence calculator (v2.1.0)
        result = ConfidenceCalculator.calculate_simple(
            parse_succeeded=parse_success,
            expected_tables=expected_count,
            found_tables=found_count,
            is_orchestrator=is_orchestrator,
            parse_failure_reason=parse_failure_reason
        )

        confidence = result['confidence']
        breakdown = result['breakdown']

        logger.debug(f"Simplified confidence: {confidence} (completeness: {breakdown.get('completeness_pct', 0):.1f}%)")
        return confidence, breakdown

    def _is_excluded(self, schema: str, table: str) -> bool:
        """Check if table should be excluded (temp tables, system schemas)."""
        if schema.lower() in self.EXCLUDED_SCHEMAS:
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
        Preprocess DDL to make it parseable by SQLGlot/SQLLineage.

        **Goal:** Extract only the core business logic (data movement statements)
        and remove T-SQL specific syntax that breaks SQL parsers.

        **Enhanced Strategy (2025-11-07 - SQL Cleaning Engine Integration):**
        1. **NEW**: Apply SQL Cleaning Engine rules (if enabled) for +27% SQLGlot success
           - Removes GO, DECLARE, SET, TRY/CATCH, RAISERROR, EXEC, transactions
           - Extracts core DML from CREATE PROC wrapper
           - 10 declarative rules with priority-based execution
        2. **Fallback**: Legacy regex-based preprocessing (if cleaning disabled)

        **Original Strategy (2025-11-03):**
        1. Normalize statement boundaries with semicolons (SQLGlot requirement)
        2. Fix DECLARE pattern to avoid greedy matching
        3. Focus on TRY block (business logic), remove CATCH/EXEC/post-COMMIT noise

        Args:
            ddl: Raw DDL from sys.sql_modules.definition

        Returns:
            Cleaned DDL ready for parser consumption
        """
        # Step 0: Apply SQL Cleaning Engine (if enabled)
        # This is a more sophisticated rule-based approach that improves SQLGlot success by 27%
        # (Baseline 53.6% → Improved 80.8% based on 349 production SPs)
        if self.enable_sql_cleaning:
            try:
                cleaned = self.cleaning_engine.apply_all(ddl, verbose=False)
                logger.debug(f"SQL Cleaning Engine applied: {len(ddl)} → {len(cleaned)} bytes")
                # Return early - cleaning engine handles all preprocessing
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
        # SQLGlot expects semicolons to separate statements, but T-SQL doesn't require them
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
        """
        Extract tables from SQLGlot AST.

        DATAFLOW MODE (v4.1.0): Only extracts DML operations
        -------------------------------------------------------
        Includes:
          - INSERT INTO (data transformation)
          - UPDATE (data modification)
          - DELETE (data removal)
          - MERGE (data upsert)
          - SELECT INTO (data creation)

        Excludes:
          - TRUNCATE (DDL housekeeping, not transformation)
          - DROP (DDL housekeeping)
          - Administrative SELECT (filtered in preprocessing)

        Enhanced to handle SELECT INTO statements correctly:
        - SELECT ... INTO #temp FROM source_table
        - #temp is a target (temp table, filtered from lineage)
        - source_table is a source (should be included)
        """
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
                # SQLGlot wraps INTO in exp.Into object
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
        # SQLGlot structure:
        #   INSERT.this = target table
        #   INSERT.expression = SELECT statement with sources
        #
        # Solution: Exclude DML targets from source extraction (per-statement)
        # Note: Global exclusion also happens in _sqlglot_parse() after all statements
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

    def _detect_phantom_tables(self, table_names: Set[str]) -> Set[str]:
        """
        Detect phantom tables (not in catalog, but not excluded).

        v4.3.0: Phantom Objects Feature
        Returns tables that are:
        - NOT in catalog (real metadata)
        - NOT dummy.* (temp table placeholders)
        - NOT sys.* or information_schema.* (system schemas)

        These are likely missing metadata or external references.
        """
        catalog = self._get_object_catalog()
        phantoms = set()

        for name in table_names:
            # Parse schema.object format
            parts = name.split('.')
            if len(parts) != 2:
                continue

            schema, table = parts

            # v4.3.0: INCLUDE LIST APPROACH - Only create phantoms for schemas matching include patterns
            if not self._schema_matches_include_list(schema):
                logger.debug(f"Skipping phantom (schema not in include list): {name}")
                continue

            # Additional filtering for dbo schema CTEs and temp objects
            if schema.lower() == 'dbo':
                table_lower = table.lower()

                # Check if table name matches any exclusion pattern
                skip = False
                for pattern in self.excluded_dbo_patterns:
                    pattern_lower = pattern.lower()
                    # Handle different pattern types
                    if '*' in pattern:
                        # Wildcard pattern
                        prefix = pattern_lower.replace('*', '')
                        if table_lower.startswith(prefix):
                            logger.debug(f"Excluding dbo object (wildcard match '{pattern}'): {name}")
                            skip = True
                            break
                    elif table_lower == pattern_lower:
                        # Exact match
                        logger.debug(f"Excluding dbo object (exact match): {name}")
                        skip = True
                        break
                    elif table_lower.startswith(pattern_lower):
                        # Prefix match
                        logger.debug(f"Excluding dbo object (prefix match '{pattern}'): {name}")
                        skip = True
                        break

                if skip:
                    continue

                # Also exclude objects starting with # or @
                if table.startswith('#') or table.startswith('@'):
                    logger.debug(f"Excluding temp table/variable: {name}")
                    continue

            # If not in catalog (case-insensitive), it's a phantom
            if name not in catalog:
                name_lower = name.lower()
                found = False
                for catalog_name in catalog:
                    if catalog_name.lower() == name_lower:
                        found = True
                        break

                if not found:
                    phantoms.add(name)
                    logger.debug(f"Phantom detected: {name}")

        logger.info(f"Identified {len(phantoms)} phantom objects (include-list filtered)")
        return phantoms

    def _create_or_get_phantom_objects(self, phantom_names: Set[str], object_type: str = 'Table') -> Dict[str, int]:
        """
        Create or get phantom objects in database.

        v4.3.0: Phantom Objects Feature
        Uses UPSERT logic to avoid duplicates.
        Returns mapping of table/function_name -> phantom_id (negative).

        Args:
            phantom_names: Set of schema.object names
            object_type: 'Table' or 'Function' (default: 'Table')

        Returns:
            Dict mapping "schema.object" -> phantom_id (negative int)
        """
        if not phantom_names:
            return {}

        phantom_map = {}

        for name in phantom_names:
            parts = name.split('.')
            if len(parts) != 2:
                logger.warning(f"Skipping invalid phantom name: {name}")
                continue

            schema, obj_name = parts

            # Check if phantom already exists
            check_query = """
                SELECT object_id
                FROM phantom_objects
                WHERE LOWER(schema_name) = LOWER(?)
                  AND LOWER(object_name) = LOWER(?)
                  AND is_promoted = FALSE
            """
            results = self.workspace.query(check_query, params=[schema, obj_name])

            if results:
                # Phantom exists, update last_seen
                phantom_id = results[0][0]
                update_query = """
                    UPDATE phantom_objects
                    SET last_seen = CURRENT_TIMESTAMP
                    WHERE object_id = ?
                """
                self.workspace.query(update_query, params=[phantom_id])
                phantom_map[name] = phantom_id
                logger.debug(f"Updated existing phantom: {name} (ID: {phantom_id})")
            else:
                # Create new phantom
                insert_query = """
                    INSERT INTO phantom_objects (schema_name, object_name, object_type, phantom_reason)
                    VALUES (?, ?, ?, 'not_in_catalog')
                """
                self.workspace.query(insert_query, params=[schema, obj_name, object_type])

                # Get the auto-generated negative ID
                get_id_query = """
                    SELECT object_id
                    FROM phantom_objects
                    WHERE LOWER(schema_name) = LOWER(?)
                      AND LOWER(object_name) = LOWER(?)
                    ORDER BY first_seen DESC
                    LIMIT 1
                """
                results = self.workspace.query(get_id_query, params=[schema, table])
                if results:
                    phantom_id = results[0][0]
                    phantom_map[name] = phantom_id
                    logger.info(f"Created phantom: {name} (ID: {phantom_id})")
                else:
                    logger.error(f"Failed to get phantom ID for {name}")

        return phantom_map

    def _track_phantom_references(self, sp_id: int, phantom_ids: Dict[str, int], dependency_types: Dict[str, str]):
        """
        Track which SPs reference which phantoms.

        v4.3.0: Phantom Objects Feature
        Used for impact analysis when phantom is promoted.

        Args:
            sp_id: Stored procedure object_id
            phantom_ids: Dict mapping table_name -> phantom_id
            dependency_types: Dict mapping table_name -> 'input' or 'output'
        """
        if not phantom_ids:
            return

        for table_name, phantom_id in phantom_ids.items():
            dep_type = dependency_types.get(table_name, 'unknown')

            # UPSERT phantom reference
            upsert_query = """
                INSERT INTO phantom_references (phantom_id, referencing_sp_id, dependency_type, last_seen)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (phantom_id, referencing_sp_id, dependency_type)
                DO UPDATE SET last_seen = CURRENT_TIMESTAMP
            """
            try:
                self.workspace.query(upsert_query, params=[phantom_id, sp_id, dep_type])
                logger.debug(f"Tracked phantom reference: SP {sp_id} -> Phantom {phantom_id} ({dep_type})")
            except Exception as e:
                logger.warning(f"Failed to track phantom reference: {e}")

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
            parse_error: Optional SQLGlot parse error message
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

        # Fallback: Use SQLGlot error if available
        if not reasons and parse_error:
            reasons.append(f"SQLGlot parse error: {parse_error[:100]}")

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

    def extract_sqlglot_dependencies(self, ddl: str) -> Dict[str, Any]:
        """
        Public wrapper for SQLGlot extraction (used by evaluation subagent).

        Runs SQLGlot AST parsing with preprocessing.
        Includes quality check metrics (comparison to regex baseline).

        Args:
            ddl: SQL DDL text

        Returns:
            {
                'sources': Set[str],
                'targets': Set[str],
                'sources_validated': Set[str],
                'targets_validated': Set[str],
                'sources_count': int,
                'targets_count': int,
                'quality_check': {
                    'regex_sources': int,
                    'regex_targets': int,
                    'parser_sources': int,
                    'parser_targets': int,
                    'source_match': float,
                    'target_match': float,
                    'overall_match': float,
                    'needs_improvement': bool
                }
            }
        """
        # Preprocess DDL (same as production)
        cleaned_ddl = self._preprocess_ddl(ddl)

        # Parse with SQLGlot
        sources, targets = self._sqlglot_parse(cleaned_ddl, ddl)

        # Validate against catalog
        sources_validated = self._validate_against_catalog(sources)
        targets_validated = self._validate_against_catalog(targets)

        # Run quality check (compare to regex baseline)
        regex_result = self.extract_regex_dependencies(ddl)
        quality = self._calculate_quality(
            len(regex_result['sources_validated']),
            len(regex_result['targets_validated']),
            len(sources_validated),
            len(targets_validated)
        )

        return {
            'sources': sources,
            'targets': targets,
            'sources_validated': sources_validated,
            'targets_validated': targets_validated,
            'sources_count': len(sources_validated),
            'targets_count': len(targets_validated),
            'quality_check': quality
        }
