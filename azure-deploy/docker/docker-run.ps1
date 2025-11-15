# ==============================================================================
# Docker Run Script - Windows PowerShell
# ==============================================================================
# Builds and runs the Docker container for local testing
# ==============================================================================

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🐳 Data Lineage Visualizer - Docker Build & Run              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "🔍 Checking Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Build frontend
Write-Host "📦 Building frontend..." -ForegroundColor Yellow
Set-Location ..\..\frontend
npm install
npm run build
Set-Location ..\azure-deploy\docker
Write-Host "✅ Frontend built" -ForegroundColor Green
Write-Host ""

# Build Docker image
Write-Host "🐳 Building Docker image..." -ForegroundColor Yellow
docker build -t datalineage:latest -f Dockerfile ..\..
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker image built: datalineage:latest" -ForegroundColor Green
Write-Host ""

# Stop existing container if running
Write-Host "🛑 Stopping existing container (if any)..." -ForegroundColor Yellow
docker stop datalineage-app 2>$null
docker rm datalineage-app 2>$null
Write-Host ""

# Run container
Write-Host "🚀 Starting container..." -ForegroundColor Yellow
docker run -d `
    --name datalineage-app `
    -p 8000:8000 `
    -e ALLOWED_ORIGINS="*" `
    -e PATH_OUTPUT_DIR="/app/data" `
    -e LOG_LEVEL="INFO" `
    -v datalineage-data:/app/data `
    datalineage:latest

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container started: datalineage-app" -ForegroundColor Green
Write-Host ""

# Wait for health check
Write-Host "⏳ Waiting for application to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$ready = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}
Write-Host ""

if ($ready) {
    Write-Host "✅ Application is ready!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Application may still be starting..." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✅ Container Running                                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Application URLs:" -ForegroundColor White
Write-Host "   App:      http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Health:   http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Container Commands:" -ForegroundColor White
Write-Host "   View logs:  docker logs -f datalineage-app" -ForegroundColor Gray
Write-Host "   Stop:       docker stop datalineage-app" -ForegroundColor Gray
Write-Host "   Remove:     docker rm datalineage-app" -ForegroundColor Gray
Write-Host ""

# Open browser
$openBrowser = Read-Host "Open browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost:8000"
}
