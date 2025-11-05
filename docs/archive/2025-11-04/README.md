# Archive: SP-to-SP Lineage Direction Fix (2025-11-04)

**Date:** November 4, 2025
**Version:** v4.0.3
**Status:** Completed

## Summary

This directory contains documentation from the SP-to-SP lineage direction fix. The parser was incorrectly treating stored procedure calls as inputs (incoming arrows) instead of outputs (outgoing arrows) in the visualization.

## Files Archived

### SP_DIRECTION_FIX_COMPLETE.md
Complete implementation report documenting root cause analysis, code changes, verification results, and GUI testing.

### verify_sp_direction_fix.md
Verification document with issue description, expected vs actual behavior, code changes needed, and impact assessment.

## The Problem

Before Fix: spLoadFactTables showed incoming arrows from the SPs it calls (wrong).
After Fix: spLoadFactTables shows outgoing arrows to the SPs it calls (correct).

## Root Causes

Bug 1: Parser added SP calls to input_ids instead of output_ids
Bug 2: Bidirectional graph reverse lookup was applied to Stored Procedures (should skip them)

## Impact

- Scope: All 151 SP-to-SP relationships
- Visual: Arrow direction in GUI now correct
- Semantic: Call hierarchy properly represented
- Confidence: No change (still 97.0% SP confidence)

## Current Status

All fixes deployed in v4.0.3. All 151 SP-to-SP relationships corrected.
