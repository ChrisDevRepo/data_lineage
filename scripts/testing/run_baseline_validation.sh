#!/bin/bash
# ==============================================================================
# Baseline Validation Script
# ==============================================================================
# Purpose: Automated regression detection for parser changes
# Usage: ./scripts/testing/run_baseline_validation.sh [before|after|diff]
#
# Workflow:
#   1. Before changes: ./run_baseline_validation.sh before
#   2. Make your parser changes
#   3. After changes: ./run_baseline_validation.sh after
#   4. Review diff: ./run_baseline_validation.sh diff
#
# Integration: Pre-commit hook automatically runs 'diff' mode
# ==============================================================================

set -e  # Exit on error

BASELINE_DIR="tests/baselines"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VALIDATION_SCRIPT="scripts/testing/check_parsing_results.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure baseline directory exists
mkdir -p "$BASELINE_DIR"

# ==============================================================================
# Functions
# ==============================================================================

capture_baseline() {
    local output_file=$1
    echo -e "${BLUE}📊 Capturing parser baseline...${NC}"

    if [ ! -f "$VALIDATION_SCRIPT" ]; then
        echo -e "${RED}❌ Error: $VALIDATION_SCRIPT not found${NC}"
        exit 1
    fi

    python3 "$VALIDATION_SCRIPT" > "$output_file" 2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Baseline captured: $(basename $output_file)${NC}"

        # Show summary
        local success_count=$(grep -oP '\d+/\d+ SPs' "$output_file" | head -1 || echo "N/A")
        local conf_100=$(grep -oP '\d+ SPs.*100%' "$output_file" | grep -oP '^\d+' || echo "0")
        local conf_85=$(grep -oP '\d+ SPs.*85%' "$output_file" | grep -oP '^\d+' || echo "0")
        local conf_75=$(grep -oP '\d+ SPs.*75%' "$output_file" | grep -oP '^\d+' || echo "0")

        echo -e "${BLUE}Summary:${NC}"
        echo -e "  Success: $success_count"
        echo -e "  Perfect (100%): ${conf_100}"
        echo -e "  Good (85%): ${conf_85}"
        echo -e "  Acceptable (75%): ${conf_75}"
    else
        echo -e "${RED}❌ Error capturing baseline${NC}"
        exit 1
    fi
}

compare_baselines() {
    local before_file=$1
    local after_file=$2

    echo -e "${BLUE}📊 Comparing baselines...${NC}"
    echo ""

    # Extract key metrics
    local before_success=$(grep -oP '\d+(?=/\d+ SPs)' "$before_file" | head -1)
    local after_success=$(grep -oP '\d+(?=/\d+ SPs)' "$after_file" | head -1)

    local before_100=$(grep -oP '\d+(?= SPs.*100%)' "$before_file" | head -1 || echo "0")
    local after_100=$(grep -oP '\d+(?= SPs.*100%)' "$after_file" | head -1 || echo "0")

    local before_85=$(grep -oP '\d+(?= SPs.*85%)' "$before_file" | head -1 || echo "0")
    local after_85=$(grep -oP '\d+(?= SPs.*85%)' "$after_file" | head -1 || echo "0")

    # Show comparison
    echo -e "${BLUE}=== Baseline Comparison ===${NC}"
    echo ""
    echo -e "  ${BLUE}Success Rate:${NC}"
    echo -e "    Before: ${before_success} SPs"
    echo -e "    After:  ${after_success} SPs"

    if [ "$after_success" -lt "$before_success" ]; then
        echo -e "    ${RED}▼ REGRESSION: -$((before_success - after_success)) SPs${NC}"
    elif [ "$after_success" -gt "$before_success" ]; then
        echo -e "    ${GREEN}▲ IMPROVEMENT: +$((after_success - before_success)) SPs${NC}"
    else
        echo -e "    ${GREEN}✓ No change${NC}"
    fi

    echo ""
    echo -e "  ${BLUE}Perfect (100%):${NC}"
    echo -e "    Before: ${before_100}"
    echo -e "    After:  ${after_100}"
    [ "$after_100" -lt "$before_100" ] && echo -e "    ${RED}▼ -$((before_100 - after_100))${NC}" || echo -e "    ${GREEN}▲ +$((after_100 - before_100))${NC}"

    echo ""
    echo -e "  ${BLUE}Good (85%):${NC}"
    echo -e "    Before: ${before_85}"
    echo -e "    After:  ${after_85}"

    echo ""
    echo -e "${BLUE}=== Detailed Diff ===${NC}"
    diff "$before_file" "$after_file" || true

    echo ""

    # Check for regression
    if [ "$after_success" -lt "$before_success" ]; then
        echo -e "${RED}❌ REGRESSION DETECTED${NC}"
        echo -e "   Success rate decreased: ${before_success} → ${after_success}"
        echo -e "   Review changes carefully!"
        return 1
    elif [ "$after_success" -gt "$before_success" ]; then
        echo -e "${GREEN}✅ IMPROVEMENT DETECTED${NC}"
        echo -e "   Success rate increased: ${before_success} → ${after_success}"
        return 0
    else
        echo -e "${GREEN}✅ No regression - success rate maintained${NC}"
        return 0
    fi
}

