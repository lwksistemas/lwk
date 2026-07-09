import { test, expect } from '@playwright/test';
import {
  CLINICA_E2E_SLUG,
  clinicaE2eCredentials,
  loginClinicaLoja,
  visitarClinicaAutenticado,
} from './clinica-auth';

const slug = CLINICA_E2E_SLUG;

test.describe('Clínica da Beleza — smoke E2E', () => {
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

  test('consultas exige autenticação ou loja válida', async ({ page }) => {
    await page.goto(`/loja/${slug}/clinica-beleza/consultas`);
    await page.waitForLoadState('networkidle');
    const url = page.url();
    const body = await page.locator('body').innerText();
    const protegido = /login/i.test(url) || /acesso|entrar|não existe/i.test(body);
    expect(protegido).toBeTruthy();
  });

  test('agenda exige autenticação ou loja válida', async ({ page }) => {
    await page.goto(`/loja/${slug}/agenda`);
    await page.waitForLoadState('networkidle');
    const url = page.url();
    const body = await page.locator('body').innerText();
    const protegido = /login/i.test(url) || /acesso|entrar|não existe/i.test(body);
    expect(protegido).toBeTruthy();
  });

  test('fluxo autenticado — módulos principais', async ({ page }) => {
    test.skip(!clinicaE2eCredentials(), 'Defina CLINICA_E2E_* ou CRM_E2E_*');

    const ok = await loginClinicaLoja(page, slug);
    test.skip(!ok, 'Loja clínica indisponível neste ambiente');

    await visitarClinicaAutenticado(page, '/clinica-beleza/consultas', slug);
    await expect(page.getByRole('heading', { name: /^consultas$/i })).toBeVisible({ timeout: 20000 });

    await visitarClinicaAutenticado(page, '/clinica-beleza/pacientes', slug);
    await expect(page.getByRole('heading', { name: /^clientes$/i })).toBeVisible({ timeout: 20000 });

    await visitarClinicaAutenticado(page, '/agenda', slug);
    await expect(page.getByRole('heading', { name: /^agenda$/i })).toBeVisible({ timeout: 20000 });
  });

  test('fluxo autenticado — coluna pagamento e financeiro', async ({ page }) => {
    test.skip(!clinicaE2eCredentials(), 'Defina CLINICA_E2E_* ou CRM_E2E_*');

    const ok = await loginClinicaLoja(page, slug);
    test.skip(!ok, 'Loja clínica indisponível neste ambiente');

    await visitarClinicaAutenticado(page, '/clinica-beleza/consultas', slug);
    await expect(page.getByRole('heading', { name: /^consultas$/i })).toBeVisible({ timeout: 20000 });
    // Coluna PAGAMENTO da lista (Receber / Pago / Parcial)
    const pagamentoHeader = page.getByRole('columnheader', { name: /pagamento/i });
    const temColuna = (await pagamentoHeader.count()) > 0;
    const temBotaoReceber = (await page.getByRole('button', { name: /receber|parcial|pago/i }).count()) > 0;
    const listaVazia = /nenhuma consulta/i.test(await page.locator('body').innerText());
    expect(temColuna || temBotaoReceber || listaVazia).toBeTruthy();

    await visitarClinicaAutenticado(page, '/clinica-beleza/financeiro', slug);
    await expect(page.getByRole('heading', { name: /financeiro/i })).toBeVisible({ timeout: 20000 });
  });
});
