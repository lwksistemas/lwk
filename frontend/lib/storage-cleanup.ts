/**
 * Utilitários para limpar storage órfão (lojas excluídas).
 * Evita dados desatualizados em localStorage/sessionStorage.
 */

const CACHE_KEY_PREFIX = 'crm_loja_info:';
const LOGIN_CPF_PREFIX = 'login_lembrar_cpf_';
const PWA_LOJA_SLUG_KEY = 'pwa_loja_slug';

/**
 * Remove chaves de storage relacionadas a uma loja (ex: quando loja foi excluída).
 * Chamar quando API retornar 404 ou "loja não encontrada".
 */
export function clearOrphanStorageForSlug(slug: string): void {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.removeItem(`${CACHE_KEY_PREFIX}${slug}`);
    localStorage.removeItem(`${LOGIN_CPF_PREFIX}${slug}`);
    if (localStorage.getItem(PWA_LOJA_SLUG_KEY) === slug) {
      localStorage.removeItem(PWA_LOJA_SLUG_KEY);
    }
  } catch {
    /* ignore */
  }
}

/**
 * Remove chaves de storage órfãs (lojas que não existem mais).
 * Útil para limpeza periódica - percorre todas as chaves e remove as que
 * referenciam slugs de lojas inexistentes.
 * Nota: requer lista de slugs válidos da API.
 */
export function clearOrphanStorageKeys(validSlugs: string[]): void {
  if (typeof window === 'undefined') return;
  const validSet = new Set(validSlugs);
  try {
    // sessionStorage: crm_loja_info:*
    for (let i = sessionStorage.length - 1; i >= 0; i--) {
      const key = sessionStorage.key(i);
      if (key?.startsWith(CACHE_KEY_PREFIX)) {
        const slug = key.slice(CACHE_KEY_PREFIX.length);
        if (slug && !validSet.has(slug)) {
          sessionStorage.removeItem(key);
        }
      }
    }
    // localStorage: login_lembrar_cpf_*
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key?.startsWith(LOGIN_CPF_PREFIX)) {
        const slug = key.slice(LOGIN_CPF_PREFIX.length);
        if (slug && !validSet.has(slug)) {
          localStorage.removeItem(key);
        }
      }
    }
  } catch {
    /* ignore */
  }
}
