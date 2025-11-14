"""
Background task processing for lineage parser.

Wraps existing lineage_v3 pipeline for web-based execution.
"""

import sys
import json
import time
import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import pyarrow.parquet as pq

# Setup logging
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core import DuckDBWorkspace, GapDetector
from lineage_v3.parsers import QualityAwareParser
from lineage_v3.output import InternalFormatter, FrontendFormatter, SummaryFormatter
from lineage_v3.utils.confidence_calculator import ConfidenceCalculator


class LineageProcessor:
    """
    Processes lineage from uploaded Parquet files.

    Wraps the existing lineage_v3 pipeline without modifications.
    """

    def __init__(self, job_dir: Path, data_dir: Optional[Path] = None, incremental: bool = True):
        """
        Initialize processor for a specific job.

        Args:
            job_dir: Directory containing uploaded Parquet files
            data_dir: Directory for persistent data storage (default: ./data)
            incremental: If True, only re-parse modified objects (default: True)
        """
        self.job_dir = job_dir
        self.data_dir = data_dir or Path("./data")
        self.incremental = incremental
        self.status_file = job_dir / "status.json"
        self.result_file = job_dir / "result.json"
        # Use persistent workspace in data directory (not job directory)
        # This allows DDL queries after job cleanup
        self.workspace_file = self.data_dir / "lineage_workspace.duckdb"
        self.start_time = time.time()

    def validate_parquet_files(self) -> Tuple[bool, List[str], List[str], Dict[str, Path]]:
        """
        Validate uploaded Parquet files by schema analysis (DQ check).

        Auto-detects file types by schema (works with any filename).
        No renaming - returns file mappings for direct loading.

        Returns:
            Tuple of (is_valid, errors, warnings, file_mappings)
            file_mappings: Dict mapping file_type -> actual filepath
        """
        errors = []
        warnings = []

        # Required files with expected column patterns
        # Order matters: more specific patterns first (definitions has both object_id AND definition)
        required_files = {
            'definitions': ['object_id', 'definition'],  # Check this first - most specific
            'dependencies': ['referencing_object_id', 'referenced_object_id'],
            'objects': ['object_id', 'schema_name', 'object_name', 'object_type']
        }

        # Find all parquet files
        parquet_files = list(self.job_dir.glob('*.parquet'))

        if not parquet_files:
            errors.append("No Parquet files found")
            return (False, errors, warnings, {})

        # Try to identify files by their schema (DQ check)
        identified = {}
        unidentified = []

        for filepath in parquet_files:
            try:
                # Read schema
                parquet_file = pq.ParquetFile(filepath)
                schema = parquet_file.schema_arrow
                column_names = [field.name.lower() for field in schema]

                # Try to match to required files
                matched = False
                for file_type, expected_columns in required_files.items():
                    # Check if expected columns exist
                    if all(col.lower() in column_names for col in expected_columns):
                        if file_type in identified:
                            warnings.append(f"Multiple files detected for '{file_type}' type. Using: {filepath.name}")
                        identified[file_type] = filepath
                        matched = True
                        break

                if not matched:
                    # Check if it might be query_logs (optional)
                    if 'request_id' in column_names or 'command' in column_names:
                        identified['query_logs'] = filepath
                    # Check if it might be table_columns (optional)
                    elif 'column_name' in column_names and 'data_type' in column_names:
                        identified['table_columns'] = filepath
                    else:
                        unidentified.append(filepath.name)

            except Exception as e:
                errors.append(f"Cannot read {filepath.name}: {str(e)}")

        # Check for missing required files
        for file_type in required_files.keys():
            if file_type not in identified:
                errors.append(f"Missing required file type: '{file_type}' (expected columns: {', '.join(required_files[file_type])})")

        # Warnings for unidentified files
        if unidentified:
            warnings.append(f"Unrecognized files (will be ignored): {', '.join(unidentified)}")

        # If optional files are missing, add warnings
        if 'query_logs' not in identified:
            warnings.append("Optional 'query_logs' file not provided (confidence scores may be lower)")
        if 'table_columns' not in identified:
            warnings.append("Optional 'table_columns' file not provided (table DDL info will not be available)")

        is_valid = len(errors) == 0
        return (is_valid, errors, warnings, identified)

    def update_status(
        self,
        status: str,
        progress: float = 0.0,
        current_step: str = "",
        message: str = "",
        include_stats: bool = False
    ) -> None:
        """
        Update job status file for frontend polling.

        Args:
            status: Job status ('processing', 'completed', 'error', 'failed')
            progress: Progress percentage (0.0-100.0)
            current_step: Current processing step description
            message: Detailed message
            include_stats: If True, query DuckDB for live confidence stats
        """
        elapsed = time.time() - self.start_time

        status_data = {
            "status": status,
            "progress": round(progress, 1),  # Round to 1 decimal place
            "current_step": current_step,
            "elapsed_seconds": elapsed,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Estimate remaining time (simple linear estimate)
        if progress > 0 and progress < 100:
            estimated_total = elapsed / (progress / 100)
            status_data["estimated_remaining_seconds"] = estimated_total - elapsed

        # Add real-time confidence stats if requested
        if include_stats:
            try:
                stats = self._get_current_confidence_stats()
                if stats:
                    status_data["stats"] = stats
            except Exception as e:
                logger.warning(f"Failed to get confidence stats: {e}")

        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

    def _get_current_confidence_stats(self) -> Optional[Dict[str, int]]:
        """
        Get current confidence statistics from DuckDB.

        Returns:
            {
                'total_objects': int,
                'high_confidence': int,
                'medium_confidence': int,
                'low_confidence': int
            } or None if lineage_metadata doesn't exist
        """
        if not hasattr(self, 'db') or not self.db:
            return None

        try:
            # Check if lineage_metadata exists
            tables = [row[0] for row in self.db.query("SHOW TABLES")]
            if 'lineage_metadata' not in tables:
                return None

            # Query confidence distribution
            query = """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN confidence >= 0.85 THEN 1 END) as high_conf,
                COUNT(CASE WHEN confidence >= 0.75 AND confidence < 0.85 THEN 1 END) as med_conf,
                COUNT(CASE WHEN confidence < 0.75 THEN 1 END) as low_conf
            FROM lineage_metadata
            """

            result = self.db.query(query)
            if result:
                row = result[0]
                return {
                    'total_objects': row[0],
                    'high_confidence': row[1],
                    'medium_confidence': row[2],
                    'low_confidence': row[3]
                }
        except Exception as e:
            logger.error(f"Error querying confidence stats: {e}")
            return None

        return None

    def process(self) -> Dict:
        """
        Execute the lineage pipeline.

        Returns:
            Dict containing final lineage data and summary
        """
        # Timing instrumentation
        step_times = {}
        step_start = time.time()

        try:
            # Step 0: Validate files (DQ check)
            self.update_status("processing", 0, "Validating files", "Checking Parquet file structure...")

            is_valid, errors, warnings, file_mappings = self.validate_parquet_files()
            step_times['validate'] = time.time() - step_start
            step_start = time.time()

            if not is_valid:
                error_result = {
                    "status": "failed",
                    "errors": errors,
                    "warnings": warnings,
                    "data": None,
                    "summary": None
                }

                with open(self.result_file, 'w') as f:
                    json.dump(error_result, f, indent=2)

                # Update status with errors and warnings
                status_data = {
                    "status": "failed",
                    "progress": 0,
                    "current_step": "Validation failed",
                    "elapsed_seconds": time.time() - self.start_time,
                    "message": f"File validation failed",
                    "errors": errors,
                    "warnings": warnings,
                    "updated_at": datetime.utcnow().isoformat()
                }
                with open(self.status_file, 'w') as f:
                    json.dump(status_data, f, indent=2)

                return error_result

            # Show warnings if any
            if warnings:
                self.update_status("processing", 5, "Validation complete", f"Warnings: {'; '.join(warnings)}")

            # Step 1: Initialize DuckDB workspace and conditionally truncate tables
            mode_text = "incremental" if self.incremental else "full refresh"
            self.update_status("processing", 8, "Preparing workspace", f"Initializing workspace in {mode_text} mode...")

            with DuckDBWorkspace(workspace_path=str(self.workspace_file)) as db:
                # Conditionally truncate data tables and delete persistent JSON
                if not self.incremental:
                    # Full refresh: truncate all data tables INCLUDING lineage_metadata
                    # This ensures a clean slate for re-parsing with updated parser logic
                    tables_to_truncate = ['objects', 'dependencies', 'definitions', 'query_logs', 'table_columns', 'lineage_metadata']
                    for table_name in tables_to_truncate:
                        try:
                            db.connection.execute(f"DROP TABLE IF EXISTS {table_name}")
                        except Exception as e:
                            # Table might not exist yet, ignore
                            pass

                    # Recreate lineage_metadata table after dropping it
                    # This is necessary because we dropped it above but still need it for parsing
                    db._initialize_schema()

                    # Also delete the persistent frontend JSON file
                    latest_data_file = self.data_dir / "latest_frontend_lineage.json"
                    if latest_data_file.exists():
                        try:
                            latest_data_file.unlink()
                            logger.info("Deleted existing frontend data file (full refresh mode)")
                        except Exception as e:
                            logger.warning(f"Failed to delete frontend data file: {e}")
                # Incremental mode: don't truncate tables, lineage_metadata persists!

                # Step 2: Load Parquet files using detected mappings
                self.update_status("processing", 10, "Loading Parquet files", "Ingesting DMV data...")
                row_counts = db.load_parquet_from_mappings(file_mappings)
                step_times['load_parquet'] = time.time() - step_start
                step_start = time.time()

                # Verify files loaded
                if not row_counts or sum(row_counts.values()) == 0:
                    raise Exception("No data loaded from Parquet files")

                # Get objects to parse (use incremental flag)
                objects_to_parse = db.get_objects_to_parse(full_refresh=not self.incremental)
                total_objects = len(objects_to_parse)

                if self.incremental:
                    self.update_status("processing", 15, "Incremental mode",
                                     f"Detected {total_objects} objects needing update (modified or new)")
                else:
                    self.update_status("processing", 15, "Full refresh mode",
                                     f"Processing all {total_objects} objects")

                # Step 2: Load DMV Dependencies (Views)
                self.update_status("processing", 20, "Loading DMV dependencies",
                                 f"Processing {total_objects} objects...", include_stats=True)

                views_with_dmv = db.query("""
                    SELECT DISTINCT
                        d.referencing_object_id,
                        o.object_name,
                        o.modify_date
                    FROM dependencies d
                    JOIN objects o ON d.referencing_object_id = o.object_id
                    WHERE o.object_type = 'View'
                """)

                if views_with_dmv:
                    for view in views_with_dmv:
                        view_id, view_name, modify_date = view

                        # Get all dependencies for this view
                        deps = db.query("""
                            SELECT
                                referenced_object_id,
                                referenced_schema_name,
                                referenced_entity_name
                            FROM dependencies
                            WHERE referencing_object_id = ?
                        """, [view_id])

                        # Extract input object_ids
                        inputs = [dep[0] for dep in deps if dep[0] is not None]
                        outputs = []

                        # Store in lineage_metadata
                        db.update_metadata(
                            object_id=view_id,
                            modify_date=modify_date,
                            primary_source='dmv',
                            confidence=1.0,
                            inputs=inputs,
                            outputs=outputs
                        )

                # Step 3: Detect gaps
                self.update_status("processing", 30, "Detecting gaps", "Identifying missing dependencies...", include_stats=True)

                gap_detector = GapDetector(db)
                gaps = gap_detector.detect_gaps()

                # Step 4: Parse Stored Procedures (respecting incremental mode)
                self.update_status("processing", 40, "Parsing stored procedures", "Analyzing SQL definitions...", include_stats=True)

                # Filter objects_to_parse for SPs only
                sps_to_parse = [obj for obj in objects_to_parse if obj['object_type'] == 'Stored Procedure']

                if sps_to_parse:
                    parser = QualityAwareParser(db)

                    for i, sp_dict in enumerate(sps_to_parse):
                        # Update progress (with stats every 10 SPs or at end)
                        sp_progress = 40 + (40 * (i + 1) / len(sps_to_parse))  # 40% to 80%
                        include_stats = (i + 1) % 10 == 0 or (i + 1) == len(sps_to_parse)
                        self.update_status(
                            "processing",
                            sp_progress,
                            f"Parsing stored procedures ({i+1}/{len(sps_to_parse)})",
                            f"Analyzing {sp_dict['schema_name']}.{sp_dict['object_name']}...",
                            include_stats=include_stats
                        )

                        try:
                            # Parse with QualityAwareParser
                            result = parser.parse_object(sp_dict['object_id'])

                            # Persist result to lineage_metadata
                            db.update_metadata(
                                object_id=sp_dict['object_id'],
                                modify_date=sp_dict['modify_date'],
                                primary_source=result.get('primary_source', 'parser'),
                                confidence=result['confidence'],
                                inputs=result.get('inputs', []),
                                outputs=result.get('outputs', [])
                            )
                        except Exception as e:
                            # Log parsing failure and continue with next SP
                            logger.error(
                                f"Failed to parse SP {sp_dict['schema_name']}.{sp_dict['object_name']} "
                                f"(object_id={sp_dict['object_id']}): {e}",
                                exc_info=True
                            )
                            # Store failure in metadata for visibility
                            try:
                                db.update_metadata(
                                    object_id=sp_dict['object_id'],
                                    modify_date=sp_dict['modify_date'],
                                    primary_source='parser',
                                    confidence=0.0,
                                    inputs=[],
                                    outputs=[],
                                    parse_failure_reason=f"Parser error: {str(e)[:200]}"
                                )
                            except Exception as meta_error:
                                logger.error(f"Failed to store error metadata: {meta_error}")

                step_times['parse_sps'] = time.time() - step_start
                step_start = time.time()

                # Step 5: Build Bidirectional Graph (Reverse Lookup)
                self.update_status("processing", 85, "Building graph relationships",
                                 "Establishing bidirectional connections...", include_stats=True)

                # Check if lineage_metadata exists before querying
                tables = db.query("SHOW TABLES")
                table_names = [row[0] for row in tables]

                if 'lineage_metadata' in table_names:
                    parsed_objects = db.query("""
                        SELECT object_id, inputs, outputs
                        FROM lineage_metadata
                        WHERE inputs IS NOT NULL OR outputs IS NOT NULL
                    """)
                else:
                    # No metadata table yet (shouldn't happen but defensive)
                    parsed_objects = []

                # Build reverse lookup map
                reverse_inputs = {}
                reverse_outputs = {}

                for row in parsed_objects:
                    obj_id, inputs_json, outputs_json = row

                    if inputs_json:
                        inputs = json.loads(inputs_json)
                        for input_id in inputs:
                            if input_id not in reverse_inputs:
                                reverse_inputs[input_id] = []
                            reverse_inputs[input_id].append(obj_id)

                    if outputs_json:
                        outputs = json.loads(outputs_json)
                        for output_id in outputs:
                            if output_id not in reverse_outputs:
                                reverse_outputs[output_id] = []
                            reverse_outputs[output_id].append(obj_id)

                # Update Tables/Views with reverse dependencies
                # IMPORTANT: Only update Tables and Views, NOT Stored Procedures
                # SPs must be parsed to extract their dependencies
                for table_id, readers in reverse_inputs.items():
                    # Get object type for this object_id
                    obj_type_result = db.query("""
                        SELECT object_type FROM objects WHERE object_id = ?
                    """, [table_id])

                    if not obj_type_result:
                        continue

                    obj_type = obj_type_result[0][0]

                    # Only update Tables and Views (not SPs)
                    if obj_type in ['Table', 'View']:
                        db.update_metadata(
                            object_id=table_id,
                            modify_date=None,
                            primary_source='metadata',
                            confidence=1.0,
                            inputs=reverse_outputs.get(table_id, []),
                            outputs=readers
                        )

                # CRITICAL FIX: Ensure ALL tables/views have metadata entries
                # Even unreferenced tables need confidence=1.0 for accurate stats
                all_tables_views = db.query("""
                    SELECT object_id
                    FROM objects
                    WHERE object_type IN ('Table', 'View')
                """)

                tables_in_metadata = set(reverse_inputs.keys()) | set(reverse_outputs.keys())

                for row in all_tables_views:
                    table_id = row[0]
                    if table_id not in tables_in_metadata:
                        # Unreferenced table/view - add with confidence=1.0
                        db.update_metadata(
                            object_id=table_id,
                            modify_date=None,
                            primary_source='metadata',
                            confidence=1.0,
                            inputs=[],
                            outputs=[]
                        )

                # Step 6: Generate output JSON files
                self.update_status("processing", 90, "Generating output", "Creating lineage JSON...")

                # Generate internal lineage.json
                internal_formatter = InternalFormatter(db)
                internal_stats = internal_formatter.generate(
                    output_path=str(self.job_dir / "lineage.json")
                )

                # Generate summary
                summary_formatter = SummaryFormatter(db)
                summary = summary_formatter.generate(
                    output_path=str(self.job_dir / "lineage_summary.json")
                )

                # Load internal lineage for frontend conversion
                with open(self.job_dir / "lineage.json", 'r') as f:
                    internal_lineage = json.load(f)

                # Generate frontend lineage.json (without DDL for performance)
                # DDL will be fetched on-demand via /api/ddl/{object_id} endpoint
                frontend_formatter = FrontendFormatter(db)
                frontend_stats = frontend_formatter.generate(
                    internal_lineage,
                    output_path=str(self.job_dir / "frontend_lineage.json"),
                    include_ddl=False  # Performance optimization: fetch DDL on demand
                )

                # Load results for response
                with open(self.job_dir / "frontend_lineage.json", 'r') as f:
                    frontend_lineage = json.load(f)

                with open(self.job_dir / "lineage_summary.json", 'r') as f:
                    lineage_summary = json.load(f)

                step_times['output_generation'] = time.time() - step_start
                step_start = time.time()

                # Copy frontend JSON to persistent storage for /api/latest-data endpoint
                try:
                    self.data_dir.mkdir(parents=True, exist_ok=True)
                    persistent_file = self.data_dir / "latest_frontend_lineage.json"
                    shutil.copy2(
                        self.job_dir / "frontend_lineage.json",
                        persistent_file
                    )
                    logger.info(f"✅ Saved latest data to {persistent_file}")
                except Exception as e:
                    logger.error(f"⚠️  Failed to save to persistent storage: {e}")
                    # Don't fail the job if persistent save fails

                # Prepare result
                result = {
                    "status": "completed",
                    "data": frontend_lineage,
                    "summary": lineage_summary,
                    "statistics": {
                        "total_nodes": frontend_stats['total_nodes'],
                        "coverage": summary['coverage'],
                        "parsed_objects": summary['parsed_objects']
                    }
                }

                # Save result to file
                with open(self.result_file, 'w') as f:
                    json.dump(result, f, indent=2)

                # Update final status
                self.update_status("completed", 100, "Complete", "Lineage analysis finished successfully")

                return result

        except Exception as e:
            # Save error state
            error_msg = str(e)
            error_result = {
                "status": "failed",
                "errors": [error_msg],
                "data": None,
                "summary": None
            }

            with open(self.result_file, 'w') as f:
                json.dump(error_result, f, indent=2)

            self.update_status("failed", 0, "Error", f"Processing failed: {error_msg}")

            return error_result


def process_lineage_job(job_id: str, job_dir: Path, data_dir: Optional[Path] = None, incremental: bool = True) -> Dict:
    """
    Background task entry point for processing lineage.

    Args:
        job_id: Unique job identifier
        job_dir: Directory containing uploaded Parquet files
        data_dir: Directory for persistent data storage (default: ./data)
        incremental: If True, only re-parse modified objects (default: True)

    Returns:
        Dict containing lineage results or error information
    """
    processor = LineageProcessor(job_dir, data_dir=data_dir, incremental=incremental)
    return processor.process()
