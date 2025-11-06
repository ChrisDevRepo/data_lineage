# Phase 1 Test Plan - Preprocessing Validation

**Date:** 2025-11-02
**Goal:** Measure SQLGlot improvement from enhanced preprocessing (DECLARE/SET removal)

---

## Test Approach

### 1. Baseline (Current State)
- High confidence SPs: 46/202 (22.8%)
- Low confidence SPs: 156/202 (77.2%)
- spLoadHumanResourcesObjects: 0.50 confidence, 0 dependencies

### 2. After Phase 1 (Expected)
- High confidence SPs: ~100/202 (50%)
- Low confidence SPs: ~102/202 (50%)
- spLoadHumanResourcesObjects: 0.85+ confidence, 20+ dependencies

### 3. Success Criteria
- ✅ At least +50 SPs improve to ≥0.85 confidence
- ✅ spLoadHumanResourcesObjects reaches ≥0.85
- ✅ No regressions (all 46 current high-conf SPs still ≥0.85)

---

## Test Execution

### Option A: CLI Full Parse (Recommended)
```bash
cd /home/chris/sandbox

# Clear existing workspace to force re-parse
rm -f data/lineage_workspace.duckdb

# Run full parse WITHOUT AI (test preprocessing only)
python lineage_v3/main.py run \
  --parquet parquet_snapshots/ \
  --full-refresh \
  --no-ai \
  --output lineage_output/

# Results will be in:
# - lineage_output/lineage_summary.json (statistics)
# - lineage_output/lineage.json (full results)
```

### Option B: API Upload (Alternative)
```bash
# Start API server
cd api && python3 main.py &

# Upload parquet files via API
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" \
  -F "files=@parquet_snapshots/objects.parquet" \
  -F "files=@parquet_snapshots/dependencies.parquet" \
  -F "files=@parquet_snapshots/definitions.parquet"

# Check results in:
# - data/latest_frontend_lineage.json
```

---

## Measurement Script

### Query to Count Improvement
```python
#!/usr/bin/env python3
"""Measure Phase 1 preprocessing improvement."""

import json
from pathlib import Path

# Load results
with open('lineage_output/lineage_summary.json', 'r') as f:
    summary = json.load(f)

# Load full lineage
with open('lineage_output/lineage.json', 'r') as f:
    lineage = json.load(f)

# Count by confidence
sps = [obj for obj in lineage if obj.get('object_type') == 'Stored Procedure']

high_conf = sum(1 for sp in sps if sp.get('provenance', {}).get('confidence', 0) >= 0.85)
medium_conf = sum(1 for sp in sps if 0.75 <= sp.get('provenance', {}).get('confidence', 0) < 0.85)
low_conf = sum(1 for sp in sps if sp.get('provenance', {}).get('confidence', 0) < 0.75)

print("="*80)
print("PHASE 1 TEST RESULTS")
print("="*80)
print(f"Total SPs: {len(sps)}")
print(f"High confidence (≥0.85): {high_conf} ({high_conf/len(sps)*100:.1f}%)")
print(f"Medium confidence (0.75-0.84): {medium_conf}")
print(f"Low confidence (<0.75): {low_conf}")
print()

# Baseline comparison
baseline_high = 46
improvement = high_conf - baseline_high
print(f"Baseline: {baseline_high} high confidence SPs")
print(f"After Phase 1: {high_conf} high confidence SPs")
print(f"Improvement: +{improvement} SPs ({improvement/baseline_high*100:+.1f}%)")
print()

# Check target
target = 100
if high_conf >= target:
    print(f"✅ SUCCESS! Reached target of {target} SPs (50%)")
else:
    shortfall = target - high_conf
    print(f"⚠️  Shortfall: {shortfall} SPs below target ({target - high_conf} needed)")

# Check spLoadHumanResourcesObjects specifically
sp_test = next((sp for sp in sps if sp.get('name') == 'spLoadHumanResourcesObjects'), None)
if sp_test:
    conf = sp_test.get('provenance', {}).get('confidence', 0)
    inputs = len(sp_test.get('inputs', []))
    outputs = len(sp_test.get('outputs', []))
    print()
    print(f"spLoadHumanResourcesObjects:")
    print(f"  Confidence: {conf:.2f}")
    print(f"  Inputs: {inputs}")
    print(f"  Outputs: {outputs}")
    if conf >= 0.85 and (inputs > 0 or outputs > 0):
        print(f"  ✅ SUCCESS! (was 0.50 with 0 deps)")
    else:
        print(f"  ❌ Still low confidence or no deps")
```

