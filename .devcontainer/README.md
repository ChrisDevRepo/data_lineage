# VS Code Dev Container - Data Lineage Visualizer

## 🚀 Quick Start

This project includes a complete VS Code Dev Container configuration for instant, reproducible development environments.

### Prerequisites

1. **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
2. **VS Code** - [Download](https://code.visualstudio.com/)
3. **Dev Containers Extension** - Install from VS Code marketplace: `ms-vscode-remote.remote-containers`

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd data_lineage
   ```

2. **Open in VS Code:**
   ```bash
   code .
   ```

3. **Reopen in Container:**
   - Press `F1` or `Ctrl+Shift+P`
   - Type: `Dev Containers: Reopen in Container`
   - Wait for container to build (first time: 5-10 minutes)

4. **Everything is ready!**
   - Python environment with all dependencies
   - Frontend dependencies installed
   - VS Code extensions pre-installed
   - Debugging configured
   - Tasks ready to use

---

## 📦 What's Included

### Development Tools

**Python Environment:**
- Python 3.12
- All project dependencies (FastAPI, DuckDB, pandas, etc.)
- Development tools: pytest, black, isort, pylint
- Debugging support with debugpy

**Frontend Environment:**
- Node.js 20 LTS
- npm/pnpm/yarn
- React development dependencies
- Tailwind CSS tooling

**Database Drivers:**
- Microsoft ODBC Driver 17 for SQL Server
- Support for Azure Synapse, Azure SQL, SQL Server, and Fabric

**VS Code Extensions:**
- Python: Pylance, Black formatter, isort, debugpy
- JavaScript/React: ESLint, Prettier, React snippets, Tailwind IntelliSense
- API Testing: REST Client, Thunder Client
- Docker, Git, YAML, Markdown support

### Pre-configured Tasks

Access via `Ctrl+Shift+P` → `Tasks: Run Task`

- **Start Backend (FastAPI)** - Launch backend server with hot reload
- **Start Frontend (React)** - Launch Vite dev server
- **Start Full Stack** - Launch both backend and frontend
- **Run Tests (All)** - Run all pytest tests
- **Run Tests (Unit Only)** - Run unit tests only
- **Build Frontend** - Build production frontend bundle
- **Format Python Code** - Run Black formatter
- **Sort Python Imports** - Run isort
- **Clean Build Artifacts** - Remove build files and caches

### Debugging Configurations

Access via `F5` or Debug panel

- **Python: FastAPI Backend** - Debug FastAPI with breakpoints
- **Python: Current File** - Debug currently open Python file
- **Python: Pytest (Current File)** - Debug current test file
- **Python: Pytest (All Tests)** - Debug all tests
- **Python: Parser Script** - Debug parser validation script
- **Attach to FastAPI (Remote)** - Attach to running FastAPI instance

---

## 🎯 Common Workflows

### Starting Development

```bash
# Backend only
Ctrl+Shift+P → Tasks: Run Task → Start Backend (FastAPI)
# Opens at http://localhost:8000

# Frontend only
Ctrl+Shift+P → Tasks: Run Task → Start Frontend (React)
# Opens at http://localhost:3000

# Both (Full Stack)
Ctrl+Shift+P → Tasks: Run Task → Start Full Stack (Backend + Frontend)
```

### Running Tests

```bash
# Via Task
Ctrl+Shift+P → Tasks: Run Task → Run Tests (All)

# Via Terminal
source venv/bin/activate
pytest tests/ -v
```

### Debugging

1. Set breakpoints in your code (click left gutter)
2. Press `F5` or go to Debug panel
3. Select configuration: "Python: FastAPI Backend"
4. Start debugging

### Formatting Code

```bash
# Auto-format on save (already configured)
# Or manually:
Ctrl+Shift+P → Tasks: Run Task → Format Python Code (Black)
```

---

## 📁 Dev Container Structure

```
.devcontainer/
├── devcontainer.json       # Main configuration
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Services configuration
├── post-create.sh          # Runs once after container creation
├── post-start.sh           # Runs on every container start
└── README.md               # This file
```

### File Details

**devcontainer.json**
- Container configuration
- VS Code settings and extensions
- Port forwarding (8000, 3000)
- Environment variables
- Post-creation commands

**Dockerfile**
- Base image: Debian 12
- Python 3.12 + Node.js 20
- ODBC drivers for SQL Server
- Development tools

**docker-compose.yml**
- Service definition
- Volume mounts for persistence
- Network configuration
- Environment variables

**post-create.sh**
- Installs Python dependencies
- Installs frontend dependencies
- Creates required directories
- Sets up .env file
- Configures git

**post-start.sh**
- Displays environment info
- Shows quick start commands
- Checks configuration

---

## 🔧 Customization

### Environment Variables

Edit `.devcontainer/docker-compose.yml` to change environment variables:

```yaml
environment:
  LOG_LEVEL: DEBUG          # Change to INFO for production-like
  RUN_MODE: debug           # Options: debug | demo | production
  SQL_DIALECT: tsql         # Database dialect
  DB_ENABLED: "false"       # Enable database connection
```

### VS Code Settings

Edit `.devcontainer/devcontainer.json` under `customizations.vscode.settings`:

```json
"settings": {
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  // Add your custom settings
}
```

### Additional Extensions

Add to `.devcontainer/devcontainer.json` under `customizations.vscode.extensions`:

```json
"extensions": [
  "ms-python.python",
  "your-extension-id"
]
```

---

## 🐛 Troubleshooting

### Container Build Fails

**Issue:** Build fails during creation

**Solution:**
1. Check Docker is running: `docker ps`
2. Rebuild container:
   - `Ctrl+Shift+P` → `Dev Containers: Rebuild Container`
3. Check Docker logs in VS Code Output panel

### Ports Already in Use

**Issue:** Port 8000 or 3000 already in use

**Solution:**
```bash
# Find process using port
lsof -i :8000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

### Python Dependencies Not Found

**Issue:** `ModuleNotFoundError` when running code

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Or run task
Ctrl+Shift+P → Tasks: Run Task → Install Python Dependencies
```

### Frontend Dependencies Not Found

**Issue:** `npm` errors or missing packages

**Solution:**
```bash
cd frontend
npm install

# Or run task
Ctrl+Shift+P → Tasks: Run Task → Install Frontend Dependencies
```

### ODBC Driver Issues

**Issue:** Database connection fails with "ODBC Driver not found"

**Solution:**
1. Rebuild container (includes ODBC driver installation)
2. Check driver installed:
   ```bash
   odbcinst -q -d
   # Should show "ODBC Driver 18 for SQL Server"
   ```

### Permission Issues

**Issue:** Permission denied errors

**Solution:**
```bash
# Container runs as 'vscode' user
# For sudo access:
sudo <command>
```

---

## 📊 Performance Tips

### Faster Rebuilds

Dev container uses named volumes to persist:
- Python virtual environment (`venv/`)
- Node modules (`frontend/node_modules/`)
- Bash history
- DuckDB data
- Uploads

These persist across rebuilds, making subsequent builds much faster.

### Clearing Volumes

To start fresh:

```bash
# Stop container
# From VS Code: Dev Containers: Close Remote Connection

# Remove volumes
docker volume rm datalineage-venv
docker volume rm datalineage-node-modules
docker volume rm datalineage-data

# Rebuild
# From VS Code: Dev Containers: Rebuild Container
```

---

## 🌐 Accessing Services

Once the container is running:

| Service | URL | Description |
|---------|-----|-------------|
| **Backend API** | http://localhost:8000 | FastAPI application |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | Health endpoint |
| **Frontend Dev** | http://localhost:3000 | Vite dev server |

---

## 💡 Tips & Best Practices

### 1. Use Tasks Instead of Terminal Commands

Tasks are pre-configured and easier to run:
- `Ctrl+Shift+P` → `Tasks: Run Task`

### 2. Format on Save

Already configured! Just save files for auto-formatting.

### 3. Use Debugger Instead of Print Statements

Set breakpoints and press `F5` - much more powerful than `print()`.

### 4. Terminal Selection

Use integrated terminal:
- `` Ctrl+` `` to open/close terminal
- Terminal is already in the container
- Virtual environment pre-activated in scripts

### 5. Git from Container

Git is configured and ready:
```bash
git status
git add .
git commit -m "Your message"
git push
```

### 6. Keep Container Running

Don't rebuild unless necessary:
- Container persists dependencies in volumes
- Rebuilding is slow (5-10 minutes)
- Only rebuild for Dockerfile/devcontainer.json changes

---

## 📚 Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Specification](https://containers.dev/)
- [Dev Container Templates](https://containers.dev/templates)
- [Python Dev Container](https://github.com/microsoft/vscode-remote-try-python)

---

## 🤝 Contributing

When contributing, ensure:
1. Dev container builds successfully
2. All tests pass: `pytest tests/ -v`
3. Code is formatted: Black + isort (auto on save)
4. Environment variables documented in `.env.example`

---

**Questions or Issues?**

- Check [Troubleshooting](#-troubleshooting) section
- Open an issue in the repository
- Review VS Code Dev Containers documentation

---

**Happy Coding! 🚀**
