import urllib.request
import json
import time
import pandas as pd
import os
import glob

API_URL = "http://localhost:8000/api"

def run_test():
    # 2. Trigger Refresh (Full Refresh to ensure re-parsing)
    print("\nTriggering Full Refresh (incremental=False)...")
    req = urllib.request.Request(f"{API_URL}/database/refresh?incremental=false", method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            job_id = data['job_id']
            print(f"Job started: {job_id}")
    except Exception as e:
        print(f"Failed to trigger refresh: {e}")
        return

    # 2. Poll Status
    while True:
        try:
            with urllib.request.urlopen(f"{API_URL}/status/{job_id}") as response:
                status_data = json.loads(response.read().decode())
                state = status_data['status']
                print(f"Status: {state} - {status_data.get('message', '')}")
                
                if state == "completed":
                    break
                if state == "failed":
                    print("Job Failed!")
                    return
        except Exception as e:
            print(f"Polling error: {e}")
            return
        
        time.sleep(2)

    # 3. Verify Results (Check lineage.json for Parsed Hints)
    # The files are in /tmp/jobs/{job_id}/
    job_dir = f"/tmp/jobs/{job_id}"
    lineage_file = f"{job_dir}/lineage.json"
    
    if not os.path.exists(lineage_file):
        print(f"❌ File not found: {lineage_file}")
        return

    print(f"Verifying {lineage_file}...")
    with open(lineage_file, 'r') as f:
        nodes = json.load(f)
        
    # Helper to find ID by name
    def find_id(schema, name):
        for n in nodes:
            if n['schema'].lower() == schema.lower() and n['name'].lower() == name.lower():
                return n['id']
        return None

    # Helper to find node by name
    def find_node(schema, name):
        for n in nodes:
            if n['schema'].lower() == schema.lower() and n['name'].lower() == name.lower():
                return n
        return None

    # Find IDs
    sp_node = find_node('dbo', 'usp_LineageTest_Hints')
    source_id = find_id('dbo', 'LineageSourceTable')
    target_id = find_id('dbo', 'LineageTargetTable')
    
    if not sp_node:
        print("❌ FAILURE: SP 'dbo.usp_LineageTest_Hints' not found in lineage.json")
        return

    if not source_id:
        print("❌ FAILURE: Table 'dbo.LineageSourceTable' not found in lineage.json")
        return
        
    if not target_id:
        print("❌ FAILURE: Table 'dbo.LineageTargetTable' not found in lineage.json")
        return
        
    print(f"SP Node ID: {sp_node['id']}")
    print(f"Source ID: {source_id}")
    print(f"Target ID: {target_id}")
    print(f"SP Inputs: {sp_node['inputs']}")
    print(f"SP Outputs: {sp_node['outputs']}")
    
    # Check Edges
    has_input = source_id in sp_node['inputs']
    has_output = target_id in sp_node['outputs']
    
    if has_input and has_output:
        print("✅ SUCCESS: Parsed Hints verified in lineage graph!")
    else:
        print("❌ FAILURE: Missing lineage edges.")
        print(f"Found Input (Source->SP): {has_input}")
        print(f"Found Output (SP->Target): {has_output}")

if __name__ == "__main__":
    run_test()
