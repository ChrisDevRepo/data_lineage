# ADR 001: Custom Exception Hierarchy

**Date:** 2025-11-14
**Status:** Accepted
**Deciders:** Development Team
**Related Sprint:** Sprint 4

## Context and Problem Statement

The codebase was using generic Python exceptions (`ValueError`, `RuntimeError`, `FileNotFoundError`, etc.) throughout the application. This made it difficult to:

1. **Distinguish error types** - All errors look the same to error handlers
2. **Debug issues** - Generic exceptions don't indicate which component failed
3. **Handle errors gracefully** - Can't catch specific lineage errors vs system errors
4. **Provide context** - Generic exception names don't convey domain meaning

**Example of the problem:**
```python
# Before: Which ValueError? From where? Why?
try:
    result = parse_object(obj_id)
except ValueError as e:
    # Was it invalid SQL? Invalid object_id? Invalid config?
    logger.error(f"Error: {e}")
```

We needed a way to categorize errors by domain concern and provide meaningful error types that reflect the application's architecture.

## Decision Drivers

- **Debuggability** - Developers should quickly understand where errors originate
- **Error handling** - Different components should handle different error types
- **Type safety** - IDEs should autocomplete exception types
- **Documentation** - Exception names should be self-documenting
- **Migration path** - Should be easy to adopt incrementally

## Considered Options

### Option 1: Continue Using Generic Exceptions
**Pros:**
- No code changes required
- Python standard library exceptions

**Cons:**
- Poor debuggability (all errors look the same)
- Can't distinguish lineage errors from system errors
- No type safety for error handling
- Hard to maintain (which ValueError is which?)

### Option 2: Custom Exception Hierarchy (CHOSEN)
**Pros:**
- Clear error categorization by domain
- Easy to debug (exception name indicates source)
- Type-safe error handling
- Self-documenting code
- Can add error-specific metadata

**Cons:**
- Requires creating new exception classes
- Need to update code to use new exceptions
- Slight learning curve for new developers

### Option 3: String-Based Error Codes
**Pros:**
- Lightweight (no new classes)
- Can be internationalized

**Cons:**
- Error codes are not discoverable (magic strings)
- No type safety
- Hard to grep/search for error types
- Requires separate error code documentation

## Decision Outcome

**Chosen option:** Custom Exception Hierarchy (Option 2)

We created a comprehensive exception hierarchy with 20 custom exceptions organized into 6 categories:

```python
LineageError (base)
├── ParsingError
│   ├── DDLNotFoundError
│   ├── SQLGlotParsingError
│   └── InvalidSQLError
├── CatalogError
│   ├── InvalidSchemaError
│   ├── InvalidObjectError
│   └── CatalogResolutionError
├── WorkspaceError
│   ├── WorkspaceNotConnectedError
│   ├── WorkspaceFileNotFoundError
│   └── WorkspaceMappingError
├── ConfigurationError
│   ├── InvalidDialectError
│   └── InvalidSettingError
├── RuleEngineError
│   ├── RuleLoadError
│   ├── RuleValidationError
│   └── RuleExecutionError
├── JobError
│   ├── JobNotFoundError
│   └── JobFailedError
└── ValidationError
    ├── InvalidIdentifierError
    └── SQLInjectionRiskError
```

### Implementation

**File:** `engine/exceptions.py` (300+ lines)

**Key features:**
1. All exceptions inherit from `LineageError` (allows catching all lineage errors)
2. Hierarchical organization (parsing, catalog, workspace, config, rules, jobs, validation)
3. Full documentation with purpose and usage examples
4. Exported from `engine/__init__.py` for easy imports
5. Helper function `get_exception_for_error_type()` for dynamic exception creation

