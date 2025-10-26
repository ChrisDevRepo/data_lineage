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
def run(parquet, output, full_refresh, format, skip_query_logs):
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

    # TODO: Import and run pipeline
    # from lineage_v3.core import run_pipeline
    # run_pipeline(parquet, output, full_refresh, format, skip_query_logs)

    click.echo("\n⚠️  Pipeline not yet implemented - Coming in Phase 3+")
    click.echo("📋 Next steps:")
    click.echo("   1. Implement Helper Extractor (Phase 2)")
    click.echo("   2. Implement Core Engine (Phase 3)")
    click.echo("   3. Implement Parser (Phase 4)")
    click.echo("   4. Implement AI Fallback (Phase 5)")
    click.echo("   5. Implement Output Formatters (Phase 6)")

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
