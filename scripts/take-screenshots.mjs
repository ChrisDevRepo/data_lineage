#!/usr/bin/env node

/**
 * Screenshot Generator for Documentation
 *
 * Takes high-quality screenshots for GitHub documentation at optimal dimensions.
 * GitHub optimal width: 1280px (looks good on all screens, not too large)
 */

import { chromium } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { mkdir } from 'fs/promises';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const screenshotsDir = join(__dirname, '../docs/screenshots');

// Optimal dimensions for GitHub README screenshots
const OPTIMAL_WIDTH = 1280;
const OPTIMAL_HEIGHT = 800;

async function takeScreenshots() {
  console.log('🎬 Starting screenshot capture...\n');

  // Ensure screenshots directory exists
  await mkdir(screenshotsDir, { recursive: true });

  const browser = await chromium.launch({
    headless: true
  });

  const context = await browser.newContext({
    viewport: { width: OPTIMAL_WIDTH, height: OPTIMAL_HEIGHT },
    deviceScaleFactor: 2  // Retina display (high DPI)
  });

  const page = await context.newPage();

  try {
    // Wait for app to be ready
    console.log('⏳ Waiting for application to load...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000); // Wait for data to load

    // Screenshot 1: Main graph view
    console.log('📸 Capturing main graph view...');
    await page.screenshot({
      path: join(screenshotsDir, '01-main-graph.png'),
      fullPage: false
    });

    // Screenshot 2: Trace mode
    console.log('📸 Capturing trace mode...');
    // Find a node and right-click
    const node = page.locator('[data-id]').first();
    if (await node.count() > 0) {
      await node.click({ button: 'right' });
      await page.waitForTimeout(500);
      await page.screenshot({
        path: join(screenshotsDir, '02-trace-mode.png'),
        fullPage: false
      });
      // Close context menu
      await page.keyboard.press('Escape');
    }

    // Screenshot 3: SQL Viewer
    console.log('📸 Capturing SQL viewer...');
    const nodeToClick = page.locator('[data-id]').first();
    if (await nodeToClick.count() > 0) {
      await nodeToClick.click();
      await page.waitForTimeout(1000); // Wait for SQL to load
      await page.screenshot({
        path: join(screenshotsDir, '03-sql-viewer.png'),
        fullPage: false
      });
    }

    // Screenshot 4: Filters panel
    console.log('📸 Capturing filters panel...');
    const filterButton = page.locator('button:has-text("Filter")').first();
    if (await filterButton.count() > 0) {
      await filterButton.click();
      await page.waitForTimeout(500);
      await page.screenshot({
        path: join(screenshotsDir, '04-filters.png'),
        fullPage: false
      });
    }

    // Screenshot 5: Developer Mode (if accessible)
    console.log('📸 Capturing developer mode...');
    const helpButton = page.locator('button[aria-label*="Help"], button:has-text("?")').first();
    if (await helpButton.count() > 0) {
      await helpButton.click();
      await page.waitForTimeout(500);

      const devButton = page.locator('text=Open Developer Panel').first();
      if (await devButton.count() > 0) {
        await devButton.click();
        await page.waitForTimeout(1000);
        await page.screenshot({
          path: join(screenshotsDir, '05-developer-mode.png'),
          fullPage: false
        });

        // YAML Rules tab
        const yamlTab = page.locator('button:has-text("YAML Rules")').first();
        if (await yamlTab.count() > 0) {
          await yamlTab.click();
          await page.waitForTimeout(500);
          await page.screenshot({
            path: join(screenshotsDir, '06-yaml-rules.png'),
            fullPage: false
          });
        }
      }
    }

    // Screenshot 6: Import modal
    console.log('📸 Capturing import modal...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const importButton = page.locator('button:has-text("Import")').first();
    if (await importButton.count() > 0) {
      await importButton.click();
      await page.waitForTimeout(500);
      await page.screenshot({
        path: join(screenshotsDir, '07-import-modal.png'),
        fullPage: false
      });
    }

    console.log('\n✅ Screenshots captured successfully!');
    console.log(`📁 Location: ${screenshotsDir}`);
    console.log(`📐 Dimensions: ${OPTIMAL_WIDTH}x${OPTIMAL_HEIGHT} @ 2x DPI\n`);

  } catch (error) {
    console.error('❌ Error capturing screenshots:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Main execution
takeScreenshots().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
