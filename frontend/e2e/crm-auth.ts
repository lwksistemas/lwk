import { expect, type Page } from '@playwright/test';

export const CRM_E2E_SLUG = process.env.CRM_E2E_LOJA_SLUG || 'novaimagem';

export function crmE2eCredentials(): { email: string; password: string } | null {
  const email = process.env.CRM_E2E_EMAIL;
  const password = process.env.CRM_E2E_PASSWORD;
  if (!email || !password) return null;
  return { email, password };
}

/** Login na loja; retorna false se a loja não estiver disponível (skip do teste). */
export async function loginCrmLoja(page: Page, slug = CRM_E2E_SLUG): Promise<boolean> {
  await page.goto(`/loja/${slug}/login`);
  const senha = page.getByPlaceholder(/digite sua senha/i);
  if ((await senha.count()) === 0) return false;

  const creds = crmE2eCredentials();
  if (!creds) throw new Error('Defina CRM_E2E_EMAIL e CRM_E2E_PASSWORD');

  await page.getByPlaceholder(/digite seu usuário/i).fill(creds.email);
  await senha.fill(creds.password);
  await page.getByRole('button', { name: /entrar/i }).click();
  await page.waitForURL(new RegExp(`/loja/${slug}/`), { timeout: 30000 });
  return true;
}

export async function visitarCrmAutenticado(
  page: Page,
  path: string,
  slug = CRM_E2E_SLUG,
): Promise<void> {
  await page.goto(`/loja/${slug}/crm-vendas${path}`);
  await page.waitForLoadState('networkidle');
  const url = page.url();
  expect(url).toMatch(new RegExp(`/loja/${slug}/crm-vendas`));
}
