#!/usr/bin/env python3
"""
Confidence Scorer

Combines results from regex parsing and AI analysis to produce a unified dependency list
with weighted confidence scores.
"""

from typing import List, Dict, Set
from parsers.sql_parser_enhanced import Dependency, ConfidenceLevel
from collections import defaultdict


class ConfidenceScorer:
    """Combines and scores dependencies from multiple detection methods."""

    # Weights for different detection methods
    METHOD_WEIGHTS = {
        'regex_from_join': 0.9,
        'regex_insert': 0.95,
        'regex_select_into': 0.9,
        'regex_update': 0.9,
        'regex_merge_target': 0.7,
        'regex_merge_source': 0.7,
        'regex_truncate': 0.95,
        'regex_exec': 0.9,
        'regex_from_join_temp_resolved': 0.85,
        'ai_merge_target': 0.85,
        'ai_merge_source': 0.85,
        'ai_merge_when_clause': 0.75,
        'ai_dynamic_sql_heuristic': 0.4,
        'ai_nested_cte': 0.8,
        'ai_pivot_source': 0.8,
        'grep_search': 0.6,
        'glob_file_found': 0.95,
    }

    def __init__(self):
        pass

    def merge_dependencies(
        self,
        regex_deps: List[Dependency],
        ai_deps: List[Dependency],
        search_deps: List[Dependency] = None
    ) -> List[Dependency]:
        """
        Merge dependencies from multiple sources, combining confidence scores.

        Args:
            regex_deps: Dependencies from regex parsing
            ai_deps: Dependencies from AI analysis
            search_deps: Dependencies from iterative search (optional)

        Returns:
            Merged list with combined confidence scores
        """
        # Group dependencies by (schema, object_name) key
        dep_groups: Dict[str, List[Dependency]] = defaultdict(list)

        all_deps = regex_deps + ai_deps
        if search_deps:
            all_deps += search_deps

        for dep in all_deps:
            key = f"{dep.schema}.{dep.object_name}"
            dep_groups[key].append(dep)

        # Merge each group
        merged = []
        for key, deps in dep_groups.items():
            merged_dep = self._merge_dependency_group(deps)
            merged.append(merged_dep)

        return merged

    def _merge_dependency_group(self, deps: List[Dependency]) -> Dependency:
        """
        Merge multiple detections of the same dependency.

        Uses weighted average of confidence scores, with higher weights for more reliable
        detection methods.
        """
        if len(deps) == 1:
            return deps[0]

        # Collect weighted scores
        weighted_scores = []
        detection_methods = []
        all_snippets = []
        needs_ai = False

        for dep in deps:
            weight = self.METHOD_WEIGHTS.get(dep.detection_method, 0.5)
            weighted_scores.append(dep.confidence * weight)
            detection_methods.append(dep.detection_method)

            if dep.sql_snippet:
                all_snippets.append(dep.sql_snippet)

            if dep.needs_ai_review:
                needs_ai = True

        # Calculate weighted average confidence
        if weighted_scores:
            avg_confidence = sum(weighted_scores) / len(weighted_scores)
        else:
            avg_confidence = 0.5

        # Boost confidence if detected by multiple methods
        if len(deps) >= 2:
            avg_confidence = min(avg_confidence * 1.1, 1.0)

        if len(deps) >= 3:
            avg_confidence = min(avg_confidence * 1.15, 1.0)

        # Use first dependency as template
        base_dep = deps[0]

        # Create merged dependency
        merged = Dependency(
            object_name=base_dep.object_name,
            schema=base_dep.schema,
            object_type=base_dep.object_type,
            confidence=avg_confidence,
            source_line=base_dep.source_line,
            sql_snippet="; ".join(set(all_snippets)) if all_snippets else None,
            needs_ai_review=needs_ai,
            detection_method=f"merged({','.join(set(detection_methods))})"
        )

        return merged

    def filter_low_confidence(
        self,
        dependencies: List[Dependency],
        min_confidence: float = 0.3
    ) -> tuple[List[Dependency], List[Dependency]]:
        """
        Filter dependencies by confidence threshold.

        Args:
            dependencies: List of dependencies to filter
            min_confidence: Minimum confidence threshold

        Returns:
            Tuple of (high_confidence_deps, low_confidence_deps)
        """
        high_confidence = []
        low_confidence = []

        for dep in dependencies:
            if dep.confidence >= min_confidence:
                high_confidence.append(dep)
            else:
                low_confidence.append(dep)

        return high_confidence, low_confidence

    def rank_dependencies(self, dependencies: List[Dependency]) -> List[Dependency]:
        """
        Rank dependencies by confidence score (highest first).

        Args:
            dependencies: List of dependencies to rank

        Returns:
            Sorted list of dependencies
        """
        return sorted(dependencies, key=lambda d: d.confidence, reverse=True)

    def calculate_overall_confidence(self, dependencies: List[Dependency]) -> float:
        """
        Calculate overall confidence for a set of dependencies.

        Args:
            dependencies: List of dependencies

        Returns:
            Overall confidence score (0.0-1.0)
        """
        if not dependencies:
            return 1.0  # No dependencies = high confidence

        # Weight by detection method
        weighted_sum = 0.0
        weight_total = 0.0

        for dep in dependencies:
            method_weight = self.METHOD_WEIGHTS.get(dep.detection_method, 0.5)
            weighted_sum += dep.confidence * method_weight
            weight_total += method_weight

        if weight_total > 0:
            return weighted_sum / weight_total
        else:
            return 0.5

    def identify_uncertain_dependencies(
        self,
        dependencies: List[Dependency],
        uncertainty_threshold: float = 0.6
    ) -> List[Dependency]:
        """
        Identify dependencies that need manual review.

        Args:
            dependencies: List of dependencies
            uncertainty_threshold: Threshold below which dependencies are uncertain

        Returns:
            List of uncertain dependencies
        """
        uncertain = []

        for dep in dependencies:
            if dep.confidence < uncertainty_threshold or dep.needs_ai_review:
                uncertain.append(dep)

        return uncertain
