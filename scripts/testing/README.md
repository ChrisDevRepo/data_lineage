# Parser Testing & Validation Tools

Comprehensive testing and validation tools for the Data Lineage Parser v4.3.1.

## Tools Overview

### 1. check_parsing_results.py
**Purpose:** Database-wide parser validation and statistics

**Usage:**
```bash
python3 scripts/testing/check_parsing_results.py
```

**Output:**
- Overall statistics (total SPs, success rate)
- Confidence distribution (0, 75, 85, 100)
- Average dependencies per SP (inputs/outputs)
- Test case validation for specific SPs
- Top 10 SPs by dependency count

**When to use:**
- After parser changes to verify no regressions
- To track overall parser performance metrics
- To validate 100% success rate is maintained

---

### 2. verify_sp_parsing.py
**Purpose:** Detailed analysis of specific stored procedure parsing

**Usage:**
```bash
python3 scripts/testing/verify_sp_parsing.py
```

**Output:**
- Actual table names (not just object IDs)
- Expected vs actual sources/targets validation
- Type information for each dependency

**When to use:**
- To debug why specific SP has unexpected results
- To validate expected dependencies are found

**Example output:**
```
📋 SP: CONSUMPTION_ClinOpsFinance.spLoadFactLaborCostForEarnedValue_Post
🎯 Confidence: 100.0

📥 INPUTS (6 tables):
  [dbo].[DimDate]
  [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
  [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc]
```

---

### 3. test_upload.sh
**Purpose:** End-to-end API workflow testing with Parquet files

**Usage:**
```bash
./scripts/testing/test_upload.sh
```

**What it does:**
1. Uploads 5 Parquet files to API endpoint
2. Polls job status (90 attempts, 3 seconds each)
3. Validates job completion
4. Reports success/failure

**When to use:**
- To test complete API upload workflow
- To verify background processing works correctly
- To test with production Parquet files

**Requirements:**
- Backend running on localhost:8000
- Parquet files in `.build/temp/` directory

---

### 4. analyze_sp.py
**Purpose:** Deep debugging tool for parser failures

**Usage:**
```bash
python3 scripts/testing/analyze_sp.py
```

**Output:**
- First 1000 chars of SP DDL
- Regex pattern matches (sources/targets)
- SQLGlot WARN mode results
- Problematic patterns identified
- Expected vs actual comparison

**When to use:**
- When specific SP fails to parse correctly
- To understand why regex patterns miss tables
- To test SQLGlot behavior on complex SQL
- To identify T-SQL constructs causing issues

---

### 5. poll_job.sh
**Purpose:** Poll API job status until completion

**Usage:**
```bash
./scripts/testing/poll_job.sh <job-id>
```

**What it does:**
- Polls job status every 3 seconds
- Timeout after 60 attempts (3 minutes)
- Returns job result JSON on completion

**When to use:**
- To monitor long-running parse jobs
- As helper script for other testing workflows
- To debug job tracking issues

---

## Testing Workflow

### After Parser Changes

1. **Baseline validation:**
   ```bash
   python3 scripts/testing/check_parsing_results.py
   ```
   - Verify 100% success rate maintained
   - Check confidence distribution unchanged (or improved)

2. **Specific SP verification:**
   ```bash
   python3 scripts/testing/verify_sp_parsing.py
   ```
   - Test known problematic SPs
   - Verify expected sources/targets found

3. **API end-to-end test:**
   ```bash
   ./scripts/testing/test_upload.sh
   ```
   - Ensure full workflow works
   - Validate background processing

### When Debugging Failures

1. **Identify failing SP:**
   ```bash
   python3 scripts/testing/check_parsing_results.py
   # Look for low confidence SPs
   ```

2. **Deep analysis:**
   ```bash
   python3 scripts/testing/analyze_sp.py
   # Modify script to test specific SP
   ```

3. **Verify fix:**
   ```bash
   python3 scripts/testing/verify_sp_parsing.py
   # Confirm SP now parses correctly
   ```

---

## Parser v4.3.1 Expected Results

**Success Metrics:**
- ✅ 100% of SPs have dependencies (349/349)
- ✅ 82.5% at confidence 100
- ✅ 7.4% at confidence 85
- ✅ 10.0% at confidence 75
- ✅ Average 3.20 inputs, 1.87 outputs per SP

**Architecture:**
- Regex-first baseline (guaranteed, no context loss)
- SQLGlot RAISE mode enhancement (optional bonus)
- Full DDL scanning (no statement splitting)

---

## Troubleshooting

**Issue: check_parsing_results.py fails with "column not found"**
- Solution: Database schema may have changed. Check column names in lineage_metadata table.

**Issue: test_upload.sh times out**
- Solution: Backend may be processing slowly. Check `/tmp/backend.log` for errors.

**Issue: verify_sp_parsing.py shows "SP not found"**
- Solution: Edit script to change SP name to one that exists in your database.

**Issue: Job status returns 404 in test_upload.sh**
- Solution: Known issue with job tracking timing. Check `data/latest_frontend_lineage.json` to verify processing completed successfully.

---

**Last Updated:** 2025-11-12
**Parser Version:** v4.3.1
