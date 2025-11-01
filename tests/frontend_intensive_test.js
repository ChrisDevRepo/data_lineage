/**
 * Comprehensive Frontend Testing Suite
 * Tests all user interactions, error tracking, and performance monitoring
 *
 * Usage: node tests/frontend_intensive_test.js
 */

const { chromium } = require('playwright');
const fs = require('fs');

class FrontendTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.errors = [];
    this.warnings = [];
    this.networkRequests = [];
    this.performanceMetrics = {};
    this.testResults = {
      passed: [],
      failed: [],
      warnings: []
    };
  }

  async init() {
    console.log('🚀 Starting Comprehensive Frontend Test Suite\n');
    console.log('Target: http://localhost:3000\n');
    console.log('═══════════════════════════════════════════════════════════\n');

    this.browser = await chromium.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    this.page = await this.browser.newPage();

    // Track console messages
    this.page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();

      if (type === 'error') {
        this.errors.push({ time: new Date().toISOString(), text });
        console.log(`  ❌ Console Error: ${text}`);
      } else if (type === 'warning') {
        this.warnings.push({ time: new Date().toISOString(), text });
        console.log(`  ⚠️  Console Warning: ${text}`);
      }
    });

    // Track page errors
    this.page.on('pageerror', error => {
      this.errors.push({
        time: new Date().toISOString(),
        text: `Page Error: ${error.message}`,
        stack: error.stack
      });
      console.log(`  ❌ Page Error: ${error.message}`);
    });

    // Track network requests
    this.page.on('request', request => {
      this.networkRequests.push({
        method: request.method(),
        url: request.url(),
        resourceType: request.resourceType()
      });
    });

    // Track failed requests
    this.page.on('requestfailed', request => {
      const failure = {
        url: request.url(),
        failure: request.failure()?.errorText
      };
      console.log(`  ❌ Request Failed: ${request.url()} - ${failure.failure}`);
      this.testResults.failed.push(`Network: ${failure.url}`);
    });
  }

  async runTest(name, testFn) {
    try {
      console.log(`\n▶️  Test: ${name}`);
      await testFn();
      console.log(`   ✅ Passed`);
      this.testResults.passed.push(name);
    } catch (error) {
      console.log(`   ❌ Failed: ${error.message}`);
      this.testResults.failed.push(`${name}: ${error.message}`);
      // Take screenshot on failure
      await this.page.screenshot({
        path: `tests/screenshots/error_${Date.now()}.png`
      });
    }
  }

  async measurePerformance() {
    // Get performance metrics
    const metrics = await this.page.evaluate(() => {
      const perf = window.performance;
      const navigation = perf.getEntriesByType('navigation')[0];

      return {
        // Page load metrics
        domContentLoaded: navigation?.domContentLoadedEventEnd - navigation?.domContentLoadedEventStart,
        loadComplete: navigation?.loadEventEnd - navigation?.loadEventStart,
        domInteractive: navigation?.domInteractive - navigation?.fetchStart,

        // Resource timing
        resourceCount: perf.getEntriesByType('resource').length,

        // Memory (if available)
        memory: performance.memory ? {
          usedJSHeapSize: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
          totalJSHeapSize: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
          jsHeapSizeLimit: (performance.memory.jsHeapSizeLimit / 1048576).toFixed(2) + ' MB'
        } : null
      };
    });

    this.performanceMetrics = metrics;
  }

  async runAllTests() {
    // Test 1: Page Load
    await this.runTest('Page loads successfully', async () => {
      const startTime = Date.now();
      await this.page.goto('http://localhost:3000', {
        waitUntil: 'networkidle',
        timeout: 30000
      });
      const loadTime = Date.now() - startTime;
      console.log(`   ⏱️  Load time: ${loadTime}ms`);

      if (loadTime > 5000) {
        this.testResults.warnings.push(`Slow page load: ${loadTime}ms`);
      }
    });

    // Test 2: Title and metadata
    await this.runTest('Page title is correct', async () => {
      const title = await this.page.title();
      if (!title || title === '') {
        throw new Error('Page title is empty');
      }
      console.log(`   📄 Title: "${title}"`);
    });

    // Test 3: Main container
    await this.runTest('Main React container renders', async () => {
      const rootExists = await this.page.locator('#root').isVisible();
      if (!rootExists) {
        throw new Error('React root element not found');
      }
    });

    // Test 4: Check for all interactive elements
    await this.runTest('Enumerate all interactive elements', async () => {
      const buttons = await this.page.locator('button').count();
      const inputs = await this.page.locator('input').count();
      const selects = await this.page.locator('select').count();
      const links = await this.page.locator('a').count();

      console.log(`   🔘 Buttons: ${buttons}`);
      console.log(`   📝 Inputs: ${inputs}`);
      console.log(`   📋 Selects: ${selects}`);
      console.log(`   🔗 Links: ${links}`);

      const totalInteractive = buttons + inputs + selects + links;
      if (totalInteractive === 0) {
        this.testResults.warnings.push('No interactive elements found');
      }
    });

    // Test 5: Click all visible buttons
    await this.runTest('Click all visible buttons', async () => {
      const buttons = await this.page.locator('button:visible').all();
      console.log(`   Found ${buttons.length} visible buttons`);

      for (let i = 0; i < buttons.length; i++) {
        try {
          const text = await buttons[i].textContent();
          console.log(`   Clicking: "${text?.trim() || 'unnamed'}"`);
          await buttons[i].click({ timeout: 2000 });
          await this.page.waitForTimeout(500); // Wait for any animations
        } catch (err) {
          console.log(`   ⚠️  Could not click button ${i}: ${err.message}`);
        }
      }
    });

    // Test 6: Test all input fields
    await this.runTest('Test all input fields', async () => {
      const inputs = await this.page.locator('input:visible').all();
      console.log(`   Found ${inputs.length} visible inputs`);

      for (let i = 0; i < inputs.length; i++) {
        try {
          const type = await inputs[i].getAttribute('type');
          const placeholder = await inputs[i].getAttribute('placeholder');
          console.log(`   Testing input: type="${type}", placeholder="${placeholder}"`);

          // Type test data
          if (type !== 'file' && type !== 'checkbox' && type !== 'radio') {
            await inputs[i].fill('test_data_123');
            await this.page.waitForTimeout(300);
            await inputs[i].clear();
          } else if (type === 'checkbox') {
            await inputs[i].check();
            await this.page.waitForTimeout(200);
            await inputs[i].uncheck();
          }
        } catch (err) {
          console.log(`   ⚠️  Could not interact with input ${i}: ${err.message}`);
        }
      }
    });

    // Test 7: Test select dropdowns
    await this.runTest('Test all select dropdowns', async () => {
      const selects = await this.page.locator('select:visible').all();
      console.log(`   Found ${selects.length} visible selects`);

      for (const select of selects) {
        try {
          const options = await select.locator('option').all();
          console.log(`   Select has ${options.length} options`);

          if (options.length > 1) {
            // Try selecting each option
            for (let i = 0; i < Math.min(options.length, 3); i++) {
              const value = await options[i].getAttribute('value');
              await select.selectOption({ index: i });
              await this.page.waitForTimeout(300);
            }
          }
        } catch (err) {
          console.log(`   ⚠️  Could not interact with select: ${err.message}`);
        }
      }
    });

    // Test 8: Test keyboard navigation
    await this.runTest('Test keyboard navigation', async () => {
      console.log(`   Testing Tab key navigation`);

      // Press Tab multiple times
      for (let i = 0; i < 5; i++) {
        await this.page.keyboard.press('Tab');
        await this.page.waitForTimeout(200);
      }

      // Press Shift+Tab to go back
      for (let i = 0; i < 3; i++) {
        await this.page.keyboard.press('Shift+Tab');
        await this.page.waitForTimeout(200);
      }
    });

    // Test 9: Test hover interactions
    await this.runTest('Test hover interactions', async () => {
      const hoverables = await this.page.locator('button:visible, a:visible').all();
      const sampleSize = Math.min(hoverables.length, 5);

      console.log(`   Hovering over ${sampleSize} elements`);
      for (let i = 0; i < sampleSize; i++) {
        try {
          await hoverables[i].hover();
          await this.page.waitForTimeout(300);
        } catch (err) {
          // Ignore hover errors
        }
      }
    });

    // Test 10: Accessibility check
    await this.runTest('Check basic accessibility', async () => {
      const images = await this.page.locator('img').all();
      let missingAlt = 0;

      for (const img of images) {
        const alt = await img.getAttribute('alt');
        if (!alt) missingAlt++;
      }

      console.log(`   Images without alt: ${missingAlt}/${images.length}`);
      if (missingAlt > 0) {
        this.testResults.warnings.push(`${missingAlt} images missing alt text`);
      }

      // Check for ARIA labels
      const ariaElements = await this.page.locator('[aria-label]').count();
      console.log(`   Elements with aria-label: ${ariaElements}`);
    });

    // Test 11: Responsive design check
    await this.runTest('Test responsive breakpoints', async () => {
      const viewports = [
        { name: 'Mobile', width: 375, height: 667 },
        { name: 'Tablet', width: 768, height: 1024 },
        { name: 'Desktop', width: 1920, height: 1080 }
      ];

      for (const viewport of viewports) {
        console.log(`   Testing ${viewport.name}: ${viewport.width}x${viewport.height}`);
        await this.page.setViewportSize({ width: viewport.width, height: viewport.height });
        await this.page.waitForTimeout(1000);

        // Check if content is still visible
        const rootVisible = await this.page.locator('#root').isVisible();
        if (!rootVisible) {
          throw new Error(`Content not visible at ${viewport.name} size`);
        }
      }

      // Reset to default
      await this.page.setViewportSize({ width: 1280, height: 720 });
    });

    // Test 12: Check for memory leaks (basic)
    await this.runTest('Monitor memory usage', async () => {
      await this.measurePerformance();

      if (this.performanceMetrics.memory) {
        console.log(`   Used heap: ${this.performanceMetrics.memory.usedJSHeapSize}`);
        console.log(`   Total heap: ${this.performanceMetrics.memory.totalJSHeapSize}`);
        console.log(`   Heap limit: ${this.performanceMetrics.memory.jsHeapSizeLimit}`);
      } else {
        console.log(`   ⚠️  Memory metrics not available`);
      }
    });

    // Test 13: Network activity analysis
    await this.runTest('Analyze network activity', async () => {
      const byType = {};
      this.networkRequests.forEach(req => {
        byType[req.resourceType] = (byType[req.resourceType] || 0) + 1;
      });

      console.log(`   Total requests: ${this.networkRequests.length}`);
      Object.entries(byType).forEach(([type, count]) => {
        console.log(`   ${type}: ${count}`);
      });
    });

    // Test 14: Take final screenshots
    await this.runTest('Capture final state screenshots', async () => {
      await this.page.screenshot({
        path: 'tests/screenshots/final_fullpage.png',
        fullPage: true
      });
      console.log(`   📸 Full page screenshot saved`);

      await this.page.screenshot({
        path: 'tests/screenshots/final_viewport.png'
      });
      console.log(`   📸 Viewport screenshot saved`);
    });
  }

  generateReport() {
    console.log('\n');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('═══════════════════════════════════════════════════════════\n');

    console.log(`✅ Passed: ${this.testResults.passed.length}`);
    console.log(`❌ Failed: ${this.testResults.failed.length}`);
    console.log(`⚠️  Warnings: ${this.testResults.warnings.length}`);
    console.log(`📝 Console Errors: ${this.errors.length}`);
    console.log(`⚠️  Console Warnings: ${this.warnings.length}`);

    if (this.testResults.failed.length > 0) {
      console.log('\n❌ Failed Tests:');
      this.testResults.failed.forEach(test => {
        console.log(`   - ${test}`);
      });
    }

    if (this.testResults.warnings.length > 0) {
      console.log('\n⚠️  Warnings:');
      this.testResults.warnings.forEach(warning => {
        console.log(`   - ${warning}`);
      });
    }

    if (this.errors.length > 0) {
      console.log('\n❌ Console Errors:');
      this.errors.slice(0, 10).forEach(err => {
        console.log(`   - ${err.text}`);
      });
      if (this.errors.length > 10) {
        console.log(`   ... and ${this.errors.length - 10} more`);
      }
    }

    console.log('\n📈 Performance Metrics:');
    if (this.performanceMetrics.domContentLoaded !== undefined) {
      console.log(`   DOM Content Loaded: ${this.performanceMetrics.domContentLoaded?.toFixed(2)}ms`);
      console.log(`   Page Load Complete: ${this.performanceMetrics.loadComplete?.toFixed(2)}ms`);
      console.log(`   DOM Interactive: ${this.performanceMetrics.domInteractive?.toFixed(2)}ms`);
      console.log(`   Resources Loaded: ${this.performanceMetrics.resourceCount}`);
    }

    // Save detailed report to file
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        passed: this.testResults.passed.length,
        failed: this.testResults.failed.length,
        warnings: this.testResults.warnings.length,
        consoleErrors: this.errors.length,
        consoleWarnings: this.warnings.length
      },
      tests: this.testResults,
      errors: this.errors,
      warnings: this.warnings,
      performance: this.performanceMetrics,
      networkRequests: {
        total: this.networkRequests.length,
        byType: this.networkRequests.reduce((acc, req) => {
          acc[req.resourceType] = (acc[req.resourceType] || 0) + 1;
          return acc;
        }, {})
      }
    };

    fs.writeFileSync(
      'tests/test_report.json',
      JSON.stringify(report, null, 2)
    );
    console.log('\n📄 Detailed report saved to: tests/test_report.json');

    console.log('\n═══════════════════════════════════════════════════════════\n');

    // Return exit code
    return this.testResults.failed.length === 0 && this.errors.length === 0 ? 0 : 1;
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

// Run the test suite
(async () => {
  const tester = new FrontendTester();

  try {
    await tester.init();
    await tester.runAllTests();
    const exitCode = tester.generateReport();
    await tester.cleanup();
    process.exit(exitCode);
  } catch (error) {
    console.error('\n❌ Test suite failed:', error);
    await tester.cleanup();
    process.exit(1);
  }
})();
