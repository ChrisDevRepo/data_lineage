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
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import yaml

from lineage_v3.config.dialect_config import SQLDialect

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
    pattern: str
    replacement: str

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

        # Compile pattern if not cached
        if self._compiled_pattern is None:
            try:
                self._compiled_pattern = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            except re.error as e:
                logger.error(f"Rule '{self.name}' has invalid regex pattern: {e}")
                return sql

        # Find all matches for logging
        matches = self._compiled_pattern.findall(sql)

        if verbose and self.debug_log_matches and matches:
            logger.debug(f"Rule '{self.name}' matched {len(matches)} occurrence(s)")
            for i, match in enumerate(matches[:5], 1):  # Show first 5
                preview = match[:50] + "..." if len(match) > 50 else match
                logger.debug(f"  Match {i}: {preview}")

        # Apply replacement
        original_sql = sql
        sql = self._compiled_pattern.sub(self.replacement, sql)

        if verbose and self.debug_log_replacements and original_sql != sql:
            size_before = len(original_sql)
            size_after = len(sql)
            reduction = ((size_before - size_after) / size_before * 100) if size_before > 0 else 0
            logger.debug(
                f"Rule '{self.name}' applied: "
                f"{size_before} → {size_after} bytes (-{reduction:.1f}%)"
            )

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

                except Exception as e:
                    # IMPORTANT: Warn but don't crash on invalid rules
                    logger.warning(f"Failed to load rule from {yaml_file}: {e}")
                    logger.debug(f"Rule load error details:", exc_info=True)

        # Sort by priority (lower = runs first)
        rules.sort(key=lambda r: r.priority)

        logger.info(f"Loaded {len(rules)} rules for dialect {dialect.value}")
        return rules

    def _load_rule_file(self, yaml_path: Path) -> Rule:
        """Load and parse a single rule YAML file."""

        with open(yaml_path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)

        # Validate required fields
        required = ['name', 'description', 'dialect', 'enabled', 'pattern', 'replacement']
        missing = [f for f in required if f not in raw]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

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
        >>> from lineage_v3.config.dialect_config import SQLDialect
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
