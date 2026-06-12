import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';

export interface LojaInfoPublica {
  id: number;
  nome: string;
}

/** Carrega id/nome da loja pelo slug da URL e sincroniza sessionStorage. */
export function useLojaInfoPublica(slug: string) {
  const [loja, setLoja] = useState<LojaInfoPublica | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (!slug) {
        if (!cancelled) setLoading(false);
        return;
      }
      try {
        const { data } = await apiClient.get<{ id?: number; nome?: string }>(
          `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`,
        );
        if (cancelled) return;
        if (data?.id) {
          setLoja({
            id: data.id,
            nome: data.nome || slug.replace(/-/g, ' '),
          });
          sessionStorage.setItem('current_loja_id', String(data.id));
        } else {
          setError(true);
        }
      } catch (e) {
        if (!cancelled) {
          logger.warn('Erro ao carregar loja:', e);
          setError(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [slug]);

  return { loja, loading, error };
}
