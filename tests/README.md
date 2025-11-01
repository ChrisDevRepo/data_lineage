# Testing

This directory contains automated tests for the Vibecoding Lineage Parser project.

## Browser Smoke Tests

### Frontend Smoke Test

**File:** `frontend_smoke_test.js`

**Purpose:** Validates the React frontend at http://localhost:3000

**Tests:**
1. ✅ Homepage loads successfully
2. ✅ Main UI elements are visible
3. ✅ No console errors
4. ✅ Screenshot capture works
5. ✅ React root element present

**Usage:**
```bash
# Start frontend first
cd ~/sandbox/frontend
npm run dev

# In another terminal, run smoke test
cd ~/sandbox
node tests/frontend_smoke_test.js
```

**Expected Output:**
```
🚀 Starting Frontend Smoke Tests...

Test 1: Loading homepage...
  ✅ Page loaded - Title: "React Flow Data Lineage"

Test 2: Checking main UI elements...
  ✅ Main container visible: true

Test 3: Checking for console errors...
  ✅ No console errors detected

Test 4: Taking screenshot...
  ✅ Screenshot saved to tests/screenshots/frontend_smoke.png

Test 5: Verifying React app...
  ✅ React root element found: true

✅ All smoke tests passed!
```

**Screenshots:** Saved to `tests/screenshots/`

## Running Tests via Claude Code

You can also run browser tests using natural language via the Playwright MCP:

**Example prompts:**

```
"Use Playwright to test the frontend at http://localhost:3000 and verify it loads correctly"
```

```
"Navigate to http://localhost:3000, click around the interface, and take a screenshot"
```

```
"Test the data lineage visualizer at localhost:3000:
1. Load the page
2. Check for any errors
3. Verify the main graph container is visible
4. Take a screenshot"
```

## MCP Servers Available

The following MCP servers are configured for testing:

1. **playwright** - Browser automation
   - Command: `npx -y @playwright/mcp@latest`
   - Use for: GUI testing, screenshots, web automation

2. **microsoft-learn** - Documentation
   - URL: `https://learn.microsoft.com/api/mcp`
   - Use for: Accessing Microsoft docs

3. **context7** - Code documentation
   - URL: `https://mcp.context7.com/mcp`
   - Use for: Version-specific library docs

## Test Structure

```
tests/
├── README.md                      # This file
├── frontend_smoke_test.js         # Frontend smoke test
├── screenshots/                   # Test screenshots
│   └── frontend_smoke.png
└── parser_regression_test.py      # Parser regression tests (Python)
```

## Future Tests

Planned automated tests:

- [ ] Backend API smoke tests
- [ ] End-to-end workflow tests (upload → parse → visualize)
- [ ] Cross-browser testing (Firefox, WebKit)
- [ ] Mobile responsive testing
- [ ] Performance benchmarks
- [ ] Accessibility audits

## Resources

- **Playwright Docs:** https://playwright.dev
- **Testing Guide:** `/docs/BROWSER_TESTING.md`
- **WSL Setup:** `/docs/WSL_SETUP.md`
