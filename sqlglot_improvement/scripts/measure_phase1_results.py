#!/usr/bin/env python3
"""Measure Phase 1 preprocessing improvement."""

import json
from pathlib import Path
import sys

# Load results
summary_file = Path('lineage_output/lineage_summary.json')
lineage_file = Path('lineage_output/lineage.json')

if not summary_file.exists():
    print("❌ lineage_summary.json not found. Run parse first!")
    sys.exit(1)

with open(summary_file, 'r') as f:
    summary = json.load(f)

with open(lineage_file, 'r') as f:
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
print(f"Baseline: {baseline_high} high confidence SPs (22.8%)")
print(f"After Phase 1: {high_conf} high confidence SPs ({high_conf/len(sps)*100:.1f}%)")
print(f"Improvement: {improvement:+d} SPs ({improvement/baseline_high*100:+.1f}%)")
print()

# Check target
target = 100
if high_conf >= target:
    print(f"✅ SUCCESS! Reached target of {target} SPs (50%)")
elif high_conf >= 75:
    print(f"⚠️  Partial success: {high_conf}/{target} SPs ({high_conf/target*100:.1f}%)")
    print(f"   Shortfall: {target - high_conf} SPs")
else:
    print(f"❌ Below target: {high_conf}/{target} SPs ({high_conf/target*100:.1f}%)")
    print(f"   Shortfall: {target - high_conf} SPs")

# Check spLoadHumanResourcesObjects specifically
print()
print("="*80)
print("TEST CASE: spLoadHumanResourcesObjects")
print("="*80)
sp_test = next((sp for sp in sps if sp.get('name') == 'spLoadHumanResourcesObjects'), None)
if sp_test:
    conf = sp_test.get('provenance', {}).get('confidence', 0)
    inputs = len(sp_test.get('inputs', []))
    outputs = len(sp_test.get('outputs', []))
    print(f"Confidence: {conf:.2f} (was 0.50)")
    print(f"Inputs: {inputs} (was 0)")
    print(f"Outputs: {outputs} (was 0)")
    
    if conf >= 0.85 and (inputs > 0 or outputs > 0):
        print(f"\n✅ SUCCESS! SP now has dependencies and high confidence")
    elif conf > 0.50:
        print(f"\n⚠️  Partial improvement (confidence increased but still <0.85)")
    else:
        print(f"\n❌ No improvement (still 0.50 confidence)")
else:
    print("❌ SP not found in results")

print()
print("="*80)
print("NEXT STEPS")
print("="*80)

if high_conf >= target:
    print("✅ Phase 1 achieved target! Ready for Phase 2 (AI simplification)")
    print("   Expected final: ~170 SPs (85%) after Phase 2")
elif high_conf >= 75:
    print("⚠️  Phase 1 partially successful. Consider:")
    print("   1. Analyze remaining low-confidence SPs")
    print("   2. Enhance preprocessing further, OR")
    print("   3. Proceed to Phase 2 with adjusted target")
else:
    print("❌ Phase 1 did not meet target. Investigate:")
    print("   1. Check if preprocessing patterns are being applied")
    print("   2. Review cleaned DDL samples")
    print("   3. Debug preprocessing logic")
