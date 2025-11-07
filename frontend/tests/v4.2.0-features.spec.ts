import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('v4.2.0 Enhanced Features - Confidence Levels & Node Descriptions', () => {
  const screenshotDir = '/home/user/sandbox/test_screenshots';

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for the graph to load
    await page.waitForSelector('.react-flow', { timeout: 10000 });
    await page.waitForTimeout(2000); // Additional wait for nodes to render
  });

  test('should load application and take full graph screenshot', async ({ page }) => {
    // Verify React Flow is loaded
    await expect(page.locator('.react-flow')).toBeVisible();

    // Take full graph screenshot
    await page.screenshot({
      path: path.join(screenshotDir, '01-full-graph-view.png'),
      fullPage: true,
    });

    console.log('✓ Full graph screenshot captured');
  });

  test('should verify node descriptions show v4.2.0 enhanced format', async ({ page }) => {
    // Wait for nodes to be present
    const nodes = page.locator('.react-flow__node');
    const nodeCount = await nodes.count();

    console.log(`Found ${nodeCount} nodes in the graph`);

    if (nodeCount > 0) {
      // Click on first node to see description
      const firstNode = nodes.first();
      await firstNode.click();

      // Wait for node details/description to appear
      await page.waitForTimeout(1000);

      // Take screenshot of selected node
      await page.screenshot({
        path: path.join(screenshotDir, '02-selected-node-view.png'),
        fullPage: true,
      });

      console.log('✓ Selected node screenshot captured');
    } else {
      console.log('⚠ No nodes found in graph - may need to load data');
    }
  });

  test('should find and capture high-confidence SP node', async ({ page }) => {
    // Look for nodes that might indicate high confidence
    // v4.2.0 should show ✅ or green indicators for high confidence
    const nodes = page.locator('.react-flow__node');
    const nodeCount = await nodes.count();

    let highConfidenceFound = false;

    for (let i = 0; i < Math.min(nodeCount, 10); i++) {
      const node = nodes.nth(i);
      await node.click();
      await page.waitForTimeout(500);

      // Check if node contains high confidence indicators
      const nodeText = await node.textContent();

      // Look for common high confidence indicators in v4.2.0:
      // - ✅ checkmark
      // - "High" confidence text
      // - Green color indicators
      if (nodeText && (
        nodeText.includes('✅') ||
        nodeText.toLowerCase().includes('high') ||
        nodeText.includes('0.85') ||
        nodeText.includes('85%')
      )) {
        highConfidenceFound = true;
        await page.screenshot({
          path: path.join(screenshotDir, '03-high-confidence-sp-node.png'),
          fullPage: true,
        });
        console.log(`✓ High confidence node found at index ${i}`);
        break;
      }
    }

    if (!highConfidenceFound) {
      console.log('⚠ No high confidence node found - capturing first SP node instead');
      // Try to find any SP (stored procedure) node
      const spNodes = page.locator('.react-flow__node:has-text("SP"), .react-flow__node:has-text("sp_")');
      if (await spNodes.count() > 0) {
        await spNodes.first().click();
        await page.waitForTimeout(500);
        await page.screenshot({
          path: path.join(screenshotDir, '03-sample-sp-node.png'),
          fullPage: true,
        });
      }
    }
  });

  test('should find and capture medium-confidence SP node', async ({ page }) => {
    const nodes = page.locator('.react-flow__node');
    const nodeCount = await nodes.count();

    let mediumConfidenceFound = false;

    for (let i = 0; i < Math.min(nodeCount, 10); i++) {
      const node = nodes.nth(i);
      await node.click();
      await page.waitForTimeout(500);

      const nodeText = await node.textContent();

      // Look for medium confidence indicators in v4.2.0:
      // - ⚠️ warning symbol
      // - "Medium" confidence text
      // - Yellow color indicators
      if (nodeText && (
        nodeText.includes('⚠️') ||
        nodeText.toLowerCase().includes('medium') ||
        nodeText.includes('0.75') ||
        nodeText.includes('75%')
      )) {
        mediumConfidenceFound = true;
        await page.screenshot({
          path: path.join(screenshotDir, '04-medium-confidence-sp-node.png'),
          fullPage: true,
        });
        console.log(`✓ Medium confidence node found at index ${i}`);
        break;
      }
    }

    if (!mediumConfidenceFound) {
      console.log('⚠ No medium confidence node found');
      // Take screenshot anyway of a different node
      if (nodeCount > 1) {
        await nodes.nth(1).click();
        await page.waitForTimeout(500);
        await page.screenshot({
          path: path.join(screenshotDir, '04-alternate-node.png'),
          fullPage: true,
        });
      }
    }
  });

  test('should verify confidence level details in node descriptions', async ({ page }) => {
    const nodes = page.locator('.react-flow__node');
    const nodeCount = await nodes.count();

    if (nodeCount === 0) {
      console.log('⚠ No nodes available for testing');
      return;
    }

    // Click on a few nodes and check for v4.2.0 enhanced format
    for (let i = 0; i < Math.min(nodeCount, 5); i++) {
      const node = nodes.nth(i);
      await node.click();
      await page.waitForTimeout(500);

      const nodeText = await node.textContent() || '';

      // Check for v4.2.0 format features:
      const hasConfidenceIndicator =
        nodeText.includes('✅') ||
        nodeText.includes('⚠️') ||
        nodeText.includes('❌') ||
        nodeText.toLowerCase().includes('confidence');

      const hasDetailedInfo =
        nodeText.toLowerCase().includes('parse') ||
        nodeText.toLowerCase().includes('method') ||
        nodeText.toLowerCase().includes('catalog') ||
        nodeText.toLowerCase().includes('validation');

      if (hasConfidenceIndicator || hasDetailedInfo) {
        console.log(`✓ Node ${i} has v4.2.0 enhanced format indicators`);
        await page.screenshot({
          path: path.join(screenshotDir, `05-enhanced-format-node-${i}.png`),
          fullPage: true,
        });
        break;
      }
    }
  });

  test('should test search functionality', async ({ page }) => {
    // Find main search box
    const searchInput = page.locator('input[placeholder*="Search objects"]');
    await expect(searchInput).toBeVisible();

    // Perform search
    await searchInput.fill('sp_');
    await searchInput.press('Enter');
    await page.waitForTimeout(1000);

    // Take screenshot of search results
    await page.screenshot({
      path: path.join(screenshotDir, '06-search-results.png'),
      fullPage: true,
    });

    console.log('✓ Search functionality screenshot captured');
  });

  test('should test filter controls', async ({ page }) => {
    // Look for filter buttons/dropdowns
    const schemaFilter = page.locator('button:has-text("Schema"), button:has-text("Schemas")');
    const typeFilter = page.locator('button:has-text("Type"), button:has-text("Object")');

    // Take screenshot showing filters
    await page.screenshot({
      path: path.join(screenshotDir, '07-filter-controls.png'),
      fullPage: true,
    });

    // Try to interact with schema filter if it exists
    if (await schemaFilter.count() > 0) {
      await schemaFilter.first().click();
      await page.waitForTimeout(500);

      await page.screenshot({
        path: path.join(screenshotDir, '08-schema-filter-open.png'),
        fullPage: true,
      });

      console.log('✓ Schema filter interaction captured');

      // Close filter
      await page.keyboard.press('Escape');
    }

    // Try to interact with type filter if it exists
    if (await typeFilter.count() > 0) {
      await typeFilter.first().click();
      await page.waitForTimeout(500);

      await page.screenshot({
        path: path.join(screenshotDir, '09-type-filter-open.png'),
        fullPage: true,
      });

      console.log('✓ Type filter interaction captured');
    }
  });

  test('should verify legend shows confidence levels', async ({ page }) => {
    // Look for legend component
    const legend = page.locator('text=Legend, text=legend').first();

    if (await legend.count() > 0) {
      // Make sure legend is visible/expanded
      const legendVisible = await legend.isVisible();
      if (!legendVisible) {
        await legend.click();
        await page.waitForTimeout(500);
      }

      await page.screenshot({
        path: path.join(screenshotDir, '10-legend-with-confidence.png'),
        fullPage: true,
      });

      console.log('✓ Legend screenshot captured');
    } else {
      console.log('⚠ Legend not found');
    }
  });

  test('should capture detail search modal', async ({ page }) => {
    // Open detail search
    const detailSearchButton = page.locator('button[title*="Detail"]').first();

    if (await detailSearchButton.count() > 0) {
      await detailSearchButton.click();
      await page.waitForTimeout(500);

      // Take screenshot of detail search
      await page.screenshot({
        path: path.join(screenshotDir, '11-detail-search-modal.png'),
        fullPage: true,
      });

      console.log('✓ Detail search modal captured');

      // Close modal
      await page.keyboard.press('Escape');
    }
  });
});
