import os
import pyodbc
from engine.config.settings import settings

def deploy_sp():
    conn_str = settings.db.connection_string
    if not conn_str:
        print("❌ DB_CONNECTION_STRING not set")
        exit(1)
        
    print(f"Connecting to: {conn_str.split(';')[0]}...")
    
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # 1. Create Dummy Tables (Source/Target)
        print("Creating dummy tables...")
        cursor.execute("""
            IF OBJECT_ID('dbo.LineageSourceTable', 'U') IS NULL
                CREATE TABLE dbo.LineageSourceTable (ID int);
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.LineageTargetTable', 'U') IS NULL
                CREATE TABLE dbo.LineageTargetTable (ID int);
        """)

        # 2. Create the SP with Hints
        # Scenario: Reads from Source, Writes to Target (via Dynamic SQL)
        # Regex won't see the dynamic SQL 'INSERT', but Hints should catch it.
        sp_sql = """
        CREATE OR ALTER PROCEDURE dbo.usp_LineageTest_Hints
        AS
        BEGIN
            -- This comment should be removed by cleaning rules
            /* BLOCK COMMENT TO REMOVE */
            
            -- Dynamic SQL (Regex-blind)
            DECLARE @sql NVARCHAR(MAX);
            SET @sql = 'INSERT INTO dbo.LineageTargetTable SELECT ID FROM dbo.LineageSourceTable';
            EXEC sp_executesql @sql;

            -- Lineage Hints (Should be parsed despite cleaning)
            -- @LINEAGE_INPUTS: dbo.LineageSourceTable
            -- @LINEAGE_OUTPUTS: dbo.LineageTargetTable
        END;
        """
        
        print("Deploying SP: dbo.usp_LineageTest_Hints...")
        cursor.execute(sp_sql)
        print("✅ SP Deployed Successfully.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    deploy_sp()
