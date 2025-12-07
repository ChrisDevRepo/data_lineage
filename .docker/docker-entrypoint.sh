#!/bin/bash
set -e

# ==============================================================================
# Data Lineage Visualizer - Docker Entrypoint
# Author: Christian Wagner
# Version: 1.0.1
# ==============================================================================
# First-run initialization: Copies defaults to external volume if not present
# ==============================================================================

CONFIG_DIR="/app/config"
ENV_FILE="$CONFIG_DIR/.env"
RULES_DIR="$CONFIG_DIR/rules"
QUERIES_DIR="$CONFIG_DIR/queries"
UTIL_DIR="$CONFIG_DIR/util"

echo "Data Lineage Visualizer v1.0.1"
echo "Author: Christian Wagner"

# Create config directories
mkdir -p "$CONFIG_DIR/data" \
         "$CONFIG_DIR/logs" \
         "$CONFIG_DIR/uploads" \
         "$UTIL_DIR"

# Copy .env.example if .env doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo "Initializing .env from template..."
    cp /app/.env.example "$ENV_FILE"
    echo "Created $ENV_FILE (customize for your environment)"
fi

# Copy SQL extraction rules if not present
RULES_COUNT=$(find "$RULES_DIR" -name "*.yaml" 2>/dev/null | wc -l)
if [ "$RULES_COUNT" -eq 0 ]; then
    echo "Initializing SQL extraction rules..."
    mkdir -p "$RULES_DIR/defaults" "$RULES_DIR/tsql"
    cp /app/engine/rules/defaults/*.yaml "$RULES_DIR/defaults/" 2>/dev/null || echo "Warning: Failed to copy default rules"
    cp /app/engine/rules/tsql/*.yaml "$RULES_DIR/tsql/" 2>/dev/null || echo "Warning: Failed to copy TSQL rules"

    # Verify copy succeeded
    COPIED_COUNT=$(find "$RULES_DIR" -name "*.yaml" 2>/dev/null | wc -l)
    if [ "$COPIED_COUNT" -gt 0 ]; then
        echo "Copied $COPIED_COUNT YAML rule files"
    else
        echo "Warning: No YAML files copied - will use built-in defaults"
    fi
fi

# Copy query templates if not present
QUERIES_COUNT=$(find "$QUERIES_DIR" -name "*.yaml" 2>/dev/null | wc -l)
if [ "$QUERIES_COUNT" -eq 0 ]; then
    echo "Initializing query templates..."
    mkdir -p "$QUERIES_DIR/tsql"
    cp /app/engine/connectors/queries/tsql/*.yaml "$QUERIES_DIR/tsql/" 2>/dev/null || echo "Warning: Failed to copy query templates"

    # Verify copy succeeded
    COPIED_QUERIES=$(find "$QUERIES_DIR" -name "*.yaml" 2>/dev/null | wc -l)
    if [ "$COPIED_QUERIES" -gt 0 ]; then
        echo "Copied $COPIED_QUERIES query template files"
    else
        echo "Warning: No query files copied - will use built-in defaults"
    fi
fi

# Create util README if not exists
if [ ! -f "$UTIL_DIR/README.md" ]; then
    cat > "$UTIL_DIR/README.md" << 'UTILEOF'
# Util Directory

This directory is accessible from the host system for easy file management.

Use cases:
- Custom scripts for data processing
- Backup automation scripts
- Data export utilities
- Integration scripts

Example:
```bash
# From host system
ls ./config-data/util
cat ./config-data/util/my-script.py
```
UTILEOF
    echo "Created util/README.md"
fi

echo "Initialization complete"
echo "Config volume: $CONFIG_DIR"
echo "Starting application on port ${PORT:-8000}..."

# Execute the main command (CMD from Dockerfile)
exec "$@"
