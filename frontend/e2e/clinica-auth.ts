import { expect, type Page } from '@playwright/test';

/** Loja clínica no beta (Nova Imagem por padrão). */
export const CLINICA_E2E_SLUG =
  process.env.CLINICA_E2E_LOJA_SLUG || process.env.CRM_E2E_LOJA_SLUG || 'novaimagem';

export function clinicaE2eCredentials(): { email: string; password: string } | null {
  const email = process.env.CLINICA_E2E_EMAIL || process.env.CRM_E2E_EMAIL;
  const password = process.env.CLINICA_E2E_PASSWORD || process.env.CRM_E2E_PASSWORD;
  if (!email || !password) return null;
  return { email, password };
}

function slugRegex(slug: string): string {
  return slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Login na loja; retorna false se a loja não estiver disponível. */
export async function loginClinicaLoja(page: Page, slug = CLINICA_E2E_SLUG): Promise<boolean> {
  await page.goto(`/loja/${slug}/login`);
  const usuario = page.getByPlaceholder(/digite seu usuário/i);
  const senha = page.getByPlaceholder(/digite sua senha/i);
  try {
    await usuario.waitFor({ state: 'visible', timeout: 25000 });
    await senha.waitFor({ state: 'visible', timeout: 5000 });
  } catch {
    return false;
  }

  const creds = clinicaE2eCredentials();
  if (!creds) throw new Error('Defina CLINICA_E2E_EMAIL/CLINICA_E2E_PASSWORD ou CRM_E2E_*');

  await usuario.fill(creds.email);
  const cpfCnpj = process.env.CLINICA_E2E_CPF_CNPJ || process.env.CRM_E2E_CPF_CNPJ;
  if (cpfCnpj) {
    const campoDoc = page.getByPlaceholder(/000\.000\.000-00/i);
    if ((await campoDoc.count()) > 0) await campoDoc.fill(cpfCnpj);
  }
  await senha.fill(creds.password);
  await page.getByRole('button', { name: /entrar/i }).click();

  const posLogin = new RegExp(`/loja/${slugRegex(slug)}/(dashboard|clinica-beleza|agenda|trocar-senha)`);
  try {
    await page.waitForURL(posLogin, { timeout: 45000 });
  } catch {
    return false;
  }
  return !page.url().includes('/login');
}

export async function visitarClinicaAutenticado(
  page: Page,
  path: string,
  slug = CLINICA_E2E_SLUG,
): Promise<void> {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  await page.goto(`/loja/${slug}${normalized}`);
  await page.waitForLoadState('networkidle');
  const url = page.url();
  expect(url).toMatch(new RegExp(`/loja/${slugRegex(slug)}/`));
  expect(url).not.toMatch(/\/login/);
}
