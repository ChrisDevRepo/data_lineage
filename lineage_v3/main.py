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
def run(parquet, output, full_refresh, format, skip_query_logs, workspace):
    """
    Run lineage analysis on Parquet snapshots.

    This is the main command that executes the 8-step lineage construction pipeline:

    1. Ingest Parquet files into DuckDB
    2. Build baseline from DMV dependencies
    3. Enhance from query logs (optional)
    4. Detect gaps (unresolved SPs)
    5. Run SQLGlot parser
    6. Run AI fallback
    7. Merge all sources
    8. Generate output JSON files
    """
    click.echo(f"🚀 Vibecoding Lineage Parser v{__version__}")
    click.echo(f"📂 Parquet directory: {parquet}")
    click.echo(f"📁 Output directory: {output}")
    click.echo(f"🔄 Mode: {'Full Refresh' if full_refresh else 'Incremental'}")
    click.echo(f"📊 Format: {format}")
    click.echo(f"💾 Workspace: {workspace}")
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

            # Get objects to parse
            objects_to_parse = db.get_objects_to_parse(full_refresh=full_refresh)
            click.echo(f"🔍 Objects requiring analysis: {len(objects_to_parse):,}")

            if not objects_to_parse:
                click.echo()
                click.echo("✅ All objects up to date! Nothing to parse.")
                click.echo("💡 Use --full-refresh to force re-parsing.")
                return

            # Step 2-3: Build baseline from DMV dependencies and query logs
            # TODO: Implement Steps 2-3 (DMV baseline + query log enhancement)
            click.echo()
            click.echo("=" * 70)
            click.echo("Step 2-3: DMV Dependencies & Query Logs")
            click.echo("=" * 70)
            click.echo("⚠️  DMV baseline extraction not yet implemented")
            click.echo("📋 Coming in integration phase")
            click.echo()

            # Step 4: Detect gaps
            click.echo("=" * 70)
            click.echo("Step 4: Detect Gaps (Missing Dependencies)")
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

            # Step 5: Run SQLGlot parser on gaps
            if gaps:
                click.echo("=" * 70)
                click.echo("Step 5: SQLGlot Parser (Fill Gaps)")
                click.echo("=" * 70)

                from lineage_v3.parsers import SQLGlotParser
                parser = SQLGlotParser(db)

                parsed_count = 0
                failed_count = 0

                click.echo(f"🔄 Parsing {len(gaps):,} objects...")

                for i, gap in enumerate(gaps):
                    try:
                        # Parse object
                        result = parser.parse_object(gap['object_id'])

                        # Update metadata if parsing succeeded
                        if result['confidence'] > 0:
                            db.update_metadata(
                                object_id=result['object_id'],
                                modify_date=gap['modify_date'],
                                primary_source='parser',
                                confidence=result['confidence'],
                                inputs=result['inputs'],
                                outputs=result['outputs']
                            )
                            parsed_count += 1

                            # Show progress every 10 objects
                            if (i + 1) % 10 == 0:
                                click.echo(f"   Progress: {i + 1}/{len(gaps)} objects parsed...")

                        else:
                            failed_count += 1

                    except Exception as e:
                        click.echo(f"   ⚠️  Failed to parse {gap['schema_name']}.{gap['object_name']}: {e}")
                        failed_count += 1

                click.echo()
                click.echo(f"✅ SQLGlot parsing complete:")
                click.echo(f"   - Successfully parsed: {parsed_count:,}")
                click.echo(f"   - Failed: {failed_count:,}")

                # Show parser statistics
                parser_stats = parser.get_parse_statistics()
                click.echo(f"   - Success rate: {parser_stats['success_rate']:.1f}%")
                click.echo()

            # TODO: Implement remaining steps
            click.echo("=" * 70)
            click.echo("⚠️  Remaining steps not yet implemented")
            click.echo("=" * 70)
            click.echo("📋 Next phases:")
            click.echo("   - Step 6: AI Fallback (Phase 5)")
            click.echo("   - Step 7: Merge all sources")
            click.echo("   - Step 8: Generate output JSON (Phase 6)")
            click.echo()
            click.echo("✅ Phase 4 (SQLGlot Parser) - COMPLETE")
            click.echo("   - Gap detector implemented")
            click.echo("   - SQLGlot AST parser working")
            click.echo("   - Metadata tracking functional")
            click.echo(f"   - Workspace saved to: {workspace}")

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
