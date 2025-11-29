# Development Setup Guide

**Data Lineage Visualizer** - Development Environment Setup

This guide covers the recommended development environment setup using VS Code Dev Containers.

---

## 🚀 VS Code Dev Container Setup (Recommended)

**⏱️ Time to Start:** 10-15 minutes (includes Docker build)

The fastest way to get started! Uses VS Code Dev Containers for a fully configured, reproducible development environment.

### Prerequisites

- Docker Desktop installed
- VS Code installed with "Dev Containers" extension (`ms-vscode-remote.remote-containers`)

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd data_lineage
   ```

2. **Open in VS Code:**
   ```bash
   code .
   ```

3. **Reopen in Container:**
   - Press `F1` (or `Ctrl+Shift+P` / `Cmd+Shift+P`)
   - Type and select: `Dev Containers: Reopen in Container`
   - Wait for container to build (first time only: 10-15 minutes)

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
- Python 3.11
- All project dependencies (FastAPI, DuckDB, pandas, etc.)
- Development tools: black, isort, pylint
- Debugging support with debugpy

**Frontend Environment:**
- Node.js 20 LTS
- npm/pnpm/yarn
- React development dependencies
- Tailwind CSS tooling

**Database Drivers:**
- Microsoft ODBC Driver 18 for SQL Server
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
- **Build Frontend** - Build production frontend bundle
- **Format Python Code** - Run Black formatter
- **Sort Python Imports** - Run isort
- **Clean Build Artifacts** - Remove build files and caches

### Debugging Configurations

Access via `F5` or Debug panel

- **Python: FastAPI Backend** - Debug FastAPI with breakpoints
- **Python: Current File** - Debug currently open Python file
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

## 🔧 Customization

### Environment Variables

Edit `.devcontainer/devcontainer.json` under `containerEnv` to change environment variables:

```json
"containerEnv": {
  "LOG_LEVEL": "DEBUG",          // Change to INFO for production-like
  "RUN_MODE": "debug",           // Options: debug | demo | production
  "SQL_DIALECT": "tsql",         // Database dialect
  "DB_ENABLED": "false"          // Enable database connection (if using direct DB)
}
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
```

### Frontend Dependencies Not Found

**Issue:** `npm` errors or missing packages

**Solution:**
```bash
cd frontend
npm install
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

### 5. Keep Container Running

Don't rebuild unless necessary:
- Container persists dependencies in volumes
- Rebuilding is slow (5-10 minutes)
- Only rebuild for Dockerfile/devcontainer.json changes

---

## 📚 Additional Resources

- **Main Documentation:** [README.md](../README.md)
- **Quick Start Guide:** [QUICKSTART.md](../QUICKSTART.md)
- **Architecture Overview:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Configuration Reference:** [CONFIGURATION.md](CONFIGURATION.md)
- **API Documentation:** [CONTRACTS.md](CONTRACTS.md)
- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Specification](https://containers.dev/)

---

## 🤝 Contributing

When contributing, ensure:
1. Dev container builds successfully
2. Code is formatted: Black + isort (auto on save)
3. Environment variables documented in `.env.example`

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](../LICENSE) file for details.

---

**Happy Developing! 🚀**
