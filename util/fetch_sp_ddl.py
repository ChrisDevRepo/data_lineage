import pyodbc
from engine.config.settings import settings

def fetch_ddl():
    conn_str = settings.db.connection_string
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    
    # ID from inspect_parquet.py: 1607676775
    # Or just use object_id function
    
    sql = "SELECT OBJECT_DEFINITION(OBJECT_ID('dbo.usp_LineageTest_Hints'))"
    cursor.execute(sql)
    row = cursor.fetchone()
    if row:
        ddl = row[0]
        print(f"--- DDL REPR ---\n{repr(ddl)}")
    else:
        print("SP not found")
        
    conn.close()

if __name__ == "__main__":
    fetch_ddl()
