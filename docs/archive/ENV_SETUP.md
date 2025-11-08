# Environment Setup Guide

Simple guide to setting up your `.env` file.

## TL;DR - Quick Setup

```bash
# Copy the example file
cp .env.example .env

# Done! Default values work for local development
```

## What is .env?

The `.env` file contains environment-specific configuration like:
- API CORS origins
- File paths
- Logging levels

**Important:** `.env` is in `.gitignore` and will **NEVER** be committed to version control.

## Setup Methods

### Method 1: Automated Setup (Recommended)

```bash
./setup-env.sh
```

This script will:
1. Copy `.env.example` to `.env`
2. Offer to open it in your editor
3. Provide setup guidance

### Method 2: Manual Setup

```bash
# Copy the example file
cp .env.example .env

# Edit if needed (optional for local dev)
nano .env
```

## Do I Need .env?

**For local development:** NO! ✅

All defaults work out of the box:
```bash
# Just start the app - no .env needed
./start-app.sh
```

**You need .env when:**
- Deploying to production (set `ALLOWED_ORIGINS`)
- Using custom file paths
- Modifying parser thresholds
- Changing log levels

## Example .env File

### Minimal (Local Development)
```bash
# .env - Minimal configuration
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

### Production
```bash
# .env - Production configuration
ALLOWED_ORIGINS=https://myapp.azurewebsites.net,http://localhost:3000
LOG_LEVEL=WARNING
DEBUG_MODE=false
```

### Custom Paths
```bash
# .env - Custom paths
PATH_WORKSPACE_FILE=/data/lineage.duckdb
PATH_OUTPUT_DIR=/output/results
LOG_LEVEL=DEBUG
```

## .gitignore Configuration

Your `.gitignore` ensures `.env` is never committed:

```gitignore
# Environment variables (NEVER commit credentials!)
.env
.env.local
.env.*.local
```

**✅ Safe to commit:**
- `.env.example` - Template file (no secrets)
- `.env.template` - Detailed documentation (no secrets)

**❌ Never commit:**
- `.env` - Your actual configuration (may contain secrets)
- `.env.local` - Local overrides

## How to Rename .env.example to .env

### Linux / macOS / WSL

```bash
cp .env.example .env
```

### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

### Windows (Command Prompt)

```cmd
copy .env.example .env
```

## Available Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS origins (comma-separated) |
| `PATH_WORKSPACE_FILE` | `lineage_workspace.duckdb` | DuckDB workspace file |
| `PATH_OUTPUT_DIR` | `lineage_output` | JSON output directory |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `DEBUG_MODE` | `false` | Enable debug mode |
| `SKIP_QUERY_LOGS` | `false` | Skip query log analysis |
| `PARSER_CONFIDENCE_HIGH` | `0.85` | High confidence threshold |

See `.env.example` for complete list with descriptions.

## Troubleshooting

### Issue: "Module not found" errors
```bash
# Install dependencies first
pip install -r requirements.txt
```

### Issue: CORS errors in browser
```bash
# Add your frontend URL to .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Issue: Permission denied on setup-env.sh
```bash
chmod +x setup-env.sh
./setup-env.sh
```

## Best Practices

1. **Never commit .env** - It's already in .gitignore
2. **Use defaults** - Only customize what you need
3. **Document changes** - Add comments explaining custom settings
4. **Production secrets** - Use Azure App Service Configuration, not .env files
5. **Team sharing** - Share via `.env.example`, not `.env`

## Related Documentation

- `.env.example` - Simple template
- `.env.template` - Detailed template with all options
- `docs/CONFIGURATION_GUIDE.md` - Complete configuration reference
- `docs/SETUP_AND_DEPLOYMENT.md` - Deployment guide

---

**Quick Reference:**

```bash
# Setup
cp .env.example .env

# Start app (auto-installs dependencies)
./start-app.sh

# That's it!
```
