# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Data Lineage Visualizer project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

**Purpose:**
- Document why decisions were made
- Provide context for future developers
- Track architectural evolution
- Prevent repeating past mistakes

## ADR Index

| Number | Title | Status | Date | Sprint |
|--------|-------|--------|------|--------|
| [001](001-exception-hierarchy.md) | Custom Exception Hierarchy | Accepted | 2025-11-14 | Sprint 4 |
| [002](002-yaml-rules-deletion.md) | Delete YAML Rules System | Accepted | 2025-11-14 | Sprint 4 |

## ADR Format

Each ADR follows this structure:

```markdown
# ADR [number]: [Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Deciders:** [List of people involved]
**Related Sprint:** [Sprint number if applicable]

## Context and Problem Statement
[Describe the context and problem being addressed]

## Decision Drivers
[Key factors that influenced the decision]

## Considered Options
[List and describe all options considered]

### Option 1: [Name]
**Pros:**
- [Advantage 1]

**Cons:**
- [Disadvantage 1]

### Option 2: [Name] (CHOSEN)
**Pros:**
- [Advantage 1]

**Cons:**
- [Disadvantage 1]

## Decision Outcome
[Explain which option was chosen and why]

## Consequences
[Positive and negative consequences of the decision]

## Validation
[How the decision was validated or tested]

## Links
[Related files, commits, or other ADRs]
```

## Creating a New ADR

### Step 1: Choose a Number

Use the next sequential number (e.g., if last ADR is 002, use 003)

### Step 2: Create the File

```bash
# Template
cp docs/adr/000-template.md docs/adr/003-your-decision.md

# Or create from scratch
touch docs/adr/003-your-decision.md
```

### Step 3: Fill in the Template

- **Title:** Short, descriptive name
- **Status:** Start with "Proposed", change to "Accepted" when approved
- **Context:** Explain the problem and why a decision is needed
- **Options:** List ALL options considered (not just the chosen one)
- **Decision:** Explain which option was chosen and why
- **Consequences:** Both positive and negative impacts

### Step 4: Update This README

Add your ADR to the index table above.

### Step 5: Commit

```bash
git add docs/adr/003-your-decision.md docs/adr/README.md
git commit -m "docs: Add ADR 003 - Your Decision"
```

## ADR Status Lifecycle

```
Proposed → Accepted → Deprecated
                   → Superseded by ADR XXX
```

- **Proposed:** Under discussion, not yet implemented
- **Accepted:** Decision approved and implemented
- **Deprecated:** Decision no longer valid but kept for historical context
- **Superseded:** Replaced by a newer ADR (link to the new one)

## When to Create an ADR

Create an ADR for decisions that:

1. **Impact architecture** - Change how components interact
2. **Are hard to reverse** - Significant effort to undo
3. **Have trade-offs** - Multiple valid options with pros/cons
4. **Need context** - Future developers need to understand why
5. **Set precedent** - Similar decisions will follow this pattern

### Examples of ADR-worthy decisions:

✅ **YES - Create ADR:**
- Choosing a database (DuckDB vs SQLite vs PostgreSQL)
- Exception hierarchy design
- Deleting unused systems (YAML rules)
- Rule engine architecture (Python vs YAML)
- Graph library selection (Graphology vs D3)

❌ **NO - Don't create ADR:**
- Fixing a bug (unless it reveals architectural issue)
- Updating dependencies (unless major version with breaking changes)
- Adding a new feature (unless it requires architectural change)
- Refactoring code (unless it changes component boundaries)

## ADR vs Other Documentation

| Type | Purpose | When to Use |
|------|---------|-------------|
| **ADR** | Why we made a decision | Architectural choices |
| **README** | How to use the system | Getting started |
| **CHANGELOG** | What changed in each version | Release notes |
| **Code Comments** | How specific code works | Implementation details |
| **Technical Docs** | How the system works | System architecture |

## Best Practices

1. **Keep it concise** - 1-2 pages max
2. **Show alternatives** - List all options, not just the chosen one
3. **Be honest** - Include negative consequences too
4. **Link everything** - Related files, commits, other ADRs
5. **Date it** - Future readers need temporal context
6. **Update status** - Mark as Deprecated when no longer valid

## Examples from This Project

### Good ADR Example: [001-exception-hierarchy.md](001-exception-hierarchy.md)

**Why it's good:**
- Clear problem statement (generic exceptions causing issues)
- Three options considered (generic, custom, error codes)
- Detailed pros/cons for each
- Validation section shows before/after
- Impact metrics quantify the change
- Links to implementation files

### Another Example: [002-yaml-rules-deletion.md](002-yaml-rules-deletion.md)

**Why it's good:**
- Context explains two parallel systems
- Shows integration, deletion, and keep-both options
- Rationale tied to user philosophy ("never change a running system")
- Validation shows file structure before/after
- Explains mitigation for negative consequences

## Tools and Resources

**ADR Tools:**
- [adr-tools](https://github.com/npryce/adr-tools) - Command-line tool for managing ADRs
- [log4brains](https://github.com/thomvaill/log4brains) - Web UI for browsing ADRs

**Further Reading:**
- [Michael Nygard's ADR article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
- [When to write an ADR](https://github.com/joelparkerhenderson/architecture-decision-record#when-to-write-an-adr)

## Migration from Undocumented Decisions

If you discover an undocumented architectural decision, create an ADR for it:

1. **Title:** Use past tense (e.g., "Chose DuckDB for Workspace")
2. **Date:** Use the date of the original decision (check git history)
3. **Status:** Mark as "Accepted" (decision already implemented)
4. **Context:** Reconstruct from code, commits, discussions
5. **Note:** Add a note that this is a retroactive ADR

**Example:**
> **Note:** This is a retroactive ADR documenting a decision made on 2024-10-15 (commit abc123). Created on 2025-11-14 for historical record.

---

**Last Updated:** 2025-11-14
**Directory Created:** 2025-11-14 (Sprint 5)
**ADR Count:** 2
