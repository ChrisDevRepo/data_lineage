#!/bin/bash
# Test AI inference with current prompt configuration

set -e

echo "=========================================="
echo "AI Inference Test"
echo "=========================================="
echo "Timestamp: $(date)"
echo ""

# Generate log filename
LOGFILE="../AI_Optimization/results/test_$(date +%Y%m%d_%H%M%S).log"

# Navigate to lineage_v3
cd /home/chris/sandbox/lineage_v3

# Delete old DuckDB for clean test
if [ -f "lineage_workspace.duckdb" ]; then
    echo "Deleting old DuckDB workspace..."
    rm -f lineage_workspace.duckdb
fi

echo "Running full-refresh test..."
echo "Log file: $LOGFILE"
echo ""

# Run test
../venv/bin/python3 main.py run --parquet ../parquet_snapshots/ --full-refresh 2>&1 | tee "$LOGFILE"

echo ""
echo "=========================================="
echo "Test complete!"
echo "Log saved to: $LOGFILE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Validate results: python ../AI_Optimization/scripts/validate_results.py"
echo "  2. View matches: python ../AI_Optimization/scripts/show_matches.py"
echo ""
