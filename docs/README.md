# Documentation Directory

## 🚨 CRITICAL FILES - HANDLE WITH CARE

The following files are **mission-critical** and require special attention:

**Policy:**
- ✅ **CAN MODIFY:** Add new sections, update content, fix errors
- ✅ **SHOULD ADD TO:** Especially the journal - document all changes!
- ❌ **DO NOT DELETE:** Never delete these files
- ❌ **DO NOT RESTRUCTURE:** Don't change overall structure without approval

**These files are living documents - they SHOULD be updated regularly!**

### 1. 📘 PARSER_DEVELOPMENT_PROCESS.md ⭐
**Purpose:** Complete end-to-end workflow for parser development
**Contains:**
- Parse → Test → Analyze → Fix → Document cycle
- Testing protocol and quality gates
- Issue resolution process
- Troubleshooting guide

**Why Critical:** This is THE main guide for all parser development work. Without it, developers won't know the correct process.

---

### 2. 📕 PARSER_CHANGE_JOURNAL.md ⭐
**Purpose:** History of all parser changes and investigations
**Contains:**
- Past bug fixes and root causes
- What NOT to change (regression prevention)
- Lessons learned
- Investigation findings

**Why Critical:** Prevents repeating past mistakes. Contains institutional knowledge about what works and what doesn't.

**⚠️ MANDATORY:** Check this file BEFORE making any parser changes!

---

### 3. 📙 PARSER_CRITICAL_REFERENCE.md ⭐
**Purpose:** Critical warnings and things NOT to change
**Contains:**
- WARN mode regression warnings
- What NOT to change in parser
- Testing protocol to prevent regressions

**Why Critical:** Documents known failure modes and how to avoid them. Read BEFORE touching parser code.

---

### 4. 📗 PARSER_TECHNICAL_GUIDE.md ⭐
**Purpose:** Complete technical architecture documentation
**Contains:**
- How parser works internally
- Regex-first baseline + SQLGlot enhancement
- Confidence model
- Architecture diagrams

**Why Critical:** Technical reference for understanding how parser works. Essential for debugging and enhancements.

---

## When to Modify These Files

### ALWAYS Update These When:

**PARSER_CHANGE_JOURNAL.md:**
- ✅ After fixing any parser bug
- ✅ After identifying root causes
- ✅ After significant investigations
- ✅ After making rule engine changes
- ✅ When discovering "what NOT to change"

**PARSER_DEVELOPMENT_PROCESS.md:**
- ✅ When adding new steps to workflow
- ✅ When discovering new troubleshooting solutions
- ✅ When updating quality gates
- ✅ When adding new validation scripts

**PARSER_CRITICAL_REFERENCE.md:**
- ✅ When discovering new failure modes
- ✅ When adding critical warnings
- ✅ When documenting regression patterns

**PARSER_TECHNICAL_GUIDE.md:**
- ✅ When architecture changes
- ✅ When adding new features
- ✅ When updating confidence model

### NEVER Do These:

- ❌ Delete any of these files
- ❌ Remove existing sections without user approval
- ❌ Restructure without user approval
- ❌ Change file names without updating all references

---

## Protection Mechanisms

### 1. Documentation + Policy
This README and `.claudeignore` document the importance and modification policy.

### 2. Git History
All critical files are tracked in git. If accidentally modified:
```bash
# Restore from git
git checkout docs/PARSER_DEVELOPMENT_PROCESS.md
git checkout docs/PARSER_CHANGE_JOURNAL.md
git checkout docs/PARSER_CRITICAL_REFERENCE.md
git checkout docs/PARSER_TECHNICAL_GUIDE.md
```

### 3. This README
Serves as a warning and explanation of file importance.

### 4. Backup Recommendation
Create periodic backups of these files:
```bash
# Create backup directory
mkdir -p docs/backups/$(date +%Y-%m-%d)

# Backup critical files
cp docs/PARSER_*.md docs/backups/$(date +%Y-%m-%d)/
```

