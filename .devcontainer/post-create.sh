#!/bin/bash
# ==============================================================================
# Post-Create Script - Dev Container Setup
# ==============================================================================
# Runs automatically after the dev container is created
# Sets up Python environment, Node dependencies, and development tools
# ==============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Setting up Data Lineage Visualizer Dev Environment        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ------------------------------------------------------------------------------
# Step 1: Python Dependencies (using system Python, no venv needed in container)
# ------------------------------------------------------------------------------
echo "📦 Step 1/6: Installing Python dependencies..."

# Upgrade pip first (show progress)
echo "   Upgrading pip..."
pip install --upgrade pip --break-system-packages 2>&1 | tail -1

# Install Python dependencies with progress (no --quiet)
echo "   Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt --break-system-packages --progress-bar on

echo "   ✅ Python dependencies installed"
echo ""

# ------------------------------------------------------------------------------
# Step 2: Frontend Dependencies
# ------------------------------------------------------------------------------
echo "📦 Step 2/6: Installing frontend dependencies..."

cd frontend

# Remove existing node_modules if permissions are wrong (common with mounted volumes)
if [ -d "node_modules" ]; then
    echo "   Cleaning existing node_modules..."
    sudo rm -rf node_modules 2>/dev/null || rm -rf node_modules
fi

# Install npm packages with progress
echo "   Installing npm packages (this may take a few minutes)..."
npm install --loglevel info

cd ..

echo "   ✅ Frontend dependencies installed"
echo ""

# ------------------------------------------------------------------------------
# Step 3: Create Required Directories
# ------------------------------------------------------------------------------
echo "📁 Step 3/6: Creating required directories..."

# Use sudo if needed for permission issues with mounted volumes
sudo mkdir -p data data/parquet_snapshots lineage_output logs uploads temp 2>/dev/null || \
    mkdir -p data data/parquet_snapshots lineage_output logs uploads temp

# Ensure vscode user owns the directories
sudo chown -R vscode:vscode data lineage_output logs uploads temp 2>/dev/null || true

echo "   ✅ Directories created"
echo ""

# ------------------------------------------------------------------------------
# Step 4: Copy .env.example to .env (if not exists)
# ------------------------------------------------------------------------------
echo "⚙️  Step 4/6: Setting up environment configuration..."

if [ ! -f ".env" ]; then
    echo "   Copying .env.example to .env..."
    cp .env.example .env 2>/dev/null || sudo cp .env.example .env
    sudo chown vscode:vscode .env 2>/dev/null || true
    echo "   ⚠️  Please review .env and update configuration as needed"
else
    echo "   ✅ .env file already exists"
fi

echo ""

# ------------------------------------------------------------------------------
# Step 5: Git Configuration
# ------------------------------------------------------------------------------
echo "🔧 Step 5/6: Configuring git..."

# Configure git safe directory
git config --global --add safe.directory /workspace

# Set git editor to VS Code (if available)
if command -v code &> /dev/null; then
    git config --global core.editor "code --wait"
fi

# Enable git colors
git config --global color.ui auto

echo "   ✅ Git configured"
echo ""

# ------------------------------------------------------------------------------
# Step 6: Pre-commit Hooks (optional)
# ------------------------------------------------------------------------------
echo "🪝 Step 6/6: Setting up development tools..."

# Install pre-commit if available
if pip show pre-commit &> /dev/null; then
    echo "   Installing pre-commit hooks..."
    pre-commit install --install-hooks 2>/dev/null || echo "   ⚠️  Pre-commit not configured (optional)"
else
    echo "   ℹ️  Pre-commit not installed (optional)"
fi

echo "   ✅ Development tools configured"
echo ""

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ Dev Environment Setup Complete!                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Next Steps:"
echo "   1. Review .env file and update configuration"
echo "   2. Run backend:  ./start-app.sh"
echo "   3. Or use VS Code tasks: Ctrl+Shift+P > 'Tasks: Run Task'"
echo ""
echo "🌐 Development URLs:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Useful Commands:"
echo "   Backend tests:   pytest tests/"
echo "   Frontend dev:    cd frontend && npm run dev"
echo "   Frontend build:  cd frontend && npm run build"
echo ""
