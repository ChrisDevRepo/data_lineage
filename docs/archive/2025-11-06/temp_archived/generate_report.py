#!/usr/bin/env python3
"""Generate report for a completed evaluation run."""

from pathlib import Path
from evaluation.report_generator import ReportGenerator

run_id = "run_20251102_164801"
evaluation_db_path = Path('evaluation_baselines/current_evaluation.duckdb')
report_generator = ReportGenerator(evaluation_db_path)

# Generate console summary
print(report_generator.generate_console_summary(run_id))

# Generate JSON report
output_dir = Path('optimization_reports')
output_dir.mkdir(exist_ok=True)
report_path = output_dir / f'{run_id}.json'
report_generator.generate_json_report(run_id, report_path)

print(f"\n✅ Reports generated!")
print(f"   JSON Report: {report_path}")
