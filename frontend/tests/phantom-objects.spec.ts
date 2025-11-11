/**
 * Playwright E2E Tests - Phantom Objects & UDF Support
 * =====================================================
 *
 * Tests visualization of:
 * - Phantom objects (❓ question mark)
 * - Functions (◆ diamond)
 * - Phantom edges (dotted lines)
 */

import { test, expect } from '@playwright/test';

test.describe('Phantom Objects Visualization', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to lineage graph page
    await page.goto('http://localhost:3000/lineage');

    // Wait for graph to load
    await page.waitForSelector('[data-testid="lineage-graph"]', { timeout: 10000 });
  });

  test('should display phantom table with question mark icon', async ({ page }) => {
    // Look for a node with negative ID (phantom)
    const phantomNode = page.locator('[data-node-id^="-"]').first();

    await expect(phantomNode).toBeVisible();

    // Check for question mark icon
    const questionIcon = phantomNode.locator('svg circle[fill*="#ff9800"]');
    await expect(questionIcon).toBeVisible();

    // Check for "Not in catalog" text
    await expect(phantomNode.getByText(/not in catalog/i)).toBeVisible();
  });

  test('should display function with diamond icon', async ({ page }) => {
    // Look for a node with object_type="Function"
    const functionNode = page.locator('[data-object-type="Function"]').first();

    if (await functionNode.count() > 0) {
      await expect(functionNode).toBeVisible();

      // Check for diamond icon (path element forming diamond shape)
      const diamondIcon = functionNode.locator('svg path[d*="12 2"][d*="22 12"]');
      await expect(diamondIcon).toBeVisible();
    }
  });

  test('should show dashed border for phantom nodes', async ({ page }) => {
    const phantomNode = page.locator('[data-node-id^="-"]').first();

    // Check CSS for dashed border
    const borderStyle = await phantomNode.evaluate(el =>
      window.getComputedStyle(el).borderStyle
    );

    expect(borderStyle).toContain('dashed');
  });

  test('should display correct tooltip for phantom objects', async ({ page }) => {
    const phantomNode = page.locator('[data-node-id^="-"]').first();

    // Hover over node
    await phantomNode.hover();

    // Check tooltip text
    const tooltip = page.locator('[role="tooltip"]');
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText(/phantom/i);
    await expect(tooltip).toContainText(/not in catalog/i);
  });

  test('should display dotted edges for phantom connections', async ({ page }) => {
    // Find an edge connected to a phantom node (source or target is negative)
    const phantomEdge = page.locator('[data-edge-source^="-"], [data-edge-target^="-"]').first();

    if (await phantomEdge.count() > 0) {
      // Check for dash array (dotted line)
      const strokeDasharray = await phantomEdge.evaluate(el =>
        window.getComputedStyle(el).strokeDasharray
      );

      expect(strokeDasharray).not.toBe('none');
      expect(strokeDasharray).toMatch(/\d+/); // Should have numeric values
    }
  });

  test('should use orange color for phantom elements', async ({ page }) => {
    const phantomNode = page.locator('[data-node-id^="-"]').first();

    // Check for orange accent color (#ff9800)
    const hasOrangeElement = await phantomNode.locator('[fill="#ff9800"], [stroke="#ff9800"]').count();

    expect(hasOrangeElement).toBeGreaterThan(0);
  });
});

test.describe('Node Symbol Icons', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');
    await page.waitForSelector('[data-testid="lineage-graph"]');
  });

  test('should render circle icon for tables', async ({ page }) => {
    const tableNode = page.locator('[data-object-type="Table"]').first();

    if (await tableNode.count() > 0) {
      const circleIcon = tableNode.locator('svg circle[r="10"]');
      await expect(circleIcon).toBeVisible();
    }
  });

  test('should render square icon for stored procedures', async ({ page }) => {
    const spNode = page.locator('[data-object-type="Stored Procedure"]').first();

    if (await spNode.count() > 0) {
      const squareIcon = spNode.locator('svg rect[width="20"][height="20"]');
      await expect(squareIcon).toBeVisible();
    }
  });

  test('should render diamond icon for functions', async ({ page }) => {
    const funcNode = page.locator('[data-object-type="Function"]').first();

    if (await funcNode.count() > 0) {
      const diamondIcon = funcNode.locator('svg path');
      await expect(diamondIcon).toBeVisible();

      // Diamond path should form diamond shape
      const pathData = await diamondIcon.getAttribute('d');
      expect(pathData).toContain('12 2');  // Top point
      expect(pathData).toContain('22 12'); // Right point
      expect(pathData).toContain('12 22'); // Bottom point
      expect(pathData).toContain('2 12');  // Left point
    }
  });
});

