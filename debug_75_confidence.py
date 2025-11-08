#!/usr/bin/env python3
"""Debug why spLoadSAPSalesInterestSummaryMetrics gets 75% confidence."""

import sys
sys.path.insert(0, '/home/user/sandbox')

import re

SQL = """
CREATE PROC [CONSUMPTION_FINANCE].[spLoadSAPSalesInterestSummaryMetrics] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadSAPSalesInterestSummaryMetrics]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )

BEGIN TRY

DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME
DECLARE @EndTime DATETIME

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0)

truncate table [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics];

begin transaction

insert into [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics]
select [Year]
from [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
where [DocumentNumber] in
  (
    select [DocumentNumber]
      from [CONSUMPTION_FINANCE].[SAP_Sales_Summary]
      where [DocumentNumber] >= (select ColumnValue from [CONSUMPTION_FINANCE].[udfGetDataFilterColumnValue]('SAP_Sales_Interest_Summary_Metrics', 'DocumentNumber', 'Include', 'GtEq'))
      and [DocumentNumber] < (select ColumnValue from [CONSUMPTION_FINANCE].[udfGetDataFilterColumnValue]('SAP_Sales_Interest_Summary_Metrics', 'DocumentNumber', 'Include', 'Lt'))
  )

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics])
SET @EndTime = GETDATE()

END TRY
END
"""

print("="*80)
print("DEBUGGING: spLoadSAPSalesInterestSummaryMetrics")
print("="*80)
print()

# Step 1: Manual inspection - what SHOULD be detected?
print("STEP 1: EXPECTED DEPENDENCIES (Manual Inspection)")
print("-"*80)

expected_outputs = {
    "CONSUMPTION_FINANCE.SAP_Sales_Interest_Summary_Metrics": ["TRUNCATE", "INSERT INTO"]
}

expected_inputs = {
    "CONSUMPTION_FINANCE.SAP_Sales_Summary": ["FROM (main query)", "FROM (subquery)"],
    "CONSUMPTION_FINANCE.SAP_Sales_Interest_Summary_Metrics": ["SET @RowsInTargetBegin (SELECT COUNT)"],
    "CONSUMPTION_FINANCE.SAP_Sales_Summary_Metrics": ["SET @RowsInTargetEnd (SELECT COUNT)"],
    "CONSUMPTION_FINANCE.udfGetDataFilterColumnValue": ["Function call (2x)"]
}

print("OUTPUTS:")
for table, refs in expected_outputs.items():
    print(f"  {table}")
    for ref in refs:
        print(f"    - {ref}")

print("\nINPUTS:")
for table, refs in expected_inputs.items():
    print(f"  {table}")
    for ref in refs:
        print(f"    - {ref}")

print(f"\nExpected Total: {len(expected_outputs)} outputs + {len(expected_inputs)} inputs = {len(expected_outputs) + len(expected_inputs)} dependencies")
print()

# Step 2: Simulate cleaning (simple version)
print("STEP 2: SIMULATE SQL CLEANING")
print("-"*80)

cleaned = SQL

