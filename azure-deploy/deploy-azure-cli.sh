#!/bin/bash
# ==============================================================================
# Azure CLI Deployment Script (Recommended Method)
# ==============================================================================
# This script deploys the Data Lineage Visualizer to Azure Web App
# using Azure CLI for reliable deployment with proper build automation.
# ==============================================================================

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Azure Web App Deployment (Azure CLI)                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIP_FILE="$SCRIPT_DIR/lineage-visualizer-azure.zip"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found"
    echo ""
    echo "Install Azure CLI:"
    echo "  • Windows: https://aka.ms/installazurecliwindows"
    echo "  • macOS: brew install azure-cli"
    echo "  • Linux: https://docs.microsoft.com/cli/azure/install-azure-cli-linux"
    echo ""
    exit 1
fi

echo "✅ Azure CLI found: $(az version --query '\"azure-cli\"' -o tsv 2>/dev/null || echo 'installed')"
echo ""

# Check if ZIP exists
if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ Deployment package not found: $ZIP_FILE"
    echo ""
    read -p "Build deployment package now? (y/n): " BUILD_NOW
    if [ "$BUILD_NOW" = "y" ] || [ "$BUILD_NOW" = "Y" ]; then
        echo ""
        bash "$SCRIPT_DIR/create-deployment-package.sh"
        if [ ! -f "$ZIP_FILE" ]; then
            echo "❌ Failed to create deployment package"
            exit 1
        fi
    else
        echo "❌ Cannot deploy without package. Run: bash create-deployment-package.sh"
        exit 1
    fi
fi

echo "📦 Deployment Package Ready:"
echo "   File: $(basename $ZIP_FILE)"
echo "   Size: $(du -h $ZIP_FILE | cut -f1)"
echo ""

# Check Azure login status
echo "🔐 Checking Azure login..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure"
    echo ""
    echo "Logging in to Azure..."
    az login
    echo ""
fi

ACCOUNT=$(az account show --query name -o tsv)
echo "✅ Logged in as: $ACCOUNT"
echo ""

# Prompt for deployment details
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Deployment Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Resource Group (e.g., rg-chwa-app): " RESOURCE_GROUP
if [ -z "$RESOURCE_GROUP" ]; then
    echo "❌ Resource group is required"
    exit 1
fi

read -p "App Name (e.g., chwa-datalineage): " APP_NAME
if [ -z "$APP_NAME" ]; then
    echo "❌ App name is required"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Deployment Target:"
echo "   Subscription: $ACCOUNT"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Name: $APP_NAME"
echo "   Package: $(basename $ZIP_FILE) ($(du -h $ZIP_FILE | cut -f1))"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Deploy to Azure? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Deploying to Azure..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ensure build automation is enabled
echo "⚙️  Ensuring build automation is enabled..."
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    --output none

echo "✅ Build automation enabled"
echo ""

# Deploy the ZIP file
echo "📤 Uploading ZIP package..."
az webapp deploy \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --src-path "$ZIP_FILE" \
    --type zip

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment Completed Successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get the app URL
APP_URL=$(az webapp show --resource-group "$RESOURCE_GROUP" --name "$APP_NAME" --query defaultHostName -o tsv)

echo "🌐 Application URL:"
echo "   https://$APP_URL"
echo ""

echo "✅ Test Endpoints:"
echo "   Health:   https://$APP_URL/health"
echo "   API Docs: https://$APP_URL/docs"
echo "   App:      https://$APP_URL"
echo ""

echo "📊 Verify Deployment:"
read -p "Test health endpoint now? (y/n): " TEST_NOW
if [ "$TEST_NOW" = "y" ] || [ "$TEST_NOW" = "Y" ]; then
    echo ""
    echo "Testing health endpoint..."
    sleep 5  # Give it a moment to start
    
    if command -v curl &> /dev/null; then
        HEALTH_RESPONSE=$(curl -s "https://$APP_URL/health" || echo '{"error":"Connection failed"}')
        echo ""
        echo "Health Response:"
        echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
    else
        echo "curl not found - please test manually"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 Next Steps:"
echo ""
echo "  1. Configure application settings (if first deployment):"
echo "     • ALLOWED_ORIGINS"
echo "     • PATH_WORKSPACE_FILE"
echo "     • PATH_OUTPUT_DIR"
echo "     • PATH_PARQUET_DIR"
echo ""
echo "  2. View logs:"
echo "     az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo ""
echo "  3. Monitor in Azure Portal:"
echo "     https://portal.azure.com → $APP_NAME"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
