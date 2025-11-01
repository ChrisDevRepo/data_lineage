# Browser GUI Testing with Playwright MCP

**Last Updated:** 2025-11-01

This document describes how to use browser automation and GUI testing in Claude Code via the Playwright MCP server on WSL Ubuntu.

## Overview

Browser automation enables Claude Code to:
- ✅ Navigate websites and web applications
- ✅ Fill forms and click buttons
- ✅ Take screenshots and verify UI
- ✅ Test web applications interactively
- ✅ Scrape data from websites
- ✅ Automate repetitive browser tasks

**Key Feature:** Browser windows are **visible on Windows desktop** via WSLg, allowing you to watch tests run in real-time.

## Architecture

```
┌─────────────────────────────────────────┐
│      Windows 11 Desktop                 │
│  (Browser windows visible here)        │
└──────────────┬──────────────────────────┘
               │ WSLg Display
┌──────────────▼──────────────────────────┐
│      WSL2 Ubuntu                        │
│  ┌────────────────────────────────┐     │
│  │  Claude Code                   │     │
│  └─────────────┬──────────────────┘     │
│                │ MCP Protocol           │
│  ┌─────────────▼──────────────────┐     │
│  │  Playwright MCP Server         │     │
│  │  (@playwright/mcp)             │     │
│  └─────────────┬──────────────────┘     │
│                │                        │
│  ┌─────────────▼──────────────────┐     │
│  │  Chromium Browser              │     │
│  │  (Playwright-controlled)       │     │
│  └────────────────────────────────┘     │
└─────────────────────────────────────────┘
```

## Installation Summary

### System Requirements
- ✅ **Windows 11** (WSLg built-in)
- ✅ **WSL2 Ubuntu** (any recent version)
- ✅ **Node.js 18+** (installed)
- ✅ **DISPLAY=:0** (WSLg sets this automatically)

### Installed Components

**1. Google Chrome**
- Version: 142.0.7444.59
- Location: `/usr/bin/google-chrome`
- Installed via: `.deb package`

**2. Playwright**
- Chromium: 141.0.7390.37 (Playwright build v1194)
- Location: `~/.cache/ms-playwright/chromium-1194`
- FFMPEG: v1011 (for video recording)
- Headless Shell: Available for headless mode

**3. Playwright MCP Server**
- Package: `@playwright/mcp@latest`
- Scope: User (all projects)
- Status: ✓ Connected

**System Dependencies Installed:**
```bash
libgbm1              # Graphics buffer management
libasound2           # Audio support
libgtk-3-0           # GTK GUI toolkit
libnotify-dev        # Notifications
libnss3              # Network Security Services
libxss1              # X11 Screen Saver
libgstreamer*        # Video streaming
```

## Usage Examples

### Example 1: Basic Navigation

**Prompt:**
```
Use Playwright to navigate to https://example.com and tell me what you see
```

**What happens:**
1. Chromium browser window opens on Windows desktop
2. Browser navigates to example.com
3. Claude reads the page content via accessibility tree
4. Claude describes the page to you

### Example 2: Screenshot Capture

**Prompt:**
```
Navigate to GitHub.com and take a screenshot
```

**What happens:**
1. Browser opens and navigates to GitHub
2. Screenshot captured
3. Screenshot saved (can be viewed/analyzed)

### Example 3: Form Automation

**Prompt:**
```
Go to https://example.com/contact and fill out the contact form with test data
```

**What happens:**
1. Browser opens contact page
2. Claude fills in form fields
3. You can watch it happen in real-time
4. Form can be submitted or left for review

### Example 4: Web Application Testing

**Prompt:**
```
Test the login flow on our staging site at http://localhost:3000
- Try valid credentials
- Try invalid credentials
- Check error messages
```

**What happens:**
1. Browser opens your local dev server
2. Claude tests different scenarios
3. You can watch the tests execute
4. Claude reports results

### Example 5: Data Scraping

**Prompt:**
```
Go to https://news.ycombinator.com and get the top 5 story titles
```

**What happens:**
1. Browser navigates to Hacker News
2. Claude extracts story titles from accessibility tree
3. Returns structured data

## Browser Modes

### Headed Mode (Default - GUI Visible)

Browser windows appear on Windows desktop.