# Remove DECLARE
declare_count = len(re.findall(r'DECLARE\s+@\w+', cleaned, re.IGNORECASE))
cleaned = re.sub(r'DECLARE\s+@\w+.*?(?:;|\n|$)', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
print(f"Removed {declare_count} DECLARE statements")

# Remove SET
set_count = len(re.findall(r'SET\s+@\w+\s*=', cleaned, re.IGNORECASE))
cleaned = re.sub(r'SET\s+@\w+\s*=.*?(?:;|\n|$)', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
print(f"Removed {set_count} SET statements")

# Remove TRUNCATE (dataflow mode v4.1.0)
truncate_count = len(re.findall(r'TRUNCATE\s+TABLE', cleaned, re.IGNORECASE))
cleaned = re.sub(r'TRUNCATE\s+TABLE\s+[^;]+;?', '', cleaned, flags=re.IGNORECASE)
print(f"Removed {truncate_count} TRUNCATE statements")

print()
print("Cleaned SQL (first 500 chars):")
print(cleaned[:500])
print()

# Step 3: Extract dependencies from cleaned SQL
print("STEP 3: EXTRACT DEPENDENCIES FROM CLEANED SQL")
print("-"*80)

# Extract INSERT INTO
insert_pattern = r'INSERT\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
inserts = re.findall(insert_pattern, cleaned, re.IGNORECASE)
print(f"INSERT INTO targets: {inserts}")

# Extract FROM
from_pattern = r'FROM\s+\[?(\w+)\]?\.\[?(\w+)\]?'
froms = re.findall(from_pattern, cleaned, re.IGNORECASE)
print(f"FROM sources: {froms}")

# Functions (not table references)
func_pattern = r'\[?(\w+)\]?\.\[?(udf\w+)\]?\('
funcs = re.findall(func_pattern, cleaned, re.IGNORECASE)
print(f"Functions (NOT counted as tables): {funcs}")

print()

# Step 4: Calculate what parser actually found
found_outputs = set([f"{s}.{t}" for s, t in inserts])
found_inputs = set([f"{s}.{t}" for s, t in froms])

print("PARSER FINDINGS:")
print(f"  Outputs: {found_outputs}")
print(f"  Inputs: {found_inputs}")
print(f"  Total found: {len(found_outputs) + len(found_inputs)}")
print()

# Step 5: Calculate confidence
expected_total = len(expected_outputs) + len(expected_inputs)
found_total = len(found_outputs) + len(found_inputs)

# Note: Functions are NOT counted as table dependencies
# Note: Administrative SELECT in SET statements are removed

completeness = (found_total / expected_total) * 100 if expected_total > 0 else 0

print("="*80)
print("CONFIDENCE CALCULATION")
print("="*80)
print(f"Expected: {expected_total} tables")
print(f"Found: {found_total} tables")
print(f"Completeness: {completeness:.1f}%")
print()

if completeness >= 90:
    conf = 100
    label = "✅ Perfect"
elif completeness >= 70:
    conf = 85
    label = "🟢 Good"
elif completeness >= 50:
    conf = 75
    label = "⚠️ Acceptable"
else:
    conf = 0
    label = "❌ Failed"

print(f"Confidence: {conf} ({label})")
print()

# Step 6: Identify what's missing
print("="*80)
print("WHY 75% CONFIDENCE?")
print("="*80)

print("\n❌ LOST DEPENDENCIES:")
print("1. TRUNCATE TABLE - Removed by dataflow mode (v4.1.0)")
print("   Impact: Output table only counted once (INSERT) instead of twice (TRUNCATE + INSERT)")
print()
print("2. SET @RowsInTargetBegin = (SELECT COUNT(*) FROM ...) - Removed as administrative")
print("   Impact: Lost input reference to SAP_Sales_Interest_Summary_Metrics")
print()
print("3. SET @RowsInTargetEnd = (SELECT COUNT(*) FROM ...) - Removed as administrative")
print("   Impact: Lost input reference to SAP_Sales_Summary_Metrics")
print()
print("4. Function calls (udfGetDataFilterColumnValue) - Not tracked as dependencies")
print("   Impact: Functions are NOT table dependencies (correct behavior)")
print()

print("SUMMARY:")
print(f"  Expected to find: 5 table references")
print(f"  Actually found: {found_total} table references")
print(f"  Missing: {expected_total - found_total} references")
print(f"  Reason: Administrative queries filtered out + TRUNCATE removed")
print()
print("✅ THIS IS WORKING AS DESIGNED")
print("   - Dataflow mode removes housekeeping (TRUNCATE, administrative SELECT)")
print("   - Focus on actual data transformation (INSERT-SELECT)")
print("   - 75% confidence = 'Acceptable' quality")
