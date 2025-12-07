#!/bin/bash
set -e

# ==============================================================================
# Azure Container Apps Deployment Script
# Author: Christian Wagner
# Version: 1.0.1
# ==============================================================================
# Smart deployment: Detects existing resources and updates them
# Handles both initial deployment and updates
# Supports optional Azure AD authentication
# ==============================================================================

# ==============================================================================
# CONFIGURATION PARAMETERS
# ==============================================================================
# Customize these parameters for your deployment
PREFIX="${PREFIX:-demo}"                          # Resource prefix (default: demo)
LOCATION="${LOCATION:-westeurope}"                # Azure region
SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-}"            # Leave empty to use default subscription
ENABLE_AUTH="${ENABLE_AUTH:-false}"               # Enable Azure AD authentication (true/false)
TENANT_ID="${TENANT_ID:-}"                        # Azure AD Tenant ID (required if ENABLE_AUTH=true)

# Derived resource names
RESOURCE_GROUP="rg-${PREFIX}-datalineage"
ACR_NAME="${PREFIX}datalineage"                   # Must be globally unique, lowercase, no hyphens
CONTAINER_APP_NAME="${PREFIX}-datalineage-app"
CONTAINER_ENV_NAME="${PREFIX}-datalineage-env"
LOG_ANALYTICS_NAME="${PREFIX}-datalineage-logs"

# Application configuration
IMAGE_NAME="datalineage"
VERSION="1.0.1"

# ==============================================================================
# SCRIPT START
# ==============================================================================
echo ""
echo "Data Lineage Visualizer - Azure Deployment v$VERSION"
echo "======================================================"
echo ""
echo "Configuration:"
echo "  Prefix:         $PREFIX"
echo "  Location:       $LOCATION"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  ACR:            $ACR_NAME"
echo "  Container App:  $CONTAINER_APP_NAME"
echo ""

# Set subscription if provided
if [ -n "$SUBSCRIPTION_ID" ]; then
    echo "Setting subscription: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Show current subscription
CURRENT_SUB=$(az account show --query name -o tsv)
echo "Using subscription: $CURRENT_SUB"
echo ""

# Validate authentication configuration
if [ "$ENABLE_AUTH" = "true" ]; then
    echo "Authentication: ENABLED (Azure AD)"
    if [ -z "$TENANT_ID" ]; then
        echo "ERROR: TENANT_ID required when ENABLE_AUTH=true"
        echo "Get tenant ID with: az account show --query tenantId -o tsv"
        exit 1
    fi
    echo "  Tenant ID: $TENANT_ID"
else
    echo "Authentication: DISABLED (public access)"
fi
echo ""

# ==============================================================================
# Step 1: Create Resource Group
# ==============================================================================
echo "[1/8] Resource Group..."
if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    echo "      Already exists"
else
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
    echo "      Created"
fi

# ==============================================================================
# Step 2: Create Azure Container Registry
# ==============================================================================
echo "[2/8] Azure Container Registry..."
if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo "      Already exists"
else
    az acr create \
        --name "$ACR_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Basic \
        --admin-enabled true \
        --output none
    echo "      Created"
fi
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)

# ==============================================================================
# Step 3: Create Log Analytics Workspace
# ==============================================================================
echo "[3/8] Log Analytics Workspace..."
if az monitor log-analytics workspace show --resource-group "$RESOURCE_GROUP" --workspace-name "$LOG_ANALYTICS_NAME" &>/dev/null; then
    echo "      Already exists"
else
    az monitor log-analytics workspace create \
        --resource-group "$RESOURCE_GROUP" \
        --workspace-name "$LOG_ANALYTICS_NAME" \
        --location "$LOCATION" \
        --output none
    echo "      Created"
fi

