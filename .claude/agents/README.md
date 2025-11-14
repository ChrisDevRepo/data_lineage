# Project Subagents

This directory contains specialized AI subagents for the Data Lineage Visualizer project.

## Available Subagents

### 1. parser-validator
**Use when:** Modifying `quality_aware_parser.py`, `sql_cleaning_rules.py`, or any parser logic
**Tools:** Read, Bash, Grep
**Model:** Haiku (fast, cost-effective)

**Purpose:** Validates parser changes to maintain 100% success rate (349/349 SPs)

**Invocation:**
- Automatic: Claude detects parser changes
- Manual: "Use parser-validator to check my changes"

**Output:**
- Success rate comparison (before/after)
- Confidence distribution analysis
- Test results (user-verified tests)
- APPROVE/REJECT verdict with reasons

---

### 2. rule-engine-reviewer
**Use when:** Modifying `sql_cleaning_rules.py` or adding/changing SQL preprocessing rules
**Tools:** Read, Grep
**Model:** Haiku (fast, cost-effective)

**Purpose:** Reviews rule changes against change journal to prevent repeating past mistakes

**Invocation:**
- Automatic: Claude detects rule engine changes
- Manual: "Use rule-engine-reviewer to check this rule change"

**Output:**
- Journal conflict check
- Safety assessment
- Red flags (conflicts with "DO NOT" patterns)
- APPROVE/REJECT recommendation

---

### 3. baseline-checker
**Use when:** About to make parser changes OR after completing parser changes
**Tools:** Bash, Read
**Model:** Haiku (fast, cost-effective)

**Purpose:** Orchestrates baseline validation workflow (before/after comparison)

**Invocation:**
- Manual (before): "Use baseline-checker to capture baseline"
- Manual (after): "Use baseline-checker to compare results"

**Output:**
- Baseline capture confirmation
- Before/after comparison
- Regression detection
- PASS/FAIL verdict

---

### 4. doc-optimizer
**Use when:** Documentation needs cleanup or CLAUDE.md exceeds 300 lines
**Tools:** Read, Grep, Bash
**Model:** Haiku (fast, cost-effective)

**Purpose:** Optimizes documentation for clarity and conciseness

**Invocation:**
- Manual: "Use doc-optimizer to analyze CLAUDE.md"
- Manual: "Help me reduce CLAUDE.md from 505 to 300 lines"

**Output:**
- Current state analysis
- Optimization targets
- Estimated line reduction
- Preserve critical information

---

## Best Practices

### When to Use Subagents

✅ **Use subagents for:**
- Parser validation before committing
- Rule engine change review
- Baseline capture and comparison
- Documentation optimization

❌ **Don't use subagents for:**
- Simple questions
- Writing new features
- General code review (use main agent)

### Invocation Methods

**Automatic:**
Claude automatically delegates when it detects matching tasks.

**Manual:**
```
"Use parser-validator to check my changes"
"Use rule-engine-reviewer for this rule"
"Use baseline-checker to capture baseline"
"Use doc-optimizer to reduce CLAUDE.md length"
```

### Subagent Workflow Example

```
User: "I'm going to modify the DECLARE/SET rule in sql_cleaning_rules.py"

Claude: "Let me use the rule-engine-reviewer to check the change journal first."
→ [rule-engine-reviewer checks journal for DECLARE/SET issues]
→ [Finds past conflicts, reports warnings]

Claude: "Based on the journal, DECLARE/SET patterns caused conflicts in v4.3.3.
Let me use baseline-checker to capture baseline before you make changes."
→ [baseline-checker captures baseline_before.txt]
→ [Confirms readiness]

User: [Makes changes to rule]

Claude: "Now let me use parser-validator to validate the changes."
→ [parser-validator runs tests and compares baseline]
→ [Reports APPROVE/REJECT verdict]
```

---

## Configuration

Subagents are configured using Markdown files with YAML frontmatter:

```markdown
---
name: agent-name
description: When to use this agent
tools: Read, Bash, Grep  # Minimal tool access (principle of least privilege)
model: haiku             # Fast and cost-effective (3x cheaper than Sonnet)
---

System prompt and instructions...
```

### Tool Access Philosophy

Following the principle of least privilege, each subagent has minimal tool access:

- **Read, Grep** - For analyzing files and journals
- **Bash** - Only for running validation scripts (no file modifications)
- **No Write/Edit** - Subagents analyze and recommend; main agent makes changes

### Model Selection

All subagents use **Haiku** model:
- 3x cost savings vs Sonnet
- 2x speed improvement
- 90% of Sonnet's capability
- Perfect for validation and analysis tasks

---

## Maintenance

### Adding New Subagents

1. Create markdown file in `.claude/agents/`
2. Use YAML frontmatter format
3. Define clear, action-oriented description
4. Minimal tool access (only what's needed)
5. Use Haiku model for cost efficiency
6. Update this README

### Modifying Subagents

1. Edit the markdown file
2. Test with manual invocation
3. Update README if behavior changes

### Removing Subagents

1. Delete markdown file
2. Update this README

---

## Integration with CI/CD

While subagents run during development, consider integrating:

- Pre-commit hook can use `parser-validator` logic
- CI/CD can use `baseline-checker` for PR validation
- Documentation checks can use `doc-optimizer` rules

---

**Last Updated:** 2025-11-14
**Subagent Count:** 4 (parser-validator, rule-engine-reviewer, baseline-checker, doc-optimizer)
