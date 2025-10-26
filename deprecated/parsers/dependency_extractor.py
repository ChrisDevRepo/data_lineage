#!/usr/bin/env python3
"""
Dependency Extractor

Extracts all types of SQL dependencies from database objects:
- Read dependencies (FROM, JOIN)
- Write dependencies (INSERT, UPDATE, MERGE, SELECT INTO)
- Execution dependencies (EXEC stored procedures)
- Schema references
"""

import re
from typing import List, Set, Dict
from pathlib import Path
from parsers.sql_parser_enhanced import Dependency, ConfidenceLevel


class DependencyExtractor:
    """Extracts all types of dependencies from SQL code."""

    def __init__(self):
        self.parser = None  # Will be injected

    def normalize_name(self, name: str) -> str:
        """Normalize object names."""
        name = re.sub(r'[\[\]"`]', '', name)
        name = name.strip()
        name = re.sub(r'\s+with\s*\(.*?\)', '', name, flags=re.IGNORECASE)
        return name

    def extract_exec_dependencies(self, content: str, line_offset: int = 0) -> List[Dependency]:
        """
        Extract stored procedure execution dependencies.

        Patterns:
        - EXEC [schema].[procedure]
        - EXECUTE [schema].[procedure]
        - EXEC @variable = [schema].[procedure]
        """
        dependencies = []

        # Pattern: EXEC/EXECUTE [schema].[procedure]
        patterns = [
            r'(?:EXEC|EXECUTE)\s+(\[?[\w]+\]?\.\[?[\w]+\]?)',
            r'(?:EXEC|EXECUTE)\s+@[\w]+\s*=\s*(\[?[\w]+\]?\.\[?[\w]+\]?)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                proc_name = self.normalize_name(match.group(1))

                if proc_name.startswith('#') or proc_name.startswith('@'):
                    continue

                parts = proc_name.split('.')
                if len(parts) >= 2:
                    schema = parts[-2]
                    obj_name = parts[-1]
                else:
                    schema = "dbo"
                    obj_name = proc_name

                line_num = content[:match.start()].count('\n') + line_offset + 1

                dep = Dependency(
                    object_name=obj_name,
                    schema=schema,
                    object_type="StoredProcedure",
                    confidence=ConfidenceLevel.HIGH.value,
                    source_line=line_num,
                    sql_snippet=match.group(0),
                    needs_ai_review=False,
                    detection_method="regex_exec"
                )

                dependencies.append(dep)

        return dependencies

    def extract_merge_dependencies(self, content: str, line_offset: int = 0) -> List[Dependency]:
        """
        Extract dependencies from MERGE statements.

        Pattern: MERGE INTO [target] USING [source]
        """
        dependencies = []

        # Pattern: MERGE INTO [schema].[table]
        pattern_target = r'MERGE\s+INTO\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

        for match in re.finditer(pattern_target, content, re.IGNORECASE):
            table_name = self.normalize_name(match.group(1))

            if table_name.startswith('#'):
                continue

            parts = table_name.split('.')
            if len(parts) >= 2:
                schema = parts[-2]
                obj_name = parts[-1]
            else:
                schema = "dbo"
                obj_name = table_name

            line_num = content[:match.start()].count('\n') + line_offset + 1

            dep = Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=ConfidenceLevel.MEDIUM.value,  # MERGE is complex
                source_line=line_num,
                sql_snippet=match.group(0),
                needs_ai_review=True,  # MERGE statements are complex
                detection_method="regex_merge_target"
            )

            dependencies.append(dep)

        # Pattern: USING [schema].[table]
        pattern_source = r'USING\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

        for match in re.finditer(pattern_source, content, re.IGNORECASE):
            # Check if this USING is part of a MERGE (look back for MERGE keyword)
            context_start = max(0, match.start() - 200)
            context = content[context_start:match.start()]

            if not re.search(r'MERGE\s+INTO', context, re.IGNORECASE):
                continue

            table_name = self.normalize_name(match.group(1))

            if table_name.startswith('#'):
                continue

            parts = table_name.split('.')
            if len(parts) >= 2:
                schema = parts[-2]
                obj_name = parts[-1]
            else:
                schema = "dbo"
                obj_name = table_name

            line_num = content[:match.start()].count('\n') + line_offset + 1

            dep = Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=ConfidenceLevel.MEDIUM.value,
                source_line=line_num,
                sql_snippet=match.group(0),
                needs_ai_review=True,
                detection_method="regex_merge_source"
            )

            dependencies.append(dep)

        return dependencies

    def extract_truncate_targets(self, content: str, line_offset: int = 0) -> List[Dependency]:
        """
        Extract tables from TRUNCATE TABLE statements.

        Pattern: TRUNCATE TABLE [schema].[table]
        """
        dependencies = []

        pattern = r'TRUNCATE\s+TABLE\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            table_name = self.normalize_name(match.group(1))

            if table_name.startswith('#'):
                continue

            parts = table_name.split('.')
            if len(parts) >= 2:
                schema = parts[-2]
                obj_name = parts[-1]
            else:
                schema = "dbo"
                obj_name = table_name

            line_num = content[:match.start()].count('\n') + line_offset + 1

            dep = Dependency(
                object_name=obj_name,
                schema=schema,
                object_type="Table",
                confidence=ConfidenceLevel.HIGH.value,
                source_line=line_num,
                sql_snippet=match.group(0),
                needs_ai_review=False,
                detection_method="regex_truncate"
            )

            dependencies.append(dep)

        return dependencies

    def extract_temp_table_creation(self, content: str) -> Dict[str, Set[str]]:
        """
        Extract temp table creation and track their source dependencies.

        Returns:
            Dict mapping temp table name to set of source table names
        """
        temp_table_deps = {}

        # Pattern: SELECT ... INTO #temp FROM [source]
        pattern = r'SELECT\s+.+?\s+INTO\s+(#\w+)\s+FROM\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

        for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
            temp_name = match.group(1)
            source_name = self.normalize_name(match.group(2))

            if temp_name not in temp_table_deps:
                temp_table_deps[temp_name] = set()

            temp_table_deps[temp_name].add(source_name)

        # Pattern: CREATE TABLE #temp
        pattern_create = r'CREATE\s+TABLE\s+(#\w+)'

        for match in re.finditer(pattern_create, content, re.IGNORECASE):
            temp_name = match.group(1)
            if temp_name not in temp_table_deps:
                temp_table_deps[temp_name] = set()

        return temp_table_deps

    def resolve_temp_table_dependencies(
        self,
        dependencies: List[Dependency],
        temp_table_map: Dict[str, Set[str]]
    ) -> List[Dependency]:
        """
        Replace temp table dependencies with their actual source dependencies.

        Args:
            dependencies: List of dependencies that may include temp tables
            temp_table_map: Mapping from temp table names to their source tables

        Returns:
            Resolved list of dependencies with temp tables replaced
        """
        resolved = []

        for dep in dependencies:
            full_name = f"{dep.schema}.{dep.object_name}" if dep.schema != "dbo" else dep.object_name

            # Check if this is a temp table reference
            if dep.object_name.startswith('#'):
                temp_name = dep.object_name

                if temp_name in temp_table_map:
                    # Replace with source dependencies
                    for source in temp_table_map[temp_name]:
                        parts = source.split('.')
                        if len(parts) >= 2:
                            schema = parts[-2]
                            obj_name = parts[-1]
                        else:
                            schema = "dbo"
                            obj_name = source

                        # Create new dependency pointing to actual source
                        resolved_dep = Dependency(
                            object_name=obj_name,
                            schema=schema,
                            object_type=dep.object_type,
                            confidence=dep.confidence * 0.9,  # Slightly lower confidence
                            source_line=dep.source_line,
                            sql_snippet=f"{dep.sql_snippet} (via temp table {temp_name})",
                            needs_ai_review=dep.needs_ai_review,
                            detection_method=f"{dep.detection_method}_temp_resolved"
                        )

                        resolved.append(resolved_dep)
                else:
                    # Temp table source unknown, keep original but flag for AI
                    dep.needs_ai_review = True
                    dep.confidence = ConfidenceLevel.LOW.value
                    resolved.append(dep)
            else:
                # Not a temp table, keep as is
                resolved.append(dep)

        return resolved

    def extract_all_dependencies(self, content: str, file_path: str, object_type: str) -> List[Dependency]:
        """
        Extract all types of dependencies from SQL content.

        Args:
            content: SQL file content
            file_path: Path to SQL file
            object_type: 'Table', 'View', or 'StoredProcedure'

        Returns:
            Complete list of dependencies with confidence scores
        """
        all_deps = []

        # Import parser here to avoid circular dependency
        from parsers.sql_parser_enhanced import EnhancedSQLParser

        parser = EnhancedSQLParser()

        # Extract read dependencies (FROM/JOIN)
        all_deps.extend(parser.extract_from_dependencies(content))

        # Extract write dependencies
        if object_type == "StoredProcedure":
            all_deps.extend(parser.extract_insert_targets(content))
            all_deps.extend(parser.extract_select_into_targets(content))
            all_deps.extend(parser.extract_update_targets(content))
            all_deps.extend(self.extract_merge_dependencies(content))
            all_deps.extend(self.extract_truncate_targets(content))
            all_deps.extend(self.extract_exec_dependencies(content))

        # Handle temp tables
        temp_table_map = self.extract_temp_table_creation(content)
        all_deps = self.resolve_temp_table_dependencies(all_deps, temp_table_map)

        # Deduplicate (keep highest confidence for each unique object)
        dep_map = {}
        for dep in all_deps:
            key = f"{dep.schema}.{dep.object_name}"
            if key not in dep_map or dep.confidence > dep_map[key].confidence:
                dep_map[key] = dep

        return list(dep_map.values())
