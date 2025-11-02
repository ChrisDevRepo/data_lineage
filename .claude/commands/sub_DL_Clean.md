---
description: Clean up old docs, archive outdated files, and update CLAUDE.md for Data Lineage
---

# Data Lineage - Clean Documentation

Archive outdated documentation files and update CLAUDE.md to reflect current project state.

## What This Does

Performs documentation housekeeping:
1. Identifies outdated or deprecated documentation files
2. Creates archive folder structure: `docs/archive/YYYY-MM-DD/`
3. Moves old documentation to archive
4. **Optimizes CLAUDE.md following Anthropic 2025 best practices:**
   - Removes references to archived files
   - Trims to 100-200 lines (max 300)
   - Converts paragraphs to bullet points
   - Removes verbose/redundant content
5. Updates documentation index/links
6. Generates summary of what was archived and why

## When to Use

Run this command when:
- 📚 Documentation has accumulated old/outdated files
- 🧹 Need to clean up before major version release
- 🗂️ Want to archive superseded documentation
- 🔄 After major feature changes that make old docs obsolete
- 📝 CLAUDE.md has references to non-existent or outdated files
- 🚨 **CLAUDE.md exceeds 300 lines** (MUST trim to 100-200 lines)
- 🎯 CLAUDE.md contains verbose paragraphs instead of bullet points
- 🔧 Need to optimize token usage (CLAUDE.md prepended to every prompt)

## Task Steps

### Step 1: Identify Outdated Documentation

Scan `/home/chris/sandbox/docs/` for files that may be outdated:

**Criteria for archival:**
- Files marked with "deprecated", "old", or "archive" in filename
- Files with "v1", "v2" version markers (if v3 is current)
- Files superseded by newer versions (check git log for replacements)
- Implementation specs for completed features
- Temporary testing/experimental docs
- Files not referenced in main README or CLAUDE.md

**Check these common patterns:**
- `*_OLD.md`
- `*_DEPRECATED.md`
- `*_v1.md`, `*_v2.md`
- `IMPLEMENTATION_SPEC_*.md` (if feature completed)
- `TEMP_*.md`
- `TEST_*.md` (if tests completed)

**Always preserve:**
- Current user guides (e.g., `PARSING_USER_GUIDE.md`)
- Active specifications (e.g., `AI_DISAMBIGUATION_SPEC.md`)
- Deployment guides (e.g., `AZURE_MANUAL_DEPLOYMENT.md`)
- Architecture docs (e.g., `DUCKDB_SCHEMA.md`)
- Evolution/changelog docs (e.g., `PARSER_EVOLUTION_LOG.md`)

### Step 2: Create Archive Structure

Create dated archive folder:
```bash
ARCHIVE_DATE=$(date +%Y-%m-%d)
ARCHIVE_DIR="/home/chris/sandbox/docs/archive/$ARCHIVE_DATE"
mkdir -p "$ARCHIVE_DIR"
```

### Step 3: Move Files to Archive

For each identified outdated file:
1. Move to archive: `mv docs/OLD_FILE.md docs/archive/$ARCHIVE_DATE/`
2. Create README in archive folder explaining what was archived and why
3. Log the move with git: `git add docs/archive/ && git rm docs/OLD_FILE.md`

**Example archive README:**
```markdown
# Documentation Archive - 2025-11-01

## Archived Files

### IMPLEMENTATION_SPEC_FINAL.md
- **Reason:** Feature fully implemented, superseded by user guides
- **Archived:** Implementation details for v3.0 parser
- **Replacement:** See docs/PARSING_USER_GUIDE.md

### OLD_DEPLOYMENT.md
- **Reason:** Deployment process changed
- **Replacement:** See docs/AZURE_MANUAL_DEPLOYMENT.md
```

### Step 4: Update CLAUDE.md (Following Best Practices)

**IMPORTANT:** CLAUDE.md should be **concise, lean, and relevant** (100-200 lines recommended).

**Best Practices from Anthropic (2025):**
- ✅ Keep it short - CLAUDE.md is prepended to EVERY prompt (uses token budget)
- ✅ Use bullet points, NOT paragraphs
- ✅ Only include rules Claude needs to perform the work
- ✅ Remove verbose explanations, redundancy, "nice-to-have" commentary
- ✅ Be declarative, not narrative
- ❌ Don't write it like onboarding docs for junior devs
- ❌ Avoid bloated, verbose content that creates noise

**Scan CLAUDE.md for issues:**

