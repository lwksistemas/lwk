import { test, expect } from '@playwright/test';

const slug = process.env.CRM_E2E_LOJA_SLUG || 'novaimagem';

test.describe('CRM Vendas — smoke E2E', () => {
  test('site público responde', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBeLessThan(500);
    await expect(page.locator('body')).toBeVisible();
  });

  test('rota de login da loja responde', async ({ page }) => {
    const response = await page.goto(`/loja/${slug}/login`);
    expect(response?.status()).toBeLessThan(500);
    await page.waitForLoadState('networkidle');
    const body = await page.locator('body').innerText();
    const temLogin =
      (await page.getByPlaceholder(/digite sua senha/i).count()) > 0 ||
      (await page.getByRole('button', { name: /entrar/i }).count()) > 0;
    const lojaInexistente = /loja.*não existe|não está ativa/i.test(body);
    const carregando = /carregando/i.test(body);
    expect(temLogin || lojaInexistente || carregando).toBeTruthy();
  });

  test('CRM exige autenticação ou loja válida', async ({ page }) => {
    await page.goto(`/loja/${slug}/crm-vendas`);
    await page.waitForLoadState('networkidle');
    const url = page.url();
    const body = await page.locator('body').innerText();
    const protegido = /login/i.test(url) || /acesso|entrar|não existe/i.test(body);
    expect(protegido).toBeTruthy();
  });

  test('fluxo autenticado — opcional', async ({ page }) => {
    const email = process.env.CRM_E2E_EMAIL;
    const password = process.env.CRM_E2E_PASSWORD;
    test.skip(!email || !password, 'Defina CRM_E2E_EMAIL e CRM_E2E_PASSWORD');

    await page.goto(`/loja/${slug}/login`);
    const senha = page.getByPlaceholder(/digite sua senha/i);
    if ((await senha.count()) === 0) test.skip(true, 'Loja indisponível neste ambiente');

    await page.getByPlaceholder(/digite seu usuário/i).fill(email!);
    await senha.fill(password!);
    await page.getByRole('button', { name: /entrar/i }).click();
    await page.waitForURL(new RegExp(`/loja/${slug}/`), { timeout: 30000 });

    await page.goto(`/loja/${slug}/crm-vendas/customers`);
    await expect(page.getByRole('heading', { name: /contas/i })).toBeVisible({ timeout: 20000 });
  });

  test('fluxo autenticado — pipeline e propostas', async ({ page }) => {
    const email = process.env.CRM_E2E_EMAIL;
    const password = process.env.CRM_E2E_PASSWORD;
    test.skip(!email || !password, 'Defina CRM_E2E_EMAIL e CRM_E2E_PASSWORD');

    await page.goto(`/loja/${slug}/login`);
    const senha = page.getByPlaceholder(/digite sua senha/i);
    if ((await senha.count()) === 0) test.skip(true, 'Loja indisponível neste ambiente');

    await page.getByPlaceholder(/digite seu usuário/i).fill(email!);
    await senha.fill(password!);
    await page.getByRole('button', { name: /entrar/i }).click();
    await page.waitForURL(new RegExp(`/loja/${slug}/`), { timeout: 30000 });

    await page.goto(`/loja/${slug}/crm-vendas/pipeline`);
    await expect(page.getByRole('heading', { name: /pipeline de vendas/i })).toBeVisible({
      timeout: 20000,
    });

    await page.goto(`/loja/${slug}/crm-vendas/propostas`);
    await page.waitForLoadState('networkidle');
    const body = await page.locator('body').innerText();
    expect(/proposta|acesso|entrar/i.test(body)).toBeTruthy();
  });
});