**Example usage:**
```python
from engine import DDLNotFoundError, WorkspaceNotConnectedError

# Clear, specific exceptions
if not ddl_text:
    raise DDLNotFoundError(f"No DDL found for object_id={object_id}")

if not self.conn:
    raise WorkspaceNotConnectedError("Not connected to DuckDB workspace")

# Catch all lineage errors
try:
    process_lineage()
except LineageError as e:
    # Handle all application errors
    logger.error(f"Lineage error: {e}")
except Exception as e:
    # Handle system errors
    logger.error(f"System error: {e}")
```

## Consequences

### Positive

1. **✅ Better debugging**
   - Exception name immediately indicates source (parsing, catalog, workspace, etc.)
   - Stack traces are more informative
   - Easier to search logs for specific error types

2. **✅ Type-safe error handling**
   - IDEs autocomplete exception types
   - Catch specific errors vs catching all exceptions
   - Prevents catching too broadly

3. **✅ Self-documenting code**
   - `DDLNotFoundError` is clearer than `ValueError("DDL not found")`
   - Exception hierarchy shows application architecture
   - New developers understand error categories quickly

4. **✅ Flexible error handling**
   - Can catch broad categories (`ParsingError`) or specific errors (`SQLGlotParsingError`)
   - Can handle lineage errors separately from system errors
   - Can add retry logic for specific error types

5. **✅ Future extensibility**
   - Easy to add new exception types as needed
   - Can add error-specific metadata (error codes, context, suggestions)
   - Can integrate with error reporting tools (Sentry, etc.)

### Negative

1. **⚠️ Migration effort**
   - Existing code uses generic exceptions
   - Need to update gradually (not breaking change)
   - Estimated 2-3 hours to replace all generic exceptions

2. **⚠️ More files to maintain**
   - Added `engine/exceptions.py` (300+ lines)
   - Need to update `__init__.py` when adding new exceptions

3. **⚠️ Learning curve**
   - New developers need to learn exception hierarchy
   - Need to choose correct exception type when raising errors

### Mitigation

- **Migration:** Adopt incrementally (new code uses custom exceptions, old code gradually updated)
- **Documentation:** All exceptions documented with examples in `exceptions.py`
- **Discoverability:** All exceptions exported from `engine` for easy imports

## Validation

### Before
```python
# Generic, unclear
raise ValueError(f"Invalid object_id: {obj_id}")
raise RuntimeError("Not connected to DuckDB workspace")
raise FileNotFoundError(f"Required file not found: {file_path}")
```

### After
```python
# Specific, clear domain errors
raise InvalidObjectError(f"Invalid object_id: {obj_id}")
raise WorkspaceNotConnectedError("Not connected to DuckDB workspace")
raise WorkspaceFileNotFoundError(f"Required file not found: {file_path}")
```

### Impact Metrics

- **File created:** `engine/exceptions.py` (300+ lines)
- **File updated:** `engine/__init__.py` (exports all exceptions)
- **Exceptions defined:** 20 custom exceptions across 6 categories
- **Code changes:** None initially (additive, backward compatible)
- **Breaking changes:** None (existing code still works)

## Links

- **Implementation:** `engine/exceptions.py`
- **Export:** `engine/__init__.py`
- **Related Commit:** e9757f2 (Sprint 4 - Cleanup & Exception Hierarchy)
- **Related ADR:** ADR 002 (YAML Rules Deletion) - shows use of `RuleEngineError` hierarchy

## Notes

This ADR documents the architectural decision made during Sprint 4 of the comprehensive cleanup session. The exception hierarchy was created alongside other quality improvements (type safety, test infrastructure, documentation).

The decision aligns with Python best practices:
- PEP 8: "Use exceptions rather than returning error codes"
- Domain-driven design: Exceptions reflect domain concepts
- Clean architecture: Clear separation of error types by layer

Future considerations:
- Add error codes (e.g., `E001: DDL_NOT_FOUND`) for internationalization
- Add `context` attribute to exceptions for structured error data
- Integrate with error monitoring tools (Sentry, Rollbar)

---

**Last Updated:** 2025-11-14
**Author:** Development Team
**Review Status:** Approved
