# ADR 002: Delete YAML Rules System

**Date:** 2025-11-14
**Status:** Accepted
**Deciders:** Development Team
**Related Sprint:** Sprint 4

## Context and Problem Statement

The codebase contained two parallel rule systems for SQL cleaning:

1. **Python Rules** (`engine/parsers/sql_cleaning_rules.py`)
   - 17 active rules in production
   - 100% success rate (349/349 SPs)
   - Well-tested, well-documented
   - Integrated with parser

2. **YAML Rules** (`engine/rules/`)
   - Complete implementation (rule loader, validation, execution)
   - 711 lines of documentation (`docs/RULE_DEVELOPMENT.md`)
   - **NOT integrated with parser**
   - Never used in production

Having two rule systems created confusion:
- Which system should developers use?
- Why does YAML exist if it's not integrated?
- Should we integrate YAML or delete it?

## Decision Drivers

- **Clarity** - Single, clear rule system for developers
- **Maintenance burden** - Two systems to maintain vs one
- **User philosophy** - "Never change a running system" (100% success rate)
- **Risk** - Integration could introduce regressions
- **Documentation accuracy** - Docs should reflect actual system

## Considered Options

### Option 1: Integrate YAML Rules System
**Implementation approach:**
```python
# Replace Python rules with YAML rules in quality_aware_parser.py
from engine.rules import load_rules
rules = load_rules(settings.dialect)
cleaned_sql = apply_rules(sql, rules)
```

**Pros:**
- Declarative rule definition (no Python code for new rules)
- Rules defined in YAML files (easier for non-Python users)
- Dynamic rule loading based on dialect
- Complete implementation already exists

**Cons:**
- ⚠️ Risk of regressions (changing working system)
- ⚠️ Requires testing all 349 SPs again
- ⚠️ Python rules work perfectly (100% success)
- ⚠️ YAML system not battle-tested
- ⚠️ 2-3 hours integration effort
- ⚠️ Violates "never change a running system"

**Estimated effort:** 2-3 hours integration + 2-3 hours testing

### Option 2: Delete YAML Rules System (CHOSEN)
**Implementation approach:**
```bash
rm -rf engine/rules/
rm docs/RULE_DEVELOPMENT.md
# Update CLAUDE.md to reference PYTHON_RULES.md
```

**Pros:**
- ✅ Eliminates confusion (one rule system)
- ✅ Reduces maintenance burden
- ✅ Documentation matches reality
- ✅ Follows "never change a running system"
- ✅ Can recreate YAML system if needed (30KB, well-structured)
- ✅ Zero risk (no changes to working code)

**Cons:**
- Need to recreate if YAML rules needed in future
- Loses declarative rule definition capability

**Estimated effort:** 30 minutes deletion + documentation updates

### Option 3: Keep Both Systems (Deferred Decision)
**Implementation approach:**
- Keep both systems
- Add clear documentation about status
- Decide later when to integrate

**Pros:**
- No immediate action required
- Preserves future option

