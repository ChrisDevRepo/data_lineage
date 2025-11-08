"""
Unified Confidence Score Calculator

Centralizes ALL confidence score calculations across the application.
Ensures consistency between backend parser, evaluation, and frontend display.

Version History:
- v1.0.0 (2025-11-03): Initial unified calculator
- v2.0.0 (2025-11-06): Multi-factor confidence model with breakdown
- v2.1.0 (2025-11-06): Fixed "Method Agreement" flaw - now measures accuracy not agreement
- v2.1.0 (2025-11-08): Added simplified 4-value confidence model (0, 75, 85, 100)

Author: Claude Code Agent
Date: 2025-11-08
Version: 2.1.0
"""

from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """
    Unified confidence score calculator.

    This class provides a single source of truth for all confidence-related
    calculations to prevent inconsistencies between:
    - Backend parser (quality_aware_parser.py)
    - Evaluation testing (score_calculator.py)
    - Frontend display

    Confidence Levels:
    - HIGH (0.85):   Regex and SQLGlot agree (±10%) OR DMV/Query Log validated
    - MEDIUM (0.75): Partial agreement (±25%)
    - LOW (0.50):    Major difference (>25%) - needs AI review
    """

    # Standard confidence thresholds (DO NOT CHANGE without consensus!)
    CONFIDENCE_HIGH = 0.85
    CONFIDENCE_MEDIUM = 0.75
    CONFIDENCE_LOW = 0.5
    CONFIDENCE_FAIL = 0.0

    # Quality match thresholds
    THRESHOLD_HIGH = 0.90    # ≥90% match → High confidence
    THRESHOLD_MEDIUM = 0.75  # ≥75% match → Medium confidence
    # <75% match → Low confidence

    @classmethod
    def from_quality_match(
        cls,
        source_match: float,
        target_match: float,
        regex_sources_count: int = 0,
        regex_targets_count: int = 0,
        sp_calls_count: int = 0
    ) -> float:
        """
        Calculate confidence from quality match percentages (Parser method).

        Used by quality_aware_parser.py when comparing regex baseline
        to SQLGlot parser results.

        Args:
            source_match: Match percentage for source tables (0.0-1.0)
            target_match: Match percentage for target tables (0.0-1.0)
            regex_sources_count: Number of sources found by regex
            regex_targets_count: Number of targets found by regex
            sp_calls_count: Number of SP calls found (for orchestrator detection)

        Returns:
            Confidence score (0.85/0.75/0.5/0.0)

        Examples:
            >>> from_quality_match(0.95, 0.95)
            0.85  # High - both match well

            >>> from_quality_match(0.80, 0.80)
            0.75  # Medium - partial match

            >>> from_quality_match(0.50, 0.60)
            0.5   # Low - poor match
        """
        # Calculate weighted overall match (targets weighted 60%)
        overall_match = (source_match * 0.4) + (target_match * 0.6)

        # Special case: Orchestrator SPs with only SP calls (no tables)
        # Example: spLoadFactTables calls 7 other SPs but reads/writes no tables
        # Confidence should be HIGH because we successfully captured all SP calls
        if regex_sources_count == 0 and regex_targets_count == 0:
            if sp_calls_count > 0:
                return cls.CONFIDENCE_HIGH  # 0.85

        # Standard threshold-based bucketing
        if overall_match >= cls.THRESHOLD_HIGH:
            return cls.CONFIDENCE_HIGH    # 0.85
        elif overall_match >= cls.THRESHOLD_MEDIUM:
            return cls.CONFIDENCE_MEDIUM  # 0.75
        else:
            return cls.CONFIDENCE_LOW     # 0.5

    @classmethod
    def from_precision_recall(
        cls,
        precision: float,
        recall: float,
        use_bucketing: bool = True
    ) -> float:
        """
        Calculate confidence from precision and recall (Evaluation method).

        Used by evaluation/score_calculator.py when comparing found
        dependencies against expected ground truth.

        Args:
            precision: TP / (TP + FP) - How many found are correct? (0.0-1.0)
            recall: TP / (TP + FN) - How many expected were found? (0.0-1.0)
            use_bucketing: If True, map F1 to standard thresholds (0.85/0.75/0.5)
                          If False, return raw F1 score (0.0-1.0)

        Returns:
            Confidence score (0.85/0.75/0.5 if bucketing, else 0.0-1.0)

        Examples:
            >>> from_precision_recall(1.0, 1.0)
            0.85  # Perfect match → High confidence

            >>> from_precision_recall(0.8, 0.8, use_bucketing=False)
            0.8   # Raw F1 score
        """
        # Calculate F1 score (harmonic mean)
        if precision + recall == 0:
            f1_score = cls.CONFIDENCE_FAIL
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)

        if not use_bucketing:
            return f1_score

        # Map F1 score to standard confidence buckets
        if f1_score >= cls.THRESHOLD_HIGH:
            return cls.CONFIDENCE_HIGH    # 0.85
        elif f1_score >= cls.THRESHOLD_MEDIUM:
            return cls.CONFIDENCE_MEDIUM  # 0.75
        elif f1_score > 0:
            return cls.CONFIDENCE_LOW     # 0.5
        else:
            return cls.CONFIDENCE_FAIL    # 0.0

    @classmethod
    def calculate_stats(
        cls,
        confidence_scores: list[float]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate confidence statistics.

        Used by summary_formatter.py and API status endpoints to provide
        consistent confidence distribution metrics.

        Args:
            confidence_scores: List of confidence scores (floats)

        Returns:
            {
                'total_count': int,
                'high_confidence_count': int,    # ≥0.85
                'medium_confidence_count': int,  # 0.75-0.84
                'low_confidence_count': int,     # <0.75
                'average': float,
                'min': float,
                'max': float
            }
        """
        if not confidence_scores:
            return {
                'total_count': 0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0,
                'average': 0.0,
                'min': 0.0,
                'max': 0.0
            }

        high_count = sum(1 for c in confidence_scores if c >= cls.CONFIDENCE_HIGH)
        medium_count = sum(1 for c in confidence_scores if cls.CONFIDENCE_MEDIUM <= c < cls.CONFIDENCE_HIGH)
        low_count = sum(1 for c in confidence_scores if c < cls.CONFIDENCE_MEDIUM)

        return {
            'total_count': len(confidence_scores),
            'high_confidence_count': high_count,
            'medium_confidence_count': medium_count,
            'low_confidence_count': low_count,
            'average': round(sum(confidence_scores) / len(confidence_scores), 4),
            'min': round(min(confidence_scores), 4),
            'max': round(max(confidence_scores), 4)
        }

    @classmethod
    def get_confidence_label(cls, confidence: float) -> str:
        """
        Get human-readable label for confidence score.

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            'High' | 'Medium' | 'Low' | 'Failed'
        """
        if confidence >= cls.CONFIDENCE_HIGH:
            return 'High'
        elif confidence >= cls.CONFIDENCE_MEDIUM:
            return 'Medium'
        elif confidence > 0:
            return 'Low'
        else:
            return 'Failed'

    @classmethod
    def get_confidence_color(cls, confidence: float) -> str:
        """
        Get color code for confidence visualization.

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            CSS color name or hex code
        """
        if confidence >= cls.CONFIDENCE_HIGH:
            return 'green'
        elif confidence >= cls.CONFIDENCE_MEDIUM:
            return 'yellow'
        elif confidence > 0:
            return 'orange'
        else:
            return 'red'

    # ========================================================================
    # SIMPLIFIED CONFIDENCE MODEL (v2.1.0) - DEFAULT
    # ========================================================================

    @classmethod
    def calculate_simple(
        cls,
        parse_succeeded: bool,
        expected_tables: int,
        found_tables: int,
        is_orchestrator: bool = False,
        parse_failure_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simple 4-value confidence model based on completeness.

        This is a simplified alternative to the multi-factor model.
        Returns confidence in {0, 75, 85, 100} only.

        User Requirement:
        "Simpler, no bonus in calc. Only four different percent values possible."
        "The calculation should not be complicated and not be a black box."

        Logic:
        - Parse failed → 0%
        - Orchestrator (only EXEC, no tables) → 100%
        - Completeness ≥90% → 100%
        - Completeness 70-89% → 85%
        - Completeness 50-69% → 75%
        - Completeness <50% → 0%

        Args:
            parse_succeeded: Whether parsing completed without errors
            expected_tables: Number of tables expected (from smoke test)
            found_tables: Number of tables actually found by parser
            is_orchestrator: Whether SP only calls other SPs (no table access)
            parse_failure_reason: Optional reason for parse failure

        Returns:
            {
                'confidence': 0 | 75 | 85 | 100,
                'breakdown': {
                    'parse_succeeded': bool,
                    'expected_tables': int,
                    'found_tables': int,
                    'completeness_pct': float,
                    'is_orchestrator': bool,
                    'explanation': str,
                    'to_improve': str (optional)
                }
            }

        Examples:
            >>> # Perfect match
            >>> calculate_simple(True, 8, 8)
            {'confidence': 100, 'breakdown': {'completeness_pct': 100.0, ...}}

            >>> # Good match
            >>> calculate_simple(True, 10, 7)
            {'confidence': 85, 'breakdown': {'completeness_pct': 70.0, ...}}

            >>> # Parse failed
            >>> calculate_simple(False, 8, 1, parse_failure_reason="Dynamic SQL")
            {'confidence': 0, 'breakdown': {'parse_succeeded': False, ...}}

            >>> # Orchestrator
            >>> calculate_simple(True, 0, 0, is_orchestrator=True)
            {'confidence': 100, 'breakdown': {'is_orchestrator': True, ...}}
        """
        # Failed parsing
        if not parse_succeeded:
            return {
                'confidence': 0,
                'breakdown': {
                    'parse_succeeded': False,
                    'expected_tables': expected_tables,
                    'found_tables': found_tables,
                    'completeness_pct': 0.0,
                    'is_orchestrator': is_orchestrator,
                    'failure_reason': parse_failure_reason or 'Parse failed',
                    'to_fix': 'Add @LINEAGE_INPUTS/@LINEAGE_OUTPUTS comment hints'
                }
            }

        # Orchestrator special case (only calls other SPs, no table access)
        if is_orchestrator:
            return {
                'confidence': 100,
                'breakdown': {
                    'parse_succeeded': True,
                    'expected_tables': expected_tables,
                    'found_tables': found_tables,
                    'completeness_pct': 100.0,
                    'is_orchestrator': True,
                    'explanation': 'Orchestrator SP (only calls other SPs)'
                }
            }

        # Calculate completeness
        if expected_tables == 0:
            completeness_pct = 100.0
        else:
            completeness_pct = (found_tables / expected_tables) * 100

        # Map to 4 discrete values
        if completeness_pct >= 90:
            confidence = 100
            explanation = f'Found {found_tables}/{expected_tables} tables ({completeness_pct:.0f}%) - Perfect or near-perfect'
            to_improve = None
        elif completeness_pct >= 70:
            confidence = 85
            missing = expected_tables - found_tables
            explanation = f'Found {found_tables}/{expected_tables} tables ({completeness_pct:.0f}%) - Good, most found'
            to_improve = f'Add @LINEAGE hints for {missing} missing table{"s" if missing > 1 else ""}'
        elif completeness_pct >= 50:
            confidence = 75
            missing = expected_tables - found_tables
            explanation = f'Found {found_tables}/{expected_tables} tables ({completeness_pct:.0f}%) - Acceptable, partial'
            to_improve = f'Add @LINEAGE hints for {missing} missing table{"s" if missing > 1 else ""}'
        else:
            confidence = 0
            missing = expected_tables - found_tables
            explanation = f'Found {found_tables}/{expected_tables} tables ({completeness_pct:.0f}%) - Too incomplete'
            to_improve = f'Add @LINEAGE hints for {missing} missing table{"s" if missing > 1 else ""}' if missing > 0 else 'Review parsing logic'

        breakdown = {
            'parse_succeeded': True,
            'expected_tables': expected_tables,
            'found_tables': found_tables,
            'completeness_pct': round(completeness_pct, 1),
            'is_orchestrator': is_orchestrator,
            'explanation': explanation
        }

        if to_improve:
            breakdown['to_improve'] = to_improve

        return {
            'confidence': confidence,
            'breakdown': breakdown
        }
