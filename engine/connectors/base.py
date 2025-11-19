"""
Base connector interface for database metadata extraction.

All database connectors must inherit from DatabaseConnector and implement
the required methods.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class ConnectionError(ConnectorError):
    """Raised when database connection fails."""
    pass


class QueryError(ConnectorError):
    """Raised when query execution fails."""
    pass


class ConfigurationError(ConnectorError):
    """Raised when connector configuration is invalid."""
    pass


@dataclass
class StoredProcedureMetadata:
    """
    Standard structure for stored procedure metadata.
    All connectors MUST return data in this format.
    """
    schema_name: str
    procedure_name: str
    source_code: str
    object_id: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    definition_hash: Optional[bytes] = None  # For incremental refresh

    @property
    def full_name(self) -> str:
        """Return fully qualified name: schema.procedure"""
        return f"{self.schema_name}.{self.procedure_name}"


@dataclass
class RefreshResult:
    """Result of a database refresh operation."""
    success: bool
    total_procedures: int
    new_procedures: int
    updated_procedures: int
    unchanged_procedures: int
    failed_procedures: int
    errors: List[str]
    duration_seconds: float

    @property
    def message(self) -> str:
        """Generate user-friendly message."""
        if not self.success:
            return f"Refresh failed: {', '.join(self.errors)}"

        if self.total_procedures == 0:
            return "No stored procedures found"

        parts = []
        if self.new_procedures > 0:
            parts.append(f"{self.new_procedures} new")
        if self.updated_procedures > 0:
            parts.append(f"{self.updated_procedures} updated")
        if self.unchanged_procedures > 0:
            parts.append(f"{self.unchanged_procedures} unchanged")

        summary = ", ".join(parts) if parts else "no changes"
        return f"Refresh successful: {self.total_procedures} procedures ({summary})"


class DatabaseConnector(ABC):
    """
    Abstract base class for database connectors.

    All database-specific connectors must inherit from this class
    and implement the required methods.
    """

    def __init__(self, connection_string: str, dialect: str, timeout: int = 30):
        """
        Initialize connector.

        Args:
            connection_string: Database connection string (format varies by dialect)
            dialect: Database dialect (tsql, postgres, snowflake, etc.)
            timeout: Query timeout in seconds
        """
        self.connection_string = connection_string
        self.dialect = dialect
        self.timeout = timeout
        self.queries = self._load_queries()
        logger.info(f"Initialized {self.dialect} connector")

    def _load_queries(self) -> Dict[str, Any]:
        """Load SQL queries from YAML configuration file."""
        query_file = Path(__file__).parent / "queries" / self.dialect / "metadata.yaml"

        if not query_file.exists():
            raise ConfigurationError(
                f"Query configuration not found: {query_file}. "
                f"Please create a metadata.yaml file for dialect '{self.dialect}'."
            )

        try:
            with open(query_file, 'r') as f:
                config = yaml.safe_load(f)

            if config.get('dialect') != self.dialect:
                raise ConfigurationError(
                    f"Dialect mismatch: expected '{self.dialect}', "
                    f"found '{config.get('dialect')}' in {query_file}"
                )

            logger.debug(f"Loaded query configuration for {self.dialect} from {query_file}")
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {query_file}: {e}")

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if database connection is reachable.

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails with specific error
        """
        pass

    @abstractmethod
    def list_procedures(self) -> List[StoredProcedureMetadata]:
        """
        List all stored procedures in the database.

        Returns:
            List of StoredProcedureMetadata objects (may have partial data)

        Raises:
            QueryError: If query execution fails
        """
        pass

    @abstractmethod
    def get_procedure_source(self, object_id: str) -> StoredProcedureMetadata:
        """
        Get full source code for a specific stored procedure.

        Args:
            object_id: Database-specific object identifier

        Returns:
            StoredProcedureMetadata with complete source code

        Raises:
            QueryError: If query execution fails
        """
        pass

    @abstractmethod
    def close(self):
        """Close database connection and cleanup resources."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()

    def supports_incremental_refresh(self) -> bool:
        """Check if this connector supports incremental refresh."""
        return self.queries.get('incremental', {}).get('enabled', False)

    def get_query_sql(self, query_name: str) -> str:
        """Get SQL query by name from configuration."""
        try:
            return self.queries['queries'][query_name]['sql']
        except KeyError:
            raise ConfigurationError(
                f"Query '{query_name}' not found in configuration for {self.dialect}"
            )
