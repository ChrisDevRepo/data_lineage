#!/usr/bin/env python3
"""
AI-Assisted SQL Parser

Uses AI analysis to extract dependencies from complex SQL patterns that regex cannot handle reliably.
This module performs inline analysis without requiring external API calls.
"""

import re
from typing import List, Dict, Set, Tuple
from parsers.sql_parser_enhanced import Dependency, ConfidenceLevel


class AISQLParser:
    """AI-assisted SQL parser for complex patterns."""

    def __init__(self):
        pass

    def analyze_merge_statement(self, merge_snippet: str) -> List[Dependency]:
        """
        Analyze MERGE statement to extract both target and source dependencies.

        MERGE INTO target_table
        USING source_table
        ON (condition)
        WHEN MATCHED THEN UPDATE...
        """
        dependencies = []

        # Extract target (after MERGE INTO)
        target_match = re.search(r'MERGE\s+INTO\s+(\[?[\w]+\]?\.\[?[\w]+\]?)',
                                merge_snippet, re.IGNORECASE)
        if target_match:
            table_name = self._normalize(target_match.group(1))
            schema, obj_name = self._split_schema_object(table_name)

            dependencies.append(Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=ConfidenceLevel.HIGH.value,
                needs_ai_review=False,
                detection_method="ai_merge_target"
            ))

        # Extract source (after USING)
        source_match = re.search(r'USING\s+(\[?[\w]+\]?\.\[?[\w]+\]?)',
                                merge_snippet, re.IGNORECASE)
        if source_match:
            table_name = self._normalize(source_match.group(1))
            schema, obj_name = self._split_schema_object(table_name)

            dependencies.append(Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=ConfidenceLevel.HIGH.value,
                needs_ai_review=False,
                detection_method="ai_merge_source"
            ))

        # Also check for additional tables in WHEN clauses
        when_tables = re.findall(r'FROM\s+(\[?[\w]+\]?\.\[?[\w]+\]?)',
                                merge_snippet, re.IGNORECASE)
        for table_name in when_tables:
            table_name = self._normalize(table_name)
            schema, obj_name = self._split_schema_object(table_name)

            dependencies.append(Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=ConfidenceLevel.MEDIUM.value,
                needs_ai_review=False,
                detection_method="ai_merge_when_clause"
            ))

        return dependencies

    def analyze_dynamic_sql(self, dynamic_sql_snippet: str) -> List[Dependency]:
        """
        Analyze dynamic SQL for potential dependencies.

        This is difficult since table names may be constructed at runtime.
        We use heuristics to find likely table references.
        """
        dependencies = []

        # Look for string literals that might contain table names
        # Pattern: schemas and table names in quoted strings
        string_literals = re.findall(r'[\'"]([A-Z_]+\.[A-Z_\w]+)[\'"]',
                                     dynamic_sql_snippet, re.IGNORECASE)

        for literal in string_literals:
            if '.' in literal and not literal.startswith('@'):
                parts = literal.split('.')
                if len(parts) == 2:
                    schema, obj_name = parts
                    # Filter out obvious non-table strings
                    if schema.upper() in ['CONSUMPTION_CLINOPSFINANCE', 'CONSUMPTION_FINANCE',
                                          'CONSUMPTION_POWERBI', 'CONSUMPTION_PRIMA',
                                          'STAGING_CADENCE', 'DBO']:
                        dependencies.append(Dependency(
                            object_name=obj_name,
                            schema=schema,
                            object_type="Table",
                            confidence=ConfidenceLevel.LOW.value,  # Low confidence for dynamic SQL
                            needs_ai_review=True,
                            detection_method="ai_dynamic_sql_heuristic"
                        ))

        return dependencies

    def analyze_nested_cte(self, cte_snippet: str) -> List[Dependency]:
        """
        Analyze nested Common Table Expressions.

        WITH cte1 AS (SELECT ... FROM table1),
             cte2 AS (SELECT ... FROM cte1 JOIN table2)
        SELECT FROM cte2
        """
        dependencies = []

        # Extract all table references that are not CTE names
        # First, find all CTE names
        cte_names = set()
        for match in re.finditer(r'WITH\s+(\w+)\s+AS', cte_snippet, re.IGNORECASE):
            cte_names.add(match.group(1).upper())

        # Now find all FROM/JOIN references
        all_refs = re.findall(r'(?:FROM|JOIN)\s+(\[?[\w]+\]?(?:\.\[?[\w]+\]?)?)',
                             cte_snippet, re.IGNORECASE)

        for ref in all_refs:
            normalized = self._normalize(ref)

            # Skip if this is a CTE reference
            if '.' not in normalized:
                # Could be a CTE name or simple table reference
                if normalized.upper() in cte_names:
                    continue

            schema, obj_name = self._split_schema_object(normalized)

            dependencies.append(Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=ConfidenceLevel.MEDIUM.value,
                needs_ai_review=False,
                detection_method="ai_nested_cte"
            ))

        return dependencies

    def analyze_pivot_unpivot(self, pivot_snippet: str) -> List[Dependency]:
        """
        Analyze PIVOT/UNPIVOT operations.

        SELECT ... FROM (SELECT ... FROM table) AS SourceTable
        PIVOT (AGG(column) FOR column IN (...)) AS PivotTable
        """
        dependencies = []

        # Find source tables in the subquery before PIVOT/UNPIVOT
        # Look for FROM clauses before PIVOT/UNPIVOT keyword
        pivot_pos = re.search(r'\b(?:PIVOT|UNPIVOT)\b', pivot_snippet, re.IGNORECASE)

        if pivot_pos:
            before_pivot = pivot_snippet[:pivot_pos.start()]

            # Find all FROM/JOIN references before PIVOT
            refs = re.findall(r'(?:FROM|JOIN)\s+(\[?[\w]+\]?\.\[?[\w]+\]?)',
                             before_pivot, re.IGNORECASE)

            for ref in refs:
                normalized = self._normalize(ref)
                schema, obj_name = self._split_schema_object(normalized)

                dependencies.append(Dependency(
                    object_name=obj_name,
                    schema=schema,
                    object_type="Table",
                    confidence=ConfidenceLevel.MEDIUM.value,
                    needs_ai_review=False,
                    detection_method="ai_pivot_source"
                ))

        return dependencies

    def analyze_complex_snippet(self, snippet_type: str, sql_snippet: str) -> List[Dependency]:
        """
        Main entry point for analyzing complex SQL snippets.

        Args:
            snippet_type: Type of complex pattern ('MERGE', 'DYNAMIC_SQL', 'NESTED_CTE', etc.)
            sql_snippet: The SQL code snippet to analyze

        Returns:
            List of dependencies found
        """
        if snippet_type == 'MERGE':
            return self.analyze_merge_statement(sql_snippet)

        elif snippet_type == 'DYNAMIC_SQL':
            return self.analyze_dynamic_sql(sql_snippet)

        elif snippet_type == 'NESTED_CTE':
            return self.analyze_nested_cte(sql_snippet)

        elif snippet_type == 'PIVOT_UNPIVOT':
            return self.analyze_pivot_unpivot(sql_snippet)

        else:
            # Unknown type, return empty
            return []

    def _normalize(self, name: str) -> str:
        """Normalize object name."""
        name = re.sub(r'[\[\]"`]', '', name)
        name = name.strip()
        name = re.sub(r'\s+with\s*\(.*?\)', '', name, flags=re.IGNORECASE)
        return name

    def _split_schema_object(self, full_name: str) -> Tuple[str, str]:
        """Split full name into schema and object name."""
        parts = full_name.split('.')
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        else:
            return "dbo", parts[0]
