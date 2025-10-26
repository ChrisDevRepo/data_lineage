#!/usr/bin/env python3
"""
SQL Complexity Detector

Analyzes SQL code to determine if AI assistance is needed for accurate dependency extraction.
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ComplexityReport:
    """Report on SQL complexity analysis."""
    complexity_score: float  # 0.0 (simple) to 1.0 (very complex)
    complex_features: List[str]
    needs_ai_assistance: bool
    reasoning: str


class SQLComplexityDetector:
    """Detects complex SQL patterns that may require AI analysis."""

    # Complexity indicators with weights
    COMPLEXITY_INDICATORS = {
        'nested_cte': (0.3, r'WITH\s+\w+\s+AS\s*\([^)]*WITH\s+\w+\s+AS'),
        'dynamic_sql': (0.4, r'EXEC\s*\(\s*@|EXECUTE\s*\(\s*@|sp_executesql'),
        'sql_in_variables': (0.4, r'@\w+\s*=\s*N?[\'"]\s*(?:SELECT|INSERT|UPDATE|DELETE)'),
        'merge_statement': (0.25, r'MERGE\s+INTO'),
        'pivot_unpivot': (0.3, r'PIVOT|UNPIVOT'),
        'openquery': (0.35, r'OPENQUERY|OPENROWSET'),
        'for_xml_json': (0.2, r'FOR\s+XML|FOR\s+JSON'),
        'deep_nesting': (0.25, None),  # Checked separately
        'complex_joins': (0.2, None),  # Checked separately
        'cursor_usage': (0.3, r'DECLARE\s+\w+\s+CURSOR'),
        'table_variables': (0.15, r'DECLARE\s+@\w+\s+TABLE'),
        'cross_apply': (0.2, r'CROSS\s+APPLY|OUTER\s+APPLY'),
        'recursive_cte': (0.35, r'WITH\s+\w+\s+AS\s*\([^)]*\bUNION\s+ALL\b[^)]*\bFROM\s+\w+\b'),
    }

    # Threshold for requiring AI assistance
    AI_ASSISTANCE_THRESHOLD = 0.5

    def __init__(self):
        pass

    def count_parentheses_depth(self, sql: str) -> int:
        """Calculate maximum nesting depth of parentheses."""
        max_depth = 0
        current_depth = 0

        for char in sql:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth = max(current_depth - 1, 0)

        return max_depth

    def count_joins(self, sql: str) -> int:
        """Count the number of JOIN clauses."""
        joins = re.findall(r'\b(?:INNER|LEFT|RIGHT|FULL|CROSS)\s+(?:OUTER\s+)?JOIN\b|\bJOIN\b',
                          sql, re.IGNORECASE)
        return len(joins)

    def count_subqueries(self, sql: str) -> int:
        """Estimate number of subqueries."""
        # Look for SELECT within parentheses
        subqueries = re.findall(r'\(\s*SELECT\b', sql, re.IGNORECASE)
        return len(subqueries)

    def has_dynamic_table_names(self, sql: str) -> bool:
        """Check if table names are constructed dynamically."""
        # Look for table names concatenated with variables
        patterns = [
            r'FROM\s+@\w+',
            r'JOIN\s+@\w+',
            r'INTO\s+@\w+',
            r'FROM\s+\+',  # String concatenation in table names
            r'[\'"]\s*\+\s*@\w+\s*\+.*?(?:FROM|JOIN|INTO)',
        ]

        for pattern in patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True

        return False

    def analyze_complexity(self, sql_content: str, object_name: str = "") -> ComplexityReport:
        """
        Analyze SQL complexity and determine if AI assistance is needed.

        Args:
            sql_content: The SQL code to analyze
            object_name: Optional name of the SQL object for context

        Returns:
            ComplexityReport with analysis results
        """
        complexity_score = 0.0
        found_features = []
        reasoning_parts = []

        # Check each complexity indicator
        for feature_name, (weight, pattern) in self.COMPLEXITY_INDICATORS.items():
            if pattern is None:
                # Special handling for features without regex patterns
                if feature_name == 'deep_nesting':
                    depth = self.count_parentheses_depth(sql_content)
                    if depth > 5:
                        complexity_score += weight * min(depth / 10, 1.0)
                        found_features.append(f"{feature_name} (depth={depth})")
                        reasoning_parts.append(f"Deep nesting detected (depth {depth})")

                elif feature_name == 'complex_joins':
                    join_count = self.count_joins(sql_content)
                    if join_count > 4:
                        complexity_score += weight * min(join_count / 10, 1.0)
                        found_features.append(f"{feature_name} (count={join_count})")
                        reasoning_parts.append(f"Multiple joins detected ({join_count})")
            else:
                # Regex-based detection
                if re.search(pattern, sql_content, re.IGNORECASE | re.DOTALL):
                    complexity_score += weight
                    found_features.append(feature_name)
                    reasoning_parts.append(f"Found {feature_name.replace('_', ' ')}")

        # Check for dynamic table names (high risk for missing dependencies)
        if self.has_dynamic_table_names(sql_content):
            complexity_score += 0.4
            found_features.append('dynamic_table_names')
            reasoning_parts.append("Dynamic table name construction detected")

        # Count subqueries
        subquery_count = self.count_subqueries(sql_content)
        if subquery_count > 3:
            complexity_score += 0.15
            found_features.append(f"multiple_subqueries (count={subquery_count})")
            reasoning_parts.append(f"Multiple subqueries ({subquery_count})")

        # Cap complexity score at 1.0
        complexity_score = min(complexity_score, 1.0)

        # Determine if AI assistance is needed
        needs_ai = complexity_score >= self.AI_ASSISTANCE_THRESHOLD

        # Build reasoning
        if needs_ai:
            reasoning = f"Complexity score {complexity_score:.2f} exceeds threshold {self.AI_ASSISTANCE_THRESHOLD}. " + \
                       " ".join(reasoning_parts)
        else:
            reasoning = f"Complexity score {complexity_score:.2f} is acceptable for regex parsing."

        return ComplexityReport(
            complexity_score=complexity_score,
            complex_features=found_features,
            needs_ai_assistance=needs_ai,
            reasoning=reasoning
        )

    def extract_complex_snippets(self, sql_content: str, max_snippet_length: int = 500) -> List[Tuple[str, str]]:
        """
        Extract snippets of complex SQL that should be analyzed by AI.

        Returns:
            List of tuples (feature_type, sql_snippet)
        """
        snippets = []

        # Extract MERGE statements
        for match in re.finditer(r'(MERGE\s+INTO.{0,500})', sql_content, re.IGNORECASE | re.DOTALL):
            snippet = match.group(1)[:max_snippet_length]
            snippets.append(('MERGE', snippet))

        # Extract dynamic SQL
        for match in re.finditer(r'((?:EXEC|EXECUTE)\s*\(\s*@.{0,500})', sql_content, re.IGNORECASE | re.DOTALL):
            snippet = match.group(1)[:max_snippet_length]
            snippets.append(('DYNAMIC_SQL', snippet))

        # Extract nested CTEs
        for match in re.finditer(r'(WITH\s+\w+\s+AS\s*\([^)]*WITH.{0,500})', sql_content, re.IGNORECASE | re.DOTALL):
            snippet = match.group(1)[:max_snippet_length]
            snippets.append(('NESTED_CTE', snippet))

        # Extract PIVOT/UNPIVOT
        for match in re.finditer(r'((?:PIVOT|UNPIVOT).{0,300})', sql_content, re.IGNORECASE | re.DOTALL):
            snippet = match.group(1)[:max_snippet_length]
            snippets.append(('PIVOT_UNPIVOT', snippet))

        return snippets
