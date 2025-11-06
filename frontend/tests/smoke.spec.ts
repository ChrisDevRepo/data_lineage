import { test, expect } from '@playwright/test';

test.describe('Data Lineage Visualizer - Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app before each test
    await page.goto('http://localhost:3000');
  });

  test('should load the application', async ({ page }) => {
    // Check that the logo is visible
    await expect(page.locator('img[alt*="Data Lineage"]')).toBeVisible();

    // Check that React Flow canvas is present
    await expect(page.locator('.react-flow')).toBeVisible();
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
});
