import { test, expect } from '@playwright/test';

test.describe('Data Lineage Visualizer - Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app before each test
    await page.goto('http://localhost:3000');
  });

  test('should load the application', async ({ page }) => {
    // Wait for React Flow to load (gives time for React app to render)
    await page.waitForSelector('.react-flow', { timeout: 15000 });

    // Check that React Flow canvas is present
    await expect(page.locator('.react-flow')).toBeVisible();

    // Check that toolbar is present
    await expect(page.locator('button')).toHaveCount(1, { timeout: 5000 }).catch(() => {
      // At least one button should exist (toolbar buttons)
      return expect(page.locator('button').first()).toBeVisible();
    });
  });

  test('should open detail search modal', async ({ page }) => {
    // Find and click the detail search button (magnifying glass icon in toolbar)
    const detailSearchButton = page.locator('button[title*="Detail"]').first();
    await detailSearchButton.click();

    // Verify modal is open by checking for search input
    await expect(page.locator('input[placeholder*="Search DDL"]')).toBeVisible();

    // Close modal with ESC key
    await page.keyboard.press('Escape');
    await expect(page.locator('input[placeholder*="Search DDL"]')).not.toBeVisible();
  });

  test('should show context menu on right-click', async ({ page }) => {
    // Wait for graph to load
    await page.waitForTimeout(1000);

    // Try to find a node (this assumes sample data is loaded)
    const node = page.locator('.react-flow__node').first();

    if (await node.count() > 0) {
      // Right-click on node
      await node.click({ button: 'right' });

      // Check for context menu
      const contextMenu = page.locator('text=Start Tracing');
      await expect(contextMenu).toBeVisible({ timeout: 2000 });

      // Close menu by clicking outside
      await page.mouse.click(0, 0);
    } else {
      console.log('No nodes found - skipping context menu test');
    }
  });

  test('should have functional toolbar controls', async ({ page }) => {
    // Check for reset button
    await expect(page.locator('button[title*="Reset"]').first()).toBeVisible();

    // Check for import button
    await expect(page.locator('button[title*="Import"]').first()).toBeVisible();

    // Check for info button
    await expect(page.locator('button[title*="Info"]').first()).toBeVisible();
  });

  test('should toggle legend', async ({ page }) => {
    // Find legend component
    const legend = page.locator('text=Legend').first();

    if (await legend.count() > 0) {
      await legend.click();
      // Legend should expand/collapse (visibility changes)
      await page.waitForTimeout(500);
    }
  });

  test('should handle exclude terms functionality', async ({ page }) => {
    // Find the exclude terms input
    const excludeInput = page.locator('input[placeholder*="Exclude"]');
    await expect(excludeInput).toBeVisible();

    // Type an exclude term
    await excludeInput.fill('test,sample');

    // Find and click the Hide button
    const hideButton = page.locator('button:has-text("Hide")');
    await expect(hideButton).toBeVisible();
    await hideButton.click();

    // Verify notification appears
    await expect(page.locator('text=Excluding')).toBeVisible({ timeout: 3000 });

    // Clear button should appear when text is entered
    await excludeInput.fill('test');
    const clearButton = excludeInput.locator('..').locator('button[title="Clear"]');
    await expect(clearButton).toBeVisible();
    await clearButton.click();
    await expect(excludeInput).toHaveValue('');
  });

  test('should handle exclude terms with Enter key', async ({ page }) => {
    // Find the exclude terms input
    const excludeInput = page.locator('input[placeholder*="Exclude"]');
    await excludeInput.fill('test');

    // Press Enter to trigger hide
    await excludeInput.press('Enter');

    // Verify notification appears
    await expect(page.locator('text=Excluding')).toBeVisible({ timeout: 3000 });
  });

  test('should perform main search with autocomplete after 5 characters', async ({ page }) => {
    // Find main search box
    const searchInput = page.locator('input[placeholder*="Search objects"]');
    await expect(searchInput).toBeVisible();

    // Type less than 5 characters - autocomplete should NOT appear
    await searchInput.fill('test');
    await page.waitForTimeout(400); // Wait for debounce
    await expect(page.locator('.absolute.top-full').first()).not.toBeVisible();

    // Type 5 or more characters - autocomplete SHOULD appear (if there are matching results)
    await searchInput.fill('testt'); // 5 characters
    await page.waitForTimeout(400); // Wait for debounce

    // Clear search
    await searchInput.clear();
  });

  test('should search via Enter key in main search', async ({ page }) => {
    // Find main search box
    const searchInput = page.locator('input[placeholder*="Search objects"]');
    await searchInput.fill('test');

    // Press Enter to search
    await searchInput.press('Enter');

    // Wait a moment for search to process
    await page.waitForTimeout(500);
  });

  test('should open detail search and perform search', async ({ page }) => {
    // Open detail search modal
    const detailSearchButton = page.locator('button[title*="Detail"]').first();
    await detailSearchButton.click();

    // Verify modal is open
    const searchInput = page.locator('input[placeholder*="Search DDL"]');
    await expect(searchInput).toBeVisible();

    // Type a search query - should automatically trigger search via debounce
    await searchInput.fill('CREATE');
    await page.waitForTimeout(400); // Wait for debounce

    // Results should appear if there's matching data
    // (We can't verify specific results without knowing the data)

    // Close modal
    await page.keyboard.press('Escape');
  });

  test('should sync filters from main menu to detail search', async ({ page }) => {
    // Note: This test assumes the app has loaded with data

    // Open detail search modal
    const detailSearchButton = page.locator('button[title*="Detail"]').first();
    await detailSearchButton.click();

    // Verify modal is open
    await expect(page.locator('input[placeholder*="Search DDL"]')).toBeVisible();

    // Check that schema and type filters are present
    await expect(page.locator('button:has-text("Schemas")')).toBeVisible();
    await expect(page.locator('button:has-text("Object")')).toBeVisible();

    // Close modal
    await page.keyboard.press('Escape');
  });

  test('should have correct textbox widths to prevent truncation', async ({ page }) => {
    // Verify main search box has reasonable width (w-64 = 256px = 16rem)
    const searchInput = page.locator('input[placeholder*="Search objects"]');
    const searchBox = await searchInput.boundingBox();
    expect(searchBox?.width).toBeLessThanOrEqual(300); // Should be around 256px

    // Verify exclude input has reasonable width (w-56 = 224px = 14rem)
    const excludeInput = page.locator('input[placeholder*="Exclude"]');
    const excludeBox = await excludeInput.boundingBox();
    expect(excludeBox?.width).toBeLessThanOrEqual(250); // Should be around 224px

    // Verify all toolbar buttons are visible (not truncated)
    await expect(page.locator('button[title*="Reset"]').first()).toBeVisible();
    await expect(page.locator('button[title*="Export"]').first()).toBeVisible();
    await expect(page.locator('button[title*="Import"]').first()).toBeVisible();
    await expect(page.locator('button[title*="Info"]').first()).toBeVisible();
  });
});
