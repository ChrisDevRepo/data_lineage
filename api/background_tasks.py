"""
Background task processing for lineage parser.

Wraps existing lineage_v3 pipeline for web-based execution.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core import DuckDBWorkspace, GapDetector
from lineage_v3.parsers import DualParser
from lineage_v3.output import InternalFormatter, FrontendFormatter, SummaryFormatter


class LineageProcessor:
    """
    Processes lineage from uploaded Parquet files.

    Wraps the existing lineage_v3 pipeline without modifications.
    """

    def __init__(self, job_dir: Path):
        """
        Initialize processor for a specific job.

        Args:
            job_dir: Directory containing uploaded Parquet files
        """
        self.job_dir = job_dir
        self.status_file = job_dir / "status.json"
        self.result_file = job_dir / "result.json"
        self.workspace_file = job_dir / "lineage_workspace.duckdb"
        self.start_time = time.time()

    def update_status(
        self,
        status: str,
        progress: float = 0.0,
        current_step: str = "",
        message: str = ""
    ):
        """Update job status file for frontend polling"""
        elapsed = time.time() - self.start_time

        status_data = {
            "status": status,
            "progress": progress,
            "current_step": current_step,
            "elapsed_seconds": elapsed,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Estimate remaining time (simple linear estimate)
        if progress > 0 and progress < 100:
            estimated_total = elapsed / (progress / 100)
            status_data["estimated_remaining_seconds"] = estimated_total - elapsed

        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

    def process(self) -> Dict:
        """
        Execute the lineage pipeline.

        Returns:
            Dict containing final lineage data and summary
        """
        try:
            self.update_status("processing", 0, "Initializing workspace", "Starting lineage analysis...")

            # Step 1: Initialize DuckDB workspace and load Parquet files
            self.update_status("processing", 10, "Loading Parquet files", "Ingesting DMV data...")

            with DuckDBWorkspace(workspace_path=str(self.workspace_file)) as db:
                # Load Parquet files
                row_counts = db.load_parquet(str(self.job_dir), full_refresh=True)

                # Verify files loaded
                if not row_counts or sum(row_counts.values()) == 0:
                    raise Exception("No data loaded from Parquet files")

                # Get objects to parse
                objects_to_parse = db.get_objects_to_parse(full_refresh=True)
                total_objects = len(objects_to_parse)

                # Step 2: Load DMV Dependencies (Views)
                self.update_status("processing", 20, "Loading DMV dependencies",
                                 f"Processing {total_objects} objects...")

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
                self.update_status("processing", 30, "Detecting gaps", "Identifying missing dependencies...")

                gap_detector = GapDetector(db)
                gaps = gap_detector.detect_gaps()

                # Step 4: Parse ALL Stored Procedures with Dual-Parser
                self.update_status("processing", 40, "Parsing stored procedures", "Analyzing SQL definitions...")

                all_sps = db.query("""
                    SELECT object_id, schema_name, object_name, modify_date
                    FROM objects
                    WHERE object_type = 'Stored Procedure'
                    ORDER BY schema_name, object_name
                """)

                if all_sps:
                    dual_parser = DualParser(db)

                    for i, sp in enumerate(all_sps):
                        # Update progress
                        sp_progress = 40 + (40 * (i + 1) / len(all_sps))  # 40% to 80%
                        self.update_status(
                            "processing",
                            sp_progress,
                            f"Parsing stored procedures ({i+1}/{len(all_sps)})",
                            f"Analyzing {sp[1]}.{sp[2]}..."
                        )

                        try:
                            # Parse with dual-parser
                            result = dual_parser.parse_object(sp[0])

                            # Persist result to lineage_metadata
                            db.update_metadata(
                                object_id=sp[0],
                                modify_date=sp[3],
                                primary_source=result.get('source', 'dual_parser'),
                                confidence=result['confidence'],
                                inputs=result.get('inputs', []),
                                outputs=result.get('outputs', [])
                            )
                        except Exception as e:
                            # Continue even if one SP fails
                            pass

                # Step 5: Build Bidirectional Graph (Reverse Lookup)
                self.update_status("processing", 85, "Building graph relationships",
                                 "Establishing bidirectional connections...")

                parsed_objects = db.query("""
                    SELECT object_id, inputs, outputs
                    FROM lineage_metadata
                    WHERE inputs IS NOT NULL OR outputs IS NOT NULL
                """)

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
                for table_id, readers in reverse_inputs.items():
                    db.update_metadata(
                        object_id=table_id,
                        modify_date=None,
                        primary_source='metadata',
                        confidence=1.0,
                        inputs=reverse_outputs.get(table_id, []),
                        outputs=readers
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

                # Generate frontend lineage.json
                frontend_formatter = FrontendFormatter(db)
                frontend_stats = frontend_formatter.generate(
                    internal_lineage,
                    output_path=str(self.job_dir / "frontend_lineage.json")
                )

                # Load results for response
                with open(self.job_dir / "frontend_lineage.json", 'r') as f:
                    frontend_lineage = json.load(f)

                with open(self.job_dir / "lineage_summary.json", 'r') as f:
                    lineage_summary = json.load(f)

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


def process_lineage_job(job_id: str, job_dir: Path) -> Dict:
    """
    Background task entry point for processing lineage.

    Args:
        job_id: Unique job identifier
        job_dir: Directory containing uploaded Parquet files

    Returns:
        Dict containing lineage results or error information
    """
    processor = LineageProcessor(job_dir)
    return processor.process()
