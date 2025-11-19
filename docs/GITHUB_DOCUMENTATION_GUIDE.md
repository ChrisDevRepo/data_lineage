# GitHub Documentation Optimization Guide

**Created:** 2025-11-19
**Version:** v0.10.0

## Summary of Optimizations

This document describes the GitHub documentation structure optimized for power users, DBAs, and developers.

---

## Documentation Structure

### Primary Files (Root Level)

| File | Purpose | Audience |
|------|---------|----------|
| **README.md** | Scannable landing page with badges, features, quick start | All users (GitHub visitors) |
| **QUICKSTART.md** | 5-10 minute setup guide with examples | Power Users & DBAs |
| **LICENSE** | MIT license (open source) | Legal / Contributors |
| **CLAUDE.md** | Complete technical reference for development | Developers (AI assistant) |

### Documentation Directory (docs/)

| File | Purpose | Audience |
|------|---------|----------|
| **ARCHITECTURE.md** | System flow, parser details, data pipeline | Technical readers |
| **SETUP.md** | Detailed installation and deployment | Operations / DevOps |
| **USAGE.md** | How to use the application | End users |
| **DATABASE_CONNECTOR_SPECIFICATION.md** | DBA guide for direct database connection | DBAs |
| **PARSER_TECHNICAL_GUIDE.md** | Parser internals and YAML rules | Developers / Power Users |

---

## Key Optimizations

### 1. README.md - GitHub Best Practices

**Before:**
- Dense text with excessive documentation links
- No badges or visual hierarchy
- Features buried in prose
- No clear audience segmentation

**After:**
- ✅ Badges at top (License, Python, Node, Version)
- ✅ Centered hero section with screenshot
- ✅ "Why This Tool?" section (bullet points)
- ✅ Features in scannable tables
- ✅ Mermaid architecture diagram
- ✅ Clear sections with visual hierarchy
- ✅ Links to detailed docs (not inline)
- ✅ Performance metrics table
- ✅ Call-to-action footer

**Result:** Scannable in 30 seconds, clear value proposition

### 2. QUICKSTART.md - Power User Focus

**Content:**
- One-command installation
- 3 data source options (Parquet, Database, JSON)
- Configuration matrix with examples
- YAML rules quick reference
- Developer Mode access instructions
- Security best practices
- Connection string examples for 6 databases
- Troubleshooting table

**Target Audience:** Power users and DBAs who want to deploy quickly

### 3. docs/ARCHITECTURE.md - Technical Deep Dive

**New File - Comprehensive system documentation:**

**Content:**
- Mermaid system flow diagram
- Data flow with pipeline stages
- Parser architecture explanation
- YAML rule engine details
- Frontend performance optimizations
- Database connector incremental refresh
- Security best practices
- Testing strategy
- Monitoring & observability

**Target Audience:** Developers, architects, technical decision-makers

### 4. JSON Output Documentation

**Clarified Data Flow:**
- **Inputs:** Parquet files OR Database connection
- **Processing:** YAML rules → Hybrid parser (Regex + SQLGlot)
- **Output:** JSON format (`data/latest_frontend_lineage.json`)

**Added to QUICKSTART.md:**
- Download command: `curl http://localhost:8000/api/latest-data > lineage.json`
- JSON format specification
- Use cases (backup, sharing, version control)

**No JSON Import:** JSON is output-only format for frontend visualization

---

## Screenshot Strategy

### Automated Screenshot Tool

**Location:** `scripts/take-screenshots.mjs`

**Features:**
- Optimal dimensions: 1280x800 @ 2x DPI (Retina)
- Automated capture via Playwright
- 6-7 strategic screenshots

**Screenshots to Capture:**

| Screenshot | Description | Use Case |
|------------|-------------|----------|
| `01-main-graph.png` | Interactive graph view with nodes | README hero image |
| `02-trace-mode.png` | Context menu showing trace options | Feature showcase |
| `03-sql-viewer.png` | Monaco Editor with SQL highlighting | Technical documentation |
| `04-filters.png` | Filter panel with schema selection | Feature showcase |
| `05-developer-mode.png` | Developer panel with logs | Power user guide |
| `06-yaml-rules.png` | YAML rules browser | Rule engine documentation |
| `07-import-modal.png` | Import options (Parquet/DB) | Quick start guide |

### Taking Screenshots

**Prerequisites:**
1. Application must be running with sample data loaded
2. Playwright must be installed in frontend

**Steps:**
```bash
# 1. Start the application
./start-app.sh

# 2. Wait for both services to be ready
# Backend: http://localhost:8000
# Frontend: http://localhost:3000

# 3. Upload sample data or use existing data

# 4. Run screenshot script
cd /home/chris/data_lineage
node scripts/take-screenshots.mjs

# 5. Check output
ls -lh docs/screenshots/
```

