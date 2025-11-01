# WSL Ubuntu Setup Guide

**Last Updated:** 2025-11-01

This document describes the WSL Ubuntu setup for the Vibecoding Lineage Parser v3.0 project.

## Overview

The project runs natively in WSL Ubuntu environment. All dependencies are pre-installed and ready to use.

## Environment Details

**Operating System:** WSL Ubuntu (Windows Subsystem for Linux)
**Python Version:** 3.12.3
**Node.js Version:** v24.11.0
**npm Version:** 11.6.1

## Installation Summary

### System Dependencies (Installed)
✅ `python3.12-venv` - Python virtual environment support

### Python Dependencies (Pre-installed in venv)
All packages installed in `~/sandbox/venv/`:

**Core Processing:**
- `duckdb>=1.4.1` - In-memory database for lineage processing
- `pyarrow>=22.0.0` - Parquet file I/O
- `pandas>=2.3.3` - Data manipulation

**SQL Parsing:**
- `sqlglot>=27.28.1` - T-SQL AST traversal
- `sqllineage>=1.5.3` - Multi-parser validation

**Web Framework (API):**
- `fastapi==0.115.0` - REST API framework
- `uvicorn==0.32.0` - ASGI server
- `python-multipart==0.0.12` - File upload support

**Azure AI (Optional):**
- `agent-framework>=1.0.0b251016` - Multi-agent orchestration
- `azure-ai-inference>=1.0.0b7` - Azure AI Foundry client
- `azure-core>=1.30.0` - Azure SDK core

**CLI & Utilities:**
- `click>=8.3.0` - CLI framework
- `python-dotenv>=1.1.1` - Environment management
- `rich>=13.7.0` - Console output formatting
- `pydantic>=2.5.0` - Data validation

**Total:** 60+ packages successfully installed

### Frontend Dependencies (Pre-installed)
All packages installed in `~/sandbox/frontend/node_modules/`:

**Core:**
- `react@19.2.0` - UI framework
- `react-dom@19.2.0` - React DOM renderer
- `reactflow@11.11.4` - Graph visualization
- `vite@6.4.1` - Build tool

**UI Components:**
- `@monaco-editor/react@4.7.0` - SQL code editor
- `dagre@0.8.5` - Graph layout algorithm
- `graphology@0.25.4` - Graph data structure

**Total:** 182 packages successfully installed

### MCP Servers (Model Context Protocol)

Claude Code MCP servers provide additional capabilities like documentation access.

**Installed:**

1. ✅ **microsoft-learn** - Microsoft documentation access
   - Type: HTTP
   - URL: `https://learn.microsoft.com/api/mcp`
   - Scope: User (available in all projects)
   - Provides: Azure docs, Synapse docs, Python docs, .NET docs, and more

2. ✅ **context7** - Up-to-date code documentation
   - Type: HTTP
   - URL: `https://mcp.context7.com/mcp`
   - Scope: User (available in all projects)
   - Provides: Version-specific documentation for any library/framework
   - Source: Upstash (35.8k ⭐ GitHub, MIT licensed)
   - Features: Real-time docs for React, FastAPI, DuckDB, TypeScript, etc.

3. ✅ **playwright** - Browser automation & GUI testing
   - Type: stdio
   - Command: `npx -y @playwright/mcp@latest`
   - Scope: User (available in all projects)
   - Provides: Web browser automation, GUI testing, screenshots, web scraping
   - Browser: Chromium (GUI mode enabled via WSLg)
   - Source: Microsoft (official Playwright MCP)
   - Features: Multi-browser support, auto-waiting, network interception

**To verify MCP servers:**
```bash
claude mcp list
```

**To view details:**
```bash
claude mcp get microsoft-learn
claude mcp get context7
claude mcp get playwright
```

## Key Architectural Changes

### Removed Dependencies

❌ **pyodbc** - ODBC database connector (no longer needed)
❌ **sqlalchemy** - SQL toolkit (removed Synapse-specific code)
❌ **Microsoft ODBC Driver 18** - SQL Server driver (not required)
❌ **unixODBC libraries** - ODBC driver manager (not required)

### Why ODBC was Removed

The application architecture uses **offline analysis** of pre-exported Parquet files:

```
[Synapse DMVs] → PySpark Extractor → [Parquet Files] → DuckDB → [Lineage JSON]
                 (runs in Synapse)       (shipped)    (local)     (output)
```

**No direct database connection required:**
- ✅ Parser works entirely from Parquet snapshots
- ✅ All metadata pre-exported by PySpark job in Synapse Studio
- ✅ DuckDB handles all SQL parsing and analysis locally
- ✅ No network connectivity to Synapse needed

## Quick Start

