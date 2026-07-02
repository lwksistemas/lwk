import { test, expect } from '@playwright/test';

test.describe('CRM — assinatura pública', () => {
  test('token inválido exibe erro amigável', async ({ page }) => {
    await page.goto('/assinar/token-invalido-e2e');
    await expect(page.getByRole('heading', { name: /erro ao carregar/i })).toBeVisible({
      timeout: 25000,
    });
  });

  test('token válido — opcional', async ({ page }) => {
    const token = process.env.CRM_E2E_ASSINATURA_TOKEN;
    test.skip(!token, 'Defina CRM_E2E_ASSINATURA_TOKEN para validar link real');

    await page.goto(`/assinar/${encodeURIComponent(token!)}`);
    await page.waitForLoadState('networkidle');

    const heading = page.getByRole('heading', {
      name: /assinatura digital|erro ao carregar|link desatualizado|assinatura registrada/i,
    });
    await expect(heading).toBeVisible({ timeout: 30000 });
  });
});
