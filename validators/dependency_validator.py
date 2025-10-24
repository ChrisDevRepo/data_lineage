#!/usr/bin/env python3
"""
Dependency Validator

Validates that detected dependencies actually exist in the codebase.
Cross-checks against actual SQL files to verify object existence.
"""

import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from parsers.sql_parser_enhanced import Dependency
import re


class ValidationResult:
    """Result of dependency validation."""

    def __init__(self):
        self.valid_dependencies: List[Dependency] = []
        self.invalid_dependencies: List[Dependency] = []
        self.missing_objects: List[str] = []
        self.object_type_mismatches: List[Tuple[str, str, str]] = []  # (object, detected_type, actual_type)


class DependencyValidator:
    """Validates dependencies against the actual codebase."""

    def __init__(self, synapse_dir: str):
        self.synapse_dir = Path(synapse_dir)
        self.tables_dir = self.synapse_dir / "Tables"
        self.views_dir = self.synapse_dir / "Views"
        self.procedures_dir = self.synapse_dir / "Stored Procedures"

        # Build index of all objects
        self.object_index: Dict[str, Dict[str, any]] = {}
        self._build_object_index()

    def _build_object_index(self):
        """Build an index of all SQL objects in the codebase."""
        # Index tables
        if self.tables_dir.exists():
            for sql_file in self.tables_dir.glob("*.sql"):
                self._index_file(sql_file, "Table")

        # Index views
        if self.views_dir.exists():
            for sql_file in self.views_dir.glob("*.sql"):
                self._index_file(sql_file, "View")

        # Index stored procedures
        if self.procedures_dir.exists():
            for sql_file in self.procedures_dir.glob("*.sql"):
                self._index_file(sql_file, "StoredProcedure")

    def _index_file(self, file_path: Path, object_type: str):
        """Index a single SQL file."""
        filename = file_path.stem

        # Parse filename: SCHEMA.ObjectName.sql
        if '.' in filename:
            parts = filename.split('.')
            schema = parts[0]
            object_name = '.'.join(parts[1:])
        else:
            schema = "dbo"
            object_name = filename

        # Create multiple index keys for lookup
        keys = [
            f"{schema}.{object_name}",
            f"{schema.upper()}.{object_name}",
            f"{schema.lower()}.{object_name}",
            object_name,  # Without schema
            object_name.upper(),
            object_name.lower(),
        ]

        for key in keys:
            self.object_index[key] = {
                'schema': schema,
                'object_name': object_name,
                'object_type': object_type,
                'file_path': str(file_path)
            }

    def validate_dependency(self, dep: Dependency) -> bool:
        """
        Validate a single dependency.

        Returns:
            True if dependency is valid, False otherwise
        """
        # Try various key formats
        keys_to_try = [
            f"{dep.schema}.{dep.object_name}",
            f"{dep.schema.upper()}.{dep.object_name}",
            f"{dep.schema.lower()}.{dep.object_name}",
            dep.object_name,
            dep.object_name.upper(),
            dep.object_name.lower(),
        ]

        for key in keys_to_try:
            if key in self.object_index:
                return True

        return False

    def get_actual_object_type(self, schema: str, object_name: str) -> Optional[str]:
        """
        Get the actual object type from the index.

        Returns:
            Object type string or None if not found
        """
        keys_to_try = [
            f"{schema}.{object_name}",
            f"{schema.upper()}.{object_name}",
            f"{schema.lower()}.{object_name}",
            object_name,
        ]

        for key in keys_to_try:
            if key in self.object_index:
                return self.object_index[key]['object_type']

        return None

    def validate_dependencies(self, dependencies: List[Dependency]) -> ValidationResult:
        """
        Validate a list of dependencies.

        Args:
            dependencies: List of dependencies to validate

        Returns:
            ValidationResult with valid and invalid dependencies
        """
        result = ValidationResult()

        for dep in dependencies:
            if self.validate_dependency(dep):
                # Check if object type matches
                actual_type = self.get_actual_object_type(dep.schema, dep.object_name)

                if actual_type and actual_type != dep.object_type:
                    # Type mismatch - update but keep as valid
                    result.object_type_mismatches.append(
                        (f"{dep.schema}.{dep.object_name}", dep.object_type, actual_type)
                    )

                    # Update dependency with correct type
                    dep.object_type = actual_type

                result.valid_dependencies.append(dep)
            else:
                # Object not found in codebase
                result.invalid_dependencies.append(dep)
                result.missing_objects.append(f"{dep.schema}.{dep.object_name}")

        return result

    def find_object_file(self, schema: str, object_name: str) -> Optional[Path]:
        """
        Find the file path for a given object.

        Args:
            schema: Schema name
            object_name: Object name

        Returns:
            Path to the SQL file or None if not found
        """
        keys_to_try = [
            f"{schema}.{object_name}",
            f"{schema.upper()}.{object_name}",
            f"{schema.lower()}.{object_name}",
        ]

        for key in keys_to_try:
            if key in self.object_index:
                file_path = self.object_index[key]['file_path']
                return Path(file_path)

        return None

    def get_all_objects_by_schema(self, schema: str) -> List[Dict]:
        """
        Get all objects in a specific schema.

        Args:
            schema: Schema name

        Returns:
            List of object dictionaries
        """
        objects = []

        for key, obj_info in self.object_index.items():
            if obj_info['schema'].upper() == schema.upper():
                if key == f"{obj_info['schema']}.{obj_info['object_name']}":
                    objects.append(obj_info)

        return objects

    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about indexed objects.

        Returns:
            Dictionary with object counts by type and schema
        """
        stats = {
            'total_objects': 0,
            'by_type': {},
            'by_schema': {}
        }

        seen = set()

        for key, obj_info in self.object_index.items():
            # Only count unique objects (not aliases)
            full_key = f"{obj_info['schema']}.{obj_info['object_name']}"
            if full_key in seen:
                continue

            seen.add(full_key)
            stats['total_objects'] += 1

            # Count by type
            obj_type = obj_info['object_type']
            stats['by_type'][obj_type] = stats['by_type'].get(obj_type, 0) + 1

            # Count by schema
            schema = obj_info['schema']
            stats['by_schema'][schema] = stats['by_schema'].get(schema, 0) + 1

        return stats
