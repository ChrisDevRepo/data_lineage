"""
Database refresh service with incremental update support.

Handles direct database connection, metadata extraction, and
incremental refresh logic with comprehensive error handling.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from engine.connectors import get_connector, ConnectorError, StoredProcedureMetadata, RefreshResult
from engine.config.settings import AppSettings

logger = logging.getLogger(__name__)


class DatabaseRefreshService:
    """
    Service for refreshing stored procedure metadata from database.

    Features:
    - Incremental refresh (only changed procedures)
    - Comprehensive error handling
    - Progress tracking
    - Failsafe operation
    """

    def __init__(self, settings: AppSettings):
        """
        Initialize database refresh service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.metadata_cache_file = Path("metadata_cache.json")

    def test_connection(self) -> tuple[bool, str]:
        """
        Test database connection.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.settings.db.enabled:
            return False, "Database connection not enabled (DB_ENABLED=false)"

        if not self.settings.db.connection_string:
            return False, "Database connection string not configured"

        try:
            logger.info("Testing database connection...")
            connector = get_connector(
                dialect=self.settings.sql_dialect,
                connection_string=self.settings.db.connection_string,
                timeout=self.settings.db.timeout
            )

            with connector:
                connector.test_connection()
                logger.info("✅ Database connection successful")
                return True, "Database connection successful"

        except ConnectorError as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False, f"Database not reachable: {str(e)}"

        except Exception as e:
            logger.error(f"❌ Unexpected error testing connection: {e}", exc_info=True)
            return False, f"Connection test failed: {str(e)}"

    def refresh_and_convert_to_parquet(self, job_dir: Path, incremental: bool = True) -> RefreshResult:
        """
        Refresh metadata from database and convert to Parquet files.

        This method creates the SAME Parquet files that the extraction script creates,
        so the downstream processing pipeline remains unchanged.

        Args:
            job_dir: Directory to save Parquet files (uploads/job_id/)
            incremental: If True, only fetch changed procedures

        Returns:
            RefreshResult with success status and statistics
        """
        start_time = time.time()

        # Validate configuration
        if not self.settings.db.enabled:
            return RefreshResult(
                success=False,
                total_procedures=0,
                new_procedures=0,
                updated_procedures=0,
                unchanged_procedures=0,
                failed_procedures=0,
                errors=["Database connection not enabled (set DB_ENABLED=true in .env)"],
                duration_seconds=0
            )

        try:
            logger.info(f"🔄 Fetching metadata from database (incremental={incremental})")

            # Fetch stored procedures from database
            procedures = self._fetch_procedures_from_database(incremental)

            if not procedures:
                logger.warning("No procedures fetched from database")
                return RefreshResult(
                    success=True,
                    total_procedures=0,
                    new_procedures=0,
                    updated_procedures=0,
                    unchanged_procedures=0,
                    failed_procedures=0,
                    errors=[],
                    duration_seconds=time.time() - start_time
                )

            # Convert to Parquet files (same format as extraction script)
            logger.info(f"Converting {len(procedures['objects'])} objects to Parquet format...")
            self._save_to_parquet_files(job_dir, procedures)

            duration = time.time() - start_time
            logger.info(f"✅ Database refresh completed in {duration:.1f}s")

            return RefreshResult(
                success=True,
                total_procedures=len(procedures.get('objects', [])),
                new_procedures=procedures.get('new_count', 0),
                updated_procedures=procedures.get('updated_count', 0),
                unchanged_procedures=procedures.get('unchanged_count', 0),
                failed_procedures=0,
                errors=[],
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Database refresh failed: {e}", exc_info=True)
            return RefreshResult(
                success=False,
                total_procedures=0,
                new_procedures=0,
                updated_procedures=0,
                unchanged_procedures=0,
                failed_procedures=0,
                errors=[str(e)],
                duration_seconds=duration
            )

    def refresh_metadata(self, incremental: bool = True) -> RefreshResult:
        """
        Refresh stored procedure metadata from database.

        Args:
            incremental: If True, only fetch changed procedures (faster)

        Returns:
            RefreshResult with success status and statistics
        """
        start_time = time.time()
        errors = []

        # Validate configuration
        if not self.settings.db.enabled:
            return RefreshResult(
                success=False,
                total_procedures=0,
                new_procedures=0,
                updated_procedures=0,
                unchanged_procedures=0,
                failed_procedures=0,
                errors=["Database connection not enabled (set DB_ENABLED=true in .env)"],
                duration_seconds=0
            )

        if not self.settings.db.connection_string:
            return RefreshResult(
                success=False,
                total_procedures=0,
                new_procedures=0,
                updated_procedures=0,
                unchanged_procedures=0,
                failed_procedures=0,
                errors=["Database connection string not configured"],
                duration_seconds=0
            )

        try:
            logger.info(f"🔄 Starting database metadata refresh (incremental={incremental})")

            # Create connector
            connector = get_connector(
                dialect=self.settings.sql_dialect,
                connection_string=self.settings.db.connection_string,
                timeout=self.settings.db.timeout
            )

            with connector:
                # Get list of all procedures
                logger.debug("Fetching list of stored procedures...")
                procedures_metadata = connector.list_procedures()

                if not procedures_metadata:
                    logger.warning("No stored procedures found in database")
                    return RefreshResult(
                        success=True,
                        total_procedures=0,
                        new_procedures=0,
                        updated_procedures=0,
                        unchanged_procedures=0,
                        failed_procedures=0,
                        errors=[],
                        duration_seconds=time.time() - start_time
                    )

                logger.info(f"Found {len(procedures_metadata)} stored procedures")

                # Load previous metadata for incremental refresh
                previous_hashes = self._load_metadata_cache() if incremental else {}

                # Fetch full source code for each procedure
                new_count = 0
                updated_count = 0
                unchanged_count = 0
                failed_count = 0
                all_procedures = []

                for i, metadata in enumerate(procedures_metadata, 1):
                    try:
                        # Check if procedure changed (incremental refresh)
                        if incremental and metadata.definition_hash:
                            previous_hash = previous_hashes.get(metadata.full_name)
                            if previous_hash == metadata.definition_hash:
                                logger.debug(f"[{i}/{len(procedures_metadata)}] {metadata.full_name}: Unchanged (skipped)")
                                unchanged_count += 1
                                continue

                        # Fetch full source code
                        logger.debug(f"[{i}/{len(procedures_metadata)}] Fetching {metadata.full_name}...")
                        procedure = connector.get_procedure_source(metadata.object_id)

                        # Track whether it's new or updated
                        if metadata.full_name in previous_hashes:
                            updated_count += 1
                            logger.info(f"  Updated: {metadata.full_name}")
                        else:
                            new_count += 1
                            logger.info(f"  New: {metadata.full_name}")

                        all_procedures.append(procedure)

                    except Exception as e:
                        failed_count += 1
                        error_msg = f"Failed to fetch {metadata.full_name}: {str(e)}"
                        logger.error(f"  ❌ {error_msg}")
                        errors.append(error_msg)
                        continue

                # Save metadata to files (same format as file upload)
                if all_procedures:
                    logger.info(f"Saving {len(all_procedures)} procedures to disk...")
                    self._save_procedures_to_files(all_procedures)

                    # Update metadata cache for incremental refresh
                    if incremental:
                        self._save_metadata_cache(procedures_metadata)

                duration = time.time() - start_time
                logger.info(
                    f"✅ Refresh completed in {duration:.1f}s: "
                    f"{new_count} new, {updated_count} updated, "
                    f"{unchanged_count} unchanged, {failed_count} failed"
                )

                return RefreshResult(
                    success=failed_count == 0,  # Success if no failures
                    total_procedures=len(procedures_metadata),
                    new_procedures=new_count,
                    updated_procedures=updated_count,
                    unchanged_procedures=unchanged_count,
                    failed_procedures=failed_count,
                    errors=errors,
                    duration_seconds=duration
                )

        except ConnectorError as e:
            duration = time.time() - start_time
            logger.error(f"❌ Database error: {e}")
            return RefreshResult(
                success=False,
                total_procedures=0,
                new_procedures=0,
                updated_procedures=0,
                unchanged_procedures=0,
                failed_procedures=0,
                errors=[f"Database error: {str(e)}"],
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Unexpected error during refresh: {e}", exc_info=True)
            return RefreshResult(
                success=False,
                total_procedures=0,
                new_procedures=0,
                updated_procedures=0,
                unchanged_procedures=0,
                failed_procedures=0,
                errors=[f"Unexpected error: {str(e)}"],
                duration_seconds=duration
            )

    def _load_metadata_cache(self) -> Dict[str, bytes]:
        """
        Load previous metadata cache for incremental refresh.

        Returns:
            Dictionary mapping procedure name to definition hash
        """
        try:
            if not self.metadata_cache_file.exists():
                return {}

            import json
            with open(self.metadata_cache_file, 'r') as f:
                data = json.load(f)

            # Convert hex strings back to bytes
            return {
                name: bytes.fromhex(hash_hex)
                for name, hash_hex in data.items()
            }

        except Exception as e:
            logger.warning(f"Failed to load metadata cache: {e}")
            return {}

    def _save_metadata_cache(self, procedures: List[StoredProcedureMetadata]):
        """Save metadata cache for next incremental refresh."""
        try:
            import json

            # Convert bytes to hex strings for JSON serialization
            cache = {
                proc.full_name: proc.definition_hash.hex()
                for proc in procedures
                if proc.definition_hash
            }

            with open(self.metadata_cache_file, 'w') as f:
                json.dump(cache, f, indent=2)

            logger.debug(f"Saved metadata cache ({len(cache)} procedures)")

        except Exception as e:
            logger.warning(f"Failed to save metadata cache: {e}")

    def _save_procedures_to_files(self, procedures: List[StoredProcedureMetadata]):
        """
        Save procedures to files in format expected by parser.

        Creates directory structure: stored_procedures/{schema}/{procedure}.sql
        """
        try:
            output_dir = Path("stored_procedures")
            output_dir.mkdir(exist_ok=True)

            for proc in procedures:
                # Create schema directory
                schema_dir = output_dir / proc.schema_name
                schema_dir.mkdir(exist_ok=True)

                # Save procedure to file
                file_path = schema_dir / f"{proc.procedure_name}.sql"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(proc.source_code)

                logger.debug(f"Saved: {file_path}")

            logger.info(f"✅ Saved {len(procedures)} procedures to {output_dir}/")

        except Exception as e:
            logger.error(f"Failed to save procedures to files: {e}")
            raise

    def _fetch_procedures_from_database(self, incremental: bool) -> Dict:
        """
        Fetch stored procedures from database using connector.

        Returns:
            Dictionary with objects, dependencies, and definitions data
        """
        import pandas as pd
        from engine.connectors import get_connector

        connector = get_connector(
            dialect=self.settings.sql_dialect,
            connection_string=self.settings.db.connection_string,
            timeout=self.settings.db.timeout
        )

        with connector:
            # Get list of all procedures
            procedures_list = connector.list_procedures()

            # Load previous metadata for incremental refresh
            previous_hashes = self._load_metadata_cache() if incremental else {}

            # Fetch full source code for each procedure
            new_count = 0
            updated_count = 0
            unchanged_count = 0
            objects_data = []
            definitions_data = []
            dependencies_data = []

            for i, metadata in enumerate(procedures_list, 1):
                try:
                    # Check if procedure changed (incremental)
                    if incremental and metadata.definition_hash:
                        previous_hash = previous_hashes.get(metadata.full_name)
                        if previous_hash == metadata.definition_hash:
                            unchanged_count += 1
                            continue

                    # Fetch full source
                    procedure = connector.get_procedure_source(metadata.object_id)

                    # Track new vs updated
                    if metadata.full_name in previous_hashes:
                        updated_count += 1
                    else:
                        new_count += 1

                    # Build objects row
                    objects_data.append({
                        'object_id': int(metadata.object_id) if metadata.object_id.isdigit() else hash(metadata.full_name),
                        'schema_name': procedure.schema_name,
                        'object_name': procedure.procedure_name,
                        'object_type': 'P'  # Stored Procedure
                    })

                    # Build definitions row
                    definitions_data.append({
                        'object_id': int(metadata.object_id) if metadata.object_id.isdigit() else hash(metadata.full_name),
                        'definition': procedure.source_code
                    })

                except Exception as e:
                    logger.error(f"Failed to fetch {metadata.full_name}: {e}")
                    continue

            # Save metadata cache for next incremental refresh
            if incremental:
                self._save_metadata_cache(procedures_list)

            return {
                'objects': pd.DataFrame(objects_data) if objects_data else pd.DataFrame(),
                'definitions': pd.DataFrame(definitions_data) if definitions_data else pd.DataFrame(),
                'dependencies': pd.DataFrame(),  # Empty for direct DB connection
                'new_count': new_count,
                'updated_count': updated_count,
                'unchanged_count': unchanged_count
            }

    def _save_to_parquet_files(self, job_dir: Path, procedures: Dict):
        """
        Save fetched data to Parquet files (same format as extraction script).

        Args:
            job_dir: Directory to save files (uploads/job_id/)
            procedures: Dictionary with DataFrames (objects, definitions, dependencies)
        """
        try:
            # Save objects.parquet
            if not procedures['objects'].empty:
                objects_path = job_dir / "objects.parquet"
                procedures['objects'].to_parquet(objects_path, index=False)
                logger.debug(f"Saved {objects_path} ({len(procedures['objects'])} rows)")

            # Save definitions.parquet
            if not procedures['definitions'].empty:
                definitions_path = job_dir / "definitions.parquet"
                procedures['definitions'].to_parquet(definitions_path, index=False)
                logger.debug(f"Saved {definitions_path} ({len(procedures['definitions'])} rows)")

            # Save dependencies.parquet (empty for direct DB connection)
            dependencies_path = job_dir / "dependencies.parquet"
            procedures['dependencies'].to_parquet(dependencies_path, index=False)
            logger.debug(f"Saved {dependencies_path} (0 rows - dependencies extracted during parsing)")

            logger.info(f"✅ Saved Parquet files to {job_dir}/")

        except Exception as e:
            logger.error(f"Failed to save Parquet files: {e}")
            raise
