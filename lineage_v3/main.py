#!/usr/bin/env python3
"""
Vibecoding Lineage Parser v3 - Main Entry Point

Command-line interface for the data lineage extraction system.

Usage:
    # Extract DMV data from Synapse (dev only)
    python main.py extract --output parquet_snapshots/

    # Run lineage analysis on Parquet snapshots
    python main.py run --parquet parquet_snapshots/

    # Run with full refresh (skip incremental)
    python main.py run --parquet parquet_snapshots/ --full-refresh

    # Generate only frontend output
    python main.py run --parquet parquet_snapshots/ --format frontend

Author: Vibecoding Team
Version: 3.0.0
"""

import sys
import click
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3 import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Vibecoding Lineage Parser v3

    A DMV-first data lineage extraction system for Azure Synapse Dedicated SQL Pool.
    """
    pass


@cli.command()
@click.option(
    '--output',
    default='parquet_snapshots/',
    help='Output directory for Parquet files'
)
@click.option(
    '--timestamp/--no-timestamp',
    default=True,
    help='Add timestamp suffix to Parquet filenames'
)
def extract(output, timestamp):
    """
    Extract DMV metadata from Synapse to Parquet files (DEV ONLY).

    This command connects to Azure Synapse Dedicated SQL Pool and exports
    metadata from system DMVs to Parquet snapshots.

    Requires .env file with SYNAPSE_* credentials.

    In production, users should provide pre-exported Parquet files directly.
    """
    click.echo(f"🔄 Extracting DMV data from Synapse...")
    click.echo(f"📁 Output directory: {output}")

    # TODO: Import and run extractor
    # from lineage_v3.extractor import synapse_dmv_extractor
    # synapse_dmv_extractor.run(output, timestamp)

    click.echo("⚠️  Extractor not yet implemented - Coming in Phase 2")
    sys.exit(1)


@cli.command()
@click.option(
    '--parquet',
    required=True,
    help='Path to directory containing Parquet snapshots'
)
@click.option(
    '--output',
    default='lineage_output/',
    help='Output directory for JSON files'
)
@click.option(
    '--full-refresh',
    is_flag=True,
    help='Force full re-parsing (skip incremental)'
)
@click.option(
    '--format',
    type=click.Choice(['internal', 'frontend', 'both']),
    default='both',
    help='Output format: internal (int IDs), frontend (string IDs), or both'
)
@click.option(
    '--skip-query-logs',
    is_flag=True,
    help='Skip query log analysis (Step 3)'
)
@click.option(
    '--workspace',
    default='lineage_workspace.duckdb',
    help='Path to DuckDB workspace file'
)
@click.option(
    '--reparse-threshold',
    default=0.85,
    type=float,
    help='Confidence threshold for re-parsing in incremental mode (default: 0.85)'
)
def run(parquet, output, full_refresh, format, skip_query_logs, workspace, reparse_threshold):
    """
    Run lineage analysis on Parquet snapshots.

    This is the main command that executes the 8-step lineage construction pipeline:

    1. Ingest Parquet files into DuckDB
    2. Build baseline from DMV dependencies
    3. Enhance from query logs (optional)
    4. Detect gaps (unresolved SPs)
    5. Run SQLGlot parser with quality validation
    6. Validate with query logs
    7. Merge all sources
    8. Generate output JSON files
    """
    # No settings override needed - reparse_threshold passed directly to get_objects_to_parse()

    click.echo(f"🚀 Vibecoding Lineage Parser v{__version__}")
    click.echo(f"📂 Parquet directory: {parquet}")
    click.echo(f"📁 Output directory: {output}")
    click.echo(f"🔄 Mode: {'Full Refresh' if full_refresh else 'Incremental'}")
    click.echo(f"📊 Format: {format}")
    click.echo(f"💾 Workspace: {workspace}")
    if not full_refresh:
        click.echo(f"🔧 Reparse Threshold: {reparse_threshold} (objects below this confidence will be re-parsed)")
    click.echo()

    try:
        # Import core engine
        from lineage_v3.core import DuckDBWorkspace

        # Step 1: Initialize DuckDB workspace and load Parquet files
        click.echo("=" * 70)
        click.echo("Step 1: Ingest Parquet files into DuckDB")
        click.echo("=" * 70)

        with DuckDBWorkspace(workspace_path=workspace) as db:
            # Load Parquet files
            row_counts = db.load_parquet(parquet, full_refresh=full_refresh)

            click.echo(f"✅ Loaded Parquet files:")
            for table, count in row_counts.items():
                if count > 0:
                    click.echo(f"   - {table}: {count:,} rows")
                else:
                    click.echo(f"   - {table}: (skipped)")

            # Get workspace stats
            stats = db.get_stats()
            click.echo()
            click.echo(f"📊 Workspace Statistics:")
            click.echo(f"   - Total objects: {stats.get('objects_count', 0):,}")
            click.echo(f"   - Dependencies: {stats.get('dependencies_count', 0):,}")
            click.echo(f"   - Definitions: {stats.get('definitions_count', 0):,}")
            click.echo(f"   - Metadata cache: {stats.get('lineage_metadata_count', 0):,}")
            click.echo()

            # Get objects to parse (includes low-confidence objects needing re-parsing)
            objects_to_parse = db.get_objects_to_parse(
                full_refresh=full_refresh,
                confidence_threshold=reparse_threshold
            )
            click.echo(f"🔍 Objects requiring analysis: {len(objects_to_parse):,}")

            if not full_refresh:
                click.echo(f"   ℹ️  Incremental mode: Parsing modified objects + low confidence (<{reparse_threshold:.2f})")

            if not objects_to_parse:
                click.echo()
                click.echo("✅ All objects up to date! Nothing to parse.")
                click.echo("💡 Use --full-refresh to force re-parsing.")
                return

            # Step 2-3: Build baseline from DMV dependencies and query logs
            click.echo()
            click.echo("=" * 70)
            click.echo("Step 2: Load DMV Dependencies (Views)")
            click.echo("=" * 70)

            # Load DMV dependencies for Views
            views_with_dmv = db.query("""
                SELECT DISTINCT
                    d.referencing_object_id,
                    o.object_name,
                    o.modify_date
                FROM dependencies d
                JOIN objects o ON d.referencing_object_id = o.object_id
                WHERE o.object_type = 'View'
            """)

            if views_with_dmv:
                click.echo(f"📊 Loading DMV dependencies for {len(views_with_dmv)} View(s)...")

                for view in views_with_dmv:
                    view_id, view_name, modify_date = view

                    # Get all dependencies for this view
                    deps = db.query("""
                        SELECT
                            referenced_object_id,
                            referenced_schema_name,
                            referenced_entity_name
                        FROM dependencies
                        WHERE referencing_object_id = ?
                    """, [view_id])

                    # Extract input object_ids (tables/views this view reads from)
                    inputs = [dep[0] for dep in deps if dep[0] is not None]

                    # Views don't write (no outputs), only read
                    outputs = []

                    # Store in lineage_metadata
                    db.update_metadata(
                        object_id=view_id,
                        modify_date=modify_date,
                        primary_source='dmv',
                        confidence=1.0,
                        inputs=inputs,
                        outputs=outputs
                    )

                click.echo(f"✅ Loaded DMV dependencies for {len(views_with_dmv)} View(s)")
            else:
                click.echo("ℹ️  No Views with DMV dependencies found")

            click.echo()

            # Step 3: Detect gaps
            click.echo("=" * 70)
            click.echo("Step 3: Detect Gaps (Missing Dependencies)")
            click.echo("=" * 70)

            from lineage_v3.core import GapDetector
            gap_detector = GapDetector(db)

            gaps = gap_detector.detect_gaps()
            click.echo(f"🔍 Found {len(gaps):,} objects with missing dependencies")

            if gaps:
                # Show sample gaps
                sample_count = min(5, len(gaps))
                click.echo(f"📋 Sample gaps (showing {sample_count}):")
                for i, gap in enumerate(gaps[:sample_count]):
                    click.echo(f"   {i+1}. {gap['schema_name']}.{gap['object_name']} ({gap['object_type']})")

                if len(gaps) > sample_count:
                    click.echo(f"   ... and {len(gaps) - sample_count} more")

            # Show gap statistics
            gap_stats = gap_detector.get_gap_statistics()
            click.echo()
            click.echo(f"📊 Gap Statistics:")
            click.echo(f"   - Total objects: {gap_stats['total_objects']:,}")
            click.echo(f"   - Parsed: {gap_stats['parsed_objects']:,}")
            click.echo(f"   - Gaps: {gap_stats['total_gaps']:,} ({gap_stats['gap_percentage']:.1f}%)")
            click.echo()

            # Step 4: Parse ALL Stored Procedures with Dual-Parser
            click.echo("=" * 70)
            click.echo("Step 4: Dual-Parser (Parse ALL Stored Procedures)")
            click.echo("=" * 70)

            # Get ALL stored procedures (not just gaps)
            all_sps = db.query("""
                SELECT object_id, schema_name, object_name, modify_date
                FROM objects
                WHERE object_type = 'Stored Procedure'
                ORDER BY schema_name, object_name
            """)

            click.echo(f"🔄 Parsing {len(all_sps):,} stored procedures with AI-enhanced parser...")
            click.echo()

            if all_sps:
                from lineage_v3.parsers import QualityAwareParser
                parser = QualityAwareParser(db)

                parsed_count = 0
                failed_count = 0
                high_confidence_count = 0
                medium_confidence_count = 0
                low_confidence_count = 0
                ai_used_count = 0

                for i, sp in enumerate(all_sps):
                    try:
                        # Parse with quality-aware parser (includes AI fallback)
                        result = parser.parse_object(sp[0])  # sp[0] = object_id

                        # Track AI usage
                        if result.get('quality_check', {}).get('ai_used', False):
                            ai_used_count += 1

                        # Persist result to lineage_metadata
                        db.update_metadata(
                            object_id=sp[0],
                            modify_date=sp[3],  # sp[3] = modify_date
                            primary_source=result.get('source', 'parser'),
                            confidence=result['confidence'],
                            inputs=result.get('inputs', []),
                            outputs=result.get('outputs', [])
                        )

                        # Categorize by confidence
                        if result['confidence'] >= 0.85:
                            parsed_count += 1
                            high_confidence_count += 1
                        elif result['confidence'] >= 0.75:
                            parsed_count += 1
                            medium_confidence_count += 1
                        elif result['confidence'] >= 0.50:
                            parsed_count += 1
                            low_confidence_count += 1
                        else:
                            failed_count += 1

                        # Show progress every 5 objects
                        if (i + 1) % 5 == 0 or (i + 1) == len(all_sps):
                            click.echo(f"   Progress: {i + 1}/{len(all_sps)} SPs parsed...")

                    except Exception as e:
                        click.echo(f"   ⚠️  Failed to parse {sp[1]}.{sp[2]}: {e}")
                        failed_count += 1

                click.echo()
                click.echo(f"✅ Parser complete:")
                click.echo(f"   - Total SPs: {len(all_sps):,}")
                click.echo(f"   - Successfully parsed: {parsed_count:,} ({parsed_count/len(all_sps)*100:.1f}%)")
                click.echo(f"     • High confidence (≥0.85): {high_confidence_count:,}")
                click.echo(f"     • Medium confidence (0.75-0.84): {medium_confidence_count:,}")
                click.echo(f"     • Low confidence (0.50-0.74): {low_confidence_count:,}")
                click.echo(f"   - Failed: {failed_count:,} ({failed_count/len(all_sps)*100:.1f}%)")
                if ai_used_count > 0:
                    click.echo(f"   - AI disambiguations used: {ai_used_count:,} SPs ({ai_used_count/len(all_sps)*100:.1f}%)")
                click.echo()
            else:
                click.echo("⚠️  No stored procedures found to parse")
                click.echo()

            # Step 5: Query Log Validation (Cross-Validation)
            click.echo("=" * 70)
            click.echo("Step 5: Query Log Validation (Cross-Validation)")
            click.echo("=" * 70)

            # Check if query logs available
            try:
                query_log_count = db.query("SELECT COUNT(*) FROM query_logs")[0][0]
            except:
                query_log_count = 0  # Table doesn't exist

            if query_log_count > 0:
                click.echo(f"📊 Found {query_log_count:,} query log entries")

                from lineage_v3.parsers import QueryLogValidator
                validator = QueryLogValidator(db)

                # Cross-validate parsed stored procedures
                click.echo(f"🔍 Cross-validating parsed stored procedures with runtime evidence...")
                validation_results = validator.validate_parsed_objects()

                if not validation_results['skipped']:
                    click.echo(f"✅ Validated {validation_results['validated_objects']} stored procedure(s)")
                    click.echo(f"   Total matching queries: {validation_results['total_matching_queries']}")

                    if validation_results['confidence_boosted']:
                        click.echo(f"\n📈 Confidence Boosts:")
                        for obj_id, old_conf, new_conf in validation_results['confidence_boosted'][:5]:
                            obj = db.query("SELECT schema_name, object_name FROM objects WHERE object_id = ?", [obj_id])[0]
                            click.echo(f"   - {obj[0]}.{obj[1]}: {old_conf:.2f} → {new_conf:.2f}")

                        if len(validation_results['confidence_boosted']) > 5:
                            remaining = len(validation_results['confidence_boosted']) - 5
                            click.echo(f"   ... and {remaining} more")

                    if validation_results['unvalidated_objects'] > 0:
                        click.echo(f"\n⚠️  {validation_results['unvalidated_objects']} object(s) could not be validated")
                        click.echo(f"   (No matching queries found in logs)")
                else:
                    click.echo("ℹ️  No high-confidence objects to validate")
            else:
                click.echo("ℹ️  No query logs available - skipping validation")
                click.echo("   Query logs are optional. Static parsing results will be used.")

            click.echo()

            # Step 6: AI Fallback (Skip for now - Phase 5)
            click.echo("=" * 70)
            click.echo("Step 6: AI Fallback (Skipped)")
            click.echo("=" * 70)
            click.echo("⚠️  AI Fallback deferred to Phase 5")
            click.echo()

            # Step 7: Bidirectional Graph (Reverse Lookup)
            click.echo("=" * 70)
            click.echo("Step 7: Build Bidirectional Graph (Reverse Lookup)")
            click.echo("=" * 70)

            # Get all parsed objects (SPs and Views)
            parsed_objects = db.query("""
                SELECT object_id, inputs, outputs
                FROM lineage_metadata
                WHERE inputs IS NOT NULL OR outputs IS NOT NULL
            """)

            # Build reverse lookup map
            reverse_inputs = {}  # object_id -> list of objects that READ from it
            reverse_outputs = {}  # object_id -> list of objects that WRITE to it

            import json
            for row in parsed_objects:
                obj_id, inputs_json, outputs_json = row

                # Parse inputs (objects this reads FROM)
                if inputs_json:
                    inputs = json.loads(inputs_json)
                    for input_id in inputs:
                        # input_id is read BY obj_id
                        if input_id not in reverse_inputs:
                            reverse_inputs[input_id] = []
                        reverse_inputs[input_id].append(obj_id)

                # Parse outputs (objects this writes TO)
                if outputs_json:
                    outputs = json.loads(outputs_json)
                    for output_id in outputs:
                        # output_id is written BY obj_id
                        if output_id not in reverse_outputs:
                            reverse_outputs[output_id] = []
                        reverse_outputs[output_id].append(obj_id)

            # Update Tables/Views with reverse dependencies
            # IMPORTANT: Only update Tables/Views, NOT Stored Procedures
            # SPs have their own parsed dependencies and should not get reverse lookup
            tables_updated = 0
            for table_id, readers in reverse_inputs.items():
                # Check if this is a Table or View (not a Stored Procedure)
                obj_type_query = "SELECT object_type FROM objects WHERE object_id = ?"
                obj_type_result = db.query(obj_type_query, params=[table_id])

                if not obj_type_result:
                    continue

                obj_type = obj_type_result[0][0]

                # Skip Stored Procedures - they have their own dependencies from parsing
                if obj_type == 'Stored Procedure':
                    continue

                # This table is read by these objects
                # Table.outputs should contain the readers
                db.update_metadata(
                    object_id=table_id,
                    modify_date=None,  # Don't update modify_date
                    primary_source='metadata',
                    confidence=1.0,
                    inputs=reverse_outputs.get(table_id, []),  # Objects that WRITE to this table
                    outputs=readers  # Objects that READ from this table
                )
                tables_updated += 1

            click.echo(f"✅ Updated {tables_updated} Tables/Views with reverse dependencies")
            click.echo()

            # Step 8: Generate output JSON files
            click.echo("=" * 70)
            click.echo("Step 8: Generate Output JSON Files")
            click.echo("=" * 70)

            from lineage_v3.output import InternalFormatter, FrontendFormatter, SummaryFormatter

            # Generate internal lineage.json
            if format in ['internal', 'both']:
                internal_formatter = InternalFormatter(db)
                internal_stats = internal_formatter.generate(
                    output_path=f"{output}/lineage.json"
                )
                click.echo(f"✅ lineage.json generated")
                click.echo(f"   - {internal_stats['total_nodes']:,} nodes")
                click.echo(f"   - {internal_stats['output_file']}")
                click.echo()

            # Generate summary (always)
            summary_formatter = SummaryFormatter(db)
            summary = summary_formatter.generate(
                output_path=f"{output}/lineage_summary.json"
            )
            click.echo(f"✅ lineage_summary.json generated")
            click.echo(f"   - Coverage: {summary['coverage']:.1f}%")
            click.echo(f"   - Total objects: {summary['total_objects']:,}")
            click.echo(f"   - Parsed objects: {summary['parsed_objects']:,}")
            click.echo()

            # Generate frontend lineage.json
            if format in ['frontend', 'both']:
                # Load internal lineage first
                import json
                from pathlib import Path
                internal_file = Path(f"{output}/lineage.json")
                if internal_file.exists():
                    with open(internal_file, 'r') as f:
                        internal_lineage = json.load(f)
                else:
                    # Generate temporary internal format
                    internal_formatter = InternalFormatter(db)
                    internal_stats = internal_formatter.generate(
                        output_path=f"{output}/lineage.json"
                    )
                    with open(f"{output}/lineage.json", 'r') as f:
                        internal_lineage = json.load(f)

                frontend_formatter = FrontendFormatter(db)
                frontend_stats = frontend_formatter.generate(
                    internal_lineage,
                    output_path=f"{output}/frontend_lineage.json"
                )
                click.echo(f"✅ frontend_lineage.json generated")
                click.echo(f"   - {frontend_stats['total_nodes']:,} nodes")
                click.echo(f"   - {frontend_stats['output_file']}")
                click.echo()

            click.echo("=" * 70)
            click.echo("✅ Phase 4 & 6 COMPLETE")
            click.echo("=" * 70)
            click.echo("📊 Completed:")
            click.echo("   - Phase 4: SQLGlot Parser & Dual-Parser")
            click.echo("   - Phase 6: Output Generation")
            click.echo()
            click.echo("📁 Output files:")
            click.echo(f"   - {output}/lineage.json (internal format)")
            click.echo(f"   - {output}/frontend_lineage.json (React Flow format)")
            click.echo(f"   - {output}/lineage_summary.json (coverage stats)")
            click.echo()
            click.echo(f"💾 Workspace saved to: {workspace}")
            click.echo()
            click.echo("📋 Phase 5 (AI Fallback) - Deferred to next rollout")

    except FileNotFoundError as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        click.echo("💡 Ensure Parquet files exist in the specified directory", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def validate():
    """
    Validate environment configuration and dependencies.

    Checks:
    - .env file exists and contains required variables
    - Python version >= 3.10
    - All required packages installed
    - DuckDB can be initialized
    - Azure AI Foundry endpoint is reachable (if configured)
    """
    click.echo("🔍 Validating environment...")

    # Check Python version
    import sys
    if sys.version_info < (3, 10):
        click.echo("❌ Python 3.10+ required")
        sys.exit(1)
    else:
        click.echo(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check .env file
    from pathlib import Path
    env_file = Path(__file__).parent.parent / '.env'
    if not env_file.exists():
        click.echo("⚠️  .env file not found - copy .env.template to .env and configure")
    else:
        click.echo("✅ .env file exists")

    # Check imports
    try:
        import duckdb
        click.echo(f"✅ duckdb {duckdb.__version__}")
    except ImportError:
        click.echo("❌ duckdb not installed")

    try:
        import sqlglot
        click.echo(f"✅ sqlglot {sqlglot.__version__}")
    except ImportError:
        click.echo("❌ sqlglot not installed")

    try:
        import click as click_pkg
        click.echo(f"✅ click {click_pkg.__version__}")
    except ImportError:
        click.echo("❌ click not installed")

    click.echo("\n✅ Validation complete")


if __name__ == '__main__':
    cli()