**Cons:**
- ⚠️ Ongoing confusion for developers
- ⚠️ Maintenance burden for unused code
- ⚠️ Documentation misleading (system exists but doesn't work)
- ⚠️ Technical debt accumulates

## Decision Outcome

**Chosen option:** Delete YAML Rules System (Option 2)

### Rationale

1. **Parser works perfectly**
   - 100% success rate (349/349 SPs)
   - Zero production issues
   - Confidence distribution: 82.5% perfect, 7.4% good, 10% acceptable

2. **YAML system never integrated**
   - WARNING banner added in Sprint 1 confirmed this
   - No production usage
   - Not tested with real SPs

3. **User philosophy**
   - "Never change a running system"
   - Risk > Reward for integration
   - Can defer to v5.0.0 if needed

4. **Maintenance clarity**
   - One rule system = clear ownership
   - Developers know where to add rules
   - Documentation accurate

5. **Low recreation cost**
   - YAML system small (30KB)
   - Well-structured, easy to recreate
   - Can restore from git if needed

### Implementation

**Deleted:**
- `engine/rules/` directory (30KB, 4 files)
  - `__init__.py`
  - `rule_loader.py` (10KB)
  - `generic/01_whitespace.yaml`
  - `tsql/01_raiserror.yaml`
- `docs/RULE_DEVELOPMENT.md` (711 lines)

**Updated:**
- `CLAUDE.md`: Updated SQL Cleaning Rules section
  - Changed from YAML examples to Python examples
  - References `PYTHON_RULES.md` instead of `RULE_DEVELOPMENT.md`

**Preserved:**
- `engine/parsers/sql_cleaning_rules.py` (17 Python rules)
- `docs/PYTHON_RULES.md` (900+ lines documenting active system)

## Consequences

### Positive

1. **✅ Single source of truth**
   - Only one rule system to understand
   - Clear where to add/modify rules
   - Documentation matches reality

2. **✅ Reduced maintenance**
   - Don't maintain unused YAML system
   - Don't sync YAML and Python rules
   - Less code to test

3. **✅ Zero risk**
   - No changes to working parser
   - 100% success rate maintained
   - No regression testing needed

4. **✅ Clearer onboarding**
   - New developers see one rule system
   - No confusion about YAML vs Python
   - Direct path to adding rules

### Negative

1. **⚠️ Lost declarative rules**
   - Can't define rules in YAML
   - Must write Python for new rules
   - Non-Python users can't add rules easily

2. **⚠️ Recreation cost**
   - If YAML needed later, must recreate
   - 30KB of code to reimplement
   - ~4 hours to recreate + test

### Mitigation

- **Future needs:** Can restore from git (commit e9757f2 and earlier)
- **Recreation:** Well-structured system, easy to recreate if needed
- **Alternatives:** Could create simple rule DSL in Python if declarative approach needed

## Validation

### Before Deletion
```
engine/
├── parsers/
│   └── sql_cleaning_rules.py    # 17 Python rules (ACTIVE)
├── rules/                        # YAML system (NOT INTEGRATED)
│   ├── __init__.py
│   ├── rule_loader.py
│   ├── generic/
│   │   └── 01_whitespace.yaml
│   └── tsql/
│       └── 01_raiserror.yaml
docs/
├── RULE_DEVELOPMENT.md           # 711 lines (YAML system)
└── PYTHON_RULES.md                # MISSING (needed)
```

### After Deletion
```
engine/
├── parsers/
│   └── sql_cleaning_rules.py    # 17 Python rules (ACTIVE)
docs/
└── PYTHON_RULES.md                # 900+ lines (documents active system)
```

### Impact Metrics

- **Files deleted:** 4 (30KB)
- **Documentation deleted:** 711 lines (RULE_DEVELOPMENT.md)
- **Documentation added:** 900+ lines (PYTHON_RULES.md)
- **Code changes to parser:** 0 (no functional changes)
- **Risk level:** None (deleted unused code)
- **Success rate impact:** 0% (no change to parser)

## Alternative Approaches

### If YAML Rules Needed in Future

**Option A: Restore from git**
```bash
git checkout e9757f2 -- engine/rules/
git checkout e9757f2 -- docs/RULE_DEVELOPMENT.md
# Then integrate with parser
```

**Option B: Python-based DSL**
```python
# Simple declarative rules in Python (no YAML)
@rule(priority=10, category="batch_separator")
def remove_go(sql: str) -> str:
    return re.sub(r'^\s*GO\s*$', '', sql, flags=re.MULTILINE)
```

**Option C: JSON Rules** (simpler than YAML)
```json
{
  "name": "remove_go",
  "pattern": "^\\s*GO\\s*$",
  "replacement": "",
  "flags": ["MULTILINE"]
}
```

## Links

- **Related Commit:** e9757f2 (Sprint 4 - Cleanup & Exception Hierarchy)
- **Active System:** `engine/parsers/sql_cleaning_rules.py`
- **Documentation:** `docs/PYTHON_RULES.md`
- **Related ADR:** ADR 001 (Exception Hierarchy) - includes `RuleEngineError` for future use
- **Git History:** YAML system preserved in commit history before e9757f2

## Notes

This decision was made during Sprint 4 as part of comprehensive cleanup efforts. Other cleanup decisions in the same sprint:

1. Deleted 215KB of outdated documentation
2. Created custom exception hierarchy
3. Archived old reports
4. Streamlined documentation

The YAML rules deletion aligns with the broader cleanup philosophy:
- Remove unused code
- Maintain only what's actively used
- Keep documentation accurate
- Reduce maintenance burden

**User Quote:**
> "Never change a running system" - emphasizes stability over features

**Parser Success Rate:** 100% (349/349 SPs) - validates decision to not change working system

---

**Last Updated:** 2025-11-14
**Author:** Development Team
**Review Status:** Approved
