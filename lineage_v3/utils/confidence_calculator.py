"""
Unified Confidence Score Calculator

Centralizes ALL confidence score calculations across the application.
Ensures consistency between backend parser, evaluation, and frontend display.

Author: Claude Code Agent
Date: 2025-11-03
Version: 1.0.0
"""

from typing import Dict, Any, Tuple
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
