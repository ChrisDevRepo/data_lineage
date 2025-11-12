#!/usr/bin/env python3
"""
Real Data Parser Analysis Script
=================================

Comprehensive evaluation of parser performance on real production data.

This script:
1. Loads real data from parquet files (objects, dependencies, definitions, etc.)
2. Runs our parser on all stored procedures
3. Compares results against ground truth (DMV dependencies)
4. Analyzes SQLGlot vs Regex performance
5. Evaluates confidence scoring accuracy
6. Assesses query log usefulness
7. Generates detailed reports

Usage:
    python evaluation/real_data_analysis.py

Output:
    evaluation/real_data_results/
    ├── parser_results.json          # Full parser output
    ├── analysis_report.md           # Comprehensive analysis
    ├── sqlglot_analysis.json        # SQLGlot success rate details
    ├── confidence_analysis.json     # Confidence scoring evaluation
    └── query_log_analysis.json      # Query log usefulness assessment

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

# Add lineage_v3 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
from lineage_v3.parsers.comment_hints_parser import CommentHintsParser
from lineage_v3.utils.confidence_calculator import ConfidenceCalculator
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealDataAnalyzer:
    """Analyzes parser performance on real production data."""

    def __init__(self, parquet_dir: str = "temp"):
        """
        Initialize analyzer with parquet data directory.

        Args:
            parquet_dir: Directory containing parquet files
        """
        self.parquet_dir = Path(parquet_dir)
        self.output_dir = Path("evaluation/real_data_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.objects_df = None
        self.dependencies_df = None
        self.definitions_df = None
        self.table_columns_df = None
        self.query_logs_df = None

        # Analysis results
        self.parser_results = []
        self.sqlglot_analysis = {}
        self.confidence_analysis = {}
        self.query_log_analysis = {}

        # Initialize DuckDB workspace for parser
        workspace_file = self.output_dir / "analysis_workspace.duckdb"
        self.workspace = DuckDBWorkspace(str(workspace_file))

        # Initialize parsers
        self.quality_parser = QualityAwareParser(self.workspace)
        self.hint_parser = CommentHintsParser()

    def load_data(self):
        """Load all parquet files into dataframes."""
        logger.info("Loading parquet files...")

        conn = duckdb.connect(':memory:')

        # Find all parquet files
        parquet_files = list(self.parquet_dir.glob("*.parquet"))
        logger.info(f"Found {len(parquet_files)} parquet files")

        # Load each file and identify by schema
        for pf in parquet_files:
            df = conn.execute(f"SELECT * FROM '{pf}'").df()
            cols = set(df.columns)

            # Identify file by columns
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

        # Validate required data
        if self.objects_df is None or self.dependencies_df is None or self.definitions_df is None:
            raise ValueError("Missing required parquet files (objects, dependencies, definitions)")

        logger.info("✅ All data loaded successfully")

    def build_ground_truth(self) -> Dict[int, Set[str]]:
        """
        Build ground truth dependency map from DMV data.

        Returns:
            Dict mapping object_id -> set of fully qualified dependency names
        """
        logger.info("Building ground truth from DMV dependencies...")

        ground_truth = defaultdict(set)

        for _, row in self.dependencies_df.iterrows():
            ref_obj_id = row['referencing_object_id']
            schema = row['referenced_schema_name']
            name = row['referenced_entity_name']

            # Create fully qualified name
            fqn = f"{schema}.{name}" if schema else name
            ground_truth[ref_obj_id].add(fqn)

        logger.info(f"✓ Ground truth built for {len(ground_truth)} objects")
        return dict(ground_truth)

    def build_catalog(self) -> Set[str]:
        """
        Build catalog of all known objects.

        Returns:
            Set of fully qualified object names
        """
        logger.info("Building catalog...")

        catalog = set()

        for _, row in self.objects_df.iterrows():
            schema = row['schema_name']
            name = row['object_name']
            fqn = f"{schema}.{name}" if schema else name
            catalog.add(fqn)

        logger.info(f"✓ Catalog built with {len(catalog)} objects")
        return catalog

    def analyze_stored_procedure(
        self,
        obj_id: int,
        obj_name: str,
        schema_name: str,
        definition: str,
        ground_truth: Set[str],
        catalog: Set[str]
    ) -> Dict[str, Any]:
        """
        Analyze a single stored procedure.

        Returns:
            Detailed analysis results
        """
        fqn = f"{schema_name}.{obj_name}"

        # Parse with our parser
        try:
            result = self.quality_parser.parse(definition)

            # Extract comment hints
            hints = self.hint_parser.parse(definition)
            has_hints = bool(hints.inputs or hints.outputs)

            # Get parsed dependencies
            parsed_sources = set()
            parsed_targets = set()

            for source in result.get('sources', []):
                if '.' in source:
                    parsed_sources.add(source)
                else:
                    # Try to resolve schema
                    parsed_sources.add(f"{schema_name}.{source}")

            for target in result.get('targets', []):
                if '.' in target:
                    parsed_targets.add(target)
                else:
                    parsed_targets.add(f"{schema_name}.{target}")

            # Combine sources and targets for comparison with ground truth
            all_parsed = parsed_sources | parsed_targets

            # Calculate metrics vs ground truth
            true_positives = len(all_parsed & ground_truth)
            false_positives = len(all_parsed - ground_truth)
            false_negatives = len(ground_truth - all_parsed)

            precision = true_positives / len(all_parsed) if all_parsed else 0.0
            recall = true_positives / len(ground_truth) if ground_truth else 1.0
            f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            # Catalog validation
            catalog_valid = len(all_parsed & catalog)
            catalog_invalid = len(all_parsed - catalog)
            catalog_validation_rate = catalog_valid / len(all_parsed) if all_parsed else 1.0

            # SQLGlot analysis
            sqlglot_data = result.get('sqlglot', {})
            regex_data = result.get('regex', {})

            sqlglot_success = not sqlglot_data.get('fallback_mode', False)

            # Method comparison
            regex_sources = set(regex_data.get('sources', []))
            regex_targets = set(regex_data.get('targets', []))
            sqlglot_sources = set(sqlglot_data.get('sources', []))
            sqlglot_targets = set(sqlglot_data.get('targets', []))

            # Calculate which method found ground truth
            regex_found = len((regex_sources | regex_targets) & ground_truth)
            sqlglot_found = len((sqlglot_sources | sqlglot_targets) & ground_truth)

            return {
                'object_id': obj_id,
                'object_name': fqn,
                'definition_size': len(definition),
                'has_comment_hints': has_hints,
                'ground_truth': {
                    'count': len(ground_truth),
                    'dependencies': sorted(ground_truth)
                },
                'parsed': {
                    'sources_count': len(parsed_sources),
                    'targets_count': len(parsed_targets),
                    'total_count': len(all_parsed),
                    'all_dependencies': sorted(all_parsed)
                },
                'accuracy': {
                    'true_positives': true_positives,
                    'false_positives': false_positives,
                    'false_negatives': false_negatives,
                    'precision': round(precision, 4),
                    'recall': round(recall, 4),
                    'f1_score': round(f1_score, 4)
                },
                'catalog_validation': {
                    'valid_count': catalog_valid,
                    'invalid_count': catalog_invalid,
                    'validation_rate': round(catalog_validation_rate, 4),
                    'invalid_objects': sorted(all_parsed - catalog)
                },
                'sqlglot': {
                    'success': sqlglot_success,
                    'sources_count': len(sqlglot_sources),
                    'targets_count': len(sqlglot_targets),
                    'found_ground_truth_count': sqlglot_found,
                    'fallback_mode': sqlglot_data.get('fallback_mode', False)
                },
                'regex': {
                    'sources_count': len(regex_sources),
                    'targets_count': len(regex_targets),
                    'found_ground_truth_count': regex_found
                },
                'confidence': {
                    'score': result.get('confidence', 0.0),
                    'label': result.get('confidence_label', 'Unknown')
                },
                'missed_dependencies': sorted(ground_truth - all_parsed),
                'false_positives_list': sorted(all_parsed - ground_truth)
            }

        except Exception as e:
            logger.error(f"Error parsing {fqn}: {str(e)}")
            return {
                'object_id': obj_id,
                'object_name': fqn,
                'error': str(e),
                'ground_truth': {
                    'count': len(ground_truth),
                    'dependencies': sorted(ground_truth)
                }
            }

    def run_analysis(self):
        """Run complete analysis on all stored procedures."""
        logger.info("Starting comprehensive parser analysis...")

        # Build ground truth and catalog
        ground_truth_map = self.build_ground_truth()
        catalog = self.build_catalog()

        # Get all stored procedures
        # Merge to get object_type, but keep only definitions columns
        sp_defs = self.definitions_df.merge(
            self.objects_df[['object_id', 'object_type']],
            on='object_id',
            how='inner'
        )

        # Filter to stored procedures only
        sp_defs = sp_defs[sp_defs['object_type'].str.contains('PROCEDURE|P', case=False, na=False)]

        logger.info(f"Analyzing {len(sp_defs)} stored procedures...")

        # Analyze each SP
        for idx, row in sp_defs.iterrows():
            obj_id = row['object_id']
            obj_name = row['object_name']
            schema_name = row['schema_name']
            definition = row['definition']

            # Get ground truth for this SP
            gt = ground_truth_map.get(obj_id, set())

            # Analyze
            result = self.analyze_stored_procedure(
                obj_id, obj_name, schema_name, definition, gt, catalog
            )

            self.parser_results.append(result)

            if (idx + 1) % 50 == 0:
                logger.info(f"Progress: {idx + 1}/{len(sp_defs)} SPs analyzed")

        logger.info("✅ Analysis complete!")

    def generate_sqlglot_analysis(self):
        """Analyze SQLGlot success rate and performance."""
        logger.info("Generating SQLGlot analysis...")

        sqlglot_successful = [r for r in self.parser_results if not r.get('error') and r.get('sqlglot', {}).get('success', False)]
        sqlglot_failed = [r for r in self.parser_results if not r.get('error') and not r.get('sqlglot', {}).get('success', False)]

        total = len(sqlglot_successful) + len(sqlglot_failed)
        success_rate = len(sqlglot_successful) / total if total > 0 else 0.0

        # Compare SQLGlot vs Regex accuracy
        sqlglot_better = 0
        regex_better = 0
        tie = 0

        for r in self.parser_results:
            if r.get('error'):
                continue

            sg_found = r.get('sqlglot', {}).get('found_ground_truth_count', 0)
            rg_found = r.get('regex', {}).get('found_ground_truth_count', 0)

            if sg_found > rg_found:
                sqlglot_better += 1
            elif rg_found > sg_found:
                regex_better += 1
            else:
                tie += 1

        self.sqlglot_analysis = {
            'success_rate': round(success_rate, 4),
            'successful_count': len(sqlglot_successful),
            'failed_count': len(sqlglot_failed),
            'total_count': total,
            'accuracy_comparison': {
                'sqlglot_better': sqlglot_better,
                'regex_better': regex_better,
                'tie': tie
            },
            'examples': {
                'successful': [r['object_name'] for r in sqlglot_successful[:5]],
                'failed': [r['object_name'] for r in sqlglot_failed[:5]]
            }
        }

        logger.info(f"✓ SQLGlot success rate: {success_rate*100:.1f}%")

    def generate_confidence_analysis(self):
        """Analyze confidence scoring accuracy."""
        logger.info("Generating confidence analysis...")

        # Group by confidence level
        high_conf = [r for r in self.parser_results if not r.get('error') and r.get('confidence', {}).get('score', 0) >= 0.85]
        med_conf = [r for r in self.parser_results if not r.get('error') and 0.75 <= r.get('confidence', {}).get('score', 0) < 0.85]
        low_conf = [r for r in self.parser_results if not r.get('error') and r.get('confidence', {}).get('score', 0) < 0.75]

        # Calculate actual accuracy for each confidence level
        def calc_avg_f1(results):
            if not results:
                return 0.0
            f1_scores = [r.get('accuracy', {}).get('f1_score', 0) for r in results]
            return sum(f1_scores) / len(f1_scores)

        self.confidence_analysis = {
            'high_confidence': {
                'count': len(high_conf),
                'avg_f1_score': round(calc_avg_f1(high_conf), 4),
                'avg_precision': round(sum(r.get('accuracy', {}).get('precision', 0) for r in high_conf) / len(high_conf) if high_conf else 0, 4),
                'avg_recall': round(sum(r.get('accuracy', {}).get('recall', 0) for r in high_conf) / len(high_conf) if high_conf else 0, 4)
            },
            'medium_confidence': {
                'count': len(med_conf),
                'avg_f1_score': round(calc_avg_f1(med_conf), 4),
                'avg_precision': round(sum(r.get('accuracy', {}).get('precision', 0) for r in med_conf) / len(med_conf) if med_conf else 0, 4),
                'avg_recall': round(sum(r.get('accuracy', {}).get('recall', 0) for r in med_conf) / len(med_conf) if med_conf else 0, 4)
            },
            'low_confidence': {
                'count': len(low_conf),
                'avg_f1_score': round(calc_avg_f1(low_conf), 4),
                'avg_precision': round(sum(r.get('accuracy', {}).get('precision', 0) for r in low_conf) / len(low_conf) if low_conf else 0, 4),
                'avg_recall': round(sum(r.get('accuracy', {}).get('recall', 0) for r in low_conf) / len(low_conf) if low_conf else 0, 4)
            },
            'calibration': {
                'high_conf_accurate': len([r for r in high_conf if r.get('accuracy', {}).get('f1_score', 0) >= 0.90]),
                'high_conf_inaccurate': len([r for r in high_conf if r.get('accuracy', {}).get('f1_score', 0) < 0.90]),
                'false_confidence_rate': round(len([r for r in high_conf if r.get('accuracy', {}).get('f1_score', 0) < 0.90]) / len(high_conf) if high_conf else 0, 4)
            }
        }

        logger.info(f"✓ Confidence calibration: {self.confidence_analysis['calibration']['false_confidence_rate']*100:.1f}% false confidence rate")

    def generate_query_log_analysis(self):
        """Analyze query log usefulness."""
        logger.info("Generating query log analysis...")

        if self.query_logs_df is None or len(self.query_logs_df) == 0:
            self.query_log_analysis = {
                'available': False,
                'message': 'No query logs available'
            }
            logger.info("✓ No query logs available")
            return

        # Analyze query log content
        total_queries = len(self.query_logs_df)

        # Count different query types
        query_types = Counter()
        for _, row in self.query_logs_df.iterrows():
            text = row['command_text'].lower()
            if 'select' in text:
                query_types['SELECT'] += 1
            if 'insert' in text:
                query_types['INSERT'] += 1
            if 'update' in text:
                query_types['UPDATE'] += 1
            if 'delete' in text:
                query_types['DELETE'] += 1
            if 'exec' in text or 'execute' in text:
                query_types['EXEC'] += 1

        self.query_log_analysis = {
            'available': True,
            'total_queries': total_queries,
            'query_types': dict(query_types),
            'coverage': {
                'total_sps': len(self.parser_results),
                'note': 'Query logs could be used for runtime validation but require matching to specific SPs'
            },
            'usefulness_assessment': {
                'pros': [
                    'Can validate runtime behavior',
                    'Shows actual usage patterns',
                    'Can identify frequently used dependencies'
                ],
                'cons': [
                    'Hard to match queries to specific SPs',
                    'May not cover all code paths',
                    'Privacy/security concerns'
                ],
                'recommendation': 'Use as optional validation, not primary parsing method'
            }
        }

        logger.info(f"✓ Query log analysis complete: {total_queries} queries")

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report."""
        logger.info("Generating markdown report...")

        # Calculate overall stats
        total_sps = len([r for r in self.parser_results if not r.get('error')])
        avg_precision = sum(r.get('accuracy', {}).get('precision', 0) for r in self.parser_results if not r.get('error')) / total_sps if total_sps > 0 else 0
        avg_recall = sum(r.get('accuracy', {}).get('recall', 0) for r in self.parser_results if not r.get('error')) / total_sps if total_sps > 0 else 0
        avg_f1 = sum(r.get('accuracy', {}).get('f1_score', 0) for r in self.parser_results if not r.get('error')) / total_sps if total_sps > 0 else 0

        # Find best and worst cases
        sorted_by_f1 = sorted([r for r in self.parser_results if not r.get('error')],
                             key=lambda x: x.get('accuracy', {}).get('f1_score', 0),
                             reverse=True)
        best_cases = sorted_by_f1[:5]
        worst_cases = sorted_by_f1[-5:]

        report = f"""# Real Data Parser Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Analyzer Version:** 1.0.0
**Parser Version:** 4.2.0

---

## Executive Summary

### Overall Performance

| Metric | Value |
|--------|-------|
| **Total Stored Procedures** | {total_sps} |
| **Average Precision** | {avg_precision*100:.1f}% |
| **Average Recall** | {avg_recall*100:.1f}% |
| **Average F1 Score** | {avg_f1*100:.1f}% |
| **SQLGlot Success Rate** | {self.sqlglot_analysis['success_rate']*100:.1f}% |

### Confidence Distribution

| Level | Count | Avg F1 Score | False Confidence Rate |
|-------|-------|--------------|----------------------|
| **HIGH (≥0.85)** | {self.confidence_analysis['high_confidence']['count']} | {self.confidence_analysis['high_confidence']['avg_f1_score']*100:.1f}% | {self.confidence_analysis['calibration']['false_confidence_rate']*100:.1f}% |
| **MEDIUM (0.75-0.84)** | {self.confidence_analysis['medium_confidence']['count']} | {self.confidence_analysis['medium_confidence']['avg_f1_score']*100:.1f}% | N/A |
| **LOW (<0.75)** | {self.confidence_analysis['low_confidence']['count']} | {self.confidence_analysis['low_confidence']['avg_f1_score']*100:.1f}% | N/A |

---

## 1. SQLGlot Analysis

### Success Rate

**Overall:** {self.sqlglot_analysis['success_rate']*100:.1f}% ({self.sqlglot_analysis['successful_count']}/{self.sqlglot_analysis['total_count']} SPs)

### Accuracy Comparison: SQLGlot vs Regex

| Outcome | Count | Percentage |
|---------|-------|------------|
| **SQLGlot Better** | {self.sqlglot_analysis['accuracy_comparison']['sqlglot_better']} | {self.sqlglot_analysis['accuracy_comparison']['sqlglot_better']/total_sps*100:.1f}% |
| **Regex Better** | {self.sqlglot_analysis['accuracy_comparison']['regex_better']} | {self.sqlglot_analysis['accuracy_comparison']['regex_better']/total_sps*100:.1f}% |
| **Tie** | {self.sqlglot_analysis['accuracy_comparison']['tie']} | {self.sqlglot_analysis['accuracy_comparison']['tie']/total_sps*100:.1f}% |

### Key Findings

**✅ SQLGlot Strengths:**
- Successfully parses {self.sqlglot_analysis['successful_count']} stored procedures
- When successful, provides structured AST parsing
- Better than regex in {self.sqlglot_analysis['accuracy_comparison']['sqlglot_better']} cases

**❌ SQLGlot Limitations:**
- Fails on {self.sqlglot_analysis['failed_count']} stored procedures ({(1-self.sqlglot_analysis['success_rate'])*100:.1f}%)
- Likely due to T-SQL specific constructs (TRY/CATCH, DECLARE, etc.)
- Regex outperforms in {self.sqlglot_analysis['accuracy_comparison']['regex_better']} cases

**📊 Recommendation:**
- Continue hybrid approach: SQLGlot + Regex
- Consider SQL Cleaning Engine (documented in PARSING_REVIEW_STATUS.md)
- SQL Cleaning Engine achieved 100% SQLGlot success in tests

---

## 2. Confidence Scoring Evaluation

### Calibration Analysis

**Question:** When our parser says HIGH confidence (≥0.85), is it actually accurate?

| Confidence Level | Avg Actual F1 | Calibration Quality |
|------------------|---------------|---------------------|
| HIGH (≥0.85) | {self.confidence_analysis['high_confidence']['avg_f1_score']*100:.1f}% | {'✅ GOOD' if self.confidence_analysis['high_confidence']['avg_f1_score'] >= 0.85 else '⚠️ NEEDS IMPROVEMENT'} |
| MEDIUM (0.75-0.84) | {self.confidence_analysis['medium_confidence']['avg_f1_score']*100:.1f}% | {'✅ GOOD' if self.confidence_analysis['medium_confidence']['avg_f1_score'] >= 0.70 else '⚠️ NEEDS IMPROVEMENT'} |
| LOW (<0.75) | {self.confidence_analysis['low_confidence']['avg_f1_score']*100:.1f}% | {'✅ GOOD' if self.confidence_analysis['low_confidence']['avg_f1_score'] < 0.75 else '⚠️ NEEDS IMPROVEMENT'} |

### False Confidence Rate

**Critical Metric:** {self.confidence_analysis['calibration']['false_confidence_rate']*100:.1f}% of HIGH confidence predictions are actually inaccurate (F1 < 0.90)

- **Target:** <5% false confidence rate
- **Actual:** {self.confidence_analysis['calibration']['false_confidence_rate']*100:.1f}%
- **Status:** {'✅ MEETS TARGET' if self.confidence_analysis['calibration']['false_confidence_rate'] < 0.05 else '❌ NEEDS IMPROVEMENT'}

### Detailed Breakdown

**HIGH Confidence (≥0.85):**
- Count: {self.confidence_analysis['high_confidence']['count']} SPs
- Avg Precision: {self.confidence_analysis['high_confidence']['avg_precision']*100:.1f}%
- Avg Recall: {self.confidence_analysis['high_confidence']['avg_recall']*100:.1f}%
- Avg F1: {self.confidence_analysis['high_confidence']['avg_f1_score']*100:.1f}%
- Accurate (F1≥0.90): {self.confidence_analysis['calibration']['high_conf_accurate']} SPs
- Inaccurate (F1<0.90): {self.confidence_analysis['calibration']['high_conf_inaccurate']} SPs

**MEDIUM Confidence (0.75-0.84):**
- Count: {self.confidence_analysis['medium_confidence']['count']} SPs
- Avg Precision: {self.confidence_analysis['medium_confidence']['avg_precision']*100:.1f}%
- Avg Recall: {self.confidence_analysis['medium_confidence']['avg_recall']*100:.1f}%
- Avg F1: {self.confidence_analysis['medium_confidence']['avg_f1_score']*100:.1f}%

**LOW Confidence (<0.75):**
- Count: {self.confidence_analysis['low_confidence']['count']} SPs
- Avg Precision: {self.confidence_analysis['low_confidence']['avg_precision']*100:.1f}%
- Avg Recall: {self.confidence_analysis['low_confidence']['avg_recall']*100:.1f}%
- Avg F1: {self.confidence_analysis['low_confidence']['avg_f1_score']*100:.1f}%

---

## 3. Query Log Analysis

**Available:** {'Yes' if self.query_log_analysis.get('available', False) else 'No'}

{self._format_query_log_section()}

---

## 4. Best and Worst Cases

### Top 5 Performing SPs (Highest F1 Scores)

| SP Name | F1 Score | Precision | Recall | Confidence |
|---------|----------|-----------|--------|------------|
{self._format_case_table(best_cases)}

### Bottom 5 Performing SPs (Lowest F1 Scores)

| SP Name | F1 Score | Precision | Recall | Confidence |
|---------|----------|-----------|--------|------------|
{self._format_case_table(worst_cases)}

---

## 5. Recommendations

### Immediate Actions

1. **{'✅ Confidence Scoring is Reliable' if self.confidence_analysis['calibration']['false_confidence_rate'] < 0.05 else '⚠️ Improve Confidence Calibration'}**
   - {'Current false confidence rate is acceptable' if self.confidence_analysis['calibration']['false_confidence_rate'] < 0.05 else f'False confidence rate ({self.confidence_analysis["calibration"]["false_confidence_rate"]*100:.1f}%) exceeds 5% target'}
   - {'Continue monitoring with UAT feedback' if self.confidence_analysis['calibration']['false_confidence_rate'] < 0.05 else 'Review multi-factor confidence model weights'}

2. **SQLGlot Enhancement**
   - Implement SQL Cleaning Engine (temp/SQL_CLEANING_ENGINE_DOCUMENTATION.md)
   - Expected improvement: {self.sqlglot_analysis['success_rate']*100:.1f}% → 70-80% success rate
   - Will boost confidence scores by 0.10-0.15 on average

3. **Query Logs**
   - {'Use as optional validation signal' if self.query_log_analysis.get('available') else 'Not available for this dataset'}
   - {'Do not rely on as primary parsing method' if self.query_log_analysis.get('available') else 'Focus on static analysis methods'}

### Testing Strategy

1. **Baseline Management**
   - Use `/sub_DL_OptimizeParsing` for all parser changes
   - Create baseline before changes: Current performance established
   - Run full evaluation after changes
   - Zero regressions policy

2. **Continuous Improvement**
   - Focus on {worst_cases[0]['object_name'] if worst_cases else 'low-performing SPs'}
   - Use UAT feedback system for real-world validation
   - Add comment hints for edge cases
   - Monitor false confidence rate

---

## 6. Next Steps

### Week 1-2: SQL Cleaning Engine Integration
- Integrate cleaning engine into quality_aware_parser.py
- Run full evaluation on {total_sps} SPs
- Measure impact on SQLGlot success rate
- Target: 70-80% SQLGlot success (currently {self.sqlglot_analysis['success_rate']*100:.1f}%)

### Week 3-4: Confidence Model Refinement
- Analyze {self.confidence_analysis['calibration']['high_conf_inaccurate']} false positive cases
- Adjust multi-factor weights if needed
- Validate with UAT feedback
- Target: <5% false confidence rate

### Week 5-6: Rule Expansion
- Add CURSOR handling rules
- Add WHILE loop rules
- Add IF/ELSE logic rules
- Target: 80%+ average F1 score

---

## Appendix: Data Summary

**Objects:** {len(self.objects_df)} total objects
**Dependencies (DMV):** {len(self.dependencies_df)} dependency relationships
**Definitions:** {len(self.definitions_df)} stored procedure definitions
**Table Columns:** {len(self.table_columns_df) if self.table_columns_df is not None else 0} columns
**Query Logs:** {len(self.query_logs_df) if self.query_logs_df is not None else 0} queries

**Ground Truth Coverage:** {len([r for r in self.parser_results if not r.get('error') and r.get('ground_truth', {}).get('count', 0) > 0])} SPs have ground truth dependencies

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Output Directory:** evaluation/real_data_results/
"""
        return report

    def _format_query_log_section(self) -> str:
        """Format query log section of report."""
        if not self.query_log_analysis.get('available', False):
            return f"**Message:** {self.query_log_analysis.get('message', 'N/A')}\n"

        section = f"""
**Total Queries:** {self.query_log_analysis['total_queries']}

**Query Type Distribution:**
"""
        for qtype, count in self.query_log_analysis['query_types'].items():
            section += f"- {qtype}: {count}\n"

        section += f"""
**Usefulness Assessment:**

**Pros:**
"""
        for pro in self.query_log_analysis['usefulness_assessment']['pros']:
            section += f"- {pro}\n"

        section += "\n**Cons:**\n"
        for con in self.query_log_analysis['usefulness_assessment']['cons']:
            section += f"- {con}\n"

        section += f"\n**Recommendation:** {self.query_log_analysis['usefulness_assessment']['recommendation']}\n"

        return section

    def _format_case_table(self, cases: List[Dict]) -> str:
        """Format case table rows."""
        rows = []
        for case in cases:
            name = case['object_name']
            f1 = case.get('accuracy', {}).get('f1_score', 0)
            precision = case.get('accuracy', {}).get('precision', 0)
            recall = case.get('accuracy', {}).get('recall', 0)
            conf = case.get('confidence', {}).get('score', 0)
            rows.append(f"| {name} | {f1*100:.1f}% | {precision*100:.1f}% | {recall*100:.1f}% | {conf:.2f} |")

        return "\n".join(rows)

    def save_results(self):
        """Save all results to files."""
        logger.info("Saving results...")

        # Save parser results
        with open(self.output_dir / "parser_results.json", 'w') as f:
            json.dump(self.parser_results, f, indent=2)

        # Save SQLGlot analysis
        with open(self.output_dir / "sqlglot_analysis.json", 'w') as f:
            json.dump(self.sqlglot_analysis, f, indent=2)

        # Save confidence analysis
        with open(self.output_dir / "confidence_analysis.json", 'w') as f:
            json.dump(self.confidence_analysis, f, indent=2)

        # Save query log analysis
        with open(self.output_dir / "query_log_analysis.json", 'w') as f:
            json.dump(self.query_log_analysis, f, indent=2)

        # Save markdown report
        report = self.generate_markdown_report()
        with open(self.output_dir / "analysis_report.md", 'w') as f:
            f.write(report)

        logger.info(f"✅ Results saved to {self.output_dir}/")

    def run(self):
        """Run complete analysis pipeline."""
        logger.info("="*80)
        logger.info("REAL DATA PARSER ANALYSIS")
        logger.info("="*80)

        try:
            self.load_data()
            self.run_analysis()
            self.generate_sqlglot_analysis()
            self.generate_confidence_analysis()
            self.generate_query_log_analysis()
            self.save_results()

            logger.info("="*80)
            logger.info("✅ ANALYSIS COMPLETE!")
            logger.info("="*80)
            logger.info(f"Results saved to: {self.output_dir}/")
            logger.info("Main report: analysis_report.md")

            # Print summary
            print(f"\n{'='*80}")
            print("SUMMARY")
            print(f"{'='*80}")
            print(f"Total SPs: {len([r for r in self.parser_results if not r.get('error')])}")
            print(f"SQLGlot Success Rate: {self.sqlglot_analysis['success_rate']*100:.1f}%")
            print(f"High Confidence SPs: {self.confidence_analysis['high_confidence']['count']}")
            print(f"False Confidence Rate: {self.confidence_analysis['calibration']['false_confidence_rate']*100:.1f}%")
            print(f"\nSee {self.output_dir}/analysis_report.md for full report")
            print(f"{'='*80}\n")

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise


if __name__ == '__main__':
    analyzer = RealDataAnalyzer()
    analyzer.run()
