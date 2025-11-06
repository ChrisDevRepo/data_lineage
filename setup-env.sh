#!/bin/bash

# ==============================================================================
# Environment Setup Script
# ==============================================================================
# Generates .env file from .env.template for local development
# ==============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🔧 Data Lineage Visualizer - Environment Setup               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env.example exists
if [ ! -f ".env.example" ]; then
    echo "❌ Error: .env.example not found!"
    exit 1
fi

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  Warning: .env file already exists!"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled. Keeping existing .env file."
        exit 0
    fi
    echo ""
fi

# Copy example to .env
echo "📋 Copying .env.example to .env..."
cp .env.example .env
echo "✅ .env file created"
echo ""

# Prompt for customization
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Configuration Options"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your .env file has been created with sensible defaults."
echo "Most settings are commented out, which means defaults will be used."
echo ""
echo "📝 Common customizations:"
echo ""
echo "1. CORS Configuration (for API access):"
echo "   ALLOWED_ORIGINS=http://localhost:3000"
echo ""
echo "2. Custom Paths (if needed):"
echo "   PATH_WORKSPACE_FILE=my_custom_workspace.duckdb"
echo "   PATH_OUTPUT_DIR=my_output"
echo ""
echo "3. Logging Level:"
echo "   LOG_LEVEL=DEBUG  # For troubleshooting"
echo ""

read -p "Do you want to edit .env now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Try to open in user's preferred editor
    if [ -n "$EDITOR" ]; then
        $EDITOR .env
    elif command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    elif command -v vi &> /dev/null; then
        vi .env
    else
        echo "⚠️  No text editor found. Please edit .env manually:"
        echo "   nano .env"
    fi
else
    echo "📝 To customize settings later, edit: .env"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Environment setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Next steps:"
echo "   1. Review .env file: nano .env"
echo "   2. Start the application: ./start-app.sh"
echo ""
echo "⚠️  Important: .env is in .gitignore and will NOT be committed."
echo "   Never commit credentials or secrets to version control!"
echo ""
