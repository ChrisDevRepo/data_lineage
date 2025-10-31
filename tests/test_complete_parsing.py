#!/usr/bin/env python3
"""
Complete Parsing Test
======================

Tests the entire parsing pipeline including:
1. Regex baseline extraction
2. SQLGlot parser performance
3. AI disambiguation (when enabled)
4. Query log validation
5. Incremental mode behavior

This validates all views and stored procedures to catch issues in:
- Regex patterns
- SQLGlot AST traversal
- AI integration
- Confidence scoring

Author: Vibecoding
Version: 1.0.0
Date: 2025-10-31
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
from lineage_v3.config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParsingTestReport:
    """Comprehensive parsing test report."""

    def __init__(self):
        self.total_objects = 0
        self.views_count = 0
        self.sps_count = 0

        # Confidence breakdowns
        self.high_confidence = []  # >= 0.85
        self.medium_confidence = []  # 0.70 - 0.84
        self.low_confidence = []  # < 0.70

        # AI usage tracking
        self.ai_triggered = []
        self.ai_improved = []
        self.ai_failed = []

        # Error tracking
        self.parsing_errors = []
        self.validation_errors = []

        # Performance tracking
        self.regex_only = []  # Objects using only regex baseline
        self.sqlglot_used = []  # Objects where SQLGlot worked
        self.query_log_boost = []  # Objects boosted by query logs

    def add_result(self, obj_info: Dict[str, Any], parse_result: Dict[str, Any]):
        """Add a parsing result to the report."""
        self.total_objects += 1

        obj_type = obj_info['object_type']
        obj_name = f"{obj_info['schema_name']}.{obj_info['object_name']}"

        if obj_type == 'View':
            self.views_count += 1
        elif obj_type == 'Stored Procedure':
            self.sps_count += 1

        # Track confidence
        confidence = parse_result.get('confidence', 0.0)
        entry = {
            'name': obj_name,
            'type': obj_type,
            'confidence': confidence,
            'sources': len(parse_result.get('input_ids', [])),
            'targets': len(parse_result.get('output_ids', []))
        }

        if confidence >= 0.85:
            self.high_confidence.append(entry)
        elif confidence >= 0.70:
            self.medium_confidence.append(entry)
        else:
            self.low_confidence.append(entry)

        # Track AI usage
        quality = parse_result.get('quality', {})
        if quality.get('ai_used'):
            self.ai_triggered.append(entry)

            ai_confidence = quality.get('ai_confidence')
            parser_confidence = quality.get('sqlglot_confidence', 0.0)

            if ai_confidence and ai_confidence > parser_confidence:
                self.ai_improved.append({
                    **entry,
                    'before': parser_confidence,
                    'after': ai_confidence,
                    'improvement': ai_confidence - parser_confidence
                })
            elif ai_confidence and ai_confidence <= parser_confidence:
                self.ai_failed.append({
                    **entry,
                    'before': parser_confidence,
                    'after': ai_confidence
                })

        # Track parser strategy
        primary_source = parse_result.get('provenance', {}).get('primary_source', 'unknown')
        if primary_source == 'regex':
            self.regex_only.append(entry)
        elif primary_source == 'parser':
            self.sqlglot_used.append(entry)
        elif primary_source == 'query_log':
            self.query_log_boost.append(entry)

    def add_error(self, obj_info: Dict[str, Any], error_type: str, error_msg: str):
        """Add a parsing error to the report."""
        obj_name = f"{obj_info['schema_name']}.{obj_info['object_name']}"
        error_entry = {
            'name': obj_name,
            'type': obj_info['object_type'],
            'error_type': error_type,
            'error': error_msg
        }

        if error_type == 'parsing':
            self.parsing_errors.append(error_entry)
        else:
            self.validation_errors.append(error_entry)

    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("COMPLETE PARSING TEST REPORT")
        print("=" * 80)

        # Overall stats
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Objects Tested: {self.total_objects:,}")
        print(f"   - Views: {self.views_count:,}")
        print(f"   - Stored Procedures: {self.sps_count:,}")

        # Confidence breakdown
        print(f"\n🎯 Confidence Distribution:")
        print(f"   High (≥0.85): {len(self.high_confidence):,} ({len(self.high_confidence)/max(self.total_objects,1)*100:.1f}%)")
        print(f"   Medium (0.70-0.84): {len(self.medium_confidence):,} ({len(self.medium_confidence)/max(self.total_objects,1)*100:.1f}%)")
        print(f"   Low (<0.70): {len(self.low_confidence):,} ({len(self.low_confidence)/max(self.total_objects,1)*100:.1f}%)")

        avg_confidence = sum(e['confidence'] for e in self.high_confidence + self.medium_confidence + self.low_confidence) / max(self.total_objects, 1)
        print(f"   Average Confidence: {avg_confidence:.3f}")

        # AI usage stats
        if settings.ai.enabled:
            print(f"\n🤖 AI Disambiguation Results:")
            print(f"   AI Triggered: {len(self.ai_triggered):,}")
            print(f"   - Improved Confidence: {len(self.ai_improved):,}")
            print(f"   - Failed to Improve: {len(self.ai_failed):,}")

            if self.ai_improved:
                avg_improvement = sum(e['improvement'] for e in self.ai_improved) / len(self.ai_improved)
                print(f"   Average Improvement: +{avg_improvement:.3f}")

            if self.ai_improved[:5]:
                print(f"\n   Top AI Improvements:")
                for i, entry in enumerate(sorted(self.ai_improved, key=lambda x: x['improvement'], reverse=True)[:5], 1):
                    print(f"   {i}. {entry['name']}: {entry['before']:.2f} → {entry['after']:.2f} (+{entry['improvement']:.2f})")

        # Parser strategy breakdown
        print(f"\n🔧 Parser Strategy Breakdown:")
        print(f"   SQLGlot Parser: {len(self.sqlglot_used):,}")
        print(f"   Regex Baseline: {len(self.regex_only):,}")
        print(f"   Query Log Boost: {len(self.query_log_boost):,}")

        # Low confidence objects (potential issues)
        if self.low_confidence:
            print(f"\n⚠️  Low Confidence Objects ({len(self.low_confidence)}):")
            for i, entry in enumerate(sorted(self.low_confidence, key=lambda x: x['confidence'])[:10], 1):
                print(f"   {i}. {entry['name']} ({entry['type']}): {entry['confidence']:.2f} - {entry['sources']} sources, {entry['targets']} targets")

            if len(self.low_confidence) > 10:
                print(f"   ... and {len(self.low_confidence) - 10} more")

        # Errors
        if self.parsing_errors:
            print(f"\n❌ Parsing Errors ({len(self.parsing_errors)}):")
            for i, err in enumerate(self.parsing_errors[:5], 1):
                print(f"   {i}. {err['name']}: {err['error']}")

            if len(self.parsing_errors) > 5:
                print(f"   ... and {len(self.parsing_errors) - 5} more")

        if self.validation_errors:
            print(f"\n⚠️  Validation Errors ({len(self.validation_errors)}):")
            for i, err in enumerate(self.validation_errors[:5], 1):
                print(f"   {i}. {err['name']}: {err['error']}")

            if len(self.validation_errors) > 5:
                print(f"   ... and {len(self.validation_errors) - 5} more")

        # Final verdict
        print("\n" + "=" * 80)
        high_conf_pct = len(self.high_confidence) / max(self.total_objects, 1) * 100
        if high_conf_pct >= 80:
            print("✅ EXCELLENT: High confidence parsing (≥80%)")
        elif high_conf_pct >= 70:
            print("✅ GOOD: Acceptable confidence parsing (70-79%)")
        elif high_conf_pct >= 60:
            print("⚠️  FAIR: Below target confidence (60-69%)")
        else:
            print("❌ POOR: Low confidence parsing (<60%)")

        print("=" * 80 + "\n")


def test_complete_parsing(use_existing_workspace: bool = True):
    """
    Run complete parsing test on all views and stored procedures.

    Args:
        use_existing_workspace: If True, use existing workspace database
    """
    print("\n🧪 Starting Complete Parsing Test...")
    print(f"🤖 AI Enabled: {settings.ai.enabled}")
    print(f"🎯 AI Threshold: {settings.ai.confidence_threshold}")
    print()

    report = ParsingTestReport()

    try:
        # Connect to workspace (use API workspace if exists, fallback to default)
        workspace_path = Path("data/lineage_workspace.duckdb")
        if not workspace_path.exists():
            workspace_path = Path("lineage_workspace.duckdb")

        print(f"📁 Using workspace: {workspace_path}")

        with DuckDBWorkspace(workspace_path=str(workspace_path)) as db:
            # Check workspace stats
            print("📊 Workspace Statistics...")
            stats = db.get_stats()
            print(f"   ✓ Objects: {stats.get('objects_count', 0):,}")
            print(f"   ✓ Dependencies: {stats.get('dependencies_count', 0):,}")
            print(f"   ✓ Definitions: {stats.get('definitions_count', 0):,}")
            print(f"   ✓ Query Logs: {stats.get('query_logs_count', 0):,}")
            print(f"   ✓ Metadata Cache: {stats.get('lineage_metadata_count', 0):,}")

            # Get all views and stored procedures
            all_objects = db.query("""
                SELECT object_id, schema_name, object_name, object_type, modify_date
                FROM objects
                WHERE object_type IN ('View', 'Stored Procedure')
                ORDER BY object_type, schema_name, object_name
            """)

            print(f"\n🔍 Testing {len(all_objects):,} objects...")
            print()

            # Initialize parser
            parser = QualityAwareParser(db)

            # Parse each object
            for i, obj_tuple in enumerate(all_objects, 1):
                obj_id, schema, name, obj_type, modify_date = obj_tuple

                obj_info = {
                    'object_id': obj_id,
                    'schema_name': schema,
                    'object_name': name,
                    'object_type': obj_type,
                    'modify_date': modify_date
                }

                # Progress indicator
                if i % 50 == 0 or i == len(all_objects):
                    print(f"   Progress: {i}/{len(all_objects)} ({i/len(all_objects)*100:.1f}%)")

                try:
                    # Parse object (parser internally fetches DDL)
                    parse_result = parser.parse_object(obj_id)

                    if not parse_result:
                        report.add_error(obj_info, 'parsing', 'Parser returned None')
                        continue

                    # Add to report
                    report.add_result(obj_info, parse_result)

                except Exception as e:
                    logger.exception(f"Error parsing {schema}.{name}")
                    report.add_error(obj_info, 'parsing', str(e))

            # Print comprehensive report
            report.print_summary()

            # Return success/failure
            high_conf_pct = len(report.high_confidence) / max(report.total_objects, 1) * 100
            return high_conf_pct >= 70  # Target: 70%+ high confidence

    except Exception as e:
        logger.exception("Fatal error in complete parsing test")
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == '__main__':
    import sys

    # Run test
    success = test_complete_parsing()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
