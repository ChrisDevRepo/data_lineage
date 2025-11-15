#!/bin/bash
# ==============================================================================
# Azure Web App ZIP Deployment Script
# ==============================================================================
# This script deploys the Data Lineage Visualizer to Azure Web App
# using ZIP Deploy API with authentication to trigger proper build.
# ==============================================================================

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Azure Web App ZIP Deployment                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIP_FILE="$SCRIPT_DIR/lineage-visualizer-azure.zip"

# Check if ZIP exists, if not offer to build it
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
echo "   Path: $ZIP_FILE"
echo ""

# Prompt for Azure Web App details
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Azure Web App Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "App Name (e.g., chwa-datalineage): " APP_NAME
if [ -z "$APP_NAME" ]; then
    echo "❌ App name is required"
    exit 1
fi

read -p "Region (e.g., swedencentral-01): " REGION
if [ -z "$REGION" ]; then
    echo "❌ Region is required"
    exit 1
fi

echo ""
echo "Get deployment credentials from Azure Portal:"
echo "  → Your Web App → Deployment Center → FTPS credentials"
echo ""

read -p "Username (e.g., \$chwa-datalineage): " USERNAME
if [ -z "$USERNAME" ]; then
    echo "❌ Username is required"
    exit 1
fi

read -sp "Password: " PASSWORD
echo ""
if [ -z "$PASSWORD" ]; then
    echo "❌ Password is required"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Deployment Target:"
echo "   App: $APP_NAME"
echo "   URL: https://$APP_NAME.azurewebsites.net"
echo "   SCM: https://$APP_NAME.scm.$REGION.azurewebsites.net"
echo "   User: $USERNAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Deploy ZIP file to Azure? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Deploying ZIP File..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build the ZIP Deploy API URL
API_URL="https://$APP_NAME.scm.$REGION.azurewebsites.net/api/zipdeploy?isAsync=true"

echo "📤 Uploading ZIP to Azure..."
echo "   Endpoint: /api/zipdeploy?isAsync=true"
echo "   Method: POST with Basic Auth"
echo ""

# Deploy ZIP using curl with authentication
RESPONSE=$(curl -X POST "$API_URL" \
    -u "$USERNAME:$PASSWORD" \
    -H "Content-Type: application/zip" \
    --data-binary @"$ZIP_FILE" \
    -w "\nHTTP_STATUS:%{http_code}" \
    -s 2>&1)

# Extract HTTP status code
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$HTTP_STATUS" = "202" ] || [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ ZIP Deployment Successful!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Response:"
    echo "   HTTP Status: $HTTP_STATUS Accepted"
    if [ -n "$RESPONSE_BODY" ]; then
        echo "   Details: $RESPONSE_BODY"
    fi
    echo ""
    echo "⏳ Azure Build Process (3-5 minutes):"
    echo "   1. Extracting ZIP file"
    echo "   2. Detecting Python 3.11 runtime"
    echo "   3. Running Oryx build"
    echo "   4. Installing pip dependencies"
    echo "   5. Creating virtual environment"
    echo "   6. Starting application"
    echo ""
    echo "📍 Monitor Deployment:"
    echo "   Open: https://$APP_NAME.scm.$REGION.azurewebsites.net"
    echo "   Go to: Deployments (left menu)"
    echo "   Status: Wait for 'Success (Active)'"
    echo ""
    echo "🔍 View Build Logs:"
    echo "   Azure Portal → $APP_NAME → Deployment Center → Logs"
    echo ""
    echo "✅ Test Endpoints (after build completes):"
    echo "   Health: https://$APP_NAME.azurewebsites.net/health"
    echo "   API Docs: https://$APP_NAME.azurewebsites.net/docs"
    echo "   App: https://$APP_NAME.azurewebsites.net"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ ZIP Deployment Failed!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "   HTTP Status: $HTTP_STATUS"
    echo "   Response: $RESPONSE_BODY"
    echo ""
    echo "🔍 Common Issues:"
    echo "   • 401: Wrong username/password"
    echo "   • 404: Wrong app name or region"
    echo "   • 409: Deployment already in progress"
    echo "   • 500: Azure internal error"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Verify credentials in Portal → Deployment Center"
    echo "   2. Check app name matches exactly"
    echo "   3. Confirm region (check SCM URL in Portal)"
    echo "   4. Try again in a few minutes"
    echo ""
    exit 1
fi

echo ""
