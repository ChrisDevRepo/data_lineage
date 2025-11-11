# Playwright E2E Testing - Phantom Objects & UDF Support

## Setup

### 1. Install Playwright

```bash
cd frontend
npm install -D @playwright/test
npx playwright install  # Installs browser binaries
```

### 2. Add Test Scripts to package.json

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:report": "playwright show-report"
  }
}
```

---

## Running Tests

### **Run All Tests** (Headless)
```bash
npm run test:e2e
```

### **Run with Browser Visible** (Headed)
```bash
npm run test:e2e:headed
```

### **Debug Mode** (Step-through)
```bash
npm run test:e2e:debug
```

### **Interactive UI Mode** (Recommended)
```bash
npm run test:e2e:ui
```

### **View Test Report**
```bash
npm run test:e2e:report
```

---

## Test Coverage

### **Phantom Objects Tests** (`phantom-objects.spec.ts`)

✅ **Visualization:**
- Phantom tables display question mark icon (❓)
- Phantom functions display question mark icon (❓)
- Dashed borders on phantom nodes
- Orange accent color (#ff9800)

✅ **Node Symbols:**
- Circle (●) for Tables/Views
- Square (■) for Stored Procedures
- Diamond (◆) for Functions
- Question Mark (❓) for Phantoms

✅ **Edges:**
- Dotted/dashed lines for phantom connections
- Orange color for phantom edges
- Normal solid lines for real connections

✅ **Interactions:**
- Tooltips show phantom status
- Details panel displays "Not in catalog"
- Hover highlights connected edges
- Click opens node details

✅ **Accessibility:**
- ARIA labels for screen readers
- Keyboard navigation support
- Focus indicators

---

## Writing New Tests

### Example: Test Phantom Function Node

```typescript
import { test, expect } from '@playwright/test';

test('should display phantom function with diamond + question mark', async ({ page }) => {
  await page.goto('/lineage');
  await page.waitForSelector('[data-testid="lineage-graph"]');

  // Find phantom function (negative ID + object_type=Function)
  const phantomFunc = page.locator('[data-node-id^="-"][data-object-type="Function"]').first();

  // Should be visible
  await expect(phantomFunc).toBeVisible();

  // Should have question mark icon (phantom)
  const questionIcon = phantomFunc.locator('svg circle[fill*="#ff9800"]');
  await expect(questionIcon).toBeVisible();

  // Should have dashed border
  const borderStyle = await phantomFunc.evaluate(el =>
    window.getComputedStyle(el).borderStyle
  );
  expect(borderStyle).toContain('dashed');
});
```

---

## Test Data Requirements

For tests to pass, ensure:

1. **Backend running** on `http://localhost:8000`
2. **Frontend running** on `http://localhost:3000`
3. **Test data loaded** with:
   - At least one phantom table (negative ID)
   - At least one function (if testing UDF support)
   - Mixed real and phantom objects

### Generate Test Data

```bash
# Run full reload to create phantoms
./start-app.sh

# Verify phantoms exist
python analyze_function_usage.py
```

---

## Test Selectors

### **Data Attributes to Add** (for reliable testing)

Update your React components to include:

```jsx
// Node component
<div
  data-testid="lineage-node"
  data-node-id={node.id}
  data-object-type={node.object_type}
  data-node-symbol={node.node_symbol}
  data-is-phantom={node.is_phantom}
>
  {/* Node content */}
</div>

// Graph component
<div data-testid="lineage-graph">
  {/* React Flow */}
</div>

// Legend component
<div data-testid="lineage-legend">
  {/* Legend content */}
</div>

// Edge component
<g
  data-edge-source={edge.source}
  data-edge-target={edge.target}
  data-edge-highlighted={isHighlighted}
>
  {/* Edge path */}
</g>
```

---

## CI/CD Integration

### **GitHub Actions Example**

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright Browsers
        run: |
          cd frontend
          npx playwright install --with-deps

      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Debugging Failed Tests

### **1. View Screenshots**
```bash
# Screenshots saved in test-results/
ls test-results/*/test-failed-*.png
```

### **2. View Videos**
```bash
# Videos saved for failed tests
ls test-results/*/video.webm
```

### **3. View Traces** (Time-travel debugging)
```bash
npx playwright show-trace test-results/*/trace.zip
```

### **4. Run Single Test**
```bash
npx playwright test phantom-objects.spec.ts:42  # Line number
```

### **5. Inspect Element**
```bash
# Use debug mode to inspect selectors
npx playwright test --debug
# Then use Playwright Inspector to find selectors
```

---

## Performance Testing

Add performance tests to `phantom-objects.spec.ts`:

```typescript
test('should render large graph with phantoms quickly', async ({ page }) => {
  const startTime = Date.now();

  await page.goto('/lineage');
  await page.waitForSelector('[data-testid="lineage-graph"]');

  // Wait for all nodes to render
  await page.waitForSelector('[data-testid="lineage-node"]');

  const loadTime = Date.now() - startTime;

  // Should load within 3 seconds
  expect(loadTime).toBeLessThan(3000);
});
```

---

## Visual Regression Testing

Install visual comparison addon:

```bash
npm install -D @playwright/test playwright-visual-comparison
```

Add visual tests:

```typescript
test('phantom node should match screenshot', async ({ page }) => {
  await page.goto('/lineage');
  const phantomNode = page.locator('[data-node-id^="-"]').first();

  await expect(phantomNode).toHaveScreenshot('phantom-node.png', {
    maxDiffPixels: 100
  });
});
```

---

## Common Issues

### **1. Tests fail with "Element not found"**
- **Fix:** Add `data-testid` attributes to components
- **Fix:** Increase `timeout` in selectors

### **2. Graph doesn't load**
- **Fix:** Ensure backend is running (`./start-app.sh`)
- **Fix:** Check API endpoint in webServer config

### **3. Flaky tests**
- **Fix:** Use `waitForLoadState('networkidle')`
- **Fix:** Add explicit `waitForSelector()` before actions

### **4. Browser not installed**
- **Fix:** Run `npx playwright install chromium`

---

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [CI Setup](https://playwright.dev/docs/ci)

---

**Ready to test?** Run `npm run test:e2e:ui` for interactive testing!