---

## What to Check

### 1. Summary Statistics
```bash
cat lineage_output/lineage_summary.json | python3 -c "
import json, sys
s = json.load(sys.stdin)
print(f\"High confidence: {s['confidence_statistics']['high_confidence_count']}\")
print(f\"Total objects: {s['total_objects']}\")
print(f\"Coverage: {s['coverage']}%\")
"
```

### 2. spLoadHumanResourcesObjects
```bash
cat lineage_output/lineage.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
sp = next((o for o in data if o['name'] == 'spLoadHumanResourcesObjects'), None)
if sp:
    print(f\"Confidence: {sp['provenance']['confidence']}\")
    print(f\"Inputs: {len(sp['inputs'])}\")
    print(f\"Outputs: {len(sp['outputs'])}\")
"
```

### 3. Check for Regressions
```bash
# Get list of current high-conf SPs
cat data/latest_frontend_lineage.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
high_conf_sps = [
    f\"{n['schema']}.{n['name']}\"
    for n in data
    if n.get('object_type') == 'Stored Procedure'
    and 'Confidence: 0.85' in n.get('description', '')
    or 'Confidence: 0.9' in n.get('description', '')
    or 'Confidence: 1.0' in n.get('description', '')
]
print('\\n'.join(sorted(high_conf_sps)))
" > baseline_high_conf_sps.txt

# Compare with new results
# (manually check that all 46 are still high confidence)
```

---

## Expected Timeline

1. **Setup:** 2 minutes
   - Clear workspace
   - Prepare test environment

2. **Parse:** 5-10 minutes
   - Full parse of 202 SPs
   - No AI calls (faster)

3. **Analysis:** 5 minutes
   - Run measurement script
   - Check specific SPs
   - Validate no regressions

**Total:** ~15-20 minutes

---

## Decision Tree

### If High Conf ≥ 100 SPs (50%)
✅ **Phase 1 SUCCESS!**
- Preprocessing achieved target
- Proceed to Phase 2 (AI simplification)
- Expected final: ~170 SPs (85%)

### If High Conf 75-99 SPs (37-49%)
⚠️ **Partial Success**
- Preprocessing helped (+29-53 SPs)
- Still need Phase 2
- Adjust Phase 2 target

### If High Conf < 75 SPs (<37%)
❌ **Phase 1 Failed**
- Preprocessing didn't help much
- Investigate why:
  - Check if patterns are being applied
  - Review cleaned DDL samples
  - May need different approach

---

## Files to Review After Test

1. **lineage_output/lineage_summary.json**
   - Overall statistics
   - Confidence distribution

2. **lineage_output/lineage.json**
   - Full SP details
   - Check improved SPs

3. **Logs (if any)**
   - Preprocessing messages
   - Parse errors
   - Confidence calculations

---

## Next Steps Based on Results

### Success Path (≥100 SPs)
1. Document Phase 1 results
2. Update specifications
3. Design Phase 2 (AI extract_lineage)
4. Implement Phase 2
5. Final test (target: 170 SPs)

### Partial Success Path (75-99 SPs)
1. Analyze why not 100
2. Identify remaining issues
3. Enhance preprocessing further OR
4. Proceed to Phase 2 with adjusted target

### Failure Path (<75 SPs)
1. Debug preprocessing
2. Check if patterns apply correctly
3. Review sample cleaned DDL
4. Consider alternative approach

---

**Ready to execute:** Run the CLI command above and report results!
