import { expect, type Page } from '@playwright/test';

export const CRM_E2E_SLUG = process.env.CRM_E2E_LOJA_SLUG || 'vendasbeta';

export function crmE2eCredentials(): { email: string; password: string } | null {
  const email = process.env.CRM_E2E_EMAIL;
  const password = process.env.CRM_E2E_PASSWORD;
  if (!email || !password) return null;
  return { email, password };
}

function slugRegex(slug: string): string {
  return slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Login na loja; retorna false se a loja não estiver disponível (skip do teste). */
export async function loginCrmLoja(page: Page, slug = CRM_E2E_SLUG): Promise<boolean> {
  await page.goto(`/loja/${slug}/login`);
  const usuario = page.getByPlaceholder(/digite seu usuário/i);
  const senha = page.getByPlaceholder(/digite sua senha/i);
  try {
    await usuario.waitFor({ state: 'visible', timeout: 25000 });
    await senha.waitFor({ state: 'visible', timeout: 5000 });
  } catch {
    return false;
  }

  const creds = crmE2eCredentials();
  if (!creds) throw new Error('Defina CRM_E2E_EMAIL e CRM_E2E_PASSWORD');

  await usuario.fill(creds.email);
  const cpfCnpj = process.env.CRM_E2E_CPF_CNPJ;
  if (cpfCnpj) {
    const campoDoc = page.getByPlaceholder(/000\.000\.000-00/i);
    if ((await campoDoc.count()) > 0) await campoDoc.fill(cpfCnpj);
  }
  await senha.fill(creds.password);
  await page.getByRole('button', { name: /entrar/i }).click();

  const posLogin = new RegExp(`/loja/${slugRegex(slug)}/(crm-vendas|dashboard|trocar-senha)`);
  try {
    await page.waitForURL(posLogin, { timeout: 45000 });
  } catch {
    return false;
  }
  return !page.url().includes('/login');
}

export async function visitarCrmAutenticado(
  page: Page,
  path: string,
  slug = CRM_E2E_SLUG,
): Promise<void> {
  await page.goto(`/loja/${slug}/crm-vendas${path}`);
  await page.waitForLoadState('networkidle');
  const url = page.url();
  expect(url).toMatch(new RegExp(`/loja/${slugRegex(slug)}/crm-vendas`));
  expect(url).not.toMatch(/\/login/);
}
