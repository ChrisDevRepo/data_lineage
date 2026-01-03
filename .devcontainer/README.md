# Dev Container

**Version:** 1.0.1 • **Author:** Christian Wagner

VSCode development environment with Python 3.11, Node.js 20, and ODBC Driver 18.

---

## Quick Start

1. Open in VS Code: `code .`
2. `F1` → "Dev Containers: Reopen in Container"
3. Wait for build (10-15 min first time)
4. `Ctrl+Shift+P` → `Tasks: Run Task` → `Start Full Stack`

**Access:** http://localhost:8000 (API) • http://localhost:3000 (Frontend)

---

## Configuration

Environment auto-configured on first run. Edit `.env` to customize.

---

## Development

**Start services:** `Ctrl+Shift+P` → `Tasks: Run Task` → Choose task
**Debug:** Press `F5`
**Format code:** `Ctrl+Shift+P` → `Tasks: Run Task` → `Format Code`

---

## Troubleshooting

**Build fails:** `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

**Port conflict:** Stop other services using ports 8000 or 3000