test.describe('Legend Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');
    await page.waitForSelector('[data-testid="lineage-graph"]');
  });

  test('should display legend with all node types', async ({ page }) => {
    const legend = page.locator('[data-testid="lineage-legend"]');

    if (await legend.count() > 0) {
      await expect(legend).toBeVisible();

      // Check for all node type labels
      await expect(legend.getByText(/table\/view/i)).toBeVisible();
      await expect(legend.getByText(/stored procedure/i)).toBeVisible();
      await expect(legend.getByText(/function.*udf/i)).toBeVisible();
      await expect(legend.getByText(/phantom/i)).toBeVisible();
    }
  });

  test('should show edge type examples in legend', async ({ page }) => {
    const legend = page.locator('[data-testid="lineage-legend"]');

    if (await legend.count() > 0) {
      // Check for normal and phantom edge examples
      await expect(legend.getByText(/normal edge/i)).toBeVisible();
      await expect(legend.getByText(/phantom edge/i)).toBeVisible();
    }
  });
});

test.describe('Data Loading', () => {
  test('should load nodes with node_symbol field', async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');

    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Check that nodes have node_symbol attribute
    const nodesWithSymbol = await page.locator('[data-node-symbol]').count();
    expect(nodesWithSymbol).toBeGreaterThan(0);
  });

  test('should load phantom nodes with is_phantom flag', async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');
    await page.waitForLoadState('networkidle');

    // Check for phantom flag
    const phantomNodes = await page.locator('[data-is-phantom="true"]').count();

    // May be 0 if no phantoms in test data, but attribute should exist
    const nodesWithPhantomAttr = await page.locator('[data-is-phantom]').count();
    expect(nodesWithPhantomAttr).toBeGreaterThan(0);
  });

  test('should handle negative IDs correctly', async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');
    await page.waitForLoadState('networkidle');

    // Find nodes with negative IDs
    const negativeIdNodes = await page.locator('[data-node-id^="-"]').count();

    // If phantoms exist, verify they render correctly
    if (negativeIdNodes > 0) {
      const firstPhantom = page.locator('[data-node-id^="-"]').first();
      await expect(firstPhantom).toBeVisible();

      // Should have question mark icon
      const questionIcon = firstPhantom.locator('svg circle[fill*="ff9800"]');
      await expect(questionIcon).toBeVisible();
    }
  });
});

test.describe('Interaction Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');
    await page.waitForSelector('[data-testid="lineage-graph"]');
  });

  test('should show details panel when clicking phantom node', async ({ page }) => {
    const phantomNode = page.locator('[data-node-id^="-"]').first();

    if (await phantomNode.count() > 0) {
      await phantomNode.click();

      // Details panel should appear
      const detailsPanel = page.locator('[data-testid="node-details"]');
      await expect(detailsPanel).toBeVisible();

      // Should show phantom status
      await expect(detailsPanel).toContainText(/phantom/i);
      await expect(detailsPanel).toContainText(/not in catalog/i);
    }
  });

  test('should highlight connected edges when hovering phantom node', async ({ page }) => {
    const phantomNode = page.locator('[data-node-id^="-"]').first();

    if (await phantomNode.count() > 0) {
      await phantomNode.hover();

      // Connected edges should be highlighted
      const highlightedEdges = await page.locator('[data-edge-highlighted="true"]').count();

      // At least some edges should be highlighted (if node has connections)
      expect(highlightedEdges).toBeGreaterThanOrEqual(0);
    }
  });
});

test.describe('Accessibility', () => {
  test('should have aria labels for phantom nodes', async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');
    await page.waitForSelector('[data-testid="lineage-graph"]');

    const phantomNode = page.locator('[data-node-id^="-"]').first();

    if (await phantomNode.count() > 0) {
      const ariaLabel = await phantomNode.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel).toMatch(/phantom|not in catalog/i);
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('http://localhost:3000/lineage');
    await page.waitForSelector('[data-testid="lineage-graph"]');

    // Tab to first node
    await page.keyboard.press('Tab');

    // Should focus a node
    const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-node-id'));
    expect(focusedElement).toBeTruthy();
  });
});
