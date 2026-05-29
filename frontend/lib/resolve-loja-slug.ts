import apiClient from '@/lib/api-client';

const cache = new Map<string, string>();

/**
 * Resolve slug da API a partir do segmento da URL (slug real ou atalho, ex.: beleza → 34787081845).
 */
export async function resolveLojaApiSlug(urlSlug: string): Promise<string> {
  const key = (urlSlug || '').trim().toLowerCase();
  if (!key) return urlSlug;
  const cached = cache.get(key);
  if (cached) return cached;

  try {
    const { data } = await apiClient.get<{ slug?: string }>(
      `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(urlSlug)}`
    );
    const resolved = (data?.slug || urlSlug).trim();
    cache.set(key, resolved);
    return resolved;
  } catch {
    return urlSlug;
  }
}
