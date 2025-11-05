# Archive - 2025-11-05

## Contents

This archive contains legacy code and experiments that were removed during the v4.0.3 codebase cleanup.

### AI_Optimization/

**Archived:** 2025-11-05
**Reason:** AI features removed in v4.0.0

This directory contained experimental AI-based disambiguation code that was part of the v3.x parser. The AI approach was replaced with a more reliable Regex + SQLGlot + Rule Engine strategy in v4.0.0.

**Historical Context:**
- v3.7.0 introduced AI-assisted disambiguation using Azure OpenAI
- Goal was to improve confidence scores for complex stored procedures
- Results showed mixed performance and added operational complexity
- v4.0.0 removed AI features in favor of deterministic parsing

**Contents:**
- AI prompt engineering experiments
- Iteration logs and results
- Few-shot learning research
- AI inference scripts
- Validation failure reports

**Reference:**
- See CODEBASE_REVIEW_REPORT.md (2025-11-05) for full cleanup details
- See PARSER_EVOLUTION_LOG.md for v4.0.0 changes

---

This archive is preserved for historical reference only. The code is not maintained and should not be used in production.
