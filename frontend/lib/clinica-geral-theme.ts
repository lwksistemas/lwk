import { isTipoClinicaGeral } from '@/lib/loja-tipo';

export const NAVY = '#2F2E5B';
export const TEAL = '#0D9B9B';
/** Nome visível do app (tipo de loja). Slug interno permanece clinica-geral. */
export const APP_NOME = 'Clínica';

export const PAGE_BG = '#F7F8FB';
export const PAGE_BG_DARK = '#16152B';
export const ZEBRA_EVEN = '#F4F6FB';
export const ZEBRA_EVEN_DARK = '#252448';
export const SURFACE_DARK = '#1E1D3A';

export const CLINICA_GERAL_DARK_KEY = 'lwk-clinica-geral-dark';

export function isClinicaGeralAppPath(pathname: string): boolean {
  return pathname.includes('/clinica-geral');
}

export function shouldApplyClinicaGeralTheme(pathname: string): boolean {
  if (isClinicaGeralAppPath(pathname)) return true;
  if (typeof window === 'undefined') return false;
  const match = pathname.match(/^\/loja\/([^/]+)\/login\/?$/);
  if (!match) return false;
  try {
    const tipo = sessionStorage.getItem(`loja_tipo_${decodeURIComponent(match[1])}`) || '';
    return isTipoClinicaGeral(tipo);
  } catch {
    return false;
  }
}

/** Tema do consultório: só dark se o usuário escolheu. Padrão = claro. */
export function isClinicaGeralDarkEnabled(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    return window.localStorage.getItem(CLINICA_GERAL_DARK_KEY) === 'true';
  } catch {
    return false;
  }
}

export function applyClinicaGeralDark(isDark: boolean): void {
  if (typeof document === 'undefined') return;
  document.documentElement.classList.toggle('dark', isDark);
  document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';
}

export function persistClinicaGeralDark(isDark: boolean): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(CLINICA_GERAL_DARK_KEY, isDark ? 'true' : 'false');
  } catch {
    /* ignore quota / private mode */
  }
  applyClinicaGeralDark(isDark);
}
