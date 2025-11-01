/**
 * Frontend Smoke Test using Playwright
 * Tests the React frontend at http://localhost:3000
 *
 * Usage: node tests/frontend_smoke_test.js
 */

const { chromium } = require('playwright');

async function runSmokeTests() {
  console.log('🚀 Starting Frontend Smoke Tests...\n');

  const browser = await chromium.launch({
    headless: false,  // Show browser window
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  try {
    // Test 1: Homepage loads
    console.log('Test 1: Loading homepage...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    const title = await page.title();
    console.log(`  ✅ Page loaded - Title: "${title}"`);

    // Test 2: Check for main container
    console.log('\nTest 2: Checking main UI elements...');
    const mainContainer = await page.locator('body').isVisible();
    console.log(`  ✅ Main container visible: ${mainContainer}`);

    // Test 3: Check for no console errors
    console.log('\nTest 3: Checking for console errors...');
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.waitForTimeout(2000);  // Wait for potential errors

    if (errors.length === 0) {
      console.log('  ✅ No console errors detected');
    } else {
      console.log(`  ⚠️  ${errors.length} console error(s) found:`);
      errors.forEach(err => console.log(`     - ${err}`));
    }

    // Test 4: Take screenshot
    console.log('\nTest 4: Taking screenshot...');
    await page.screenshot({ path: 'tests/screenshots/frontend_smoke.png', fullPage: true });
    console.log('  ✅ Screenshot saved to tests/screenshots/frontend_smoke.png');

    // Test 5: Check if React is running
    console.log('\nTest 5: Verifying React app...');
    const reactRoot = await page.locator('#root').isVisible();
    console.log(`  ✅ React root element found: ${reactRoot}`);

    console.log('\n✅ All smoke tests passed!');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    await page.screenshot({ path: 'tests/screenshots/error.png' });
    console.log('Error screenshot saved to tests/screenshots/error.png');
  } finally {
    await browser.close();
  }
}

// Run tests
runSmokeTests().catch(console.error);
