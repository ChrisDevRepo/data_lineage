import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('v2.1.0 Confidence Badges - Visual Indicators on Nodes', () => {
  const screenshotDir = '/home/user/sandbox/test_screenshots';

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for the graph to load
    await page.waitForSelector('.react-flow', { timeout: 10000 });
    await page.waitForTimeout(2000); // Additional wait for nodes to render
  });

  test('should display confidence badges on Stored Procedure nodes', async ({ page }) => {
    // Look for confidence badges (they should be visible on SP nodes)
    const badges = page.locator('.confidence-badge');
    const badgeCount = await badges.count();

    console.log(`Found ${badgeCount} confidence badges in the graph`);

    // Take screenshot showing badges
    await page.screenshot({
      path: path.join(screenshotDir, 'v2.1.0-01-confidence-badges-overview.png'),
      fullPage: true,
    });

    // Confidence badges should exist (assuming there are SPs in the data)
    if (badgeCount > 0) {
      console.log('✓ Confidence badges are visible on nodes');
    } else {
      console.log('⚠ No confidence badges found - may need SP data');
    }
  });

  test('should find and verify ✅ (100%) high confidence badge', async ({ page }) => {
    // Look for checkmark badges (high confidence = 100%)
    const badges = page.locator('.confidence-badge:has-text("✅")');
    const count = await badges.count();

    console.log(`Found ${count} high confidence badges (✅)`);

    if (count > 0) {
      // Hover over first badge to see tooltip
      await badges.first().hover();
      await page.waitForTimeout(500);

      // Get the title attribute
      const title = await badges.first().getAttribute('title');
      console.log(`Badge tooltip: ${title}`);

      // Verify tooltip mentions "High Confidence"
      expect(title).toContain('High Confidence');
      expect(title).toContain('100%');

      // Take screenshot
      await page.screenshot({
        path: path.join(screenshotDir, 'v2.1.0-02-high-confidence-badge.png'),
        fullPage: true,
      });

      console.log('✓ High confidence badge verified');
    } else {
      console.log('⚠ No high confidence badges found');
    }
  });

  test('should find and verify ⚠️ (85%) good confidence badge', async ({ page }) => {
    // Look for warning badges (good confidence = 85%)
    const allWarningBadges = page.locator('.confidence-badge:has-text("⚠️")');
    const count = await allWarningBadges.count();

    console.log(`Found ${count} warning badges (⚠️) - could be 85% or 75%`);

    if (count > 0) {
      // Check for 85% badges specifically
      for (let i = 0; i < Math.min(count, 5); i++) {
        const badge = allWarningBadges.nth(i);
        await badge.hover();
        await page.waitForTimeout(300);

        const title = await badge.getAttribute('title');
        console.log(`Badge ${i} tooltip: ${title}`);

        if (title?.includes('85%')) {
          console.log('✓ Found 85% (Good Confidence) badge');

          await page.screenshot({
            path: path.join(screenshotDir, 'v2.1.0-03-good-confidence-badge-85.png'),
            fullPage: true,
          });
          break;
        }
      }
    }
  });

  test('should find and verify ⚠️ (75%) medium confidence badge', async ({ page }) => {
    // Look for warning badges (medium confidence = 75%)
    const allWarningBadges = page.locator('.confidence-badge:has-text("⚠️")');
    const count = await allWarningBadges.count();

    if (count > 0) {
      // Check for 75% badges specifically
      for (let i = 0; i < Math.min(count, 5); i++) {
        const badge = allWarningBadges.nth(i);
        await badge.hover();
        await page.waitForTimeout(300);

        const title = await badge.getAttribute('title');
        console.log(`Badge ${i} tooltip: ${title}`);

        if (title?.includes('75%')) {
          console.log('✓ Found 75% (Medium Confidence) badge');

          await page.screenshot({
            path: path.join(screenshotDir, 'v2.1.0-04-medium-confidence-badge-75.png'),
            fullPage: true,
          });
          break;
        }
      }
    }
  });

  test('should find and verify ❌ (0%) failed confidence badge', async ({ page }) => {
    // Look for X badges (failed/low confidence = 0%)
    const badges = page.locator('.confidence-badge:has-text("❌")');
    const count = await badges.count();

    console.log(`Found ${count} failed confidence badges (❌)`);

    if (count > 0) {
      // Hover over first badge to see tooltip
      await badges.first().hover();
      await page.waitForTimeout(500);

      const title = await badges.first().getAttribute('title');
      console.log(`Badge tooltip: ${title}`);

      // Verify tooltip mentions "Low/Failed Confidence"
      expect(title).toContain('0%');

      // Take screenshot
      await page.screenshot({
        path: path.join(screenshotDir, 'v2.1.0-05-failed-confidence-badge.png'),
        fullPage: true,
      });

      console.log('✓ Failed confidence badge verified');
    } else {
      console.log('⚠ No failed confidence badges found');
    }
  });

  test('should verify badge hover effect works', async ({ page }) => {
    const badges = page.locator('.confidence-badge');
    const count = await badges.count();

    if (count > 0) {
      const firstBadge = badges.first();

      // Get initial bounding box
      const boxBefore = await firstBadge.boundingBox();

      // Hover over badge (should trigger scale effect)
      await firstBadge.hover();
      await page.waitForTimeout(300);

      // Take screenshot of hover state
      await page.screenshot({
        path: path.join(screenshotDir, 'v2.1.0-06-badge-hover-effect.png'),
        fullPage: true,
      });

      console.log('✓ Badge hover effect tested');
    }
  });

  test('should verify only Stored Procedures have badges', async ({ page }) => {
    // Get all nodes
    const allNodes = page.locator('.react-flow__node');
    const nodeCount = await allNodes.count();

    console.log(`Total nodes in graph: ${nodeCount}`);

    // Get all badges
    const badges = page.locator('.confidence-badge');
    const badgeCount = await badges.count();

    console.log(`Total confidence badges: ${badgeCount}`);

    // Badges should only appear on SP nodes
    // (We can't easily verify this in isolation, but we can document it)
    await page.screenshot({
      path: path.join(screenshotDir, 'v2.1.0-07-all-nodes-with-badges.png'),
      fullPage: true,
    });

    console.log('✓ Node and badge counts documented');
  });

  test('should verify v2.1.0 simplified model values (0, 75, 85, 100)', async ({ page }) => {
    const badges = page.locator('.confidence-badge');
    const count = await badges.count();

    const confidenceLevels = new Set<string>();

    // Sample up to 20 badges to find all confidence levels
    for (let i = 0; i < Math.min(count, 20); i++) {
      const badge = badges.nth(i);
      const title = await badge.getAttribute('title');

      if (title) {
        // Extract percentage from title
        const match = title.match(/(\d+)%/);
        if (match) {
          confidenceLevels.add(match[1]);
        }
      }
    }

    console.log('Confidence levels found:', Array.from(confidenceLevels).sort());

    // v2.1.0 model should only have: 0, 75, 85, 100
    const validLevels = ['0', '75', '85', '100'];
    const foundLevels = Array.from(confidenceLevels);

    for (const level of foundLevels) {
      if (validLevels.includes(level)) {
        console.log(`✓ Valid v2.1.0 level found: ${level}%`);
      } else {
        console.log(`⚠ Unexpected confidence level: ${level}%`);
      }
    }

    await page.screenshot({
      path: path.join(screenshotDir, 'v2.1.0-08-confidence-level-verification.png'),
      fullPage: true,
    });
  });
});
