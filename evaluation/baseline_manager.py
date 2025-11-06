"""
Baseline Manager for sub_DL_OptimizeParsing

Handles baseline snapshot creation, loading, and updates.
Baselines store frozen DDL + verified dependencies for comparison.

Author: Claude Code Agent
Date: 2025-11-02
Version: 1.0
"""

import duckdb
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from evaluation.schemas import (
    initialize_baseline_db,
    BASELINE_CHANGE_LOG_SCHEMA
)

logger = logging.getLogger(__name__)


class BaselineManager:
    """
    Manages baseline snapshots for evaluation.

    A baseline is a frozen snapshot of:
    - Object DDLs (SHA256 hashed for change detection)
    - Expected dependencies (inputs/outputs from high-confidence production run)

    Baselines are stored in separate DuckDB files for isolation and portability.
    """

    def __init__(self, baseline_dir: Path):
        """
        Initialize baseline manager.

        Args:
            baseline_dir: Directory containing baseline databases
                         (e.g., evaluation_baselines/)
        """
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def create_baseline(
        self,
        name: str,
        production_workspace_path: Path,
        parser_version: str = "v3.7.0",
        description: str = ""
    ) -> int:
        """
        Create new baseline from production workspace.

        Extracts all Stored Procedure DDLs and current high-confidence
        dependencies from production lineage_workspace.duckdb.

        Args:
            name: Baseline name (e.g., 'baseline_v3.7.0')
            production_workspace_path: Path to lineage_workspace.duckdb
            parser_version: Parser version string
            description: Optional description

        Returns:
            Number of objects captured in baseline

        Raises:
            FileNotFoundError: If production workspace doesn't exist
            RuntimeError: If baseline creation fails
        """
        prod_workspace = Path(production_workspace_path)
        if not prod_workspace.exists():
            raise FileNotFoundError(f"Production workspace not found: {prod_workspace}")

        baseline_db_path = self.baseline_dir / f"{name}.duckdb"

        if baseline_db_path.exists():
            logger.warning(f"Baseline {name} already exists, will be overwritten")
            baseline_db_path.unlink()

        try:
            # Connect to production workspace (read-only)
            prod_conn = duckdb.connect(str(prod_workspace), read_only=True)

            # Create baseline database
            baseline_conn = duckdb.connect(str(baseline_db_path))
            initialize_baseline_db(baseline_conn)

            # Extract objects (Stored Procedures only)
            query_objects = """
                SELECT
                    o.object_id,
                    o.object_name,
                    o.schema_name,
                    o.object_type,
                    d.definition as ddl_text
                FROM objects o
                JOIN definitions d ON o.object_id = d.object_id
                WHERE o.object_type = 'Stored Procedure'
                ORDER BY o.schema_name, o.object_name
            """

            objects = prod_conn.execute(query_objects).fetchall()

            if not objects:
                raise RuntimeError("No Stored Procedures found in production workspace")

            # Extract expected dependencies from lineage_metadata
            query_lineage = """
                SELECT
                    object_id,
                    inputs,
                    outputs,
                    confidence
                FROM lineage_metadata
            """

            lineage_map = {}
            lineage_results = prod_conn.execute(query_lineage).fetchall()

            for obj_id, inputs_json, outputs_json, confidence in lineage_results:
                lineage_map[obj_id] = {
                    'inputs': inputs_json,
                    'outputs': outputs_json,
                    'confidence': confidence
                }

            # Insert baseline metadata
            baseline_conn.execute("""
                INSERT INTO baseline_metadata (
                    baseline_name,
                    created_at,
                    parser_version,
                    total_objects,
                    description,
                    source_workspace_path
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                name,
                datetime.now(),
                parser_version,
                len(objects),
                description,
                str(prod_workspace)
            ])

            # Insert baseline objects
            captured_count = 0
            for obj_id, obj_name, schema_name, obj_type, ddl_text in objects:
                # Calculate DDL hash
                ddl_hash = hashlib.sha256(ddl_text.encode('utf-8')).hexdigest()

                # Get expected dependencies
                expected_inputs = lineage_map.get(obj_id, {}).get('inputs', '[]')
                expected_outputs = lineage_map.get(obj_id, {}).get('outputs', '[]')
                confidence = lineage_map.get(obj_id, {}).get('confidence', 0.0)

                # Verified = True if high confidence
                verified = confidence >= 0.85

                baseline_conn.execute("""
                    INSERT INTO baseline_objects (
                        object_id,
                        object_name,
                        schema_name,
                        object_type,
                        ddl_text,
                        ddl_hash,
                        expected_inputs_json,
                        expected_outputs_json,
                        verified,
                        notes,
                        captured_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    obj_id,
                    obj_name,
                    schema_name,
                    obj_type,
                    ddl_text,
                    ddl_hash,
                    expected_inputs,
                    expected_outputs,
                    verified,
                    f"Confidence: {confidence:.2f}",
                    datetime.now()
                ])

                captured_count += 1

            baseline_conn.close()
            prod_conn.close()

            logger.info(f"✅ Baseline '{name}' created with {captured_count} objects")
            return captured_count

        except Exception as e:
            logger.error(f"Failed to create baseline: {e}")
            if baseline_db_path.exists():
                baseline_db_path.unlink()  # Cleanup on failure
            raise RuntimeError(f"Baseline creation failed: {e}")

    def load_baseline(self, name: str) -> Dict[int, Dict]:
        """
        Load baseline objects.

        Args:
            name: Baseline name (e.g., 'baseline_v3.7.0')

        Returns:
            Dict mapping object_id -> {
                'object_name': str,
                'schema_name': str,
                'ddl_text': str,
                'ddl_hash': str,
                'expected_inputs': List[int],
                'expected_outputs': List[int],
                'verified': bool
            }

        Raises:
            FileNotFoundError: If baseline doesn't exist
        """
        baseline_db_path = self.baseline_dir / f"{name}.duckdb"

        if not baseline_db_path.exists():
            raise FileNotFoundError(f"Baseline not found: {baseline_db_path}")

        conn = duckdb.connect(str(baseline_db_path), read_only=True)

        query = """
            SELECT
                object_id,
                object_name,
                schema_name,
                ddl_text,
                ddl_hash,
                expected_inputs_json,
                expected_outputs_json,
                verified
            FROM baseline_objects
            ORDER BY object_id
        """

        results = conn.execute(query).fetchall()
        conn.close()

        baseline_objects = {}
        for row in results:
            obj_id, obj_name, schema_name, ddl_text, ddl_hash, inputs_json, outputs_json, verified = row

            # Parse JSON arrays
            expected_inputs = json.loads(inputs_json) if inputs_json else []
            expected_outputs = json.loads(outputs_json) if outputs_json else []

            baseline_objects[obj_id] = {
                'object_name': obj_name,
                'schema_name': schema_name,
                'ddl_text': ddl_text,
                'ddl_hash': ddl_hash,
                'expected_inputs': expected_inputs,
                'expected_outputs': expected_outputs,
                'verified': verified
            }

        logger.info(f"✅ Loaded baseline '{name}' with {len(baseline_objects)} objects")
        return baseline_objects

    def update_object_ddl(
        self,
        baseline_name: str,
        object_id: int,
        new_ddl: str,
        run_id: str
    ) -> None:
        """
        Update baseline object DDL (auto-update on change detection).

        Args:
            baseline_name: Baseline name
            object_id: Object ID to update
            new_ddl: New DDL text
            run_id: Evaluation run_id that detected the change
        """
        baseline_db_path = self.baseline_dir / f"{baseline_name}.duckdb"

        if not baseline_db_path.exists():
            raise FileNotFoundError(f"Baseline not found: {baseline_db_path}")

        conn = duckdb.connect(str(baseline_db_path))

        # Get old hash
        old_hash_result = conn.execute(
            "SELECT ddl_hash FROM baseline_objects WHERE object_id = ?",
            [object_id]
        ).fetchone()

        old_hash = old_hash_result[0] if old_hash_result else None

        # Calculate new hash
        new_hash = hashlib.sha256(new_ddl.encode('utf-8')).hexdigest()

        # Update baseline object
        conn.execute("""
            UPDATE baseline_objects
            SET ddl_text = ?,
                ddl_hash = ?
            WHERE object_id = ?
        """, [new_ddl, new_hash, object_id])

        # Log change
        conn.execute("""
            INSERT INTO baseline_change_log (
                baseline_name,
                object_id,
                change_type,
                old_ddl_hash,
                new_ddl_hash,
                changed_at,
                detected_in_run
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            baseline_name,
            object_id,
            'ddl_updated',
            old_hash,
            new_hash,
            datetime.now(),
            run_id
        ])

        conn.close()
        logger.info(f"✅ Updated object {object_id} DDL in baseline '{baseline_name}'")

    def add_new_object(
        self,
        baseline_name: str,
        object_id: int,
        object_data: Dict,
        run_id: str
    ) -> None:
        """
        Add new object to baseline (auto-add when discovered).

        Args:
            baseline_name: Baseline name
            object_id: Object ID
            object_data: Dict with keys:
                - object_name
                - schema_name
                - object_type
                - ddl_text
                - expected_inputs (List[int])
                - expected_outputs (List[int])
            run_id: Evaluation run_id that discovered the object
        """
        baseline_db_path = self.baseline_dir / f"{baseline_name}.duckdb"

        if not baseline_db_path.exists():
            raise FileNotFoundError(f"Baseline not found: {baseline_db_path}")

        conn = duckdb.connect(str(baseline_db_path))

        # Calculate DDL hash
        ddl_hash = hashlib.sha256(object_data['ddl_text'].encode('utf-8')).hexdigest()

        # Insert new object
        conn.execute("""
            INSERT INTO baseline_objects (
                object_id,
                object_name,
                schema_name,
                object_type,
                ddl_text,
                ddl_hash,
                expected_inputs_json,
                expected_outputs_json,
                verified,
                notes,
                captured_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            object_id,
            object_data['object_name'],
            object_data['schema_name'],
            object_data['object_type'],
            object_data['ddl_text'],
            ddl_hash,
            json.dumps(object_data.get('expected_inputs', [])),
            json.dumps(object_data.get('expected_outputs', [])),
            False,  # New objects not verified
            f"Auto-added in run {run_id}",
            datetime.now()
        ])

        # Log change
        conn.execute("""
            INSERT INTO baseline_change_log (
                baseline_name,
                object_id,
                change_type,
                old_ddl_hash,
                new_ddl_hash,
                changed_at,
                detected_in_run
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            baseline_name,
            object_id,
            'new_object',
            None,
            ddl_hash,
            datetime.now(),
            run_id
        ])

        conn.close()
        logger.info(f"✅ Added new object {object_id} to baseline '{baseline_name}'")

    def get_baseline_metadata(self, name: str) -> Dict:
        """
        Get baseline metadata.

        Args:
            name: Baseline name

        Returns:
            Dict with metadata fields
        """
        baseline_db_path = self.baseline_dir / f"{name}.duckdb"

        if not baseline_db_path.exists():
            raise FileNotFoundError(f"Baseline not found: {baseline_db_path}")

        conn = duckdb.connect(str(baseline_db_path), read_only=True)

        result = conn.execute(
            "SELECT * FROM baseline_metadata WHERE baseline_name = ?",
            [name]
        ).fetchone()

        conn.close()

        if not result:
            return {}

        return {
            'baseline_name': result[0],
            'created_at': result[1],
            'parser_version': result[2],
            'total_objects': result[3],
            'description': result[4],
            'source_workspace_path': result[5]
        }
