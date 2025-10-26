"""
Dual-Parser with Cross-Validation
==================================

Combines SQLGlot (quality-aware) + SQLLineage for improved accuracy.

Strategy:
1. Regex baseline (expected counts)
2. SQLGlot parse (quality-aware)
3. SQLLineage parse (independent validation)
4. Cross-validate and determine consensus

Author: Vibecoding
Version: 3.3.0
Date: 2025-10-26
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from sqllineage.runner import LineageRunner
import logging

from .quality_aware_parser import QualityAwareParser

logger = logging.getLogger(__name__)


class DualParser(QualityAwareParser):
    """
    Quality-aware parser with SQLLineage cross-validation.

    Strategy:
    1. Regex baseline (expected counts)
    2. SQLGlot parse (quality-aware)
    3. SQLLineage parse (independent validation)
    4. Cross-validate and determine consensus
    """

    def __init__(self, workspace):
        """Initialize dual parser."""
        super().__init__(workspace)
        self.stats = {
            'high_agreement': 0,
            'moderate_agreement': 0,
            'low_agreement_needs_ai': 0,
            'sqlglot_preferred': 0,
            'sqllineage_preferred': 0
        }

    def parse_object(self, object_id: int) -> Dict[str, Any]:
        """
        Parse with dual-parser cross-validation.

        Returns same format as QualityAwareParser but with enhanced confidence
        and additional provenance metadata.
        """
        # Step 1: Get quality-aware SQLGlot result
        sqlglot_result = super().parse_object(object_id)

        # If SQLGlot failed completely, no point in cross-validation
        if sqlglot_result['confidence'] == 0.0:
            return sqlglot_result

        # Step 2: Fetch DDL for SQLLineage
        ddl = self._fetch_ddl(object_id)
        if not ddl:
            return sqlglot_result

        try:
            # Step 3: Parse with SQLLineage
            sqllineage_result = self._sqllineage_parse(ddl)

            # Step 4: Cross-validate and determine consensus
            final_result = self._cross_validate(
                sqlglot_result,
                sqllineage_result,
                object_id
            )

            return final_result

        except Exception as e:
            logger.warning(f"SQLLineage parse failed for object_id {object_id}: {e}")
            # Fallback to SQLGlot result
            return sqlglot_result

    def _sqllineage_parse(self, ddl: str) -> Dict[str, Any]:
        """
        Parse using SQLLineage.

        Returns:
            {
                'sources': Set[str],  # schema.table format
                'targets': Set[str],
                'method': 'sqllineage'
            }
        """
        # Preprocess DDL (remove control flow that breaks parsers)
        cleaned_ddl = self._preprocess_ddl(ddl)

        # Run SQLLineage parser
        runner = LineageRunner(cleaned_ddl, dialect='tsql')

        sources = set()
        targets = set()

        # Extract source tables
        for table in runner.source_tables:
            # SQLLineage returns Table objects with schema and name
            table_str = str(table)  # Format: schema.table or just table

            # Normalize to schema.table format
            if '.' not in table_str:
                table_str = f"dbo.{table_str}"  # Default schema

            sources.add(table_str)

        # Extract target tables
        for table in runner.target_tables:
            table_str = str(table)

            if '.' not in table_str:
                table_str = f"dbo.{table_str}"

            targets.add(table_str)

        return {
            'sources': sources,
            'targets': targets,
            'method': 'sqllineage'
        }

    def _cross_validate(
        self,
        sqlglot_result: Dict[str, Any],
        sqllineage_result: Dict[str, Any],
        object_id: int
    ) -> Dict[str, Any]:
        """
        Compare both parser results and determine consensus.

        Returns enhanced result with dual-parser provenance.
        """
        # Convert SQLGlot object_ids back to table names for comparison
        sqlglot_sources = self._resolve_ids_to_names(sqlglot_result['inputs'])
        sqlglot_targets = self._resolve_ids_to_names(sqlglot_result['outputs'])

        # Validate SQLLineage results against catalog
        lineage_sources = self._validate_against_catalog(sqllineage_result['sources'])
        lineage_targets = self._validate_against_catalog(sqllineage_result['targets'])

        # Calculate agreement metrics
        agreement = self._calculate_agreement(
            sqlglot_sources, sqlglot_targets,
            lineage_sources, lineage_targets
        )

        # Determine which parser to trust
        final_sources, final_targets, confidence, decision = self._determine_consensus(
            sqlglot_sources, sqlglot_targets,
            lineage_sources, lineage_targets,
            sqlglot_result.get('quality_check', {}),
            agreement
        )

        # Update statistics
        self._update_stats(decision)

        # Resolve final table names to object_ids
        final_input_ids = self._resolve_table_names(final_sources)
        final_output_ids = self._resolve_table_names(final_targets)

        result = {
            'object_id': object_id,
            'inputs': final_input_ids,
            'outputs': final_output_ids,
            'confidence': confidence,
            'source': 'dual_parser',
            'parse_error': None,
            'dual_parser_metrics': {
                'sqlglot_sources': len(sqlglot_sources),
                'sqlglot_targets': len(sqlglot_targets),
                'sqllineage_sources': len(lineage_sources),
                'sqllineage_targets': len(lineage_targets),
                'source_agreement': agreement['source_agreement'],
                'target_agreement': agreement['target_agreement'],
                'overall_agreement': agreement['overall_agreement'],
                'decision': decision
            },
            'quality_check': sqlglot_result.get('quality_check')
        }

        # Log to comparison table
        self._log_parser_comparison(object_id, sqlglot_result, sqllineage_result, agreement, decision, result)

        return result

    def _calculate_agreement(
        self,
        sqlglot_sources: Set[str],
        sqlglot_targets: Set[str],
        lineage_sources: Set[str],
        lineage_targets: Set[str]
    ) -> Dict[str, float]:
        """Calculate agreement percentage between two parsers."""

        # Source agreement (Jaccard similarity)
        if len(sqlglot_sources) == 0 and len(lineage_sources) == 0:
            source_agreement = 1.0  # Both found nothing - perfect agreement
        elif len(sqlglot_sources) == 0 or len(lineage_sources) == 0:
            source_agreement = 0.0  # One found something, other didn't
        else:
            intersection = len(sqlglot_sources & lineage_sources)
            union = len(sqlglot_sources | lineage_sources)
            source_agreement = intersection / union if union > 0 else 0.0

        # Target agreement
        if len(sqlglot_targets) == 0 and len(lineage_targets) == 0:
            target_agreement = 1.0
        elif len(sqlglot_targets) == 0 or len(lineage_targets) == 0:
            target_agreement = 0.0
        else:
            intersection = len(sqlglot_targets & lineage_targets)
            union = len(sqlglot_targets | lineage_targets)
            target_agreement = intersection / union if union > 0 else 0.0

        # Overall agreement (weighted - targets more important)
        overall = (source_agreement * 0.4) + (target_agreement * 0.6)

        return {
            'source_agreement': source_agreement,
            'target_agreement': target_agreement,
            'overall_agreement': overall
        }

    def _determine_consensus(
        self,
        sqlglot_sources: Set[str],
        sqlglot_targets: Set[str],
        lineage_sources: Set[str],
        lineage_targets: Set[str],
        quality_check: Dict[str, Any],
        agreement: Dict[str, float]
    ) -> Tuple[Set[str], Set[str], float, str]:
        """
        Determine final result based on consensus logic between two parsers.

        **Strategy:**
        Uses Jaccard similarity (intersection / union) to measure parser agreement.
        When parsers disagree, uses regex baseline quality to pick the better result.

        **Scenarios:**
        1. High agreement (≥90%): Both parsers found same tables → Confidence 0.95
        2. Moderate agreement (≥70%): Mostly agree → Confidence 0.85
        3. Low agreement (<70%): Pick parser with better regex match → Confidence 0.50-0.85
        4. Both poor quality: Use union, flag for AI → Confidence 0.50

        Args:
            sqlglot_sources: Tables found by SQLGlot (FROM/JOIN)
            sqlglot_targets: Tables found by SQLGlot (INSERT/UPDATE/MERGE)
            lineage_sources: Tables found by SQLLineage (FROM/JOIN)
            lineage_targets: Tables found by SQLLineage (INSERT/UPDATE/MERGE)
            quality_check: SQLGlot quality metrics vs regex baseline
            agreement: Jaccard similarity scores between parsers

        Returns:
            Tuple of (final_sources, final_targets, confidence, decision)
            - final_sources: Set of source table names (schema.table)
            - final_targets: Set of target table names (schema.table)
            - confidence: 0.5-0.95 based on agreement level
            - decision: 'high_agreement' | 'moderate_agreement' | 'sqlglot_preferred' |
                       'sqllineage_preferred' | 'low_agreement_needs_ai'
        """
        overall_agreement = agreement['overall_agreement']

        # Scenario 1: High agreement (≥90%) - Both parsers found nearly identical tables
        if overall_agreement >= 0.90:
            # Both parsers agree - use union to capture everything
            # Example: SQLGlot=[A,B], SQLLineage=[A,B,C] → Union=[A,B,C]
            final_sources = sqlglot_sources | lineage_sources
            final_targets = sqlglot_targets | lineage_targets
            confidence = 0.95  # Highest confidence - dual validation
            decision = 'high_agreement'

        # Scenario 2: Moderate agreement (≥70%) - Parsers mostly agree
        elif overall_agreement >= 0.70:
            # Parsers mostly agree - use union but slightly less confident
            # Example: SQLGlot=[A,B,C], SQLLineage=[A,B,D] → Union=[A,B,C,D] (66% match)
            final_sources = sqlglot_sources | lineage_sources
            final_targets = sqlglot_targets | lineage_targets
            confidence = 0.85
            decision = 'moderate_agreement'

        # Scenario 3: Low agreement (<70%) - Need to pick the better parser
        else:
            # Use regex baseline quality to decide which parser to trust
            sqlglot_quality = quality_check.get('overall_match', 0.0)

            # Calculate SQLLineage quality (compare to regex baseline)
            regex_sources = quality_check.get('regex_sources', 0)
            regex_targets = quality_check.get('regex_targets', 0)

            lineage_quality = self._calculate_lineage_quality(
                lineage_sources, lineage_targets,
                regex_sources, regex_targets
            )

            # Pick parser with better regex match
            if lineage_quality > sqlglot_quality:
                # SQLLineage matched regex baseline better
                final_sources = lineage_sources
                final_targets = lineage_targets
                confidence = 0.75
                decision = 'sqllineage_preferred'
            else:
                # SQLGlot matched regex baseline better (or tied)
                final_sources = sqlglot_sources
                final_targets = sqlglot_targets
                # Use SQLGlot's quality-based confidence (0.5-0.85)
                confidence = self._determine_confidence(quality_check)
                decision = 'sqlglot_preferred'

            # Scenario 4: Both parsers have poor quality (<75% match to regex)
            # This indicates complex SQL that neither parser handled well
            if sqlglot_quality < 0.75 and lineage_quality < 0.75:
                # Use union to capture everything, let AI validate in Phase 5
                # Example: Complex dynamic SQL, nested CTEs, etc.
                final_sources = sqlglot_sources | lineage_sources
                final_targets = sqlglot_targets | lineage_targets
                confidence = 0.5  # Low confidence - AI review required
                decision = 'low_agreement_needs_ai'

        return final_sources, final_targets, confidence, decision

    def _calculate_lineage_quality(
        self,
        lineage_sources: Set[str],
        lineage_targets: Set[str],
        regex_sources: int,
        regex_targets: int
    ) -> float:
        """Calculate SQLLineage quality vs regex baseline."""

        # Match percentages
        if regex_sources > 0:
            source_match = min(len(lineage_sources) / regex_sources, 1.0)
        else:
            source_match = 1.0 if len(lineage_sources) == 0 else 0.0

        if regex_targets > 0:
            target_match = min(len(lineage_targets) / regex_targets, 1.0)
        else:
            target_match = 1.0 if len(lineage_targets) == 0 else 0.0

        # Overall match (weighted - targets more important)
        overall_match = (source_match * 0.4) + (target_match * 0.6)

        return overall_match

    def _resolve_ids_to_names(self, object_ids: List[int]) -> Set[str]:
        """Convert object_ids back to schema.table names."""
        if not object_ids:
            return set()

        names = set()

        for obj_id in object_ids:
            query = f"""
            SELECT schema_name || '.' || object_name
            FROM objects
            WHERE object_id = {obj_id}
            """

            results = self.workspace.query(query)
            if results:
                names.add(results[0][0])

        return names

    def _update_stats(self, decision: str):
        """Update parser statistics."""
        if decision in self.stats:
            self.stats[decision] += 1

    def _log_parser_comparison(
        self,
        object_id: int,
        sqlglot_result: Dict[str, Any],
        sqllineage_result: Dict[str, Any],
        agreement: Dict[str, float],
        decision: str,
        final_result: Dict[str, Any]
    ):
        """Log parser comparison to DuckDB table for later analysis."""

        # Get object metadata
        query = f"""
        SELECT schema_name, object_name, object_type
        FROM objects
        WHERE object_id = {object_id}
        """
        obj_info = self.workspace.query(query)
        if not obj_info:
            return

        schema_name, object_name, object_type = obj_info[0]

        # Extract quality check metrics
        qc = sqlglot_result.get('quality_check', {})

        # Build insert query with proper escaping
        # Escape single quotes in string values
        object_name_escaped = object_name.replace("'", "''")
        schema_name_escaped = schema_name.replace("'", "''")
        object_type_escaped = object_type.replace("'", "''")
        decision_escaped = decision.replace("'", "''")

        insert_query = f"""
        INSERT INTO parser_comparison_log (
            object_id,
            object_name,
            schema_name,
            object_type,
            regex_sources_expected,
            regex_targets_expected,
            sqlglot_sources_found,
            sqlglot_targets_found,
            sqlglot_confidence,
            sqlglot_quality_match,
            sqllineage_sources_found,
            sqllineage_targets_found,
            sqllineage_quality_match,
            dual_parser_agreement,
            dual_parser_decision,
            final_sources_count,
            final_targets_count,
            final_confidence,
            final_source,
            ai_used
        ) VALUES (
            {object_id},
            '{object_name_escaped}',
            '{schema_name_escaped}',
            '{object_type_escaped}',
            {qc.get('regex_sources', 0)},
            {qc.get('regex_targets', 0)},
            {qc.get('parser_sources', 0)},
            {qc.get('parser_targets', 0)},
            {sqlglot_result.get('confidence', 0.0)},
            {qc.get('overall_match', 0.0)},
            {len(sqllineage_result.get('sources', []))},
            {len(sqllineage_result.get('targets', []))},
            NULL,  -- Will calculate in next version
            {agreement.get('overall_agreement', 0.0)},
            '{decision_escaped}',
            {len(final_result.get('inputs', []))},
            {len(final_result.get('outputs', []))},
            {final_result.get('confidence', 0.0)},
            'dual_parser',
            FALSE
        )
        """

        try:
            self.workspace.connection.execute(insert_query)
        except Exception as e:
            logger.error(f"Failed to log parser comparison for object_id {object_id} ({schema_name}.{object_name}): {e}")
            logger.error(f"SQL Query: {insert_query[:500]}...")  # Log first 500 chars for debugging

    def get_parse_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics including dual-parser metrics."""
        base_stats = super().get_parse_statistics()

        base_stats['dual_parser_stats'] = {
            'high_agreement': self.stats['high_agreement'],
            'moderate_agreement': self.stats['moderate_agreement'],
            'low_agreement_needs_ai': self.stats['low_agreement_needs_ai'],
            'sqlglot_preferred': self.stats['sqlglot_preferred'],
            'sqllineage_preferred': self.stats['sqllineage_preferred']
        }

        return base_stats
