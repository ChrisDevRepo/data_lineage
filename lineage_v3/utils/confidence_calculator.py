"""
Unified Confidence Score Calculator

Centralizes ALL confidence score calculations across the application.
Ensures consistency between backend parser, evaluation, and frontend display.

Version History:
- v1.0.0 (2025-11-03): Initial unified calculator
- v2.0.0 (2025-11-06): Multi-factor confidence model with breakdown
- v2.1.0 (2025-11-06): Fixed "Method Agreement" flaw - now measures accuracy not agreement

Author: Claude Code Agent
Date: 2025-11-06
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
    # MULTI-FACTOR CONFIDENCE MODEL (v2.1.0)
    # ========================================================================

    # Factor weights (must sum to 1.0)
    WEIGHT_PARSE_SUCCESS = 0.30    # 30% - Did parsing complete without errors?
    WEIGHT_PARSE_QUALITY = 0.25    # 25% - Quality of parsing results (accuracy proxy)
    WEIGHT_CATALOG_VALID = 0.20    # 20% - Do extracted objects exist in catalog?
    WEIGHT_COMMENT_HINTS = 0.10    # 10% - Did developer provide hints?
    WEIGHT_UAT_VALIDATED = 0.15    # 15% - Has user verified this SP?

    @classmethod
    def calculate_parse_quality(
        cls,
        source_match: float,
        target_match: float,
        catalog_validation_rate: float
    ) -> float:
        """
        Calculate parse quality score (0.0-1.0).

        IMPORTANT: This measures quality/accuracy, NOT just agreement!

        Strategy (v2.1.0 - Fixed confidence model):
        1. Trust catalog validation as proxy for accuracy
           - If 90%+ of extracted tables exist in catalog → high quality
        2. Use SQLGlot agreement as confidence booster (not penalty!)
           - If regex and SQLGlot agree → additional validation
        3. Be conservative only when BOTH catalog AND agreement are low
           - Indicates potential parsing issues

        Args:
            source_match: Match percentage for source tables (0.0-1.0)
                         How many sources do regex and SQLGlot both find?
            target_match: Match percentage for target tables (0.0-1.0)
                         How many targets do regex and SQLGlot both find?
            catalog_validation_rate: % of extracted objects found in catalog (0.0-1.0)
                                    Proxy for accuracy (real tables = likely correct)

        Returns:
            Quality score (0.0-1.0)

        Examples:
            >>> # Regex perfect, SQLGlot fails, but catalog confirms
            >>> calculate_parse_quality(0.0, 0.0, 1.0)
            1.0  # High quality - catalog validates accuracy

            >>> # Both methods agree, catalog confirms
            >>> calculate_parse_quality(0.95, 0.95, 1.0)
            1.0  # High quality - double validation

            >>> # Disagreement with low catalog validation
            >>> calculate_parse_quality(0.50, 0.60, 0.60)
            0.42  # Low quality - uncertain results
        """
        # Strategy 1: If catalog validation is high (90%+), trust the results
        # This indicates low false positive rate - extracted tables are real
        # Even if SQLGlot failed, regex is likely correct
        if catalog_validation_rate >= 0.90:
            return catalog_validation_rate  # 0.90-1.0

        # Strategy 2: If SQLGlot agrees with regex, boost confidence
        # Agreement provides additional validation beyond catalog
        if source_match >= 0.80 and target_match >= 0.80:
            agreement = (source_match * 0.4) + (target_match * 0.6)
            # Weighted blend: 60% catalog + 40% agreement
            # This rewards double-validation while still trusting catalog more
            return min(1.0, catalog_validation_rate * 0.6 + agreement * 0.4)

        # Strategy 3: If disagreement AND low catalog validation, be conservative
        # This indicates potential parsing issues or uncertain results
        return catalog_validation_rate * 0.7

    @classmethod
    def calculate_multifactor(
        cls,
        parse_success: bool,
        source_match: float,
        target_match: float,
        catalog_validation_rate: float,
        has_comment_hints: bool = False,
        uat_validated: bool = False,
        regex_sources_count: int = 0,
        regex_targets_count: int = 0,
        sp_calls_count: int = 0
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate confidence using multi-factor model with detailed breakdown.

        This is the NEW recommended method for confidence calculation (v2.0.0).
        Provides both final score and breakdown for transparency.

        Args:
            parse_success: Whether parsing completed without errors
            source_match: Match percentage for source tables (0.0-1.0)
            target_match: Match percentage for target tables (0.0-1.0)
            catalog_validation_rate: % of extracted objects found in catalog (0.0-1.0)
            has_comment_hints: Whether developer provided comment hints
            uat_validated: Whether user has verified this SP
            regex_sources_count: Number of sources found by regex
            regex_targets_count: Number of targets found by regex
            sp_calls_count: Number of SP calls found

        Returns:
            Tuple of (final_confidence, breakdown_dict)

            breakdown_dict = {
                'parse_success': {'score': 0-1, 'weight': 0.30, 'contribution': 0-0.30},
                'parse_quality': {'score': 0-1, 'weight': 0.25, 'contribution': 0-0.25},
                'catalog_validation': {'score': 0-1, 'weight': 0.20, 'contribution': 0-0.20},
                'comment_hints': {'score': 0-1, 'weight': 0.10, 'contribution': 0-0.10},
                'uat_validation': {'score': 0-1, 'weight': 0.15, 'contribution': 0-0.15},
                'total_score': 0.0-1.0,
                'bucketed_confidence': 0.85/0.75/0.50,
                'label': 'High'|'Medium'|'Low',
                'color': 'green'|'yellow'|'orange'
            }

        Example:
            >>> confidence, breakdown = calculate_multifactor(
            ...     parse_success=True,
            ...     source_match=0.95,
            ...     target_match=0.95,
            ...     catalog_validation_rate=1.0,
            ...     has_comment_hints=True,
            ...     uat_validated=False
            ... )
            >>> confidence
            0.85
            >>> breakdown['parse_success']['contribution']
            0.30
        """
        # Factor 1: Parse Success (30%)
        parse_score = 1.0 if parse_success else 0.0

        # Factor 2: Parse Quality (25%) - v2.1.0 FIX
        # OLD: Simple agreement (penalized when SQLGlot failed)
        # NEW: Quality score (trusts catalog validation, uses agreement as bonus)
        quality_score = cls.calculate_parse_quality(
            source_match,
            target_match,
            catalog_validation_rate
        )

        # Factor 3: Catalog Validation (20%)
        catalog_score = catalog_validation_rate

        # Factor 4: Comment Hints (10%)
        hints_score = 1.0 if has_comment_hints else 0.0

        # Factor 5: UAT Validation (15%)
        uat_score = 1.0 if uat_validated else 0.0

        # Calculate weighted contributions
        parse_contribution = parse_score * cls.WEIGHT_PARSE_SUCCESS
        quality_contribution = quality_score * cls.WEIGHT_PARSE_QUALITY
        catalog_contribution = catalog_score * cls.WEIGHT_CATALOG_VALID
        hints_contribution = hints_score * cls.WEIGHT_COMMENT_HINTS
        uat_contribution = uat_score * cls.WEIGHT_UAT_VALIDATED

        # Total raw score (0.0-1.0)
        total_score = (
            parse_contribution +
            quality_contribution +
            catalog_contribution +
            hints_contribution +
            uat_contribution
        )

        # Special case: Orchestrator SPs (only SP calls, no tables)
        if regex_sources_count == 0 and regex_targets_count == 0 and sp_calls_count > 0:
            # Orchestrator SPs should get high confidence if parsing succeeded
            if parse_success:
                total_score = max(total_score, 0.85)

        # Bucket into standard confidence levels
        if total_score >= 0.80:  # Slightly lower threshold for multi-factor
            bucketed_confidence = cls.CONFIDENCE_HIGH  # 0.85
        elif total_score >= 0.65:
            bucketed_confidence = cls.CONFIDENCE_MEDIUM  # 0.75
        elif total_score > 0:
            bucketed_confidence = cls.CONFIDENCE_LOW  # 0.50
        else:
            bucketed_confidence = cls.CONFIDENCE_FAIL  # 0.0

        # Build detailed breakdown
        breakdown = {
            'parse_success': {
                'score': parse_score,
                'weight': cls.WEIGHT_PARSE_SUCCESS,
                'contribution': round(parse_contribution, 4)
            },
            'parse_quality': {
                'score': round(quality_score, 4),
                'weight': cls.WEIGHT_PARSE_QUALITY,
                'contribution': round(quality_contribution, 4)
            },
            'catalog_validation': {
                'score': round(catalog_score, 4),
                'weight': cls.WEIGHT_CATALOG_VALID,
                'contribution': round(catalog_contribution, 4)
            },
            'comment_hints': {
                'score': hints_score,
                'weight': cls.WEIGHT_COMMENT_HINTS,
                'contribution': round(hints_contribution, 4)
            },
            'uat_validation': {
                'score': uat_score,
                'weight': cls.WEIGHT_UAT_VALIDATED,
                'contribution': round(uat_contribution, 4)
            },
            'total_score': round(total_score, 4),
            'bucketed_confidence': bucketed_confidence,
            'label': cls.get_confidence_label(bucketed_confidence),
            'color': cls.get_confidence_color(bucketed_confidence)
        }

        return bucketed_confidence, breakdown

    @classmethod
    def calculate_catalog_validation_rate(
        cls,
        extracted_objects: set,
        catalog_objects: set
    ) -> float:
        """
        Calculate what percentage of extracted objects exist in catalog.

        Args:
            extracted_objects: Set of table names extracted by parser
            catalog_objects: Set of table names in database catalog

        Returns:
            Validation rate (0.0-1.0)

        Example:
            >>> extracted = {'dbo.Table1', 'dbo.Table2', 'dbo.InvalidTable'}
            >>> catalog = {'dbo.Table1', 'dbo.Table2', 'dbo.Table3'}
            >>> calculate_catalog_validation_rate(extracted, catalog)
            0.6667  # 2 out of 3 extracted objects exist
        """
        if not extracted_objects:
            return 1.0  # No objects to validate = 100% valid

        valid_count = len(extracted_objects & catalog_objects)
        total_count = len(extracted_objects)

        return valid_count / total_count if total_count > 0 else 1.0
