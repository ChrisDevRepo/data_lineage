#!/bin/bash
# Phase 1 Verification Script - Dialect Configuration Layer
# ===========================================================
# Run this after installing dependencies to verify Phase 1 is complete

set -e

echo "======================================================================"
echo "Phase 1 Verification: Dialect Configuration Layer"
echo "======================================================================"
echo ""

# Check Python version
echo "1. Checking Python version..."
python --version
echo "✅ Python version OK"
echo ""

# Install dependencies if needed
echo "2. Checking dependencies..."
if ! python -c "import pydantic" 2>/dev/null; then
    echo "⚠️  Pydantic not installed. Installing dependencies..."
    pip install -q pydantic pydantic-settings pytest
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi
echo ""

# Test dialect_config module
echo "3. Testing dialect_config module..."
python -c "
from lineage_v3.config.dialect_config import (
    SQLDialect, validate_dialect, get_dialect_metadata, list_supported_dialects
)

# Test validate_dialect
assert validate_dialect('tsql') == SQLDialect.TSQL
assert validate_dialect('FABRIC') == SQLDialect.FABRIC

# Test get_dialect_metadata
metadata = get_dialect_metadata(SQLDialect.TSQL)
assert metadata.display_name is not None
assert metadata.metadata_source == 'dmv'

# Test list_supported_dialects
dialects = list_supported_dialects()
assert len(dialects) == 7

print('✅ dialect_config module working')
"
echo ""

# Test settings integration
echo "4. Testing settings integration..."
python -c "
from lineage_v3.config.settings import Settings
from lineage_v3.config.dialect_config import SQLDialect

# Test default
settings = Settings()
assert settings.sql_dialect == 'tsql'
assert settings.dialect == SQLDialect.TSQL

# Test other dialects
settings = Settings(sql_dialect='postgres')
assert settings.dialect == SQLDialect.POSTGRES

print('✅ Settings integration working')
"
echo ""

# Run pytest tests
echo "5. Running pytest tests..."
python -m pytest tests/unit/config/test_dialect_config.py -v --tb=short
echo ""

python -m pytest tests/unit/config/test_settings.py -v --tb=short
echo ""

echo "======================================================================"
echo "✅ Phase 1 Verification Complete"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  ✅ Dialect configuration layer created"
echo "  ✅ 7 dialects defined (tsql, fabric, postgres, oracle, snowflake, redshift, bigquery)"
echo "  ✅ Settings integration complete"
echo "  ✅ All unit tests passing"
echo ""
echo "Next: Phase 2 - Metadata Extractor Abstraction"
echo ""