**When to use:**
- ✅ Interactive testing
- ✅ Debugging automation scripts
- ✅ Visual verification
- ✅ Watching tests run

**Configuration:** Default (no special flags needed)

### Headless Mode (No GUI)

Browser runs in background without visible window.

**When to use:**
- ✅ Fast automated tests
- ✅ CI/CD pipelines
- ✅ Background scraping
- ✅ Resource-constrained environments

**Configuration:** Add `--headless` flag to MCP server args (not currently configured)

## How It Works: Accessibility Tree

Unlike traditional screenshot-based automation, Playwright MCP uses the **accessibility tree** for page understanding:

**Accessibility Tree:**
```json
{
  "role": "button",
  "name": "Sign In",
  "enabled": true,
  "focused": false
}
```

**Benefits:**
- 🚀 Faster than screenshot analysis
- 📊 Structured, LLM-friendly data
- ♿ Ensures UI is accessible
- 🎯 More reliable element identification

## Testing Your Setup

### Quick Test (Command Line)

```bash
cd ~/sandbox
cat > test_playwright.js << 'EOF'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();
  await page.goto('https://example.com');
  await page.waitForTimeout(3000);
  await browser.close();
  console.log('✅ Test successful!');
})();
EOF

npm install playwright
node test_playwright.js
```

**Expected:** Browser window opens on Windows desktop, shows example.com for 3 seconds, then closes.

### Test via Claude Code

1. Open Claude Code in your project
2. Type: `"Use Playwright to open https://example.com"`
3. Watch browser window appear on Windows
4. Claude will describe the page

## Troubleshooting

### Issue: Browser doesn't appear

**Check DISPLAY variable:**
```bash
echo $DISPLAY  # Should show :0
```

**Fix:**
```bash
export DISPLAY=:0
# Add to ~/.bashrc for persistence
echo 'export DISPLAY=:0' >> ~/.bashrc
```

### Issue: "No sandbox error"

**Cause:** WSL requires `--no-sandbox` flag

**Solution:** Playwright MCP automatically handles this, but if using custom scripts:
```javascript
await chromium.launch({
  args: ['--no-sandbox', '--disable-setuid-sandbox']
});
```

### Issue: MCP server not connecting

**Check MCP status:**
```bash
claude mcp list
# Should show: playwright: npx -y @playwright/mcp@latest - ✓ Connected
```

**Restart Claude Code:**
```bash
# Exit and restart claude-code
```

### Issue: Missing dependencies

**Reinstall Playwright dependencies:**
```bash
npx playwright install-deps chromium
npx playwright install chromium --force
```

## Advanced Configuration

### Multi-Browser Testing

Playwright supports Chromium, Firefox, and WebKit:

**Chromium (default):**
- Best automation support
- Chrome DevTools Protocol
- Fastest performance

**Firefox:**
```bash
npx playwright install firefox
```

**WebKit (Safari engine):**
```bash
npx playwright install webkit
```

### Network Interception

Playwright can intercept and modify network requests:
- Block analytics scripts
- Mock API responses
- Capture network traffic
- Test offline scenarios

### Mobile Emulation

Test responsive designs with mobile device emulation:
- iPhone, iPad, Android devices
- Custom screen sizes
- Touch events
- Geolocation

### Video Recording

Record test execution:
```javascript
const browser = await chromium.launch({
  recordVideo: { dir: './videos/' }
});
```

## Security Considerations

### The `--no-sandbox` Flag

**What it does:** Disables Chromium's security sandbox

**Why needed:** WSL2 doesn't support the Linux namespacing required for Chrome's sandbox

**Implications:**
- ⚠️ Reduced browser security
- ⚠️ Don't browse sensitive/untrusted sites during automation
- ✅ Acceptable for testing environments
- ✅ Safe for localhost and known sites

**Mitigation:**
- Use separate WSL instance for testing
- Clear browser data after tests
- Don't use for personal browsing

### MCP Server Permissions

The Playwright MCP server can:
- ✅ Control browser (open tabs, navigate, click)
- ✅ Read page content
- ✅ Take screenshots
- ✅ Execute JavaScript in pages

**Best practices:**
- Only use on trusted sites
- Review automation prompts
- Use for testing, not production data access

