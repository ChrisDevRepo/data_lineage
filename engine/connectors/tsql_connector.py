"""
T-SQL connector for SQL Server / Azure Synapse Analytics.

Uses pyodbc for database connectivity.
"""

import logging
import pyodbc
from datetime import datetime
from typing import List, Optional
from .base import (
    DatabaseConnector,
    StoredProcedureMetadata,
    ConnectionError,
    QueryError,
)

logger = logging.getLogger(__name__)


class TsqlConnector(DatabaseConnector):
    """
    T-SQL connector for SQL Server and Azure Synapse Analytics.

    Connection String Format:
        DRIVER={ODBC Driver 18 for SQL Server};SERVER=server;DATABASE=db;UID=user;PWD=pass
        Or use pyodbc connection string format
    """

    def __init__(self, connection_string: str, timeout: int = 30):
        super().__init__(connection_string, dialect="tsql", timeout=timeout)
        self.connection: Optional[pyodbc.Connection] = None

    def _connect(self) -> pyodbc.Connection:
        """Establish database connection."""
        if self.connection is None or self.connection.closed:
            try:
                self.connection = pyodbc.connect(
                    self.connection_string,
                    timeout=self.timeout,
                    autocommit=True
                )
                logger.debug("T-SQL connection established")
            except pyodbc.Error as e:
                logger.error(f"T-SQL connection failed: {e}")
                raise ConnectionError(f"Failed to connect to database: {e}")

        return self.connection

    def test_connection(self) -> bool:
        """Test if database connection is reachable."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            logger.info("T-SQL connection test successful")
            return True

        except Exception as e:
            logger.error(f"T-SQL connection test failed: {e}")
            raise ConnectionError(f"Database not reachable: {e}")

    def list_procedures(self) -> List[StoredProcedureMetadata]:
        """
        List all stored procedures with metadata.

        Returns stored procedures with partial data (no source code yet).
        Use get_procedure_source() to retrieve full source code.
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Get SQL from YAML configuration
            sql = self.get_query_sql('list_stored_procedures')

            logger.debug(f"Executing list_procedures query")
            cursor.execute(sql)

            procedures = []
            for row in cursor:
                try:
                    procedures.append(StoredProcedureMetadata(
                        schema_name=row.schema_name,
                        procedure_name=row.procedure_name,
                        object_id=str(row.object_id),
                        source_code="",  # Not loaded yet
                        created_date=row.create_date if hasattr(row, 'create_date') else None,
                        modified_date=row.modify_date if hasattr(row, 'modify_date') else None,
                        definition_hash=row.definition_hash if hasattr(row, 'definition_hash') else None,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse procedure row: {e}")
                    continue

            logger.info(f"Found {len(procedures)} stored procedures")
            return procedures

        except pyodbc.Error as e:
            logger.error(f"Failed to list procedures: {e}")
            raise QueryError(f"Failed to list procedures: {e}")

    def get_procedure_source(self, object_id: str) -> StoredProcedureMetadata:
        """
        Get full source code for a specific stored procedure.

        Args:
            object_id: T-SQL object_id (integer as string)

        Returns:
            StoredProcedureMetadata with complete source code
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Get SQL from YAML configuration
            sql = self.get_query_sql('get_procedure_source')

            logger.debug(f"Fetching source for object_id={object_id}")
            cursor.execute(sql, int(object_id))
            row = cursor.fetchone()

            if not row:
                raise QueryError(f"Procedure not found: object_id={object_id}")

            return StoredProcedureMetadata(
                schema_name=row.schema_name,
                procedure_name=row.procedure_name,
                source_code=row.source_code or "",
                object_id=object_id,
                modified_date=row.modify_date if hasattr(row, 'modify_date') else None,
            )

        except pyodbc.Error as e:
            logger.error(f"Failed to get procedure source for {object_id}: {e}")
            raise QueryError(f"Failed to get procedure source: {e}")

    def close(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            try:
                self.connection.close()
                logger.debug("T-SQL connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

        self.connection = None
