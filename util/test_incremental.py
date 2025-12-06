import urllib.request
import json
import time
import pyodbc
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.config.settings import settings

API_URL = "http://localhost:8000/api"

def trigger_refresh(incremental=True):
    url = f"{API_URL}/database/refresh?incremental={'true' if incremental else 'false'}"
    print(f"\nTriggering Refresh (incremental={incremental})...")
    req = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['job_id']
    except Exception as e:
        print(f"Failed to trigger refresh: {e}")
        return None

def poll_job(job_id):
    print(f"Polling Job: {job_id}")
    while True:
        try:
            with urllib.request.urlopen(f"{API_URL}/status/{job_id}") as response:
                status_data = json.loads(response.read().decode())
                state = status_data['status']
                
                if state == "completed":
                    return status_data
                if state == "failed":
                    print("Job Failed!")
                    return status_data
                
                time.sleep(1)
        except Exception as e:
            print(f"Polling error: {e}")
            return None

def update_sp_in_db():
    print("\nModifying 'dbo.usp_LineageTest_Hints' in database...")
    conn_str = settings.db.connection_string
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    
    # Just update the comment/whitespace to trigger modify_date update
    # Keeping the Hints exactly the same
    sp_sql = """
    CREATE OR ALTER PROCEDURE dbo.usp_LineageTest_Hints
    AS
    BEGIN
        -- UPDATED FOR INCREMENTAL TEST
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
    cursor.execute(sp_sql)
    conn.close()
    print("✅ SP Updated.")

def run_test():
    # 1. Baseline: Run incremental. Should process 0 objects if nothing changed.
    # (Assuming full refresh happened recently)
    job_id = trigger_refresh(incremental=True)
    result = poll_job(job_id)
    
    # Check stats in result (if available) or Summary file
    # For now, we look at the message or summary json
    summary_url = f"{API_URL}/lineage/export?format=json" # This might be the wrong endpoint for job summary
    # Actually, the result of poll_job might contain stats if we look at status_data
    
    # Let's inspect the job dir locally for precise counts
    # Baseline: Check backend log for "Returning X objects for parsing"
    # We'll read the last 100 lines of /tmp/backend.log
    time.sleep(2) # Wait for logs to flush
    
    def get_last_detected_count():
        try:
            with open("/tmp/backend.log", "r") as f:
                lines = f.readlines()
                # Read from end
                for line in reversed(lines):
                    if "Returning" in line and "objects for parsing" in line:
                         # Format:2025-.. - [DEBUG] Returning X objects for parsing
                         # split by Returning and take the part after
                         parts = line.split("Returning")
                         if len(parts) > 1:
                             count_part = parts[1].strip().split(" ")[0]
                             return int(count_part)
        except Exception as e:
            print(f"Log parsing error: {e}")
            return -1
        return -1

    baseline_count = get_last_detected_count()
    print(f"Baseline (Incremental) Count: {baseline_count}")

    # 2. Modify Logic
    update_sp_in_db()

    # 3. Test: Run incremental again. Should process exactly 1 object.
    job_id_2 = trigger_refresh(incremental=True)
    result_2 = poll_job(job_id_2)
    time.sleep(2) # Wait for logs
    
    incremental_count = get_last_detected_count()
    print(f"Incremental Count after Modification: {incremental_count}")
    
    if incremental_count == 1:
        print("✅ SUCCESS: Incremental refresh parsed exactly 1 modified object.")
    elif incremental_count == 0:
        print("❌ FAILURE: Parsed 0 objects. Modification not detected.")
    else:
         print(f"⚠️  WARNING: Parsed {incremental_count} objects. Expected 1.")

if __name__ == "__main__":
    run_test()
