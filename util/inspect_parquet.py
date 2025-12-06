import pandas as pd
import sys

job_id = "4a15a198-0eb8-442e-9b4d-7f1df91960b2"
job_dir = f"/tmp/jobs/{job_id}"

print(f"--- Objects ({job_dir}/objects.parquet) ---")
try:
    obj_df = pd.read_parquet(f"{job_dir}/objects.parquet")
    print(obj_df[obj_df['schema_name'] == 'dbo'][['object_id', 'object_name', 'object_type']].to_string())
    
    sp_row = obj_df[(obj_df['schema_name'] == 'dbo') & (obj_df['object_name'] == 'usp_LineageTest_Hints')]
    if not sp_row.empty:
        sp_id = sp_row.iloc[0]['object_id']
        print(f"\nFound SP ID: {sp_id}")
    else:
        print("\n❌ SP 'usp_LineageTest_Hints' NOT FOUND in objects.parquet")
        sp_id = None
        
    print("\n--- Hinted Tables Check ---")
    hints_check = obj_df[obj_df['object_name'].isin(['LineageSourceTable', 'LineageTargetTable'])]
    if not hints_check.empty:
        print(hints_check[['object_id', 'schema_name', 'object_name', 'object_type']].to_string())
    else:
        print("❌ Hinted tables NOT FOUND in objects.parquet")

except Exception as e:
    print(e)
    sp_id = None

if sp_id:
    print(f"\n--- Dependencies for {sp_id} ({job_dir}/dependencies.parquet) ---")
    try:
        dep_df = pd.read_parquet(f"{job_dir}/dependencies.parquet")
        print(dep_df[dep_df['referencing_object_id'] == sp_id].to_string())
    except Exception as e:
        print(e)
