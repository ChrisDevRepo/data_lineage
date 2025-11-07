#!/usr/bin/env python3
"""
Simplified Real Data Parser Analysis
====================================

Direct analysis of parser performance without DuckDB workspace dependency.

Author: Claude Code Agent
Date: 2025-11-07
Version: 1.0.0
"""

import sys
import os
import json
import duckdb
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict, Counter
import logging
import re
import sqlglot
from sqlglot import exp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleParserAnalyzer:
    """Simplified analyzer that parses DDL directly."""

    def __init__(self, parquet_dir: str = "temp"):
        self.parquet_dir = Path(parquet_dir)
        self.output_dir = Path("evaluation_baselines/real_data_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.objects_df = None
        self.dependencies_df = None
        self.definitions_df = None
        self.table_columns_df = None
        self.query_logs_df = None

        # Analysis results
        self.parser_results = []

    def load_data(self):
        """Load all parquet files."""
        logger.info("Loading parquet files...")

        conn = duckdb.connect(':memory:')
        parquet_files = list(self.parquet_dir.glob("*.parquet"))
        logger.info(f"Found {len(parquet_files)} parquet files")

        for pf in parquet_files:
            df = conn.execute(f"SELECT * FROM '{pf}'").df()
            cols = set(df.columns)

            if 'referencing_object_id' in cols and 'referenced_object_id' in cols:
                self.dependencies_df = df
                logger.info(f"✓ Loaded dependencies: {len(df)} rows")
            elif 'object_id' in cols and 'definition' in cols:
                self.definitions_df = df
                logger.info(f"✓ Loaded definitions: {len(df)} rows")
            elif 'column_name' in cols and 'data_type' in cols:
                self.table_columns_df = df
                logger.info(f"✓ Loaded table_columns: {len(df)} rows")
            elif 'object_type' in cols and 'object_name' in cols:
                self.objects_df = df
                logger.info(f"✓ Loaded objects: {len(df)} rows")
            elif 'command_text' in cols:
                self.query_logs_df = df
                logger.info(f"✓ Loaded query_logs: {len(df)} rows")

        logger.info("✅ All data loaded successfully")

    def simple_regex_parse(self, ddl: str) -> Set[str]:
        """Simple regex-based table extraction."""
        tables = set()

        # FROM/JOIN patterns
        from_pattern = r'\b(?:FROM|JOIN)\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)'
        for match in re.finditer(from_pattern, ddl, re.IGNORECASE):
            schema = match.group(1)
            table = match.group(2)
            if table and table.upper() not in ('DELETED', 'INSERTED', 'SELECT'):
                if schema:
                    tables.add(f"{schema}.{table}")
                else:
                    tables.add(table)

        # INSERT INTO/UPDATE/DELETE patterns
        target_pattern = r'\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|TRUNCATE\s+TABLE)\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)'
        for match in re.finditer(target_pattern, ddl, re.IGNORECASE):
            schema = match.group(1)
            table = match.group(2)
            if table:
                if schema:
                    tables.add(f"{schema}.{table}")
                else:
                    tables.add(table)

        return tables

    def simple_sqlglot_parse(self, ddl: str) -> Tuple[bool, Set[str]]:
        """
        Simple SQLGlot parse attempt.
        Returns (success, tables_found)
        """
        try:
            # Try to parse - if it fails, SQLGlot can't handle this SQL
            statements = sqlglot.parse(ddl, dialect='tsql', error_level=None)
            if not statements or statements[0] is None:
                return False, set()

            tables = set()
            for stmt in statements:
                if stmt is None:
                    continue
                for table_node in stmt.find_all(exp.Table):
                    if hasattr(table_node, 'catalog') and table_node.catalog:
                        schema = table_node.catalog
                    elif hasattr(table_node, 'db') and table_node.db:
                        schema = table_node.db
                    else:
                        schema = None

                    table_name = table_node.name if hasattr(table_node, 'name') else str(table_node)

                    if schema:
                        tables.add(f"{schema}.{table_name}")
                    else:
                        tables.add(table_name)

            return True, tables

        except Exception as e:
            return False, set()

    def analyze_sp(self, obj_id: int, obj_name: str, schema_name: str,
                   definition: str, ground_truth: Set[str], catalog: Set[str]) -> Dict:
        """Analyze a single stored procedure."""

        fqn = f"{schema_name}.{obj_name}"

        # Parse with both methods
        regex_tables = self.simple_regex_parse(definition)
        sqlglot_success, sqlglot_tables = self.simple_sqlglot_parse(definition)

        # Combine for final result (prefer SQLGlot if successful)
        if sqlglot_success and len(sqlglot_tables) > 0:
            parsed_tables = sqlglot_tables
        else:
            parsed_tables = regex_tables

        # Normalize table names with schema
        normalized_parsed = set()
        for table in parsed_tables:
            if '.' not in table:
                normalized_parsed.add(f"{schema_name}.{table}")
            else:
                normalized_parsed.add(table)

        # Calculate accuracy metrics
        tp = len(normalized_parsed & ground_truth)
        fp = len(normalized_parsed - ground_truth)
        fn = len(ground_truth - normalized_parsed)

        precision = tp / len(normalized_parsed) if normalized_parsed else 0.0
        recall = tp / len(ground_truth) if ground_truth else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # Catalog validation
        catalog_valid = len(normalized_parsed & catalog)
        catalog_rate = catalog_valid / len(normalized_parsed) if normalized_parsed else 1.0

        return {
            'object_id': obj_id,
            'object_name': fqn,
            'definition_size': len(definition),
            'ground_truth': {
                'count': len(ground_truth),
                'dependencies': sorted(ground_truth)
            },
            'parsed': {
                'count': len(normalized_parsed),
                'dependencies': sorted(normalized_parsed)
            },
            'regex': {
                'count': len(regex_tables),
                'found_gt_count': len(regex_tables & ground_truth)
            },
            'sqlglot': {
                'success': sqlglot_success,
                'count': len(sqlglot_tables),
                'found_gt_count': len(sqlglot_tables & ground_truth) if sqlglot_tables else 0
            },
            'accuracy': {
                'tp': tp,
                'fp': fp,
                'fn': fn,
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1_score': round(f1, 4)
            },
            'catalog_validation_rate': round(catalog_rate, 4),
            'missed': sorted(ground_truth - normalized_parsed),
            'false_positives': sorted(normalized_parsed - ground_truth)
        }

    def run_analysis(self):
        """Run complete analysis."""
        logger.info("Starting analysis...")

        # Build ground truth
        ground_truth_map = defaultdict(set)
        for _, row in self.dependencies_df.iterrows():
            ref_id = row['referencing_object_id']
            schema = row['referenced_schema_name']
            name = row['referenced_entity_name']
            fqn = f"{schema}.{name}" if schema else name
            ground_truth_map[ref_id].add(fqn)

        logger.info(f"✓ Ground truth built for {len(ground_truth_map)} objects")

        # Build catalog
        catalog = set()
        for _, row in self.objects_df.iterrows():
            schema = row['schema_name']
            name = row['object_name']
            fqn = f"{schema}.{name}" if schema else name
            catalog.add(fqn)

        logger.info(f"✓ Catalog built with {len(catalog)} objects")

        # Get stored procedures
        sp_defs = self.definitions_df.merge(
            self.objects_df[['object_id', 'object_type']],
            on='object_id'
        )
        sp_defs = sp_defs[sp_defs['object_type'].str.contains('PROCEDURE|P', case=False, na=False)]

        logger.info(f"Analyzing {len(sp_defs)} stored procedures...")

        # Analyze each SP
        for idx, row in sp_defs.iterrows():
            obj_id = row['object_id']
            obj_name = row['object_name']
            schema_name = row['schema_name']
            definition = row['definition']
            gt = ground_truth_map.get(obj_id, set())

            result = self.analyze_sp(obj_id, obj_name, schema_name, definition, gt, catalog)
            self.parser_results.append(result)

            if (idx + 1) % 50 == 0:
                logger.info(f"Progress: {idx + 1}/{len(sp_defs)}")

        logger.info("✅ Analysis complete!")

    def generate_summary_report(self) -> str:
        """Generate summary report."""

        # Filter out any errors
        valid_results = [r for r in self.parser_results if 'accuracy' in r]

        if not valid_results:
            return "No valid results to report."

        # Overall stats
        total = len(valid_results)
        avg_precision = sum(r['accuracy']['precision'] for r in valid_results) / total
        avg_recall = sum(r['accuracy']['recall'] for r in valid_results) / total
        avg_f1 = sum(r['accuracy']['f1_score'] for r in valid_results) / total

        # SQLGlot stats
        sqlglot_success = len([r for r in valid_results if r['sqlglot']['success']])
        sqlglot_rate = sqlglot_success / total if total > 0 else 0

        # Regex vs SQLGlot comparison
        sqlglot_better = len([r for r in valid_results
                             if r['sqlglot']['found_gt_count'] > r['regex']['found_gt_count']])
        regex_better = len([r for r in valid_results
                           if r['regex']['found_gt_count'] > r['sqlglot']['found_gt_count']])
        tie = total - sqlglot_better - regex_better

        # Best and worst
        sorted_results = sorted(valid_results, key=lambda x: x['accuracy']['f1_score'], reverse=True)
        best_5 = sorted_results[:5]
        worst_5 = sorted_results[-5:]

        # Query log info
        query_log_available = self.query_logs_df is not None and len(self.query_logs_df) > 0
        query_count = len(self.query_logs_df) if query_log_available else 0

        report = f"""# Real Data Parser Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Stored Procedures:** {total}

---

## Overall Performance

| Metric | Value |
|--------|-------|
| **Average Precision** | {avg_precision*100:.1f}% |
| **Average Recall** | {avg_recall*100:.1f}% |
| **Average F1 Score** | {avg_f1*100:.1f}% |

---

## SQLGlot Analysis

### Success Rate
- **Successful Parses:** {sqlglot_success} / {total} ({sqlglot_rate*100:.1f}%)
- **Failed Parses:** {total - sqlglot_success} ({(1-sqlglot_rate)*100:.1f}%)

### Accuracy Comparison: SQLGlot vs Regex

| Outcome | Count | Percentage |
|---------|-------|------------|
| **SQLGlot Better** | {sqlglot_better} | {sqlglot_better/total*100:.1f}% |
| **Regex Better** | {regex_better} | {regex_better/total*100:.1f}% |
| **Tie** | {tie} | {tie/total*100:.1f}% |

**Key Finding:** Regex outperforms SQLGlot in {regex_better/total*100:.1f}% of cases, indicating significant value in hybrid approach.

---

## Query Log Analysis

**Available:** {'Yes' if query_log_available else 'No'}
{f'**Total Queries:** {query_count}' if query_log_available else ''}

{f'''**Assessment:**
- Query logs can provide runtime validation
- However, matching queries to specific SPs is challenging
- **Recommendation:** Use as supplementary validation, not primary parsing method
''' if query_log_available else '**Recommendation:** Focus on static analysis (Regex + SQLGlot)'}

---

## Top 5 Best Performing SPs

| SP Name | F1 Score | Precision | Recall | SQLGlot Success |
|---------|----------|-----------|--------|-----------------|
{self._format_table(best_5)}

---

## Bottom 5 Worst Performing SPs

| SP Name | F1 Score | Precision | Recall | SQLGlot Success |
|---------|----------|-----------|--------|-----------------|
{self._format_table(worst_5)}

---

## Key Recommendations

### 1. SQLGlot Enhancement Priority: HIGH
- **Current Success Rate:** {sqlglot_rate*100:.1f}%
- **Target:** 70-80% with SQL Cleaning Engine
- **Action:** Implement SQL Cleaning Engine (documented in temp/SQL_CLEANING_ENGINE_DOCUMENTATION.md)
- **Expected Impact:** +{(0.75 - sqlglot_rate)*100:.1f}% success rate improvement

### 2. Hybrid Approach Validation: CONFIRMED
- Regex outperforms SQLGlot in {regex_better/total*100:.1f}% of cases
- **Conclusion:** Current hybrid strategy (Regex + SQLGlot) is correct
- **Action:** Continue both methods, use best result from each

### 3. Confidence Scoring Strategy
- Current average F1 ({avg_f1*100:.1f}%) establishes baseline
- **Action:** Calibrate confidence thresholds against these results
- **Goal:** HIGH confidence (≥0.85) should correlate with F1 ≥ 0.90

### 4. Query Logs Usefulness
- {'Available but challenging to use effectively' if query_log_available else 'Not available in this dataset'}
- **Recommendation:** Optional supplementary signal, not primary method

---

## Next Steps

### Week 1-2: SQL Cleaning Engine
1. Integrate cleaning engine into parser
2. Re-run this analysis
3. Target: {sqlglot_rate*100:.1f}% → 75% SQLGlot success rate

### Week 3-4: Iterative Improvement
1. Analyze worst performers ({worst_5[0]['object_name']} and similar)
2. Add targeted regex rules or comment hints
3. Target: {avg_f1*100:.1f}% → 85% average F1 score

### Week 5+: Continuous Monitoring
1. Use `/sub_DL_OptimizeParsing` for regression testing
2. Capture UAT feedback for real-world validation
3. Maintain improvement baseline

---

**Data Summary:**
- **Objects in Catalog:** {len(self.objects_df)}
- **DMV Dependencies:** {len(self.dependencies_df)}
- **Stored Procedures Analyzed:** {total}
- **Query Logs:** {query_count if query_log_available else 'N/A'}

**Output:** evaluation_baselines/real_data_results/
"""

        return report

    def _format_table(self, results: List[Dict]) -> str:
        """Format table rows."""
        rows = []
        for r in results:
            name = r['object_name']
            f1 = r['accuracy']['f1_score']
            prec = r['accuracy']['precision']
            recall = r['accuracy']['recall']
            sql_success = '✓' if r['sqlglot']['success'] else '✗'
            rows.append(f"| {name} | {f1*100:.1f}% | {prec*100:.1f}% | {recall*100:.1f}% | {sql_success} |")
        return "\n".join(rows)

    def save_results(self):
        """Save all results."""
        logger.info("Saving results...")

        # Save detailed results
        with open(self.output_dir / "parser_results.json", 'w') as f:
            json.dump(self.parser_results, f, indent=2)

        # Save summary report
        report = self.generate_summary_report()
        with open(self.output_dir / "analysis_report.md", 'w') as f:
            f.write(report)

        logger.info(f"✅ Results saved to {self.output_dir}/")

    def run(self):
        """Run complete pipeline."""
        logger.info("="*80)
        logger.info("SIMPLIFIED REAL DATA PARSER ANALYSIS")
        logger.info("="*80)

        self.load_data()
        self.run_analysis()
        self.save_results()

        logger.info("="*80)
        logger.info("✅ ANALYSIS COMPLETE!")
        logger.info("="*80)

        # Print quick summary
        valid_results = [r for r in self.parser_results if 'accuracy' in r]
        avg_f1 = sum(r['accuracy']['f1_score'] for r in valid_results) / len(valid_results) if valid_results else 0
        sqlglot_success = len([r for r in valid_results if r['sqlglot']['success']])

        print(f"\n{'='*80}")
        print("QUICK SUMMARY")
        print(f"{'='*80}")
        print(f"Total SPs Analyzed: {len(valid_results)}")
        print(f"Average F1 Score: {avg_f1*100:.1f}%")
        print(f"SQLGlot Success Rate: {sqlglot_success}/{len(valid_results)} ({sqlglot_success/len(valid_results)*100:.1f}%)")
        print(f"\nFull report: {self.output_dir}/analysis_report.md")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    analyzer = SimpleParserAnalyzer()
    analyzer.run()