**Output:** High-quality PNG files optimized for GitHub documentation

---

## Documentation Hierarchy

### Landing Page (README.md)
```
README.md (Scannable, visual, concise)
    ├─ Why this tool? (Bullet points)
    ├─ Quick Start (One command)
    ├─ Features (Tables)
    ├─ Architecture (Mermaid diagram)
    ├─ Documentation (Links by audience)
    ├─ Tech Stack (Overview)
    ├─ Configuration (Key options)
    ├─ Deployment (Quick examples)
    ├─ Testing (Commands)
    └─ Performance (Metrics table)
```

### Detail Pages (Linked from README)
```
QUICKSTART.md (Power Users & DBAs)
    ├─ Installation (One command)
    ├─ Configuration (All options)
    ├─ Data Sources (3 options)
    ├─ Power User Features (YAML, Dev Mode)
    ├─ Testing & Validation
    └─ Deployment

docs/ARCHITECTURE.md (Technical Deep Dive)
    ├─ System Flow (Mermaid)
    ├─ Data Pipeline (5 stages)
    ├─ Parser Architecture
    ├─ YAML Rule Engine
    ├─ Frontend Optimizations
    ├─ Database Connector
    ├─ Security
    └─ Performance Metrics

docs/DATABASE_CONNECTOR_SPECIFICATION.md (DBAs)
    ├─ Metadata Contract
    ├─ YAML Query Configuration
    ├─ Connection Examples (6 databases)
    ├─ Incremental Refresh
    ├─ Security Best Practices
    └─ Connector Implementation Guide
```

---

## Writing Style Guide

### General Principles

1. **Scannable First**
   - Use tables instead of prose
   - Bullet points over paragraphs
   - Code blocks with syntax highlighting

2. **Visual Hierarchy**
   - H2 for major sections
   - H3 for subsections
   - Tables for comparisons/options
   - Code blocks for commands

3. **Concise but Complete**
   - README: Overview only, link to details
   - Detail pages: Complete but organized
   - No duplication across files

4. **Audience-Specific**
   - End Users: Simple, visual
   - Power Users: Configuration, customization
   - DBAs: Connection, security, metadata
   - Developers: Architecture, testing, CI/CD

### Example Patterns

**Good (Table):**
```markdown
| Feature | Description |
|---------|-------------|
| **Trace Mode** | Analyze dependencies |
```

**Avoid (Prose):**
```markdown
The trace mode feature allows you to analyze dependencies
by exploring upstream and downstream relationships...
```

**Good (Command):**
```bash
./start-app.sh  # One command
```

**Avoid (Verbose):**
```markdown
To start the application, you need to run the start-app.sh
script which will automatically detect your virtual environment...
```

---

## Maintenance

### When to Update

| Change | Files to Update |
|--------|-----------------|
| New feature | README.md (table), ARCHITECTURE.md, QUICKSTART.md |
| New config option | QUICKSTART.md, .env.example |
| New database support | DATABASE_CONNECTOR_SPECIFICATION.md, QUICKSTART.md |
| Parser changes | ARCHITECTURE.md, PARSER_TECHNICAL_GUIDE.md |
| Performance improvements | README.md (metrics), ARCHITECTURE.md |

### Version Updates

When releasing a new version:
1. Update version badge in README.md
2. Update version in QUICKSTART.md header
3. Update "Last Updated" dates in docs
4. Update performance metrics if changed
5. Retake screenshots if UI changed
6. Update CLAUDE.md with new features

---

## GitHub-Specific Best Practices

### Badges
- Use shields.io for consistency
- Include: License, Python version, Node version, Version
- Keep to 4-6 badges maximum (avoid clutter)

### Screenshots
- Use 1280x800 @ 2x DPI (Retina)
- Store in docs/screenshots/ or tests/screenshots/
- Use descriptive filenames (01-main-graph.png)
- Reference with relative paths

### Mermaid Diagrams
- Use for system architecture
- Keep simple (5-7 nodes max)
- Use descriptive labels
- Test rendering on GitHub

### Links
- Use relative paths (./docs/FILE.md)
- Test all links before committing
- Use descriptive link text (not "click here")

### Tables
- Use for comparisons and options
- Keep columns to 2-4 maximum
- Use bold for emphasis in first column
- Add horizontal rules for readability

---

## Checklist for New Documentation

- [ ] Is it scannable in 30 seconds?
- [ ] Does it use tables instead of prose?
- [ ] Are code blocks syntax-highlighted?
- [ ] Are links relative and tested?
- [ ] Is the audience clear?
- [ ] Does it avoid duplication?
- [ ] Are screenshots high-quality and relevant?
- [ ] Is the version number updated?
- [ ] Does it follow the style guide?
- [ ] Is it linked from the appropriate parent page?

---

**Result:** Professional, scannable documentation optimized for GitHub that serves all audiences without overwhelming any single group.
