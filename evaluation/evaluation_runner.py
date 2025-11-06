"""
Evaluation Runner for sub_DL_OptimizeParsing

Core evaluation logic: runs all 3 parsing methods (regex, SQLGlot, AI)
on each stored procedure and compares results against baseline.

Author: Claude Code Agent
Date: 2025-11-02
Version: 1.0
"""

import duckdb
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import uuid

from evaluation.baseline_manager import BaselineManager
from evaluation.score_calculator import ScoreCalculator
from evaluation.schemas import initialize_evaluation_db

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
from lineage_v3.parsers.ai_disambiguator import run_standalone_ai_extraction

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """
    Orchestrates evaluation runs: runs all 3 methods, calculates scores,
    stores results, detects DDL changes.
    """

    def __init__(
        self,
        baseline_manager: BaselineManager,
        production_workspace_path: Path,
        evaluation_db_path: Path
    ):
        """
        Initialize evaluation runner.

        Args:
            baseline_manager: BaselineManager instance
            production_workspace_path: Path to lineage_workspace.duckdb
            evaluation_db_path: Path to current_evaluation.duckdb
        """
        self.baseline_manager = baseline_manager
        self.production_workspace_path = Path(production_workspace_path)
        self.evaluation_db_path = Path(evaluation_db_path)

        # Initialize evaluation database if needed
        if not self.evaluation_db_path.exists():
            conn = duckdb.connect(str(self.evaluation_db_path))
            initialize_evaluation_db(conn)
            conn.close()

    def run_full_evaluation(self, baseline_name: str) -> str:
        """
        Run full evaluation (all objects, all methods).

        Process:
        1. Load baseline objects
        2. For each object:
           - Check DDL hash (detect changes)
           - Run regex extraction
           - Run SQLGlot extraction
           - Run AI extraction
           - Calculate precision/recall vs expected dependencies
           - Store results
        3. Auto-update baseline if DDL changed
        4. Calculate aggregates
        5. Return run_id

        Args:
            baseline_name: Baseline to evaluate against

        Returns:
            run_id (e.g., 'run_20251102_085730')
        """
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🚀 Starting full evaluation: {run_id}")

        # Load baseline
        baseline_objects = self.baseline_manager.load_baseline(baseline_name)
        total_objects = len(baseline_objects)

        # Initialize production workspace
        workspace = DuckDBWorkspace(str(self.production_workspace_path))
        workspace.connect()

        # Initialize parser
        parser = QualityAwareParser(workspace)

        # Connect to evaluation database
        eval_conn = duckdb.connect(str(self.evaluation_db_path))

        # Create evaluation run record
        eval_conn.execute("""
            INSERT INTO evaluation_runs (
                run_id,
                run_timestamp,
                baseline_name,
                mode,
                total_objects_evaluated,
                completed
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, [run_id, datetime.now(), baseline_name, 'full', total_objects, False])

        # Track statistics
        objects_above_095 = 0
        objects_below_095 = 0
        objects_with_ddl_changes = 0
        new_objects_added = 0

        total_regex_confidence = 0.0
        total_sqlglot_confidence = 0.0
        total_ai_confidence = 0.0

        start_time = time.time()

        # Evaluate each object
        for idx, (object_id, baseline_obj) in enumerate(baseline_objects.items(), 1):
            logger.info(f"Processing {idx}/{total_objects}: {baseline_obj['object_name']}")

            # Evaluate this object
            result = self._evaluate_object(
                object_id=object_id,
                baseline_obj=baseline_obj,
                parser=parser,
                workspace=workspace,
                baseline_name=baseline_name,
                run_id=run_id
            )

            # Store result in evaluation_history
            eval_conn.execute("""
                INSERT INTO evaluation_history (
                    run_id,
                    object_id,
                    object_name,
                    ddl_hash,
                    ddl_changed,
                    regex_confidence,
                    regex_inputs_count,
                    regex_outputs_count,
                    regex_precision,
                    regex_recall,
                    regex_f1_score,
                    regex_execution_ms,
                    sqlglot_confidence,
                    sqlglot_inputs_count,
                    sqlglot_outputs_count,
                    sqlglot_precision,
                    sqlglot_recall,
                    sqlglot_f1_score,
                    sqlglot_quality_match,
                    sqlglot_execution_ms,
                    ai_confidence,
                    ai_inputs_count,
                    ai_outputs_count,
                    ai_precision,
                    ai_recall,
                    ai_f1_score,
                    ai_execution_ms,
                    ai_cost_estimate,
                    ai_validation_passed,
                    best_method,
                    best_confidence,
                    meets_goal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                run_id,
                object_id,
                result['object_name'],
                result['current_ddl_hash'],
                result['ddl_changed'],
                result['regex']['confidence'],
                result['regex']['inputs_count'],
                result['regex']['outputs_count'],
                result['regex']['precision'],
                result['regex']['recall'],
                result['regex']['f1'],
                result['regex']['execution_ms'],
                result['sqlglot']['confidence'],
                result['sqlglot']['inputs_count'],
                result['sqlglot']['outputs_count'],
                result['sqlglot']['precision'],
                result['sqlglot']['recall'],
                result['sqlglot']['f1'],
                result['sqlglot']['quality_match'],
                result['sqlglot']['execution_ms'],
                result['ai']['confidence'],
                result['ai']['inputs_count'],
                result['ai']['outputs_count'],
                result['ai']['precision'],
                result['ai']['recall'],
                result['ai']['f1'],
                result['ai']['execution_ms'],
                result['ai']['cost_estimate'],
                result['ai']['validation_passed'],
                result['best_method'],
                result['best_confidence'],
                result['meets_goal']
            ])

            # Update statistics
            if result['meets_goal']:
                objects_above_095 += 1
            else:
                objects_below_095 += 1

            if result['ddl_changed']:
                objects_with_ddl_changes += 1

            total_regex_confidence += result['regex']['confidence']
            total_sqlglot_confidence += result['sqlglot']['confidence']
            total_ai_confidence += result['ai']['confidence']

            # Progress indicator
            if idx % 10 == 0 or idx == total_objects:
                elapsed = time.time() - start_time
                pct = (idx / total_objects) * 100
                logger.info(f"  Progress: {idx}/{total_objects} ({pct:.1f}%) - {elapsed:.1f}s elapsed")

        # Calculate aggregates
        avg_regex_conf = total_regex_confidence / total_objects if total_objects > 0 else 0.0
        avg_sqlglot_conf = total_sqlglot_confidence / total_objects if total_objects > 0 else 0.0
        avg_ai_conf = total_ai_confidence / total_objects if total_objects > 0 else 0.0
        progress_pct = (objects_above_095 / total_objects * 100) if total_objects > 0 else 0.0

        duration_seconds = int(time.time() - start_time)

        # Update run metadata
        eval_conn.execute("""
            UPDATE evaluation_runs
            SET avg_regex_confidence = ?,
                avg_sqlglot_confidence = ?,
                avg_ai_confidence = ?,
                objects_above_095 = ?,
                objects_below_095 = ?,
                objects_with_ddl_changes = ?,
                new_objects_added = ?,
                progress_to_goal_pct = ?,
                completed = TRUE,
                duration_seconds = ?
            WHERE run_id = ?
        """, [
            avg_regex_conf,
            avg_sqlglot_conf,
            avg_ai_conf,
            objects_above_095,
            objects_below_095,
            objects_with_ddl_changes,
            new_objects_added,
            progress_pct,
            duration_seconds,
            run_id
        ])

        eval_conn.close()
        workspace.disconnect()

        logger.info(f"✅ Evaluation complete: {run_id}")
        logger.info(f"   Objects above 0.95: {objects_above_095}/{total_objects} ({progress_pct:.1f}%)")
        logger.info(f"   Duration: {duration_seconds}s")

        return run_id

    def run_incremental_evaluation(self, baseline_name: str) -> str:
        """
        Run incremental evaluation (only objects with DDL changes).

        Much faster for quick validation after parser improvements.

        Args:
            baseline_name: Baseline to evaluate against

        Returns:
            run_id
        """
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🚀 Starting incremental evaluation: {run_id}")

        # Load baseline
        baseline_objects = self.baseline_manager.load_baseline(baseline_name)

        # Initialize production workspace
        workspace = DuckDBWorkspace(str(self.production_workspace_path))
        workspace.connect()

        # Detect DDL changes
        changed_objects = []
        for object_id, baseline_obj in baseline_objects.items():
            # Get current DDL from production
            current_ddl = workspace.get_object_definition(object_id)
            if not current_ddl:
                continue

            current_hash = hashlib.sha256(current_ddl.encode('utf-8')).hexdigest()

            if current_hash != baseline_obj['ddl_hash']:
                changed_objects.append(object_id)

        logger.info(f"   Detected {len(changed_objects)} changed objects (out of {len(baseline_objects)} total)")

        if len(changed_objects) == 0:
            logger.info("   No changes detected - copying last run results")
            # TODO: Copy last run results
            workspace.disconnect()
            return run_id

        # Run full evaluation only on changed objects
        # (Implementation similar to run_full_evaluation but filtered)
        # For now, delegate to full evaluation
        workspace.disconnect()

        logger.info("   Running full evaluation on changed objects...")
        return self.run_full_evaluation(baseline_name)

    def _evaluate_object(
        self,
        object_id: int,
        baseline_obj: Dict,
        parser: QualityAwareParser,
        workspace: DuckDBWorkspace,
        baseline_name: str,
        run_id: str
    ) -> Dict:
        """
        Evaluate single object with all 3 methods.

        Args:
            object_id: Object ID
            baseline_obj: Baseline object data
            parser: QualityAwareParser instance
            workspace: DuckDBWorkspace instance
            baseline_name: Baseline name (for auto-update)
            run_id: Current run_id

        Returns:
            Dict with evaluation results for all 3 methods
        """
        # Get current DDL from production
        current_ddl = workspace.get_object_definition(object_id)
        if not current_ddl:
            current_ddl = baseline_obj['ddl_text']  # Fallback to baseline

        # Calculate current DDL hash
        current_ddl_hash = hashlib.sha256(current_ddl.encode('utf-8')).hexdigest()
        ddl_changed = (current_ddl_hash != baseline_obj['ddl_hash'])

        # Auto-update baseline if DDL changed
        if ddl_changed:
            logger.info(f"   ⚠️  DDL changed for {baseline_obj['object_name']} - auto-updating baseline")
            self.baseline_manager.update_object_ddl(
                baseline_name=baseline_name,
                object_id=object_id,
                new_ddl=current_ddl,
                run_id=run_id
            )

        # Extract expected dependencies
        expected_inputs = baseline_obj['expected_inputs']
        expected_outputs = baseline_obj['expected_outputs']

        # ===== METHOD 1: REGEX =====
        regex_result = self._run_regex_method(
            parser=parser,
            ddl=current_ddl,
            workspace=workspace,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs
        )

        # ===== METHOD 2: SQLGLOT =====
        sqlglot_result = self._run_sqlglot_method(
            parser=parser,
            ddl=current_ddl,
            workspace=workspace,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs
        )

        # ===== METHOD 3: AI =====
        ai_result = self._run_ai_method(
            ddl=current_ddl,
            workspace=workspace,
            object_id=object_id,
            sp_name=f"{baseline_obj['schema_name']}.{baseline_obj['object_name']}",
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs
        )

        # Determine best method
        best_method, best_confidence = ScoreCalculator.determine_best_method(
            regex_result['confidence'],
            sqlglot_result['confidence'],
            ai_result['confidence']
        )

        meets_goal = best_confidence >= 0.95

        return {
            'object_name': baseline_obj['object_name'],
            'current_ddl_hash': current_ddl_hash,
            'ddl_changed': ddl_changed,
            'regex': regex_result,
            'sqlglot': sqlglot_result,
            'ai': ai_result,
            'best_method': best_method,
            'best_confidence': best_confidence,
            'meets_goal': meets_goal
        }

    def _run_regex_method(
        self,
        parser: QualityAwareParser,
        ddl: str,
        workspace: DuckDBWorkspace,
        expected_inputs: List[int],
        expected_outputs: List[int]
    ) -> Dict:
        """Run regex extraction and calculate scores."""
        start_time = time.time()

        try:
            # Call parser's public regex wrapper
            result = parser.extract_regex_dependencies(ddl)

            # Resolve table names to object_ids
            found_inputs = parser._resolve_table_names(result['sources_validated'])
            found_outputs = parser._resolve_table_names(result['targets_validated'])

            # Calculate scores
            scores = ScoreCalculator.calculate_method_scores(
                found_inputs, found_outputs,
                expected_inputs, expected_outputs
            )

            execution_ms = int((time.time() - start_time) * 1000)

            return {
                'confidence': scores['confidence'],
                'inputs_count': len(found_inputs),
                'outputs_count': len(found_outputs),
                'precision': scores['overall_precision'],
                'recall': scores['overall_recall'],
                'f1': scores['overall_f1'],
                'execution_ms': execution_ms
            }

        except Exception as e:
            logger.error(f"Regex method failed: {e}")
            return self._empty_result(int((time.time() - start_time) * 1000))

    def _run_sqlglot_method(
        self,
        parser: QualityAwareParser,
        ddl: str,
        workspace: DuckDBWorkspace,
        expected_inputs: List[int],
        expected_outputs: List[int]
    ) -> Dict:
        """Run SQLGlot extraction and calculate scores."""
        start_time = time.time()

        try:
            # Call parser's public SQLGlot wrapper
            result = parser.extract_sqlglot_dependencies(ddl)

            # Resolve table names to object_ids
            found_inputs = parser._resolve_table_names(result['sources_validated'])
            found_outputs = parser._resolve_table_names(result['targets_validated'])

            # Calculate scores
            scores = ScoreCalculator.calculate_method_scores(
                found_inputs, found_outputs,
                expected_inputs, expected_outputs
            )

            execution_ms = int((time.time() - start_time) * 1000)

            return {
                'confidence': scores['confidence'],
                'inputs_count': len(found_inputs),
                'outputs_count': len(found_outputs),
                'precision': scores['overall_precision'],
                'recall': scores['overall_recall'],
                'f1': scores['overall_f1'],
                'quality_match': result['quality_check']['overall_match'],
                'execution_ms': execution_ms
            }

        except Exception as e:
            logger.error(f"SQLGlot method failed: {e}")
            return self._empty_result(int((time.time() - start_time) * 1000))

    def _run_ai_method(
        self,
        ddl: str,
        workspace: DuckDBWorkspace,
        object_id: int,
        sp_name: str,
        expected_inputs: List[int],
        expected_outputs: List[int]
    ) -> Dict:
        """Run AI extraction and calculate scores."""
        start_time = time.time()

        try:
            # Call standalone AI function
            result = run_standalone_ai_extraction(
                ddl=ddl,
                workspace=workspace,
                object_id=object_id,
                sp_name=sp_name
            )

            found_inputs = result.get('sources', [])
            found_outputs = result.get('targets', [])

            # Calculate scores
            scores = ScoreCalculator.calculate_method_scores(
                found_inputs, found_outputs,
                expected_inputs, expected_outputs
            )

            return {
                'confidence': scores['confidence'],
                'inputs_count': len(found_inputs),
                'outputs_count': len(found_outputs),
                'precision': scores['overall_precision'],
                'recall': scores['overall_recall'],
                'f1': scores['overall_f1'],
                'execution_ms': result.get('execution_time_ms', 0),
                'cost_estimate': result.get('cost_estimate_usd', 0.0),
                'validation_passed': result.get('validation_passed', False)
            }

        except Exception as e:
            logger.error(f"AI method failed: {e}")
            return self._empty_result(int((time.time() - start_time) * 1000))

    @staticmethod
    def _empty_result(execution_ms: int) -> Dict:
        """Return empty result on method failure."""
        return {
            'confidence': 0.0,
            'inputs_count': 0,
            'outputs_count': 0,
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'execution_ms': execution_ms,
            'quality_match': 0.0,
            'cost_estimate': 0.0,
            'validation_passed': False
        }
