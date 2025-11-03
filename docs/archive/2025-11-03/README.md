# Documentation Archive - 2025-11-03

## Archived Files

This archive contains documentation that has become outdated or superseded by newer implementation plans.

### Files Archived

1. **OPEN_ACTION_ITEMS.md** (7.5 KB)
   - Point-in-time task list for v4.0.0 slim parser development
   - Status snapshot from post-baseline creation
   - Reason: Task lists become stale quickly; active tasks tracked in git issues

2. **PARSER_ISSUE_DECLARE_PATTERN.md** (21 KB)
   - Detailed analysis of DECLARE pattern bug affecting 10-20 SPs
   - Root cause analysis and proposed solutions
   - Reason: Issue FIXED in v4.0.1 - archived after successful implementation

3. **V4_SLIM_PARSER_BASELINE.md** (5.5 KB)
   - Baseline evaluation results for v4.0.0 slim parser
   - Initial metrics: 58.94% regex confidence, 46.01% SQLGlot confidence
   - Reason: Baseline snapshot; superseded by evaluation reports in `optimization_reports/`

4. **V4_0_2_RELEASE_NOTES.md** (10 KB) - *ADDED 2025-11-03 18:30*
   - Release notes for v4.0.2 (Orchestrator SP confidence fix)
   - Achievement: 97.0% of SPs at high confidence (196/202)
   - Reason: Release completed and in production; documented in PARSER_EVOLUTION_LOG.md

5. **UNRELATED_OBJECTS_ANALYSIS.md** (8.7 KB) - *ADDED 2025-11-03 18:30*
   - One-time analysis of objects with no inputs/outputs
   - Result: Only 1 object found (data quality issue, not parser bug)
   - Reason: Analysis completed; no further action required

## Context

These documents were created during the v4.0.0 slim parser development phase. They represent:
- Initial baseline evaluation (Nov 3, 2025)
- Known issues identified during baseline creation
- Prioritized action items for parser improvement

## Active Documentation

For current documentation, see:
- [docs/PARSER_EVOLUTION_LOG.md](../../PARSER_EVOLUTION_LOG.md) - Version history and changes
- [docs/PARSING_USER_GUIDE.md](../../PARSING_USER_GUIDE.md) - SQL parsing guide
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](../../SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Evaluation spec
- [evaluation_baselines/](../../../evaluation_baselines/) - Baseline lifecycle management
- [optimization_reports/](../../../optimization_reports/) - Evaluation results

---

**Archived by:** Claude Code (sub_DL_Clean)
**Archive date:** 2025-11-03
**Branch:** feature/slim-parser-no-ai