### Activate Environment

```bash
# Every session, activate the virtual environment
cd ~/sandbox
source venv/bin/activate
```

### Verify Installation

```bash
# Test Python packages
python -c "import duckdb, sqlglot, fastapi, pandas, pyarrow; print('✅ Python ready')"

# Test Node.js packages
cd frontend
npm list --depth=0
```

### Run Backend API

**Important:** Backend requires Azure OpenAI environment variables to start.

```bash
cd ~/sandbox

# Export environment variables and start backend
source venv/bin/activate && \
export AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/ && \
export AZURE_OPENAI_API_KEY=your-api-key && \
export AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano && \
export AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano && \
export AZURE_OPENAI_API_VERSION=2024-12-01-preview && \
export AI_ENABLED=true && \
export ALLOWED_ORIGINS=http://localhost:3000 && \
python3 api/main.py
```

Backend available at: `http://localhost:8000`

**Note:** Replace `your-endpoint` and `your-api-key` with actual Azure OpenAI credentials from your `.env` file.

### Run Frontend

```bash
cd ~/sandbox/frontend
npm run dev
```

Frontend available at: `http://localhost:3000`

### Run CLI Parser

```bash
cd ~/sandbox
source venv/bin/activate

# Run lineage analysis (incremental mode)
python lineage_v3/main.py run --parquet parquet_snapshots/

# Full refresh mode
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

## Claude Code Configuration

Auto-approval settings configured in `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Read(~/**)",
      "Edit(~/**)",
      "Write(~/**)",
      "Bash"
    ]
  },
  "sandbox": {
    "autoAllowBashIfSandboxed": true,
    "enabled": true
  },
  "alwaysThinkingEnabled": true
}
```

This configuration ensures Claude Code can work in the sandbox directory without approval prompts.

## Troubleshooting

### Virtual Environment Not Found

```bash
cd ~/sandbox
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r api/requirements.txt
```

### Import Errors

Make sure virtual environment is activated:
```bash
source ~/sandbox/venv/bin/activate
```

### Frontend Errors

Reinstall dependencies:
```bash
cd ~/sandbox/frontend
rm -rf node_modules
npm install
```

### Permission Denied Errors

Check Claude Code settings:
```bash
cat ~/.claude/settings.json
```

Ensure `"Bash"` is in the `permissions.allow` array.

### Azure OpenAI Validation Error

**Error:** `ValidationError: 2 validation errors for AzureOpenAISettings`

**Cause:** Backend requires Azure OpenAI credentials even when AI is disabled.

**Solution:** Export environment variables when starting backend:
```bash
source venv/bin/activate && \
export AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/ && \
export AZURE_OPENAI_API_KEY=your-api-key && \
export AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano && \
export AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano && \
export AZURE_OPENAI_API_VERSION=2024-12-01-preview && \
export AI_ENABLED=true && \
python3 api/main.py
```

**Note:** Remove quotes from values in `.env` file - Pydantic Settings doesn't accept quoted values.

### SQLViewer Import Error

**Error:** `Failed to resolve import "./components/SQLViewer"`

**Cause:** Import path used wrong casing (SQLViewer vs SqlViewer).

**Solution:** This has been fixed in App.tsx. If you still see this error:
```bash
# Verify the import in App.tsx is:
import { SqlViewer } from './components/SqlViewer';  # Correct (lowercase 'ql')

# Not:
import { SqlViewer } from './components/SQLViewer';  # Wrong (all caps)
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Kill backend (port 8000)
lsof -ti:8000 | xargs -r kill

# Kill frontend (port 3000)
lsof -ti:3000 | xargs -r kill
```

## File Structure

```
~/sandbox/
├── venv/                          # Python virtual environment
│   ├── bin/activate              # Activation script
│   └── lib/python3.12/site-packages/  # Installed packages
├── lineage_v3/                    # Core parser
├── api/                           # FastAPI backend
├── frontend/                      # React frontend
│   └── node_modules/             # Node.js packages
├── requirements.txt               # Python dependencies (updated)
└── .env.template                  # Environment config template
```

## Next Steps

1. **Obtain Parquet files** - Get DMV exports from Synapse team or run PySpark extractor
2. **Configure .env** - Copy `.env.template` to `.env` and configure (if using Azure AI features)
3. **Run the application** - Start backend and frontend as shown above
4. **Upload Parquet files** - Use the web UI to upload and parse Parquet files

## Support

For issues or questions:
- Check [CLAUDE.md](../CLAUDE.md) for detailed project documentation
- Review [README.md](../README.md) for architecture overview
- See [docs/PARSING_USER_GUIDE.md](PARSING_USER_GUIDE.md) for SQL parsing best practices