LOG_ANALYTICS_ID=$(az monitor log-analytics workspace show \
    --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_ANALYTICS_NAME" \
    --query customerId -o tsv)

LOG_ANALYTICS_KEY=$(az monitor log-analytics workspace get-shared-keys \
    --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_ANALYTICS_NAME" \
    --query primarySharedKey -o tsv)

# ==============================================================================
# Step 4: Create Container Apps Environment
# ==============================================================================
echo "[4/8] Container Apps Environment..."
if az containerapp env show --name "$CONTAINER_ENV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo "      Already exists"
else
    az containerapp env create \
        --name "$CONTAINER_ENV_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --logs-workspace-id "$LOG_ANALYTICS_ID" \
        --logs-workspace-key "$LOG_ANALYTICS_KEY" \
        --output none
    echo "      Created"
fi

# ==============================================================================
# Step 5: Build Frontend
# ==============================================================================
echo "[5/8] Building frontend..."
cd frontend
npm install --silent
npm run build --silent
cd ..
echo "      Done"

# ==============================================================================
# Step 6: Build and Push Docker Image
# ==============================================================================
echo "[6/8] Building Docker image..."
docker build -t $IMAGE_NAME:$VERSION -f .azure-deploy/docker/Dockerfile . -q
docker tag $IMAGE_NAME:$VERSION $ACR_LOGIN_SERVER/$IMAGE_NAME:$VERSION
docker tag $IMAGE_NAME:$VERSION $ACR_LOGIN_SERVER/$IMAGE_NAME:latest
echo "      Done"

echo "[7/8] Pushing to ACR..."
az acr login --name $ACR_NAME --output none
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$VERSION > /dev/null 2>&1
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:latest > /dev/null 2>&1
echo "      Done"

# ==============================================================================
# Step 7: Get ACR Credentials
# ==============================================================================
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# ==============================================================================
# Step 8: Create/Update Container App
# ==============================================================================
echo "[8/8] Deploying Container App..."
if az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo "      Updating existing app..."
    az containerapp update \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$VERSION" \
        --output none
    echo "      Updated"
else
    echo "      Creating new app..."
    az containerapp create \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$CONTAINER_ENV_NAME" \
        --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$VERSION" \
        --registry-server "$ACR_LOGIN_SERVER" \
        --registry-username "$ACR_USERNAME" \
        --registry-password "$ACR_PASSWORD" \
        --target-port 8000 \
        --ingress external \
        --cpu 1.0 \
        --memory 2.0Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --env-vars \
            "ALLOWED_ORIGINS=*" \
            "LOG_LEVEL=INFO" \
            "RUN_MODE=production" \
            "SQL_DIALECT=tsql" \
        --output none
    echo "      Created"
fi

# ==============================================================================
# Get Application URL
# ==============================================================================
APP_URL=$(az containerapp show \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.configuration.ingress.fqdn -o tsv)

# ==============================================================================
# Configure Authentication (if enabled)
# ==============================================================================
if [ "$ENABLE_AUTH" = "true" ]; then
    echo ""
    echo "Configuring Azure AD authentication..."

    AUTH_ENABLED=$(az containerapp auth show \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "platform.enabled" -o tsv 2>/dev/null || echo "false")

    if [ "$AUTH_ENABLED" = "true" ]; then
        echo "  Already configured"
    else
        az containerapp auth microsoft update \
            --name "$CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --tenant-id "$TENANT_ID" \
            --client-id-setting-name "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET" \
            --yes \
            --output none 2>/dev/null || {

            echo "  Manual configuration required:"
            echo "  1. Portal > $CONTAINER_APP_NAME > Authentication"
            echo "  2. Add Microsoft provider (Tenant: $TENANT_ID)"
            echo "  3. Require authentication"
        }

        az containerapp update \
            --name "$CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --set-env-vars "ALLOWED_ORIGINS=https://$APP_URL" \
            --output none

        echo "  Done"
    fi
fi

# ==============================================================================
# Deployment Summary
# ==============================================================================
echo ""
echo "======================================================"
echo "Deployment Complete"
echo "======================================================"
echo ""
echo "Application URL:"
echo "  https://$APP_URL"
echo ""
echo "Resources:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  ACR:            $ACR_NAME"
echo "  Container App:  $CONTAINER_APP_NAME"
echo "  Authentication: $([ "$ENABLE_AUTH" = "true" ] && echo "ENABLED (Azure AD)" || echo "DISABLED")"
echo ""
echo "Useful commands:"
echo "  View logs:"
echo "    az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "  Update deployment:"
if [ "$ENABLE_AUTH" = "true" ]; then
echo "    ENABLE_AUTH=true TENANT_ID=$TENANT_ID PREFIX=$PREFIX ./deploy.sh"
else
echo "    PREFIX=$PREFIX ./deploy.sh"
fi
echo ""
