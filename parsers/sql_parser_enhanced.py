#!/usr/bin/env python3
"""
Enhanced SQL Parser with Confidence Scoring

This module provides an improved SQL parser that:
- Extracts dependencies from CREATE TABLE, VIEW, PROCEDURE statements
- Assigns confidence scores to each detected dependency
- Flags complex patterns for AI review
- Handles Azure Synapse specific patterns
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for dependency detection."""
    HIGH = 1.0      # Very confident (clear, standard SQL patterns)
    MEDIUM = 0.7    # Moderately confident (some ambiguity)
    LOW = 0.4       # Low confidence (complex pattern, might need AI)
    UNCERTAIN = 0.2 # Very uncertain (definitely needs AI review)


@dataclass
class Dependency:
    """Represents a SQL object dependency."""
    object_name: str
    schema: str
    object_type: str  # 'Table', 'View', 'StoredProcedure'
    confidence: float
    source_line: Optional[int] = None
    sql_snippet: Optional[str] = None
    needs_ai_review: bool = False
    detection_method: str = "regex"


@dataclass
class ParsedSQLObject:
    """Represents a parsed SQL object with metadata."""
    object_name: str
    schema: str
    object_type: str
    dependencies: List[Dependency]
    file_path: str
    confidence_score: float  # Overall confidence for this object
    needs_ai_review: bool = False
    complex_patterns: List[str] = None  # List of complex pattern types found


