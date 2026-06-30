/** Redirecionamento único para /assinatura quando a loja está bloqueada por inadimplência. */

export const STORE_BLOCKED_SESSION_KEY = 'lwk_store_blocked';
const BLOCKED_REDIRECT_TS_KEY = 'lwk_store_blocked_redirect_ts';
const REDIRECT_COOLDOWN_MS = 2500;

export function lojaSlugFromPathname(pathname?: string): string | null {
  const p = pathname ?? (typeof window !== 'undefined' ? window.location.pathname : '');
  const m = p.match(/\/loja\/([^/]+)/);
  return m?.[1] ?? null;
}

export function assinaturaPathForUrlSlug(urlSlug: string): string {
  return `/loja/${urlSlug}/assinatura`;
}

export function isAssinaturaPath(pathname?: string): boolean {
  const p = pathname ?? (typeof window !== 'undefined' ? window.location.pathname : '');
  return /\/assinatura\/?$/.test(p);
}

export function isStoreBlockedMarked(): boolean {
  if (typeof window === 'undefined') return false;
  return sessionStorage.getItem(STORE_BLOCKED_SESSION_KEY) === '1';
}

export function markStoreBlocked(): void {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(STORE_BLOCKED_SESSION_KEY, '1');
}

export function clearStoreBlockedMark(): void {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(STORE_BLOCKED_SESSION_KEY);
  sessionStorage.removeItem(BLOCKED_REDIRECT_TS_KEY);
}

/** `true` se disparou navegação para a página de assinatura. */
export function redirectToAssinatura(urlSlug: string): boolean {
  if (typeof window === 'undefined' || !urlSlug.trim()) return false;
  const target = assinaturaPathForUrlSlug(urlSlug.trim());
  if (isAssinaturaPath()) {
    clearStoreBlockedMark();
    return false;
  }
  const now = Date.now();
  const last = Number(sessionStorage.getItem(BLOCKED_REDIRECT_TS_KEY) || 0);
  if (now - last < REDIRECT_COOLDOWN_MS) return false;
  sessionStorage.setItem(BLOCKED_REDIRECT_TS_KEY, String(now));
  markStoreBlocked();
  window.location.replace(target);
  return true;
}

export function handleStoreBlockedResponse(urlSlug?: string | null): boolean {
  const slug = urlSlug ?? lojaSlugFromPathname();
  if (!slug) return false;
  return redirectToAssinatura(slug);
}
