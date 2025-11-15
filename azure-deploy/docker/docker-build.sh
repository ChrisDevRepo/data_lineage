#!/bin/bash
# ==============================================================================
# Docker Build Script - Local Testing
# ==============================================================================
# Builds the Docker image for local testing before deploying to Azure
# ==============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🐳 Building Docker Image                                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Build frontend first
echo "📦 Building frontend..."
cd ../../frontend
npm install
npm run build
cd ../azure-deploy/docker
echo "✅ Frontend built"
echo ""

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t datalineage:latest -f Dockerfile ../..
echo "✅ Docker image built: datalineage:latest"
echo ""

# Show image size
IMAGE_SIZE=$(docker images datalineage:latest --format "{{.Size}}")
echo "📊 Image size: $IMAGE_SIZE"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ Build Complete                                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Run locally with:"
echo "   docker run -p 8000:8000 datalineage:latest"
echo ""
echo "🚀 Or use Docker Compose:"
echo "   docker-compose up"
echo ""
echo "🌐 Access the app at:"
echo "   http://localhost:8000"
echo ""
