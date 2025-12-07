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
from engine.config.settings import Settings

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

    def __init__(self, settings: Settings):
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
            # Clean up DuckDB workspace on full refresh (non-incremental) to ensure fresh start
            if not incremental:
                self._delete_duckdb_workspace()

            logger.info(f"🔄 Fetching metadata from database (incremental={incremental})")

            # Fetch stored procedures from database
            procedures = self._fetch_procedures_from_database(incremental)

            # Check if we got any objects (DataFrame with 0 rows returns False for bool(), so check length explicitly)
            objects_count = len(procedures.get('objects', [])) if procedures and 'objects' in procedures else 0

            if objects_count == 0:
                error_msg = "No objects found in database. Please verify database connection and that objects exist in the target database."
                logger.error(error_msg)
                return RefreshResult(
                    success=False,
                    total_procedures=0,
                    new_procedures=0,
                    updated_procedures=0,
                    unchanged_procedures=0,
                    failed_procedures=0,
                    errors=[error_msg],
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
        Fetch all object types from database using connector.

        Fetches:
        - Stored Procedures (P)
        - Tables (U)
        - Views (V)
        - Functions (FN, TF, IF)
        - Dependencies between objects

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
            objects_data = []
            definitions_data = []
            dependencies_data = []

            # Fetch stored procedures
            logger.info("Fetching stored procedures...")
            procedures_list = connector.list_procedures()
            for metadata in procedures_list:
                try:
                    procedure = connector.get_procedure_source(metadata.object_id)
                    obj_id = int(metadata.object_id) if metadata.object_id.isdigit() else hash(metadata.full_name)

                    objects_data.append({
                        'object_id': obj_id,
                        'schema_name': procedure.schema_name,
                        'object_name': procedure.procedure_name,
                        'object_type': 'Stored Procedure',  # Friendly name (not 'P' code)
                        'modify_date': procedure.modified_date or datetime.now()
                    })
                    definitions_data.append({
                        'object_id': obj_id,
                        'definition': procedure.source_code
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch procedure {metadata.full_name}: {e}")
                    continue

            # Fetch tables
            logger.info("Fetching user tables...")
            tables_list = connector.list_tables()
            for table in tables_list:
                try:
                    obj_id = int(table['object_id']) if table['object_id'].isdigit() else hash(f"{table['schema_name']}.{table['table_name']}")

                    objects_data.append({
                        'object_id': obj_id,
                        'schema_name': table['schema_name'],
                        'object_name': table['table_name'],
                        'object_type': 'Table',  # Friendly name (not 'U' code)
                        'modify_date': table['modify_date'] or datetime.now()
                    })
                    # Tables don't have source code definitions
                except Exception as e:
                    logger.warning(f"Failed to process table {table.get('schema_name', '?')}.{table.get('table_name', '?')}: {e}")
                    continue

            # Fetch views
            logger.info("Fetching user views...")
            views_list = connector.list_views()
            for view in views_list:
                try:
                    obj_id = int(view['object_id']) if view['object_id'].isdigit() else hash(f"{view['schema_name']}.{view['view_name']}")

                    objects_data.append({
                        'object_id': obj_id,
                        'schema_name': view['schema_name'],
                        'object_name': view['view_name'],
                        'object_type': 'View',  # Friendly name (not 'V' code)
                        'modify_date': view['modify_date'] or datetime.now()
                    })
                except Exception as e:
                    logger.warning(f"Failed to process view {view.get('schema_name', '?')}.{view.get('view_name', '?')}: {e}")
                    continue

            # Fetch functions
            logger.info("Fetching user-defined functions...")
            functions_list = connector.list_functions()
            for func in functions_list:
                try:
                    obj_id = int(func['object_id']) if func['object_id'].isdigit() else hash(f"{func['schema_name']}.{func['function_name']}")

                    # All functions use friendly name 'Function' regardless of subtype
                    # (Scalar, Table-Valued, Inline all treated as 'Function')
                    object_type = 'Function'

                    objects_data.append({
                        'object_id': obj_id,
                        'schema_name': func['schema_name'],
                        'object_name': func['function_name'],
                        'object_type': object_type,
                        'modify_date': func['modify_date'] or datetime.now()
                    })
                except Exception as e:
                    logger.warning(f"Failed to process function {func.get('schema_name', '?')}.{func.get('function_name', '?')}: {e}")
                    continue

            # 4. Fetch definitions
            logger.info("Fetching object definitions...")
            definitions_data_from_connector = connector.list_definitions() if hasattr(connector, 'list_definitions') else []
            
            # Construct definitions dataframe from source code in objects if needed
            definitions_list = []
            if not definitions_data_from_connector:
                for metadata in procedures_list:
                    try:
                        procedure = connector.get_procedure_source(metadata.object_id)
                        if procedure.source_code:
                            obj_id = int(metadata.object_id) if metadata.object_id.isdigit() else hash(metadata.full_name)
                            definitions_list.append({
                                'object_id': obj_id,
                                'definition': procedure.source_code
                            })
                    except Exception as e:
                        logger.warning(f"Failed to get source for procedure {metadata.full_name} for definitions: {e}")
                
                for view in views_list:
                    if 'source_code' in view and view['source_code']:
                        obj_id = int(view['object_id']) if view['object_id'].isdigit() else hash(f"{view['schema_name']}.{view['view_name']}")
                        definitions_list.append({
                            'object_id': obj_id,
                            'definition': view['source_code']
                        })

                for func in functions_list:
                    if 'source_code' in func and func['source_code']:
                        obj_id = int(func['object_id']) if func['object_id'].isdigit() else hash(f"{func['schema_name']}.{func['function_name']}")
                        definitions_list.append({
                            'object_id': obj_id,
                            'definition': func['source_code']
                        })
            else:
                 definitions_list = definitions_data_from_connector

            # 5. Fetch table columns (New in 4.5.3)
            logger.info("Fetching table columns...")
            columns_list = connector.list_table_columns() if hasattr(connector, 'list_table_columns') else []
            
            # 6. Fetch query logs (New in 4.5.3)
            logger.info("Fetching query logs...")
            query_logs_list = connector.extract_query_logs() if hasattr(connector, 'extract_query_logs') else []

            # 7. Fetch dependencies
            logger.info("Fetching object dependencies...")
            try:
                dependencies_list = connector.list_dependencies()
                for dep in dependencies_list:
                    try:
                        # Store ALL dependencies from SQL Server with correct schema
                        # Schema matches DATA_CONTRACTS.md: referencing_object_id, referenced_object_id,
                        # referenced_schema_name, referenced_entity_name
                        dependencies_data.append({
                            'referencing_object_id': dep['referencing_id'],
                            'referenced_object_id': dep['referenced_id'],
                            'referenced_schema_name': dep['referenced_schema'],
                            'referenced_entity_name': dep['referenced_object']
                        })
                    except Exception as e:
                        logger.warning(f"Failed to process dependency: {e}")
                        continue

                logger.info(f"Fetched {len(dependencies_data)} dependencies from sys.sql_expression_dependencies")
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch dependencies (optional): {e}")
                # Dependencies are optional - continue without them

            # Count by object type
            object_counts = {}
            for obj in objects_data:
                obj_type = obj['object_type']
                object_counts[obj_type] = object_counts.get(obj_type, 0) + 1

            # Map friendly names to plural forms for response message
            type_names = {
                'Stored Procedure': 'Stored Procedures',
                'Table': 'Tables',
                'View': 'Views',
                'Function': 'Functions'
            }

            count_str = ", ".join([
                f"{count} {type_names.get(obj_type, obj_type)}"
                for obj_type, count in sorted(object_counts.items())
            ])

            logger.info(f"Fetched {len(objects_data)} total objects: {count_str} with {len(dependencies_data)} dependencies")

            # Create DataFrames with explicit schema for dependencies (even if empty)
            # This ensures the parquet file has the correct schema for validation
            if dependencies_data and len(dependencies_data) > 0:
                dependencies_df = pd.DataFrame(dependencies_data)
            else:
                # Create empty DataFrame with correct schema per DATA_CONTRACTS.md
                dependencies_df = pd.DataFrame(columns=['referencing_object_id', 'referenced_object_id', 'referenced_schema_name', 'referenced_entity_name'])

            return {
                'objects': pd.DataFrame(objects_data) if objects_data else pd.DataFrame(),
                'definitions': pd.DataFrame(definitions_list) if definitions_list else pd.DataFrame(),
                'dependencies': pd.DataFrame(dependencies_data) if dependencies_data else pd.DataFrame(columns=['referencing_object_id', 'referenced_object_id', 'referenced_schema_name', 'referenced_entity_name']),
                'table_columns': pd.DataFrame(columns_list) if columns_list else pd.DataFrame(),
                'query_logs': pd.DataFrame(query_logs_list) if query_logs_list else pd.DataFrame(),
                'refresh_timestamp': datetime.utcnow(),
                'new_count': len(objects_data),  # All are "new" in direct DB connection
                'updated_count': 0,
                'unchanged_count': 0
            }

    def _delete_duckdb_workspace(self):
        """
        Delete DuckDB workspace to ensure clean start on full refresh.

        This is called when switching data sources (e.g., Parquet to Database import)
        to prevent stale data from previous imports from affecting the new import.
        """
        try:
            workspace_path = Path("lineage_workspace.duckdb")
            if workspace_path.exists():
                workspace_path.unlink()
                logger.info(f"✅ Deleted DuckDB workspace: {workspace_path}")
            else:
                logger.debug("DuckDB workspace not found (first import)")
        except Exception as e:
            logger.warning(f"Failed to delete DuckDB workspace: {e}")
            # Don't fail the refresh if we can't delete - it's not critical

    def _save_to_parquet_files(self, job_dir: Path, procedures: Dict):
        """
        Save fetched data to Parquet files (same format as extraction script).

        Args:
            job_dir: Directory to save files (uploads/job_id/)
            procedures: Dictionary with DataFrames (objects, definitions, dependencies)
        """
        import pandas as pd

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

            # Save dependencies.parquet (may be empty for direct DB connection)
            dependencies_path = job_dir / "dependencies.parquet"
            # Ensure dependencies DataFrame has correct schema even if empty
            if procedures['dependencies'].empty:
                # Create empty DataFrame with schema per DATA_CONTRACTS.md
                procedures['dependencies'] = pd.DataFrame(columns=['referencing_object_id', 'referenced_object_id', 'referenced_schema_name', 'referenced_entity_name'])
            procedures['dependencies'].to_parquet(dependencies_path, index=False)
            logger.debug(f"Saved {dependencies_path} ({len(procedures['dependencies'])} rows - dependencies extracted during parsing)")

            logger.debug(f"Saved {dependencies_path} ({len(procedures['dependencies'])} rows - dependencies extracted during parsing)")

            # Save table_columns.parquet (optional)
            if 'table_columns' in procedures and not procedures['table_columns'].empty:
                columns_path = job_dir / "table_columns.parquet"
                procedures['table_columns'].to_parquet(columns_path, index=False)
                logger.debug(f"Saved {columns_path} ({len(procedures['table_columns'])} rows)")

            # Save query_logs.parquet (optional)
            if 'query_logs' in procedures and not procedures['query_logs'].empty:
                logs_path = job_dir / "query_logs.parquet"
                procedures['query_logs'].to_parquet(logs_path, index=False)
                logger.debug(f"Saved {logs_path} ({len(procedures['query_logs'])} rows)")

            logger.info(f"✅ Saved Parquet files to {job_dir}/")

        except Exception as e:
            logger.error(f"Failed to save Parquet files: {e}")
            raise
