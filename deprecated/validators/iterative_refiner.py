#!/usr/bin/env python3
"""
Iterative Refiner

Uses Grep/Glob search to iteratively find missing dependencies and refine the lineage graph.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple
from parsers.sql_parser_enhanced import Dependency, ConfidenceLevel


class IterativeRefiner:
    """Refines dependency detection using iterative search."""

    def __init__(self, synapse_dir: str):
        self.synapse_dir = Path(synapse_dir)

    def search_object_references(self, schema: str, object_name: str) -> List[Tuple[str, int, str]]:
        """
        Search for references to an object across all SQL files.

        Args:
            schema: Schema name
            object_name: Object name

        Returns:
            List of (file_path, line_number, line_content) tuples
        """
        references = []

        # Search patterns
        patterns = [
            f"{schema}.{object_name}",
            f"[{schema}].[{object_name}]",
            f"{schema}.\\[{object_name}\\]",
            f"\\[{schema}\\].{object_name}",
        ]

        for pattern in patterns:
            try:
                # Use grep to search for the pattern
                result = subprocess.run(
                    ['grep', '-rn', '-i', pattern, str(self.synapse_dir)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    # Parse grep output
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                file_path, line_num, content = parts[0], parts[1], parts[2]
                                references.append((file_path, int(line_num), content.strip()))

            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                # Grep not available or timeout, skip this pattern
                continue

        # Deduplicate
        return list(set(references))

    def find_procedures_writing_to_table(self, schema: str, table_name: str) -> List[str]:
        """
        Find stored procedures that write to a specific table.

        Args:
            schema: Table schema
            table_name: Table name

        Returns:
            List of stored procedure file paths
        """
        writing_procedures = []

        # Search for INSERT INTO, UPDATE, MERGE INTO, SELECT INTO patterns
        references = self.search_object_references(schema, table_name)

        for file_path, line_num, content in references:
            # Check if this is a write operation
            if re.search(r'\b(?:INSERT\s+INTO|UPDATE|MERGE\s+INTO|SELECT\s+.*\s+INTO)\b',
                        content, re.IGNORECASE):
                # Check if this is a stored procedure file
                if 'Stored Procedures' in file_path and file_path.endswith('.sql'):
                    writing_procedures.append(file_path)

        return list(set(writing_procedures))

    def find_tables_read_by_procedure(self, procedure_file: str) -> List[Tuple[str, str]]:
        """
        Find tables/views read by a stored procedure.

        Args:
            procedure_file: Path to stored procedure file

        Returns:
            List of (schema, table_name) tuples
        """
        tables = []

        try:
            with open(procedure_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find FROM and JOIN clauses
            pattern = r'(?:FROM|JOIN)\s+(\[?[\w]+\]?\.\[?[\w]+\]?)'

            for match in re.finditer(pattern, content, re.IGNORECASE):
                table_ref = match.group(1)

                # Normalize
                table_ref = re.sub(r'[\[\]"`]', '', table_ref)

                if '.' in table_ref:
                    parts = table_ref.split('.')
                    schema = parts[0]
                    table_name = parts[1]

                    # Skip temp tables
                    if not table_name.startswith('#'):
                        tables.append((schema, table_name))

        except (IOError, OSError):
            pass

        return list(set(tables))

    def discover_missing_dependencies(
        self,
        target_object: str,
        known_dependencies: Set[str]
    ) -> List[Dependency]:
        """
        Discover missing dependencies through iterative search.

        Args:
            target_object: Target object in format "schema.object_name"
            known_dependencies: Set of already known dependencies (schema.object_name)

        Returns:
            List of newly discovered dependencies
        """
        new_dependencies = []

        # Split target object
        if '.' in target_object:
            schema, obj_name = target_object.split('.', 1)
        else:
            schema = "dbo"
            obj_name = target_object

        # Find procedures that write to this object
        writing_procs = self.find_procedures_writing_to_table(schema, obj_name)

        for proc_file in writing_procs:
            # Extract procedure name from file
            proc_filename = Path(proc_file).stem

            if '.' in proc_filename:
                proc_schema, proc_name = proc_filename.split('.', 1)
            else:
                proc_schema = "dbo"
                proc_name = proc_filename

            proc_key = f"{proc_schema}.{proc_name}"

            # If this procedure is not in known dependencies, add it
            if proc_key not in known_dependencies:
                dep = Dependency(
                    object_name=proc_name,
                    schema=proc_schema,
                    object_type="StoredProcedure",
                    confidence=ConfidenceLevel.MEDIUM.value,
                    needs_ai_review=False,
                    detection_method="grep_search"
                )

                new_dependencies.append(dep)

        return new_dependencies

    def find_reverse_dependencies(self, schema: str, object_name: str) -> List[str]:
        """
        Find objects that depend on the given object (reverse dependencies).

        Args:
            schema: Schema name
            object_name: Object name

        Returns:
            List of dependent object names in format "schema.object_name"
        """
        dependents = []

        references = self.search_object_references(schema, object_name)

        for file_path, line_num, content in references:
            if file_path.endswith('.sql'):
                # Extract object name from file path
                filename = Path(file_path).stem

                if '.' in filename:
                    dependent_schema, dependent_name = filename.split('.', 1)
                else:
                    dependent_schema = "dbo"
                    dependent_name = filename

                dependent_key = f"{dependent_schema}.{dependent_name}"
                dependents.append(dependent_key)

        return list(set(dependents))

    def validate_lineage_completeness(
        self,
        lineage_graph: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Validate that the lineage graph is complete by checking for missing links.

        Args:
            lineage_graph: Dict mapping object_name to list of its dependencies

        Returns:
            Dict of missing dependencies (object -> [missing_deps])
        """
        missing = {}

        for obj, deps in lineage_graph.items():
            # For each dependency, check if it exists in the graph
            for dep in deps:
                if dep not in lineage_graph:
                    # This dependency is not in the graph - might be missing
                    if obj not in missing:
                        missing[obj] = []

                    missing[obj].append(dep)

        return missing
