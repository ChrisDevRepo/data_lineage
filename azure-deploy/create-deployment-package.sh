#!/bin/bash
# ==============================================================================
# Create Azure Web App Deployment Package
# ==============================================================================
# This script creates a ZIP file ready for deployment to Azure Web App.
# It includes the backend API, frontend static files, and configuration.
# ==============================================================================

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  📦 Creating Azure Web App Deployment Package                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory (azure-deploy/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Output configuration
PACKAGE_NAME="lineage-visualizer-azure.zip"
OUTPUT_DIR="$SCRIPT_DIR"
TEMP_DIR="$SCRIPT_DIR/package_temp"

echo "📁 Project Root: $PROJECT_ROOT"
echo "📦 Package Name: $PACKAGE_NAME"
echo ""

# Clean up any previous build
echo "🧹 Cleaning up previous builds..."
rm -rf "$TEMP_DIR"
rm -f "$OUTPUT_DIR/$PACKAGE_NAME"
mkdir -p "$TEMP_DIR"

# ============================================================================
# 1. Build Frontend
# ============================================================================
echo "🎨 Building frontend..."
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   📦 Installing Node.js dependencies..."
    npm install
fi

# Build production bundle
echo "   🔨 Building production bundle..."
npm run build

# Verify build output
if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "❌ Frontend build failed! dist/ folder not found."
    exit 1
fi

echo "   ✅ Frontend built successfully"
echo ""

# ============================================================================
# 2. Copy Backend Files
# ============================================================================
echo "🔧 Copying backend files..."

# Copy Python source code (excluding __pycache__)
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' "$PROJECT_ROOT/api/" "$TEMP_DIR/api/"
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' "$PROJECT_ROOT/lineage_v3/" "$TEMP_DIR/lineage_v3/"

# Copy requirements (use flattened version for Azure compatibility)
cp "$SCRIPT_DIR/requirements-flat.txt" "$TEMP_DIR/requirements.txt"

echo "   ✅ Backend files copied"
echo ""

# ============================================================================
# 3. Copy Frontend Build
# ============================================================================
echo "📂 Copying frontend static files..."

# Copy built frontend to static/ directory (served by FastAPI)
mkdir -p "$TEMP_DIR/static"
cp -r "$PROJECT_ROOT/frontend/dist/"* "$TEMP_DIR/static/"

echo "   ✅ Frontend static files copied"
echo ""

# ============================================================================
# 4. Copy Azure Configuration Files
# ============================================================================
echo "⚙️  Adding Azure configuration..."

# Copy startup script
cp "$SCRIPT_DIR/startup.sh" "$TEMP_DIR/"
chmod +x "$TEMP_DIR/startup.sh"

# Copy .env.example for reference
cp "$SCRIPT_DIR/.env.example" "$TEMP_DIR/"

# Copy install guide
cp "$SCRIPT_DIR/INSTALL.md" "$TEMP_DIR/"

# Create .deployment file (tells Azure which file to use)
cat > "$TEMP_DIR/.deployment" << 'EOF'
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT = true
EOF

echo "   ✅ Configuration files added"
echo ""

# ============================================================================
# 5. Create ZIP Package
# ============================================================================
echo "📦 Creating ZIP package..."

# Use Python to create ZIP (more portable than zip command)
cd "$TEMP_DIR"
OUTPUT_DIR="$OUTPUT_DIR" PACKAGE_NAME="$PACKAGE_NAME" python3 << 'PYEOF'
import zipfile
import os
from pathlib import Path

output_file = Path(os.environ['OUTPUT_DIR']) / os.environ['PACKAGE_NAME']
source_dir = Path('.')

with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file_path in source_dir.rglob('*'):
        if file_path.is_file():
            arcname = file_path.relative_to(source_dir)
            zipf.write(file_path, arcname)
PYEOF

# Get file size
PACKAGE_SIZE=$(du -h "$OUTPUT_DIR/$PACKAGE_NAME" | cut -f1)

echo "   ✅ Package created: $PACKAGE_NAME ($PACKAGE_SIZE)"
echo ""

# ============================================================================
# 6. Verify Package Contents
# ============================================================================
echo "🔍 Verifying package contents..."

REQUIRED_FILES=(
    "api/main.py"
    "lineage_v3/__init__.py"
    "requirements.txt"
    "startup.sh"
    "static/index.html"
    ".env.example"
    "INSTALL.md"
)

ALL_GOOD=true
for file in "${REQUIRED_FILES[@]}"; do
    # Use Python to check ZIP contents (more portable)
    if python3 -c "import zipfile; z=zipfile.ZipFile('$OUTPUT_DIR/$PACKAGE_NAME'); exit(0 if '$file' in z.namelist() else 1)" 2>/dev/null; then
        echo "   ✅ $file"
    else
        echo "   ❌ MISSING: $file"
        ALL_GOOD=false
    fi
done

echo ""

# ============================================================================
# 7. Cleanup
# ============================================================================
echo "🧹 Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# ============================================================================
# 8. Final Status
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$ALL_GOOD" = true ]; then
    echo "✅ SUCCESS! Deployment package ready:"
    echo ""
    echo "   📦 File: $OUTPUT_DIR/$PACKAGE_NAME"
    echo "   📏 Size: $PACKAGE_SIZE"
    echo ""
    echo "📖 Next Steps:"
    echo "   1. Open Azure Portal: https://portal.azure.com"
    echo "   2. Navigate to your Web App"
    echo "   3. Go to: Deployment Center > Zip Deploy"
    echo "   4. Upload: $PACKAGE_NAME"
    echo "   5. Follow guide: INSTALL.md"
else
    echo "❌ WARNING: Package created but some files are missing!"
    echo "   Review the verification output above."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
