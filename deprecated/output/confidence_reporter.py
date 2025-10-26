#!/usr/bin/env python3
"""
Confidence Reporter

Generates human-readable confidence reports for lineage analysis.
"""

import json
from typing import List, Dict
from datetime import datetime


class ConfidenceReporter:
    """Generates confidence reports for lineage analysis."""

    def __init__(self):
        pass

    def generate_report(
        self,
        target_object: str,
        lineage_graph: Dict[str, Dict],
        overall_confidence: float,
        uncertain_dependencies: List[Dict],
        validation_results: Dict,
        processing_time: float
    ) -> Dict:
        """
        Generate a comprehensive confidence report.

        Args:
            target_object: The target object analyzed
            lineage_graph: The complete lineage graph
            overall_confidence: Overall confidence score (0-1)
            uncertain_dependencies: List of uncertain dependencies
            validation_results: Results from dependency validation
            processing_time: Time taken for analysis (seconds)

        Returns:
            Report dictionary
        """
        report = {
            "target_object": target_object,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "processing_time_seconds": round(processing_time, 2),
            "overall_confidence_score": round(overall_confidence, 3),
            "confidence_rating": self._get_confidence_rating(overall_confidence),
            "statistics": {
                "total_objects": len(lineage_graph),
                "total_dependencies": sum(len(obj.get('dependencies', [])) for obj in lineage_graph.values()),
                "objects_by_type": self._count_by_type(lineage_graph),
                "objects_by_schema": self._count_by_schema(lineage_graph),
            },
            "validation": {
                "valid_dependencies": validation_results.get('valid_count', 0),
                "invalid_dependencies": validation_results.get('invalid_count', 0),
                "missing_objects": validation_results.get('missing_objects', []),
                "type_mismatches": validation_results.get('type_mismatches', []),
            },
            "uncertain_dependencies": [
                {
                    "object": f"{dep['schema']}.{dep['name']}",
                    "confidence": round(dep.get('confidence', 0), 3),
                    "reason": dep.get('reason', 'Unknown')
                }
                for dep in uncertain_dependencies
            ],
            "recommendations": self._generate_recommendations(
                overall_confidence,
                uncertain_dependencies,
                validation_results
            )
        }

        return report

    def _get_confidence_rating(self, score: float) -> str:
        """Convert confidence score to rating."""
        if score >= 0.9:
            return "EXCELLENT"
        elif score >= 0.75:
            return "GOOD"
        elif score >= 0.6:
            return "FAIR"
        elif score >= 0.4:
            return "POOR"
        else:
            return "VERY_POOR"

    def _count_by_type(self, lineage_graph: Dict[str, Dict]) -> Dict[str, int]:
        """Count objects by type."""
        counts = {}

        for obj_info in lineage_graph.values():
            obj_type = obj_info.get('object_type', 'Unknown')
            counts[obj_type] = counts.get(obj_type, 0) + 1

        return counts

    def _count_by_schema(self, lineage_graph: Dict[str, Dict]) -> Dict[str, int]:
        """Count objects by schema."""
        counts = {}

        for obj_key in lineage_graph.keys():
            parts = obj_key.split('.', 1)
            schema = parts[0] if len(parts) == 2 else "dbo"
            counts[schema] = counts.get(schema, 0) + 1

        return counts

    def _generate_recommendations(
        self,
        overall_confidence: float,
        uncertain_dependencies: List[Dict],
        validation_results: Dict
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if overall_confidence < 0.7:
            recommendations.append(
                "Overall confidence is below 70%. Consider manual review of the lineage."
            )

        if len(uncertain_dependencies) > 0:
            recommendations.append(
                f"Found {len(uncertain_dependencies)} uncertain dependencies. "
                f"Review these dependencies manually for accuracy."
            )

        if validation_results.get('invalid_count', 0) > 0:
            recommendations.append(
                f"Found {validation_results['invalid_count']} invalid dependencies. "
                f"These objects may not exist in the codebase or may need manual verification."
            )

        if validation_results.get('type_mismatches'):
            recommendations.append(
                f"Found {len(validation_results['type_mismatches'])} object type mismatches. "
                f"These have been corrected in the output."
            )

        if len(recommendations) == 0:
            recommendations.append(
                "Lineage analysis completed successfully with high confidence. "
                "No major issues detected."
            )

        return recommendations

    def write_report(self, report: Dict, output_file: str):
        """
        Write report to JSON file.

        Args:
            report: Report dictionary
            output_file: Path to output file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def generate_summary_text(self, report: Dict) -> str:
        """
        Generate a human-readable text summary of the report.

        Args:
            report: Report dictionary

        Returns:
            Text summary
        """
        lines = []

        lines.append("=" * 70)
        lines.append(f"LINEAGE ANALYSIS REPORT: {report['target_object']}")
        lines.append("=" * 70)
        lines.append("")

        lines.append(f"Analysis Time: {report['analysis_timestamp']}")
        lines.append(f"Processing Time: {report['processing_time_seconds']}s")
        lines.append("")

        lines.append(f"Overall Confidence: {report['overall_confidence_score']} "
                    f"({report['confidence_rating']})")
        lines.append("")

        lines.append("STATISTICS:")
        stats = report['statistics']
        lines.append(f"  Total Objects: {stats['total_objects']}")
        lines.append(f"  Total Dependencies: {stats['total_dependencies']}")
        lines.append("")

        lines.append("  Objects by Type:")
        for obj_type, count in stats['objects_by_type'].items():
            lines.append(f"    - {obj_type}: {count}")
        lines.append("")

        lines.append("  Objects by Schema:")
        for schema, count in stats['objects_by_schema'].items():
            lines.append(f"    - {schema}: {count}")
        lines.append("")

        validation = report['validation']
        lines.append("VALIDATION:")
        lines.append(f"  Valid Dependencies: {validation['valid_dependencies']}")
        lines.append(f"  Invalid Dependencies: {validation['invalid_dependencies']}")

        if validation['missing_objects']:
            lines.append(f"  Missing Objects: {len(validation['missing_objects'])}")
            lines.append(f"    (These are external objects not found in the repository)")

            # Group missing objects by schema
            missing_by_schema = {}
            for obj in validation['missing_objects']:
                parts = obj.split('.', 1)
                schema = parts[0] if len(parts) == 2 else 'dbo'
                if schema not in missing_by_schema:
                    missing_by_schema[schema] = []
                missing_by_schema[schema].append(obj)

            # Show summary by schema
            for schema, objs in sorted(missing_by_schema.items()):
                lines.append(f"    - {schema}: {len(objs)} objects")

        if validation['type_mismatches']:
            lines.append(f"  Type Mismatches: {len(validation['type_mismatches'])}")

        lines.append("")

        if report['uncertain_dependencies']:
            lines.append(f"UNCERTAIN DEPENDENCIES ({len(report['uncertain_dependencies'])}):")
            for dep in report['uncertain_dependencies'][:10]:  # Show first 10
                lines.append(f"  - {dep['object']} (confidence: {dep['confidence']})")

            if len(report['uncertain_dependencies']) > 10:
                lines.append(f"  ... and {len(report['uncertain_dependencies']) - 10} more")
            lines.append("")

        lines.append("RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            lines.append(f"  {i}. {rec}")

        lines.append("")
        lines.append("=" * 70)

        return '\n'.join(lines)
