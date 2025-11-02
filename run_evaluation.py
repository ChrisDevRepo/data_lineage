#!/usr/bin/env python3
"""
Quick CLI to run sub_DL_OptimizeParsing evaluation.

Usage:
    python run_evaluation.py --mode full --baseline baseline_v3.7.0_before_phase1
    python run_evaluation.py --mode incremental --baseline baseline_v3.7.0_before_phase1
"""

import argparse
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import evaluation components
from evaluation.baseline_manager import BaselineManager
from evaluation.evaluation_runner import EvaluationRunner
from evaluation.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description='Run parsing evaluation')
    parser.add_argument('--mode', choices=['full', 'incremental'], required=True,
                       help='Evaluation mode')
    parser.add_argument('--baseline', type=str, required=True,
                       help='Baseline name (e.g., baseline_v3.7.0_before_phase1)')

    args = parser.parse_args()

    # Setup paths
    workspace_path = Path('lineage_workspace.duckdb')
    baselines_dir = Path('evaluation_baselines')
    evaluation_db_path = baselines_dir / 'current_evaluation.duckdb'

    # Verify workspace exists
    if not workspace_path.exists():
        logger.error(f"❌ Workspace not found: {workspace_path}")
        logger.error("   Run the parser first: python lineage_v3/main.py run --parquet parquet_snapshots/")
        sys.exit(1)

    # Initialize components
    baseline_manager = BaselineManager(baselines_dir)
    runner = EvaluationRunner(
        baseline_manager=baseline_manager,
        production_workspace_path=workspace_path,
        evaluation_db_path=evaluation_db_path
    )
    report_generator = ReportGenerator(evaluation_db_path)

    # Run evaluation
    logger.info(f"Starting {args.mode} evaluation with baseline: {args.baseline}")

    try:
        if args.mode == 'full':
            run_id = runner.run_full_evaluation(args.baseline)
        else:
            run_id = runner.run_incremental_evaluation(args.baseline)

        # Generate report
        logger.info(f"\n{'='*70}")
        logger.info("Generating report...")
        logger.info(f"{'='*70}\n")

        summary = report_generator.generate_console_summary(run_id)
        print(summary)

        # Save JSON report
        output_dir = Path('optimization_reports')
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / f'{run_id}.json'
        report_generator.generate_json_report(run_id, report_path)

        logger.info(f"\n✅ Evaluation complete!")
        logger.info(f"   Run ID: {run_id}")
        logger.info(f"   JSON Report: {report_path}")

    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