---

## Other Important Files

### Investigation Documents
- `INVESTIGATION_COMPLETE.md` (project root)
- `EMPTY_LINEAGE_ROOT_CAUSE.md` (project root)
- `REPARSE_ITERATION_SUMMARY.md` (project root)

These document specific investigations and should be preserved for historical reference.

### Configuration Guides
- `CONFIGURATION_VERIFICATION_REPORT.md` - Multi-database config
- `PYTHON_RULES.md` - SQL cleaning rules documentation
- `GRAPHOLOGY_BFS_ANALYSIS.md` - Frontend graph library decisions

---

## Archived Reports

The following reports have been moved to the archive for historical reference:

1. **DATABASE_SUPPORT_ASSESSMENT.md**
   - Provides historical context for database support decisions.
   - Key insights have been integrated into the main documentation.

2. **PHANTOM_FUNCTION_FILTER_BUG.md**
   - Highlights a resolved bug related to phantom function schema filtering.
   - Key lessons have been incorporated into the main documentation.

---

## File Hierarchy

```
docs/
├── README.md ⭐ (This file - explains protection)
├── PARSER_DEVELOPMENT_PROCESS.md ⭐ (Main workflow guide)
├── PARSER_CHANGE_JOURNAL.md ⭐ (Change history)
├── PARSER_CRITICAL_REFERENCE.md ⭐ (Critical warnings)
├── PARSER_TECHNICAL_GUIDE.md ⭐ (Technical architecture)
├── PARSER_V4.3.3_SUMMARY.md (Version summary)
├── reports/ (Generated reports)
└── archived/ (Old documents)
```

---

## Modification Protocol

### To Modify Critical Files:

1. **Check with user first** - Get explicit approval
2. **Create backup** - Before making changes
3. **Document reason** - Why change is needed
4. **Review impact** - Check references to file
5. **Update changelog** - Document what changed

### To Add New Content:

- **DO:** Add new sections to existing files
- **DO:** Create new files for new topics
- **DON'T:** Delete or significantly restructure critical files
- **DON'T:** Remove existing sections without user approval

---

## Recovery Procedures

### If Critical File Deleted:

```bash
# 1. Check git history
git log --all --full-history -- docs/PARSER_DEVELOPMENT_PROCESS.md

# 2. Restore from git
git checkout <commit-hash> -- docs/PARSER_DEVELOPMENT_PROCESS.md

# 3. If not in git, restore from backup
cp docs/backups/YYYY-MM-DD/PARSER_DEVELOPMENT_PROCESS.md docs/
```

### If Critical File Corrupted:

```bash
# 1. Check git diff
git diff docs/PARSER_DEVELOPMENT_PROCESS.md

# 2. Restore if needed
git checkout docs/PARSER_DEVELOPMENT_PROCESS.md
```

---

## Best Practices

### For Claude Code:
1. ✅ **READ** these files frequently (for context)
2. ✅ **REFERENCE** them in responses
3. ✅ **ADD** new sections with user approval
4. ❌ **DON'T DELETE** critical files
5. ❌ **DON'T RESTRUCTURE** without approval

### For Developers:
1. ✅ **Read** before making parser changes
2. ✅ **Update** PARSER_CHANGE_JOURNAL.md after fixes
3. ✅ **Follow** PARSER_DEVELOPMENT_PROCESS.md workflow
4. ✅ **Backup** before major changes
5. ❌ **Don't skip** documentation steps

---

## Version Control

**Last Updated:** 2025-11-14
**Protected Files:** 4 critical + 3 investigation documents
**Protection Method:** .claudeignore + git + README

**Change Log:**
- 2025-11-14: Created README and .claudeignore for file protection
- 2025-11-14: Documented all 4 critical parser files
- 2025-11-14: Updated the documentation index to reflect the movement of `DATABASE_SUPPORT_ASSESSMENT.md` and `PHANTOM_FUNCTION_FILTER_BUG.md` to the archive directory
