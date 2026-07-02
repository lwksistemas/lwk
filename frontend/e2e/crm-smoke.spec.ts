import { test, expect } from '@playwright/test';
import {
  CRM_E2E_SLUG,
  crmE2eCredentials,
  loginCrmLoja,
  visitarCrmAutenticado,
} from './crm-auth';

const slug = CRM_E2E_SLUG;

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

  test('fluxo autenticado — módulos principais', async ({ page }) => {
    test.skip(!crmE2eCredentials(), 'Defina CRM_E2E_EMAIL e CRM_E2E_PASSWORD');

    const ok = await loginCrmLoja(page, slug);
    test.skip(!ok, 'Loja indisponível neste ambiente');

    await visitarCrmAutenticado(page, '/pipeline', slug);
    await expect(page.getByRole('heading', { name: /pipeline de vendas/i })).toBeVisible({
      timeout: 20000,
    });

    await visitarCrmAutenticado(page, '/leads', slug);
    await expect(page.getByRole('heading', { name: /^leads$/i })).toBeVisible({ timeout: 20000 });

    await visitarCrmAutenticado(page, '/propostas', slug);
    await expect(page.getByRole('heading', { name: /criar propostas/i })).toBeVisible({
      timeout: 20000,
    });

    await visitarCrmAutenticado(page, '/contratos', slug);
    await expect(page.getByRole('heading', { name: /criar contrato/i })).toBeVisible({
      timeout: 20000,
    });

    await visitarCrmAutenticado(page, '/financeiro', slug);
    await expect(page.getByRole('heading', { name: /financeiro do vendedor/i })).toBeVisible({
      timeout: 20000,
    });

    await visitarCrmAutenticado(page, '/customers', slug);
    await expect(page.getByRole('heading', { name: /contas/i })).toBeVisible({ timeout: 20000 });
  });
});
