#!/usr/bin/env python3
"""
SQLGlot Improvement Analysis - Before/After SQL Cleaning Engine
================================================================

Compares parser performance WITH and WITHOUT SQL Cleaning Engine integration.

This script:
1. Loads real data from parquet files (349 SPs)
2. Runs SQLGlot WITHOUT cleaning (baseline)
3. Runs SQLGlot WITH cleaning (improved)
4. Compares results and reports improvement
5. Generates detailed before/after report

Usage:
    python evaluation_baselines/sqlglot_improvement_analysis.py

Output:
    evaluation_baselines/sqlglot_improvement_results/
    ├── baseline_results.json           # Without cleaning
    ├── improved_results.json           # With cleaning
    ├── comparison_report.md            # Before/after comparison
    ├── improvement_details.json        # Detailed improvements per SP

Author: Claude Code Agent
Date: 2025-11-07
Version: 1.0.0
"""

import sys
import json
import duckdb
import pandas as pd
import sqlglot
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict, Counter
import logging
import re

# Add lineage_v3 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLGlotImprovementAnalyzer:
    """Analyzes SQLGlot improvement with SQL Cleaning Engine."""

    def __init__(self, parquet_dir: str = "temp"):
        """Initialize analyzer."""
        self.parquet_dir = Path(parquet_dir)
        self.output_dir = Path("evaluation_baselines/sqlglot_improvement_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.objects_df = None
        self.definitions_df = None

        # Results
        self.baseline_results = []  # WITHOUT cleaning
        self.improved_results = []  # WITH cleaning

        # Initialize SQL Cleaning Engine
        self.cleaning_engine = RuleEngine()

    def load_data(self):
        """Load parquet files using schema-based detection."""
        logger.info("Loading parquet files...")

        conn = duckdb.connect(':memory:')

        # Find parquet files
        parquet_files = list(self.parquet_dir.glob("*.parquet"))
        logger.info(f"Found {len(parquet_files)} parquet files")

        # Auto-detect files by schema
        for pf in parquet_files:
            try:
                # Read first row to check schema
                df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
                columns = set(df.columns)

                # Detect file type by column names
                if {'object_id', 'schema_name', 'object_name', 'object_type'}.issubset(columns):
                    # Objects file
                    self.objects_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
                    logger.info(f"✓ Loaded objects: {len(self.objects_df)} rows")

                elif {'object_id', 'definition'}.issubset(columns) and 'referencing_object_id' not in columns:
                    # Definitions file
                    self.definitions_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
                    logger.info(f"✓ Loaded definitions: {len(self.definitions_df)} rows")

            except Exception as e:
                logger.warning(f"Skipping file {pf.name}: {e}")

        conn.close()

        # Validate required files loaded
        if self.objects_df is None or self.definitions_df is None:
            raise Exception("Required parquet files not found (objects, definitions)")

        logger.info("✅ All required data loaded successfully")

    def simple_sqlglot_parse(self, ddl: str, with_cleaning: bool = False) -> Tuple[bool, Set[str]]:
        """
        Try parsing with SQLGlot.

        Args:
            ddl: SQL DDL text
            with_cleaning: If True, apply SQL cleaning first

        Returns:
            (success, tables_found)
        """
        try:
            # Apply SQL cleaning if requested
            sql_to_parse = self.cleaning_engine.apply_all(ddl) if with_cleaning else ddl

            # Try parsing
            statements = sqlglot.parse(sql_to_parse, dialect='tsql', error_level=None)

            # Check if parsing succeeded
            if not statements or any(isinstance(stmt, sqlglot.exp.Command) for stmt in statements):
                return (False, set())

            # Extract table names
            tables = set()
            for statement in statements:
                if statement:
                    for table in statement.find_all(sqlglot.exp.Table):
                        if table.name:
                            schema = table.db or 'dbo'
                            tables.add(f"{schema}.{table.name}")

            return (True, tables)

        except Exception as e:
            return (False, set())

    def analyze_stored_procedures(self):
        """Analyze all stored procedures with and without cleaning."""
        # Merge objects and definitions
        sp_defs = self.definitions_df.merge(
            self.objects_df[['object_id', 'object_type']],
            on='object_id',
            how='inner'
        )

        # Filter stored procedures
        sp_defs = sp_defs[sp_defs['object_type'] == 'Stored Procedure']

        total_sps = len(sp_defs)
        logger.info(f"Analyzing {total_sps} stored procedures...")

        for idx, row in sp_defs.iterrows():
            object_id = row['object_id']
            schema_name = row['schema_name']
            object_name = row['object_name']
            definition = row['definition']

            # Parse WITHOUT cleaning (baseline)
            baseline_success, baseline_tables = self.simple_sqlglot_parse(definition, with_cleaning=False)

            # Parse WITH cleaning (improved)
            improved_success, improved_tables = self.simple_sqlglot_parse(definition, with_cleaning=True)

            # Store results
            result = {
                'object_id': object_id,
                'schema_name': schema_name,
                'object_name': object_name,
                'baseline_success': baseline_success,
                'baseline_tables_count': len(baseline_tables),
                'baseline_tables': sorted(list(baseline_tables)),
                'improved_success': improved_success,
                'improved_tables_count': len(improved_tables),
                'improved_tables': sorted(list(improved_tables)),
                'improvement': {
                    'success_changed': baseline_success != improved_success,
                    'tables_gained': sorted(list(improved_tables - baseline_tables)),
                    'tables_lost': sorted(list(baseline_tables - improved_tables)),
                    'net_table_change': len(improved_tables) - len(baseline_tables)
                }
            }

            self.baseline_results.append({
                'object_id': object_id,
                'object_name': f"{schema_name}.{object_name}",
                'success': baseline_success,
                'tables_count': len(baseline_tables)
            })

            self.improved_results.append({
                'object_id': object_id,
                'object_name': f"{schema_name}.{object_name}",
                'success': improved_success,
                'tables_count': len(improved_tables),
                'result': result
            })

            # Progress indicator
            if (idx + 1) % 50 == 0:
                logger.info(f"Processed {idx + 1}/{total_sps} SPs...")

        logger.info("✅ Analysis complete!")

    def generate_comparison_report(self) -> str:
        """Generate markdown report comparing baseline vs improved."""
        # Calculate statistics
        baseline_success = sum(1 for r in self.baseline_results if r['success'])
        improved_success = sum(1 for r in self.improved_results if r['success'])
        total_sps = len(self.baseline_results)

        baseline_success_rate = baseline_success / total_sps * 100 if total_sps > 0 else 0
        improved_success_rate = improved_success / total_sps * 100 if total_sps > 0 else 0
        improvement_delta = improved_success_rate - baseline_success_rate

        # Find SPs that improved
        improved_sps = [
            r for r in self.improved_results
            if not next((b for b in self.baseline_results if b['object_id'] == r['object_id']), {}).get('success', False)
            and r['success']
        ]

        # Find SPs that regressed
        regressed_sps = [
            r for r in self.improved_results
            if next((b for b in self.baseline_results if b['object_id'] == r['object_id']), {}).get('success', False)
            and not r['success']
        ]

        report = f"""# SQLGlot Improvement Analysis Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total SPs Analyzed:** {total_sps}

---

## Executive Summary

| Metric | Baseline (No Cleaning) | Improved (With Cleaning) | Change |
|--------|------------------------|--------------------------|---------|
| **SQLGlot Success Rate** | {baseline_success}/{total_sps} ({baseline_success_rate:.1f}%) | {improved_success}/{total_sps} ({improved_success_rate:.1f}%) | **{improvement_delta:+.1f}%** |
| **SQLGlot Failure Rate** | {total_sps - baseline_success}/{total_sps} ({100-baseline_success_rate:.1f}%) | {total_sps - improved_success}/{total_sps} ({100-improved_success_rate:.1f}%) | {baseline_success_rate - improved_success_rate:+.1f}% |

### Key Findings

"""

        if improvement_delta > 0:
            report += f"✅ **SUCCESS**: SQL Cleaning Engine improved SQLGlot success rate by **{improvement_delta:.1f}%**\n\n"
            report += f"- **{len(improved_sps)} SPs** went from FAILURE → SUCCESS\n"
        elif improvement_delta < 0:
            report += f"⚠️ **REGRESSION**: SQL Cleaning Engine DECREASED success rate by **{improvement_delta:.1f}%**\n\n"
        else:
            report += f"ℹ️ **NO CHANGE**: SQL Cleaning Engine had no impact on success rate\n\n"

        if regressed_sps:
            report += f"- **{len(regressed_sps)} SPs** went from SUCCESS → FAILURE (REGRESSIONS)\n"

        report += f"\n---\n\n## Detailed Statistics\n\n"

        # Improvement breakdown
        report += f"### SPs That Improved ({len(improved_sps)})\n\n"
        if improved_sps:
            for sp in improved_sps[:10]:  # Top 10
                result = sp['result']
                report += f"- **{sp['object_name']}**: 0 → {result['improved_tables_count']} tables\n"
            if len(improved_sps) > 10:
                report += f"- ... and {len(improved_sps) - 10} more\n"
        else:
            report += "None\n"

        # Regression breakdown
        report += f"\n### SPs That Regressed ({len(regressed_sps)})\n\n"
        if regressed_sps:
            for sp in regressed_sps:
                result = sp['result']
                report += f"- **{sp['object_name']}**: {result['baseline_tables_count']} → 0 tables\n"
        else:
            report += "None\n"

        # Success rate by before/after
        report += f"\n---\n\n## Success Matrix\n\n"
        report += "| Baseline | Improved | Count | Percentage |\n"
        report += "|----------|----------|-------|------------|\n"

        both_success = sum(1 for i, r in enumerate(self.improved_results)
                          if r['success'] and self.baseline_results[i]['success'])
        both_fail = sum(1 for i, r in enumerate(self.improved_results)
                       if not r['success'] and not self.baseline_results[i]['success'])
        baseline_only = sum(1 for i, r in enumerate(self.improved_results)
                           if not r['success'] and self.baseline_results[i]['success'])
        improved_only = sum(1 for i, r in enumerate(self.improved_results)
                           if r['success'] and not self.baseline_results[i]['success'])

        report += f"| ✅ Success | ✅ Success | {both_success} | {both_success/total_sps*100:.1f}% |\n"
        report += f"| ✅ Success | ❌ Fail | {baseline_only} | {baseline_only/total_sps*100:.1f}% |\n"
        report += f"| ❌ Fail | ✅ Success | {improved_only} | {improved_only/total_sps*100:.1f}% |\n"
        report += f"| ❌ Fail | ❌ Fail | {both_fail} | {both_fail/total_sps*100:.1f}% |\n"

        report += f"\n---\n\n## Conclusion\n\n"
        if improvement_delta >= 5:
            report += f"✅ **RECOMMENDED**: Deploy SQL Cleaning Engine to production\n"
            report += f"- Improves SQLGlot success rate by {improvement_delta:.1f}%\n"
            report += f"- {len(improved_sps)} SPs benefit from cleaning\n"
            if regressed_sps:
                report += f"- ⚠️ Review {len(regressed_sps)} regressions before deployment\n"
        elif improvement_delta > 0:
            report += f"ℹ️ **MARGINAL IMPROVEMENT**: SQL Cleaning Engine provides minor benefit ({improvement_delta:.1f}%)\n"
        else:
            report += f"❌ **NOT RECOMMENDED**: SQL Cleaning Engine does not improve results\n"

        return report

    def save_results(self):
        """Save all results to files."""
        logger.info("Saving results...")

        # Baseline results
        baseline_file = self.output_dir / "baseline_results.json"
        with open(baseline_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_sps': len(self.baseline_results),
                'success_count': sum(1 for r in self.baseline_results if r['success']),
                'results': self.baseline_results
            }, f, indent=2)
        logger.info(f"✓ Saved baseline results: {baseline_file}")

        # Improved results
        improved_file = self.output_dir / "improved_results.json"
        with open(improved_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_sps': len(self.improved_results),
                'success_count': sum(1 for r in self.improved_results if r['success']),
                'results': [
                    {
                        'object_id': r['object_id'],
                        'object_name': r['object_name'],
                        'success': r['success'],
                        'tables_count': r['tables_count']
                    }
                    for r in self.improved_results
                ]
            }, f, indent=2)
        logger.info(f"✓ Saved improved results: {improved_file}")

        # Detailed improvement analysis
        improvement_file = self.output_dir / "improvement_details.json"
        with open(improvement_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_sps': len(self.improved_results),
                'details': [r['result'] for r in self.improved_results]
            }, f, indent=2)
        logger.info(f"✓ Saved improvement details: {improvement_file}")

        # Comparison report
        report = self.generate_comparison_report()
        report_file = self.output_dir / "comparison_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        logger.info(f"✓ Saved comparison report: {report_file}")

    def run(self):
        """Run complete analysis."""
        try:
            logger.info("=" * 80)
            logger.info("SQLGLOT IMPROVEMENT ANALYSIS - BEFORE/AFTER SQL CLEANING")
            logger.info("=" * 80)

            self.load_data()
            self.analyze_stored_procedures()
            self.save_results()

            # Print summary
            baseline_success = sum(1 for r in self.baseline_results if r['success'])
            improved_success = sum(1 for r in self.improved_results if r['success'])
            total = len(self.baseline_results)

            logger.info("=" * 80)
            logger.info("ANALYSIS COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Baseline (no cleaning): {baseline_success}/{total} ({baseline_success/total*100:.1f}%)")
            logger.info(f"Improved (with cleaning): {improved_success}/{total} ({improved_success/total*100:.1f}%)")
            logger.info(f"Improvement: {improved_success - baseline_success:+d} SPs ({(improved_success-baseline_success)/total*100:+.1f}%)")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    analyzer = SQLGlotImprovementAnalyzer()
    analyzer.run()
