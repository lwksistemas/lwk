import { getPrimaryApiRoot } from './api-base';

/** eTLD+1 simplificado (.com.br e domínios comuns). */
function registrableDomain(host: string): string {
  const h = host.toLowerCase();
  const parts = h.split('.');
  if (parts.length >= 3 && parts.slice(-2).join('.') === 'com.br') {
    return parts.slice(-3).join('.');
  }
  if (parts.length >= 2) {
    return parts.slice(-2).join('.');
  }
  return h;
}

/** Cookies httpOnly só funcionam quando API e frontend são same-site (ex.: *.lwksistemas.com.br). */
function isSameSiteApi(): boolean {
  if (typeof window === 'undefined') return true;
  try {
    const root = getPrimaryApiRoot();
    const apiHost = new URL(root.includes('://') ? root : `https://${root}`).hostname;
    return registrableDomain(apiHost) === registrableDomain(window.location.hostname);
  } catch {
    return true;
  }
}

/** JWT em cookies httpOnly (backend JWT_USE_HTTPONLY_COOKIES + withCredentials). */
export const USE_JWT_HTTPONLY_COOKIES =
  process.env.NEXT_PUBLIC_JWT_HTTPONLY_COOKIES === 'true' && isSameSiteApi();
