#!/usr/bin/env python3
"""
Autonomous Data Lineage Engine

Fully autonomous system for reverse engineering SQL data lineage without manual approvals.
Combines regex parsing, AI-assisted analysis, and iterative search for high accuracy.

Usage:
    python autonomous_lineage.py <target_object_name> [--synapse-dir <path>]

Example:
    python autonomous_lineage.py CadenceBudgetData
    python autonomous_lineage.py BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
"""

import sys
import argparse
import time
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict, deque

# Add parent directory to path so imports work from scripts/ folder
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all components
from parsers.sql_parser_enhanced import EnhancedSQLParser, ParsedSQLObject
from parsers.dependency_extractor import DependencyExtractor
from ai_analyzer.sql_complexity_detector import SQLComplexityDetector
from ai_analyzer.ai_sql_parser import AISQLParser
from ai_analyzer.confidence_scorer import ConfidenceScorer
from validators.dependency_validator import DependencyValidator
from validators.iterative_refiner import IterativeRefiner
from output.json_formatter import JSONFormatter
from output.confidence_reporter import ConfidenceReporter


class AutonomousLineageEngine:
    """Main orchestrator for autonomous lineage analysis."""

    def __init__(self, synapse_dir: str):
        self.synapse_dir = Path(synapse_dir)
        self.tables_dir = self.synapse_dir / "Tables"
        self.views_dir = self.synapse_dir / "Views"
        self.procedures_dir = self.synapse_dir / "Stored Procedures"

        # Initialize components
        self.sql_parser = EnhancedSQLParser()
        self.dep_extractor = DependencyExtractor()
        self.complexity_detector = SQLComplexityDetector()
        self.ai_parser = AISQLParser()
        self.confidence_scorer = ConfidenceScorer()
        self.validator = DependencyValidator(synapse_dir)
        self.refiner = IterativeRefiner(synapse_dir)
        self.json_formatter = JSONFormatter()
        self.reporter = ConfidenceReporter()

        # Lineage graph: schema.object_name -> {object_type, dependencies, confidence, ...}
        self.lineage_graph: Dict[str, Dict] = {}

        # Processing queues
        self.to_process: deque = deque()
        self.processed: Set[str] = set()

    def find_object_file(self, schema: str, object_name: str) -> tuple[Path | None, str | None]:
        """
        Find the SQL file for an object.

        Args:
            schema: Schema name (e.g., 'CONSUMPTION_FINANCE')
            object_name: Object name (e.g., 'FactGLCognos')

        Returns:
            Tuple of (file_path, object_type) or (None, None) if not found
        """
        # Define search locations with their corresponding object types
        search_locations = [
            (self.tables_dir, "Table"),
            (self.views_dir, "View"),
            (self.procedures_dir, "StoredProcedure")
        ]

        # Search for the object file in each location
        for directory, obj_type in search_locations:
            file_path = directory / f"{schema}.{object_name}.sql"
            if file_path.exists():
                return file_path, obj_type

        return None, None

    def parse_object(self, file_path: Path, object_type: str) -> ParsedSQLObject:
        """Parse a SQL object file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Use enhanced parser
        parsed = self.sql_parser.parse_sql_object(content, str(file_path), object_type)

        # If complex patterns detected, use AI analyzer
        if parsed.needs_ai_review and parsed.complex_patterns:
            # Extract complex snippets
            snippets = self.complexity_detector.extract_complex_snippets(content)

            # Analyze each snippet with AI
            ai_deps = []
            for snippet_type, snippet in snippets:
                ai_found = self.ai_parser.analyze_complex_snippet(snippet_type, snippet)
                ai_deps.extend(ai_found)

            # Merge AI deps with regex deps
            parsed.dependencies = self.confidence_scorer.merge_dependencies(
                parsed.dependencies,
                ai_deps
            )

        return parsed

    def analyze_object(self, schema: str, object_name: str) -> bool:
        """
        Analyze a single object and add it to the lineage graph.

        Returns:
            True if successful, False if object not found
        """
        obj_key = f"{schema}.{object_name}"

        # Skip if already processed
        if obj_key in self.processed:
            return True

        print(f"  Analyzing: {obj_key}")

        # Find file
        file_path, object_type = self.find_object_file(schema, object_name)

        if not file_path:
            # Object not found in files, might be dynamically created
            # Add as unknown but mark for search
            self.lineage_graph[obj_key] = {
                'schema': schema,
                'object_name': object_name,
                'object_type': 'Table',  # Assume table
                'dependencies': [],
                'outputs': [],
                'confidence': 0.5,
                'needs_verification': True
            }
            self.processed.add(obj_key)
            return False

        # Parse object
        parsed = self.parse_object(file_path, object_type)

        # Add to graph
        dep_keys = []
        for dep in parsed.dependencies:
            dep_key = f"{dep.schema}.{dep.object_name}"
            dep_keys.append(dep_key)

            # Queue dependency for processing
            if dep_key not in self.processed:
                self.to_process.append((dep.schema, dep.object_name))

        # Extract outputs (for stored procedures only)
        output_keys = []
        if object_type == "StoredProcedure":
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            output_keys = self._extract_write_targets(content)

        self.lineage_graph[obj_key] = {
            'schema': schema,
            'object_name': object_name,
            'object_type': parsed.object_type,
            'dependencies': dep_keys,
            'outputs': output_keys,
            'confidence': parsed.confidence_score,
            'needs_ai_review': parsed.needs_ai_review
        }

        self.processed.add(obj_key)
        return True

    def is_logging_object(self, schema: str, object_name: str) -> bool:
        """Check if an object is a logging/utility object that should be excluded."""
        logging_objects = {
            ('ADMIN', 'Logs'),
            ('dbo', 'LogMessage'),
            ('dbo', 'spLastRowCount'),
            ('DBO', 'LogMessage'),
            ('DBO', 'spLastRowCount'),
        }
        return (schema, object_name) in logging_objects

    def fix_table_dependencies(self):
        """
        Fix table inputs: Tables should list SPs that write to them.

        Current state after parsing:
        - SP: dependencies = tables it reads from ✓
        - Table: dependencies = [] (empty) ✗

        Correct state:
        - SP: dependencies (inputs) = tables/views it reads from ✓
        - Table: dependencies (inputs) = SPs that write to it ✓

        This creates the "inputs" direction of the bidirectional graph.
        """
        print("\n🔧 Fixing table inputs (dependencies)...")

        # Build a reverse map: table -> list of SPs that write to it
        table_writers = defaultdict(list)

        for obj_key, obj_info in self.lineage_graph.items():
            if obj_info['object_type'] == 'StoredProcedure':
                # Parse the SP to find tables it writes to
                parts = obj_key.split('.', 1)
                if len(parts) == 2:
                    schema, obj_name = parts
                else:
                    schema = "dbo"
                    obj_name = obj_key

                # Find the file and extract write targets
                file_path, _ = self.find_object_file(schema, obj_name)
                if file_path:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Extract INSERT INTO, UPDATE, SELECT INTO targets
                    write_targets = self._extract_write_targets(content)

                    for target_key in write_targets:
                        # Skip logging tables
                        target_parts = target_key.split('.', 1)
                        if len(target_parts) == 2:
                            target_schema, target_name = target_parts
                        else:
                            target_schema = "dbo"
                            target_name = target_key

                        if self.is_logging_object(target_schema, target_name):
                            continue

                        table_writers[target_key].append(obj_key)

        # Now update table dependencies (inputs)
        tables_updated = 0
        for obj_key, obj_info in self.lineage_graph.items():
            if obj_info['object_type'] == 'Table':
                # Replace dependencies with SPs that write to this table
                if obj_key in table_writers:
                    obj_info['dependencies'] = table_writers[obj_key]
                    tables_updated += 1
                else:
                    # No writers found - this is a source table
                    obj_info['dependencies'] = []

        # Filter out logging objects from SP/View dependencies
        for obj_key, obj_info in self.lineage_graph.items():
            if obj_info['object_type'] in ['StoredProcedure', 'View']:
                # Filter out logging objects
                filtered_deps = []
                for dep_key in obj_info.get('dependencies', []):
                    parts = dep_key.split('.', 1)
                    if len(parts) == 2:
                        dep_schema, dep_name = parts
                    else:
                        dep_schema = "dbo"
                        dep_name = dep_key

                    if not self.is_logging_object(dep_schema, dep_name):
                        filtered_deps.append(dep_key)

                obj_info['dependencies'] = filtered_deps

        # Remove logging objects from the graph entirely
        logging_keys_to_remove = []
        for obj_key in list(self.lineage_graph.keys()):
            parts = obj_key.split('.', 1)
            if len(parts) == 2:
                schema, obj_name = parts
            else:
                schema = "dbo"
                obj_name = obj_key

            if self.is_logging_object(schema, obj_name):
                logging_keys_to_remove.append(obj_key)

        for key in logging_keys_to_remove:
            del self.lineage_graph[key]

        print(f"  ✓ Updated {tables_updated} tables with their writer SPs (inputs)")
        print(f"  ✓ Removed {len(logging_keys_to_remove)} logging objects")

    def fix_table_outputs(self):
        """
        Fix table/view outputs: Tables and views should list SPs/Views that READ from them.

        This creates the "outputs" direction of the bidirectional graph, completing the
        edge relationships for proper graph visualization.

        After this method:
        - Table/View: outputs = SPs/Views that read from it ✓
        - SP: outputs = tables it writes to (already set in analyze_object) ✓

        Handles circular dependencies: A SP can appear in both inputs and outputs of a table
        when it both reads from and writes to the same table.
        """
        print("\n🔧 Fixing table/view outputs...")

        # Build a map: table/view -> list of SPs/Views that read from it
        table_readers = defaultdict(list)

        for obj_key, obj_info in self.lineage_graph.items():
            if obj_info['object_type'] in ['StoredProcedure', 'View']:
                # Get objects this SP/View reads from (its dependencies/inputs)
                for dep_key in obj_info.get('dependencies', []):
                    # Check if dependency exists in graph
                    if dep_key in self.lineage_graph:
                        dep_obj = self.lineage_graph[dep_key]
                        # Only add to readers if it's a Table or View
                        if dep_obj['object_type'] in ['Table', 'View']:
                            table_readers[dep_key].append(obj_key)

        # Update table/view outputs
        objects_updated = 0
        for obj_key, obj_info in self.lineage_graph.items():
            if obj_info['object_type'] in ['Table', 'View']:
                if obj_key in table_readers:
                    # Remove duplicates while preserving order
                    obj_info['outputs'] = list(dict.fromkeys(table_readers[obj_key]))
                    objects_updated += 1
                else:
                    # No readers found - this is a terminal/unused object
                    obj_info['outputs'] = []

        # Validate circular dependencies and log them
        circular_deps = []
        for obj_key, obj_info in self.lineage_graph.items():
            if obj_info['object_type'] == 'Table':
                inputs = set(obj_info.get('dependencies', []))
                outputs = set(obj_info.get('outputs', []))
                # Check if any SP both reads from and writes to this table
                circular_sps = inputs.intersection(outputs)
                if circular_sps:
                    circular_deps.append((obj_key, circular_sps))

        print(f"  ✓ Updated {objects_updated} tables/views with their reader SPs/Views (outputs)")
        if circular_deps:
            print(f"  ℹ Found {len(circular_deps)} tables with circular dependencies:")
            for table_key, sps in circular_deps[:5]:  # Show first 5
                print(f"    - {table_key}: {', '.join(list(sps)[:3])}")
            if len(circular_deps) > 5:
                print(f"    ... and {len(circular_deps) - 5} more")

    def _extract_write_targets(self, content: str) -> List[str]:
        """Extract tables that are written to (INSERT, UPDATE, SELECT INTO, MERGE, TRUNCATE)."""
        targets = set()

        # Pattern for INSERT INTO
        for match in re.finditer(r'INSERT\s+INTO\s+(\[?[\w]+\]?\.\[?[\w]+\]?)', content, re.IGNORECASE):
            table_name = self._normalize_table_name(match.group(1))
            if not table_name.startswith('#'):
                targets.add(table_name)

        # Pattern for UPDATE
        for match in re.finditer(r'UPDATE\s+(\[?[\w]+\]?\.\[?[\w]+\]?)', content, re.IGNORECASE):
            table_name = self._normalize_table_name(match.group(1))
            if not table_name.startswith('#') and '.' in table_name:
                targets.add(table_name)

        # Pattern for SELECT INTO
        for match in re.finditer(r'INTO\s+(\[?[\w]+\]?\.\[?[\w]+\]?)', content, re.IGNORECASE):
            table_name = self._normalize_table_name(match.group(1))
            if not table_name.startswith('#'):
                targets.add(table_name)

        # Pattern for MERGE INTO
        for match in re.finditer(r'MERGE\s+INTO\s+(\[?[\w]+\]?\.\[?[\w]+\]?)', content, re.IGNORECASE):
            table_name = self._normalize_table_name(match.group(1))
            if not table_name.startswith('#'):
                targets.add(table_name)

        # Pattern for TRUNCATE TABLE
        for match in re.finditer(r'TRUNCATE\s+TABLE\s+(\[?[\w]+\]?\.\[?[\w]+\]?)', content, re.IGNORECASE):
            table_name = self._normalize_table_name(match.group(1))
            if not table_name.startswith('#'):
                targets.add(table_name)

        return list(targets)

    def _normalize_table_name(self, name: str) -> str:
        """Normalize table name."""
        name = re.sub(r'[\[\]"`]', '', name)
        name = name.strip()
        name = re.sub(r'\s+with\s*\(.*?\)', '', name, flags=re.IGNORECASE)

        parts = [p.strip() for p in name.split('.')]
        if len(parts) >= 2:
            return f"{parts[-2]}.{parts[-1]}"
        return name

    def build_lineage(self, target_schema: str, target_object: str):
        """
        Build complete lineage graph recursively from target object.

        Args:
            target_schema: Schema of target object
            target_object: Name of target object
        """
        print(f"\n🔍 Building lineage for: {target_schema}.{target_object}")
        print("=" * 70)

        # Start with target object
        self.to_process.append((target_schema, target_object))

        # Process queue until empty
        while self.to_process:
            schema, obj_name = self.to_process.popleft()
            self.analyze_object(schema, obj_name)

        print(f"\n✓ Initial analysis complete: {len(self.lineage_graph)} objects found")

        # NOTE: Dependency fixing moved to generate_output() after external objects are added

    def validate_lineage(self):
        """Validate all dependencies in the lineage graph."""
        print("\n🔍 Validating dependencies...")

        # Collect all dependencies
        all_deps = []
        for obj_key, obj_info in self.lineage_graph.items():
            for dep_key in obj_info.get('dependencies', []):
                parts = dep_key.split('.', 1)
                if len(parts) == 2:
                    schema, obj_name = parts
                else:
                    schema = "dbo"
                    obj_name = dep_key

                # Create mock dependency for validation
                from parsers.sql_parser_enhanced import Dependency, ConfidenceLevel
                dep = Dependency(
                    object_name=obj_name,
                    schema=schema,
                    object_type=self.lineage_graph.get(dep_key, {}).get('object_type', 'Table'),
                    confidence=ConfidenceLevel.HIGH.value,
                    needs_ai_review=False,
                    detection_method="validation"
                )
                all_deps.append(dep)

        # Validate
        validation_result = self.validator.validate_dependencies(all_deps)

        print(f"  ✓ Valid: {len(validation_result.valid_dependencies)}")
        print(f"  ✗ Invalid: {len(validation_result.invalid_dependencies)}")

        if validation_result.object_type_mismatches:
            print(f"  ⚠ Type mismatches: {len(validation_result.object_type_mismatches)}")

        return {
            'valid_count': len(validation_result.valid_dependencies),
            'invalid_count': len(validation_result.invalid_dependencies),
            'missing_objects': validation_result.missing_objects,
            'type_mismatches': validation_result.object_type_mismatches
        }

    def refine_lineage(self):
        """Use iterative search to find missing dependencies."""
        print("\n🔍 Refining lineage with search...")

        refinement_count = 0

        # For each object, check if we missed any dependencies
        for obj_key in list(self.lineage_graph.keys()):
            known_deps = set(self.lineage_graph[obj_key].get('dependencies', []))

            # Discover missing dependencies
            new_deps = self.refiner.discover_missing_dependencies(obj_key, known_deps)

            for new_dep in new_deps:
                new_key = f"{new_dep.schema}.{new_dep.object_name}"

                # Add to lineage if not already there
                if new_key not in self.lineage_graph:
                    self.analyze_object(new_dep.schema, new_dep.object_name)
                    refinement_count += 1

        # CRITICAL: Process any new objects added to queue during refinement
        # This ensures their dependencies are also analyzed recursively
        while self.to_process:
            schema, obj_name = self.to_process.popleft()
            if f"{schema}.{obj_name}" not in self.processed:
                self.analyze_object(schema, obj_name)
                refinement_count += 1

        if refinement_count > 0:
            print(f"  ✓ Found {refinement_count} additional dependencies")
        else:
            print(f"  ✓ No additional dependencies found")

    def generate_output(self, target_object: str, processing_time: float):
        """Generate JSON output and confidence report."""
        print("\n📊 Generating output...")

        # Calculate overall confidence
        all_confidences = [obj.get('confidence', 0.5) for obj in self.lineage_graph.values()]
        overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5

        # Identify uncertain dependencies
        uncertain = []
        for obj_key, obj_info in self.lineage_graph.items():
            if obj_info.get('confidence', 1.0) < 0.7 or obj_info.get('needs_ai_review', False):
                parts = obj_key.split('.', 1)
                uncertain.append({
                    'schema': parts[0] if len(parts) == 2 else "dbo",
                    'name': parts[1] if len(parts) == 2 else obj_key,
                    'confidence': obj_info.get('confidence', 0.5),
                    'reason': 'Complex SQL patterns detected' if obj_info.get('needs_ai_review') else 'Low confidence'
                })

        # Validate lineage
        validation_results = self.validate_lineage()

        # Add missing objects to lineage graph as stubs
        missing_objects = validation_results.get('missing_objects', [])
        external_added = 0
        for missing_obj in missing_objects:
            if missing_obj not in self.lineage_graph:
                parts = missing_obj.split('.', 1)
                if len(parts) == 2:
                    schema, obj_name = parts
                else:
                    schema = "dbo"
                    obj_name = missing_obj

                # Add as stub node
                self.lineage_graph[missing_obj] = {
                    'schema': schema,
                    'object_name': obj_name,
                    'object_type': 'Table',  # Assume table for missing objects
                    'dependencies': [],
                    'outputs': [],
                    'confidence': 0.0,
                    'exists_in_repo': False,
                    'is_external': True
                }
                external_added += 1

        # CRITICAL: Now that ALL objects are in the graph (including external),
        # fix the bidirectional edges. This must happen AFTER all objects are added.
        print(f"\n🔧 Building bidirectional graph structure...")
        print(f"  Total objects in graph: {len(self.lineage_graph)}")

        # Step 1: Fix table inputs (SPs that write to them)
        self.fix_table_dependencies()

        # Step 2: Fix table/view outputs (SPs that read from them)
        self.fix_table_outputs()

        # Format as JSON (all objects present, all edges bidirectional)
        json_nodes = self.json_formatter.format_lineage(self.lineage_graph, target_object)

        # Validate format
        if not self.json_formatter.validate_json_format(json_nodes):
            print("  ✗ JSON format validation failed!")
            return

        # Create output directory if it doesn't exist
        output_dir = Path("lineage_output")
        output_dir.mkdir(exist_ok=True)

        # Write JSON output
        output_file = output_dir / f"{target_object}_lineage.json"
        self.json_formatter.write_json(json_nodes, str(output_file))
        print(f"  ✓ JSON lineage: {output_file}")

        # Generate confidence report
        report = self.reporter.generate_report(
            target_object,
            self.lineage_graph,
            overall_confidence,
            uncertain,
            validation_results,
            processing_time
        )

        # Write confidence report
        confidence_file = output_dir / f"{target_object}_confidence.json"
        self.reporter.write_report(report, str(confidence_file))
        print(f"  ✓ Confidence report: {confidence_file}")

        # Print summary
        print("\n" + self.reporter.generate_summary_text(report))

    def run(self, target_object: str):
        """
        Run complete autonomous lineage analysis.

        Args:
            target_object: Target object name (can include schema: schema.object)
        """
        start_time = time.time()

        # Parse target object
        if '.' in target_object:
            target_schema, target_name = target_object.split('.', 1)
        else:
            # Try to find the object
            target_schema = None
            target_name = target_object

            # Search for the object
            for schema in ['CONSUMPTION_ClinOpsFinance', 'CONSUMPTION_FINANCE', 'CONSUMPTION_POWERBI',
                          'CONSUMPTION_PRIMA', 'STAGING_CADENCE', 'dbo']:
                file_path, obj_type = self.find_object_file(schema, target_name)
                if file_path:
                    target_schema = schema
                    break

            if not target_schema:
                print(f"✗ Error: Could not find object '{target_object}' in any schema")
                return False

        # Step 1: Build lineage graph
        self.build_lineage(target_schema, target_name)

        # Step 2: Refine with search
        self.refine_lineage()

        # Step 3: Validate
        print(f"\n✓ Total objects in lineage: {len(self.lineage_graph)}")

        # Step 4: Generate output
        processing_time = time.time() - start_time
        self.generate_output(f"{target_schema}.{target_name}", processing_time)

        print(f"\n✅ Analysis complete in {processing_time:.2f}s")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Data Lineage Engine for Azure Synapse"
    )
    parser.add_argument(
        "target_object",
        help="Target object name (e.g., CadenceBudgetData or CONSUMPTION_ClinOpsFinance.CadenceBudgetData)"
    )
    parser.add_argument(
        "--synapse-dir",
        default="Synapse_Data_Warehouse",
        help="Path to Synapse Data Warehouse directory (default: Synapse_Data_Warehouse)"
    )

    args = parser.parse_args()

    # Initialize engine
    engine = AutonomousLineageEngine(args.synapse_dir)

    # Run analysis
    success = engine.run(args.target_object)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
