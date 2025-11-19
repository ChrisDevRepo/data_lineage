#!/usr/bin/env python3
"""
Database Helper Utility

A convenience module for testing and verifying Synapse connections during development.

Usage:
    # From repository root
    python engine/utils/db_helper.py

    # Or import in other scripts
    from engine.utils.db_helper import SynapseHelper

    helper = SynapseHelper()
    results = helper.query("SELECT TOP 10 * FROM sys.objects")
    helper.print_results(results)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pyodbc
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

console = Console()


class SynapseHelper:
    """Helper class for Synapse database connections and queries."""

    def __init__(self):
        """Initialize connection using .env credentials."""
        self.server = os.getenv('SYNAPSE_SERVER')
        self.database = os.getenv('SYNAPSE_DATABASE')
        self.username = os.getenv('SYNAPSE_USERNAME')
        self.password = os.getenv('SYNAPSE_PASSWORD')
        self.connection = None

        # Validate credentials
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError(
                "Missing Synapse credentials in .env file. "
                "Required: SYNAPSE_SERVER, SYNAPSE_DATABASE, SYNAPSE_USERNAME, SYNAPSE_PASSWORD"
            )

    def connect(self) -> pyodbc.Connection:
        """
        Establish connection to Synapse.

        Returns:
            pyodbc.Connection object

        Raises:
            pyodbc.Error: If connection fails
        """
        if self.connection:
            return self.connection

        # Build connection string
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )

        try:
            console.print(f"[yellow]Connecting to {self.server}...[/yellow]")
            self.connection = pyodbc.connect(conn_str)
            console.print(f"[green]✓ Connected to {self.database}[/green]")
            return self.connection
        except pyodbc.Error as e:
            console.print(f"[red]✗ Connection failed: {e}[/red]")
            raise

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            console.print("[yellow]Disconnected from Synapse[/yellow]")

    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries.

        Args:
            sql: SQL query string
            params: Optional tuple of parameters for parameterized queries

        Returns:
            List of dictionaries with column names as keys
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # Get column names
            columns = [column[0] for column in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            return results

        finally:
            cursor.close()

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        """
        Execute a SQL statement (INSERT, UPDATE, DELETE) and return affected rows.

        Args:
            sql: SQL statement
            params: Optional tuple of parameters

        Returns:
            Number of affected rows
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            conn.commit()
            return cursor.rowcount

        finally:
            cursor.close()

    def print_results(self, results: List[Dict[str, Any]], title: str = "Query Results"):
        """
        Pretty-print query results using Rich tables.

        Args:
            results: List of dictionaries from query()
            title: Table title
        """
        if not results:
            console.print(f"[yellow]{title}: No results[/yellow]")
            return

        # Create table
        table = Table(title=title, show_header=True, header_style="bold magenta")

        # Add columns
        for column in results[0].keys():
            table.add_column(column)

        # Add rows
        for row in results:
            table.add_row(*[str(value) for value in row.values()])

        console.print(table)
        console.print(f"[cyan]({len(results)} rows)[/cyan]")

    def test_connection(self) -> bool:
        """
        Test database connection and print server info.

        Returns:
            True if connection successful
        """
        try:
            # Synapse-compatible version query
            results = self.query("SELECT @@VERSION AS Version")
            self.print_results(results, "Connection Test")
            console.print(f"[green]✓ Connected to database: {self.database}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Connection test failed: {e}[/red]")
            return False

    def list_schemas(self) -> List[str]:
        """
        List all schemas in the database.

        Returns:
            List of schema names
        """
        results = self.query("""
            SELECT name
            FROM sys.schemas
            ORDER BY name
        """)
        schemas = [r['name'] for r in results]
        console.print(f"[green]Found {len(schemas)} schemas[/green]")
        return schemas

    def list_objects(self, schema: str = None, object_type: str = None) -> List[Dict[str, Any]]:
        """
        List database objects with optional filtering.

        Args:
            schema: Filter by schema name (optional)
            object_type: Filter by type: 'U' (table), 'V' (view), 'P' (procedure)

        Returns:
            List of objects with schema, name, and type
        """
        sql = """
            SELECT
                s.name AS schema_name,
                o.name AS object_name,
                o.type_desc AS object_type,
                o.create_date,
                o.modify_date
            FROM sys.objects o
            JOIN sys.schemas s ON o.schema_id = s.schema_id
            WHERE o.type IN ('U', 'V', 'P')
        """

        conditions = []
        if schema:
            conditions.append(f"s.name = '{schema}'")
        if object_type:
            conditions.append(f"o.type = '{object_type}'")

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        sql += " ORDER BY s.name, o.name"

        return self.query(sql)

    def get_object_definition(self, schema: str, object_name: str) -> Optional[str]:
        """
        Get the DDL definition of a stored procedure or view.

        Args:
            schema: Schema name
            object_name: Object name

        Returns:
            DDL definition text or None if not found
        """
        results = self.query("""
            SELECT m.definition
            FROM sys.sql_modules m
            JOIN sys.objects o ON m.object_id = o.object_id
            JOIN sys.schemas s ON o.schema_id = s.schema_id
            WHERE s.name = ? AND o.name = ?
        """, (schema, object_name))

        return results[0]['definition'] if results else None

    def get_dependencies(self, schema: str, object_name: str) -> List[Dict[str, Any]]:
        """
        Get dependencies for an object using sys.sql_expression_dependencies.

        Args:
            schema: Schema name
            object_name: Object name

        Returns:
            List of dependencies with referencing and referenced objects
        """
        return self.query("""
            SELECT
                s1.name AS referencing_schema,
                o1.name AS referencing_object,
                o1.type_desc AS referencing_type,
                d.referenced_schema_name,
                d.referenced_entity_name,
                o2.type_desc AS referenced_type
            FROM sys.sql_expression_dependencies d
            JOIN sys.objects o1 ON d.referencing_id = o1.object_id
            JOIN sys.schemas s1 ON o1.schema_id = s1.schema_id
            LEFT JOIN sys.objects o2 ON d.referenced_id = o2.object_id
            WHERE s1.name = ? AND o1.name = ?
        """, (schema, object_name))

    def get_table_info(self, schema: str, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a table.

        Args:
            schema: Schema name
            table_name: Table name

        Returns:
            Dictionary with table metadata
        """
        results = self.query("""
            SELECT
                o.object_id,
                s.name AS schema_name,
                o.name AS table_name,
                o.create_date,
                o.modify_date,
                p.rows AS row_count,
                ds.name AS distribution_type
            FROM sys.objects o
            JOIN sys.schemas s ON o.schema_id = s.schema_id
            JOIN sys.pdw_table_mappings tm ON o.object_id = tm.object_id
            JOIN sys.pdw_nodes_tables nt ON tm.physical_name = nt.name
            JOIN sys.partitions p ON nt.object_id = p.object_id AND p.index_id IN (0,1)
            JOIN sys.pdw_table_distribution_properties dp ON o.object_id = dp.object_id
            JOIN sys.pdw_distributions ds ON dp.distribution_policy_desc = ds.distribution_policy_desc
            WHERE s.name = ? AND o.name = ? AND o.type = 'U'
            GROUP BY o.object_id, s.name, o.name, o.create_date, o.modify_date, p.rows, ds.name
        """, (schema, table_name))

        return results[0] if results else {}


def main():
    """Main function for testing the helper."""
    console.print("[bold cyan]Synapse Database Helper Utility[/bold cyan]")
    console.print("=" * 70)

    try:
        # Initialize helper
        helper = SynapseHelper()

        # Test connection
        console.print("\n[bold]1. Testing Connection[/bold]")
        if not helper.test_connection():
            return 1

        # List schemas
        console.print("\n[bold]2. Listing Schemas[/bold]")
        schemas = helper.list_schemas()
        console.print(f"[cyan]Schemas:[/cyan] {', '.join(schemas)}")

        # List tables in CONSUMPTION_FINANCE
        console.print("\n[bold]3. Sample: Tables in CONSUMPTION_FINANCE[/bold]")
        objects = helper.list_objects(schema='CONSUMPTION_FINANCE', object_type='U')
        helper.print_results(objects[:10], "Tables in CONSUMPTION_FINANCE (first 10)")

        # List stored procedures in CONSUMPTION_ClinOpsFinance
        console.print("\n[bold]4. Sample: Stored Procedures in CONSUMPTION_ClinOpsFinance[/bold]")
        procedures = helper.list_objects(schema='CONSUMPTION_ClinOpsFinance', object_type='P')
        helper.print_results(procedures[:10], "Stored Procedures (first 10)")

        # Disconnect
        helper.disconnect()

        console.print("\n[green]✓ All tests completed successfully![/green]")
        return 0

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
