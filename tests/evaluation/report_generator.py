"""
Report Generator for sub_DL_OptimizeParsing

Generates console summaries and detailed JSON reports from evaluation results.

Author: Claude Code Agent
Date: 2025-11-02
Version: 1.0
"""

import duckdb
import json
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates evaluation reports in multiple formats:
    - Console summary (formatted text with tables, progress bars)
    - Detailed JSON report (full results for all objects)
    """

    def __init__(self, evaluation_db_path: Path):
        """
        Initialize report generator.

        Args:
            evaluation_db_path: Path to current_evaluation.duckdb
        """
        self.evaluation_db_path = Path(evaluation_db_path)

    def generate_console_summary(self, run_id: str) -> str:
        """
        Generate formatted console output.

        Args:
            run_id: Evaluation run ID

        Returns:
            Multi-line string with formatted summary
        """
        conn = duckdb.connect(str(self.evaluation_db_path), read_only=True)

        # Get run metadata
        run_meta = conn.execute(
            "SELECT * FROM evaluation_runs WHERE run_id = ?",
            [run_id]
        ).fetchone()

        if not run_meta:
            return f"❌ Run {run_id} not found"

        run_timestamp, baseline_name, mode, total_objects = run_meta[1], run_meta[2], run_meta[3], run_meta[4]
        avg_regex, avg_sqlglot, avg_ai = run_meta[5], run_meta[6], run_meta[7]
        above_095, below_095 = run_meta[8], run_meta[9]
        ddl_changes, new_objects = run_meta[10], run_meta[11]
        progress_pct, completed, duration = run_meta[12], run_meta[13], run_meta[14]

        # Get objects below 0.95
        below_095_objects = conn.execute("""
            SELECT object_name, best_method, best_confidence,
                   regex_confidence, sqlglot_confidence, ai_confidence
            FROM evaluation_history
            WHERE run_id = ? AND meets_goal = FALSE
            ORDER BY best_confidence ASC
            LIMIT 52
        """, [run_id]).fetchall()

        # Get baseline changes
        baseline_changes = conn.execute("""
            SELECT object_id, object_name, ddl_changed
            FROM evaluation_history
            WHERE run_id = ? AND ddl_changed = TRUE
        """, [run_id]).fetchall()

        conn.close()

        # Build console output
        output = []
        output.append("╔" + "═" * 70 + "╗")
        output.append(f"║  PARSING EVALUATION REPORT - {run_id:<37} ║")
        output.append("╚" + "═" * 70 + "╝")
        output.append("")

        # Summary
        output.append("📊 SUMMARY")
        output.append("━" * 72)
        output.append(f"  Baseline: {baseline_name} ({total_objects} objects)")
        output.append(f"  Evaluated: {total_objects} objects")
        output.append(f"  Duration: {duration}s" if duration else "  Duration: N/A")
        output.append("")

        # Goal tracking
        output.append("🎯 GOAL TRACKING (95% Confidence Target)")
        output.append("━" * 72)
        output.append(f"  Objects ≥ 0.95:  {above_095:3d} / {total_objects}  ({progress_pct:.1f}%)")
        output.append(f"  Objects < 0.95:  {below_095:3d} / {total_objects}  ({100-progress_pct:.1f}%)")
        output.append("")

        # Progress bar
        bar_width = 40
        filled = int(bar_width * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        output.append(f"  Progress: {bar} {progress_pct:.1f}% / 95% target")
        output.append("")

        # Method comparison
        output.append("📈 METHOD COMPARISON")
        output.append("━" * 72)
        output.append(f"  Method     Avg Confidence")
        output.append(f"  {'─' * 30}")
        output.append(f"  Regex      {avg_regex:.3f}")
        output.append(f"  SQLGlot    {avg_sqlglot:.3f}  {'← Best overall' if avg_sqlglot >= max(avg_regex, avg_ai) else ''}")
        output.append(f"  AI         {avg_ai:.3f}  {'← Best overall' if avg_ai > max(avg_regex, avg_sqlglot) else ''}")
        output.append("")

        # Objects below 0.95
        if below_095_objects:
            output.append(f"⚠️  OBJECTS BELOW 0.95 CONFIDENCE ({len(below_095_objects)} objects)")
            output.append("━" * 72)
            output.append(f"  {'Object Name':<40} {'Best':>6} {'Regex':>6} {'SQL':>6} {'AI':>6}")
            output.append(f"  {'-' * 70}")

            for obj_name, best_method, best_conf, regex_conf, sqlglot_conf, ai_conf in below_095_objects[:10]:
                output.append(
                    f"  {obj_name[:40]:<40} "
                    f"{best_conf:>6.2f} "
                    f"{regex_conf:>6.2f} "
                    f"{sqlglot_conf:>6.2f} "
                    f"{ai_conf:>6.2f}"
                )

            if len(below_095_objects) > 10:
                output.append(f"  ... and {len(below_095_objects) - 10} more")
        output.append("")

        # Baseline changes
        if baseline_changes:
            output.append("📋 BASELINE CHANGES")
            output.append("━" * 72)
            output.append(f"  ⚠️  {len(baseline_changes)} object(s) had DDL changes (auto-updated in baseline)")
            for obj_id, obj_name, _ in baseline_changes[:5]:
                output.append(f"      - {obj_name}")
            if len(baseline_changes) > 5:
                output.append(f"      ... and {len(baseline_changes) - 5} more")
        output.append("")

        # Footer
        output.append("✅ EVALUATION COMPLETE")
        output.append("━" * 72)
        output.append(f"  Report: optimization_reports/{run_id}.json")
        output.append("")

        return "\n".join(output)

    def generate_json_report(self, run_id: str, output_path: Path) -> None:
        """
        Generate detailed JSON report.

        Args:
            run_id: Evaluation run ID
            output_path: Where to save JSON report
        """
        conn = duckdb.connect(str(self.evaluation_db_path), read_only=True)

        # Get run metadata
        run_meta = conn.execute(
            "SELECT * FROM evaluation_runs WHERE run_id = ?",
            [run_id]
        ).fetchone()

        if not run_meta:
            logger.error(f"Run {run_id} not found")
            return

        # Get all evaluation results
        results = conn.execute("""
            SELECT
                object_id,
                object_name,
                ddl_hash,
                ddl_changed,
                regex_confidence, regex_inputs_count, regex_outputs_count,
                regex_precision, regex_recall, regex_f1_score, regex_execution_ms,
                sqlglot_confidence, sqlglot_inputs_count, sqlglot_outputs_count,
                sqlglot_precision, sqlglot_recall, sqlglot_f1_score,
                sqlglot_quality_match, sqlglot_execution_ms,
                ai_confidence, ai_inputs_count, ai_outputs_count,
                ai_precision, ai_recall, ai_f1_score,
                ai_execution_ms, ai_cost_estimate, ai_validation_passed,
                best_method, best_confidence, meets_goal
            FROM evaluation_history
            WHERE run_id = ?
            ORDER BY best_confidence ASC
        """, [run_id]).fetchall()

        # Get baseline changes
        # (Query baseline_change_log if needed - for now, use ddl_changed flag)

        conn.close()

        # Build JSON report
        report = {
            "summary": {
                "run_id": run_id,
                "run_timestamp": str(run_meta[1]),
                "baseline_name": run_meta[2],
                "mode": run_meta[3],
                "total_objects": run_meta[4],
                "objects_above_095": run_meta[8],
                "objects_below_095": run_meta[9],
                "objects_with_ddl_changes": run_meta[10],
                "new_objects_added": run_meta[11],
                "progress_to_goal_pct": run_meta[12],
                "duration_seconds": run_meta[14],
                "avg_confidence": {
                    "regex": run_meta[5],
                    "sqlglot": run_meta[6],
                    "ai": run_meta[7]
                }
            },
            "method_comparison": {
                "regex": {
                    "avg_confidence": run_meta[5],
                    "description": "Baseline regex pattern matching"
                },
                "sqlglot": {
                    "avg_confidence": run_meta[6],
                    "description": "SQLGlot AST parsing with preprocessing"
                },
                "ai": {
                    "avg_confidence": run_meta[7],
                    "description": "Azure OpenAI disambiguation"
                }
            },
            "objects_below_095": [],
            "baseline_changes": [],
            "full_results": []
        }

        # Add detailed results
        for row in results:
            obj_data = {
                "object_id": row[0],
                "object_name": row[1],
                "ddl_hash": row[2],
                "ddl_changed": row[3],
                "scores": {
                    "regex": {
                        "confidence": row[4],
                        "inputs_count": row[5],
                        "outputs_count": row[6],
                        "precision": row[7],
                        "recall": row[8],
                        "f1": row[9],
                        "execution_ms": row[10]
                    },
                    "sqlglot": {
                        "confidence": row[11],
                        "inputs_count": row[12],
                        "outputs_count": row[13],
                        "precision": row[14],
                        "recall": row[15],
                        "f1": row[16],
                        "quality_match": row[17],
                        "execution_ms": row[18]
                    },
                    "ai": {
                        "confidence": row[19],
                        "inputs_count": row[20],
                        "outputs_count": row[21],
                        "precision": row[22],
                        "recall": row[23],
                        "f1": row[24],
                        "execution_ms": row[25],
                        "cost_estimate_usd": row[26],
                        "validation_passed": row[27]
                    }
                },
                "best_method": row[28],
                "best_confidence": row[29],
                "meets_goal": row[30]
            }

            report["full_results"].append(obj_data)

            # Add to objects_below_095 if doesn't meet goal
            if not row[30]:  # meets_goal
                report["objects_below_095"].append(obj_data)

            # Add to baseline_changes if DDL changed
            if row[3]:  # ddl_changed
                report["baseline_changes"].append({
                    "object_id": row[0],
                    "object_name": row[1],
                    "change_type": "ddl_updated"
                })

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✅ JSON report saved to: {output_path}")

    def compare_runs(self, run_id_1: str, run_id_2: str) -> str:
        """
        Compare two evaluation runs.

        Args:
            run_id_1: First run ID
            run_id_2: Second run ID

        Returns:
            Formatted comparison report
        """
        conn = duckdb.connect(str(self.evaluation_db_path), read_only=True)

        # Get run metadata for both runs
        run1 = conn.execute(
            "SELECT * FROM evaluation_runs WHERE run_id = ?",
            [run_id_1]
        ).fetchone()

        run2 = conn.execute(
            "SELECT * FROM evaluation_runs WHERE run_id = ?",
            [run_id_2]
        ).fetchone()

        if not run1 or not run2:
            return "❌ One or both runs not found"

        # Extract metrics
        r1_above, r1_below = run1[8], run1[9]
        r2_above, r2_below = run2[8], run2[9]

        r1_avg_regex, r1_avg_sqlglot, r1_avg_ai = run1[5], run1[6], run1[7]
        r2_avg_regex, r2_avg_sqlglot, r2_avg_ai = run2[5], run2[6], run2[7]

        conn.close()

        # Build comparison output
        output = []
        output.append("╔" + "═" * 70 + "╗")
        output.append(f"║  RUN COMPARISON: {run_id_1[:20]} vs {run_id_2[:20]:<20} ║")
        output.append("╚" + "═" * 70 + "╝")
        output.append("")

        # Goal progress comparison
        delta_above = r2_above - r1_above
        delta_symbol = "📈" if delta_above > 0 else "📉" if delta_above < 0 else "➡️"

        output.append("🎯 GOAL PROGRESS")
        output.append("━" * 72)
        output.append(f"  Objects ≥ 0.95:")
        output.append(f"    Run 1: {r1_above}")
        output.append(f"    Run 2: {r2_above}  ({delta_above:+d}) {delta_symbol}")
        output.append("")

        # Method comparison
        output.append("📈 METHOD IMPROVEMENTS")
        output.append("━" * 72)

        def format_delta(v1, v2):
            delta = v2 - v1
            symbol = "📈" if delta > 0.01 else "📉" if delta < -0.01 else "➡️"
            return f"{v1:.3f} → {v2:.3f} ({delta:+.3f}) {symbol}"

        output.append(f"  Regex:   {format_delta(r1_avg_regex, r2_avg_regex)}")
        output.append(f"  SQLGlot: {format_delta(r1_avg_sqlglot, r2_avg_sqlglot)}")
        output.append(f"  AI:      {format_delta(r1_avg_ai, r2_avg_ai)}")
        output.append("")

        return "\n".join(output)
