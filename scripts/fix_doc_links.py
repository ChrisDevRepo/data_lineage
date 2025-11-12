#!/usr/bin/env python3
"""
Fix broken documentation links across the repository.

This script:
1. Maps broken links to correct file paths
2. Updates all documentation files with correct links
3. Removes references to non-existent files
"""

import re
from pathlib import Path

# Link mapping: old link -> new link (or None to remove)
LINK_FIXES = {
    # README.md fixes
    'ENV_SETUP.md': 'docs/archive/ENV_SETUP.md',
    'docs/SETUP_AND_DEPLOYMENT.md': 'docs/SETUP.md',
    'docs/SYSTEM_OVERVIEW.md': 'docs/documentation-mode/01_CURRENT_SYSTEM_ARCHITECTURE.md',
    'docs/CONFIGURATION_GUIDE.md': 'docs/SETUP.md',  # Configuration is part of SETUP
    'lineage_specs.md': None,  # Doesn't exist, remove
    'docs/PARSING_USER_GUIDE.md': 'docs/USAGE.md',
    'docs/PARSER_EVOLUTION_LOG.md': 'docs/REFERENCE.md',  # Merged into REFERENCE
    'docs/DUCKDB_SCHEMA.md': 'docs/REFERENCE.md',  # Schema is in REFERENCE
    'extractor/README.md': None,  # Not yet implemented
    'docs/MAINTENANCE_GUIDE.md': 'docs/USAGE.md',  # Troubleshooting is in USAGE
    'docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md': None,  # Not yet implemented

    # docs/README.md fixes (references to guides/, reference/, development/ subdirs)
    'guides/SETUP_AND_DEPLOYMENT.md': 'SETUP.md',
    'guides/CONFIGURATION_GUIDE.md': 'SETUP.md',
    'guides/MAINTENANCE_GUIDE.md': 'USAGE.md',
    'guides/PARSING_USER_GUIDE.md': 'USAGE.md',
    'guides/COMMENT_HINTS_DEVELOPER_GUIDE.md': 'USAGE.md',
    'reference/SYSTEM_OVERVIEW.md': 'documentation-mode/01_CURRENT_SYSTEM_ARCHITECTURE.md',
    'reference/PARSER_EVOLUTION_LOG.md': 'REFERENCE.md',
    'reference/DUCKDB_SCHEMA.md': 'REFERENCE.md',
    'reference/SUB_DL_OPTIMIZE_PARSING_SPEC.md': None,
    'development/sql_cleaning_engine/README.md': None,
    'development/sql_cleaning_engine/SQL_CLEANING_ENGINE_SUMMARY.md': None,
    'development/sql_cleaning_engine/SQL_CLEANING_ENGINE_DOCUMENTATION.md': None,
    'development/sql_cleaning_engine/SQL_CLEANING_ENGINE_ACTION_PLAN.md': None,
    'archive/README.md': None,  # No archive README needed

    # api/README.md fixes
    '../docs/API_TESTING.md': None,  # Doesn't exist
    '../docs/IMPLEMENTATION_SPEC_FINAL.md': None,  # Doesn't exist

    # frontend/README.md fixes
    './CHANGELOG.md': None,  # Doesn't exist
    './docs/FRONTEND_ARCHITECTURE.md': None,
    './docs/LOCAL_DEVELOPMENT.md': None,
    './docs/DEPLOYMENT_AZURE.md': None,
    './docs/UI_STANDARDIZATION_GUIDE.md': None,

    # tests/README.md fixes
    '../docs/guides/SETUP_AND_DEPLOYMENT.md': '../docs/SETUP.md',
    '../docs/reference/PARSER_SPECIFICATION.md': '../docs/REFERENCE.md',
    '../docs/reference/PARSER_EVOLUTION_LOG.md': '../docs/REFERENCE.md',
    '../docs/guides/PARSING_USER_GUIDE.md': '../docs/USAGE.md',
    '../docs/reference/SUB_DL_OPTIMIZE_PARSING_SPEC.md': None,
    '../docs/development/PARSING_REVIEW_STATUS.md': None,
}


def fix_links_in_file(file_path: Path):
    """Fix broken links in a single markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return False

    original_content = content
    changes_made = 0

    # Find all markdown links
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        full_match = match.group(0)
        link_text = match.group(1)
        link_url = match.group(2)

        # Skip external URLs
        if link_url.startswith('http'):
            continue

        # Check if this link needs fixing
        if link_url in LINK_FIXES:
            new_link = LINK_FIXES[link_url]

            if new_link is None:
                # Remove the entire line containing this link
                lines = content.split('\n')
                new_lines = [line for line in lines if full_match not in line]
                content = '\n'.join(new_lines)
                print(f"  Removed link: {link_url}")
                changes_made += 1
            else:
                # Replace with correct link
                new_match = f'[{link_text}]({new_link})'
                content = content.replace(full_match, new_match)
                print(f"  Fixed: {link_url} -> {new_link}")
                changes_made += 1

    if changes_made > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Saved {file_path} with {changes_made} changes")
            return True
        except Exception as e:
            print(f"  Error writing {file_path}: {e}")
            return False

    return False


def main():
    """Fix all broken links in documentation"""
    print("Fixing broken documentation links...\n")

    files_to_fix = [
        Path('README.md'),
        Path('CLAUDE.md'),
        Path('docs/README.md'),
        Path('api/README.md'),
        Path('frontend/README.md'),
        Path('tests/README.md'),
    ]

    total_fixed = 0
    for file_path in files_to_fix:
        if file_path.exists():
            print(f"Checking {file_path}...")
            if fix_links_in_file(file_path):
                total_fixed += 1
        else:
            print(f"  Skipping (not found): {file_path}")

    print(f"\n✓ Fixed {total_fixed} files")


if __name__ == '__main__':
    main()
