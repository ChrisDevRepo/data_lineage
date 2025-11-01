# MCP Quick Reference

**Last Updated:** 2025-11-01

This document provides a quick reference for the MCP (Model Context Protocol) servers configured in this project.

## Installed MCP Servers

### 1. microsoft-learn 📚

**Type:** HTTP
**URL:** https://learn.microsoft.com/api/mcp
**Status:** ✓ Connected
**Scope:** User (all projects)

**Purpose:** Access official Microsoft documentation in real-time

**Use Cases:**
- Azure services documentation
- Synapse Analytics guides
- Python standard library
- .NET and C# APIs
- TypeScript/JavaScript references
- SQL Server T-SQL syntax

**Example Usage:**
```
"Use microsoft-learn to find the latest Azure Synapse Parquet support"
"Get documentation for DuckDB Python API from Microsoft Learn"
"Show me FastAPI async/await patterns from the docs"
```

---

### 2. context7 🔍

**Type:** HTTP
**URL:** https://mcp.context7.com/mcp
**Status:** ✓ Connected
**Scope:** User (all projects)
**Source:** Upstash (35.8k ⭐, MIT licensed)

**Purpose:** Fetch up-to-date, version-specific documentation for any library or framework

**Use Cases:**
- Current React/Vue/Angular APIs
- Latest Python package documentation
- npm package current versions
- Framework-specific examples
- Code snippets from official docs

**Example Usage:**
```
"Use context7 to get the latest React hooks documentation"
"Fetch current Playwright API for taking screenshots"
"Show me the latest Pandas DataFrame methods"
"Get DuckDB Parquet reading examples"
```

**Advantages:**
- Version-specific (avoids outdated APIs)
- Pulls from official sources
- Real-time updates
- Supports virtually any library

---

### 3. playwright 🎭

**Type:** stdio
**Command:** `npx -y @playwright/mcp@latest`
**Status:** ✓ Connected
**Scope:** User (all projects)
**Browser:** Chromium 141.0.7390.37
**Source:** Microsoft (official)

**Purpose:** Browser automation, web testing, screenshots, and UI validation

