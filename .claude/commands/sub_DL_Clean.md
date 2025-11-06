---
description: Clean up old docs, archive outdated files, and optimize CLAUDE.md
---

**Your task:** Archive outdated documentation and optimize CLAUDE.md following Anthropic 2025 best practices.

1. Identify outdated documentation files:
   ```bash
   cd /home/chris/sandbox
   find docs/ -name "*_OLD.md" -o -name "*_DEPRECATED.md" -o -name "*_v1.md" -o -name "*_v2.md"
   ```
   - Look for: deprecated files, old versions, completed implementation specs
   - Preserve: current user guides, active specs, deployment docs

2. Create archive structure:
   ```bash
   ARCHIVE_DATE=$(date +%Y-%m-%d)
   mkdir -p docs/archive/$ARCHIVE_DATE
   ```

3. For each outdated file:
   - Move to archive: `mv docs/OLD_FILE.md docs/archive/$ARCHIVE_DATE/`
   - Create README in archive explaining what was archived and why

4. Optimize CLAUDE.md (CRITICAL):
   - Check length: `wc -l CLAUDE.md` (target: 100-200 lines, max: 300)
   - Remove archived file references
   - Convert paragraphs to bullet points
   - Remove verbose/redundant content
   - Keep only essential commands, structure, and rules

5. Verify all documentation links work:
   ```bash
   grep -r "\[.*\](.*\.md)" docs/ README.md CLAUDE.md
   ```

6. Create git commit:
   ```bash
   git add docs/archive/
   git rm docs/[archived files]
   git add CLAUDE.md README.md
   git commit -m "docs: Archive outdated documentation - $ARCHIVE_DATE"
   ```

7. Report:
   - Files archived (with reasons)
   - CLAUDE.md changes (length before/after)
   - Broken links fixed
   - Git commit hash

**CLAUDE.md optimization rules:**
- Target: 100-200 lines (absolutely max 300)
- Use bullet points, NOT paragraphs
- Remove verbose explanations and redundancy
- Be declarative, not narrative
