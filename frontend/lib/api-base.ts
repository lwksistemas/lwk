/**
 * Origem da URL da API (Next.js).
 * Configure NEXT_PUBLIC_API_URL no ambiente de deploy (variáveis do host).
 * Em beta/staging, detecta pelo hostname se a variável não estiver definida.
 */

function stripTrailingSlashes(s: string): string {
  return s.replace(/\/+$/, '');
}

const PRODUCTION_API_ROOT = 'https://api.lwksistemas.com.br';
const STAGING_API_ROOT = 'https://lwks-backend-staging-staging.up.railway.app';

export function isBetaHost(host: string): boolean {
  return host === 'beta.lwksistemas.com.br';
}

/** Raiz da API a partir do hostname (sem barra final). */
export function getApiRootForHost(host: string): string | null {
  const h = host.toLowerCase().split(':')[0];
  if (isBetaHost(h)) return STAGING_API_ROOT;
  if (h === 'lwksistemas.com.br' || h === 'www.lwksistemas.com.br') {
    return PRODUCTION_API_ROOT;
  }
  return null;
}

/** Base `/api` para SSR quando o host da requisição é conhecido. */
export function getPrimaryApiBaseUrlFromHost(host: string): string {
  const root = getApiRootForHost(host) ?? getPrimaryApiRoot();
  return root.endsWith('/api') ? root : `${root}/api`;
}

/** True no beta (hostname ou build Preview da branch staging). */
export function isBetaEnvironment(): boolean {
  if (typeof window !== 'undefined') {
    return isBetaHost(window.location.hostname.toLowerCase());
  }
  if (process.env.NEXT_PUBLIC_LWK_BETA === '1') return true;
  const vercelEnv = process.env.NEXT_PUBLIC_VERCEL_ENV || process.env.VERCEL_ENV;
  const gitRef = process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_REF || process.env.VERCEL_GIT_COMMIT_REF;
  return vercelEnv === 'preview' && gitRef === 'staging';
}

function resolveApiRootFromHost(): string | null {
  if (typeof window === 'undefined') return null;
  const host = window.location.hostname.toLowerCase();
  if (isBetaHost(host)) {
    return STAGING_API_ROOT;
  }
  if (host === 'lwksistemas.com.br' || host === 'www.lwksistemas.com.br') {
    return PRODUCTION_API_ROOT;
  }
  return null;
}

/** Raiz do backend (sem barra final). Pode ou não incluir `/api`. */
export function getPrimaryApiRoot(): string {
  const fromHost = resolveApiRootFromHost();
  if (fromHost) return fromHost;
  return stripTrailingSlashes(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
}

/** Base para chamadas DRF (termina em `/api`). */
export function getPrimaryApiBaseUrl(): string {
  const root = getPrimaryApiRoot();
  return root.endsWith('/api') ? root : `${root}/api`;
}
