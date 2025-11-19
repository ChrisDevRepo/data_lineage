"""
YAML Rule Loader for SQL Cleaning Rules.

Loads SQL cleaning rules from YAML files, supports dialect-specific rules,
and provides validation and testing capabilities.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import yaml

from engine.config.dialect_config import SQLDialect

logger = logging.getLogger(__name__)


@dataclass
class RuleTestCase:
    """A test case for a rule."""
    name: str
    description: str
    input: str
    expected: str


@dataclass
class Rule:
    """A SQL cleaning rule loaded from YAML."""

    name: str
    description: str
    dialect: str  # 'generic' or specific dialect
    category: str
    enabled: bool
    priority: int

    # Pattern configuration
    pattern_type: str  # 'regex' | 'sqlglot_transform'
    pattern: Any  # str for single pattern, List[str] for multi-step
    replacement: Any  # str for single replacement, List[str] for multi-step

    # Testing
    test_cases: List[RuleTestCase]

    # Debug configuration
    debug_log_matches: bool
    debug_log_replacements: bool
    debug_context_lines: int

    # Metadata
    metadata: Dict[str, Any]

    # File source
    source_file: Path

    # Compiled regex (cached)
    _compiled_pattern: Optional[re.Pattern] = None

    def applies_to(self, dialect: SQLDialect) -> bool:
        """Check if this rule applies to the given dialect."""
        if self.dialect == 'generic':
            return True
        return self.dialect == dialect.value

    def apply(self, sql: str, verbose: bool = False) -> str:
        """
        Apply this rule to SQL code.

        Supports both single-pattern and multi-step rules.

        Args:
            sql: SQL code to transform
            verbose: Enable verbose logging

        Returns:
            Transformed SQL code
        """
        if not self.enabled:
            if verbose:
                logger.debug(f"Rule '{self.name}' is disabled, skipping")
            return sql

        if self.pattern_type != 'regex':
            logger.warning(f"Rule '{self.name}' has unsupported pattern_type: {self.pattern_type}")
            return sql

        # Support multi-step rules (list of patterns)
        if isinstance(self.pattern, list) and isinstance(self.replacement, list):
            return self._apply_multi_step(sql, verbose)

        # Single pattern rule (original logic)
        # Compile pattern if not cached
        if self._compiled_pattern is None:
            try:
                self._compiled_pattern = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            except re.error as e:
                logger.error(f"❌ Rule '{self.name}' has invalid regex pattern: {e}")
                logger.error(f"   Rule skipped during execution. Fix the pattern in: {self.source_file}")
                return sql

        # Find all matches for logging (with error handling)
        try:
            matches = self._compiled_pattern.findall(sql)
        except Exception as e:
            logger.error(f"❌ Rule '{self.name}' failed during pattern matching: {e}")
            logger.error(f"   SQL might contain unexpected characters. Rule skipped.")
            if verbose:
                logger.debug(f"Pattern match error details:", exc_info=True)
            return sql

        if verbose and self.debug_log_matches and matches:
            logger.debug(f"Rule '{self.name}' matched {len(matches)} occurrence(s)")
            for i, match in enumerate(matches[:5], 1):  # Show first 5
                preview = match[:50] + "..." if len(match) > 50 else match
                logger.debug(f"  Match {i}: {preview}")

        # Apply replacement (with error handling)
        original_sql = sql
        try:
            sql = self._compiled_pattern.sub(self.replacement, sql)
        except Exception as e:
            logger.error(f"❌ Rule '{self.name}' failed during replacement: {e}")
            logger.error(f"   Check the 'replacement' field in: {self.source_file}")
            if verbose:
                logger.debug(f"Replacement error details:", exc_info=True)
            return original_sql  # Return unchanged SQL

        if verbose and self.debug_log_replacements and original_sql != sql:
            size_before = len(original_sql)
            size_after = len(sql)
            reduction = ((size_before - size_after) / size_before * 100) if size_before > 0 else 0
            logger.debug(
                f"Rule '{self.name}' applied: "
                f"{size_before} → {size_after} bytes (-{reduction:.1f}%)"
            )

        return sql

    def _apply_multi_step(self, sql: str, verbose: bool = False) -> str:
        """
        Apply multi-step rule (multiple patterns sequentially).

        For complex rules that need multiple regex passes.
        If any step fails, it's skipped but other steps continue.

        Args:
            sql: SQL code to transform
            verbose: Enable verbose logging

        Returns:
            Transformed SQL code
        """
        for i, (pattern, replacement) in enumerate(zip(self.pattern, self.replacement), 1):
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                matches_before = len(compiled.findall(sql))

                sql = compiled.sub(replacement, sql)

                if verbose and matches_before > 0:
                    logger.debug(f"Rule '{self.name}' step {i}/{len(self.pattern)}: {matches_before} matches")

            except re.error as e:
                logger.error(f"❌ Rule '{self.name}' step {i}/{len(self.pattern)} has invalid regex: {e}")
                logger.error(f"   Skipping this step, continuing with remaining steps.")
                if verbose:
                    logger.debug(f"Regex compile error in multi-step rule:", exc_info=True)
                continue  # Skip this step, continue with others

            except Exception as e:
                logger.error(f"❌ Rule '{self.name}' step {i}/{len(self.pattern)} failed: {e}")
                logger.error(f"   Skipping this step, continuing with remaining steps.")
                if verbose:
                    logger.debug(f"Multi-step application error:", exc_info=True)
                continue  # Skip this step, continue with others

        return sql

    def test(self) -> List[Dict[str, Any]]:
        """
        Run embedded test cases.

        Returns:
            List of test results with pass/fail status
        """
        results = []

        for test_case in self.test_cases:
            actual = self.apply(test_case.input, verbose=False)
            passed = actual == test_case.expected

            results.append({
                'test_name': test_case.name,
                'description': test_case.description,
                'passed': passed,
                'expected': test_case.expected,
                'actual': actual,
                'input': test_case.input
            })

        return results


class RuleLoader:
    """Loads SQL cleaning rules from YAML files."""

    def __init__(self, rules_dir: Optional[Path] = None, custom_dirs: Optional[List[Path]] = None):
        """
        Initialize the rule loader.

        Args:
            rules_dir: Base directory containing rule subdirectories (generic/, tsql/, etc.)
            custom_dirs: Additional custom rule directories
        """
        if rules_dir is None:
            rules_dir = Path(__file__).parent

        self.rules_dir = rules_dir
        self.custom_dirs = custom_dirs or []

        logger.info(f"RuleLoader initialized with rules_dir: {rules_dir}")
        if self.custom_dirs:
            logger.info(f"Custom rule directories: {self.custom_dirs}")

    def load_for_dialect(self, dialect: SQLDialect, verbose: bool = False) -> List[Rule]:
        """
        Load all rules applicable to a specific dialect.

        Args:
            dialect: SQL dialect to load rules for
            verbose: Enable verbose logging

        Returns:
            List of Rule objects, sorted by priority
        """
        rules: List[Rule] = []
        errors = []  # Track files that failed to load

        # Standard directories to scan
        directories = [
            self.rules_dir / 'generic',  # Always load generic rules
            self.rules_dir / dialect.value  # Dialect-specific rules
        ]

        # Add custom directories
        directories.extend(self.custom_dirs)

        for directory in directories:
            if not directory.exists():
                if verbose:
                    logger.debug(f"Rule directory not found, skipping: {directory}")
                continue

            logger.info(f"Loading rules from: {directory}")

            for yaml_file in sorted(directory.glob('*.yaml')):
                try:
                    rule = self._load_rule_file(yaml_file)

                    # Check if rule applies to this dialect
                    if not rule.applies_to(dialect):
                        if verbose:
                            logger.debug(f"Rule '{rule.name}' doesn't apply to {dialect.value}, skipping")
                        continue

                    # Check if disabled
                    if not rule.enabled:
                        logger.warning(f"Rule '{rule.name}' is disabled in {yaml_file.name}")
                        continue

                    rules.append(rule)
                    logger.info(f"Loaded rule '{rule.name}' from {yaml_file.name}")

                except yaml.YAMLError as e:
                    # YAML syntax error - invalid file format
                    logger.error(f"❌ YAML syntax error in {yaml_file.name}: {e}")
                    logger.error(f"   File: {yaml_file}")
                    logger.error(f"   Fix the YAML syntax and restart. Rule skipped.")
                    errors.append((yaml_file.name, "YAML syntax error", str(e)))
                    if verbose:
                        logger.debug(f"YAML error details:", exc_info=True)
                except ValueError as e:
                    # Missing fields or validation error
                    logger.error(f"❌ Invalid rule configuration in {yaml_file.name}: {e}")
                    logger.error(f"   File: {yaml_file}")
                    logger.error(f"   Check README.md for required fields. Rule skipped.")
                    errors.append((yaml_file.name, "Invalid configuration", str(e)))
                    if verbose:
                        logger.debug(f"Validation error details:", exc_info=True)
                except re.error as e:
                    # Invalid regex pattern
                    logger.error(f"❌ Invalid regex pattern in {yaml_file.name}: {e}")
                    logger.error(f"   File: {yaml_file}")
                    logger.error(f"   Fix the 'pattern' field. Rule skipped.")
                    errors.append((yaml_file.name, "Invalid regex", str(e)))
                    if verbose:
                        logger.debug(f"Regex error details:", exc_info=True)
                except Exception as e:
                    # Unknown error - catch-all safety net
                    logger.error(f"❌ Unexpected error loading {yaml_file.name}: {e}")
                    logger.error(f"   File: {yaml_file}")
                    logger.error(f"   Rule skipped. Check file format.")
                    errors.append((yaml_file.name, "Unexpected error", str(e)))
                    logger.debug(f"Unexpected error details:", exc_info=True)

        # Sort by priority (lower = runs first)
        rules.sort(key=lambda r: r.priority)

        # Summary report
        logger.info(f"✅ Successfully loaded {len(rules)} rules for dialect '{dialect.value}'")

        if errors:
            logger.warning(f"⚠️  Failed to load {len(errors)} rule file(s):")
            for filename, error_type, details in errors:
                logger.warning(f"   - {filename}: {error_type}")
                if verbose:
                    logger.debug(f"      Details: {details}")
            logger.warning(f"   Fix the errors above and restart to enable these rules.")
        else:
            logger.info(f"✅ All rule files loaded successfully (no errors)")

        if rules:
            logger.info(f"Rule execution order (by priority):")
            for r in rules[:10]:  # Show first 10
                logger.info(f"  {r.priority:3d} - {r.name} ({r.category})")
            if len(rules) > 10:
                logger.info(f"  ... and {len(rules) - 10} more rules")

        return rules

    def _validate_regex_patterns(self, pattern: Union[str, List[str]], rule_name: str) -> None:
        """
        Validate regex patterns can be compiled.

        Raises:
            re.error: If any pattern is invalid
        """
        patterns = [pattern] if isinstance(pattern, str) else pattern

        for i, p in enumerate(patterns, 1):
            try:
                re.compile(p, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            except re.error as e:
                if len(patterns) > 1:
                    raise re.error(f"Pattern step {i}/{len(patterns)} is invalid: {e}")
                else:
                    raise re.error(f"Pattern is invalid: {e}")

    def _load_rule_file(self, yaml_path: Path) -> Rule:
        """
        Load and parse a single rule YAML file with comprehensive validation.

        Raises:
            yaml.YAMLError: Invalid YAML syntax
            ValueError: Missing required fields or validation errors
            re.error: Invalid regex pattern
        """
        # Read and parse YAML
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML syntax: {e}")

        if not isinstance(raw, dict):
            raise ValueError(f"YAML file must contain a dictionary, got {type(raw)}")

        # Validate required fields
        required = ['name', 'description', 'dialect', 'enabled', 'pattern', 'replacement']
        missing = [f for f in required if f not in raw]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Validate pattern/replacement types match
        pattern = raw['pattern']
        replacement = raw['replacement']

        if isinstance(pattern, list) != isinstance(replacement, list):
            raise ValueError(
                f"Pattern and replacement must both be strings or both be lists. "
                f"Got pattern={type(pattern).__name__}, replacement={type(replacement).__name__}"
            )

        if isinstance(pattern, list) and len(pattern) != len(replacement):
            raise ValueError(
                f"Pattern list has {len(pattern)} items but replacement list has {len(replacement)} items. "
                f"They must have the same length for multi-step rules."
            )

        # Validate regex patterns (compile to check syntax)
        self._validate_regex_patterns(pattern, raw['name'])

        # Parse test cases
        test_cases = []
        for tc in raw.get('test_cases', []):
            test_cases.append(RuleTestCase(
                name=tc.get('name', 'unnamed'),
                description=tc.get('description', ''),
                input=tc.get('input', ''),
                expected=tc.get('expected', '')
            ))

        # Parse debug config
        debug = raw.get('debug', {})

        return Rule(
            name=raw['name'],
            description=raw['description'],
            dialect=raw['dialect'],
            category=raw.get('category', 'general'),
            enabled=raw['enabled'],
            priority=raw.get('priority', 50),

            pattern_type=raw.get('pattern_type', 'regex'),
            pattern=raw['pattern'],
            replacement=raw['replacement'],

            test_cases=test_cases,

            debug_log_matches=debug.get('log_matches', False),
            debug_log_replacements=debug.get('log_replacements', False),
            debug_context_lines=debug.get('show_context_lines', 0),

            metadata=raw.get('metadata', {}),
            source_file=yaml_path
        )

    def test_all_rules(self, dialect: SQLDialect) -> Dict[str, List[Dict[str, Any]]]:
        """
        Test all rules for a dialect.

        Args:
            dialect: Dialect to test rules for

        Returns:
            Dictionary mapping rule names to test results
        """
        rules = self.load_for_dialect(dialect)
        results = {}

        for rule in rules:
            results[rule.name] = rule.test()

        return results


# Singleton instance
_loader: Optional[RuleLoader] = None


def get_rule_loader(custom_dirs: Optional[List[Path]] = None) -> RuleLoader:
    """Get the singleton RuleLoader instance."""
    global _loader
    if _loader is None:
        _loader = RuleLoader(custom_dirs=custom_dirs)
    return _loader


def load_rules(dialect: SQLDialect, custom_dirs: Optional[List[Path]] = None) -> List[Rule]:
    """
    Convenience function to load rules for a dialect.

    Args:
        dialect: SQL dialect
        custom_dirs: Optional custom rule directories

    Returns:
        List of applicable rules sorted by priority

    Example:
        >>> from engine.config.dialect_config import SQLDialect
        >>> from lineage_v3.rules.rule_loader import load_rules
        >>>
        >>> rules = load_rules(SQLDialect.TSQL)
        >>> for rule in rules:
        ...     print(f"{rule.priority}: {rule.name}")
        1: normalize_whitespace
        10: remove_raiserror
    """
    loader = get_rule_loader(custom_dirs=custom_dirs)
    return loader.load_for_dialect(dialect)
