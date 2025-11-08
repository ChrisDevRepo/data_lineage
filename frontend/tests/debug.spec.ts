import { test, expect } from '@playwright/test';

test.describe('Debug: What Playwright Sees', () => {
  test('should capture page content and console logs', async ({ page }) => {
    // Listen for console messages
    const consoleLogs = [];
    page.on('console', msg => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));

    // Listen for page errors
    const pageErrors = [];
    page.on('pageerror', err => pageErrors.push(err.message));

    await page.goto('http://localhost:3000');

    // Wait a bit for React to render
    await page.waitForTimeout(5000);

    // Get page title
    const title = await page.title();
    console.log('Page title:', title);

    // Get page content
    const content = await page.content();
    console.log('Page HTML length:', content.length);

    // Check for React root
    const hasRoot = await page.locator('#root').count();
    console.log('React root found:', hasRoot > 0);

    // Check for any images
    const imgCount = await page.locator('img').count();
    console.log('Images found:', imgCount);

    // Check for React Flow canvas
    const reactFlowCount = await page.locator('.react-flow').count();
    console.log('React Flow elements:', reactFlowCount);

    // Print console logs
    console.log('\n=== Console Logs ===');
    consoleLogs.forEach(log => console.log(log));

    // Print errors
    if (pageErrors.length > 0) {
      console.log('\n=== Page Errors ===');
      pageErrors.forEach(err => console.log(err));
    }

    // Take screenshot
    await page.screenshot({ path: '/tmp/debug-screenshot.png', fullPage: true });
    console.log('Screenshot saved to /tmp/debug-screenshot.png');
  });
});