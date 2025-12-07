# Dev Container Setup

VSCode development environment with Python, Node.js, and SQL Server tooling.

**Version:** 1.0.1 • **Author:** Christian Wagner

---

## Quick Start

**Prerequisites:** Docker Desktop, VS Code, Dev Containers extension

1. Open project in VS Code: `code .`
2. `F1` → "Dev Containers: Reopen in Container"
3. Wait for build (10-15 min first time)
4. Start development: `Ctrl+Shift+P` → `Tasks: Run Task` → `Start Full Stack`

**Access:** http://localhost:8000 (API) • http://localhost:3000 (Frontend)

---

## What's Included

**Environment:**
- Python 3.11 + Node.js 20
- Microsoft ODBC Driver 18 for SQL Server
- All Python/Node dependencies pre-installed
- VS Code extensions configured

**Pre-configured Tasks:** (`Ctrl+Shift+P` → `Tasks: Run Task`)
- Start Backend / Frontend / Full Stack
- Build Frontend (production)
- Format Code (Black + isort)
- Run Tests

**Debugging:** Press `F5` → Select "Python: FastAPI Backend"

---

## Configuration

Environment variables are auto-configured on first run. Edit `.env` in workspace root to customize.

---

## Development Workflow

### Start Services

```bash
# Backend only (port 8000)
Ctrl+Shift+P → Tasks: Run Task → Start Backend

# Frontend only (port 3000)
Ctrl+Shift+P → Tasks: Run Task → Start Frontend

# Both services
Ctrl+Shift+P → Tasks: Run Task → Start Full Stack
```

### Code Formatting

```bash
Ctrl+Shift+P → Tasks: Run Task → Format Code
```

Runs Black (Python) and isort (imports) on all code.

---

## Troubleshooting

### Container Build Fails

```bash
# Check Docker running
docker ps

# Rebuild container
Ctrl+Shift+P → "Dev Containers: Rebuild Container"
```

### Ports Already in Use

**Windows:**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -i :8000
kill -9 <PID>
```

### ODBC Driver Issues

Rebuild container - ODBC Driver 18 installed automatically.

Verify: `odbcinst -q -d`

---

## Deployment Options

### Production Deployment

See deployment-specific READMEs:
- **[.docker/README.md](../.docker/README.md)** - Local Docker production deployment
- **[.azure-deploy/README.md](../.azure-deploy/README.md)** - Azure Container Apps deployment

### Container Structure

```
.devcontainer/
├── Dockerfile           # Debian 12 + Python 3.11 + Node 20 + ODBC 18
├── devcontainer.json    # VS Code config, extensions, environment
├── post-create.sh       # Runs once after creation
├── post-start.sh        # Runs on every start
└── README.md            # This file
```

---

**Status:** Development Ready • **Maintainer:** Christian Wagner
