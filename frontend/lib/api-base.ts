/**
 * Origem única da URL da API (Next.js + Vercel).
 * Evita duplicar hosts de produção no código — configure NEXT_PUBLIC_API_URL no deploy.
 */

function stripTrailingSlashes(s: string): string {
  return s.replace(/\/+$/, '');
}

/** Raiz do backend como em api-client (sem barra final). Pode ou não incluir `/api`. */
export function getPrimaryApiRoot(): string {
  return stripTrailingSlashes(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
}

/** Base para fetch diretos a rotas DRF (termina em `/api`). */
export function getPrimaryApiBaseUrl(): string {
  const root = getPrimaryApiRoot();
  return root.endsWith('/api') ? root : `${root}/api`;
}

/** URL de backup (Render, etc.); vazia se não configurada. */
export function getBackupApiRoot(): string {
  const raw = process.env.NEXT_PUBLIC_API_BACKUP_URL;
  return raw ? stripTrailingSlashes(raw) : '';
}
