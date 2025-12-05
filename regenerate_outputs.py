#!/usr/bin/env python3
"""
Regenerate Output Files from Existing DuckDB
=============================================

This script regenerates lineage output files (lineage.json, frontend_lineage.json,
lineage_summary.json) from an existing DuckDB workspace WITHOUT re-parsing SQL.

Use this after code changes to output formatters to update the JSON files
with new fields (like bidirectional_with) without reprocessing the entire dataset.

Usage:
    python regenerate_outputs.py [--duckdb PATH] [--output-dir PATH]

Arguments:
    --duckdb PATH       Path to DuckDB file (default: data/lineage_workspace.duckdb)
    --output-dir PATH   Output directory (default: data/)
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.core.duckdb_workspace import DuckDBWorkspace
from engine.output import FrontendFormatter, InternalFormatter, SummaryFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def regenerate_outputs(duckdb_path: str, output_dir: str):
    """
    Regenerate all output files from existing DuckDB workspace.

    Args:
        duckdb_path: Path to DuckDB workspace file
        output_dir: Directory to write output files
    """
    duckdb_path = Path(duckdb_path)
    output_dir = Path(output_dir)

    if not duckdb_path.exists():
        logger.error(f"❌ DuckDB file not found: {duckdb_path}")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"📂 Loading DuckDB workspace: {duckdb_path}")
    logger.info(f"📁 Output directory: {output_dir}")

    try:
        # Open workspace
        workspace = DuckDBWorkspace(str(duckdb_path))
        workspace.connect()

        # Check if we have data
        result = workspace.query("SELECT COUNT(*) FROM objects")
        object_count = result[0][0]

        result = workspace.query("SELECT COUNT(*) FROM lineage_edges")
        edge_count = result[0][0]

        logger.info(
            f"📊 Workspace contains {object_count} objects and {edge_count} edges"
        )

        if object_count == 0:
            logger.error("❌ No objects found in workspace. Please import data first.")
            return False

        # Generate internal lineage.json
        logger.info("🔨 Generating internal lineage.json...")
        internal_formatter = InternalFormatter(workspace)
        internal_stats = internal_formatter.generate(
            output_path=str(output_dir / "lineage.json")
        )
        logger.info(f"✅ Internal lineage: {internal_stats['total_nodes']} nodes")

        # Generate summary
        logger.info("🔨 Generating lineage_summary.json...")
        summary_formatter = SummaryFormatter(workspace)
        summary = summary_formatter.generate(
            output_path=str(output_dir / "lineage_summary.json")
        )
        logger.info(f"✅ Summary generated")

        # Load internal lineage for frontend conversion
        with open(output_dir / "lineage.json", "r") as f:
            internal_lineage = json.load(f)

        # Generate frontend lineage.json (without DDL for performance)
        logger.info("🔨 Generating frontend_lineage.json...")
        frontend_formatter = FrontendFormatter(workspace)
        frontend_stats = frontend_formatter.generate(
            internal_lineage,
            output_path=str(output_dir / "frontend_lineage.json"),
            include_ddl=False,
        )
        logger.info(f"✅ Frontend lineage: {frontend_stats['total_nodes']} nodes")

        # Copy to latest_frontend_lineage.json (for UI)
        import shutil

        shutil.copy(
            output_dir / "frontend_lineage.json",
            output_dir / "latest_frontend_lineage.json",
        )
        logger.info(f"✅ Copied to latest_frontend_lineage.json")

        logger.info("🎉 All output files regenerated successfully!")
        logger.info(f"📂 Output files:")
        logger.info(f"   - {output_dir / 'lineage.json'}")
        logger.info(f"   - {output_dir / 'frontend_lineage.json'}")
        logger.info(f"   - {output_dir / 'latest_frontend_lineage.json'}")
        logger.info(f"   - {output_dir / 'lineage_summary.json'}")

        if workspace.connection:
            workspace.connection.close()
        return True    except Exception as e:
        logger.error(f"❌ Error regenerating outputs: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate lineage output files from existing DuckDB workspace"
    )
    parser.add_argument(
        "--duckdb",
        default="data/lineage_workspace.duckdb",
        help="Path to DuckDB workspace file (default: data/lineage_workspace.duckdb)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/",
        help="Output directory for JSON files (default: data/)",
    )

    args = parser.parse_args()

    success = regenerate_outputs(args.duckdb, args.output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
