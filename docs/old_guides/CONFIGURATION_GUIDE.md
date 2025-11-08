# Configuration Guide

Complete guide to configuring the Data Lineage Visualizer across all components.

## Table of Contents
- [Quick Start](#quick-start)
- [Backend/Parser Configuration](#backendparser-configuration)
- [API Configuration](#api-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Environment Files](#environment-files)
- [Best Practices](#best-practices)

---

## Quick Start

### For Local Development (No Configuration Needed!)

```bash
# 1. Start the application (uses all defaults)
./start-app.sh

# Done! No .env file required for local development
```

All components have sensible defaults that work out of the box:
- Parser: Uses `lineage_workspace.duckdb` in current directory
- API: Listens on `http://localhost:8000` with CORS for `localhost:3000`
- Frontend: Connects to `http://localhost:8000`

### When You Need Custom Configuration

```bash
# 1. Generate .env from template
./setup-env.sh

# 2. Edit configuration
nano .env

# 3. Start the application
./start-app.sh
```

---

## Backend/Parser Configuration

### Configuration File: `.env` (optional)

The parser uses **Pydantic Settings** with cascading configuration:

**Priority (highest to lowest):**
1. Command-line flags (e.g., `--parquet`, `--output`)
2. Environment variables
3. `.env` file
4. Hardcoded defaults in `lineage_v3/config/settings.py`

### Available Settings

#### Path Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PATH_WORKSPACE_FILE` | `lineage_workspace.duckdb` | DuckDB workspace database file |
| `PATH_OUTPUT_DIR` | `lineage_output` | Output directory for JSON files |
| `PATH_PARQUET_DIR` | `parquet_snapshots` | Default Parquet snapshot directory |

**Example:**
```bash
# .env
PATH_WORKSPACE_FILE=/data/lineage.duckdb
PATH_OUTPUT_DIR=/output/results
```

#### Parser Quality Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `PARSER_CONFIDENCE_HIGH` | `0.85` | High confidence (regex + SQLGlot agree ±10%) |
| `PARSER_CONFIDENCE_MEDIUM` | `0.75` | Medium confidence (partial agreement ±25%) |
| `PARSER_CONFIDENCE_LOW` | `0.5` | Low confidence (major difference >25%) |
| `PARSER_THRESHOLD_GOOD` | `0.10` | Good match threshold (±10% difference) |
| `PARSER_THRESHOLD_FAIR` | `0.25` | Fair match threshold (±25% difference) |

**Example (stricter quality):**
```bash
# .env
PARSER_CONFIDENCE_HIGH=0.90
PARSER_CONFIDENCE_MEDIUM=0.80
```

#### Runtime Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `DEBUG_MODE` | `false` | Enable debug mode (additional logging) |
| `SKIP_QUERY_LOGS` | `false` | Skip query log analysis |

**Example:**
```bash
# .env
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

### CLI Override Examples

CLI flags **always override** environment variables:

```bash
# Override output directory
python lineage_v3/main.py run --parquet data/ --output custom_output/

# Full refresh (ignore incremental cache)
python lineage_v3/main.py run --parquet data/ --full-refresh

# Skip query logs
python lineage_v3/main.py run --parquet data/ --skip-query-logs

# Custom workspace file
python lineage_v3/main.py run --parquet data/ --workspace my_workspace.duckdb
```

### Programmatic Access

```python
from lineage_v3.config import settings

# Type-safe configuration access
print(settings.parser.confidence_high)      # 0.85
print(settings.paths.workspace_file)        # Path("lineage_workspace.duckdb")
print(settings.log_level)                   # "INFO"
```

---

## API Configuration

### Configuration File: `.env` (optional)

The FastAPI backend reads configuration from environment variables.

### Available Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |

### Local Development

```bash
# .env (optional, this is the default)
ALLOWED_ORIGINS=http://localhost:3000
```

### Production Deployment

```bash
# .env
ALLOWED_ORIGINS=https://my-frontend.azurewebsites.net,http://localhost:3000
```

### Multiple Origins

```bash
# .env
ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com,http://localhost:3000
```

---

## Frontend Configuration

### Configuration Files

The frontend uses **Vite environment variables** with separate files for each environment:

```
frontend/
├── .env.development    # Used by: npm run dev
└── .env.production     # Used by: npm run build
```

### Available Settings

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | Backend API base URL |

### Development Configuration

**File:** `frontend/.env.development`

```bash
# Points to local backend
VITE_API_URL=http://localhost:8000
```

**Usage:**
```bash
cd frontend
npm run dev  # Uses .env.development
```

### Production Configuration

**File:** `frontend/.env.production`

```bash
# Points to production backend
VITE_API_URL=https://my-backend-app.azurewebsites.net
```

**Usage:**
```bash
cd frontend
npm run build  # Uses .env.production
```

### Accessing in React/TypeScript

```typescript
// Get API URL
const apiUrl = import.meta.env.VITE_API_URL;

// Make API calls
fetch(`${apiUrl}/api/lineage`)
  .then(res => res.json());
```

---

## Environment Files

### File Structure

```
/
├── .env.template           # ✅ Template (committed to git)
├── .env                    # ❌ Local config (in .gitignore)
├── .env.local              # ❌ Local overrides (in .gitignore)
├── setup-env.sh            # ✅ Setup script (committed to git)
│
├── frontend/
│   ├── .env.development    # ✅ Dev config (committed - no secrets)
│   └── .env.production     # ✅ Prod config (committed - no secrets)
│
└── lineage_v3/config/
    └── settings.py         # ✅ Defaults + Pydantic models (committed)
```

### What Gets Committed?

**✅ COMMIT (Safe to share):**
- `.env.template` - Template with documentation
- `frontend/.env.development` - Development API URL (no secrets)
- `frontend/.env.production` - Production API URL (no secrets)
- `lineage_v3/config/settings.py` - Defaults and validation

**❌ NEVER COMMIT (May contain secrets):**
- `.env` - Your local configuration
- `.env.local` - Local overrides
- `.env.*.local` - Environment-specific local overrides

### .gitignore Configuration

The `.gitignore` file ensures sensitive configuration is never committed:

```gitignore
# Environment variables (NEVER commit credentials!)
.env
.env.local
.env.*.local
.env.development.local
.env.production.local
.env.test.local
```

---

## Best Practices

### 1. Use Defaults for Local Development

**❌ Don't:**
```bash
# Creating .env for local dev with all defaults
cp .env.template .env
# (Unnecessary - adds complexity)
```

**✅ Do:**
```bash
# Just start - defaults work!
./start-app.sh
```

### 2. Create .env Only When Needed

**When to create `.env`:**
- Custom file paths (non-default workspace location)
- Modified parser thresholds (team-specific quality standards)
- Production deployment (CORS, logging levels)
- Multiple developers with different setups

### 3. Use CLI Flags for One-Off Changes

**❌ Don't:**
```bash
# Edit .env for one-time change
echo "PATH_OUTPUT_DIR=temp_output" >> .env
python lineage_v3/main.py run --parquet data/
```

**✅ Do:**
```bash
# Use CLI flag
python lineage_v3/main.py run --parquet data/ --output temp_output/
```

### 4. Document Team-Specific Settings

If your team has custom defaults, document them:

```bash
# .env (team configuration)
# ==============================================================================
# Team Standard Configuration
# ==============================================================================
# Our quality bar is higher than default
PARSER_CONFIDENCE_HIGH=0.90

# We don't have query logs in our snapshots
SKIP_QUERY_LOGS=true

# Custom workspace location (shared network drive)
PATH_WORKSPACE_FILE=/mnt/shared/lineage_workspace.duckdb
```

### 5. Never Commit Secrets

**❌ NEVER put secrets in .env files that might be committed:**
- Database passwords
- API keys
- Authentication tokens
- Personal file paths

**✅ For production secrets, use:**
- Azure App Service Configuration
- AWS Parameter Store
- Environment variables set by deployment system

### 6. Validate Configuration on Startup

The parser validates all settings using Pydantic:

```python
# Automatic validation
settings = Settings()  # Raises error if invalid

# Example: confidence_high must be 0.0-1.0
PARSER_CONFIDENCE_HIGH=1.5  # ❌ ValidationError!
```

### 7. Use Type-Safe Access

**❌ Don't:**
```python
import os
confidence = float(os.getenv('PARSER_CONFIDENCE_HIGH', '0.85'))
```

**✅ Do:**
```python
from lineage_v3.config import settings
confidence = settings.parser.confidence_high  # Type-safe, validated
```

---

## Setup Instructions

### Initial Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd sandbox

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Generate .env if you need custom settings
./setup-env.sh

# 5. Start the application
./start-app.sh
```

### Team Onboarding

```bash
# 1. Clone repository
git clone <repo-url>
cd sandbox

# 2. Setup environment (auto-installs dependencies)
./start-app.sh

# That's it! No manual configuration needed.
```

### Production Deployment (Azure)

```bash
# 1. Configure App Service environment variables:
ALLOWED_ORIGINS=https://your-frontend-app.azurewebsites.net
LOG_LEVEL=WARNING

# 2. Frontend: Update .env.production
VITE_API_URL=https://your-backend-app.azurewebsites.net

# 3. Build and deploy
npm run build
```

---

## Troubleshooting

### Issue: "Module not found" errors

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: CORS errors in browser

**Solution:** Add frontend URL to ALLOWED_ORIGINS
```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Issue: Parser can't find workspace file

**Solution:** Check PATH_WORKSPACE_FILE or use CLI flag
```bash
# Use CLI flag
python lineage_v3/main.py run --parquet data/ --workspace path/to/workspace.duckdb
```

### Issue: Frontend can't connect to API

**Solution:** Check VITE_API_URL in `frontend/.env.development`
```bash
VITE_API_URL=http://localhost:8000
```

---

## Reference

### Quick Reference Card

| Component | Config File | Key Setting |
|-----------|-------------|-------------|
| **Parser** | `.env` (optional) | `PATH_WORKSPACE_FILE`, `PARSER_CONFIDENCE_HIGH` |
| **API** | `.env` (optional) | `ALLOWED_ORIGINS` |
| **Frontend Dev** | `frontend/.env.development` | `VITE_API_URL=http://localhost:8000` |
| **Frontend Prod** | `frontend/.env.production` | `VITE_API_URL=https://your-api.com` |

### Complete .env Example

```bash
# ==============================================================================
# Data Lineage Visualizer - Environment Configuration
# ==============================================================================

# Parser Paths
PATH_WORKSPACE_FILE=lineage_workspace.duckdb
PATH_OUTPUT_DIR=lineage_output

# Parser Quality
PARSER_CONFIDENCE_HIGH=0.85

# Logging
LOG_LEVEL=INFO

# API CORS
ALLOWED_ORIGINS=http://localhost:3000

# ==============================================================================
```

---

## Related Documentation

- [SETUP_AND_DEPLOYMENT.md](SETUP_AND_DEPLOYMENT.md) - Installation and deployment
- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - Architecture overview
- [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md) - Operations and troubleshooting
- `.env.template` - Complete configuration reference

---

**Last Updated:** 2025-11-06
**Version:** v4.1.3
