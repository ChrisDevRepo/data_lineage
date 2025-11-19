#!/usr/bin/env python3
"""
DuckDB Workspace Helper Utility
================================

Quick helper for testing and verifying DuckDB workspace queries.
Useful during development for:
- Testing workspace queries
- Verifying table contents
- Debugging parser results

Usage:
    python engine/utils/duckdb_helper.py
    python engine/utils/duckdb_helper.py "SELECT * FROM objects LIMIT 5"

Author: Vibecoding
Version: 1.0.0
Date: 2025-10-26
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table as RichTable
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.core import DuckDBWorkspace


class DuckDBHelper:
    """Helper class for DuckDB workspace operations."""

    def __init__(self, workspace_path: str = "parquet_snapshots/lineage_workspace.duckdb"):
        """Initialize helper with workspace path."""
        self.workspace_path = workspace_path
        self.workspace = None
        self.console = Console()

    def connect(self):
        """Connect to DuckDB workspace."""
        self.console.print(f"\n[bold cyan]DuckDB Workspace Helper Utility[/bold cyan]")
        self.console.print("=" * 70)

        self.console.print(f"\n1. Connecting to Workspace")
        self.console.print(f"Workspace: [cyan]{self.workspace_path}[/cyan]")

        self.workspace = DuckDBWorkspace(self.workspace_path)
        self.workspace.connect()

        self.console.print("[green]✓[/green] Connected to workspace")

    def list_tables(self):
        """List all tables in workspace."""
        self.console.print("\n2. Listing Tables")

        query = "SHOW TABLES"
        results = self.workspace.query(query)

        if results:
            tables = [row[0] for row in results]
            self.console.print(f"Found [bold]{len(tables)}[/bold] tables:")
            for table in tables:
                self.console.print(f"  - [cyan]{table}[/cyan]")
        else:
            self.console.print("[yellow]⚠[/yellow] No tables found (workspace empty)")

    def show_object_stats(self):
        """Show object statistics."""
        self.console.print("\n3. Object Statistics")

        # Check if objects table exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]
        if 'objects' not in tables:
            self.console.print("[yellow]⚠[/yellow] Objects table not loaded")
            return

        query = """
        SELECT object_type, COUNT(*) as count
        FROM objects
        GROUP BY object_type
        ORDER BY count DESC
        """

        results = self.workspace.query(query)

        if results:
            table = RichTable(title="Objects by Type")
            table.add_column("Type", style="cyan")
            table.add_column("Count", style="green", justify="right")

            total = 0
            for obj_type, count in results:
                table.add_row(obj_type, str(count))
                total += count

            table.add_section()
            table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

            self.console.print(table)
        else:
            self.console.print("[yellow]⚠[/yellow] No objects found")

    def show_parser_stats(self):
        """Show parser statistics."""
        self.console.print("\n4. Parser Statistics")

        # Check if lineage_metadata table exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]
        if 'lineage_metadata' not in tables:
            self.console.print("[yellow]⚠[/yellow] lineage_metadata table not found")
            return

        query = """
        SELECT
            COUNT(*) as total_parsed,
            SUM(CASE WHEN confidence >= 0.85 THEN 1 ELSE 0 END) as high_conf,
            SUM(CASE WHEN confidence >= 0.75 AND confidence < 0.85 THEN 1 ELSE 0 END) as med_conf,
            SUM(CASE WHEN confidence < 0.75 THEN 1 ELSE 0 END) as low_conf,
            AVG(confidence) as avg_conf
        FROM lineage_metadata
        WHERE primary_source = 'parser'
        """

        results = self.workspace.query(query)

        if results and results[0][0] > 0:
            total, high, med, low, avg = results[0]

            table = RichTable(title="Parser Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Total Parsed", str(total))
            table.add_row("High Confidence (≥0.85)", f"{high} ({high/total*100:.1f}%)")
            table.add_row("Medium Confidence (0.75-0.84)", f"{med} ({med/total*100:.1f}%)")
            table.add_row("Low Confidence (<0.75)", f"{low} ({low/total*100:.1f}%)")
            table.add_row("Average Confidence", f"{avg:.3f}")

            self.console.print(table)
        else:
            self.console.print("[yellow]⚠[/yellow] No parsed objects found")

    def show_dual_parser_stats(self):
        """Show dual-parser statistics."""
        self.console.print("\n5. Dual-Parser Statistics")

        # Check if parser_comparison_log table exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]
        if 'parser_comparison_log' not in tables:
            self.console.print("[yellow]⚠[/yellow] parser_comparison_log table not found (dual-parser not used)")
            return

        query = """
        SELECT
            dual_parser_decision,
            COUNT(*) as count,
            AVG(final_confidence) as avg_conf
        FROM parser_comparison_log
        GROUP BY dual_parser_decision
        ORDER BY count DESC
        """

        results = self.workspace.query(query)

        if results:
            table = RichTable(title="Dual-Parser Decisions")
            table.add_column("Decision", style="cyan")
            table.add_column("Count", style="green", justify="right")
            table.add_column("Avg Confidence", style="yellow", justify="right")

            total = sum(row[1] for row in results)
            for decision, count, avg_conf in results:
                table.add_row(
                    decision,
                    f"{count} ({count/total*100:.1f}%)",
                    f"{avg_conf:.3f}"
                )

            self.console.print(table)
        else:
            self.console.print("[yellow]⚠[/yellow] No dual-parser comparisons logged yet")

    def query(self, sql: str):
        """Execute custom query and display results."""
        self.console.print(f"\n[bold cyan]Custom Query:[/bold cyan]")
        self.console.print(Panel(sql, border_style="dim"))

        try:
            results = self.workspace.query(sql)

            if results:
                self.print_results(results)
            else:
                self.console.print("[yellow]No results[/yellow]")
        except Exception as e:
            self.console.print(f"[red]✗[/red] Query failed: {e}")

    def print_results(self, results, max_rows: int = 50):
        """Print query results in a formatted table."""
        if not results:
            self.console.print("[yellow]No results[/yellow]")
            return

        # Get column count
        num_cols = len(results[0])

        table = RichTable()
        for i in range(num_cols):
            table.add_column(f"Column {i}", style="cyan")

        # Add rows (limit to max_rows)
        for i, row in enumerate(results):
            if i >= max_rows:
                self.console.print(f"\n[dim]... showing first {max_rows} of {len(results)} rows[/dim]")
                break
            table.add_row(*[str(val) for val in row])

        self.console.print(table)
        self.console.print(f"[dim]({len(results)} rows)[/dim]")

    def disconnect(self):
        """Disconnect from workspace."""
        if self.workspace:
            self.workspace.disconnect()
            self.console.print("\n[green]✓[/green] Disconnected from workspace")


def main():
    """Main entry point."""
    # Parse arguments: workspace path can be specified as --workspace=path
    workspace_path = "lineage_workspace.duckdb"  # Default
    query_args = []

    for arg in sys.argv[1:]:
        if arg.startswith("--workspace="):
            workspace_path = arg.split("=", 1)[1]
        else:
            query_args.append(arg)

    helper = DuckDBHelper(workspace_path=workspace_path)

    try:
        helper.connect()

        # If custom query provided, execute it
        if query_args:
            custom_query = " ".join(query_args)
            helper.query(custom_query)
        else:
            # Default: show all statistics
            helper.list_tables()
            helper.show_object_stats()
            helper.show_parser_stats()
            helper.show_dual_parser_stats()

        helper.disconnect()

        helper.console.print("\n[green]✓[/green] All operations completed successfully!")

    except Exception as e:
        helper.console.print(f"\n[red]✗ Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