# ==============================================================================
# Main Script
# ==============================================================================

case "$1" in
    before)
        # Capture baseline BEFORE making changes
        OUTPUT_FILE="$BASELINE_DIR/baseline_before_$TIMESTAMP.txt"
        capture_baseline "$OUTPUT_FILE"

        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo -e "  1. Make your parser changes"
        echo -e "  2. Run: $0 after"
        echo -e "  3. Review: $0 diff"
        ;;

    after)
        # Capture baseline AFTER making changes
        OUTPUT_FILE="$BASELINE_DIR/baseline_after_$TIMESTAMP.txt"
        capture_baseline "$OUTPUT_FILE"

        # Auto-compare with latest 'before' baseline
        LATEST_BEFORE=$(ls -t "$BASELINE_DIR"/baseline_before_*.txt 2>/dev/null | head -1)

        if [ -f "$LATEST_BEFORE" ]; then
            echo ""
            echo -e "${BLUE}Auto-comparing with latest 'before' baseline...${NC}"
            echo -e "${BLUE}Before: $(basename $LATEST_BEFORE)${NC}"
            echo -e "${BLUE}After:  $(basename $OUTPUT_FILE)${NC}"
            echo ""

            compare_baselines "$LATEST_BEFORE" "$OUTPUT_FILE"
            exit_code=$?

            if [ $exit_code -ne 0 ]; then
                echo ""
                echo -e "${YELLOW}⚠️  To proceed with regression:${NC}"
                echo -e "   1. Ensure regression is intentional"
                echo -e "   2. Update user-verified cases if needed"
                echo -e "   3. Document reason in commit message"
                exit 1
            fi
        else
            echo ""
            echo -e "${YELLOW}⚠️  No 'before' baseline found to compare${NC}"
            echo -e "   Run '$0 before' first, then make changes"
        fi
        ;;

    diff)
        # Compare latest before/after baselines
        LATEST_BEFORE=$(ls -t "$BASELINE_DIR"/baseline_before_*.txt 2>/dev/null | head -1)
        LATEST_AFTER=$(ls -t "$BASELINE_DIR"/baseline_after_*.txt 2>/dev/null | head -1)

        if [ ! -f "$LATEST_BEFORE" ]; then
            echo -e "${RED}❌ No 'before' baseline found${NC}"
            echo -e "   Run: $0 before"
            exit 1
        fi

        if [ ! -f "$LATEST_AFTER" ]; then
            echo -e "${RED}❌ No 'after' baseline found${NC}"
            echo -e "   Run: $0 after"
            exit 1
        fi

        echo -e "${BLUE}Comparing:${NC}"
        echo -e "  Before: $(basename $LATEST_BEFORE)"
        echo -e "  After:  $(basename $LATEST_AFTER)"
        echo ""

        compare_baselines "$LATEST_BEFORE" "$LATEST_AFTER"
        ;;

    clean)
        # Clean old baselines (keep last 10 of each type)
        echo -e "${BLUE}🧹 Cleaning old baselines...${NC}"

        # Keep last 10 'before' baselines
        ls -t "$BASELINE_DIR"/baseline_before_*.txt 2>/dev/null | tail -n +11 | xargs -r rm -v

        # Keep last 10 'after' baselines
        ls -t "$BASELINE_DIR"/baseline_after_*.txt 2>/dev/null | tail -n +11 | xargs -r rm -v

        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;

    *)
        echo "Usage: $0 {before|after|diff|clean}"
        echo ""
        echo "Commands:"
        echo "  before  - Capture baseline BEFORE making parser changes"
        echo "  after   - Capture baseline AFTER making parser changes (auto-compares)"
        echo "  diff    - Compare latest before/after baselines"
        echo "  clean   - Remove old baselines (keeps last 10 of each type)"
        echo ""
        echo "Typical workflow:"
        echo "  1. ./run_baseline_validation.sh before"
        echo "  2. Make your parser changes"
        echo "  3. ./run_baseline_validation.sh after"
        echo ""
        echo "Integration:"
        echo "  - Pre-commit hook runs 'diff' automatically"
        echo "  - CI/CD compares PR branch with main branch"
        exit 1
        ;;
esac
