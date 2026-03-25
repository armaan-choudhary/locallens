import { test, expect } from '@playwright/test';

test.describe('Document Scoping UX', () => {
  test.beforeEach(async ({ page }) => {
    // Note: Assumes the dev server is running and a document is already ingested
    // In a real CI environment, we'd mock the API or seed the DB
    await page.goto('http://localhost:5173/query');
  });

  test('should toggle global search mode', async ({ page }) => {
    const globalSearchBtn = page.getByTestId('global-search-toggle');
    
    // Initially should be global if no session or new session
    await expect(globalSearchBtn).toHaveClass(/bg-accentDim/);
    await expect(page.getByPlaceholder(/Ask anything about all documents/)).toBeVisible();

    // Select a document (if any exists in sidebar)
    const firstDocCheckbox = page.locator('aside button').filter({ has: page.locator('svg.lucide-square') }).first();
    if (await firstDocCheckbox.isVisible()) {
      await firstDocCheckbox.click();
      
      // Global search should now be inactive
      await expect(globalSearchBtn).not.toHaveClass(/bg-accentDim/);
      await expect(page.getByPlaceholder(/Search across 1 selected documents/)).toBeVisible();
      
      // Clicking Global Search should reset it
      await globalSearchBtn.click();
      await expect(globalSearchBtn).toHaveClass(/bg-accentDim/);
      await expect(page.getByPlaceholder(/Ask anything about all documents/)).toBeVisible();
    }
  });

  test('should show mentions dropdown when typing @', async ({ page }) => {
    const input = page.getByPlaceholder(/Ask/);
    await input.fill('what is in @');
    
    const dropdown = page.locator('text=Select Scope');
    await expect(dropdown).toBeVisible();
    
    // Check if dropdown contains files
    const firstMention = page.locator('button:has-text("chunks")').first();
    if (await firstMention.isVisible()) {
      const fileName = await firstMention.locator('div').first().innerText();
      await firstMention.click();
      
      // Dropdown should close
      await expect(dropdown).not.toBeVisible();
      
      // Input should have removed the @mention part but kept the prefix
      await expect(input).toHaveValue('what is in ');
      
      // Sidebar should reflect the selection
      await expect(page.getByPlaceholder(/Search across 1 selected documents/)).toBeVisible();
    }
  });

  test('bulk actions should work', async ({ page }) => {
    const selectAllBtn = page.getByRole('button', { name: 'All' });
    const clearAllBtn = page.getByRole('button', { name: 'None' });

    if (await selectAllBtn.isVisible()) {
      await selectAllBtn.click();
      await expect(page.getByPlaceholder(/Search across/)).toBeVisible();
      
      await clearAllBtn.click();
      await expect(page.getByPlaceholder(/Ask anything about all documents/)).toBeVisible();
    }
  });
});
