import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Detail Search 2.2: Monaco Editor Keyboard Capture Bug', () => {
  const screenshotDir = '/home/user/sandbox/test_screenshots';

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for the graph to load
    await page.waitForSelector('.react-flow', { timeout: 10000 });
    await page.waitForTimeout(2000);
  });

  test('should open Detail Search modal', async ({ page }) => {
    // Find and click Detail Search button
    const detailSearchButton = page.locator('button[title*="Detail Search"], button:has-text("Detail Search")').first();

    if (await detailSearchButton.count() === 0) {
      console.log('⚠ Detail Search button not found - may be disabled');
      return;
    }

    // Click to open modal
    await detailSearchButton.click();
    await page.waitForTimeout(1000);

    // Verify modal is open
    const modal = page.locator('[role="dialog"], .modal, [class*="Modal"]');
    const modalVisible = await modal.isVisible().catch(() => false);

    await page.screenshot({
      path: path.join(screenshotDir, 'bug002-01-detail-search-modal-open.png'),
      fullPage: true,
    });

    console.log('✓ Detail Search modal opened');
    expect(modalVisible).toBe(true);
  });

  test('should FAIL: typing in search input triggers Monaco editor (confirms bug)', async ({ page }) => {
    // This test is EXPECTED TO FAIL - it confirms the bug exists

    // Open Detail Search
    const detailSearchButton = page.locator('button[title*="Detail Search"], button:has-text("Detail Search")').first();

    if (await detailSearchButton.count() === 0) {
      console.log('⚠ Detail Search button not found');
      return;
    }

    await detailSearchButton.click();
    await page.waitForTimeout(1000);

    // Find search input field
    const searchInput = page.locator('input[placeholder*="search" i], input[type="text"]').first();

    if (await searchInput.count() === 0) {
      console.log('⚠ Search input not found in modal');
      return;
    }

    // Focus on search input
    await searchInput.focus();
    await page.waitForTimeout(500);

    console.log('Search input focused - about to type...');

    // Type in search input
    const testText = 'SELECT * FROM';
    await searchInput.type(testText, { delay: 100 });
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: path.join(screenshotDir, 'bug002-02-typing-in-search-input.png'),
      fullPage: true,
    });

    // Check search input value
    const inputValue = await searchInput.inputValue();
    console.log(`Search input value: "${inputValue}"`);

    // Check if Monaco editor exists and captured keystrokes
    const monacoEditor = page.locator('.monaco-editor, [class*="monaco"]').first();
    const monacoExists = await monacoEditor.count() > 0;

    if (monacoExists) {
      console.log('Monaco editor detected in modal');

      // Try to get Monaco editor content (if it captured keystrokes, it will have content)
      const monacoContent = await page.evaluate(() => {
        // Monaco editor content is usually in a textarea or contenteditable
        const editorTextarea = document.querySelector('.monaco-editor textarea');
        if (editorTextarea instanceof HTMLTextAreaElement) {
          return editorTextarea.value;
        }

        // Alternative: check view-lines for content
        const viewLines = document.querySelector('.view-lines');
        if (viewLines) {
          return viewLines.textContent || '';
        }

        return '';
      }).catch(() => '');

      console.log(`Monaco editor content: "${monacoContent}"`);

      // BUG CONFIRMATION: If Monaco has content, it captured our keystrokes
      if (monacoContent.length > 0) {
        console.log('❌ BUG CONFIRMED: Monaco editor captured keystrokes from search input!');
        console.log(`   Monaco content: "${monacoContent}"`);
      }

      // Check if search input still has focus
      const inputHasFocus = await searchInput.evaluate((el) => el === document.activeElement);
      console.log(`Search input has focus: ${inputHasFocus}`);

      if (!inputHasFocus) {
        console.log('❌ BUG CONFIRMED: Search input lost focus to Monaco editor!');
      }
    }

    // This assertion should PASS if bug doesn't exist
    // It will FAIL if Monaco captured keystrokes
    expect(inputValue).toBe(testText);
  });

  test('should check for Monaco editor autofocus issues', async ({ page }) => {
    // Open Detail Search
    const detailSearchButton = page.locator('button[title*="Detail Search"], button:has-text("Detail Search")').first();

    if (await detailSearchButton.count() === 0) {
      console.log('⚠ Detail Search button not found');
      return;
    }

    await detailSearchButton.click();
    await page.waitForTimeout(1000);

    // Check what element has focus immediately after modal opens
    const focusedElement = await page.evaluate(() => {
      const activeEl = document.activeElement;
      if (!activeEl) return 'none';

      return {
        tagName: activeEl.tagName,
        className: activeEl.className,
        id: activeEl.id,
        placeholder: activeEl instanceof HTMLInputElement ? activeEl.placeholder : '',
      };
    });

    console.log('Focused element after modal open:', focusedElement);

    await page.screenshot({
      path: path.join(screenshotDir, 'bug002-03-initial-focus-check.png'),
      fullPage: true,
    });

    // Check if Monaco has autofocus attribute
    const monacoHasAutofocus = await page.evaluate(() => {
      const monaco = document.querySelector('.monaco-editor');
      if (!monaco) return false;

      // Check for autofocus on Monaco or its children
      const hasAutofocus = monaco.querySelector('[autofocus]') !== null;
      return hasAutofocus;
    }).catch(() => false);

    console.log(`Monaco has autofocus: ${monacoHasAutofocus}`);

    if (monacoHasAutofocus) {
      console.log('⚠ Monaco editor has autofocus - may steal focus from search input');
    }
  });

  test('should check event propagation from search input', async ({ page }) => {
    // Open Detail Search
    const detailSearchButton = page.locator('button[title*="Detail Search"], button:has-text("Detail Search")').first();

    if (await detailSearchButton.count() === 0) {
      console.log('⚠ Detail Search button not found');
      return;
    }

    await detailSearchButton.click();
    await page.waitForTimeout(1000);

    // Find search input
    const searchInput = page.locator('input[placeholder*="search" i], input[type="text"]').first();

    if (await searchInput.count() === 0) {
      console.log('⚠ Search input not found');
      return;
    }

    // Add event listener to detect if events are propagating
    await page.evaluate(() => {
      const input = document.querySelector('input[type="text"]');
      if (!input) return;

      (window as any).capturedEvents = [];

      input.addEventListener('keydown', (e) => {
        (window as any).capturedEvents.push({
          type: 'keydown',
          key: e.key,
          propagationStopped: e.cancelBubble,
          defaultPrevented: e.defaultPrevented,
        });
      });

      input.addEventListener('keypress', (e) => {
        (window as any).capturedEvents.push({
          type: 'keypress',
          key: e.key,
          propagationStopped: e.cancelBubble,
          defaultPrevented: e.defaultPrevented,
        });
      });
    });

    // Type in search input
    await searchInput.focus();
    await searchInput.type('TEST', { delay: 100 });
    await page.waitForTimeout(500);

    // Get captured events
    const events = await page.evaluate(() => (window as any).capturedEvents || []);

    console.log('Captured keyboard events:', events);

    // Check if events are being stopped or prevented
    const stoppedEvents = events.filter((e: any) => e.propagationStopped);
    const preventedEvents = events.filter((e: any) => e.defaultPrevented);

    if (stoppedEvents.length > 0) {
      console.log('⚠ Some events had propagation stopped:', stoppedEvents);
    }

    if (preventedEvents.length > 0) {
      console.log('⚠ Some events had default prevented:', preventedEvents);
    }

    await page.screenshot({
      path: path.join(screenshotDir, 'bug002-04-event-propagation-check.png'),
      fullPage: true,
    });
  });

  test('should verify search input and Monaco are visually separated', async ({ page }) => {
    // Open Detail Search
    const detailSearchButton = page.locator('button[title*="Detail Search"], button:has-text("Detail Search")').first();

    if (await detailSearchButton.count() === 0) {
      console.log('⚠ Detail Search button not found');
      return;
    }

    await detailSearchButton.click();
    await page.waitForTimeout(1000);

    // Get bounding boxes of search input and Monaco editor
    const searchInput = page.locator('input[placeholder*="search" i], input[type="text"]').first();
    const monacoEditor = page.locator('.monaco-editor').first();

    const searchBox = await searchInput.boundingBox().catch(() => null);
    const monacoBox = await monacoEditor.boundingBox().catch(() => null);

    if (searchBox && monacoBox) {
      console.log('Search input position:', searchBox);
      console.log('Monaco editor position:', monacoBox);

      // Check if they overlap (which would be bad)
      const overlap = !(
        searchBox.x + searchBox.width < monacoBox.x ||
        monacoBox.x + monacoBox.width < searchBox.x ||
        searchBox.y + searchBox.height < monacoBox.y ||
        monacoBox.y + monacoBox.height < searchBox.y
      );

      if (overlap) {
        console.log('⚠ Search input and Monaco editor overlap!');
      } else {
        console.log('✓ Search input and Monaco editor are visually separated');
      }
    }

    await page.screenshot({
      path: path.join(screenshotDir, 'bug002-05-layout-check.png'),
      fullPage: true,
    });
  });
});