1. **Check length:** `wc -l CLAUDE.md` (target: 100-200 lines max)
2. **Check for archived file references:** `grep -n "\[.*\](docs/.*\.md)" CLAUDE.md`
3. **Identify bloat:**
   - Long narrative paragraphs (should be bullet points)
   - Redundant explanations
   - "Nice-to-have" details that aren't essential
   - Extensive copy-pasted documentation
   - Verbose instructions that could be 1-2 lines

**Update CLAUDE.md:**

1. **Remove archived file references:**
   - Find all links to archived files
   - Remove the link or section
   - Update to point to replacement documentation
   - Add brief note about archival if relevant

2. **Trim excessive content (if over 200 lines):**
   - Move detailed specs to separate docs (link instead of inline)
   - Convert paragraphs to concise bullet points
   - Remove redundant explanations
   - Keep only essential commands, structure, and rules
   - Delete "nice-to-have" commentary

3. **Update documentation sections:**
   - File structure diagram (if present)
   - "Essential Documentation" section
   - "Last Updated" date at bottom

**Example updates:**
```markdown
# Before (verbose paragraph)
When you need to understand the parsing system, you should first read the comprehensive
documentation which includes detailed explanations of how the parser works...

# After (concise bullet point)
- Parser docs: [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)

# Before (redundant)
- **Implementation Spec:** [docs/IMPLEMENTATION_SPEC_FINAL.md](docs/IMPLEMENTATION_SPEC_FINAL.md)

# After (removed - archived)
<!-- Removed: IMPLEMENTATION_SPEC_FINAL.md - archived 2025-11-01 -->

# After (replaced)
- **User Guide:** [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
```

**CRITICAL:** If CLAUDE.md is over 300 lines, it MUST be trimmed significantly.

### Step 5: Update Documentation Index

If `/home/chris/sandbox/README.md` has documentation links:
1. Remove references to archived files
2. Add links to new replacement docs
3. Update structure diagrams
4. Verify all links are valid

### Step 6: Verify All Links

Check that no broken links exist:
```bash
# Find all markdown links
grep -r "\[.*\](.*\.md)" docs/ README.md CLAUDE.md

# Verify each file exists
# Report any broken links
```

### Step 7: Generate Archive Report

Create summary document in archive folder:
```markdown
# Documentation Cleanup - 2025-11-01

## Summary
- Files archived: 3
- CLAUDE.md updated: Yes
- Broken links fixed: 2

## Archived Files
1. IMPLEMENTATION_SPEC_FINAL.md → Superseded by PARSING_USER_GUIDE.md
2. OLD_DEPLOYMENT.md → Superseded by AZURE_MANUAL_DEPLOYMENT.md
3. TEMP_TESTING_NOTES.md → Testing completed

## CLAUDE.md Changes
- Removed 3 references to archived files
- Added links to replacement documentation
- Updated "Last Updated" date

## Validation
- ✅ All documentation links verified
- ✅ No broken references
- ✅ Archive folder created with README
```

### Step 8: Git Commit

Create descriptive commit:
```bash
git add docs/archive/
git rm docs/[archived files]
git add CLAUDE.md README.md
git commit -m "docs: Archive outdated documentation - 2025-11-01

Archived files:
- IMPLEMENTATION_SPEC_FINAL.md (superseded by PARSING_USER_GUIDE.md)
- OLD_DEPLOYMENT.md (superseded by AZURE_MANUAL_DEPLOYMENT.md)

Updated CLAUDE.md to remove references to archived files.
All documentation links verified working."
```

## Success Criteria

✅ Archive folder created with date: `docs/archive/YYYY-MM-DD/`
✅ Outdated files moved to archive
✅ Archive README created explaining what was archived and why
✅ **CLAUDE.md updated - no references to archived files**
✅ **CLAUDE.md optimized - concise, lean, 100-200 lines (max 300)**
✅ **CLAUDE.md uses bullet points, not paragraphs**
✅ All documentation links verified working
✅ No broken links in README.md
✅ Git commit created documenting changes
✅ Summary report generated

## Files to Check

### Documentation Files (`/docs/`)
- `IMPLEMENTATION_SPEC_*.md` - Implementation specs for completed features
- `*_OLD.md`, `*_DEPRECATED.md` - Explicitly marked as old
- `TEMP_*.md` - Temporary documentation
- Version-specific: `*_v1.md`, `*_v2.md` (if v3 exists)
- Test/experimental docs that are no longer relevant

### Root Documentation
- `CLAUDE.md` - Main guidance file (update references)
- `README.md` - Project overview (update links)
- `DEPLOYMENT_QUICK_START.md` - Keep if current
- `*.md` - Check for outdated root-level docs

