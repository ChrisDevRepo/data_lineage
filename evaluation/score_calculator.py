"""
Score Calculator for sub_DL_OptimizeParsing

Calculates precision, recall, F1 scores for parsing evaluation.
Compares found dependencies against expected (ground truth) dependencies.

Now uses unified ConfidenceCalculator for consistency with parser.

Author: Claude Code Agent
Date: 2025-11-03
Version: 2.0
"""

import sys
from pathlib import Path
from typing import List, Tuple, Set
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.utils.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)


class ScoreCalculator:
    """
    Calculates evaluation metrics for parsing results.

    Metrics:
    - Precision: TP / (TP + FP) - How many found dependencies are correct?
    - Recall: TP / (TP + FN) - How many expected dependencies were found?
    - F1 Score: Harmonic mean of precision and recall
    - Confidence: Based on F1 score
    """

    @staticmethod
    def calculate_precision_recall(
        found_ids: List[int],
        expected_ids: List[int]
    ) -> Tuple[float, float, float]:
        """
        Calculate precision, recall, and F1 score.

        Args:
            found_ids: List of object_ids found by parser
            expected_ids: List of expected object_ids (ground truth)

        Returns:
            (precision, recall, f1_score) - all floats between 0.0 and 1.0

        Examples:
            >>> calculate_precision_recall([1, 2, 3], [1, 2, 3])
            (1.0, 1.0, 1.0)  # Perfect match

            >>> calculate_precision_recall([1, 2], [1, 2, 3])
            (1.0, 0.667, 0.8)  # Found all correct but missed one

            >>> calculate_precision_recall([1, 2, 4], [1, 2, 3])
            (0.667, 0.667, 0.667)  # Found 2/3, but 1 was wrong
        """
        found_set = set(found_ids)
        expected_set = set(expected_ids)

        # True Positives: Found AND expected
        true_positives = len(found_set & expected_set)

        # False Positives: Found but NOT expected (hallucinations)
        false_positives = len(found_set - expected_set)

        # False Negatives: Expected but NOT found (missed dependencies)
        false_negatives = len(expected_set - found_set)

        # Precision: What percentage of found dependencies are correct?
        if len(found_set) == 0:
            precision = 1.0 if len(expected_set) == 0 else 0.0
        else:
            precision = true_positives / len(found_set)

        # Recall: What percentage of expected dependencies were found?
        if len(expected_set) == 0:
            recall = 1.0 if len(found_set) == 0 else 0.0
        else:
            recall = true_positives / len(expected_set)

        # F1 Score: Harmonic mean of precision and recall
        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)

        return precision, recall, f1_score

    @staticmethod
    def calculate_confidence_score(
        precision: float,
        recall: float,
        use_bucketing: bool = True
    ) -> float:
        """
        Calculate confidence score based on precision and recall.

        Uses unified ConfidenceCalculator for consistency with parser.

        Args:
            precision: Precision value (0.0-1.0)
            recall: Recall value (0.0-1.0)
            use_bucketing: If True, map to standard thresholds (0.85/0.75/0.5)
                          If False, return raw F1 score (0.0-1.0)

        Returns:
            Confidence score (bucketed or raw F1)
        """
        return ConfidenceCalculator.from_precision_recall(
            precision=precision,
            recall=recall,
            use_bucketing=use_bucketing
        )

    @staticmethod
    def determine_best_method(
        regex_conf: float,
        sqlglot_conf: float,
        ai_conf: float
    ) -> Tuple[str, float]:
        """
        Determine which method gave best confidence.

        Args:
            regex_conf: Regex confidence score
            sqlglot_conf: SQLGlot confidence score
            ai_conf: AI confidence score

        Returns:
            (method_name, confidence_score)

        Priority: AI > SQLGlot > Regex (if tied, prefer cheaper method)
        """
        # Find max confidence
        max_conf = max(regex_conf, sqlglot_conf, ai_conf)

        # Prefer cheaper method if tied
        if ai_conf == max_conf and ai_conf > 0:
            return ('ai', ai_conf)
        elif sqlglot_conf == max_conf and sqlglot_conf > 0:
            return ('sqlglot', sqlglot_conf)
        else:
            return ('regex', regex_conf)

    @staticmethod
    def calculate_method_scores(
        found_inputs: List[int],
        found_outputs: List[int],
        expected_inputs: List[int],
        expected_outputs: List[int]
    ) -> dict:
        """
        Calculate comprehensive scores for a single parsing method.

        Args:
            found_inputs: Input object_ids found by method
            found_outputs: Output object_ids found by method
            expected_inputs: Expected input object_ids
            expected_outputs: Expected output object_ids

        Returns:
            {
                'inputs_precision': float,
                'inputs_recall': float,
                'inputs_f1': float,
                'outputs_precision': float,
                'outputs_recall': float,
                'outputs_f1': float,
                'overall_precision': float,  # Weighted average
                'overall_recall': float,     # Weighted average
                'overall_f1': float,         # Weighted average
                'confidence': float          # Overall F1
            }
        """
        # Calculate for inputs
        inputs_precision, inputs_recall, inputs_f1 = ScoreCalculator.calculate_precision_recall(
            found_inputs, expected_inputs
        )

        # Calculate for outputs
        outputs_precision, outputs_recall, outputs_f1 = ScoreCalculator.calculate_precision_recall(
            found_outputs, expected_outputs
        )

        # Weighted average (outputs more important - 60%)
        total_expected = len(expected_inputs) + len(expected_outputs)

        if total_expected == 0:
            overall_precision = 1.0
            overall_recall = 1.0
            overall_f1 = 1.0
        else:
            input_weight = len(expected_inputs) / total_expected if total_expected > 0 else 0.4
            output_weight = len(expected_outputs) / total_expected if total_expected > 0 else 0.6

            overall_precision = (inputs_precision * input_weight) + (outputs_precision * output_weight)
            overall_recall = (inputs_recall * input_weight) + (outputs_recall * output_weight)

            if overall_precision + overall_recall == 0:
                overall_f1 = 0.0
            else:
                overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall)

        # Calculate confidence using unified calculator
        # Use bucketing=False to keep raw F1 for detailed evaluation metrics
        confidence = ConfidenceCalculator.from_precision_recall(
            precision=overall_precision,
            recall=overall_recall,
            use_bucketing=False  # Keep raw F1 for evaluation
        )

        return {
            'inputs_precision': round(inputs_precision, 4),
            'inputs_recall': round(inputs_recall, 4),
            'inputs_f1': round(inputs_f1, 4),
            'outputs_precision': round(outputs_precision, 4),
            'outputs_recall': round(outputs_recall, 4),
            'outputs_f1': round(outputs_f1, 4),
            'overall_precision': round(overall_precision, 4),
            'overall_recall': round(overall_recall, 4),
            'overall_f1': round(overall_f1, 4),
            'confidence': round(confidence, 4)  # Unified confidence calculation
        }