**Use Cases:**
- Frontend testing (http://localhost:3000)
- Automated UI testing
- Screenshot capture
- Form automation
- Web scraping
- Smoke tests

**Key Features:**
- GUI mode (browser visible on Windows desktop via WSLg)
- Accessibility tree-based (LLM-friendly)
- Auto-waiting for elements
- Network interception
- Multi-browser support (Chromium ready, Firefox/WebKit available)

**Example Usage:**
```
"Use Playwright to test http://localhost:3000"
"Navigate to the frontend and take a screenshot"
"Verify the login form works correctly"
"Run smoke tests on the web application"
"Check if the data lineage graph renders properly"
```

**Test Script Available:**
```bash
cd ~/sandbox
node tests/frontend_smoke_test.js
```

---

## Quick Commands

### Verify MCP Status
```bash
claude mcp list
```

### Get Server Details
```bash
claude mcp get microsoft-learn
claude mcp get context7
claude mcp get playwright
```

### Remove a Server
```bash
claude mcp remove <server-name> --scope user
```

### Add New Server
```bash
# HTTP server
claude mcp add --scope user --transport http <name> <url>

# stdio server
claude mcp add --scope user <name> -- <command>
```

---

## Usage Guidelines for Claude

### When to Use microsoft-learn
✅ Microsoft-specific technologies (Azure, Synapse, .NET, TypeScript)
✅ SQL Server and T-SQL syntax
✅ Python standard library
✅ Enterprise Microsoft documentation

❌ Third-party libraries (use context7 instead)
❌ Community packages

### When to Use context7
✅ Any npm package (React, Vue, Express, etc.)
✅ Any Python package (Pandas, NumPy, FastAPI, etc.)
✅ Framework-specific documentation
✅ Version-specific API references
✅ Code examples from official sources

❌ Microsoft-specific docs (use microsoft-learn)

### When to Use playwright
✅ Testing web applications
✅ Automating browser interactions
✅ Taking screenshots for documentation
✅ Verifying UI components
✅ End-to-end testing
✅ Web scraping

❌ Non-web automation
❌ API testing (use requests/httpx instead)

---

## Best Practices

### 1. Proactive Documentation Fetching
**Before suggesting code:**
```
Bad:  "Here's how to use React hooks (based on training data)"
Good: "Let me fetch the latest React hooks documentation from context7..."
```

### 2. Verify APIs Before Coding
```
Bad:  Writing code with potentially outdated syntax
Good: Checking current API via MCP first, then writing code
```

### 3. Automated Testing
```
Bad:  "The frontend looks good (no verification)"
Good: "Let me use Playwright to test the frontend at localhost:3000..."
```

### 4. Version-Specific Examples
```
Bad:  "Here's a Pandas example (might be outdated)"
Good: "Fetching the current Pandas DataFrame API via context7..."
```

---

## Common Workflows

### Workflow 1: Implementing a New React Feature

1. **Fetch docs:** Use context7 to get latest React patterns
2. **Write code:** Implement feature with current API
3. **Test:** Use Playwright to verify UI works
4. **Screenshot:** Capture result for documentation

### Workflow 2: Debugging Frontend Issue

1. **Test:** Use Playwright to navigate to problematic page
2. **Inspect:** Check console errors, DOM structure
3. **Screenshot:** Capture error state
4. **Fix:** Implement solution
5. **Verify:** Re-test with Playwright

### Workflow 3: Adding Python Package Usage

1. **Fetch docs:** Use context7 for package documentation
2. **Check examples:** Get current syntax and patterns
3. **Implement:** Write code with verified API
4. **Test:** Run code to verify functionality

### Workflow 4: Azure Synapse Research

1. **Fetch docs:** Use microsoft-learn for Synapse guides
2. **Get specifics:** Find Parquet/DuckDB integration details
3. **Implement:** Apply learnings to codebase
4. **Document:** Update project docs

---

## Troubleshooting

### MCP Server Not Connected

**Check status:**
```bash
claude mcp list
```

**Expected output:**
```
microsoft-learn: ✓ Connected
context7: ✓ Connected
playwright: ✓ Connected
```

**If disconnected:**
1. Restart Claude Code
2. Check network connectivity (for HTTP servers)
3. Verify npx works (for stdio servers)

### Playwright Browser Won't Open

**Check DISPLAY:**
```bash
echo $DISPLAY  # Should show :0
```

**Test manually:**
```bash
google-chrome https://example.com &
```

**If browser doesn't appear:**
- Verify WSLg is enabled (Windows 11)
- Check X11 setup (Windows 10)

### Context7 Rate Limits

**Symptom:** "Rate limit exceeded" error

**Solutions:**
- Wait a few minutes
- Get free API key at https://context7.com/dashboard
- Configure API key in MCP settings

---

## Advanced Configuration

### Adding API Keys

**Context7 with API key:**
```bash
claude mcp remove context7 --scope user
claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp \
  --header "Authorization: Bearer YOUR_API_KEY"
```

### Custom Playwright Options

Edit `~/.claude.json` to customize Playwright:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--browser", "firefox"],
      "env": {
        "DISPLAY": ":0",
        "PLAYWRIGHT_BROWSERS_PATH": "~/.cache/ms-playwright"
      }
    }
  }
}
```

---

## Resources

### Official Documentation
- **MCP Specification:** https://modelcontextprotocol.io
- **Microsoft Learn MCP:** https://github.com/MicrosoftDocs/mcp
- **Context7:** https://github.com/upstash/context7
- **Playwright MCP:** https://github.com/microsoft/playwright-mcp

### Related Docs in This Project
- [BROWSER_TESTING.md](BROWSER_TESTING.md) - Comprehensive Playwright guide
- [WSL_SETUP.md](WSL_SETUP.md) - WSL Ubuntu setup details
- [CLAUDE.md](../CLAUDE.md) - Main development environment guide

---

## Quick Reference Card

| Server | Type | Use For | Example |
|--------|------|---------|---------|
| **microsoft-learn** | HTTP | Microsoft docs | Azure, Synapse, .NET, Python stdlib |
| **context7** | HTTP | Any library docs | React, FastAPI, Pandas, DuckDB |
| **playwright** | stdio | Browser testing | UI tests, screenshots, automation |

**Status Check:** `claude mcp list`
**Server Details:** `claude mcp get <name>`
**Documentation:** See [docs/](.) directory

---

**Last Updated:** 2025-11-01
**All MCP Servers:** ✓ Connected and Ready
