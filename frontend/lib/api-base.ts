/**
 * Origem da URL da API (Next.js).
 * Configure NEXT_PUBLIC_API_URL no ambiente de deploy (variáveis do host).
 */

function stripTrailingSlashes(s: string): string {
  return s.replace(/\/+$/, '');
}

/** Raiz do backend (sem barra final). Pode ou não incluir `/api`. */
export function getPrimaryApiRoot(): string {
  return stripTrailingSlashes(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
}

/** Base para chamadas DRF (termina em `/api`). */
export function getPrimaryApiBaseUrl(): string {
  const root = getPrimaryApiRoot();
  return root.endsWith('/api') ? root : `${root}/api`;
}
