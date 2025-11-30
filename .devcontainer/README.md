# Dev Container - Data Lineage Visualizer

## Quick Start

**Prerequisites:** Docker Desktop + VS Code + Dev Containers extension

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
- All dependencies pre-installed
- VS Code extensions configured

**Pre-configured Tasks:** (`Ctrl+Shift+P` → `Tasks: Run Task`)
- Start Backend / Frontend / Full Stack
- Build Frontend (production)
- Format Code (Black + isort)
- Run Tests

**Debugging:** Press `F5` → Select "Python: FastAPI Backend"

---

## Project-Specific Configuration

### Environment Variables

Located in `.devcontainer/docker-compose.yml`:

```yaml
environment:
  LOG_LEVEL: INFO                    # DEBUG for development
  RUN_MODE: debug                    # debug | demo | production
  SQL_DIALECT: tsql                  # Currently: tsql only
  EXCLUDED_SCHEMAS: sys,information_schema,tempdb
```

### Volume Persistence

Persisted across rebuilds:
- `venv/` - Python dependencies
- `frontend/node_modules/` - npm packages
- DuckDB workspace database
- Bash history

**Clear volumes:** Stop container → `docker volume rm datalineage-venv datalineage-node-modules datalineage-data`

---

## 🚀 Azure Deployment

The Dev Container Dockerfile serves as the foundation for Azure deployment.

### Deployment Options

**1. Azure Container Apps** (Recommended)
- Fully managed, auto-scaling
- HTTPS ingress + Azure AD auth
- Managed identity for secure database access

**2. Azure Container Instances**
- Serverless, pay-per-second
- Quick testing deployments

**3. Azure App Service (Containers)**
- Managed hosting + built-in CI/CD

### Build Production Image

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Build Docker image
docker build -t datalineage:latest -f .devcontainer/Dockerfile .

# Test locally
docker run -p 8000:8000 datalineage:latest
```

### Production Environment Variables

```bash
ALLOWED_ORIGINS=https://your-domain.com
PATH_OUTPUT_DIR=/app/data
LOG_LEVEL=INFO
RUN_MODE=production
SQL_DIALECT=tsql
```

### Best Practices

**Security:**
- ✅ Use Azure Key Vault for connection strings
- ✅ Enable managed identity (no hardcoded credentials)
- ✅ Azure AD authentication for user access
- ✅ Private endpoints for database connections
- ✅ Scan images for vulnerabilities

**Optimization:**
- Consider separate production Dockerfile (multi-stage build)
- Remove dev tools (pytest, debugpy, ipython)
- Minimize image size
- Configure appropriate CPU/memory (0.5-2 cores, 1-4 Gi)

**Monitoring:**
- Application Insights for telemetry
- Container logs for diagnostics

---

## Troubleshooting

**Container build fails:**
- Check Docker running: `docker ps`
- Rebuild: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

**Ports in use:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

**Dependencies not found:**
```bash
# Python
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

**ODBC Driver issues:**
- Rebuild container (includes driver installation)
- Verify: `odbcinst -q -d` (should show "ODBC Driver 18 for SQL Server")

---

## Container Structure

```
.devcontainer/
├── devcontainer.json    # VS Code config, extensions, environment
├── Dockerfile           # Debian 12 + Python 3.11 + Node 20 + ODBC 18
├── docker-compose.yml   # Services, volumes, networks
├── post-create.sh       # Runs once after creation (install deps)
└── post-start.sh        # Runs on every start (show info)
```

**Key Files:**
- **Dockerfile** - Base: Debian 12, Python 3.11, Node 20, ODBC Driver 18
- **devcontainer.json** - Port forwarding (8000, 3000), extensions, settings
- **docker-compose.yml** - Volumes for persistence, environment variables

---

## Tips

1. **Use Tasks** - Pre-configured for common operations (`Ctrl+Shift+P` → Tasks)
2. **Format on Save** - Already configured (Black + isort)
3. **Debug with F5** - More powerful than print statements
4. **Keep Container Running** - Only rebuild for Dockerfile changes (slow)
5. **Volumes Persist** - Dependencies cached between rebuilds

---

## Resources

- **Project Docs:** [DEVELOPMENT.md](../docs/DEVELOPMENT.md) - Full development guide
- **Configuration:** [CONFIGURATION.md](../docs/CONFIGURATION.md) - Environment variables

---

**Built with:** Python 3.11 • Node.js 20 • ODBC Driver 18 • Debian 12