class EnhancedSQLParser:
    """Enhanced SQL parser with confidence scoring."""

    def __init__(self):
        self.complex_pattern_indicators = [
            r'MERGE\s+INTO',
            r'WITH\s+\w+\s+AS\s+\(.*?WITH\s+\w+\s+AS',  # Nested CTEs
            r'EXEC\s*\(',  # Dynamic SQL
            r'EXECUTE\s*\(',
            r'@\w+\s*=\s*N?[\'"](SELECT|INSERT|UPDATE)',  # SQL in variables
            r'PIVOT|UNPIVOT',
            r'OPENQUERY|OPENROWSET',
            r'FOR\s+XML|FOR\s+JSON',
        ]

    def normalize_object_name(self, name: str) -> str:
        """
        Normalize object names by removing brackets, quotes, and extra whitespace.
        """
        # Remove brackets and quotes
        name = re.sub(r'[\[\]"`]', '', name)
        name = name.strip()

        # Handle temp tables
        if name.startswith('#'):
            return name

        # Remove table hints
        name = re.sub(r'\s+with\s*\(.*?\)', '', name, flags=re.IGNORECASE)

        # Remove alias specifications
        name = re.sub(r'\s+as\s+\w+$', '', name, flags=re.IGNORECASE)

        # Split by dot and normalize
        parts = [p.strip() for p in name.split('.')]

        if len(parts) == 1:
            return parts[0]
        elif len(parts) >= 2:
            return f"{parts[-2]}.{parts[-1]}"

        return name

    def extract_schema_and_object(self, full_name: str) -> Tuple[str, str]:
        """Extract schema and object name from full object name."""
        normalized = self.normalize_object_name(full_name)
        parts = normalized.split('.')

        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return "dbo", parts[0]

    def detect_complex_patterns(self, content: str) -> List[str]:
        """Detect complex SQL patterns that might need AI review."""
        found_patterns = []

        for pattern in self.complex_pattern_indicators:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                found_patterns.append(pattern)

        return found_patterns

    def calculate_confidence(self, pattern_match: re.Match, context: str) -> Tuple[float, bool]:
        """
        Calculate confidence score for a detected dependency.

        Returns:
            Tuple of (confidence_score, needs_ai_review)
        """
        confidence = ConfidenceLevel.HIGH.value
        needs_ai = False

        matched_text = pattern_match.group(0)

        # Check for complexity indicators
        if re.search(r'CASE\s+WHEN', matched_text, re.IGNORECASE):
            confidence = min(confidence, ConfidenceLevel.MEDIUM.value)

        if re.search(r'EXISTS|NOT\s+EXISTS', matched_text, re.IGNORECASE):
            confidence = min(confidence, ConfidenceLevel.MEDIUM.value)

        # Check for subqueries
        if matched_text.count('(') > 2:
            confidence = min(confidence, ConfidenceLevel.LOW.value)
            needs_ai = True

        # Check for dynamic table names
        if re.search(r'@\w+', matched_text):
            confidence = ConfidenceLevel.UNCERTAIN.value
            needs_ai = True

        # Check for complex joins
        join_count = len(re.findall(r'JOIN', matched_text, re.IGNORECASE))
        if join_count > 3:
            confidence = min(confidence, ConfidenceLevel.MEDIUM.value)

        return confidence, needs_ai

    def extract_from_dependencies(self, content: str, line_offset: int = 0) -> List[Dependency]:
        """Extract dependencies from FROM and JOIN clauses with confidence scoring."""
        dependencies = []

        # Remove CTEs to avoid false positives
        content_no_cte = self.remove_ctes(content)

        # Pattern: FROM/JOIN [schema].[table]
        pattern = r'(?:FROM|JOIN)\s+(\[?[\w]+\]?\.\[?[\w]+\]?)(?:\s+(?:AS\s+)?[\w]+)?(?:\s+WITH\s*\([^)]*\))?'

        for match in re.finditer(pattern, content_no_cte, re.IGNORECASE):
            table_name = self.normalize_object_name(match.group(1))

            # Skip temp tables
            if table_name.startswith('#'):
                continue

            # Calculate confidence
            confidence, needs_ai = self.calculate_confidence(match, content_no_cte)

            # Extract line number
            line_num = content[:match.start()].count('\n') + line_offset + 1

            # Extract schema and object
            schema, obj_name = self.extract_schema_and_object(table_name)

            # Create dependency
            dep = Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",  # Could be table or view, will be resolved later
                confidence=confidence,
                source_line=line_num,
                sql_snippet=match.group(0),
                needs_ai_review=needs_ai,
                detection_method="regex_from_join"
            )

            dependencies.append(dep)

        return dependencies

    def extract_insert_targets(self, content: str, line_offset: int = 0) -> List[Dependency]:
        """Extract target tables from INSERT INTO statements."""
        dependencies = []

        # Pattern: INSERT INTO [schema].[table]
        pattern = r'INSERT\s+INTO\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            table_name = self.normalize_object_name(match.group(1))

            if table_name.startswith('#'):
                continue

            confidence, needs_ai = self.calculate_confidence(match, content)
            line_num = content[:match.start()].count('\n') + line_offset + 1
            schema, obj_name = self.extract_schema_and_object(table_name)

            dep = Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=confidence,
                source_line=line_num,
                sql_snippet=match.group(0),
                needs_ai_review=needs_ai,
                detection_method="regex_insert"
            )

            dependencies.append(dep)

        return dependencies

    def extract_select_into_targets(self, content: str, line_offset: int = 0) -> List[Dependency]:
        """Extract target tables from SELECT INTO statements."""
        dependencies = []

        # Pattern: INTO [schema].[table]
        pattern = r'INTO\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            table_name = self.normalize_object_name(match.group(1))

            if table_name.startswith('#'):
                continue

            confidence, needs_ai = self.calculate_confidence(match, content)
            line_num = content[:match.start()].count('\n') + line_offset + 1
            schema, obj_name = self.extract_schema_and_object(table_name)

            dep = Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=confidence,
                source_line=line_num,
                sql_snippet=match.group(0),
                needs_ai_review=needs_ai,
                detection_method="regex_select_into"
            )

            dependencies.append(dep)

        return dependencies

    def extract_update_targets(self, content: str, line_offset: int = 0) -> List[Dependency]:
        """Extract target tables from UPDATE statements."""
        dependencies = []

        # Pattern: UPDATE [schema].[table]
        pattern = r'UPDATE\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            table_name = self.normalize_object_name(match.group(1))

            if table_name.startswith('#') or '.' not in table_name:
                continue

            confidence, needs_ai = self.calculate_confidence(match, content)
            line_num = content[:match.start()].count('\n') + line_offset + 1
            schema, obj_name = self.extract_schema_and_object(table_name)

            dep = Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=confidence,
                source_line=line_num,
                sql_snippet=match.group(0),
                needs_ai_review=needs_ai,
                detection_method="regex_update"
            )

            dependencies.append(dep)

        return dependencies

    def remove_ctes(self, content: str) -> str:
        """Remove Common Table Expressions to avoid false positives."""
        # This is a simplified CTE removal - complex nested CTEs may need AI
        pattern = r'WITH\s+\w+\s+AS\s*\([^)]*\)'

        # Simple removal for single-level CTEs
        result = re.sub(pattern, '', content, flags=re.IGNORECASE)

        # If we still have WITH after removal, might be nested - flag for AI
        if re.search(r'WITH\s+\w+\s+AS', result, re.IGNORECASE):
            # Complex nested CTEs present
            return result

        return result

    def parse_sql_object(self, content: str, file_path: str, object_type: str) -> ParsedSQLObject:
        """
        Parse a SQL object and extract all dependencies with confidence scores.

        Args:
            content: SQL file content
            file_path: Path to the SQL file
            object_type: 'Table', 'View', or 'StoredProcedure'

        Returns:
            ParsedSQLObject with dependencies and metadata
        """
        # Detect complex patterns
        complex_patterns = self.detect_complex_patterns(content)
        needs_ai_review = len(complex_patterns) > 0

        # Extract all dependencies
        all_dependencies = []

        # FROM/JOIN dependencies (read dependencies)
        all_dependencies.extend(self.extract_from_dependencies(content))

        # For stored procedures, also extract write targets
        if object_type == "StoredProcedure":
            all_dependencies.extend(self.extract_insert_targets(content))
            all_dependencies.extend(self.extract_select_into_targets(content))
            all_dependencies.extend(self.extract_update_targets(content))

        # Deduplicate dependencies (keep highest confidence)
        dep_map = {}
        for dep in all_dependencies:
            key = f"{dep.schema}.{dep.object_name}"
            if key not in dep_map or dep.confidence > dep_map[key].confidence:
                dep_map[key] = dep

        unique_dependencies = list(dep_map.values())

        # Calculate overall confidence score
        if unique_dependencies:
            avg_confidence = sum(d.confidence for d in unique_dependencies) / len(unique_dependencies)
        else:
            avg_confidence = 1.0  # No dependencies, high confidence

        # Flag for AI review if any dependency needs it or complex patterns found
        needs_ai_review = needs_ai_review or any(d.needs_ai_review for d in unique_dependencies)

        # Extract object name from file path
        from pathlib import Path
        filename = Path(file_path).stem
        if '.' in filename:
            parts = filename.split('.')
            schema = parts[0]
            object_name = '.'.join(parts[1:])
        else:
            schema = "dbo"
            object_name = filename

        return ParsedSQLObject(
            object_name=object_name,
            schema=schema,
            object_type=object_type,
            dependencies=unique_dependencies,
            file_path=file_path,
            confidence_score=avg_confidence,
            needs_ai_review=needs_ai_review,
            complex_patterns=complex_patterns if complex_patterns else None
        )
