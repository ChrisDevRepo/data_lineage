"""
Simple input validators for lineage parser.

Since this is an internal tool with read-only access, we only validate
to prevent accidental errors, not malicious attacks.

Author: Vibecoding
Version: 3.0.0
"""

import re
from typing import Union


def sanitize_identifier(name: str) -> str:
    """
    Sanitize SQL identifier (schema/table/object name).

    Args:
        name: Identifier to sanitize

    Returns:
        Sanitized identifier

    Raises:
        ValueError: If identifier contains suspicious characters

    Example:
        >>> sanitize_identifier("dbo.Customer")
        'dbo.Customer'
        >>> sanitize_identifier("schema'; DROP TABLE--")
        ValueError: Invalid identifier format
    """
    if not name:
        raise ValueError("Identifier cannot be empty")

    # Allow: alphanumeric, dots, underscores, brackets
    # This covers: dbo.TableName, [schema].[table], schema_name
    if not re.match(r'^[\w\.\[\]]+$', name):
        raise ValueError(f"Invalid identifier format: {name}")

    # Additional check: no SQL keywords that could be dangerous
    suspicious = ['drop', 'delete', 'truncate', 'exec', 'execute', '--', '/*', '*/']
    lower_name = name.lower()
    if any(keyword in lower_name for keyword in suspicious):
        raise ValueError(f"Identifier contains suspicious keyword: {name}")

    return name


def validate_object_id(obj_id: Union[int, str]) -> int:
    """
    Validate object_id is a positive integer.

    Args:
        obj_id: Object ID to validate

    Returns:
        Validated integer object_id

    Raises:
        ValueError: If object_id is invalid

    Example:
        >>> validate_object_id(123)
        123
        >>> validate_object_id("123")
        123
        >>> validate_object_id(-1)
        ValueError: Invalid object_id: -1
    """
    try:
        obj_id_int = int(obj_id)
    except (ValueError, TypeError):
        raise ValueError(f"object_id must be an integer, got: {obj_id}")

    if obj_id_int < 0:
        raise ValueError(f"Invalid object_id: {obj_id_int}")

    return obj_id_int


def validate_object_type(obj_type: str) -> str:
    """
    Validate object_type is one of the allowed types.

    Args:
        obj_type: Object type to validate

    Returns:
        Validated object type

    Raises:
        ValueError: If object type is invalid
    """
    allowed_types = {
        'Table', 'View', 'Stored Procedure',
        'Function', 'Synonym', 'Type'
    }

    if obj_type not in allowed_types:
        raise ValueError(f"Invalid object_type: {obj_type}. Allowed: {allowed_types}")

    return obj_type
