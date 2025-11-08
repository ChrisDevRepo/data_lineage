import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('BUG-001.1: Main Toolbar During Trace Mode', () => {
  const screenshotDir = '/home/user/sandbox/test_screenshots';

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for the graph to load
    await page.waitForSelector('.react-flow', { timeout: 10000 });
    await page.waitForTimeout(2000);
  });

  test('should confirm toolbar is responsive BEFORE trace starts', async ({ page }) => {
    // Baseline test: toolbar should work before trace

    // Find schema filter button
    const schemaFilter = page.locator('button:has-text("Schema"), button:has-text("Schemas")').first();

    if (await schemaFilter.count() > 0) {
      // Click to open dropdown
      await schemaFilter.click();
      await page.waitForTimeout(500);

      // Verify dropdown opened (look for checkboxes or options)
      const dropdownVisible = await page.locator('[role="menu"], [role="listbox"], .dropdown, .menu').isVisible().catch(() => false);

      await page.screenshot({
        path: path.join(screenshotDir, 'bug001-01-toolbar-before-trace.png'),
        fullPage: true,
      });

      console.log('✓ Baseline: Toolbar is responsive before trace');
      expect(dropdownVisible).toBe(true);

      // Close dropdown
      await page.keyboard.press('Escape');
    } else {
      console.log('⚠ Schema filter not found - skipping baseline test');
    }
  });

  test('should FAIL: toolbar becomes unresponsive during trace (confirms bug)', async ({ page }) => {
    // This test is EXPECTED TO FAIL - it confirms the bug exists

    // Step 1: Start a trace
    const nodes = page.locator('.react-flow__node');
    const nodeCount = await nodes.count();

    if (nodeCount === 0) {
      console.log('⚠ No nodes available for testing');
      return;
    }

    // Right-click on first node to open context menu
    const firstNode = nodes.first();
    await firstNode.click({ button: 'right' });
    await page.waitForTimeout(500);

    await page.screenshot({
      path: path.join(screenshotDir, 'bug001-02-context-menu.png'),
      fullPage: true,
    });

    // Look for "Start Trace" or "Trace" option in context menu
    const traceOption = page.locator('text=/.*Trace.*/i').first();

    if (await traceOption.count() > 0) {
      await traceOption.click();
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: path.join(screenshotDir, 'bug001-03-trace-controls-open.png'),
        fullPage: true,
      });

      console.log('✓ Trace controls opened');

      // Step 2: Try to interact with toolbar
      const schemaFilter = page.locator('button:has-text("Schema"), button:has-text("Schemas")').first();

      if (await schemaFilter.count() > 0) {
        // Check if button is disabled
        const isDisabled = await schemaFilter.isDisabled().catch(() => false);
        console.log(`Schema filter disabled: ${isDisabled}`);

        // Try to click it
        await schemaFilter.click({ timeout: 3000 }).catch((e) => {
          console.log('❌ BUG CONFIRMED: Cannot click schema filter during trace');
        });

        await page.waitForTimeout(500);

        // Check if dropdown opened
        const dropdownVisible = await page.locator('[role="menu"], [role="listbox"], .dropdown, .menu').isVisible().catch(() => false);

        await page.screenshot({
          path: path.join(screenshotDir, 'bug001-04-toolbar-during-trace.png'),
          fullPage: true,
        });

        console.log(`Dropdown visible after click: ${dropdownVisible}`);

        // This assertion is EXPECTED TO FAIL if bug exists
        expect(dropdownVisible).toBe(true); // Should be true, but will fail if bug exists

      } else {
        console.log('⚠ Schema filter not found');
      }
    } else {
      console.log('⚠ Trace option not found in context menu');
    }
  });

  test('should check if toolbar has disabled styling during trace', async ({ page }) => {
    // Check visual state of toolbar during trace

    const nodes = page.locator('.react-flow__node');
    const nodeCount = await nodes.count();

    if (nodeCount === 0) {
      console.log('⚠ No nodes available');
      return;
    }

    // Start trace
    await nodes.first().click({ button: 'right' });
    await page.waitForTimeout(500);

    const traceOption = page.locator('text=/.*Trace.*/i').first();
    if (await traceOption.count() > 0) {
      await traceOption.click();
      await page.waitForTimeout(1000);

      // Check toolbar for disabled attributes or classes
      const toolbar = page.locator('[class*="toolbar"], [class*="Toolbar"], header, [role="toolbar"]').first();

      if (await toolbar.count() > 0) {
        const toolbarClasses = await toolbar.getAttribute('class') || '';
        const toolbarDisabled = await toolbar.getAttribute('disabled') || 'false';
        const toolbarAriaDisabled = await toolbar.getAttribute('aria-disabled') || 'false';

        console.log('Toolbar classes:', toolbarClasses);
        console.log('Toolbar disabled attr:', toolbarDisabled);
        console.log('Toolbar aria-disabled:', toolbarAriaDisabled);

        await page.screenshot({
          path: path.join(screenshotDir, 'bug001-05-toolbar-state-check.png'),
          fullPage: true,
        });

        // Check individual filter buttons
        const filterButtons = page.locator('button:has-text("Schema"), button:has-text("Type"), button:has-text("Filter")');
        const buttonCount = await filterButtons.count();

        for (let i = 0; i < Math.min(buttonCount, 3); i++) {
          const button = filterButtons.nth(i);
          const buttonText = await button.textContent();
          const buttonDisabled = await button.isDisabled().catch(() => false);
          const buttonClasses = await button.getAttribute('class') || '';

          console.log(`Button "${buttonText}": disabled=${buttonDisabled}, classes=${buttonClasses}`);

          // Bug confirmation: buttons should NOT be disabled
          if (buttonDisabled) {
            console.log(`❌ BUG CONFIRMED: Button "${buttonText}" is disabled during trace`);
          }
        }
      }
    }
  });

  test('should check pointer-events and z-index issues', async ({ page }) => {
    // Check for CSS issues that might block interaction

    const nodes = page.locator('.react-flow__node');
    if (await nodes.count() === 0) {
      console.log('⚠ No nodes available');
      return;
    }

    // Start trace
    await nodes.first().click({ button: 'right' });
    await page.waitForTimeout(500);

    const traceOption = page.locator('text=/.*Trace.*/i').first();
    if (await traceOption.count() > 0) {
      await traceOption.click();
      await page.waitForTimeout(1000);

      // Check computed styles
      const schemaFilter = page.locator('button:has-text("Schema"), button:has-text("Schemas")').first();

      if (await schemaFilter.count() > 0) {
        const styles = await schemaFilter.evaluate((el) => {
          const computed = window.getComputedStyle(el);
          return {
            pointerEvents: computed.pointerEvents,
            zIndex: computed.zIndex,
            opacity: computed.opacity,
            display: computed.display,
            visibility: computed.visibility,
          };
        });

        console.log('Schema filter computed styles:', styles);

        // Check for blocking issues
        if (styles.pointerEvents === 'none') {
          console.log('❌ BUG FOUND: pointer-events is "none" on toolbar');
        }
        if (parseFloat(styles.opacity) < 0.5) {
          console.log('⚠ Warning: Low opacity detected');
        }

        await page.screenshot({
          path: path.join(screenshotDir, 'bug001-06-css-inspection.png'),
          fullPage: true,
        });
      }
    }
  });
});