### Frontend Documentation (`/frontend/docs/`)
- Usually keep - but check for duplicates or outdated files

### Never Archive
- Active user guides
- Current specifications
- API documentation
- Schema references
- Architecture diagrams (unless superseded)
- Changelog files
- Testing guides (if tests still run)

## Error Handling

### No Outdated Files Found
- Report that documentation is already clean
- Suggest running git log to find recently modified files
- Ask user if they want to manually specify files to archive

### CLAUDE.md Update Conflicts
- If CLAUDE.md has uncommitted changes, warn user
- Suggest committing or stashing changes first
- Provide diff of proposed changes before applying

### Broken Link Detection
- List all broken links found
- Suggest replacements or removal
- Create issue/note for links that need manual review

### Git Errors
- If git operations fail, provide manual commands
- Suggest checking git status first
- Handle case where files are already in .gitignore

## Important Notes

- **Preservation:** Never delete files - always archive them
- **Traceability:** Archive folder includes README explaining what and why
- **Git History:** Archived files remain in git history
- **Reversible:** Files can be restored from archive if needed
- **Links:** Update CLAUDE.md and README.md to prevent broken links
- **Documentation:** Archive folder is self-documenting
- **CLAUDE.md Optimization:** Following Anthropic 2025 best practices:
  - CLAUDE.md is prepended to EVERY prompt (consumes token budget)
  - Target: 100-200 lines maximum (absolutely no more than 300)
  - Use bullet points, not paragraphs
  - Only include rules Claude needs to perform the work
  - Remove verbose explanations, redundancy, "nice-to-have" commentary
  - Be declarative, not narrative ("you're writing for Claude, not onboarding a junior dev")

## Archive Folder Structure

```
docs/archive/
├── 2025-11-01/
│   ├── README.md                      # What was archived and why
│   ├── IMPLEMENTATION_SPEC_FINAL.md   # Archived file
│   └── OLD_DEPLOYMENT.md              # Archived file
├── 2025-10-15/
│   └── ...
└── README.md                          # Archive index (if needed)
```

## Related Commands

- Manual archive: `mv docs/FILE.md docs/archive/$(date +%Y-%m-%d)/`
- Find old files: `find docs/ -name "*_OLD.md" -o -name "*_DEPRECATED.md"`
- Check links: `grep -r "\[.*\](.*\.md)" docs/ README.md CLAUDE.md`
- Git log for doc changes: `git log --oneline docs/`

## CLAUDE.md Health Check

**Before archiving, check CLAUDE.md quality:**

```bash
# Check length (target: 100-200, max: 300)
wc -l CLAUDE.md

# Find long paragraphs (lines over 100 chars)
awk 'length > 100' CLAUDE.md | head -n 10

# Find potential bloat patterns
grep -E "(should|you can|in order to|it is important)" CLAUDE.md
```

**Common CLAUDE.md Bloat Patterns to Fix:**

❌ **Verbose narrative:**
```markdown
When you need to work with the parser, you should first understand
how the system works by reading the comprehensive documentation...
```

✅ **Concise bullet point:**
```markdown
- Parser: [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
```

❌ **Redundant explanations:**
```markdown
The backend API is built with FastAPI. FastAPI is a modern, fast web
framework for Python. It uses Pydantic for data validation...
```

✅ **Essential info only:**
```markdown
- Backend: FastAPI + Pydantic
- Start: `cd api && python3 main.py`
```

❌ **Copy-pasted docs:**
```markdown
# Backend API

The API has the following endpoints:
- POST /api/upload-parquet - Uploads parquet files
  - Parameters: files (multipart/form-data), incremental (boolean)
  - Returns: {status: "success", message: "..."}
  - Description: This endpoint accepts parquet files...
```

✅ **Link to docs:**
```markdown
- API: [api/README.md](api/README.md) - 7 REST endpoints
```

**If CLAUDE.md > 300 lines:** MUST trim significantly before committing.

## Post-Cleanup Checklist

After running this command, verify:
- [ ] Archive folder created with current date
- [ ] All archived files have explanatory README
- [ ] CLAUDE.md has no references to archived files
- [ ] **CLAUDE.md length: 100-200 lines (max 300)**
- [ ] **CLAUDE.md uses bullet points (no long paragraphs)**
- [ ] **CLAUDE.md is lean and declarative**
- [ ] README.md links are all valid
- [ ] Documentation index updated (if exists)
- [ ] Git commit created
- [ ] No broken links in documentation
- [ ] Key documentation still accessible