## Performance Tips

### Faster Execution

1. **Use headless mode** for non-visual tests
2. **Disable images** when not needed:
   ```javascript
   await page.route('**/*.{png,jpg,jpeg}', route => route.abort());
   ```
3. **Block unnecessary resources** (ads, analytics)
4. **Reuse browser contexts** instead of launching new browsers

### Resource Management

**Close browsers when done:**
```javascript
await browser.close();
```

**Monitor resource usage:**
```bash
ps aux | grep chromium
```

**Kill hung processes:**
```bash
pkill -f chromium
```

## Use Cases

### 1. Frontend Testing
- Test React/Vue/Angular applications
- Verify UI components render correctly
- Test user interactions
- Validate responsive design

### 2. Integration Testing
- Test full user workflows
- Verify data flows through system
- Test authentication flows
- Validate form submissions

### 3. Regression Testing
- Automated UI regression tests
- Screenshot comparison
- Visual diff detection
- Cross-browser compatibility

### 4. Web Scraping
- Extract data from websites
- Monitor competitors
- Aggregate information
- Research and analysis

### 5. Automated Data Entry
- Fill forms repeatedly
- Upload files in bulk
- Submit applications
- Administrative tasks

## Best Practices

### 1. Structure Your Tests
```
Arrange: Set up test data
Act: Perform actions
Assert: Verify results
Cleanup: Close browser
```

### 2. Use Explicit Waits
```javascript
await page.waitForSelector('button.submit');
await page.waitForLoadState('networkidle');
```

### 3. Handle Errors Gracefully
```javascript
try {
  await page.click('button');
} catch (error) {
  console.error('Click failed:', error);
}
```

### 4. Take Screenshots on Failure
Helpful for debugging:
```javascript
await page.screenshot({ path: 'error.png' });
```

### 5. Clean Up Resources
Always close browsers to free memory:
```javascript
await browser.close();
```

## Integration with Your Project

### Testing the Frontend

Your React frontend (`http://localhost:3000`) can be tested:

**Start frontend:**
```bash
cd ~/sandbox/frontend
npm run dev
```

**Test with Claude:**
```
"Use Playwright to test the frontend at http://localhost:3000:
1. Navigate to home page
2. Verify all components load
3. Test navigation menu
4. Take screenshot"
```

### Testing the API Backend

Test API responses via browser:

**Start backend:**
```bash
cd ~/sandbox/api
source ../venv/bin/activate
python main.py
```

**Test with Claude:**
```
"Open http://localhost:8000/docs in the browser and verify the Swagger UI loads"
```

## Resources

### Official Documentation
- **Playwright:** https://playwright.dev
- **Playwright MCP:** https://github.com/microsoft/playwright-mcp
- **WSLg:** https://github.com/microsoft/wslg

### Example Scripts
- Browser automation examples in Playwright docs
- MCP server examples in GitHub repo

### Community
- Playwright Discord
- GitHub Discussions
- Stack Overflow (playwright tag)

## Limitations

### WSLg Limitations
- ❌ No Flatpak/Snap support
- ❌ Limited window decorations
- ❌ Some window management quirks
- ❌ Clipboard text-only (no images)

### Browser Limitations
- ❌ Requires `--no-sandbox` in WSL
- ❌ No native Chrome extensions support (use Chromium)
- ❌ Some DRM-protected content may not work

### Performance
- Network-dependent (external sites)
- Resource-intensive (browser processes)
- Slower than headless for non-visual tests

## Future Enhancements

### Potential Improvements
- [ ] Add Firefox/WebKit support
- [ ] Configure video recording
- [ ] Set up screenshot comparison
- [ ] Create test suite templates
- [ ] Add mobile device emulation presets
- [ ] Configure custom browser profiles

## Summary

You now have a fully functional browser GUI testing setup:
- ✅ Chromium browser installed and working
- ✅ WSLg displays browser on Windows desktop
- ✅ Playwright MCP connected to Claude Code
- ✅ Can run headed (visible) or headless tests
- ✅ Full automation capabilities available

**Next Steps:**
1. Try the example prompts above
2. Test your own web applications
3. Explore Playwright's advanced features
4. Integrate into your testing workflow

Happy testing! 🎉
